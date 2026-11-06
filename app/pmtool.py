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
                "due_date": r["due_date"], "status": r["status"], "links": db.L(r["links"]),
                "comments": db.L(r["comments"])}

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
    name = "jira"

    def __init__(self):
        tok = base64.b64encode(f"{config.JIRA_EMAIL}:{config.JIRA_API_TOKEN}".encode()).decode()
        self._auth = "Basic " + tok

    def _req(self, method, path, body=None):
        req = urllib.request.Request(config.JIRA_BASE_URL + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": self._auth, "Accept": "application/json",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Jira {method} {path} -> {e.code}: {audit.redact(e.read().decode()[:400])}")

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

    def _search(self, jql):
        res, token = [], None
        while True:
            q = {"jql": jql, "fields": "summary,labels,status,parent,duedate,description,issuetype,issuelinks",
                 "maxResults": 100}
            if token:
                q["nextPageToken"] = token
            data = self._req("GET", "/rest/api/3/search/jql?" + urllib.parse.urlencode(q))
            for i in data.get("issues", []):
                f = i["fields"]
                labels = f.get("labels", [])
                ext = next((l for l in labels if l.startswith(config.EXT_KEY_PREFIX)), None)
                res.append({"key": i["key"], "ext_key": ext, "issue_type": f["issuetype"]["name"],
                            "summary": f.get("summary"), "description": self._plain(f.get("description")),
                            "labels": labels, "parent_key": (f.get("parent") or {}).get("key"),
                            "due_date": f.get("duedate"), "status": f["status"]["name"],
                            "links": [{"type": "is blocked by", "key": l["inwardIssue"]["key"]} if "inwardIssue" in l
                                      else {"type": "blocks", "key": l["outwardIssue"]["key"]}
                                      for l in f.get("issuelinks", [])], "comments": []})
            token = data.get("nextPageToken")
            if not token or data.get("isLast", True):
                return res

    def find_by_ext(self, ext_key):
        return self._search(f'project = "{config.JIRA_PROJECT_KEY}" AND labels = "{ext_key}"')

    def create(self, it, parent_key):
        fields = {"project": {"key": config.JIRA_PROJECT_KEY}, "summary": it["summary"],
                  "issuetype": {"name": it["issue_type"]}, "labels": it["labels"],
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

    def link_blocks(self, blocker_key, blocked_key):
        self._req("POST", "/rest/api/3/issueLink", {"type": {"name": "Blocks"},
                                                     "outwardIssue": {"key": blocker_key},
                                                     "inwardIssue": {"key": blocked_key}})
        return True

    def list_all(self):
        return self._search(f'project = "{config.JIRA_PROJECT_KEY}" AND labels = "{config.AI_LABEL}" ORDER BY key')


class Guarded:
    """The only object agents receive. It exposes create/update/comment/link/read and
    turns any destructive or closing request into a logged, blocked guardrail event."""

    def __init__(self, backend):
        self._b = backend
        self.name = backend.name

    def find_by_ext(self, k): return self._b.find_by_ext(k)
    def list_all(self): return self._b.list_all()

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


# ------------------------------------------------------------------ sync
def preview():
    """Read-only diff between the approved plan and the board. Safe to run any time."""
    pm = backend()
    if not plan_approved():
        return {"ok": False, "reason": "HC2 (plan baseline) not approved yet", "items": []}
    out = []
    for it in plan_items():
        h = content_hash(it)
        remote = pm.find_by_ext(it["ext_key"])
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


def _same(remote, it):
    return remote["summary"] == it["summary"] and sorted(remote["labels"]) == sorted(it["labels"]) \
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
    keymap = {}
    items = plan_items()
    for it in items:                       # parents first: plan_items is ordered by WBS sort
        h = content_hash(it)
        remote = pm.find_by_ext(it["ext_key"])
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
                pm.update(key, {"summary": it["summary"], "description": it["description"], "labels": it["labels"],
                                "due_date": it["due_date"], "parent_key": parent_key})
                updated += 1
        keymap[it["ext_key"]] = key
        db.ex("INSERT OR REPLACE INTO pm_sync_map VALUES(?,?,?,?,?)", (it["ext_key"], pm.name, key, h, db.now()))
    for it in items:
        for dep in it["blocks_on"]:
            if dep in keymap:
                pm.link_blocks(keymap[dep], keymap[it["ext_key"]])
    res = {"ok": True, "backend": pm.name, "created": created, "updated": updated, "unchanged": unchanged}
    audit.log(AGENT, "pm sync applied", "sync_preview", preview_id, detail=res)
    res["readback"] = readback()
    return res


def readback():
    """Read the board and verify it reflects the plan (missing, mismatched, duplicate,
    non-labelled, and items a human moved to Done)."""
    pm = backend()
    board = pm.list_all()
    by_ext = {}
    for b in board:
        if b["ext_key"]:
            by_ext.setdefault(b["ext_key"], []).append(b)
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
    done = [b["key"] for b in board if b["status"].lower() in ("done", "closed")]
    res = {"backend": pm.name, "board_items": len(board), "plan_items": len(items), "missing": missing,
           "mismatched": mismatch, "duplicates": dups, "unlabelled": unlabelled, "human_done": done,
           "verified": not missing and not mismatch and not dups}
    audit.log(AGENT, "pm readback", "board", pm.name, detail={k: (len(v) if isinstance(v, (list, dict)) else v)
                                                             for k, v in res.items()})
    return res


def board():
    return backend().list_all()
