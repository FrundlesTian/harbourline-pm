"""Module 5 - Reporting Agent.
Builds ONE fact sheet, then two audience-specific drafts from it:
  * EDC exception update (one page: what changed / what is late / decisions needed - L07)
  * NRF monthly progress report (NRF 3.2: progress, expenditure vs eligible cost,
    tranche conditions, top five risks)
Every line is a claim carrying fact ids and/or source ids; computed numbers carry the
formula. Drafts go straight to the Critic (automatic hand-off); only HC5 releases."""
import hashlib

from . import audit, critic, db, llm, risk, sources
from .agents import AGENT_CARDS

AGENT = "reporting"


def fact(fid):
    return db.q1("SELECT * FROM facts WHERE id=?", (fid,))


def line(text, cites=(), calc=None):
    return {"text": text, "cites": list(cites), "calc": calc or []}


def _events():
    return db.q("SELECT * FROM change_events ORDER BY received_at")


def _event_lines(kind):
    out = []
    for e in _events():
        if kind == "edc":
            out.append(line(f"{e['id']} ({e['date']}): {e['title']}. Change impact note drafted; sponsor decisions "
                            f"and actions await HC6.", [e["id"]]))
        else:
            out.append(line(f"{e['id']} ({e['date']}): {e['title']} - effect on tranche conditions and eligible cost "
                            f"is set out in the change impact note.", [e["id"]]))
    return out


def _top5_lines():
    return [line(f"{r['id']} {r['description']} - L{r['likelihood']} x I{r['impact']} = {r['score']}; owner {r['owner']}; "
                 f"trigger: {r['trigger_cond']}", [f"RISK:{r['id']}"]) for r in risk.top5()]


CONFLICT_SUMMARY = {
    "CF01": "brief: works within 22 months and fully open by Q4 2028; KHB baseline practical completion 2028-12-31; "
            "deliverable D22 due 2028-10-31. Completion after 31 December 2028 needs Fund approval.",
    "CF03": "brief: 60% of the S$18.5M budget is grant-funded; NRF: 60% of ELIGIBLE cost, capped at S$17.0M "
            "(maximum S$10.2M), food court and rooftop amenity ineligible.",
    "CF04": "about S$1.18M remains after contract and fees, not decided as contingency; asbestos estimate S$0.35-0.60M.",
    "CF08": "KHB writes 'broadly on programme' while physical progress is 3.5% against 6.0% planned.",
}


def _conflict_lines(ids):
    out = []
    for c in db.q("SELECT * FROM conflicts"):
        if c["id"] in ids:
            out.append(line(f"{c['id']} {c['topic']} - sources disagree, not resolved by the agent: "
                            f"{CONFLICT_SUMMARY.get(c['id'], 'see conflict register')}", db.L(c["sources"])))
    return out


def build_edc(as_of):
    S = []
    S.append(("What changed", [
        line("Asbestos (chrysotile) confirmed in level 2 ceiling boards; works in that zone stopped on 2027-03-03.", ["F47", "F40"]),
        line("KHB estimate for removal: S$0.35-0.60M and 4-6 weeks; removal sequence not yet agreed.", ["F38", "F39", "F48"]),
        line("Roof slab needs strengthening for the rooftop garden; cost not yet estimated.", ["F41"]),
        line("NRF Tranche 1 claim submitted on 2027-03-19.", ["F44"]),
        line("Resident consultation closed with 214 responses; summary still overdue.", ["F42", "F75"]),
    ] + _event_lines("edc")))
    S.append(("What is late", [
        line("Physical progress 3.5% against 6.0% planned (KHB March report).", ["F50", "F51"]),
        line("Design completion 26% against 35% planned; Design stage 2 report (D04) overdue.", ["F52", "DEL-D04"]),
        line("Temporary access plan for lifts (D07) overdue since 2027-03-31.", ["DEL-D07"]),
        line("Active ageing operator appointment (D12) overdue; EOI extended to 2027-04-30 with 1 response.", ["F77", "F37", "F36"]),
        line("February NRF report was submitted late (2027-03-16).", ["F74"]),
    ]))
    head = round(float(fact("F01")["value"]) - float(fact("F19")["value"]) - float(fact("F20")["value"]), 2)
    S.append(("Decisions needed", [
        line("Closures: none agreed; KHB estimates 6-8 weeks delay if lift works cannot start June 2027. Options in what-if W2.", ["F15", "F56"]),
        line(f"Contingency: is the ~S${head}M headroom contingency, and who may draw on it?", ["F21", "F22"],
             [{"expr": "F01-F19-F20", "value": head}]),
        line("Rooftop garden: keep or defer (no decision recorded).", ["F46", "F41"]),
        line("Completion: KHB practical completion 2028-12-31 vs brief 'fully open by Q4 2028'; programme not reconciled.", ["F34", "F04", "F43"]),
    ]))
    S.append(("Top five risks", _top5_lines()))
    S.append(("Conflicts flagged", _conflict_lines({"CF01", "CF04", "CF08"})))
    return f"EDC exception update - as of {as_of}", S, ["reporting", "asbestos", "closures", "rooftop", "contingency",
                                                     "completion", "aac-operator", "progress", "budget", "schedule"]


def build_nrf(as_of):
    cap = float(fact("F24")["value"])
    paid = float(fact("F54")["value"].replace(",", ""))
    pct = round(paid / (cap * 1e6) * 100, 2)
    S = []
    S.append(("Progress against the baseline programme", [
        line("Baseline programme submitted on 2027-02-24; KHB baseline practical completion 2028-12-31.", ["F71", "F34"]),
        line("Overall physical progress 3.5% against 6.0% planned.", ["F50", "F51"]),
        line("Design completion 26% against 35% planned; submittals approved 10 against 19.", ["F52", "F53"]),
        line("Works in the level 2 west wing stopped on 2027-03-03 (asbestos); KHB estimates 4-6 weeks for removal.", ["F40", "F39"]),
    ]))
    S.append(("Expenditure to date against eligible cost", [
        line(f"Cumulative contractor payment claims to March: S$985,000, which is {pct}% of the S$17.0M eligible-cost cap.",
             ["F54", "F24"], [{"expr": "F54/(F24*1000000)*100", "value": pct}]),
        line("Eligible / ineligible split of expenditure: NOT FOUND in the data pack (food court and rooftop amenity are ineligible).", ["F26", "EDC-3.5"]),
        line("Asbestos variation estimate S$0.35-0.60M: grant eligibility NOT FOUND as of this report.", ["F38"]),
    ] + [l for l in _event_lines("nrf")]))
    S.append(("Status of each tranche condition", [
        line("T1 (contract award and baseline programme): claim submitted 2027-03-19.", ["F44", "NRF-T1"]),
        line("T2 (rough-in complete AND signed operator agreements for ALL social service spaces): AT RISK - active ageing operator not appointed (1 EOI response; 3 required); agreement owner not assigned.",
             ["F45", "F36", "F14", "F72"]),
        line("T3 (TOP for the whole facility): not yet due.", ["NRF-T3"]),
        line("T4 (six months of operation and utilisation report): not yet due.", ["NRF-T4"]),
    ]))
    S.append(("Top five risks", _top5_lines()))
    S.append(("Conflicts flagged", _conflict_lines({"CF01", "CF03", "CF08"})))
    return f"NRF monthly progress report - March 2027 (as of {as_of})", S, ["reporting", "grant", "eligible-cost",
                                                                           "tranche-2", "asbestos", "aac-operator",
                                                                           "progress", "completion", "schedule"]


def render(title, sections, summary=None):
    md = [f"# {title}", ""]
    if summary:
        md += ["## Summary", summary, ""]
    for name, lines in sections:
        md.append(f"## {name}")
        for l in lines:
            tag = " [" + ", ".join(l["cites"]) + "]" if l["cites"] else ""
            md.append(f"- {l['text']}{tag}")
        md.append("")
    return "\n".join(md)


def _llm_summary(sections):
    if not llm.available():
        return None
    bullets = "\n".join(f"- {l['text']} [" + ", ".join(l["cites"]) + "]" for _, ls in sections[:3] for l in ls)
    sysmsg = next(a for a in AGENT_CARDS if a["id"] == AGENT)["system_prompt"]
    text, _ = llm.chat(AGENT, sysmsg, f"BULLETS:\n{bullets}\n\nWrite a 3-sentence executive summary.", max_tokens=300)
    return text


def generate(kind, as_of="2027-03-31", use_llm=True, event_id=None, mutate=None):
    """Draft -> automatic Critic hand-off -> stored with status. `mutate` is used only by
    the evaluation harness to plant faults."""
    title, sections, tags = (build_edc if kind == "edc" else build_nrf)(as_of)
    summary = _llm_summary(sections) if use_llm else None
    claims = [dict(l, section=name) for name, ls in sections for l in ls]
    if summary:
        claims.insert(0, {"text": summary, "cites": sorted({c for l in claims for c in l["cites"]}),
                          "calc": [c for l in claims for c in l["calc"]], "section": "Summary", "llm": True})
    if mutate:
        title, sections, claims, summary = mutate(title, sections, claims, summary)
    content = render(title, sections, summary)
    h = hashlib.sha256(content.encode()).hexdigest()[:12]
    latest = db.q1("SELECT * FROM reports WHERE kind=? AND as_of=? AND planted IS NULL ORDER BY version DESC LIMIT 1",
                   (kind, as_of))
    if latest and latest["content"] == content and not mutate and latest["status"] != "stale":
        audit.log(AGENT, "report unchanged (no new version)", "report", latest["id"])
        return latest
    ver = ((latest["version"] if latest else 0) + 1)
    rid = f"{kind.upper()}-{as_of}-v{ver}" + (f"-planted-{h[:4]}" if mutate else "")
    findings = critic.check(kind, sections, claims, content, event_aware=True)
    status = "critic_stopped" if any(f["severity"] == "STOP" for f in findings) else "critic_passed"
    db.ex("INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (rid, kind, title, as_of, content, db.J(claims), status, db.J(findings), db.J(tags), ver if not mutate else 0,
           db.now(), event_id, "planted" if mutate else None, 1 if summary else 0))
    if not mutate:
        audit.log(AGENT, "write report draft", "report", rid, detail={"version": ver, "hash": h})
        audit.handoff(AGENT, "critic", rid, len(claims))
        audit.log("critic", f"critic {status}", "report", rid,
                  detail={"stops": sum(f["severity"] == "STOP" for f in findings), "findings": len(findings)})
    return db.q1("SELECT * FROM reports WHERE id=?", (rid,))


def release(report_id, approver, comment=""):
    r = db.q1("SELECT * FROM reports WHERE id=?", (report_id,))
    if not r:
        raise ValueError("no such report")
    if r["status"] != "critic_passed":
        audit.log(approver, "release refused", "report", report_id, outcome="blocked",
                  detail={"status": r["status"]}, actor_type="human")
        raise ValueError(f"Report status is {r['status']}: only Critic-passed drafts can be released")
    audit.record_approval("HC5", "report", report_id, approver, "approved", comment)
    db.ex("UPDATE reports SET status='released' WHERE id=?", (report_id,))
    return db.q1("SELECT * FROM reports WHERE id=?", (report_id,))


def run_all(as_of="2027-03-31", use_llm=True, event_id=None):
    return [generate("edc", as_of, use_llm, event_id), generate("nrf", as_of, use_llm, event_id)]
