"""Orchestrator. A full run chains Planning -> Risk -> Governance (bias) -> Reporting ->
Critic with machine hand-offs (logged in `handoffs`). Human checkpoints sit between
the chain and anything a stakeholder or the PM tool sees."""
import hashlib
import time

from . import audit, config, db, facts_catalog, governance, llm, memory, planning, reporting, risk, sources


def init():
    n = sources.ingest()
    f = facts_catalog.load()
    memory.restore_decisions()
    for e in db.q("SELECT * FROM change_events"):
        sources.add_source(e["id"], f"Change event {e['id']} ({e['source']})", f"{e['id']} dated {e['date']}", e["text"], "change")
    audit.log("orchestrator", "ingest", "sources", "pack", detail={"chunks": n, "facts": f["loaded"],
                                                                 "facts_rejected": len(f["rejected"])}, actor_type="system")
    return {"chunks": n, "facts": f["loaded"], "facts_rejected": f["rejected"]}


def full_run(use_llm=True, as_of="2027-03-31"):
    t0 = time.time()
    with audit.Run("full") as run:
        out = {"planning": planning.run()}
        out["risk"] = risk.run()
        governance.bias_check()
        out["reports"] = [{"id": r["id"], "status": r["status"]} for r in reporting.run_all(as_of, use_llm and llm.available())]
        out["seconds"] = round(time.time() - t0, 3)
        out["llm"] = llm.available() and use_llm
        run["summary"] = out
    out["run_id"] = run["id"]
    out["tokens_in"], out["tokens_out"], out["cost_usd"] = run["tokens_in"], run["tokens_out"], round(run["cost_usd"], 6)
    return out


def risk_hash():
    rows = db.q("SELECT id,likelihood,impact,score,owner,trigger_cond,wbs_links FROM risks ORDER BY id")
    return hashlib.sha256(db.J(rows).encode()).hexdigest()[:12]


def gaps_hash():
    rows = db.q("SELECT id,question,status,answer FROM gaps ORDER BY id")
    return hashlib.sha256(db.J(rows).encode()).hexdigest()[:12]


def status():
    def n(t, w=""):
        return db.q1(f"SELECT COUNT(*) c FROM {t} {w}")["c"]
    ph = planning.plan_hash() if n("wbs") else None
    return {
        "llm": llm.available(),
        "pm_backend": config.PM_BACKEND,
        "counts": {"sources": n("sources"), "facts": n("facts"), "gaps": n("gaps"), "conflicts": n("conflicts"),
                   "wbs": n("wbs"), "milestones": n("milestones"), "risks": n("risks"), "whatifs": n("whatifs"),
                   "reports": n("reports", "WHERE planted IS NULL"), "pm_issues": n("pm_issues"),
                   "audit": n("audit_log"), "approvals": n("approvals"), "change_events": n("change_events"),
                   "pending_actions": n("actions", "WHERE status='pending'")},
        "checkpoints": {
            "HC1": audit.is_approved("HC1", "gaps", gaps_hash()) if n("gaps") else False,
            "HC2": audit.is_approved("HC2", "plan", ph) if ph else False,
            "HC4": audit.is_approved("HC4", "risk_register", risk_hash()) if n("risks") else False,
            "HC7": (db.q1("SELECT status FROM bias_checks WHERE id='BIAS-1'") or {}).get("status"),
        },
        "plan_hash": ph, "risk_hash": risk_hash() if n("risks") else None, "gaps_hash": gaps_hash() if n("gaps") else None,
        "handoffs": db.q("SELECT * FROM handoffs ORDER BY id DESC LIMIT 12"),
        "runs": db.q("SELECT * FROM runs ORDER BY started DESC LIMIT 8"),
    }


def reset_demo():
    """Clear outputs, board and events for a clean demo. Audit log, approvals and the
    decision log are governance records and are never erased."""
    db.wipe_outputs()
    for t in ("pm_issues", "pm_sync_map", "change_events", "actions", "reports", "risks", "whatifs", "qa_log"):
        db.ex(f"DELETE FROM {t}")
    db.ex("DELETE FROM sources WHERE kind='change'")
    sources.INDEX.invalidate()
    audit.log("orchestrator", "demo reset (outputs cleared; audit + approvals kept)", "system", "reset", actor_type="system")
