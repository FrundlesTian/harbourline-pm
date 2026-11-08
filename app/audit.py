"""Governance layer primitives: audit log, named human checkpoints, approvals,
module hand-off log and run accounting."""
import contextvars
import re
import time
import uuid

from . import db

CURRENT_RUN = contextvars.ContextVar("current_run", default=None)
# The logged-in account behind the current HTTP request (set by the server).
CURRENT_USER = contextvars.ContextVar("current_user", default=None)

# Named human checkpoints. Designed in, not discovered: every agent output that
# reaches a stakeholder or the PM tool passes one of these.
CHECKPOINTS = {
    "HC1": {"name": "Scope statement & Sponsor Questions sign-off",
            "role": "Team PM lead", "gates": "Planning -> sponsor channel / assumption register"},
    "HC2": {"name": "WBS, dictionary & milestone plan baseline approval",
            "role": "Team PM lead", "gates": "Planning -> Tool integration"},
    "HC3": {"name": "PM tool write confirmation (diff preview)",
            "role": "Tool integration owner", "gates": "Tool integration -> Jira/mock board writes"},
    "HC4": {"name": "Risk register & what-if publication",
            "role": "Risk owner (team)", "gates": "Risk -> reports / PM tool"},
    "HC5": {"name": "Report release after Critic pass",
            "role": "Reporting owner (team)", "gates": "Reporting -> EDC / NRF readers"},
    "HC6": {"name": "Change-impact actions approval",
            "role": "Team PM lead", "gates": "Change agent -> plan, register, PM tool"},
    "HC7": {"name": "Bias & fairness sign-off on consultation summary",
            "role": "Governance lead", "gates": "Consultation summary -> design input / reports"},
}

_TOKEN_PAT = re.compile(r"(ATATT[0-9A-Za-z_\-=]+|sk-[0-9A-Za-z]{16,}|Bearer\s+\S+|Basic\s+\S+)")


def redact(text):
    """Belt and braces: never let something that looks like a token reach the log."""
    if text is None:
        return text
    return _TOKEN_PAT.sub("[REDACTED]", str(text))


def log(actor, action, target_type="", target_id="", outcome="ok", detail=None,
        actor_type="agent"):
    run = CURRENT_RUN.get()
    db.ex("INSERT INTO audit_log(ts,run_id,actor,actor_type,action,target_type,target_id,outcome,detail)"
          " VALUES(?,?,?,?,?,?,?,?,?)",
          (db.now(), run["id"] if run else None, actor, actor_type, action, target_type,
           str(target_id), outcome, redact(db.J(detail) if detail is not None else "")))


def handoff(from_agent, to_agent, payload_ref, items):
    """Record a machine-to-machine hand-off (no human copy/paste)."""
    run = CURRENT_RUN.get()
    db.ex("INSERT INTO handoffs(ts,run_id,from_agent,to_agent,payload_ref,items) VALUES(?,?,?,?,?,?)",
          (db.now(), run["id"] if run else None, from_agent, to_agent, payload_ref, items))
    log(from_agent, "handoff", "agent", to_agent, detail={"payload": payload_ref, "items": items})


def record_approval(checkpoint, item_type, item_id, approver, decision, comment=""):
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"Unknown checkpoint {checkpoint}")
    if not approver or not approver.strip():
        raise ValueError("A named human approver is required")
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be approved|rejected")
    role = CHECKPOINTS[checkpoint]["role"]
    user = CURRENT_USER.get()
    db.ex("INSERT INTO approvals(checkpoint,item_type,item_id,approver,role,decision,comment,ts,account,account_role)"
          " VALUES(?,?,?,?,?,?,?,?,?,?)",
          (checkpoint, item_type, str(item_id), approver.strip(), role, decision, comment, db.now(),
           user["username"] if user else None, user["role"] if user else None))
    log(approver.strip(), f"checkpoint {checkpoint} {decision}", item_type, item_id,
        detail={"comment": comment, "checkpoint": CHECKPOINTS[checkpoint]["name"]},
        actor_type="human")


def is_approved(checkpoint, item_type, item_id):
    r = db.q1("SELECT decision FROM approvals WHERE checkpoint=? AND item_type=? AND item_id=?"
              " ORDER BY id DESC LIMIT 1", (checkpoint, item_type, str(item_id)))
    return bool(r and r["decision"] == "approved")


def latest_approval(checkpoint, item_type, item_id):
    return db.q1("SELECT * FROM approvals WHERE checkpoint=? AND item_type=? AND item_id=?"
                 " ORDER BY id DESC LIMIT 1", (checkpoint, item_type, str(item_id)))


class Run:
    """Context manager that times a run and accumulates LLM token usage."""

    def __init__(self, kind):
        self.kind = kind
        self.rec = {"id": f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}",
                    "kind": kind, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0,
                    "llm_calls": 0}

    def __enter__(self):
        self.t0 = time.time()
        self.token = CURRENT_RUN.set(self.rec)
        db.ex("INSERT INTO runs(id,kind,started) VALUES(?,?,?)", (self.rec["id"], self.kind, db.now()))
        log("orchestrator", f"run start: {self.kind}", "run", self.rec["id"], actor_type="system")
        return self.rec

    def __exit__(self, et, ev, tb):
        secs = round(time.time() - self.t0, 3)
        r = self.rec
        db.ex("UPDATE runs SET ended=?, seconds=?, tokens_in=?, tokens_out=?, cost_usd=?, llm_calls=?,"
              " summary=? WHERE id=?",
              (db.now(), secs, r["tokens_in"], r["tokens_out"], round(r["cost_usd"], 6),
               r["llm_calls"], db.J(r.get("summary", {})), r["id"]))
        log("orchestrator", f"run end: {self.kind}", "run", r["id"],
            outcome="error" if et else "ok",
            detail={"seconds": secs, "error": str(ev) if ev else None}, actor_type="system")
        CURRENT_RUN.reset(self.token)
        return False
