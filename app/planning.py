"""Module 1 - Planning Agent.
Scope statement, gap/Sponsor-Question register (with assumptions), conflict register,
WBS to Level 3 with dictionary and traceability, and a milestone plan with dependencies.

When an LLM is configured (default), scope, Sponsor Questions, WBS and milestones are
GENERATED from the brief, sponsor answers and data pack (`_llm_plan`), then validated:
unknown source ids are dropped, WBS hierarchy and traceability are enforced, milestone
dependencies must point backwards, and a date is kept only if a cited source states it.
The curated tables below (SCOPE, GAPS, WBS, MILESTONES) are the BASELINE: used when the
LLM is off (HCH_GENERATION=baseline or no key) or when the generated plan fails validation.
The conflict detectors are deterministic computations over the fact store in both modes."""
import re
from datetime import date

from . import audit, critic, db, gen, llm, sources
from .agents import AGENT_CARDS

AGENT = "planning"

# ------------------------------------------------------------------ baseline: scope
SCOPE = [
    ("SC01", "Upgraded multi-purpose sports hall", "BRIEF-p3-4", "in"),
    ("SC02", "New early childhood centre (~100 children) run by Little Harbour Learning", "BRIEF-p3-4", "in"),
    ("SC03", "Active ageing centre, operator to be appointed (Council procurement, tracked as dependency)", "BRIEF-p3-4", "in"),
    ("SC04", "Community kitchen and food court refresh", "BRIEF-p3-4", "in"),
    ("SC05", "Rooftop community garden", "BRIEF-p3-4", "in"),
    ("SC06", "Full barrier-free access and new lifts", "BRIEF-p3-4", "in"),
    ("SC07", "Replacement of M&E systems", "BRIEF-p3-4", "in"),
    ("SC08", "Improve accessibility and energy performance (objective)", "BRIEF-p3-3", "objective"),
    ("SC09", "Single design-and-build contract (contractor designs and builds)", "BRIEF-p3-6", "delivery"),
    ("SC10", "Hub remains open to residents throughout the works", "BRIEF-p3-6", "constraint"),
    ("SC11", "Residents consulted on the design (Council work package feeding design)", "SA-Q4", "in"),
    ("SC12", "Weekly EDC status update and monthly grant progress report", "BRIEF-p3-7", "in"),
    ("SC13", "60% central grant released in tranches against milestones (NRF conditions)", "BRIEF-p3-5", "constraint"),
    ("SC14", "Budget S$18.5M; 22 months construction from site possession", "BRIEF-p3-5", "constraint"),
    ("SC15", "Childcare operator wishes to begin enrolment in month 18", "BRIEF-p3-6", "constraint"),
    ("OS01", "OUT: tendering the D&B contract (already awarded 18 Dec 2026)", "SA-Q1", "out"),
    ("OS02", "OUT: fundraising for the 40% balance (Council capital reserves)", "SA-Q5", "out"),
]

# ------------------------------------------------------------------ gap checklist
# A planner's decision checklist run against the brief. Each item: what a planner
# needs, the brief evidence showing it is missing/contradictory, and where (if
# anywhere) the sponsor or the pack later resolved it.
GAPS = [
    ("GQ01", "Schedule basis", "Does the 22-month duration include tendering and design, and what is the start date?",
     "Brief gives 22 months but no start date or what the period covers.", ["BRIEF-p3-5"], 1,
     "Answered", "22 months is construction only, from site possession on 4 Jan 2027; design is on the critical path.", ["SA-Q1"], ["schedule"]),
    ("GQ02", "Completion commitment", "Which completion date is the commitment: 22 months from possession, 'fully open by Q4 2028', or KHB's 31 Dec 2028 practical completion - and what does 'fully open' mean?",
     "Brief states 22 months AND fully open by Q4 2028; these are different tests.", ["BRIEF-p3-5", "EDC-4.1", "EDC-4.2"], 1,
     "Open", "Programme reconciliation (EDC action 4.2) still outstanding at Meeting 5.", ["EDC-5.4", "NRF-4.2"], ["schedule", "completion"]),
    ("GQ03", "Hub open vs works", "How can lifts and M&E be replaced with the Hub open, and which areas may close in what order?",
     "Brief requires the Hub open throughout but includes new lifts and full M&E replacement.", ["BRIEF-p3-6", "BRIEF-p3-4"], 1,
     "Partially answered", "No closures agreed; short notified closures considered if shown necessary; no closure priority set - bring options as a decision.", ["SA-Q3"], ["closures"]),
    ("GQ04", "AAC operator", "Who appoints the active ageing centre operator, and by when?",
     "Brief says 'operator to be appointed' with no owner or date.", ["BRIEF-p3-4"], 1,
     "Answered (date open)", "Council procures separately; EOI Feb 2027; min. three responses; no confirmed date - track as dependency.", ["SA-Q2"], ["aac-operator"]),
    ("GQ05", "Childcare handover", "When must the childcare floor be handed over, and how long does the operator need for fit-out and licensing before enrolment?",
     "Brief gives enrolment in month 18 but no handover date or licensing period.", ["BRIEF-p3-6"], 1,
     "Open", "Operator asks 'by month 18'; KHB programme shows month 20; Seabreeze needed ~7 months.", ["EDC-2.2", "EDC-4.1", "EDC-4.3", "LL-L04"], ["childcare", "schedule"]),
    ("GQ06", "Grant conditions", "What are the grant conditions, eligible costs and tranche milestones?",
     "Brief: 'grant conditions will follow'.", ["BRIEF-p3-5"], 1,
     "Answered by data pack", "NRF letter: 60% of eligible cost, cap S$17.0M, T1-T4 conditions, food court and rooftop amenity ineligible.", ["NRF-1.1", "NRF-1.2", "NRF-1.3", "NRF-T2"], ["grant", "eligible-cost"]),
    ("GQ07", "Funding balance", "Who funds the remaining 40%?",
     "Brief states only the 60% grant.", ["BRIEF-p3-5"], 1,
     "Answered", "Town Council capital reserves; no fundraising package.", ["SA-Q5"], ["budget"]),
    ("GQ08", "Contingency", "Does the S$18.5M budget include a contingency, is the ~S$1.18M headroom that contingency, and who may draw on it?",
     "Brief gives a single budget figure; no contingency or drawdown authority.", ["BRIEF-p3-5", "EDC-1.2"], 1,
     "Open", "EDC 1.2: question raised, no decision recorded.", ["EDC-1.2"], ["budget", "contingency"]),
    ("GQ09", "Cost split by scope element", "What is the cost of each scope element, especially the ineligible food court refresh and rooftop garden?",
     "Brief has no cost breakdown; needed to compute eligible cost and the real grant.", ["BRIEF-p3-5", "NRF-1.3"], 1,
     "Open", "Finance paper figures not minuted (EDC 3.5): NOT FOUND in pack.", ["EDC-3.5"], ["eligible-cost", "budget"]),
    ("GQ10", "Consultation timing", "Is resident consultation before tender or during design-and-build, and who runs it?",
     "Brief says residents will be consulted, with no timing or owner.", ["BRIEF-p3-6"], 1,
     "Answered", "During D&B, 1-28 Feb 2027, run by Council Community Engagement; summary feeds design.", ["SA-Q4"], ["consultation"]),
    ("GQ11", "Success measure", "How is 'high resident satisfaction' measured, against what baseline and target?",
     "Success criterion has no metric.", ["BRIEF-p3-8"], 1, "Open", "", [], ["success"]),
    ("GQ12", "Energy target", "What energy-performance target or standard must the refurbishment meet?",
     "Objective mentions energy performance but no target.", ["BRIEF-p3-3"], 1, "Open", "", [], ["design"]),
    ("GQ13", "Temporary barrier-free access", "During the 14-week east core closure, how is barrier-free access to levels 3-4 kept, and is a temporary lift funded?",
     "Brief requires full barrier-free access and an open Hub; NRF 5.1 requires access during works.", ["BRIEF-p3-4", "NRF-5.1", "EDC-3.1"], 1,
     "Open", "Temporary lift possible but not priced; D07 temporary access plan overdue.", ["EDC-3.2", "DEL-D07"], ["accessibility", "lifts", "closures"]),
    ("GQ14", "Existing leases", "What happens to existing leases/licences (tuition centre, food court stalls) during closures - relocation or compensation?",
     "Brief notes all spaces are on leases or licences but says nothing about them during works.", ["BRIEF-p3-2"], 1, "Open", "", [], ["closures", "food-court"]),
    ("GQ15", "Change authority", "Who approves variations and scope changes, and up to what value, before they go to the EDC or the Fund?",
     "Brief gives no delegation or change-control thresholds.", ["BRIEF-p3-6"], 1,
     "Open", "NRF 4.1 needs Fund approval for social-service scope changes; internal thresholds NOT FOUND.", ["NRF-4.1"], ["variation", "scope"]),
    ("GQ16", "Reporting cadence", "What must the weekly EDC update contain, and does it stay weekly?",
     "Brief: 'short status update' weekly.", ["BRIEF-p3-7"], 0,
     "Partially answered", "EDC meets fortnightly from Feb with written updates in alternate weeks.", ["EDC-2.3", "LL-L07"], ["reporting"]),
    ("GQ17", "Rooftop garden", "Is the rooftop garden kept, deferred or re-scoped given its ineligibility and the roof slab strengthening need?",
     "Brief lists it in scope without structural or funding qualification.", ["BRIEF-p3-4", "NRF-1.3"], 1,
     "Open", "Deferral discussed, members divided, no decision.", ["EDC-6.3", "EDC-5.2"], ["rooftop"]),
    ("GQ18", "Hazardous materials", "Who commissions and pays for an intrusive hazardous-materials survey for this 1994 building?",
     "Brief is silent; pack shows survey not in original scope.", ["BRIEF-p3-2", "DEL-D06"], 1,
     "Open", "Asbestos since confirmed (EDC 6.5); survey still 'not in original scope'.", ["DEL-D06", "LL-L03"], ["hazmat", "asbestos"]),
    ("GQ19", "Operations after handover", "Who operates the Hub after completion and owns the 6-month utilisation report needed for Tranche 4?",
     "Brief ends at 'fully operational'.", ["BRIEF-p3-8", "NRF-T4"], 1, "Open", "", [], ["grant"]),
    ("GQ20", "Tracking system", "Who owns the move from spreadsheets to the PM tool and the data in it?",
     "Brief: 'Our current tracking is in spreadsheets'.", ["BRIEF-p3-7"], 0, "Open", "", [], ["reporting"]),
]

# ------------------------------------------------------------------ WBS
# code, name, scope refs, deliverable refs, owner, acceptance, tags
WBS = [
    ("1", "Project management & governance", ["SC12", "SC13", "SC14"], [], "Council PM", "", ["reporting"]),
    ("1.1", "Planning & controls", ["SC14"], [], "Council PM", "", ["schedule"]),
    ("1.1.1", "Scope statement, Sponsor Questions & assumption register", ["SC14"], [], "Council PM", "HC1 sign-off recorded", ["scope"]),
    ("1.1.2", "Baseline programme review & reconciliation (22 months vs Q4 2028)", ["SC14"], ["D03"], "Council PM", "Reconciled programme accepted by EDC", ["schedule", "completion"]),
    ("1.1.3", "Risk register maintenance & what-if analysis", ["SC14"], [], "Council PM", "HC4 approval of register", ["risk"]),
    ("1.2", "Reporting", ["SC12"], [], "Council PM", "", ["reporting"]),
    ("1.2.1", "Weekly/alternate-week EDC exception update", ["SC12"], [], "Council PM", "Critic PASS + HC5 release", ["reporting"]),
    ("1.2.2", "Monthly NRF progress report (by 10th working day)", ["SC12", "SC13"], ["D08", "D09", "D10"], "Council PM", "Contains NRF 3.2 items; Critic PASS; HC5", ["reporting", "grant", "eligible-cost"]),
    ("1.2.3", "NRF tranche claims T1-T4", ["SC13"], ["D11"], "Finance", "Claim submitted with evidence of condition", ["grant", "tranche-2"]),
    ("1.3", "Grant & budget control", ["SC13", "SC14"], [], "Finance", "", ["budget", "grant"]),
    ("1.3.1", "Eligible-cost tracking against S$17.0M cap", ["SC13"], [], "Finance", "Expenditure split eligible/ineligible each month", ["eligible-cost", "budget"]),
    ("1.3.2", "Contingency & variation control", ["SC14"], [], "Finance", "Every variation logged with funding source", ["contingency", "variation", "budget", "asbestos"]),
    ("2", "Design (design-and-build)", ["SC09"], [], "KHB", "", ["design"]),
    ("2.1", "Design stages", ["SC09"], [], "KHB", "", ["design"]),
    ("2.1.1", "Design stage 2 report", ["SC09", "SC11"], ["D04"], "KHB", "Council sign-off incl. consultation input", ["design", "consultation"]),
    ("2.1.2", "Design stage 3 (detailed) report", ["SC09"], ["D16"], "KHB", "Council sign-off", ["design"]),
    ("2.1.3", "Energy & accessibility design compliance", ["SC08", "SC06"], [], "KHB", "Target NOT FOUND - see GQ12", ["design", "accessibility"]),
    ("2.2", "Surveys & assessments", ["SC07", "SC05"], [], "KHB", "", ["design"]),
    ("2.2.1", "M&E condition survey", ["SC07"], ["D05"], "KHB", "Survey report accepted", ["design"]),
    ("2.2.2", "Hazardous materials survey", ["SC07"], ["D06"], "KHB", "Intrusive survey report (owner/funding open - GQ18)", ["hazmat", "asbestos"]),
    ("2.2.3", "Roof structural assessment", ["SC05"], ["D20"], "KHB", "Engineer's assessment accepted", ["rooftop", "roof"]),
    ("3", "Stakeholders, consultation & operators", ["SC11", "SC02", "SC03"], [], "Council PM", "", ["consultation"]),
    ("3.1", "Resident consultation", ["SC11"], [], "Community Engagement", "", ["consultation"]),
    ("3.1.1", "Consultation run (online, paper, town hall)", ["SC11"], [], "Community Engagement", "Closed 28 Feb 2027", ["consultation"]),
    ("3.1.2", "Consultation summary with bias & fairness check", ["SC11"], ["D15"], "Community Engagement", "HC7 sign-off", ["consultation"]),
    ("3.1.3", "Consultation output handed to contractor as design input", ["SC11", "SC09"], [], "Community Engagement", "Receipt by KHB recorded", ["consultation", "design"]),
    ("3.2", "Operators", ["SC02", "SC03"], [], "Estate Development", "", ["operator-agreements"]),
    ("3.2.1", "Childcare operator agreement (Little Harbour Learning)", ["SC02"], ["D13"], "Legal", "Signed agreement", ["childcare", "operator-agreements", "tranche-2"]),
    ("3.2.2", "AAC operator EOI & appointment", ["SC03"], ["D12"], "Council PM", ">=3 responses then appointment", ["aac-operator"]),
    ("3.2.3", "AAC operator agreement", ["SC03"], ["D14"], "UNASSIGNED (D14 owner not assigned)", "Signed agreement", ["aac-operator", "operator-agreements", "tranche-2"]),
    ("3.3", "Hub users & community communications", ["SC10"], [], "Council PM", "", ["closures"]),
    ("3.3.1", "Closure notices to users", ["SC10"], ["D18"], "Council PM", "Notice issued before closure", ["closures"]),
    ("3.3.2", "Weekly works notices at lift lobbies", ["SC10"], [], "Community Engagement", "Posted weekly", ["closures"]),
    ("4", "Phasing & keeping the Hub open", ["SC10"], [], "KHB", "", ["closures"]),
    ("4.1", "Phasing", ["SC10"], [], "KHB", "", ["closures"]),
    ("4.1.1", "Phasing plan review", ["SC10"], ["D02"], "Council PM", "Council decision recorded", ["closures"]),
    ("4.1.2", "Closure options & sponsor decision", ["SC10"], [], "Estate Development", "Sponsor decision with options compared", ["closures", "lifts", "schedule"]),
    ("4.1.3", "Temporary barrier-free access plan (lifts)", ["SC06", "SC10"], ["D07"], "KHB", "Plan accepted; access to all public floors", ["accessibility", "lifts", "closures"]),
    ("5", "Construction works", ["SC01", "SC02", "SC03", "SC04", "SC05", "SC06", "SC07"], [], "KHB", "", ["construction"]),
    ("5.1", "Enabling works", ["SC07"], [], "KHB", "", ["construction"]),
    ("5.1.1", "Site possession & hoarding", ["SC14"], ["D01"], "KHB", "Complete 4 Jan 2027", ["construction"]),
    ("5.1.2", "Soft-strip", ["SC07"], [], "KHB", "", ["construction", "asbestos"]),
    ("5.1.3", "Asbestos removal (level 2 west wing)", ["SC07"], [], "KHB", "Licensed removal + clearance certificate", ["asbestos", "variation", "eligible-cost", "schedule"]),
    ("5.2", "Sports hall", ["SC01"], [], "KHB", "", ["closures"]),
    ("5.2.1", "Sports hall roof & M&E replacement", ["SC01", "SC07"], [], "KHB", "", ["closures"]),
    ("5.2.2", "Sports hall upgrade & fit-out", ["SC01"], [], "KHB", "", []),
    ("5.3", "Early childhood centre", ["SC02"], [], "KHB", "", ["childcare"]),
    ("5.3.1", "Childcare floor works", ["SC02"], [], "KHB", "", ["childcare"]),
    ("5.3.2", "Childcare floor handover for fit-out", ["SC02", "SC15"], ["D21"], "KHB", "Handover in time for licensing (GQ05)", ["childcare", "schedule"]),
    ("5.4", "Active ageing centre", ["SC03"], [], "KHB", "", ["aac-operator"]),
    ("5.4.1", "AAC floor works", ["SC03"], [], "KHB", "", ["aac-operator"]),
    ("5.4.2", "AAC layout confirmation with appointed operator", ["SC03"], [], "Council PM", "Layout confirmed before fix (L05)", ["aac-operator"]),
    ("5.5", "Community kitchen & food court", ["SC04"], [], "KHB", "", ["food-court"]),
    ("5.5.1", "Kitchen exhaust & grease-trap works", ["SC04"], [], "KHB", "", ["food-court", "closures"]),
    ("5.5.2", "Kitchen exhaust permit application", ["SC04"], ["D19"], "KHB", "Permit granted", ["food-court"]),
    ("5.5.3", "Food court refresh fit-out (grant-ineligible)", ["SC04"], [], "KHB", "", ["food-court", "eligible-cost"]),
    ("5.6", "Rooftop community garden", ["SC05"], [], "KHB", "", ["rooftop"]),
    ("5.6.1", "Roof slab strengthening", ["SC05"], [], "KHB", "Cost NOT FOUND - not yet estimated", ["rooftop", "roof"]),
    ("5.6.2", "Rooftop garden works (grant-ineligible)", ["SC05"], [], "KHB", "", ["rooftop", "eligible-cost"]),
    ("5.7", "Accessibility & lifts", ["SC06"], [], "KHB", "", ["lifts", "accessibility"]),
    ("5.7.1", "Lift package award", ["SC06"], ["D17"], "KHB", "Award by due date", ["lifts", "closures"]),
    ("5.7.2", "East core lift replacement", ["SC06"], [], "KHB", "", ["lifts", "closures", "accessibility", "schedule"]),
    ("5.7.3", "Barrier-free access works (ramps, routes)", ["SC06"], [], "KHB", "", ["accessibility"]),
    ("5.8", "M&E replacement", ["SC07"], [], "KHB", "", ["construction"]),
    ("5.8.1", "Sprinkler mains replacement", ["SC07"], [], "KHB", "", ["construction"]),
    ("5.8.2", "Structural & M&E rough-in (incl. level 2 risers)", ["SC07"], [], "KHB", "Rough-in complete (NRF T2 condition)", ["tranche-2", "asbestos", "schedule"]),
    ("5.8.3", "Testing & commissioning", ["SC07"], [], "KHB", "", ["completion"]),
    ("6", "Completion, handover & grant close-out", ["SC13", "SC14"], [], "Council PM", "", ["completion"]),
    ("6.1", "Completion", ["SC14"], [], "KHB", "", ["completion"]),
    ("6.1.1", "Temporary Occupation Permit (whole facility)", ["SC13"], [], "KHB", "TOP issued (NRF T3)", ["completion", "grant"]),
    ("6.1.2", "Practical completion", ["SC14"], ["D22"], "KHB", "PC certificate", ["completion", "schedule"]),
    ("6.1.3", "Operator handovers & Hub fully open", ["SC02", "SC03", "SC14"], [], "Council PM", "All facilities open", ["completion", "childcare", "aac-operator"]),
    ("6.2", "Post-occupancy", ["SC13"], [], "Council PM", "", ["grant"]),
    ("6.2.1", "Six months operation & utilisation report (NRF T4)", ["SC13"], [], "UNASSIGNED (GQ19)", "Report submitted", ["grant"]),
]

# Candidate elements an eager planner (or LLM) might add. Traceability check rejects them.
CANDIDATES = [
    ("Tender the design-and-build contract", "OS01", ["SA-Q1"]),
    ("Fundraising campaign for the 40% balance", "OS02", ["SA-Q5"]),
    ("Relocate the tuition centre to a temporary site", None, ["BRIEF-p3-2"]),
    ("Car park resurfacing", None, []),
]

# ------------------------------------------------------------------ milestones
# id, name, wbs, relative, date(or None), depends, sources, note, tags
MILESTONES = [
    ("MS01", "Site possession", "5.1.1", "M+0", "2027-01-04", [], ["SA-Q1", "DEL-D01"], "", ["schedule"]),
    ("MS02", "Baseline programme submitted", "1.1.2", "M+1.7", "2027-02-24", ["MS01"], ["PR2-1", "DEL-D03"], "Due 2027-02-15; submitted late", ["schedule"]),
    ("MS03", "NRF Tranche 1 claim (award + baseline)", "1.2.3", "M+2.5", "2027-03-19", ["MS02"], ["NRF-T1", "EDC-6.1"], "", ["grant"]),
    ("MS04", "Resident consultation closed", "3.1.1", "M+1.8", "2027-02-28", [], ["SA-Q4", "EDC-5.3"], "", ["consultation"]),
    ("MS05", "Consultation summary to contractor", "3.1.3", "M+2.2", "2027-03-11", ["MS04"], ["DEL-D15", "EDC-6.4"], "Overdue - postponed twice", ["consultation"]),
    ("MS06", "Sponsor decision on closures", "4.1.2", "TBD", None, ["MS02"], ["SA-Q3", "PR3-3"], "NOT FOUND: no decision date. Lift works need a June 2027 start.", ["closures"]),
    ("MS07", "Design stage 2 sign-off", "2.1.1", "M+2.4", "2027-03-15", ["MS05"], ["DEL-D04"], "Overdue", ["design"]),
    ("MS08", "AAC operator appointed", "3.2.2", "TBD", None, [], ["SA-Q2", "EDC-4.4", "DEL-D12"], "Dependency, no confirmed date (EOI extended to 2027-04-30)", ["aac-operator"]),
    ("MS09", "Lift package award", "5.7.1", "M+4.4", "2027-05-15", ["MS06", "MS07"], ["DEL-D17"], "", ["lifts", "closures"]),
    ("MS10", "All operator agreements signed", "3.2.3", "M+5.9", "2027-06-30", ["MS08"], ["DEL-D13", "DEL-D14"], "D14 owner not assigned", ["operator-agreements", "aac-operator", "tranche-2"]),
    ("MS11", "Structural & M&E rough-in complete", "5.8.2", "TBD", None, ["MS09"], ["NRF-T2"], "NOT FOUND: date not in pack", ["tranche-2", "asbestos"]),
    ("MS12", "NRF Tranche 2 claim", "1.2.3", "TBD", None, ["MS10", "MS11"], ["NRF-T2"], "Needs rough-in AND all operator agreements", ["tranche-2", "grant"]),
    ("MS13", "Childcare floor handover for fit-out", "5.3.2", "M+18 (target) / M+20 (KHB)", "2028-06-30", ["MS09"], ["DEL-D21", "EDC-4.1", "EDC-2.2"], "CONFLICT: D21 due 2028-06-30 vs KHB programme Aug 2028", ["childcare", "schedule"]),
    ("MS14", "Practical completion", "6.1.2", "M+22 (brief) / M+24 (KHB)", "2028-12-31", ["MS11", "MS13"], ["EDC-4.1", "DEL-D22", "BRIEF-p3-5"], "CONFLICT: brief 22 months vs D22 2028-10-31 vs KHB 2028-12-31", ["completion", "schedule"]),
    ("MS15", "TOP + NRF Tranche 3 claim", "6.1.1", "after MS14", None, ["MS14"], ["NRF-T3"], "", ["completion", "grant"]),
    ("MS16", "Hub fully open", "6.1.3", "Q4 2028 (brief)", None, ["MS14"], ["BRIEF-p3-5"], "", ["completion"]),
    ("MS17", "Childcare first intake", "6.1.3", "M+24", "2029-01", ["MS13"], ["EDC-2.2"], "", ["childcare"]),
    ("MS18", "NRF Tranche 4 (6 months operation + utilisation report)", "6.2.1", "MS16 + 6 months", None, ["MS16"], ["NRF-T4"], "", ["grant"]),
]


def _add_months(d, m):
    y, mo = d.year + (d.month - 1 + m) // 12, (d.month - 1 + m) % 12 + 1
    return date(y, mo, min(d.day, 28))


def detect_conflicts():
    """Rule-based detectors. Each computes its evidence from the fact store and
    names every source involved instead of silently choosing one."""
    f = {r["id"]: r for r in db.q("SELECT * FROM facts")}
    out = []
    poss = date.fromisoformat(f["F10"]["value"])
    end22 = _add_months(poss, int(f["F03"]["value"]))
    out.append(("CF01", "Completion date",
                f"Brief: 22 months from possession {poss} -> about {end22.isoformat()} (computed); brief also says fully open by Q4 2028; "
                f"KHB baseline practical completion {f['F34']['value']}; deliverables D22 due 2028-10-31 with note 'Programme shows 31 Dec 2028'. "
                f"NRF 4.2: completion later than 31 Dec 2028 needs Fund approval.",
                ["BRIEF-p3-5", "SA-Q1", "EDC-4.1", "DEL-D22", "NRF-4.2"], ["schedule", "completion"],
                {"possession": str(poss), "plus_22_months": end22.isoformat(), "khb_pc": f["F34"]["value"]}))
    lic = int(f["F67"]["value"])
    need = _add_months(date(2029, 1, 1), -lic)
    out.append(("CF02", "Childcare handover vs licensing",
                f"Brief: enrolment month 18; operator wants handover 'by month 18' (D21 2028-06-30); KHB programme month 20 (Aug 2028). "
                f"First intake Jan 2029 minus Seabreeze licensing lead time {lic} months -> handover needed by about {need.strftime('%b %Y')} (computed).",
                ["BRIEF-p3-6", "EDC-2.2", "EDC-4.1", "EDC-4.3", "DEL-D21", "LL-L04"], ["childcare", "schedule"],
                {"handover_needed_by": need.isoformat()}))
    budget, share, cap, gmax = float(f["F01"]["value"]), float(f["F02"]["value"]), float(f["F24"]["value"]), float(f["F25"]["value"])
    implied = round(budget * share / 100, 2)
    out.append(("CF03", "Grant amount",
                f"Brief implies 60% of S${budget}M = S${implied}M (computed). NRF: 60% of ELIGIBLE cost, eligible capped at S${cap}M -> max S${gmax}M; "
                f"food court and rooftop amenity ineligible, so the real grant is lower still (element costs NOT FOUND).",
                ["BRIEF-p3-5", "NRF-1.1", "NRF-1.2", "NRF-1.3", "EDC-2.1"], ["grant", "eligible-cost", "budget"],
                {"brief_implied_grant": implied, "nrf_max_grant": gmax, "shortfall_vs_brief": round(implied - gmax, 2)}))
    head = round(budget - float(f["F19"]["value"]) - float(f["F20"]["value"]), 2)
    out.append(("CF04", "Budget headroom / contingency",
                f"S${budget}M - contract S${f['F19']['value']}M - fees S${f['F20']['value']}M = S${head}M (computed; minutes say about S$1.18M). "
                f"Not decided whether this is contingency. Asbestos estimate S$0.35-0.60M alone would use 30-51% of it.",
                ["BRIEF-p3-5", "EDC-1.1", "EDC-1.2", "EDC-5.1"], ["budget", "contingency", "asbestos"], {"headroom": head}))
    out.append(("CF05", "Hub open vs closures vs accessibility",
                "Brief/EDC: Hub remains open throughout. KHB phasing proposes east core 14 wks (no barrier-free access to L3-4), sports hall 10 wks, food court 6 wks, "
                "and L2 west wing 6 wks (asbestos). NRF 5.1 requires barrier-free access to all public floors. Sponsor: no closures agreed.",
                ["BRIEF-p3-6", "EDC-1.3", "EDC-3.1", "PR3-5", "NRF-5.1", "SA-Q3"], ["closures", "accessibility", "lifts"], {}))
    out.append(("CF06", "EDC meeting cadence",
                "Brief and EDC 1.6: weekly. EDC 2.3: fortnightly from February with written updates in alternate weeks.",
                ["BRIEF-p3-7", "EDC-1.6", "EDC-2.3"], ["reporting"], {}))
    out.append(("CF07", "Hazardous materials",
                "Seed register R08 'not expected per desk study', status Closed; asbestos (chrysotile) confirmed in L2 (EDC 6.5, PR3). "
                "D06 hazardous survey 'Not in original scope'. Seabreeze L03 recommended intrusive survey for pre-2000 buildings.",
                ["RISK-R08", "EDC-5.1", "EDC-6.5", "PR3-3", "DEL-D06", "LL-L03"], ["hazmat", "asbestos"], {}))
    out.append(("CF08", "Contractor progress narrative vs numbers",
                "PR3 says 'broadly on programme' while physical progress is 3.5% vs 6.0% planned (-2.5%), design 26% vs 35%, submittals 10 vs 19.",
                ["PR3-1", "PR3-2"], ["progress"], {"physical_variance_pct": -2.5}))
    out.append(("CF09", "AAC appointment due date",
                "D12 appointment due 2027-03-31 (Overdue) while EOI was extended to 30 Apr 2027 with one response; sponsor says no confirmed date.",
                ["DEL-D12", "EDC-4.4", "SA-Q2"], ["aac-operator"], {}))
    out.append(("CF10", "Data quality in deliverables schedule",
                "Mixed date formats (D03 actual '24/02/2027', D10 due '14/04/2027'); D20 'Submitted - no date recorded'; D14 has no owner.",
                ["DEL-D03", "DEL-D10", "DEL-D20", "DEL-D14"], ["data-quality"], {}))
    out.append(("CF11", "Seed risk register quality",
                "R03 and R04 duplicate (noise); R01 owner left Council Aug 2026; R11 has no owner or mitigation; register not updated since June 2025.",
                ["RISK-R03", "RISK-R04", "RISK-R01", "RISK-R11", "RISK-note"], ["risk"], {}))
    out.append(("CF12", "Asbestos variation status",
                "EDC 6.5 (25 Mar): variation 'to be raised by KHB'; PR3 (6 Apr): 'To be submitted'. "
                "Any later statement that the variation was submitted at the March meeting conflicts with both.",
                ["EDC-6.5", "PR3-4"], ["asbestos", "variation"], {}))
    db.ex("DELETE FROM conflicts")
    db.exmany("INSERT INTO conflicts(id,topic,detail,sources,tags,computed) VALUES(?,?,?,?,?,?)",
              [(a, b, c, db.J(d), db.J(e), db.J(g)) for a, b, c, d, e, g in out])
    return len(out)


def _llm_extra_gaps():
    """Optional: ask the LLM for gaps missing from the checklist. Each proposal must cite
    an existing BRIEF chunk; it enters as 'Proposed (LLM)' and needs HC1 like the rest."""
    if not llm.available():
        return 0
    brief = db.q("SELECT id,text FROM sources WHERE id LIKE 'BRIEF-p3-%'")
    have = "\n".join(f"- {g[2]}" for g in GAPS)
    src = "\n\n".join(f"[{b['id']}]\n{b['text']}" for b in brief)
    sysmsg = next(a for a in AGENT_CARDS if a["id"] == AGENT)["system_prompt"]
    user = (f"SOURCES (the sponsor brief):\n{src}\n\nQuestions already raised:\n{have}\n\n"
            "List up to 5 ADDITIONAL decisions a planner needs that the brief leaves missing or contradictory. "
            'Return JSON {"gaps":[{"question":"...","why":"...","source":"BRIEF-p3-x"}]}. Use only the source ids shown.')
    data, _ = llm.chat_json(AGENT, sysmsg, user)
    n = 0
    for i, g in enumerate((data or {}).get("gaps", [])[:5], start=1):
        if not sources.get(g.get("source", "")) or not g.get("question"):
            audit.log(AGENT, "reject llm gap", "gap", "", outcome="rejected", detail={"reason": "bad citation", "gap": g})
            continue
        gid = f"GQL{i:02d}"
        db.ex("INSERT OR REPLACE INTO gaps VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
              (gid, "LLM-proposed", g["question"], g.get("why", ""), db.J([g["source"]]), 1,
               "Proposed (LLM) - needs HC1", "", db.J([]), "", "llm", db.J([])))
        n += 1
    return n


def _change_annotations(text):
    return [seg for seg in (text or "").split(" | ") if "(CE-" in seg]


# ------------------------------------------------------------------ LLM generation
GAP_STATUS = ("Open", "Partially answered", "Answered", "Answered by data pack", "Answered (date open)")
SCOPE_KINDS = ("in", "objective", "delivery", "constraint", "out")


def _code_key(code):
    return tuple(int(x) for x in code.split("."))


def _sys():
    return "You are the Planning Agent for the Harbourline Community Hub Refurbishment. " + gen.GROUND


def _gen_scope_gaps():
    user = (f"SOURCES:\n{gen.block(['BRIEF-p3-', 'SA-', 'NRF-', 'EDC-', 'DEL-', 'LL-'])}\n\n"
            "TASK. Draft (a) the scope statement and (b) the register of Questions for the Sponsor.\n"
            "(a) scope: 12-20 lines. Use id SC01, SC02 ... for in-scope work, objectives, delivery approach and "
            "constraints, and OS01, OS02 ... for work the sponsor answers put explicitly OUT of scope. "
            f"kind is one of {list(SCOPE_KINDS)}. source is the single chunk id that states the line.\n"
            "(b) gaps: 15-25 decisions a planner needs that the BRIEF leaves missing, vague or contradictory. "
            "'why' says what the brief is missing; 'sources' cites the BRIEF chunk(s). Then check the sponsor answers "
            f"and data pack: status is one of {list(GAP_STATUS)}; 'answer' summarises what the sources say "
            "(empty when Open) and 'answer_sources' cites them. sponsor_only is true when only the sponsor can decide. "
            f"tags are chosen only from {gen.TAGS}.\n"
            'Return {"scope":[{"id":"SC01","text":"","source":"","kind":""}],'
            '"gaps":[{"id":"GQ01","category":"","question":"","why":"","sources":[],"sponsor_only":true,'
            '"status":"","answer":"","answer_sources":[],"tags":[]}]}')
    data, _ = llm.cached_json(AGENT, _sys(), user, max_tokens=6000)
    if not data:
        return None, None, "no JSON from LLM (scope/gaps)"
    scope, seen = [], set()
    for s in data.get("scope", []):
        sid, src = str(s.get("id", "")), gen.known([s.get("source")])
        if not re.fullmatch(r"(SC|OS)\d\d", sid) or sid in seen or not src or not str(s.get("text", "")).strip():
            continue
        kind = s.get("kind") if s.get("kind") in SCOPE_KINDS else ("out" if sid.startswith("OS") else "in")
        text = s["text"].strip()
        if kind == "out" and not text.upper().startswith("OUT"):
            text = "OUT: " + text
        seen.add(sid)
        scope.append((sid, text, src[0], kind))
    gaps, seen = [], set()
    for g in data.get("gaps", []):
        gid, srcs = str(g.get("id", "")), gen.known(g.get("sources"))
        if not re.fullmatch(r"GQ\d\d", gid) or gid in seen or not srcs or not str(g.get("question", "")).strip():
            continue
        status = g.get("status") if g.get("status") in GAP_STATUS else "Open"
        ans_src = gen.known(g.get("answer_sources"))
        if status != "Open" and not ans_src:          # an answer must be sourced
            status = "Open"
        seen.add(gid)
        gaps.append((gid, str(g.get("category", "")).strip() or "General", g["question"].strip(), str(g.get("why", "")).strip(),
                     srcs, 1 if g.get("sponsor_only", True) else 0, status,
                     str(g.get("answer", "")).strip() if status != "Open" else "", ans_src if status != "Open" else [],
                     gen.tags(g.get("tags"))))
    if sum(1 for s in scope if s[3] != "out") < 8:
        return None, None, f"too few valid scope lines ({len(scope)})"
    if len(gaps) < 10:
        return None, None, f"too few valid Sponsor Questions ({len(gaps)})"
    return scope, gaps, ""


def _gen_wbs(scope):
    lines = "\n".join(f"{s[0]} ({s[3]}): {s[1]}" for s in scope)
    user = (f"SCOPE LINES (the only valid scope_refs):\n{lines}\n\n"
            f"CONTRACT DELIVERABLES (valid deliverable_refs are the D numbers):\n{gen.block(['DEL-D'])}\n\n"
            f"SOURCES (context):\n{gen.block(['BRIEF-p3-', 'SA-', 'NRF-'])}\n\n"
            "TASK. Build the Work Breakdown Structure to Level 3 with a dictionary entry per element. 50-80 elements, "
            "codes '1', '1.1', '1.1.1' (no Level 4). 5-8 Level-1 elements; every Level-1 has Level-2 children and every "
            "Level-2 has 2-4 Level-3 children. Cover: project management, reporting and grant/budget control; design "
            "(design-and-build); consultation and operators; phasing and keeping the Hub open; construction for every "
            "in-scope element; completion, handover and grant close-out.\n"
            "Each element: scope_refs = the SC ids it traces to (never an OS id); deliverable_refs = D numbers (e.g. "
            "'D04'); owner = an organisation or role named in the sources (e.g. KHB, Council PM, Finance, Legal, "
            "Community Engagement, Estate Development), or 'UNASSIGNED (<why>)' when the sources say no owner; "
            f"acceptance = acceptance criterion (may be empty); tags only from {gen.TAGS}.\n"
            "Work a planner might be tempted to add but that traces only to an OS line or to no scope line goes in "
            "'rejected' (name, reason, sources) instead of the WBS.\n"
            'Return {"wbs":[{"code":"1","name":"","scope_refs":[],"deliverable_refs":[],"owner":"","acceptance":"","tags":[]}],'
            '"rejected":[{"name":"","reason":"","sources":[]}]}')
    data, _ = llm.cached_json(AGENT, _sys(), user, max_tokens=8000)
    if not data:
        return None, None, "no JSON from LLM (WBS)"
    dels = {d["id"][4:] for d in db.q("SELECT id FROM sources WHERE id LIKE 'DEL-D%'")}
    rows, codes = {}, set()
    for w in data.get("wbs", []):
        code = str(w.get("code", "")).strip().rstrip(".")
        if not re.fullmatch(r"\d+(\.\d+){0,2}", code) or code in codes or not str(w.get("name", "")).strip():
            continue
        codes.add(code)
        owner = str(w.get("owner", "")).strip() or "UNASSIGNED (owner not stated in sources)"
        rows[code] = (code, w["name"].strip(), [str(r) for r in w.get("scope_refs", []) if str(r).strip()],
                      sorted({str(d).replace("DEL-", "") for d in w.get("deliverable_refs", [])} & dels),
                      owner, str(w.get("acceptance", "") or "").strip(), gen.tags(w.get("tags")))
    wbs = [rows[c] for c in sorted(rows, key=_code_key)
           if "." not in c or c.rsplit(".", 1)[0] in rows]          # orphans (missing parent) are dropped
    l1 = sum(1 for w in wbs if "." not in w[0])
    l3 = sum(1 for w in wbs if w[0].count(".") == 2)
    if l1 < 4 or l3 < 25:
        return None, None, f"WBS too shallow (L1={l1}, L3={l3})"
    rejected = [(str(r.get("name", "")).strip(), str(r.get("reason", "")).strip() or "No scope line",
                 gen.known(r.get("sources"))) for r in data.get("rejected", []) if str(r.get("name", "")).strip()]
    return wbs, rejected, ""


def _date_supported(d, srcs):
    """Keep a generated date only if a cited source states it (critic date tracer)."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return not critic.trace_claim({"text": d, "cites": srcs})
    if re.fullmatch(r"\d{4}-\d{2}", d):
        y, m = d.split("-")
        mon = critic.MONTHS[int(m) - 1]
        texts = [(sources.get(s) or {}).get("text", "").lower() for s in srcs]
        return any(y in t and (mon in t or mon[:3] in t) for t in texts)
    return False


def _gen_milestones(wbs):
    lines = "\n".join(f"{w[0]} {w[1]}" for w in wbs)
    user = (f"WBS (the only valid wbs codes):\n{lines}\n\n"
            f"SOURCES:\n{gen.block(['BRIEF-p3-5', 'BRIEF-p3-6', 'SA-', 'EDC-', 'DEL-', 'NRF-', 'PR3-', 'LL-L04'])}\n\n"
            "TASK. Milestone plan with dependencies: 12-20 milestones in relative time from site possession "
            "('M+0', 'M+4.4', 'M+22') until the sponsor gives dates. ids MS01, MS02 ... listed in dependency order: "
            "depends_on may only name EARLIER milestones. 'date' is ISO yyyy-mm-dd (or yyyy-mm) ONLY when a cited "
            "source states that date; otherwise null, rel 'TBD' or 'after MSnn', and the note says NOT FOUND. Where "
            "sources give different dates for the same milestone, keep the earliest commitment as date and write "
            "'CONFLICT: ...' in the note citing all sources. Include site possession, baseline programme, the grant "
            "tranche claims T1-T4 and their conditions, consultation, closures decision, operator appointment and "
            "agreements, lift package, childcare handover, practical completion and Hub fully open. "
            f"tags only from {gen.TAGS}.\n"
            'Return {"milestones":[{"id":"MS01","name":"","wbs":"","rel":"","date":null,"depends_on":[],'
            '"sources":[],"note":"","tags":[]}]}')
    data, _ = llm.cached_json(AGENT, _sys(), user, max_tokens=5000)
    if not data:
        return None, "no JSON from LLM (milestones)"
    codes = {w[0] for w in wbs}
    out, ids = [], []
    for m in data.get("milestones", []):
        mid, srcs = str(m.get("id", "")), gen.known(m.get("sources"))
        wcode = str(m.get("wbs", "")).strip()
        if not re.fullmatch(r"MS\d\d", mid) or mid in ids or wcode not in codes or not srcs:
            continue
        note = str(m.get("note", "") or "").strip()
        rel = str(m.get("rel", "") or "").strip() or "TBD"
        d = m.get("date")
        d = str(d).strip() if d not in (None, "", "null") else None
        if d and not _date_supported(d, srcs):
            note = (note + " | " if note else "") + f"LLM date {d} rejected: not stated in cited sources (NOT FOUND)."
            d = None
        if not d and not rel.startswith(("TBD", "after", "Q4", "MS")) and "NOT FOUND" not in note:
            note = (note + " | " if note else "") + "Date NOT FOUND in sources."
        deps = [x for x in m.get("depends_on", []) if x in ids]          # backwards only -> acyclic
        ids.append(mid)
        out.append((mid, str(m.get("name", "")).strip() or mid, wcode, rel, d, deps, srcs, note, gen.tags(m.get("tags"))))
    if len(out) < 8:
        return None, f"too few valid milestones ({len(out)})"
    return out, ""


def _llm_plan():
    scope, gaps, why = _gen_scope_gaps()
    if why:
        return None, why
    wbs, rejected, why = _gen_wbs(scope)
    if why:
        return None, why
    ms, why = _gen_milestones(wbs)
    if why:
        return None, why
    return {"scope": scope, "gaps": gaps, "wbs": wbs, "rejected": rejected, "milestones": ms}, ""


def run(use_llm=True):
    """Full planning pass. LLM-generated (validated) when an LLM is configured, curated
    baseline otherwise; both are deterministic for the same inputs (temperature 0 + cache).
    Human-approved change annotations (HC6) on milestones and gaps are carried over."""
    keep_ms = {m["id"]: _change_annotations(m["note"]) for m in db.q("SELECT id, note FROM milestones")}
    keep_gap = {g["id"]: (_change_annotations(g["answer"]), [s for s in db.L(g["answer_sources"]) if s.startswith("CE-")])
                for g in db.q("SELECT id, answer, answer_sources FROM gaps")}
    plan, why = (_llm_plan() if llm.generation_enabled(use_llm) else
                 (None, "LLM not configured" if not llm.available() else "baseline mode requested"))
    if plan:
        scope, gaps, wbs_rows, milestones = plan["scope"], plan["gaps"], plan["wbs"], plan["milestones"]
        flagged_extra = [(n, r + " - flagged, not kept", s) for n, r, s in plan["rejected"]]
        gap_origin = "llm"
    else:
        scope, gaps, wbs_rows, milestones = SCOPE, GAPS, WBS, MILESTONES
        flagged_extra = [(n, (f"Traces only to out-of-scope line {ref}" if ref else "No scope line in brief or sponsor answers")
                          + " - flagged, not kept", s) for n, ref, s in CANDIDATES]
        gap_origin = "checklist"
    db.ex("DELETE FROM scope_lines")
    db.exmany("INSERT INTO scope_lines(id,text,source_id,kind) VALUES(?,?,?,?)", scope)
    db.ex("DELETE FROM gaps")
    rows = []
    for (gid, cat, qn, why_, srcs, sponsor_only, status, ans, ans_src, tags) in gaps:
        assumption = "" if status.startswith("Answered") else f"ASSUMPTION A-{gid[2:]}: until the sponsor answers, plan treats this as unresolved and tracks it as a risk/decision."
        rows.append((gid, cat, qn, why_, db.J(srcs), sponsor_only, status, ans, db.J(ans_src), assumption, gap_origin, db.J(tags)))
    db.exmany("INSERT INTO gaps VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    n_llm = _llm_extra_gaps() if (not plan and llm.generation_enabled(use_llm)) else 0
    n_conf = detect_conflicts()

    # WBS with traceability check: an element whose scope refs are missing or not all
    # in-scope lines is flagged, not kept (applies to generated and baseline WBS alike)
    scope_ids = {s[0] for s in scope if s[3] != "out"}
    db.ex("DELETE FROM wbs")
    db.ex("DELETE FROM wbs_flagged")
    kept, kept_codes = [], set()
    for i, (code, name, refs, dels, owner, acc, tags) in enumerate(wbs_rows):
        parent = code.rsplit(".", 1)[0] if "." in code else None
        if not refs or not set(refs) <= scope_ids or (parent and parent not in kept_codes):
            why_f = "no scope line" if not refs else ("traces to a line that is not in scope" if not set(refs) <= scope_ids
                                                       else f"parent {parent} not kept")
            db.ex("INSERT OR REPLACE INTO wbs_flagged VALUES(?,?,?)", (name, why_f + " - flagged, not kept", db.J(refs)))
            continue
        level = code.count(".") + 1
        src = [s for (sid, _, s, _) in scope if sid in refs] + [f"DEL-{d}" for d in dels]
        kept.append((code, level, parent, name, _dictionary(code, name, refs, dels, owner, acc), db.J(refs),
                     db.J(dels), owner, acc, db.J(sorted(set(src))), db.J(tags), i))
        kept_codes.add(code)
    db.exmany("INSERT INTO wbs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", kept)
    for name, reason, src in flagged_extra:
        db.ex("INSERT OR REPLACE INTO wbs_flagged VALUES(?,?,?)", (name, reason, db.J(src)))

    milestones = [m for m in milestones if m[2] in kept_codes]
    ms_ids = {m[0] for m in milestones}
    db.ex("DELETE FROM milestones")
    db.exmany("INSERT INTO milestones VALUES(?,?,?,?,?,?,?,?,?,?)",
              [(m[0], m[1], m[2], m[3], m[4], db.J([d for d in m[5] if d in ms_ids]), db.J(m[6]),
                " | ".join([m[7]] + keep_ms.get(m[0], [])).strip(" |"), db.J(m[8]), i) for i, m in enumerate(milestones)])
    for gid, (ann, srcs) in keep_gap.items():
        if ann:
            g = db.q1("SELECT answer, answer_sources FROM gaps WHERE id=?", (gid,))
            if g:
                db.ex("UPDATE gaps SET answer=?, answer_sources=? WHERE id=?",
                      (" | ".join([g["answer"]] + ann).strip(" |"), db.J(sorted(set(db.L(g["answer_sources"]) + srcs))), gid))
    mode = "llm" if plan else "baseline"
    gen.set_origin(AGENT, mode, "" if plan else why, scope=len(scope), gaps=len(gaps), wbs=len(kept), milestones=len(milestones))
    audit.log(AGENT, "write plan", "plan", mode,
              detail={"scope": len(scope), "gaps": len(gaps) + n_llm, "conflicts": n_conf, "wbs": len(kept),
                      "milestones": len(milestones), "origin": mode})
    audit.handoff(AGENT, "risk", "wbs+milestones", len(kept))
    return {"origin": mode, "fallback_reason": "" if plan else why, "scope_lines": len(scope), "gaps": len(gaps) + n_llm,
            "llm_gaps": n_llm, "conflicts": n_conf, "wbs": len(kept), "flagged": len(db.q("SELECT name FROM wbs_flagged")),
            "milestones": len(milestones)}


def _dictionary(code, name, refs, dels, owner, acc):
    parts = [f"{code} {name}.", f"Traces to scope: {', '.join(refs)}."]
    if dels:
        parts.append(f"Contract deliverables: {', '.join(dels)}.")
    parts.append(f"Owner: {owner}.")
    if acc:
        parts.append(f"Acceptance: {acc}.")
    return " ".join(parts)


def scope_statement():
    sl = db.q("SELECT * FROM scope_lines")
    return {
        "title": "Harbourline Community Hub Refurbishment - Scope statement (draft for HC1)",
        "objective": {"text": "Refurbish the Hub into an integrated community facility that serves residents of all ages, "
                              "improves accessibility and energy performance, and becomes the estate's flagship shared space.",
                      "source": sources.cite("BRIEF-p3-3")},
        "lines": [dict(s, cite=sources.cite(s["source_id"])) for s in sl],
        "success": {"text": "A fully operational Hub, delivered on budget, with high resident satisfaction (metric NOT FOUND - see GQ11).",
                    "source": sources.cite("BRIEF-p3-8")},
    }


def unresolved_dates():
    return [m for m in db.q("SELECT * FROM milestones ORDER BY sort") if not m["date"]]


def plan_snapshot():
    return {"wbs": db.q("SELECT * FROM wbs ORDER BY sort"), "milestones": db.q("SELECT * FROM milestones ORDER BY sort")}


def critical_path_check():
    """Simple dependency sanity: every dependency must exist and precede (where both dated)."""
    ms = {m["id"]: m for m in db.q("SELECT * FROM milestones")}
    issues = []
    for m in ms.values():
        for d in db.L(m["depends_on"]):
            if d not in ms:
                issues.append(f"{m['id']} depends on unknown {d}")
            elif ms[d]["date"] and m["date"] and ms[d]["date"] > m["date"]:
                issues.append(f"{m['id']} ({m['date']}) is dated before its predecessor {d} ({ms[d]['date']})")
    return issues


def plan_hash():
    """HC2 approves a specific plan version: any change to WBS or milestones needs re-approval."""
    import hashlib
    snap = plan_snapshot()
    return hashlib.sha256(db.J(snap).encode()).hexdigest()[:12]
