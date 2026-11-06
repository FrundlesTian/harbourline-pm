"""Harbourline AI PM system - HTTP server (Python standard library only).
Run:  python3 server.py   then open http://127.0.0.1:8000"""
import json
import mimetypes
import os
import subprocess
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import (agents, audit, change, config, db, governance, memory, pipeline, planning, pmtool,
                 reporting, risk, sources)

ROOT = config.ROOT


def ok(data=None, **kw):
    return 200, dict(data or {}, **kw)


def body_of(h):
    n = int(h.headers.get("Content-Length") or 0)
    return json.loads(h.rfile.read(n).decode() or "{}") if n else {}


# ------------------------------------------------------------------ handlers
def api_status(q, b):
    return ok(pipeline.status())


def api_run(q, b):
    return ok(pipeline.full_run(use_llm=b.get("use_llm", True)))


def api_reset(q, b):
    pipeline.reset_demo()
    return ok({"reset": True})


def api_planning(q, b):
    def cites(ids):
        return [sources.cite(i) for i in ids]
    gaps = [dict(g, sources=cites(db.L(g["sources"])), answer_sources=cites(db.L(g["answer_sources"])))
            for g in db.q("SELECT * FROM gaps ORDER BY id")]
    conflicts = [dict(c, sources=cites(db.L(c["sources"])), computed=db.L(c["computed"], {}))
                 for c in db.q("SELECT * FROM conflicts ORDER BY id")]
    wbs = [dict(w, scope_refs=db.L(w["scope_refs"]), deliverable_refs=db.L(w["deliverable_refs"]),
                sources=cites(db.L(w["sources"])), tags=db.L(w["tags"])) for w in db.q("SELECT * FROM wbs ORDER BY sort")]
    ms = [dict(m, depends_on=db.L(m["depends_on"]), sources=cites(db.L(m["sources"])))
          for m in db.q("SELECT * FROM milestones ORDER BY sort")]
    ph = planning.plan_hash() if wbs else None
    gh = pipeline.gaps_hash() if gaps else None
    return ok({"scope": planning.scope_statement() if wbs else None, "gaps": gaps, "conflicts": conflicts, "wbs": wbs,
               "flagged": [dict(f, sources=db.L(f["sources"])) for f in db.q("SELECT * FROM wbs_flagged")],
               "milestones": ms, "plan_hash": ph, "gaps_hash": gh,
               "hc1": audit.latest_approval("HC1", "gaps", gh) if gh else None,
               "hc2": audit.latest_approval("HC2", "plan", ph) if ph else None,
               "dependency_issues": planning.critical_path_check()})


def api_source(q, b, sid):
    f = db.q1("SELECT * FROM facts WHERE id=?", (sid,))
    if f:
        s = sources.get(f["source_id"])
        c = sources.cite(f["source_id"])
        c["label"] = f"Fact {sid} - {f['label']} = {f['value']} {f['unit'] or ''} - quote verified in {c['label']}"
        return ok(dict(s, cite=c, fact=f))
    s = sources.get(sid)
    if not s:
        return 404, {"error": "unknown source"}
    return ok(dict(s, cite=sources.cite(sid)))


def api_approve(q, b):
    cp, approver, decision = b.get("checkpoint"), b.get("approver", ""), b.get("decision", "approved")
    comment, item = b.get("comment", ""), b.get("item_id")
    if cp == "HC1":
        audit.record_approval("HC1", "gaps", pipeline.gaps_hash(), approver, decision, comment)
    elif cp == "HC2":
        audit.record_approval("HC2", "plan", planning.plan_hash(), approver, decision, comment)
    elif cp == "HC3":
        audit.record_approval("HC3", "sync_preview", item, approver, decision, comment)
    elif cp == "HC4":
        audit.record_approval("HC4", "risk_register", pipeline.risk_hash(), approver, decision, comment)
    elif cp == "HC5":
        if decision == "approved":
            return ok({"report": reporting.release(item, approver, comment)})
        audit.record_approval("HC5", "report", item, approver, "rejected", comment)
    elif cp == "HC6":
        return ok({"result": change.approve_action(item, approver, decision, comment)})
    elif cp == "HC7":
        governance.sign_off_bias(approver, decision, comment)
    else:
        return 400, {"error": "unknown checkpoint"}
    return ok({"recorded": True})


def api_pm_preview(q, b):
    return ok(pmtool.preview())


def api_pm_apply(q, b):
    return ok(pmtool.apply(b.get("preview_id")))


def api_pm_board(q, b):
    return ok({"backend": config.PM_BACKEND, "project": config.JIRA_PROJECT_KEY, "issues": pmtool.board()})


def api_pm_readback(q, b):
    return ok(pmtool.readback())


def api_pm_agent_attempt(q, b):
    pm = pmtool.backend()
    op, key = b.get("op", "close"), b.get("key", "")
    try:
        {"delete": lambda: pm.delete(key), "close": lambda: pm.close(key),
         "done": lambda: pm.transition(key, "Done")}[op]()
        return ok({"blocked": False})
    except pmtool.GuardrailViolation as e:
        return ok({"blocked": True, "message": str(e)})


def api_pm_human(q, b):
    if config.PM_BACKEND != "mock":
        return 400, {"error": "On Jira, humans move items in Jira's own UI."}
    who = (b.get("human") or "").strip()
    if not who:
        return 400, {"error": "named human required"}
    pmtool.MockBoard().human_transition(b["key"], b.get("status", "Done"))
    audit.log(who, f"human moved item to {b.get('status', 'Done')}", "pm_issue", b["key"], actor_type="human")
    return ok({"done": True})


def api_ask(q, b):
    return ok(memory.answer(b.get("question", ""), use_llm=b.get("use_llm", True)))


def api_qa_log(q, b):
    return ok({"log": db.q("SELECT * FROM qa_log ORDER BY id DESC LIMIT 50"),
               "decisions": db.q("SELECT * FROM decisions ORDER BY id")})


def api_decision(q, b):
    if not b.get("made_by") or not b.get("text"):
        return 400, {"error": "text and made_by required"}
    return ok({"id": memory.record_decision(b["text"], b["made_by"], b.get("source", ""))})


def api_risk(q, b):
    regs = [dict(r, wbs_links=db.L(r["wbs_links"]), sources=[sources.cite(s) for s in db.L(r["sources"])])
            for r in db.q("SELECT * FROM risks ORDER BY score DESC, id")]
    wi = [dict(w, assumptions=db.L(w["assumptions"]), result=db.L(w["result"], {}),
               sources=[sources.cite(s) for s in db.L(w["sources"])]) for w in db.q("SELECT * FROM whatifs ORDER BY id")]
    rh = pipeline.risk_hash() if regs else None
    return ok({"register": regs, "whatifs": wi, "seed_qa": risk.seed_qa(), "top5": [r["id"] for r in risk.top5()],
               "risk_hash": rh, "hc4": audit.latest_approval("HC4", "risk_register", rh) if rh else None})


def api_reports(q, b):
    rows = db.q("SELECT id,kind,title,as_of,status,version,created_at,event_id,planted,llm_used FROM reports "
                "WHERE planted IS NULL ORDER BY created_at DESC, id DESC")
    return ok({"reports": rows})


def api_report(q, b, rid):
    r = db.q1("SELECT * FROM reports WHERE id=?", (rid,))
    if not r:
        return 404, {"error": "no report"}
    return ok(dict(r, claims=db.L(r["claims"]), critic=db.L(r["critic"]),
                   approval=audit.latest_approval("HC5", "report", rid)))


def api_reports_generate(q, b):
    r = reporting.generate(b.get("kind", "edc"), use_llm=b.get("use_llm", True))
    return ok({"id": r["id"], "status": r["status"]})


def api_plant(q, b):
    """Demo: plant a fault in a copy of the current draft and show the Critic stopping it."""
    from eval import faults
    kind, fault = b.get("kind", "nrf"), b.get("fault", "wrong_number")
    r = reporting.generate(kind, use_llm=False, mutate=faults.FAULTS[fault])
    return ok(dict(r, critic=db.L(r["critic"])))


def api_change(q, b):
    evs = []
    for e in db.q("SELECT * FROM change_events ORDER BY received_at"):
        evs.append(dict(e, impact=db.L(e["impact"], {}), tags=db.L(e["tags"])))
    files = sorted(p.stem for p in config.CHANGE_EVENTS.glob("CE-*.json"))
    return ok({"events": evs, "available": files,
               "stale": db.q("SELECT * FROM stale_items ORDER BY id"),
               "actions": [dict(a, payload=db.L(a["payload"], {})) for a in db.q("SELECT * FROM actions ORDER BY id")]})


def api_change_inject(q, b):
    if b.get("custom"):
        c = b["custom"]
        if not all(c.get(k) for k in ("id", "title", "date", "text")):
            return 400, {"error": "custom event needs id, title, date, text"}
        return ok(change.inject(custom=c))
    with audit.Run("change"):
        return ok(change.inject(b.get("id", "CE-01")))


def api_change_note(q, b, eid):
    return ok({"markdown": change.impact_note_md(eid)})


def api_governance(q, b):
    lim = int((q.get("limit") or ["300"])[0])
    bias = db.q1("SELECT * FROM bias_checks WHERE id='BIAS-1'")
    return ok({"checkpoints": governance.checkpoint_map(),
               "approvals": db.q("SELECT * FROM approvals ORDER BY id DESC"),
               "audit": db.q("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (lim,)),
               "audit_total": db.q1("SELECT COUNT(*) c FROM audit_log")["c"],
               "blocked": db.q("SELECT * FROM audit_log WHERE outcome IN ('blocked','rejected') ORDER BY id DESC"),
               "bias": dict(bias, result=db.L(bias["result"], {})) if bias else None,
               "hc7": audit.latest_approval("HC7", "bias_check", "BIAS-1")})


def api_agents(q, b):
    return ok({"agents": agents.AGENT_CARDS, "checkpoints": audit.CHECKPOINTS})


def api_eval_latest(q, b):
    p = ROOT / "eval" / "results" / "latest.json"
    return ok(json.loads(p.read_text()) if p.exists() else {"missing": True})


def api_eval_run(q, b):
    cmd = [sys.executable, str(ROOT / "eval" / "run_eval.py")]
    if not b.get("use_llm"):
        cmd.append("--no-llm")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        return 500, {"error": r.stderr[-2000:]}
    return api_eval_latest(q, b)


ROUTES = {
    ("GET", "/api/status"): api_status, ("POST", "/api/run"): api_run, ("POST", "/api/reset"): api_reset,
    ("GET", "/api/planning"): api_planning, ("POST", "/api/approve"): api_approve,
    ("GET", "/api/pm/preview"): api_pm_preview, ("POST", "/api/pm/apply"): api_pm_apply,
    ("GET", "/api/pm/board"): api_pm_board, ("GET", "/api/pm/readback"): api_pm_readback,
    ("POST", "/api/pm/agent_attempt"): api_pm_agent_attempt, ("POST", "/api/pm/human"): api_pm_human,
    ("POST", "/api/ask"): api_ask, ("GET", "/api/qa"): api_qa_log, ("POST", "/api/decision"): api_decision,
    ("GET", "/api/risk"): api_risk, ("GET", "/api/reports"): api_reports,
    ("POST", "/api/reports/generate"): api_reports_generate, ("POST", "/api/reports/plant"): api_plant,
    ("GET", "/api/change"): api_change, ("POST", "/api/change/inject"): api_change_inject,
    ("GET", "/api/governance"): api_governance, ("GET", "/api/agents"): api_agents,
    ("GET", "/api/eval"): api_eval_latest, ("POST", "/api/eval/run"): api_eval_run,
}
PREFIX = [("GET", "/api/source/", api_source), ("GET", "/api/report/", api_report),
          ("GET", "/api/change/note/", api_change_note)]


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if os.environ.get("HCH_VERBOSE"):
            super().log_message(fmt, *args)

    def _send(self, code, payload, ctype="application/json"):
        data = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if "json" in ctype or "text" in ctype else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path.startswith("/api/export/"):
                name = u.path.rsplit("/", 1)[-1]
                if name == "audit.csv":
                    return self._send(200, governance.audit_export_csv().encode(), "text/csv")
                if name == "approvals.csv":
                    return self._send(200, governance.approvals_export_csv().encode(), "text/csv")
                if name == "governance.json":
                    g = api_governance({"limit": ["100000"]}, {})[1]
                    return self._send(200, json.dumps(g, ensure_ascii=False, indent=2, default=str).encode(), "application/json")
                return self._send(404, {"error": "unknown export"})
            b = body_of(self) if method == "POST" else {}
            fn = ROUTES.get((method, u.path))
            if fn:
                code, data = fn(q, b)
                return self._send(code, data)
            for m, pre, f in PREFIX:
                if m == method and u.path.startswith(pre):
                    code, data = f(q, b, u.path[len(pre):])
                    return self._send(code, data)
            if method == "GET":
                return self._static(u.path)
            return self._send(404, {"error": "not found"})
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:  # failures are visible, not silent
            traceback.print_exc()
            audit.log("server", "error", "http", u.path, outcome="error", detail={"error": str(e)}, actor_type="system")
            return self._send(500, {"error": str(e)})

    def _static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        f = (config.STATIC / path.lstrip("/")).resolve()
        if config.STATIC.resolve() not in f.parents or not f.is_file():
            return self._send(404, {"error": "not found"})
        self._send(200, f.read_bytes(), mimetypes.guess_type(str(f))[0] or "application/octet-stream")

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def main():
    info = pipeline.init()
    if info["facts_rejected"]:
        print("WARNING facts rejected (quote not in source):", info["facts_rejected"])
    if not db.q("SELECT code FROM wbs LIMIT 1"):
        pipeline.full_run()
    print(f"Harbourline PM system on http://{config.HOST}:{config.PORT}  "
          f"(LLM: {'DeepSeek ' + config.DEEPSEEK_MODEL if config.DEEPSEEK_API_KEY else 'off - deterministic mode'}, "
          f"PM backend: {config.PM_BACKEND})")
    ThreadingHTTPServer((config.HOST, config.PORT), H).serve_forever()


if __name__ == "__main__":
    main()
