"""SQLite persistence (single file). Every table that holds an agent output carries
`tags` (JSON list) so the Change Agent can find what an event makes stale."""
import json
import sqlite3
import threading
from datetime import datetime, timezone

from . import config

_lock = threading.RLock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, file TEXT, locator TEXT, line_start INT, line_end INT,
  text TEXT, kind TEXT DEFAULT 'pack');
CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY, label TEXT, value TEXT, unit TEXT, source_id TEXT,
  quote TEXT, tags TEXT, verified INT DEFAULT 0, superseded_by TEXT);
CREATE TABLE IF NOT EXISTS conflicts (
  id TEXT PRIMARY KEY, topic TEXT, detail TEXT, sources TEXT, tags TEXT, computed TEXT);
CREATE TABLE IF NOT EXISTS scope_lines (
  id TEXT PRIMARY KEY, text TEXT, source_id TEXT, kind TEXT);
CREATE TABLE IF NOT EXISTS gaps (
  id TEXT PRIMARY KEY, category TEXT, question TEXT, why TEXT, sources TEXT,
  sponsor_only INT, status TEXT, answer TEXT, answer_sources TEXT,
  assumption TEXT, origin TEXT, tags TEXT);
CREATE TABLE IF NOT EXISTS wbs (
  code TEXT PRIMARY KEY, level INT, parent TEXT, name TEXT, description TEXT,
  scope_refs TEXT, deliverable_refs TEXT, owner TEXT, acceptance TEXT,
  sources TEXT, tags TEXT, sort INT);
CREATE TABLE IF NOT EXISTS wbs_flagged (
  name TEXT PRIMARY KEY, reason TEXT, sources TEXT);
CREATE TABLE IF NOT EXISTS milestones (
  id TEXT PRIMARY KEY, name TEXT, wbs_code TEXT, rel_month TEXT, date TEXT,
  depends_on TEXT, sources TEXT, note TEXT, tags TEXT, sort INT);
CREATE TABLE IF NOT EXISTS risks (
  id TEXT PRIMARY KEY, category TEXT, description TEXT, owner TEXT,
  likelihood INT, impact INT, score INT, trigger_cond TEXT, mitigation TEXT,
  wbs_links TEXT, sources TEXT, status TEXT, origin TEXT, note TEXT,
  tags TEXT, version INT DEFAULT 1, stale INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS whatifs (
  id TEXT PRIMARY KEY, name TEXT, assumptions TEXT, result TEXT, sources TEXT,
  tags TEXT, version INT DEFAULT 1, stale INT DEFAULT 0, event_id TEXT);
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY, kind TEXT, title TEXT, as_of TEXT, content TEXT,
  claims TEXT, status TEXT, critic TEXT, tags TEXT, version INT,
  created_at TEXT, event_id TEXT, planted TEXT, llm_used INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS change_events (
  id TEXT PRIMARY KEY, title TEXT, date TEXT, source TEXT, text TEXT,
  tags TEXT, received_at TEXT, impact TEXT);
CREATE TABLE IF NOT EXISTS stale_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, item_type TEXT,
  item_id TEXT, reason TEXT, refreshed_id TEXT);
CREATE TABLE IF NOT EXISTS actions (
  id TEXT PRIMARY KEY, origin TEXT, kind TEXT, target TEXT, payload TEXT,
  rationale TEXT, status TEXT, checkpoint TEXT, created_at TEXT, applied_at TEXT);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, checkpoint TEXT, item_type TEXT,
  item_id TEXT, approver TEXT, role TEXT, decision TEXT, comment TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, run_id TEXT, actor TEXT,
  actor_type TEXT, action TEXT, target_type TEXT, target_id TEXT,
  outcome TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS pm_issues (
  key TEXT PRIMARY KEY, ext_key TEXT, issue_type TEXT, summary TEXT,
  description TEXT, labels TEXT, parent_key TEXT, due_date TEXT,
  status TEXT, links TEXT, comments TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS pm_sync_map (
  ext_key TEXT, backend TEXT, remote_key TEXT, content_hash TEXT, synced_at TEXT,
  PRIMARY KEY (ext_key, backend));
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY, text TEXT, source TEXT, made_by TEXT, date TEXT);
CREATE TABLE IF NOT EXISTS qa_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, question TEXT, answer TEXT,
  citations TEXT, not_found INT, mode TEXT);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, kind TEXT, started TEXT, ended TEXT, seconds REAL,
  tokens_in INT DEFAULT 0, tokens_out INT DEFAULT 0, cost_usd REAL DEFAULT 0,
  llm_calls INT DEFAULT 0, summary TEXT);
CREATE TABLE IF NOT EXISTS handoffs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, run_id TEXT, from_agent TEXT,
  to_agent TEXT, payload_ref TEXT, items INT);
CREATE TABLE IF NOT EXISTS bias_checks (
  id TEXT PRIMARY KEY, created_at TEXT, result TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
"""


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def conn():
    global _conn
    with _lock:
        if _conn is None:
            config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            _conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.executescript(SCHEMA)
            _conn.commit()
        return _conn


def reset_connection():
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None


def q(sql, args=()):
    with _lock:
        return [dict(r) for r in conn().execute(sql, args).fetchall()]


def q1(sql, args=()):
    rows = q(sql, args)
    return rows[0] if rows else None


def ex(sql, args=()):
    with _lock:
        c = conn()
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


def exmany(sql, rows):
    with _lock:
        c = conn()
        c.executemany(sql, rows)
        c.commit()


def J(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def L(text, default=None):
    if text is None or text == "":
        return default if default is not None else []
    return json.loads(text)


def kv_get(k, default=None):
    r = q1("SELECT v FROM kv WHERE k=?", (k,))
    return json.loads(r["v"]) if r else default


def kv_set(k, v):
    ex("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (k, J(v)))


def wipe_outputs(keep_pm=True, keep_governance=True):
    """Clear agent outputs (used by a fresh full run). Governance tables and the
    PM board are kept by default: the audit trail must never be erased."""
    tables = ["conflicts", "scope_lines", "gaps", "wbs", "wbs_flagged", "milestones",
              "risks", "whatifs", "reports", "stale_items", "handoffs", "bias_checks"]
    for t in tables:
        ex(f"DELETE FROM {t}")
