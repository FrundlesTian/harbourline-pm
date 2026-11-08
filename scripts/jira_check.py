"""Read-only Jira Cloud connection check. Writes nothing to Jira.
    python3 scripts/jira_check.py"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HCH_DB", str(Path(tempfile.mkdtemp(prefix="hch-jira-check-")) / "check.db"))

from app import config, pmtool  # noqa: E402

if config.JIRA_MISSING:
    sys.exit(f"Jira not configured: set {', '.join(config.JIRA_MISSING)} in .env")
h = pmtool.health()
h.pop("email", None)
print(json.dumps(h, indent=2, ensure_ascii=False))
if not h["ok"]:
    sys.exit(1)
bad = [k for k, v in h["type_mapping"].items() if v.startswith("MISSING")]
if bad or not h["blocks_link_type"]:
    sys.exit(f"Project is reachable but not ready: missing issue types {bad} / Blocks link type {h['blocks_link_type']}")
board = pmtool.backend().list_all()
print(f"OK - {len(board)} ai-generated items currently in {config.JIRA_PROJECT_KEY}")
