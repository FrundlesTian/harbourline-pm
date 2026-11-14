"""Offline check of the start-screen Reset demo -> evidence for the Governance Log.

    python3 scripts/reset_check.py [out_file]   (default: docs/governance/evidence/reset_check.json)

Runs on a THROW-AWAY database in baseline mode against the local mock board; Jira credentials
are blanked, so no Jira issue can be touched. It syncs the plan once (HC2 + HC3), then calls the
same server handlers as the start screen: a wrong confirmation, a stale preview id, and a valid
reset. It records what each returns and which tables survive."""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["HCH_DB"] = str(Path(tempfile.mkdtemp(prefix="hch-reset-")) / "reset.db")
os.environ["HCH_GENERATION"] = "baseline"
os.environ["HCH_DISABLE_LLM"] = "1"
os.environ["PM_BACKEND"] = "mock"
for key in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
    os.environ[key] = ""

import server  # noqa: E402
from app import audit, auth, config, db, pipeline, pmtool  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "governance" / "evidence" / "reset_check.json"
TABLES = ("pm_issues", "approvals", "decisions", "audit_log", "users")


def counts():
    return {t: db.q1(f"SELECT COUNT(*) c FROM {t}")["c"] for t in TABLES}


def main():
    pipeline.init()
    auth.ensure_seed()
    pipeline.full_run(use_llm=False)
    audit.CURRENT_USER.set(auth.public(db.q1("SELECT * FROM users WHERE username='pm'")))
    server.api_approve({}, {"checkpoint": "HC2", "decision": "approved", "comment": "reset check"})
    preview = pmtool.preview()
    server.api_approve({}, {"checkpoint": "HC3", "decision": "approved", "item_id": preview["preview_id"]})
    pmtool.apply(preview["preview_id"])
    audit.CURRENT_USER.set(None)          # the start screen has no session

    out = {"mode": "baseline (no LLM), mock board, Jira credentials blanked",
           "jira_reset_enabled": pmtool.reset_jira_available(), "before": counts()}
    snap, _ = server.reset_snapshot()
    out["preview"] = {k: snap[k] for k in ("jira_enabled", "jira_count", "mock_count", "confirm_text")}
    out["wrong_confirmation"] = server.api_restore_initial({}, {"confirm": "WRONG", "preview_id": snap["preview_id"]})
    out["stale_preview_id"] = server.api_restore_initial({}, {"confirm": snap["confirm_text"], "preview_id": "0" * 16})
    code, res = server.api_restore_initial({}, {"confirm": snap["confirm_text"], "preview_id": snap["preview_id"]})
    out["valid_reset"] = [code, {k: res.get(k) for k in ("reset", "jira_deleted")}]
    out["after"] = counts()
    out["audit_log_kept"] = out["after"]["audit_log"] >= out["before"]["audit_log"]
    out["reset_audit_rows"] = db.q("SELECT actor, actor_type, action, outcome FROM audit_log "
                                   "WHERE target_type='system' AND target_id='reset'")
    out["generated"] = db.now()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
