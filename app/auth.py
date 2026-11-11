"""Login, sessions and role-based access control (RBAC).

Four roles. The server enforces every permission; the UI only hides what the server
would refuse anyway. Approvals are signed with the logged-in account, so a checkpoint
can no longer be approved under a typed-in name.

  admin            System administrator - sees and can do everything, manages users.
  project_manager  Planning, PM tool, change handling. Owns HC1, HC2, HC3, HC6.
  group_leader     Risk and reporting work streams. Owns HC4, HC5.
  supervisor       Independent oversight: governance, audit, evaluation. Owns HC7.
"""
import hashlib
import secrets
import os
from datetime import datetime, timedelta, timezone

from . import audit, db

SESSION_HOURS = int(os.environ.get("HCH_SESSION_HOURS", "12"))
COOKIE = "hch_session"

VIEWS = ["dashboard", "overview", "planning", "pm", "memory", "risk", "reports", "change",
         "governance", "agents", "eval", "admin"]

ROLES = {
    "admin": {
        "label": "System Admin", "label_zh": "系统管理员",
        "description": "Full visibility across every module, audit and user management.",
        "views": VIEWS,
        "actions": ["run.pipeline", "reset.demo", "pm.write", "memory.ask", "memory.decide",
                    "reports.generate", "reports.plant", "change.inject", "eval.run",
                    "audit.view", "audit.export", "users.manage"],
        "checkpoints": ["HC1", "HC2", "HC3", "HC4", "HC5", "HC6", "HC7"],
    },
    "project_manager": {
        "label": "Project Manager", "label_zh": "项目经理",
        "description": "Plans the project, syncs the PM tool and handles change events.",
        "views": ["dashboard", "overview", "planning", "pm", "memory", "risk", "reports", "change", "agents"],
        "actions": ["run.pipeline", "pm.write", "memory.ask", "memory.decide", "change.inject",
                    "reports.generate"],
        "checkpoints": ["HC1", "HC2", "HC3", "HC6"],
    },
    "group_leader": {
        "label": "Group Leader", "label_zh": "组长",
        "description": "Leads the risk and reporting work streams; reads the plan and change impact.",
        "views": ["dashboard", "overview", "planning", "memory", "risk", "reports", "change", "agents"],
        "actions": ["memory.ask", "reports.generate", "reports.plant"],
        "checkpoints": ["HC4", "HC5"],
    },
    "supervisor": {
        "label": "Supervisor", "label_zh": "监督员",
        "description": "Independent oversight: governance, bias sign-off, audit trail and evaluation.",
        "views": ["dashboard", "overview", "memory", "risk", "reports", "change", "governance", "agents", "eval"],
        "actions": ["memory.ask", "audit.view", "audit.export", "eval.run"],
        "checkpoints": ["HC7"],
    },
}

DEFAULT_USERS = [
    ("admin", "System Admin", "admin"),
    ("pm", "Project Manager", "project_manager"),
    ("leader", "Group Leader", "group_leader"),
    ("supervisor", "Supervisor", "supervisor"),
]


class AuthError(Exception):
    """401 - no active session or selectable identity."""


class Forbidden(Exception):
    """403 - logged in, but the role does not allow this."""


def _utc(dt=None):
    return (dt or datetime.now(timezone.utc)).isoformat(timespec="seconds")


def ensure_seed():
    if db.q1("SELECT COUNT(*) c FROM users")["c"]:
        return
    for username, name, role in DEFAULT_USERS:
        create_user(username, name, role, by="system")


def create_user(username, display_name, role, by="admin"):
    username = (username or "").strip().lower()
    if not username or not username.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise ValueError("username must be letters, digits, '.', '-' or '_'")
    if role not in ROLES:
        raise ValueError(f"unknown role {role}")
    if not display_name or not display_name.strip():
        raise ValueError("display name required")
    if db.q1("SELECT 1 FROM users WHERE username=?", (username,)):
        raise ValueError("username already exists")
    db.ex("INSERT INTO users(username,display_name,role,active,created_at) VALUES(?,?,?,1,?)",
          (username, display_name.strip(), role, db.now()))
    audit.log(by, "user created", "user", username, detail={"role": role},
              actor_type="system" if by == "system" else "human")


def update_user(username, by, role=None, active=None, display_name=None):
    u = db.q1("SELECT * FROM users WHERE username=?", (username,))
    if not u:
        raise ValueError("unknown user")
    changes = {}
    if role is not None and role != u["role"]:
        if role not in ROLES:
            raise ValueError(f"unknown role {role}")
        changes["role"] = role
    if active is not None and int(bool(active)) != u["active"]:
        changes["active"] = int(bool(active))
    if display_name and display_name.strip() != u["display_name"]:
        changes["display_name"] = display_name.strip()
    if username == by and (changes.get("role", "admin") != "admin" or changes.get("active", 1) == 0):
        raise ValueError("you cannot demote or disable your own admin account")
    if u["role"] == "admin" and ("role" in changes or changes.get("active") == 0):
        if db.q1("SELECT COUNT(*) c FROM users WHERE role='admin' AND active=1")["c"] <= 1:
            raise ValueError("at least one active admin must remain")
    for k, v in changes.items():
        db.ex(f"UPDATE users SET {k}=? WHERE username=?", (v, username))
    if changes.get("active") == 0 or "role" in changes:
        db.ex("DELETE FROM sessions WHERE username=?", (username,))   # force re-login
    if changes:
        audit.log(by, "user updated", "user", username, detail=changes, actor_type="human")
    return changes


def selectable_users():
    return db.q("SELECT username,display_name,role FROM users WHERE active=1 ORDER BY "
                "CASE role WHEN 'admin' THEN 0 WHEN 'project_manager' THEN 1 WHEN 'group_leader' THEN 2 ELSE 3 END, username")


def login(username, ip=""):
    username = (username or "").strip().lower()
    u = db.q1("SELECT * FROM users WHERE username=?", (username,))
    if not u or not u["active"]:
        audit.log(username or "(blank)", "identity selection failed", "session", "", outcome="rejected",
                  detail={"ip": ip}, actor_type="human")
        raise AuthError("Identity unavailable")
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.ex("INSERT INTO sessions(token,username,created_at,expires_at,last_seen,ip) VALUES(?,?,?,?,?,?)",
          (hashlib.sha256(token.encode()).hexdigest(), username, _utc(now),
           _utc(now + timedelta(hours=SESSION_HOURS)), _utc(now), ip))
    db.ex("UPDATE users SET last_login=? WHERE username=?", (db.now(), username))
    audit.log(username, "login", "session", "", detail={"role": u["role"], "ip": ip}, actor_type="human")
    return token, public(u)


def logout(token):
    if not token:
        return
    h = hashlib.sha256(token.encode()).hexdigest()
    s = db.q1("SELECT username FROM sessions WHERE token=?", (h,))
    db.ex("DELETE FROM sessions WHERE token=?", (h,))
    if s:
        audit.log(s["username"], "logout", "session", "", actor_type="human")


def user_for(token):
    if not token:
        return None
    h = hashlib.sha256(token.encode()).hexdigest()
    s = db.q1("SELECT * FROM sessions WHERE token=?", (h,))
    if not s or s["expires_at"] < _utc():
        if s:
            db.ex("DELETE FROM sessions WHERE token=?", (h,))
        return None
    u = db.q1("SELECT * FROM users WHERE username=? AND active=1", (s["username"],))
    if not u:
        return None
    db.ex("UPDATE sessions SET last_seen=? WHERE token=?", (_utc(), h))
    return public(u)


def public(u):
    r = ROLES[u["role"]]
    return {"username": u["username"], "name": u["display_name"], "role": u["role"],
            "role_label": r["label"], "role_label_zh": r["label_zh"], "views": r["views"],
            "actions": r["actions"], "checkpoints": r["checkpoints"]}


def can(user, perm):
    """perm is 'view.<tab>', an action name, or a checkpoint id (HC1..HC7)."""
    if not user:
        return False
    r = ROLES[user["role"]]
    if perm.startswith("view."):
        return perm[5:] in r["views"]
    if perm.startswith("HC"):
        return perm in r["checkpoints"]
    return perm in r["actions"]


def require(user, perm, target=""):
    if not user:
        raise AuthError("Please log in")
    if not can(user, perm):
        audit.log(user["username"], f"access denied: {perm}", "permission", target or perm, outcome="blocked",
                  detail={"role": user["role"]}, actor_type="human")
        raise Forbidden(f"Role '{ROLES[user['role']]['label']}' is not permitted: {perm}")


def users_overview():
    users = db.q("SELECT username,display_name,role,active,created_at,last_login FROM users ORDER BY "
                 "CASE role WHEN 'admin' THEN 0 WHEN 'project_manager' THEN 1 WHEN 'group_leader' THEN 2 ELSE 3 END, username")
    sess = {r["username"]: r["n"] for r in db.q("SELECT username, COUNT(*) n FROM sessions WHERE expires_at>? GROUP BY username", (_utc(),))}
    appr = {r["account"]: r["n"] for r in db.q("SELECT account, COUNT(*) n FROM approvals WHERE account IS NOT NULL GROUP BY account")}
    acts = {r["actor"]: r["n"] for r in db.q("SELECT actor, COUNT(*) n FROM audit_log WHERE actor_type='human' GROUP BY actor")}
    denied = {r["actor"]: r["n"] for r in db.q("SELECT actor, COUNT(*) n FROM audit_log WHERE action LIKE 'access denied%' GROUP BY actor")}
    for u in users:
        u["active_sessions"] = sess.get(u["username"], 0)
        u["approvals"] = appr.get(u["username"], 0)
        u["human_actions"] = acts.get(u["username"], 0)
        u["denied"] = denied.get(u["username"], 0)
    return {"users": users, "roles": {k: {kk: vv for kk, vv in v.items()} for k, v in ROLES.items()},
            "views": VIEWS, "checkpoints": audit.CHECKPOINTS,
            "access_log": db.q("SELECT id,ts,actor,action,target_id,outcome FROM audit_log WHERE target_type IN ('session','permission','user') "
                               "ORDER BY id DESC LIMIT 60")}
