"""Module 6 - Change Agent.
Injects a dated, numbered change event without touching the original data pack;
detects what in the plan, register, what-ifs, reports and PM board is now stale;
refreshes stale drafts automatically; drafts a Change Impact Note and pending actions
that only a human (HC6) can approve. Never edits the baseline, closes or deletes."""
import json
import re

from . import audit, config, critic, db, llm, pmtool, reporting, risk, sources
from .agents import AGENT_CARDS

AGENT = "change"

KEYWORDS = [
    (r"asbestos", ["asbestos", "variation"]),
    (r"eligib", ["eligible-cost", "grant"]),
    (r"variation", ["variation", "budget"]),
    (r"programme|schedule|opening date", ["schedule"]),
    (r"operator", ["aac-operator"]),
    (r"active ageing", ["aac-operator"]),
    (r"withdr", ["aac-operator"]),
    (r"signed operator agreements|operator agreement", ["operator-agreements", "tranche-2"]),
    (r"grant", ["grant"]),
    (r"impact note|committee", ["reporting"]),
]


SECONDARY = {"grant", "schedule", "budget", "reporting"}   # broad tags: need a second match to count


def derive_tags(text):
    tags = set()
    for pat, t in KEYWORDS:
        if re.search(pat, text, re.I):
            tags.update(t)
    return sorted(tags)


def load_event_file(eid):
    p = config.CHANGE_EVENTS / f"{eid}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _downstream(ms_ids):
    ms = db.q("SELECT id, depends_on FROM milestones")
    out, frontier = set(ms_ids), set(ms_ids)
    while frontier:
        nxt = {m["id"] for m in ms if set(db.L(m["depends_on"])) & frontier} - out
        out |= nxt
        frontier = nxt
    return sorted(out - set(ms_ids))


def _f(fid):
    return db.q1("SELECT * FROM facts WHERE id=?", (fid,))


def _specific(eid):
    """Event-specific cost/time analysis, decisions and unresolved items, all cited."""
    head = float(_f("F21")["value"])
    unresolved = [
        {"item": "Addressee 'Finance Director' is not identified in the pack (EDC lists Ms Ong as Finance Manager).",
         "sources": ["EDC-attendees", eid]},
        {"item": "Exact date of the 'April committee meeting': NOT FOUND. Next minuted EDC meeting is 2027-04-08 (2 days after the event).",
         "sources": ["EDC-6.6", eid]},
    ]
    if eid == "CE-01":
        lo, hi = 0.35, 0.60
        cost = [
            {"text": f"Asbestos removal S${lo}-{hi}M is now fully Council-funded (previously its eligibility was NOT FOUND).", "cites": ["F38", eid]},
            {"text": f"Budget headroom ~S${head}M falls to S${round(head - hi, 2)}-{round(head - lo, 2)}M if the variation is charged to it.",
             "cites": ["F21", "F38"], "calc": [{"expr": "F21-0.60", "value": round(head - hi, 2)}, {"expr": "F21-0.35", "value": round(head - lo, 2)}]},
            {"text": "Whether the headroom is contingency is still undecided; roof strengthening (unpriced) competes for the same money.", "cites": ["F22", "F41"]},
            {"text": "Time: KHB estimate 4-6 weeks; no programme change agreed; forecast completion beyond 2028-12-31 would need Fund prior approval.",
             "cites": ["F39", "F34", "F63", eid]},
        ]
        decisions = [
            {"what": "Approve the funding route for the ineligible asbestos cost (headroom / contingency / capital reserves).",
             "who": "Sponsor (D. Koh) with Finance Manager (M.L. Ong)", "when": "Before the April EDC meeting (next minuted: 2027-04-08)",
             "sources": [eid, "EDC-1.2", "SA-Q5"]},
            {"what": "Instruct KHB on the variation and decide whether to accept an extension of time (programme change not agreed).",
             "who": "Sponsor / EDC", "when": "Before the April EDC meeting", "sources": [eid, "EDC-6.5", "PR3-3"]},
            {"what": "Decide whether to seek NRF prior approval under clause 4.2 if completion moves past 31 Dec 2028.",
             "who": "Sponsor with Finance Manager", "when": "Once KHB prices the extension (date NOT FOUND)", "sources": ["NRF-4.2", "EDC-4.1"]},
        ]
        unresolved += [
            {"item": "CONFLICT CF12: the event says the variation was submitted at the March committee meeting; EDC 6.5 says 'to be raised' and KHB Report No.3 says 'To be submitted'.",
             "sources": [eid, "EDC-6.5", "PR3-4"]},
            {"item": "Final variation value is not known (estimate range only).", "sources": ["PR3-4"]},
            {"item": "Programme float on the level 2 riser path: NOT FOUND.", "sources": ["PR3-3"]},
        ]
    else:
        t2 = round(float(_f("F25")["value"]) * 0.30, 2)
        cost = [
            {"text": "AAC EOI now has no respondents; Council policy needs at least 3 before appointment.", "cites": ["F14", eid]},
            {"text": f"Tranche 2 (30% of grant; S${t2}M of the S$10.2M maximum) cannot be released without signed agreements for ALL social service spaces.",
             "cites": ["F45", "F70", "F25"], "calc": [{"expr": "F25*0.30", "value": t2}]},
            {"text": "Seabreeze analogs (indicative only): missed operator condition delayed a tranche 4 months; late operator appointment cost S$85,000 in rework.",
             "cites": ["F69", "F68"]},
            {"text": "The withdrawal cites uncertain opening dates - the unreconciled programme (EDC action 4.2) is a root cause.", "cites": [eid, "F43"]},
        ]
        decisions = [
            {"what": "Choose the re-procurement route for the AAC operator (re-issue / widen EOI, or another route allowed by Council policy).",
             "who": "Sponsor (D. Koh) with Council PM (R. Shankar)", "when": "Before the April EDC meeting (next minuted: 2027-04-08)",
             "sources": [eid, "SA-Q2", "EDC-4.4"]},
            {"what": "Engage the Fund on the Tranche 2 condition; any change to AAC scope needs the Fund's prior written approval.",
             "who": "Sponsor with Finance Manager (M.L. Ong)", "when": "Before the T2 claim is planned (date NOT FOUND)", "sources": ["NRF-T2", "NRF-4.1"]},
            {"what": "Publish firm opening dates (reconcile the programme) so a new EOI can attract respondents.",
             "who": "Council PM (R. Shankar)", "when": "Before re-issuing the EOI", "sources": [eid, "EDC-4.2", "EDC-5.4"]},
            {"what": "Assign an owner to the AAC operator agreement (D14).", "who": "Sponsor", "when": "Now", "sources": ["DEL-D14"]},
        ]
        unresolved += [
            {"item": "New AAC appointment date: NOT FOUND.", "sources": ["SA-Q2"]},
            {"item": "Whether the Fund would accept a phased T2 claim: NOT FOUND.", "sources": ["NRF-T2"]},
        ]
    return cost, decisions, unresolved


def inject(eid=None, custom=None):
    ev = custom or load_event_file(eid)
    eid = ev["id"]
    tags = derive_tags(ev["title"] + " " + ev["text"])
    sources.add_source(eid, f"Change event {eid} ({ev.get('source', 'Week 12')})", f"{eid} dated {ev['date']}",
                       ev["text"], "change")
    db.ex("INSERT OR REPLACE INTO change_events(id,title,date,source,text,tags,received_at,impact) VALUES(?,?,?,?,?,?,?,?)",
          (eid, ev["title"], ev["date"], ev.get("source", ""), ev["text"], db.J(tags), db.now(), db.J({})))
    audit.log(AGENT, "change event received", "change_event", eid, detail={"tags": tags, "date": ev["date"]})
    return analyse(eid)


def analyse(eid):
    ev = db.q1("SELECT * FROM change_events WHERE id=?", (eid,))
    tags = set(db.L(ev["tags"]))
    primary = tags - SECONDARY

    def hit(t):
        it = set(db.L(t))
        return bool(it & primary) or len(it & tags) >= 2
    wbs = [w for w in db.q("SELECT * FROM wbs ORDER BY sort") if w["level"] == 3 and hit(w["tags"])]
    dels = sorted({d for w in wbs for d in db.L(w["deliverable_refs"])})
    ms = [m for m in db.q("SELECT * FROM milestones ORDER BY sort") if hit(m["tags"])]
    downstream = _downstream([m["id"] for m in ms])
    risks = [r for r in db.q("SELECT * FROM risks ORDER BY score DESC") if hit(r["tags"])]
    whatifs = [w for w in db.q("SELECT * FROM whatifs") if hit(w["tags"])]
    reports = [r for r in db.q("SELECT * FROM reports WHERE planted IS NULL AND status!='stale'")
               if hit(r["tags"]) and eid not in r["content"]]

    db.ex("DELETE FROM stale_items WHERE event_id=?", (eid,))
    stale = []
    for r in risks:
        stale.append(("risk", r["id"], f"tags {sorted(set(db.L(r['tags'])) & tags)}"))
        db.ex("UPDATE risks SET stale=1 WHERE id=?", (r["id"],))
    for w in whatifs:
        stale.append(("whatif", w["id"], "assumptions depend on the event's subject"))
        db.ex("UPDATE whatifs SET stale=1 WHERE id=?", (w["id"],))
    for r in reports:
        stale.append(("report", r["id"], "drafted before the event; topic overlaps"))
        db.ex("UPDATE reports SET status='stale' WHERE id=?", (r["id"],))
    for m in ms:
        stale.append(("milestone", m["id"], "date/condition depends on the event's subject"))
    for (t, i, why) in stale:
        db.ex("INSERT INTO stale_items(event_id,item_type,item_id,reason) VALUES(?,?,?,?)", (eid, t, i, why))
        audit.log(AGENT, "mark stale", t, i, detail={"event": eid, "reason": why})

    cost, decisions, unresolved = _specific(eid)
    for c in cost:   # the change agent's own claims are critic-checked too
        probs = critic.trace_claim(c)
        c["trace"] = "ok" if not probs else probs

    # Automatic refresh (no human re-run): what-ifs and report drafts regenerate now.
    risk.run_whatifs(event=eid)
    for w in whatifs:
        db.ex("UPDATE stale_items SET refreshed_id=? WHERE event_id=? AND item_type='whatif' AND item_id=?",
              (w["id"] + f" v{db.q1('SELECT version FROM whatifs WHERE id=?', (w['id'],))['version']}", eid, w["id"]))
    new_reports = reporting.run_all(use_llm=llm.available(), event_id=eid) if reports or db.q("SELECT id FROM reports") else []
    for old in reports:
        nr = next((n for n in new_reports if n["kind"] == old["kind"]), None)
        if nr:
            db.ex("UPDATE stale_items SET refreshed_id=? WHERE event_id=? AND item_type='report' AND item_id=?",
                  (nr["id"], eid, old["id"]))
    audit.handoff(AGENT, "reporting", f"{eid} stale reports", len(reports))

    actions = _draft_actions(eid, wbs, ms, risks)
    impact = {
        "event": {"id": eid, "title": ev["title"], "date": ev["date"], "source": ev["source"]},
        "tags": sorted(tags),
        "affected_wbs": [{"code": w["code"], "name": w["name"]} for w in wbs],
        "affected_deliverables": dels,
        "affected_milestones": [{"id": m["id"], "name": m["name"]} for m in ms],
        "downstream_milestones": downstream,
        "affected_risks": [{"id": r["id"], "score": r["score"], "description": r["description"]} for r in risks],
        "stale": [{"type": t, "id": i, "reason": why} for (t, i, why) in stale],
        "regenerated": [n["id"] + f" ({n['status']})" for n in new_reports] + [f"what-if {w['id']}" for w in whatifs],
        "cost_time": cost, "decisions": decisions, "unresolved": unresolved,
        "actions": [a["id"] for a in actions],
    }
    impact["narrative"] = _llm_narrative(eid, impact)
    db.ex("UPDATE change_events SET impact=? WHERE id=?", (db.J(impact), eid))
    audit.log(AGENT, "change impact note drafted", "change_event", eid,
              detail={"stale": len(stale), "actions": len(actions), "decisions": len(decisions)})
    return impact


def _llm_narrative(eid, impact):
    if not llm.available():
        return None
    srcs = [eid, "EDC-5.1", "EDC-6.5", "EDC-4.4", "NRF-T2", "EDC-1.2", "PR3-3"]
    ctx = "\n".join(f"[{s}] {sources.get(s)['text']}" for s in srcs if sources.get(s))
    facts = "\n".join(f"- {c['text']}" for c in impact["cost_time"])
    sysmsg = next(a for a in AGENT_CARDS if a["id"] == AGENT)["system_prompt"]
    text, _ = llm.chat(AGENT, sysmsg, f"SOURCES:\n{ctx}\n\nFACTS:\n{facts}\n\nWrite a 4-sentence impact summary for the Finance Manager.",
                       max_tokens=350)
    if not text:
        return None
    probs = critic.trace_claim({"text": text, "cites": srcs + ["F21", "F38", "F39", "F25", "F14", "F45", "F70"],
                                "calc": [c for x in impact["cost_time"] for c in x.get("calc", [])]})
    if probs:
        audit.log(AGENT, "reject llm narrative", "change_event", eid, outcome="rejected", detail={"problems": probs[:5]})
        return {"text": None, "rejected": probs[:5]}
    return {"text": text}


def _draft_actions(eid, wbs, ms, risks):
    db.ex("DELETE FROM actions WHERE origin=? AND status='pending'", (eid,))
    out = []
    n = 0

    def add(kind, target, payload, why):
        nonlocal n
        n += 1
        aid = f"{eid}-A{n:02d}"
        if db.q1("SELECT id FROM actions WHERE id=?", (aid,)):
            return
        db.ex("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?)",
              (aid, eid, kind, target, db.J(payload), why, "pending", "HC6", db.now(), None))
        out.append({"id": aid})

    for p in risk.rescore_proposals(eid):
        add("risk_rescore", p["risk"], p, p["rationale"])
    keys = [pmtool.ext_key_for("wbs", w["code"]) for w in wbs] + [pmtool.ext_key_for("ms", m["id"]) for m in ms]
    for k in keys:
        add("pm_flag", k, {"text": f"[{eid}] Change event affects this item - see Change Impact Note. "
                                   f"No status change made by the agent.", "add_label": f"change-{eid.lower()}"},
            "Comment + label the affected PM item (no status change)")
    note = {"CE-01": ("MS14", "AT RISK (CE-01): asbestos cost ineligible; extension of time not agreed."),
            "CE-02": ("MS12", "AT RISK (CE-02): no AAC operator; T2 needs ALL operator agreements.")}.get(eid)
    if note:
        add("milestone_note", note[0], {"append": note[1]}, "Keep the milestone plan current")
    gap = {"CE-01": ("GQ09", "Asbestos removal is NOT eligible cost (CE-01)."),
           "CE-02": ("GQ04", "Sole AAC EOI respondent withdrew (CE-02); appointment date unknown.")}.get(eid)
    if gap:
        add("assumption_update", gap[0], {"append": gap[1]}, "Update the assumption register")
    return out


def approve_action(aid, approver, decision, comment=""):
    a = db.q1("SELECT * FROM actions WHERE id=?", (aid,))
    if not a or a["status"] != "pending":
        raise ValueError("action not pending")
    audit.record_approval("HC6", "action", aid, approver, decision, comment)
    if decision == "rejected":
        db.ex("UPDATE actions SET status='rejected' WHERE id=?", (aid,))
        return {"id": aid, "status": "rejected"}
    p = db.L(a["payload"], {})
    result = "applied"
    try:
        if a["kind"] == "risk_rescore":
            risk.apply_rescore(a["origin"], p)
            for r in db.q("SELECT id FROM reports WHERE status IN ('critic_passed','critic_stopped') AND planted IS NULL"):
                db.ex("UPDATE reports SET status='stale' WHERE id=?", (r["id"],))
                db.ex("INSERT INTO stale_items(event_id,item_type,item_id,reason) VALUES(?,?,?,?)",
                      (a["origin"], "report", r["id"], f"risk {p['risk']} re-scored by approved action {aid}"))
            reporting.run_all(use_llm=llm.available(), event_id=a["origin"])
        elif a["kind"] == "pm_flag":
            pm = pmtool.backend()
            rem = pm.find_by_ext(a["target"])
            if not rem:
                result = "skipped: item not on board (run Tool sync first)"
            else:
                pm.comment(rem[0]["key"], p["text"], actor=AGENT)
                labels = sorted(set(rem[0]["labels"]) | {p["add_label"]})
                pm.update(rem[0]["key"], {"labels": labels}, actor=AGENT)
        elif a["kind"] == "milestone_note":
            m = db.q1("SELECT note FROM milestones WHERE id=?", (a["target"],))
            if p["append"] not in m["note"]:
                db.ex("UPDATE milestones SET note=? WHERE id=?", ((m["note"] + " | " if m["note"] else "") + p["append"], a["target"]))
            audit.log(AGENT, "milestone note updated (approved)", "milestone", a["target"], detail=p)
        elif a["kind"] == "assumption_update":
            g = db.q1("SELECT answer FROM gaps WHERE id=?", (a["target"],))
            if p["append"] not in (g["answer"] or ""):
                db.ex("UPDATE gaps SET answer=?, answer_sources=? WHERE id=?",
                      (((g["answer"] or "") + " | " + p["append"]).strip(" |"),
                       db.J(sorted(set(db.L(db.q1('SELECT answer_sources FROM gaps WHERE id=?', (a['target'],))['answer_sources']) + [a["origin"]]))),
                       a["target"]))
            audit.log(AGENT, "assumption register updated (approved)", "gap", a["target"], detail=p)
    except pmtool.GuardrailViolation as e:
        result = f"blocked: {e}"
    db.ex("UPDATE actions SET status=?, applied_at=? WHERE id=?", ("applied" if result == "applied" else result, db.now(), aid))
    return {"id": aid, "status": result}


def impact_note_md(eid):
    ev = db.q1("SELECT * FROM change_events WHERE id=?", (eid,))
    imp = db.L(ev["impact"], {})
    L = [f"# Change Impact Note - {eid}: {ev['title']}", f"Event date {ev['date']} · source: {ev['source']}", "",
         f"> {ev['text']}", "", "## Affected work"]
    L += [f"- WBS {w['code']} {w['name']}" for w in imp.get("affected_wbs", [])]
    L += [f"- Deliverables: {', '.join(imp.get('affected_deliverables', [])) or 'none'}",
          f"- Milestones: {', '.join(m['id'] for m in imp.get('affected_milestones', []))}; downstream: {', '.join(imp.get('downstream_milestones', [])) or 'none'}",
          f"- Risks: {', '.join(r['id'] for r in imp.get('affected_risks', []))}", "", "## Now stale"]
    L += [f"- {s['type']} {s['id']}: {s['reason']}" for s in imp.get("stale", [])]
    L += ["", "## Cost and time impact"]
    L += [f"- {c['text']} [{', '.join(c['cites'])}]" for c in imp.get("cost_time", [])]
    L += ["", "## Regenerated automatically (drafts)"] + [f"- {r}" for r in imp.get("regenerated", [])]
    L += ["", "## Sponsor decisions needed"]
    L += [f"- {d['what']} - WHO: {d['who']} - WHEN: {d['when']} [{', '.join(d['sources'])}]" for d in imp.get("decisions", [])]
    L += ["", "## UNRESOLVED"] + [f"- {u['item']} [{', '.join(u['sources'])}]" for u in imp.get("unresolved", [])]
    L += ["", "## Actions awaiting HC6"]
    L += [f"- {a['id']} {a['kind']} -> {a['target']} ({a['status']})" for a in db.q("SELECT * FROM actions WHERE origin=? ORDER BY id", (eid,))]
    return "\n".join(L)
