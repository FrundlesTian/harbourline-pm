"""Module 2 - Tool Integration Agent.
Writes the HC2-approved WBS and milestones into Jira Cloud (or a local mock board with
the same data contract) behind HC3, using stable external keys so re-runs update rather
than duplicate, and reads the board back to verify.

Data contract (plan -> PM issue)
  ext key      ext-HCH-WBS-<code with dashes> | ext-HCH-<milestone id>   (label, unique)
  issue type   WBS L1 Epic, L2 Task, L3 Subtask; milestone Task
  summary      "[<code>] <name>"
  description  WBS dictionary / milestone note + sources
  labels       ai-generated, <ext key>, wbs|milestone
  parent       parent's issue key (via ext key map)
  due date     milestone date when a full ISO date is known
  links        milestone dependency -> "Blocks"
Guardrail: no delete, no close/resolve, no transition to Done - those are human acts."""
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import audit, config, db, sources

AGENT = "tooling"
FORBIDDEN_FIELDS = {"status", "resolution", "resolutiondate"}


class GuardrailViolation(Exception):
    pass


# ------------------------------------------------------------------ plan -> items
def ext_key_for(kind, ident):
    return config.EXT_KEY_PREFIX + ("WBS-" + ident.replace(".", "-") if kind == "wbs" else ident)


def plan_items():
    items = []
    for w in db.q("SELECT * FROM wbs ORDER BY sort"):
        itype = {1: "Epic", 2: "Task"}.get(w["level"], os.environ.get("JIRA_SUBTASK_TYPE", "Subtask"))
        cites = "; ".join(sources.cite(s)["label"] for s in db.L(w["sources"]))
        items.append({"ext_key": ext_key_for("wbs", w["code"]), "kind": "wbs", "ref": w["code"],
                      "issue_type": itype, "summary": f"[{w['code']}] {w['name']}",
                      "description": f"{w['description']}\nSources: {cites}",
                      "labels": sorted([config.AI_LABEL, ext_key_for('wbs', w['code']), "wbs"]),
                      "parent_ext": ext_key_for("wbs", w["parent"]) if w["parent"] else None,
                      "due_date": None, "blocks_on": []})
    for m in db.q("SELECT * FROM milestones ORDER BY sort"):
        due = m["date"] if m["date"] and re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["date"]) else None
        cites = "; ".join(sources.cite(s)["label"] for s in db.L(m["sources"]))
        items.append({"ext_key": ext_key_for("ms", m["id"]), "kind": "milestone", "ref": m["id"],
                      "issue_type": "Task", "summary": f"[{m['id']}] Milestone: {m['name']}",
                      "description": f"Relative time: {m['rel_month']}. Date: {m['date'] or 'TBD - NOT FOUND'}. "
                                     f"WBS {m['wbs_code']}. {m['note']}\nSources: {cites}",
                      "labels": sorted([config.AI_LABEL, ext_key_for('ms', m['id']), "milestone"]),
                      "parent_ext": None, "due_date": due,
                      "blocks_on": [ext_key_for("ms", d) for d in db.L(m["depends_on"])]})
    return items


def content_hash(it):
    core = {k: it[k] for k in ("issue_type", "summary", "description", "labels", "parent_ext", "due_date", "blocks_on")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()[:16]


# ------------------------------------------------------------------ adapters
class MockBoard:
    name = "mock"

    def find_by_ext(self, ext_key):
        return [self._row(r) for r in db.q("SELECT * FROM pm_issues WHERE ext_key=?", (ext_key,))]

    def _row(self, r):
        return {"key": r["key"], "ext_key": r["ext_key"], "issue_type": r["issue_type"], "summary": r["summary"],
                "description": r["description"], "labels": db.L(r["labels"]), "parent_key": r["parent_key"],
                "due_date": r["due_date"], "status": r["status"],
                "status_category": "done" if (r["status"] or "").lower() in ("done", "closed") else "new",
                "links": db.L(r["links"]), "comments": db.L(r["comments"]), "url": None}

    def get_many(self, keys):
        return [self._row(r) for r in db.q(f"SELECT * FROM pm_issues WHERE key IN ({','.join('?' * len(keys))})", keys)] if keys else []

    def health(self):
        return {"account": "local mock board", "project": {"key": config.JIRA_PROJECT_KEY, "name": "Mock board (SQLite)"},
                "issue_types": ["Epic", "Task", "Subtask"], "type_mapping": {"Epic": "Epic", "Task": "Task", "Subtask": "Subtask"},
                "blocks_link_type": True}

    def create(self, it, parent_key):
        n = (db.q1("SELECT COUNT(*) c FROM pm_issues")["c"] or 0) + 1
        key = f"{config.JIRA_PROJECT_KEY}-{n}"
        while db.q1("SELECT key FROM pm_issues WHERE key=?", (key,)):
            n += 1
            key = f"{config.JIRA_PROJECT_KEY}-{n}"
        db.ex("INSERT INTO pm_issues VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (key, it["ext_key"], it["issue_type"], it["summary"], it["description"], db.J(it["labels"]),
               parent_key, it["due_date"], "To Do", db.J([]), db.J([]), db.now(), db.now()))
        return key

    def update(self, key, fields):
        sets, args = [], []
        for k, col in (("summary", "summary"), ("description", "description"), ("due_date", "due_date"),
                       ("parent_key", "parent_key"), ("issue_type", "issue_type")):
            if k in fields:
                sets.append(f"{col}=?"); args.append(fields[k])
        if "labels" in fields:
            sets.append("labels=?"); args.append(db.J(fields["labels"]))
        sets.append("updated_at=?"); args.append(db.now())
        db.ex(f"UPDATE pm_issues SET {', '.join(sets)} WHERE key=?", (*args, key))

    def comment(self, key, text):
        r = db.q1("SELECT comments FROM pm_issues WHERE key=?", (key,))
        c = db.L(r["comments"]) + [{"ts": db.now(), "author": "agent", "body": text}]
        db.ex("UPDATE pm_issues SET comments=?, updated_at=? WHERE key=?", (db.J(c), db.now(), key))

    def link_blocks(self, blocker_key, blocked_key):
        r = db.q1("SELECT links FROM pm_issues WHERE key=?", (blocked_key,))
        links = db.L(r["links"])
        if {"type": "is blocked by", "key": blocker_key} not in links:
            links.append({"type": "is blocked by", "key": blocker_key})
            db.ex("UPDATE pm_issues SET links=? WHERE key=?", (db.J(links), blocked_key))
            return True
        return False

    def list_all(self):
        return [self._row(r) for r in db.q("SELECT * FROM pm_issues ORDER BY rowid")]

    # Human-only operations on the mock board (Jira equivalents are done in Jira's UI)
    def human_transition(self, key, status):
        db.ex("UPDATE pm_issues SET status=?, updated_at=? WHERE key=?", (status, db.now(), key))


class JiraCloud:
    """Jira Cloud REST v3 adapter (API token + account e-mail, Basic auth).
    Uses the JQL search for discovery and the bulk-fetch endpoint for keys we already
    know, because Jira's search index lags a few seconds behind writes."""
    name = "jira"
    FIELDS = ["summary", "labels", "status", "parent", "duedate", "description", "issuetype", "issuelinks"]
    _types_cache = {}
    _link_inverted = None          # learned once: does POST /issueLink use the inverted direction?

    def __init__(self):
        if config.JIRA_MISSING:
            raise RuntimeError("Jira is not configured - missing " + ", ".join(config.JIRA_MISSING) + " in .env")
        tok = base64.b64encode(f"{config.JIRA_EMAIL}:{config.JIRA_API_TOKEN}".encode()).decode()
        self._auth = "Basic " + tok

    def _req(self, method, path, body=None, ok404=False):
        for attempt in range(5):
            req = urllib.request.Request(config.JIRA_BASE_URL + path, method=method,
                                         data=json.dumps(body).encode() if body is not None else None,
                                         headers={"Authorization": self._auth, "Accept": "application/json",
                                                  "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read().decode()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                if e.code in (429, 503) and attempt < 4:      # rate limited: honour Retry-After
                    time.sleep(min(float(e.headers.get("Retry-After") or 2 ** attempt), 10))
                    continue
                if e.code == 404 and ok404:
                    return None
                msg = audit.redact(e.read().decode()[:400])
                hint = {401: " (check JIRA_EMAIL and JIRA_API_TOKEN)", 403: " (account lacks permission on this project)",
                        404: " (check JIRA_BASE_URL / JIRA_PROJECT_KEY)"}.get(e.code, "")
                raise RuntimeError(f"Jira {method} {path.split('?')[0]} -> {e.code}{hint}: {msg}")
            except urllib.error.URLError as e:
                raise RuntimeError(f"Cannot reach Jira at {config.JIRA_BASE_URL}: {e.reason}")

    @staticmethod
    def _adf(text):
        return {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": line}]} for line in text.split("\n") if line]}

    @staticmethod
    def _plain(adf):
        if not adf:
            return ""
        out = []
        def walk(n):
            if isinstance(n, dict):
                if n.get("type") == "text":
                    out.append(n.get("text", ""))
                for c in n.get("content", []):
                    walk(c)
                if n.get("type") == "paragraph":
                    out.append("\n")
        walk(adf)
        return "".join(out).strip()

    def _norm(self, i):
        f = i["fields"]
        labels = f.get("labels", [])
        st = f.get("status") or {}
        return {"key": i["key"], "ext_key": next((l for l in labels if l.startswith(config.EXT_KEY_PREFIX)), None),
                "issue_type": (f.get("issuetype") or {}).get("name"), "summary": f.get("summary"),
                "description": self._plain(f.get("description")), "labels": labels,
                "parent_key": (f.get("parent") or {}).get("key"), "due_date": f.get("duedate"),
                "status": st.get("name", ""), "status_category": (st.get("statusCategory") or {}).get("key", ""),
                "links": [{"type": "is blocked by", "key": l["inwardIssue"]["key"], "id": l.get("id")} if "inwardIssue" in l
                          else {"type": "blocks", "key": l["outwardIssue"]["key"], "id": l.get("id")}
                          for l in f.get("issuelinks", []) if (l.get("type") or {}).get("name") == "Blocks"],
                "comments": [], "url": f"{config.JIRA_BASE_URL}/browse/{i['key']}"}

    def _search(self, jql):
        res, token = [], None
        while True:
            q = {"jql": jql, "fields": ",".join(self.FIELDS), "maxResults": 100}
            if token:
                q["nextPageToken"] = token
            data = self._req("GET", "/rest/api/3/search/jql?" + urllib.parse.urlencode(q))
            res += [self._norm(i) for i in data.get("issues", [])]
            token = data.get("nextPageToken")
            if not token or data.get("isLast") is True:
                return res

    def get_many(self, keys):
        """Read issues by key (strongly consistent, unlike JQL search)."""
        out = []
        keys = [k for k in keys if k and k.startswith(config.JIRA_PROJECT_KEY + "-")]
        for i in range(0, len(keys), 100):
            data = self._req("POST", "/rest/api/3/issue/bulkfetch",
                             {"issueIdsOrKeys": keys[i:i + 100], "fields": self.FIELDS})
            out += [self._norm(x) for x in data.get("issues", [])]
        return out

    def find_by_ext(self, ext_key):
        return self._search(f'project = "{config.JIRA_PROJECT_KEY}" AND labels = "{ext_key}"')

    TASK_NAMES = {"task", "任务", "任務", "タスク", "tarea", "tâche", "aufgabe", "tarefa", "attività"}

    def issue_types(self):
        if config.JIRA_PROJECT_KEY not in self._types_cache:
            d = self._req("GET", f"/rest/api/3/issue/createmeta/{config.JIRA_PROJECT_KEY}/issuetypes?maxResults=100")
            self._types_cache[config.JIRA_PROJECT_KEY] = [
                {"id": t["id"], "name": t["name"], "subtask": bool(t.get("subtask")),
                 "level": t.get("hierarchyLevel", -1 if t.get("subtask") else 0)}
                for t in (d.get("issueTypes") or d.get("values") or [])]
        return self._types_cache[config.JIRA_PROJECT_KEY]

    def resolve_type(self, wanted):
        """Map the contract's Epic / Task / Subtask onto this project's issue types by hierarchy
        level, so localized sites (e.g. 长篇故事 / 任务 / 子任务) work. Returns {id, name}.
        Override with JIRA_TYPE_EPIC / JIRA_TYPE_TASK / JIRA_TYPE_SUBTASK (name or id)."""
        types = self.issue_types()
        w = wanted.lower().replace("-", "")
        role = "subtask" if w == "subtask" else w
        override = os.environ.get(f"JIRA_TYPE_{role.upper()}")
        if override:
            hit = [t for t in types if override in (t["id"], t["name"])]
            if hit:
                return {"id": hit[0]["id"], "name": hit[0]["name"]}
        level = {"epic": 1, "task": 0, "subtask": -1}.get(role)
        cands = [t for t in types if t["level"] == level] if level is not None else []
        if role == "task":
            cands.sort(key=lambda t: (t["name"].lower() not in self.TASK_NAMES, t["name"]))
        if not cands:
            cands = [t for t in types if t["name"].lower() == wanted.lower()]
        if not cands:
            raise RuntimeError(f"Jira project {config.JIRA_PROJECT_KEY} has no issue type for '{wanted}' "
                               f"(available: {', '.join(t['name'] for t in types)})")
        return {"id": cands[0]["id"], "name": cands[0]["name"]}

    def create(self, it, parent_key):
        fields = {"project": {"key": config.JIRA_PROJECT_KEY}, "summary": it["summary"],
                  "issuetype": {"id": self.resolve_type(it["issue_type"])["id"]}, "labels": it["labels"],
                  "description": self._adf(it["description"])}
        if it["due_date"]:
            fields["duedate"] = it["due_date"]
        if parent_key:
            fields["parent"] = {"key": parent_key}
        return self._req("POST", "/rest/api/3/issue", {"fields": fields})["key"]

    def update(self, key, fields):
        f = {}
        if "summary" in fields: f["summary"] = fields["summary"]
        if "description" in fields: f["description"] = self._adf(fields["description"])
        if "labels" in fields: f["labels"] = fields["labels"]
        if "due_date" in fields: f["duedate"] = fields["due_date"]
        if "parent_key" in fields and fields["parent_key"]: f["parent"] = {"key": fields["parent_key"]}
        self._req("PUT", f"/rest/api/3/issue/{key}", {"fields": f})

    def comment(self, key, text):
        self._req("POST", f"/rest/api/3/issue/{key}/comment", {"body": self._adf(text)})

    def _blocked_by(self, key):
        d = self._req("GET", f"/rest/api/3/issue/{key}?fields=issuelinks")
        return [l for l in self._norm({"key": key, "fields": d.get("fields", {})})["links"]]

    def link_blocks(self, blocker_key, blocked_key):
        """Idempotent 'blocker blocks blocked'. Jira's POST /issueLink direction is easy to get
        backwards, so the first link of a session is read back and the direction learned."""
        if any(l["type"] == "is blocked by" and l["key"] == blocker_key for l in self._blocked_by(blocked_key)):
            return False
        inv = bool(JiraCloud._link_inverted)
        body = {"type": {"name": "Blocks"},
                "outwardIssue": {"key": blocked_key if inv else blocker_key},
                "inwardIssue": {"key": blocker_key if inv else blocked_key}}
        self._req("POST", "/rest/api/3/issueLink", body)
        if JiraCloud._link_inverted is None:
            links = self._blocked_by(blocked_key)
            if any(l["type"] == "is blocked by" and l["key"] == blocker_key for l in links):
                JiraCloud._link_inverted = inv
            else:   # we created the reverse link: remove our own wrong link and redo it the other way
                for l in links:
                    if l["type"] == "blocks" and l["key"] == blocker_key and l.get("id"):
                        self._req("DELETE", f"/rest/api/3/issueLink/{l['id']}")
                        audit.log(AGENT, "pm link direction corrected", "pm_link", l["id"],
                                  detail={"note": "agent removed the reversed link it had just created"})
                JiraCloud._link_inverted = not inv
                body["outwardIssue"], body["inwardIssue"] = body["inwardIssue"], body["outwardIssue"]
                self._req("POST", "/rest/api/3/issueLink", body)
        return True

    def list_all(self):
        return self._search(f'project = "{config.JIRA_PROJECT_KEY}" AND labels = "{config.AI_LABEL}" ORDER BY key')

    def health(self):
        me = self._req("GET", "/rest/api/3/myself")
        proj = self._req("GET", f"/rest/api/3/project/{config.JIRA_PROJECT_KEY}", ok404=True)
        if not proj:
            raise RuntimeError(f"Project {config.JIRA_PROJECT_KEY} not found on {config.JIRA_BASE_URL} "
                               "(create it in Jira, or set JIRA_PROJECT_KEY)")
        types = self.issue_types()
        mapping = {}
        for w in ("Epic", "Task", "Subtask"):
            try:
                mapping[w] = self.resolve_type(w)["name"]
            except RuntimeError as e:
                mapping[w] = "MISSING - " + str(e)
        lt = self._req("GET", "/rest/api/3/issueLinkType")
        return {"account": me.get("displayName"), "account_email_ok": bool(me.get("accountId")),
                "project": {"key": proj.get("key"), "name": proj.get("name"),
                            "style": proj.get("style"), "url": f"{config.JIRA_BASE_URL}/browse/{proj.get('key')}"},
                "issue_types": [t["name"] for t in types], "type_mapping": mapping,
                "blocks_link_type": any(t.get("name") == "Blocks" for t in lt.get("issueLinkTypes", []))}


class Guarded:
    """The only object agents receive. It exposes create/update/comment/link/read and
    turns any destructive or closing request into a logged, blocked guardrail event."""

    def __init__(self, backend):
        self._b = backend
        self.name = backend.name

    def find_by_ext(self, k): return self._b.find_by_ext(k)
    def list_all(self): return self._b.list_all()
    def get_many(self, keys): return self._b.get_many(keys)
    def health(self): return self._b.health()

    def create(self, it, parent_key):
        if config.AI_LABEL not in it["labels"]:
            raise GuardrailViolation("agent-created items must carry the ai-generated label")
        key = self._b.create(it, parent_key)
        audit.log(AGENT, "pm create", "pm_issue", key, detail={"ext_key": it["ext_key"], "backend": self.name})
        return key

    def update(self, key, fields, actor=AGENT):
        bad = FORBIDDEN_FIELDS & set(fields)
        if bad:
            self._blocked(actor, f"update with {sorted(bad)}", key)
        self._b.update(key, fields)
        audit.log(actor, "pm update", "pm_issue", key, detail={"fields": sorted(fields), "backend": self.name})

    def comment(self, key, text, actor=AGENT):
        self._b.comment(key, text)
        audit.log(actor, "pm comment", "pm_issue", key, detail={"chars": len(text), "backend": self.name})

    def link_blocks(self, blocker, blocked):
        if self._b.link_blocks(blocker, blocked):
            audit.log(AGENT, "pm link", "pm_issue", blocked, detail={"is_blocked_by": blocker})

    def delete(self, key, actor=AGENT):
        self._blocked(actor, "delete", key)

    def transition(self, key, status, actor=AGENT):
        self._blocked(actor, f"transition to {status}", key)

    def close(self, key, actor=AGENT):
        self._blocked(actor, "close", key)

    def _blocked(self, actor, what, key):
        audit.log(actor, f"BLOCKED: {what}", "pm_issue", key, outcome="blocked",
                  detail={"rule": "Agents may create, update and comment. Done/close/delete is a human act."})
        raise GuardrailViolation(f"Guardrail: agents may not {what} ({key}). This is a human act.")


def backend():
    return Guarded(JiraCloud() if config.PM_BACKEND == "jira" else MockBoard())


def reset_jira_available():
    return config.PM_BACKEND == "jira" or not config.JIRA_MISSING


def reset_candidates():
    """Find live project issues, including syncs missing from Jira's search index."""
    if not reset_jira_available():
        return []
    cloud = JiraCloud()
    searched = cloud._search(f'project = "{config.JIRA_PROJECT_KEY}" ORDER BY key')
    keys = {issue["key"] for issue in searched}
    known = db.q("SELECT remote_key FROM pm_sync_map WHERE backend='jira'")
    keys.update(r["remote_key"] for r in known if r["remote_key"])
    return cloud.get_many(sorted(keys))


def clear_jira_for_reset(expected_keys):
    """Delete the confirmed Jira project contents outside the agent's Guarded adapter."""
    if not reset_jira_available():
        if expected_keys:
            raise ValueError("Jira is not configured for reset")
        return 0
    cloud = JiraCloud()
    current = reset_candidates()
    keys = sorted(issue["key"] for issue in current)
    if keys != sorted(expected_keys):
        raise ValueError("Jira issues changed since the preview; preview the reset again")
    fresh = cloud.get_many(keys)
    if len(fresh) != len(keys) or {issue["key"] for issue in fresh} != set(keys):
        raise RuntimeError("Jira issues changed since the preview; nothing was deleted")
    by_key = {issue["key"]: issue for issue in fresh}

    def depth(issue):
        n, parent = 0, issue["parent_key"]
        while parent in by_key and n < len(by_key):
            n += 1
            parent = by_key[parent]["parent_key"]
        return n

    deleted = 0
    for issue in sorted(fresh, key=depth, reverse=True):
        key = issue["key"]
        # Subtasks are deleted first; false prevents an unreviewed cascade.
        try:
            cloud._req("DELETE", f"/rest/api/3/issue/{urllib.parse.quote(key)}?deleteSubtasks=false")
        except RuntimeError as exc:
            raise RuntimeError(f"Jira cleanup stopped after {deleted}/{len(fresh)} issues; "
                               f"local data was not reset: {exc}") from exc
        deleted += 1
        audit.log("demo reset", "Jira project issue deleted", "pm_issue", key,
                  detail={"project": config.JIRA_PROJECT_KEY}, actor_type="human")
    return deleted


# ------------------------------------------------------------------ sync
def remote_index(pm):
    """ext key -> board items, from ONE search plus a consistent read of keys we wrote
    before (covers Jira's search-index lag, so a quick re-run never duplicates)."""
    idx, seen = {}, set()

    def add(b):
        if b["ext_key"] and b["key"] not in seen:
            seen.add(b["key"])
            idx.setdefault(b["ext_key"], []).append(b)
    for b in pm.list_all():
        add(b)
    known = db.q("SELECT ext_key, remote_key FROM pm_sync_map WHERE backend=?", (pm.name,))
    lag = [r["remote_key"] for r in known if r["ext_key"] not in idx and r["remote_key"]]
    if lag:
        for b in pm.get_many(lag):
            add(b)
    return idx


def locate(pm, ext_key):
    """Find one plan item on the board: the key we recorded at sync time first (consistent
    read), then the label search."""
    m = db.q1("SELECT remote_key FROM pm_sync_map WHERE ext_key=? AND backend=?", (ext_key, pm.name))
    if m and m["remote_key"]:
        got = [b for b in pm.get_many([m["remote_key"]]) if b["ext_key"] == ext_key]
        if got:
            return got
    return pm.find_by_ext(ext_key)


def preview():
    """Read-only diff between the approved plan and the board. Safe to run any time."""
    pm = backend()
    if not plan_approved():
        return {"ok": False, "reason": "HC2 (plan baseline) not approved yet", "items": []}
    out = []
    idx = remote_index(pm)
    for it in plan_items():
        h = content_hash(it)
        remote = idx.get(it["ext_key"], [])
        if not remote:
            action = "create"
        elif len(remote) > 1:
            action = "duplicate-on-board (human must resolve; agent will update the first)"
        else:
            m = db.q1("SELECT content_hash FROM pm_sync_map WHERE ext_key=? AND backend=?", (it["ext_key"], pm.name))
            action = "unchanged" if (m and m["content_hash"] == h and _same(remote[0], it)) else "update"
        out.append({"ext_key": it["ext_key"], "summary": it["summary"], "action": action, "hash": h,
                    "remote_key": remote[0]["key"] if remote else None})
    pid = hashlib.sha256(json.dumps([(o["ext_key"], o["action"], o["hash"]) for o in out]).encode()).hexdigest()[:12]
    counts = {}
    for o in out:
        counts[o["action"].split(" ")[0]] = counts.get(o["action"].split(" ")[0], 0) + 1
    db.kv_set("last_preview", {"id": pid, "counts": counts})
    audit.log(AGENT, "pm preview (read-only)", "sync_preview", pid, detail=counts)
    return {"ok": True, "preview_id": pid, "backend": pm.name, "counts": counts, "items": out}


def _kept_labels(remote):
    """Labels added on the board after an approved HC6 action (change-*) survive re-syncs."""
    return {l for l in remote.get("labels", []) if l.startswith("change-")}


def _same(remote, it):
    return remote["summary"] == it["summary"] \
        and sorted(set(remote["labels"]) - _kept_labels(remote)) == sorted(it["labels"]) \
        and (remote.get("due_date") or None) == it["due_date"]


def plan_approved():
    from . import planning
    return audit.is_approved("HC2", "plan", planning.plan_hash())


def apply(preview_id):
    """Write to the PM tool. Requires HC3 approval of this exact preview."""
    if not audit.is_approved("HC3", "sync_preview", preview_id):
        audit.log(AGENT, "pm sync refused", "sync_preview", preview_id, outcome="blocked",
                  detail={"reason": "HC3 approval missing"})
        return {"ok": False, "reason": "HC3 approval for this preview is missing"}
    pm = backend()
    created = updated = unchanged = 0
    keymap, links = {}, {}
    items = plan_items()
    idx = remote_index(pm)
    for it in items:                       # parents first: plan_items is ordered by WBS sort
        h = content_hash(it)
        remote = idx.get(it["ext_key"], [])
        if remote:
            links[remote[0]["key"]] = {(l["type"], l["key"]) for l in remote[0].get("links", [])}
        parent_key = keymap.get(it["parent_ext"]) if it["parent_ext"] else None
        if not remote:
            key = pm.create(it, parent_key)
            created += 1
        else:
            key = remote[0]["key"]
            m = db.q1("SELECT content_hash FROM pm_sync_map WHERE ext_key=? AND backend=?", (it["ext_key"], pm.name))
            if m and m["content_hash"] == h and _same(remote[0], it):
                unchanged += 1
            else:
                pm.update(key, {"summary": it["summary"], "description": it["description"],
                                "labels": sorted(set(it["labels"]) | _kept_labels(remote[0])),
                                "due_date": it["due_date"], "parent_key": parent_key})
                updated += 1
        keymap[it["ext_key"]] = key
        db.ex("INSERT OR REPLACE INTO pm_sync_map VALUES(?,?,?,?,?)", (it["ext_key"], pm.name, key, h, db.now()))
    for it in items:
        for dep in it["blocks_on"]:
            if dep in keymap and ("is blocked by", keymap[dep]) not in links.get(keymap[it["ext_key"]], set()):
                pm.link_blocks(keymap[dep], keymap[it["ext_key"]])
    res = {"ok": True, "backend": pm.name, "created": created, "updated": updated, "unchanged": unchanged}
    audit.log(AGENT, "pm sync applied", "sync_preview", preview_id, detail=res)
    res["readback"] = readback()
    return res


def readback():
    """Read the board and verify it reflects the plan (missing, mismatched, duplicate,
    non-labelled, and items a human moved to Done)."""
    pm = backend()
    by_ext = remote_index(pm)
    board = pm.list_all()
    listed = {b["key"] for b in board}
    board += [b for v in by_ext.values() for b in v if b["key"] not in listed]
    items = plan_items() if plan_approved() else []
    missing, mismatch = [], []
    for it in items:
        r = by_ext.get(it["ext_key"])
        if not r:
            missing.append(it["ext_key"])
        elif not _same(r[0], it):
            mismatch.append(it["ext_key"])
    dups = {k: [x["key"] for x in v] for k, v in by_ext.items() if len(v) > 1}
    unlabelled = [b["key"] for b in board if config.AI_LABEL not in b["labels"]]
    done = [b["key"] for b in board if b.get("status_category") == "done" or b["status"].lower() in ("done", "closed")]
    res = {"backend": pm.name, "board_items": len(board), "plan_items": len(items), "missing": missing,
           "mismatched": mismatch, "duplicates": dups, "unlabelled": unlabelled, "human_done": done,
           "verified": not missing and not mismatch and not dups}
    audit.log(AGENT, "pm readback", "board", pm.name, detail={k: (len(v) if isinstance(v, (list, dict)) else v)
                                                             for k, v in res.items()})
    return res


def board():
    return backend().list_all()


def health():
    """Connection / configuration check shown in the UI. Never returns the token."""
    info = {"backend": config.PM_BACKEND, "project_key": config.JIRA_PROJECT_KEY,
            "site": config.JIRA_BASE_URL or None, "email": config.JIRA_EMAIL or None,
            "token_set": bool(config.JIRA_API_TOKEN), "missing": config.JIRA_MISSING,
            "synced_items": db.q1("SELECT COUNT(*) c FROM pm_sync_map WHERE backend=?", (config.PM_BACKEND,))["c"],
            "last_sync": (db.q1("SELECT MAX(synced_at) t FROM pm_sync_map WHERE backend=?", (config.PM_BACKEND,)) or {}).get("t")}
    try:
        info.update(backend().health(), ok=True)
    except Exception as e:
        info.update(ok=False, error=str(e))
    audit.log(AGENT, "pm health check", "board", config.PM_BACKEND, outcome="ok" if info["ok"] else "error",
              detail={"ok": info["ok"], "error": info.get("error")})
    return info
