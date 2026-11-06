"""Module 4 - Risk & What-if Agent.
Scored register (L x I) with owners, triggers, linked WBS and sources; seed-register QA;
three what-ifs with cost and schedule impact and stated assumptions; automatic
re-scoring proposals when a change event alters the plan."""
import csv
import io
from datetime import date, timedelta

from . import audit, config, db, sources

AGENT = "risk"

# id, category, description, owner, L, I, trigger, mitigation, wbs, sources, status, origin, note, tags
REGISTER = [
    ("R01", "Funding", "Grant conditions reduce eligible cost: cap S$17.0M; food court and rooftop amenity ineligible",
     "Finance Manager (M.L. Ong)", 5, 4, "Any cost classed ineligible, or eligible forecast above the S$17.0M cap",
     "Track eligible/ineligible spend monthly; confirm element costs (GQ09)", ["1.3.1", "5.5.3", "5.6.2"],
     ["RISK-R01", "NRF-1.2", "NRF-1.3", "EDC-2.1"], "Open - realised in part", "seed+pack",
     "Seed owner R. Tan left Council Aug 2026 - owner reassigned (proposal)", ["grant", "eligible-cost", "budget"]),
    ("R02", "Programme", "Keeping the Hub open extends the programme; closures not accepted so lift and sports hall packages cannot start as programmed",
     "Council PM (R. Shankar)", 4, 4, "No Council closure decision before lift works must start (June 2027)",
     "Bring closure options to the sponsor as a decision (MS06)", ["4.1.2", "5.7.2", "5.2.1"],
     ["RISK-R02", "PR2-3", "PR3-3", "SA-Q3", "LL-L01"], "Open", "seed+pack", "", ["closures", "schedule", "lifts"]),
    ("R03", "Stakeholder", "Noise and dust complaints from residents (merged duplicate R04)",
     "Community Engagement Lead (F. Aziz)", 4, 3, "Hacking works start, or first formal noise complaint",
     "Weekly works notice at lift lobbies (Seabreeze L02)", ["3.3.2"],
     ["RISK-R03", "RISK-R04", "LL-L02"], "Open", "seed", "R04 merged: same risk as R03", ["closures"]),
    ("R05", "Operator", "Childcare operator withdraws or delays opening",
     "Estate Development (D. Koh)", 3, 5, "Programme handover later than licensing lead time allows (EDC 4.3)",
     "Agree handover date with LHL; protect childcare floor sequence", ["3.2.1", "5.3.2"],
     ["RISK-R05", "EDC-4.3", "EDC-2.2"], "Open", "seed+pack", "Likelihood raised from 2: operator objected to Aug 2028 handover", ["childcare"]),
    ("R06", "Operator", "Active ageing centre operator not found (one EOI response; policy needs three)",
     "Council PM (R. Shankar)", 4, 5, "EOI closes 30 Apr 2027 with fewer than three responses",
     "Market sounding; widen EOI; prepare sponsor decision", ["3.2.2", "3.2.3", "5.4.2", "1.2.3"],
     ["RISK-R06", "EDC-4.4", "SA-Q2", "NRF-T2", "EDC-6.2"], "Open", "seed+pack",
     "Seed score 6 is arithmetically wrong (2x4=8); re-scored on pack evidence", ["aac-operator", "tranche-2"]),
    ("R07", "Technical", "Existing M&E worse than surveyed (sprinkler mains)",
     "KHB (J. Lim)", 4, 3, "Further provisional-sum instructions for M&E",
     "Complete condition survey; manage provisional sums", ["2.2.1", "5.8.1"],
     ["RISK-R07", "PR1-3", "PR2-4"], "Open - realised in part", "seed+pack", "S$120,000 provisional sum instructed", ["construction", "budget"]),
    ("R08", "Technical", "Hazardous materials: asbestos (chrysotile) confirmed in level 2 west wing",
     "KHB (J. Lim) / Council PM for variation", 5, 4, "Triggered 3 Mar 2027; further finds in other zones during soft-strip",
     "Licensed removal; agree sequence; commission intrusive survey of remaining zones (D06)", ["5.1.3", "2.2.2", "5.8.2", "1.3.2"],
     ["RISK-R08", "EDC-5.1", "EDC-6.5", "PR3-3", "LL-L03", "DEL-D06"], "REOPENED - realised", "seed+pack",
     "Seed register had this Closed ('not expected per desk study')", ["asbestos", "hazmat", "variation", "schedule", "eligible-cost"]),
    ("R09", "Cost", "Construction price inflation", "Finance Manager (M.L. Ong)", 4, 3,
     "Lift package (D17) price above contract allowance (allowance NOT FOUND)", "Hold contingency (GQ08)",
     ["1.3.2", "5.7.1"], ["RISK-R09"], "Open", "seed", "", ["budget", "contingency"]),
    ("R10", "Regulatory", "Authority approvals delayed (e.g. kitchen exhaust permit)", "KHB (J. Lim)", 3, 3,
     "D19 permit not granted by 2027-04-30", "Early submission", ["5.5.2"], ["RISK-R10", "DEL-D19"], "Open", "seed",
     "Seed owner 'TBC' - owner proposed", ["food-court"]),
    ("R11", "Accessibility", "Barrier-free access lost to levels 3-4 during 14-week east core lift closure",
     "Council PM (R. Shankar)", 4, 5, "East core closure approved without an accepted temporary access plan (D07 overdue)",
     "Price temporary lift; seek Fund written agreement (NRF 5.1)", ["4.1.3", "5.7.2"],
     ["RISK-R11", "EDC-3.1", "EDC-3.2", "NRF-5.1", "DEL-D07"], "Open", "seed+pack",
     "Seed had no owner or mitigation", ["accessibility", "lifts", "closures"]),
    ("R12", "Scope", "Roof slab needs strengthening for rooftop garden loads; cost not estimated",
     "KHB (J. Lim)", 5, 3, "Roof strengthening priced, or sponsor decides on deferral (EDC 6.3)",
     "Decide keep/defer (GQ17); price strengthening", ["5.6.1", "2.2.3"],
     ["RISK-R12", "EDC-5.2", "EDC-6.3", "PR3-3"], "Open - realised", "seed+pack", "", ["rooftop", "roof"]),
    ("R13", "Safety", "Public interface with live works", "KHB (J. Lim)", 3, 5, "Any public-zone incident or near miss",
     "Hoarding and segregation", ["4.1.1"], ["RISK-R13"], "Open", "seed", "", ["closures"]),
    ("R14", "Reporting", "Committee and grant reporting effort / lateness", "Council PM (R. Shankar)", 3, 2,
     "A report misses its due date", "One-page exception report (L07); single fact source", ["1.2.1", "1.2.2"],
     ["RISK-R14", "LL-L07", "DEL-D09"], "Open", "seed+pack", "", ["reporting"]),
    ("R15", "Programme", "Completion after 31 Dec 2028 (needs Fund approval) and after 'fully open by Q4 2028'",
     "Council PM (R. Shankar)", 4, 4, "Any forecast slip of KHB practical completion (31 Dec 2028)",
     "Reconcile programme (EDC 4.2); prepare NRF 4.2 request early", ["6.1.2", "1.1.2"],
     ["EDC-4.1", "EDC-4.2", "NRF-4.2", "BRIEF-p3-5", "PR3-3"], "Open", "pack", "", ["completion", "schedule"]),
    ("R16", "Programme", "Childcare floor handover too late for licensing before Jan 2029 intake",
     "Estate Development (D. Koh)", 4, 4, "Programme handover later than about Jun 2028",
     "Re-sequence childcare floor; agree date with LHL", ["5.3.2"],
     ["EDC-4.1", "EDC-4.3", "LL-L04", "DEL-D21"], "Open", "pack", "", ["childcare", "schedule"]),
    ("R17", "Funding", "Tranche 2 (30%) delayed: needs signed operator agreements for ALL social service spaces",
     "Finance Manager (M.L. Ong)", 4, 5, "AAC agreement (D14) not signed by 2027-06-30 or still without owner",
     "Put every grant condition in the schedule with an owner (L08); assign D14 owner", ["1.2.3", "3.2.3"],
     ["NRF-T2", "EDC-6.2", "LL-L08", "DEL-D14"], "Open", "pack", "", ["tranche-2", "aac-operator", "operator-agreements", "grant"]),
    ("R18", "Reporting", "Two consecutive late NRF reports may suspend the next tranche (Feb report was late)",
     "Council PM (R. Shankar)", 3, 4, "March report (D10) not submitted by 10th working day",
     "Fixed reporting calendar; KHB inputs by 5th working day", ["1.2.2"],
     ["NRF-3.3", "DEL-D09", "DEL-D10", "PR3-3"], "Open", "pack", "", ["reporting", "grant"]),
    ("R19", "Design", "Design behind plan (26% vs 35%); stage 2 report overdue", "KHB (J. Lim)", 4, 3,
     "Design variance worse than -9% in April report", "Recovery plan for design submittals", ["2.1.1", "2.1.2"],
     ["PR3-2", "DEL-D04"], "Open", "pack", "", ["design", "progress"]),
    ("R20", "Governance", "Consultation summary under-represents seniors and non-English speakers",
     "Community Engagement Lead (F. Aziz)", 4, 3, "Bias check (HC7) finds the oldest age band or non-English responses materially under-represented",
     "Re-weight by age band; second multilingual round (L06); HC7 sign-off", ["3.1.2"],
     ["LL-L06", "DEL-D15", "EDC-5.3"], "Open", "pack", "", ["consultation"]),
    ("R21", "Operator", "Late AAC appointment forces layout rework after design fixed", "Council PM (R. Shankar)", 3, 3,
     "AAC layout frozen in design stage 3 before an operator is appointed", "Hold AAC layout flexible (5.4.2)", ["5.4.2", "2.1.2"],
     ["LL-L05", "SA-Q2", "DEL-D16"], "Open", "pack", "", ["aac-operator", "design"]),
    ("R22", "Cost", "Contingency undefined and likely insufficient: ~S$1.18M headroom vs asbestos S$0.35-0.60M + roof strengthening (unpriced)",
     "Finance Manager (M.L. Ong)", 4, 4, "Committed variations exceed S$1.18M headroom",
     "Sponsor to confirm contingency and drawdown authority (GQ08)", ["1.3.2"],
     ["EDC-1.2", "EDC-5.1", "EDC-5.2"], "Open", "pack", "", ["contingency", "budget", "asbestos", "variation"]),
    ("R23", "Delivery system", "Vendor/tool change affects the AI PM system (brief: log vendor change as a risk)",
     "Team tool owner", 2, 2, "Vendor announces shutdown or free-tier change of a tool we use",
     "Re-check tools in Week 12; keep mock board fallback", ["1.1.1"], ["BRIEF-p6-5"], "Open", "brief", "", ["tooling"]),
]


def seed_qa():
    """Quality findings on the inherited 2025 register (computed from the CSV)."""
    raw = (config.DATA_PACK / "04_Seed_risk_register.csv").read_text(encoding="utf-8-sig").split("\n", 1)[1]
    rows = list(csv.DictReader(io.StringIO(raw)))
    out = []
    for r in rows:
        L, I, S = int(r["likelihood_1to5"]), int(r["impact_1to5"]), int(r["score"])
        if L * I != S:
            out.append({"risk": r["risk_id"], "issue": f"score {S} != {L}x{I}={L * I}", "source": f"RISK-{r['risk_id']}"})
        if not r["owner"] or r["owner"] in ("TBC",) or "left" in r["owner"]:
            out.append({"risk": r["risk_id"], "issue": f"owner invalid: '{r['owner'] or 'blank'}'", "source": f"RISK-{r['risk_id']}"})
        if not r["mitigation"]:
            out.append({"risk": r["risk_id"], "issue": "no mitigation", "source": f"RISK-{r['risk_id']}"})
    out.append({"risk": "R03/R04", "issue": "duplicate (noise complaints)", "source": "RISK-R04"})
    out.append({"risk": "R08", "issue": "Closed, but asbestos confirmed (EDC 6.5)", "source": "RISK-R08"})
    out.append({"risk": "ALL", "issue": "register not updated since June 2025", "source": "RISK-note"})
    return out


def run():
    wbs = {w["code"] for w in db.q("SELECT code FROM wbs")}
    if not wbs:
        raise RuntimeError("Risk agent needs the WBS hand-off from Planning first")
    changed = 0
    for (rid, cat, desc, owner, L, I, trig, mit, links, srcs, status, origin, note, tags) in REGISTER:
        bad = [w for w in links if w not in wbs]
        missing = [s for s in srcs if not sources.get(s)]
        if bad or missing:
            audit.log(AGENT, "reject risk", "risk", rid, outcome="rejected", detail={"bad_wbs": bad, "missing_src": missing})
            continue
        cur = db.q1("SELECT * FROM risks WHERE id=?", (rid,))
        row = dict(id=rid, category=cat, description=desc, owner=owner, likelihood=L, impact=I, score=L * I,
                   trigger_cond=trig, mitigation=mit, wbs_links=db.J(links), sources=db.J(srcs), status=status,
                   origin=origin, note=note, tags=db.J(tags))
        if cur and cur["origin"].startswith("change:"):
            continue  # an approved change-driven re-score supersedes the baseline row
        if cur and all(str(cur[k]) == str(v) for k, v in row.items()):
            if cur["stale"]:
                db.ex("UPDATE risks SET stale=0 WHERE id=?", (rid,))
            continue
        ver = (cur["version"] + 1) if cur else 1
        db.ex("INSERT OR REPLACE INTO risks(id,category,description,owner,likelihood,impact,score,trigger_cond,mitigation,"
              "wbs_links,sources,status,origin,note,tags,version,stale) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
              (*row.values(), ver))
        changed += 1
    audit.log(AGENT, "write risk register", "risk_register", "baseline", detail={"rows_written": changed})
    n = run_whatifs()
    audit.handoff(AGENT, "reporting", "risk_register+whatifs", len(REGISTER))
    return {"risks": len(db.q("SELECT id FROM risks")), "written": changed, "whatifs": n, "seed_findings": len(seed_qa())}


def top5():
    rows = db.q("SELECT * FROM risks WHERE status NOT LIKE 'Closed%' ORDER BY score DESC, id ASC")
    return rows[:5]


# ------------------------------------------------------------------ what-ifs
def _f(fid):
    return db.q1("SELECT * FROM facts WHERE id=?", (fid,))


def _rng(v):
    a, b = v.replace("–", "-").split("-")
    return float(a), float(b)


def _wk(d, w):
    return (d + timedelta(weeks=w)).isoformat()


def whatif_defs(event=None):
    pc = date.fromisoformat(_f("F34")["value"])
    head = float(_f("F21")["value"])
    clo, chi = _rng(_f("F38")["value"])
    wlo, whi = (int(x) for x in _rng(_f("F39")["value"]))
    dlo, dhi = (int(x) for x in _rng(_f("F56")["value"]))
    ce01 = event == "CE-01"
    w1_fund = ("Grant body ruled asbestos removal INELIGIBLE (CE-01): Council funds 100%." if ce01 else
               "Eligibility of the asbestos variation is NOT FOUND in the pack: Council exposure shown from 40% (eligible, under cap) to 100% (ineligible or above cap).")
    exp_lo = clo if ce01 else round(clo * 0.4, 2)
    W = [
        {"id": "W1", "name": "Asbestos removal in level 2 west wing",
         "assumptions": [f"Cost S${clo}-{chi}M and {wlo}-{whi} weeks (KHB estimate) [F38,F39]",
                         "Delay transfers 1:1 to practical completion - programme float NOT FOUND [PR3-3 says critical path affected]",
                         w1_fund, f"Variation is charged against the ~S${head}M headroom [F21] (contingency status undecided [F22])",
                         "Seabreeze analog: removal added 5 weeks [F66] - indicative only"],
         "result": {"cost_SGD_M": [clo, chi], "council_exposure_SGD_M": [exp_lo, chi],
                    "headroom_left_SGD_M": [round(head - chi, 2), round(head - clo, 2)],
                    "delay_weeks": [wlo, whi], "pc_forecast": [_wk(pc, wlo), _wk(pc, whi)],
                    "needs_NRF_4.2_approval": True},
         "sources": ["EDC-5.1", "PR3-3", "PR3-4", "EDC-1.2", "LL-L03", "NRF-4.2"] + (["CE-01"] if ce01 else []),
         "tags": ["asbestos", "eligible-cost", "budget", "contingency", "schedule", "completion", "variation"]},
        {"id": "W2", "name": "Closures not accepted - keep every area open",
         "assumptions": [f"KHB: {dlo}-{dhi} weeks delay if lift works cannot start June 2027 [F56]",
                         "KHB cost claim for keeping open: NOT FOUND (KHB 'reserves its position') [PR2-3]",
                         "Seabreeze analog: keeping open added about 3 months and S$0.6M [F65] - different building, indicative only",
                         "Alternative (accept closures): east core 14 wks with no barrier-free access to L3-4 [F31] needs Fund written agreement [F64]; temporary lift cost NOT FOUND [F78]"],
         "result": {"delay_weeks": [dlo, dhi], "pc_forecast": [_wk(pc, dlo), _wk(pc, dhi)],
                    "cost_SGD_M": "NOT FOUND (analog 0.6)", "needs_NRF_4.2_approval": True,
                    "alternative_accept_closures": {"delay_weeks": 0, "access_impact": "L3-4 no barrier-free access for ~14 weeks",
                                                    "needs": "Fund written agreement (NRF 5.1) + temporary lift (unpriced)"}},
         "sources": ["PR3-3", "PR2-3", "LL-L01", "EDC-3.1", "EDC-3.2", "NRF-5.1", "SA-Q3"],
         "tags": ["closures", "lifts", "schedule", "accessibility", "completion"]},
        {"id": "W3", "name": "Defer the rooftop community garden",
         "assumptions": ["Garden cost: NOT FOUND in pack (Finance figures not minuted [EDC-3.5])",
                         "Roof slab strengthening cost: not yet estimated [F41] - avoided if deferred",
                         "Garden is grant-ineligible [F26], so deferral does not reduce the grant",
                         "NRF 4.1 prior approval applies to social-service scope; garden is not listed as one [F62] - confirm with sponsor",
                         "Residents split: see consultation counts (computed)"],
         "result": {"cost_saving_SGD_M": "NOT FOUND", "grant_effect": "none (ineligible item)",
                    "schedule_effect": "NOT FOUND", "resident_view": _garden_split()},
         "sources": ["EDC-6.3", "EDC-5.2", "NRF-1.3", "NRF-4.1", "EDC-3.5"],
         "tags": ["rooftop", "roof", "budget", "scope"]},
    ]
    if event == "CE-02":
        W.append({"id": "W4", "name": "AAC operator withdrawal (CE-02): re-run EOI",
                  "assumptions": ["Sole EOI respondent withdrew; no other respondents [CE-02]",
                                  "Council policy requires at least three responses [F14]",
                                  "Tranche 2 needs signed agreements for ALL social service spaces [F45]; T2 = 30% of grant [F70]",
                                  "Seabreeze analog: missed operator condition delayed a tranche 4 months [F69]; late operator cost S$85,000 rework [F68]",
                                  "New EOI duration: NOT FOUND"],
                  "result": {"tranche2_share_of_max_grant_SGD_M": round(float(_f("F25")["value"]) * 0.30, 2),
                             "analog_tranche_delay_months": 4, "analog_rework_SGD": 85000,
                             "new_appointment_date": "NOT FOUND"},
                  "sources": ["CE-02", "SA-Q2", "NRF-T2", "NRF-1.2", "LL-L08", "LL-L05"],
                  "tags": ["aac-operator", "tranche-2", "grant"]})
    return W


def _garden_split():
    rows = list(csv.DictReader(open(config.DATA_PACK / "05_Resident_consultation_responses.csv", encoding="utf-8-sig")))
    pro = sum(1 for r in rows if "Rooftop garden sounds lovely" in r["comment"])
    con = sum(1 for r in rows if "Rooftop garden is a waste" in r["comment"])
    return {"supportive_comments": pro, "opposed_comments": con, "of_responses": len(rows)}


def run_whatifs(event=None):
    n = 0
    for w in whatif_defs(event):
        cur = db.q1("SELECT * FROM whatifs WHERE id=?", (w["id"],))
        payload = (db.J(w["assumptions"]), db.J(w["result"]), db.J(w["sources"]), db.J(w["tags"]))
        if cur and (cur["assumptions"], cur["result"], cur["sources"], cur["tags"]) == payload:
            db.ex("UPDATE whatifs SET stale=0 WHERE id=?", (w["id"],))
            continue
        ver = (cur["version"] + 1) if cur else 1
        db.ex("INSERT OR REPLACE INTO whatifs VALUES(?,?,?,?,?,?,?,0,?)",
              (w["id"], w["name"], *payload, ver, event))
        audit.log(AGENT, "write what-if", "whatif", w["id"], detail={"version": ver, "event": event})
        n += 1
    return n


# ------------------------------------------------------------------ re-scoring
RESCORE_RULES = {
    "CE-01": [("R01", 5, 5, "Asbestos removal ruled ineligible: Council bears full variation cost"),
              ("R22", 5, 4, "Ineligible asbestos cost S$0.35-0.60M lands entirely on ~S$1.18M headroom"),
              ("R08", 5, 5, "Programme change for asbestos not agreed; cost now fully Council's")],
    "CE-02": [("R06", 5, 5, "Sole EOI respondent withdrew; zero respondents vs policy minimum of three"),
              ("R17", 5, 5, "Tranche 2 cannot be claimed without a signed AAC agreement; no operator in prospect"),
              ("R21", 4, 3, "Appointment now later; AAC layout risk of rework rises")],
}


def rescore_proposals(event_id):
    out = []
    for rid, L, I, why in RESCORE_RULES.get(event_id, []):
        cur = db.q1("SELECT * FROM risks WHERE id=?", (rid,))
        if cur:
            out.append({"risk": rid, "from": [cur["likelihood"], cur["impact"], cur["score"]],
                        "to": [L, I, L * I], "rationale": why})
    return out


def apply_rescore(event_id, prop):
    cur = db.q1("SELECT * FROM risks WHERE id=?", (prop["risk"],))
    L, I, S = prop["to"]
    srcs = sorted(set(db.L(cur["sources"]) + [event_id]))
    db.ex("UPDATE risks SET likelihood=?, impact=?, score=?, note=?, sources=?, version=version+1, stale=0, origin=?"
          " WHERE id=?", (L, I, S, (cur["note"] + " | " if cur["note"] else "") + f"{event_id}: {prop['rationale']}",
                          db.J(srcs), f"change:{event_id}", prop["risk"]))
    audit.log(AGENT, "risk re-scored (approved)", "risk", prop["risk"], detail=prop)
