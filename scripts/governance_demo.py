"""Governance demonstration run -> exports for the Governance Log.

    python3 scripts/governance_demo.py [out_dir]      (default: docs/governance/evidence)

Runs one end-to-end session on a THROW-AWAY database: deterministic baseline mode (no LLM
calls, no cost), local mock board (never Jira). Every approval goes through the same
server handler the UI uses (`server.api_approve`), signed by the seeded role accounts
(project_manager / group_leader / supervisor), so RBAC and approval signing are exercised
exactly as in the app. Approvals here are DEMONSTRATION decisions by role accounts, not the
team's real decisions.

Writes: audit_log.csv (all rows), agent_writes.csv (agent write actions only),
approvals.csv, bias_check.json, change_impact_CE-01.md, summary.json."""
import csv
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["HCH_DB"] = str(Path(tempfile.mkdtemp(prefix="hch-gov-")) / "gov.db")
os.environ["HCH_GENERATION"] = "baseline"
os.environ["HCH_DISABLE_LLM"] = "1"
os.environ["PM_BACKEND"] = "mock"

import server  # noqa: E402
from app import audit, auth, change, db, governance, pipeline, pmtool, reporting  # noqa: E402
from eval import faults  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "governance" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
DEMO = "Demonstration run (scripted) - "


def as_user(username):
    u = db.q1("SELECT * FROM users WHERE username=?", (username,))
    audit.CURRENT_USER.set(auth.public(u))


def approve(username, cp, decision="approved", item=None, comment=""):
    as_user(username)
    code, res = server.api_approve({}, {"checkpoint": cp, "decision": decision, "item_id": item,
                                        "comment": DEMO + comment})
    return res


def main():
    pipeline.init()
    auth.ensure_seed()
    summary = {"mode": "baseline (no LLM), mock board", "steps": []}
    step = summary["steps"].append

    run = pipeline.full_run(use_llm=False)
    step({"full_run": {k: run[k] for k in ("seconds", "tokens_in", "tokens_out", "cost_usd")},
          "reports": run["reports"]})

    # RBAC: a role that does not own a checkpoint is refused before anything is recorded
    try:
        approve("leader", "HC2", comment="should be refused")
        step({"rbac": "group_leader approving HC2 was NOT refused"})
    except auth.Forbidden as e:
        step({"rbac_refused": f"group_leader -> HC2: {e}"})   # auth.require logs 'access denied'

    approve("pm", "HC1", comment="scope and Sponsor Questions reviewed")
    approve("pm", "HC2", comment="WBS, dictionary and milestones baselined")
    as_user("pm")
    p = pmtool.preview()
    approve("pm", "HC3", item=p["preview_id"], comment=f"sync preview {p['counts']}")
    sync1 = pmtool.apply(p["preview_id"])
    p2 = pmtool.preview()
    approve("pm", "HC3", item=p2["preview_id"], comment="re-sync to show idempotency")
    sync2 = pmtool.apply(p2["preview_id"])
    step({"pm_sync_1": {k: sync1[k] for k in ("created", "updated", "unchanged")},
          "pm_sync_2": {k: sync2[k] for k in ("created", "updated", "unchanged")},
          "readback_verified": sync2["readback"]["verified"]})

    approve("leader", "HC4", comment="risk register and what-ifs reviewed")

    # Guardrail: agent attempts to close / delete / move to Done
    key = pmtool.board()[0]["key"]
    blocked = []
    for op in ("close", "delete", "done"):
        code, res = server.api_pm_agent_attempt({}, {"op": op, "key": key})
        blocked.append((op, res["blocked"]))
    step({"agent_guardrail_attempts": blocked})

    # HC5: a Critic-stopped draft cannot be released; a passed draft can
    bad = reporting.generate("nrf", use_llm=False, mutate=faults.FAULTS["invented_figure"])
    try:
        approve("leader", "HC5", item=bad["id"], comment="attempt to release a planted-fault draft")
        step({"hc5_planted": "released (unexpected)"})
    except ValueError as e:
        step({"hc5_planted_refused": str(e)})
    live = db.q("SELECT id FROM reports WHERE planted IS NULL AND status='critic_passed' ORDER BY id")
    approve("leader", "HC5", item=live[0]["id"], comment="EDC update released after Critic PASS")

    # Week 12 change event (CE-01 used for the demonstration)
    as_user("pm")
    imp = change.inject("CE-01")
    acts = db.q("SELECT * FROM actions WHERE origin='CE-01' ORDER BY id")
    done = []
    for a in acts:
        if a["kind"] == "risk_rescore" and not any(d[1] == "risk_rescore" for d in done):
            approve("pm", "HC6", item=a["id"], comment="re-score accepted")
            done.append((a["id"], a["kind"], "approved"))
        elif a["kind"] == "pm_flag" and not any(d[1] == "pm_flag" for d in done):
            approve("pm", "HC6", item=a["id"], comment="comment + label the affected PM item")
            done.append((a["id"], a["kind"], "approved"))
        elif a["kind"] == "milestone_note":
            approve("pm", "HC6", decision="rejected", item=a["id"], comment="wording to be agreed with the sponsor first")
            done.append((a["id"], a["kind"], "rejected"))
    step({"CE-01": {"stale": len(imp["stale"]), "decisions": len(imp["decisions"]), "actions": len(acts),
                    "hc6_decisions": done, "pending_left": db.q1(
                        "SELECT COUNT(*) c FROM actions WHERE origin='CE-01' AND status='pending'")["c"]}})

    governance.bias_check()
    approve("supervisor", "HC7", comment="findings B1-B6 accepted; actions to Community Engagement")

    # exports
    (OUT / "audit_log.csv").write_text(governance.audit_export_csv(), encoding="utf-8")
    (OUT / "approvals.csv").write_text(governance.approvals_export_csv(), encoding="utf-8")
    writes = db.q("SELECT * FROM audit_log WHERE actor_type='agent' AND outcome!='blocked' AND ("
                  "action LIKE 'pm %' OR action LIKE 'write %' OR action LIKE 'mark stale%' OR action LIKE '%updated (approved)'"
                  " OR action LIKE 'risk re-scored%' OR action LIKE 'change impact%' OR action LIKE 'bias%') "
                  "AND action NOT IN ('pm preview (read-only)','pm readback','pm health check') ORDER BY id")
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["id", "ts", "run_id", "actor", "action", "target_type", "target_id", "outcome", "detail"]
    w.writerow(cols)
    for r in writes:
        w.writerow([r[c] for c in cols])
    (OUT / "agent_writes.csv").write_text(buf.getvalue(), encoding="utf-8")
    b = db.q1("SELECT * FROM bias_checks WHERE id='BIAS-1'")
    (OUT / "bias_check.json").write_text(json.dumps({"status": b["status"], **db.L(b["result"], {})},
                                                    indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "change_impact_CE-01.md").write_text(change.impact_note_md("CE-01"), encoding="utf-8")
    summary["counts"] = {
        "audit_rows": db.q1("SELECT COUNT(*) c FROM audit_log")["c"],
        "agent_write_rows": len(writes),
        "blocked_rows": db.q1("SELECT COUNT(*) c FROM audit_log WHERE outcome='blocked'")["c"],
        "approvals": db.q1("SELECT COUNT(*) c FROM approvals")["c"],
        "pm_issues": db.q1("SELECT COUNT(*) c FROM pm_issues")["c"],
        "by_action": {r["action"]: r["c"] for r in db.q(
            "SELECT action, COUNT(*) c FROM audit_log WHERE actor_type='agent' GROUP BY action ORDER BY c DESC")},
    }
    summary["generated"] = db.now()
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str)[:3000])


if __name__ == "__main__":
    main()
