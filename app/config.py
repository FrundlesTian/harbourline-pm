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

# --- LLM providers (OpenAI-compatible chat completions) ------------------------
# Primary: Gemini via Google AI Studio's OpenAI-compatible endpoint (free tier).
# Backup: DeepSeek. A call that fails on one provider is retried on the next one
# (order: HCH_LLM_ORDER). A provider is used only when its API key is set.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# "none" turns off thinking on Flash models so the whole max_tokens budget is answer text;
# set GEMINI_REASONING_EFFORT= (empty) for models that do not accept the parameter.
GEMINI_REASONING_EFFORT = os.environ.get("GEMINI_REASONING_EFFORT", "none").strip()
GEMINI_PRICE_IN_PER_M = float(os.environ.get("GEMINI_PRICE_IN_PER_M", "0"))     # free tier
GEMINI_PRICE_OUT_PER_M = float(os.environ.get("GEMINI_PRICE_OUT_PER_M", "0"))

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
# USD per 1M tokens. Check DeepSeek's current price page and override in .env.
PRICE_IN_PER_M = float(os.environ.get("DEEPSEEK_PRICE_IN_PER_M", "0.28"))
PRICE_OUT_PER_M = float(os.environ.get("DEEPSEEK_PRICE_OUT_PER_M", "0.42"))
LLM_ORDER = [x.strip().lower() for x in os.environ.get("HCH_LLM_ORDER", "gemini,deepseek").split(",") if x.strip()]


def llm_providers():
    """Configured providers in fallback order. Keys stay in memory only."""
    all_ = {
        "gemini": dict(name="gemini", key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL, model=GEMINI_MODEL,
                       price_in=GEMINI_PRICE_IN_PER_M, price_out=GEMINI_PRICE_OUT_PER_M,
                       extra={"reasoning_effort": GEMINI_REASONING_EFFORT} if GEMINI_REASONING_EFFORT else {}),
        "deepseek": dict(name="deepseek", key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, model=DEEPSEEK_MODEL,
                         price_in=PRICE_IN_PER_M, price_out=PRICE_OUT_PER_M, extra={}),
    }
    return [all_[n] for n in LLM_ORDER if n in all_ and all_[n]["key"]]


LLM_DISABLED = os.environ.get("HCH_DISABLE_LLM", "") == "1"
# "llm" (default): when an LLM provider is configured, agents generate their core outputs from the
# sources and deterministic validators check them; the curated baseline is the fallback.
# "baseline": always use the curated, hand-checked baseline (reproducible regression mode).
GENERATION_MODE = os.environ.get("HCH_GENERATION", "llm").strip().lower()
LLM_FRESH = os.environ.get("HCH_LLM_FRESH", "") == "1"     # bypass the LLM response cache

# --- PM tool -----------------------------------------------------------------
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")   # https://<site>.atlassian.net
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "HCH")
JIRA_REQUIRED = {"JIRA_BASE_URL": JIRA_BASE_URL, "JIRA_EMAIL": JIRA_EMAIL, "JIRA_API_TOKEN": JIRA_API_TOKEN}
JIRA_MISSING = [k for k, v in JIRA_REQUIRED.items() if not v]
# Jira is used automatically once the site URL, account e-mail and API token are all set.
PM_BACKEND = os.environ.get("PM_BACKEND", "mock" if JIRA_MISSING else "jira")

EXT_KEY_PREFIX = "ext-HCH-"          # stable external key label prefix
AI_LABEL = "ai-generated"            # guardrail: every agent-created item carries this

# Report "as of" date for the data pack (pack covers Jan-Mar 2027)
DEFAULT_AS_OF = "2027-03-31"

HOST = os.environ.get("HCH_HOST", "127.0.0.1")
PORT = int(os.environ.get("HCH_PORT", "8000"))
