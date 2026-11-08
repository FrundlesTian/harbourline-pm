"""Aggregates for the visual dashboard and the admin demo walkthrough.
Every section is gated by the caller's role: a section the role may not view is
omitted from the payload, not merely hidden in the UI."""
from collections import Counter

from . import audit, auth, config, db, pipeline, planning

# The eight-step demo path from the README, with the role that owns each step.
DEMO_STEPS = [
    ("S1", "Run the full pipeline", "overview", "project_manager", None),
    ("S2", "Approve gaps register and plan baseline", "planning", "project_manager", "HC1 · HC2"),
    ("S3", "Preview, approve and write the PM board", "pm", "project_manager", "HC3"),
    ("S4", "Ask memory questions (one NOT FOUND)", "memory", "group_leader", None),
    ("S5", "Approve the risk register", "risk", "group_leader", "HC4"),
    ("S6", "Plant a fault, then release a clean report", "reports", "group_leader", "HC5"),
    ("S7", "Inject a change event and clear HC6 actions", "change", "project_manager", "HC6"),
    ("S8", "Sign off the bias check and export the audit", "governance", "supervisor", "HC7"),
]


def _n(sql, args=()):
    return db.q1(sql, args)["c"]


def _demo_progress(cp):
    exported = _n("SELECT COUNT(*) c FROM audit_log WHERE action='audit exported'")
    done = {
        "S1": _n("SELECT COUNT(*) c FROM runs WHERE kind='full' AND ended IS NOT NULL") > 0,
        "S2": cp["HC1"]["state"] == "approved" and cp["HC2"]["state"] == "approved",
        "S3": _n("SELECT COUNT(*) c FROM pm_issues") > 0,
        "S4": _n("SELECT COUNT(*) c FROM qa_log") > 0,
        "S5": cp["HC4"]["state"] == "approved",
        "S6": _n("SELECT COUNT(*) c FROM reports WHERE status='released'") > 0,
        "S7": _n("SELECT COUNT(*) c FROM change_events") > 0 and _n("SELECT COUNT(*) c FROM actions WHERE status='pending'") == 0,
        "S8": cp["HC7"]["state"] == "approved",
    }
    detail = {
        "S1": f"{_n('SELECT COUNT(*) c FROM runs')} runs",
        "S3": f"{_n('SELECT COUNT(*) c FROM pm_issues')} board items",
        "S4": f"{_n('SELECT COUNT(*) c FROM qa_log')} questions, {_n('SELECT COUNT(*) c FROM qa_log WHERE not_found=1')} NOT FOUND",
        "S6": f"{_n('SELECT COUNT(*) c FROM reports WHERE planted IS NOT NULL')} planted, "
              f"{_n('SELECT COUNT(*) c FROM reports WHERE status=?', ('released',))} released",
        "S7": f"{_n('SELECT COUNT(*) c FROM change_events')} events, "
              f"{_n('SELECT COUNT(*) c FROM actions WHERE status=?', ('pending',))} pending",
        "S8": f"{exported} audit exports",
    }
    return [{"id": i, "title": t, "tab": tab, "owner": owner, "owner_label": auth.ROLES[owner]["label"],
             "checkpoint": hc, "done": done[i], "detail": detail.get(i, "")}
            for i, t, tab, owner, hc in DEMO_STEPS]


def _checkpoints():
    """Current state of each checkpoint: approved / rejected / pending / n/a."""
    gh = pipeline.gaps_hash() if _n("SELECT COUNT(*) c FROM gaps") else None
    ph = planning.plan_hash() if _n("SELECT COUNT(*) c FROM wbs") else None
    rh = pipeline.risk_hash() if _n("SELECT COUNT(*) c FROM risks") else None

    def latest(cp, typ, item):
        a = audit.latest_approval(cp, typ, item) if item else None
        return a

    def st(a, has_item=True):
        if not has_item:
            return "n/a"
        return a["decision"] if a else "pending"

    out = {}
    for cp, typ, item in (("HC1", "gaps", gh), ("HC2", "plan", ph), ("HC4", "risk_register", rh), ("HC7", "bias_check", "BIAS-1")):
        has = bool(item) and (cp != "HC7" or bool(db.q1("SELECT 1 FROM bias_checks WHERE id='BIAS-1'")))
        a = latest(cp, typ, item) if has else None
        out[cp] = {"state": st(a, has), "by": a and a["approver"], "ts": a and a["ts"]}
    # HC3: latest sync preview approved?  HC5: any release?  HC6: pending actions?
    a3 = db.q1("SELECT * FROM approvals WHERE checkpoint='HC3' ORDER BY id DESC LIMIT 1")
    out["HC3"] = {"state": a3["decision"] if a3 else ("pending" if ph else "n/a"), "by": a3 and a3["approver"], "ts": a3 and a3["ts"]}
    a5 = db.q1("SELECT * FROM approvals WHERE checkpoint='HC5' ORDER BY id DESC LIMIT 1")
    passed = _n("SELECT COUNT(*) c FROM reports WHERE status='critic_passed' AND planted IS NULL")
    out["HC5"] = {"state": "pending" if passed else (a5["decision"] if a5 else "n/a"), "by": a5 and a5["approver"],
                  "ts": a5 and a5["ts"], "waiting": passed}
    pend = _n("SELECT COUNT(*) c FROM actions WHERE status='pending'")
    a6 = db.q1("SELECT * FROM approvals WHERE checkpoint='HC6' ORDER BY id DESC LIMIT 1")
    out["HC6"] = {"state": "pending" if pend else (a6["decision"] if a6 else "n/a"), "by": a6 and a6["approver"],
                  "ts": a6 and a6["ts"], "waiting": pend}
    for k, v in out.items():
        v.update(id=k, name=audit.CHECKPOINTS[k]["name"], role=audit.CHECKPOINTS[k]["role"],
                 owner_roles=[r for r, d in auth.ROLES.items() if k in d["checkpoints"] and r != "admin"],
                 approvals=_n("SELECT COUNT(*) c FROM approvals WHERE checkpoint=?", (k,)))
    return out


def build(user):
    v = lambda tab: auth.can(user, "view." + tab)   # noqa: E731
    cp = _checkpoints()
    out = {"role": user["role"], "checkpoints": cp,
           "kpis": {"facts": _n("SELECT COUNT(*) c FROM facts"), "wbs": _n("SELECT COUNT(*) c FROM wbs"),
                    "risks": _n("SELECT COUNT(*) c FROM risks"),
                    "reports": _n("SELECT COUNT(*) c FROM reports WHERE planted IS NULL"),
                    "pending_actions": _n("SELECT COUNT(*) c FROM actions WHERE status='pending'"),
                    "approvals": _n("SELECT COUNT(*) c FROM approvals"),
                    "open_gaps": _n("SELECT COUNT(*) c FROM gaps WHERE status='Open'"),
                    "blocked": _n("SELECT COUNT(*) c FROM audit_log WHERE outcome IN ('blocked','rejected')")},
           "flow": {
               "sources": _n("SELECT COUNT(*) c FROM sources"), "facts": _n("SELECT COUNT(*) c FROM facts"),
               "planning": {"wbs": _n("SELECT COUNT(*) c FROM wbs"), "gaps": _n("SELECT COUNT(*) c FROM gaps"),
                            "milestones": _n("SELECT COUNT(*) c FROM milestones")},
               "pm": {"issues": _n("SELECT COUNT(*) c FROM pm_sync_map WHERE backend=?", (config.PM_BACKEND,))
                      if config.PM_BACKEND == "jira" else _n("SELECT COUNT(*) c FROM pm_issues"),
                      "backend": config.PM_BACKEND, "project": config.JIRA_PROJECT_KEY},
               "memory": {"questions": _n("SELECT COUNT(*) c FROM qa_log"), "decisions": _n("SELECT COUNT(*) c FROM decisions")},
               "risk": {"risks": _n("SELECT COUNT(*) c FROM risks"), "whatifs": _n("SELECT COUNT(*) c FROM whatifs"),
                        "stale": _n("SELECT COUNT(*) c FROM risks WHERE stale=1")},
               "reports": {r["status"]: r["c"] for r in db.q("SELECT status, COUNT(*) c FROM reports WHERE planted IS NULL GROUP BY status")},
               "critic_stops": _n("SELECT COUNT(*) c FROM reports WHERE status='critic_stopped'"),
               "change": {"events": _n("SELECT COUNT(*) c FROM change_events"),
                          "pending": _n("SELECT COUNT(*) c FROM actions WHERE status='pending'"),
                          "stale": _n("SELECT COUNT(*) c FROM stale_items")},
               "bias": (db.q1("SELECT status FROM bias_checks WHERE id='BIAS-1'") or {}).get("status"),
               "handoffs": db.q("SELECT from_agent, to_agent, COUNT(*) n, SUM(items) items FROM handoffs GROUP BY from_agent, to_agent"),
           }}
    if v("planning"):
        out["gaps"] = {r["status"]: r["c"] for r in db.q("SELECT status, COUNT(*) c FROM gaps GROUP BY status")}
        out["milestones"] = [dict(m, depends_on=db.L(m["depends_on"]))
                             for m in db.q("SELECT id,name,wbs_code,rel_month,date,depends_on,note FROM milestones ORDER BY sort")]
        out["wbs_levels"] = {str(r["level"]): r["c"] for r in db.q("SELECT level, COUNT(*) c FROM wbs GROUP BY level")}
    if v("risk"):
        out["risks"] = db.q("SELECT id,category,description,owner,likelihood,impact,score,status,stale FROM risks ORDER BY score DESC, id")
    if v("pm"):
        out["pm_status"] = {r["status"]: r["c"] for r in db.q("SELECT status, COUNT(*) c FROM pm_issues GROUP BY status")}
    if auth.can(user, "audit.view"):
        out["audit"] = db.q("SELECT ts, actor_type, outcome FROM audit_log ORDER BY id DESC LIMIT 3000")
        out["approvals_by"] = db.q("SELECT checkpoint, decision, COUNT(*) c FROM approvals GROUP BY checkpoint, decision")
        out["denied"] = db.q("SELECT actor, COUNT(*) c FROM audit_log WHERE action LIKE 'access denied%' GROUP BY actor")
    if user["role"] == "admin":
        out["demo"] = _demo_progress(cp)
        out["users_by_role"] = dict(Counter(r["role"] for r in db.q("SELECT role FROM users WHERE active=1")))
    return out
