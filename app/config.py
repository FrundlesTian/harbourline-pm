"""Central configuration. Secrets come ONLY from environment variables or a local .env
file that is git-ignored. Tokens are never written to the database, audit log or UI."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PACK = ROOT / "data_pack"
CHANGE_EVENTS = ROOT / "change_events"
DB_PATH = Path(os.environ.get("HCH_DB", ROOT / "data" / "harbourline.db"))
STATIC = ROOT / "static"


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

# --- LLM (DeepSeek, OpenAI-compatible) ---------------------------------------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
# USD per 1M tokens. Check DeepSeek's current price page and override in .env.
PRICE_IN_PER_M = float(os.environ.get("DEEPSEEK_PRICE_IN_PER_M", "0.28"))
PRICE_OUT_PER_M = float(os.environ.get("DEEPSEEK_PRICE_OUT_PER_M", "0.42"))
LLM_DISABLED = os.environ.get("HCH_DISABLE_LLM", "") == "1"

# --- PM tool -----------------------------------------------------------------
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")   # https://<site>.atlassian.net
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "HCH")
PM_BACKEND = os.environ.get("PM_BACKEND", "jira" if (JIRA_BASE_URL and JIRA_API_TOKEN) else "mock")

EXT_KEY_PREFIX = "ext-HCH-"          # stable external key label prefix
AI_LABEL = "ai-generated"            # guardrail: every agent-created item carries this

# Report "as of" date for the data pack (pack covers Jan-Mar 2027)
DEFAULT_AS_OF = "2027-03-31"

HOST = os.environ.get("HCH_HOST", "127.0.0.1")
PORT = int(os.environ.get("HCH_PORT", "8000"))
