"""The fact store's data contract. Every fact names the source chunk and an exact quote.
`verify()` re-reads the source at ingest and refuses any fact whose quote is not present,
so nothing in this list can be an invention. Reports may only state facts from here
(or values computed from them, with the formula shown)."""

F = [
    # id, label, value, unit, source chunk, quote, tags
    ("F01", "Approved budget", "18.5", "S$M", "BRIEF-p3-5", "Approved budget is S$18.5 million", ["budget"]),
    ("F02", "Grant share stated in brief", "60", "%", "BRIEF-p3-5", "Sixty per cent is funded by a central grant released in tranches", ["grant", "budget"]),
    ("F03", "Works duration (brief)", "22", "months", "BRIEF-p3-5", "Works are to complete within 22 months", ["schedule", "completion"]),
    ("F04", "Hub fully open (brief)", "Q4 2028", "", "BRIEF-p3-5", "Hub fully open by the fourth quarter of 2028", ["schedule", "completion"]),
    ("F05", "Hub must remain open during works", "yes", "", "BRIEF-p3-6", "The Hub must remain open to residents throughout the works", ["closures", "accessibility"]),
    ("F06", "Childcare enrolment start (brief)", "month 18", "", "BRIEF-p3-6", "Little Harbour Learning wishes to begin enrolment in month 18", ["childcare", "schedule"]),
    ("F07", "Childcare capacity", "100", "children", "BRIEF-p3-4", "early childhood centre for about 100 children", ["childcare"]),
    ("F08", "EDC meeting cadence (brief)", "weekly", "", "BRIEF-p3-7", "The Estate Development Committee meets weekly", ["reporting"]),
    ("F09", "Building completed", "1994", "", "BRIEF-p3-2", "four-storey building completed in 1994", ["hazmat"]),
    ("F10", "Site possession date", "2027-01-04", "date", "SA-Q1", "Site possession is Monday 4 January 2027", ["schedule"]),
    ("F11", "22 months = construction only", "construction only", "", "SA-Q1", "The 22 months is construction only, counted from site possession", ["schedule"]),
    ("F12", "D&B contract award date", "2026-12-18", "date", "SA-Q1", "awarded on 18 December 2026", ["schedule"]),
    ("F13", "AAC operator appointment date", "none confirmed", "", "SA-Q2", "There is no confirmed appointment date", ["aac-operator"]),
    ("F14", "Procurement rule: minimum EOI responses", "3", "responses", "SA-Q2", "requires at least three responses before an appointment", ["aac-operator"]),
    ("F15", "Closures agreed", "none", "", "SA-Q3", "No closures have been agreed yet", ["closures"]),
    ("F16", "Closure priority set by Council", "not set", "", "SA-Q3", "The Council has not set a closure priority among them", ["closures"]),
    ("F17", "Consultation period", "1-28 Feb 2027", "", "SA-Q4", "It runs 1 to 28 February 2027", ["consultation"]),
    ("F18", "Balance funding source", "Town Council capital reserves", "", "SA-Q5", "The Town Council funds the balance from its own capital reserves", ["budget", "grant"]),
    ("F19", "Contract sum", "16.42", "S$M", "EDC-1.1", "at a contract sum of S$16.42 million", ["budget"]),
    ("F20", "Consultancy & authority fees (outside contract)", "0.90", "S$M", "EDC-1.1", "estimated at S$0.90 million, held outside the contract", ["budget"]),
    ("F21", "Budget headroom after contract and fees", "1.18", "S$M", "EDC-1.2", "leaves about S$1.18 million", ["budget", "contingency"]),
    ("F22", "Headroom treated as contingency?", "no decision recorded", "", "EDC-1.2", "No decision recorded", ["contingency"]),
    ("F23", "EDC cadence from Feb 2027", "fortnightly", "", "EDC-2.3", "the EDC will meet FORTNIGHTLY from February", ["reporting"]),
    ("F24", "Eligible cost cap", "17.0", "S$M", "NRF-1.2", "Eligible project cost is capped at S$17.0 million", ["grant", "eligible-cost"]),
    ("F25", "Maximum grant", "10.2", "S$M", "NRF-1.2", "Maximum grant S$10.2 million", ["grant", "eligible-cost"]),
    ("F26", "Ineligible items", "food court; rooftop amenity", "", "NRF-1.3", "refurbishment of commercial premises (including food courts and leased retail), and landscaping or rooftop amenity", ["grant", "eligible-cost", "food-court", "rooftop"]),
    ("F27", "Cost above cap borne by", "recipient", "", "NRF-1.4", "Cost increases above the cap are borne by the recipient", ["grant", "eligible-cost"]),
    ("F28", "Childcare enrolment opens", "July 2028", "", "EDC-2.2", "open enrolment in July 2028", ["childcare", "schedule"]),
    ("F29", "First childcare intake", "January 2029", "", "EDC-2.2", "admit the first children in January 2029", ["childcare", "schedule"]),
    ("F30", "Childcare handover requested", "by month 18", "", "EDC-2.2", "childcare floor \"by month 18\"", ["childcare", "schedule"]),
    ("F31", "East core closure (2 lifts)", "14", "weeks", "EDC-3.1", "closing the east core for about 14 weeks", ["closures", "lifts", "accessibility"]),
    ("F32", "Sports hall closure", "10", "weeks", "EDC-3.1", "hall closed for about 10 weeks", ["closures"]),
    ("F33", "Food court closure", "6", "weeks", "EDC-3.1", "food court must close for 6 weeks", ["closures", "food-court"]),
    ("F34", "Practical completion (KHB baseline)", "2028-12-31", "date", "EDC-4.1", "practical completion 31 December 2028", ["schedule", "completion"]),
    ("F35", "Childcare handover (KHB baseline)", "month 20 (August 2028)", "", "EDC-4.1", "month 20 (August 2028)", ["childcare", "schedule"]),
    ("F36", "AAC EOI responses", "1", "response", "EDC-4.4", "one response received", ["aac-operator"]),
    ("F37", "AAC EOI extended to", "2027-04-30", "date", "EDC-4.4", "EOI extended to 30 April 2027", ["aac-operator"]),
    ("F38", "Asbestos removal estimate", "0.35-0.60", "S$M", "EDC-5.1", "S$0.35–0.60 million and 4–6 weeks", ["asbestos", "variation", "budget"]),
    ("F39", "Asbestos removal duration", "4-6", "weeks", "EDC-5.1", "S$0.35–0.60 million and 4–6 weeks", ["asbestos", "schedule"]),
    ("F40", "Works stopped in L2 west wing", "2027-03-03", "date", "EDC-5.1", "Works in that zone stopped on 3 March", ["asbestos"]),
    ("F41", "Roof slab strengthening cost", "not yet estimated", "", "EDC-5.2", "Cost not yet estimated", ["rooftop", "roof"]),
    ("F42", "Consultation responses", "214", "responses", "EDC-5.3", "214 responses recorded", ["consultation"]),
    ("F43", "Programme reconciliation (action 4.2)", "not done", "", "EDC-5.4", "has not yet reconciled the programme", ["schedule", "completion"]),
    ("F44", "NRF Tranche 1 claim submitted", "2027-03-19", "date", "EDC-6.1", "NRF Tranche 1 claim submitted 19 March", ["grant"]),
    ("F45", "Tranche 2 needs all operator agreements", "yes", "", "NRF-T2", "signed operator agreements for ALL social service spaces", ["tranche-2", "aac-operator", "operator-agreements"]),
    ("F46", "Rooftop garden deferral", "no decision recorded", "", "EDC-6.3", "no decision recorded", ["rooftop"]),
    ("F47", "Asbestos type", "chrysotile", "", "EDC-6.5", "confirmed chrysotile in level 2 ceiling boards", ["asbestos"]),
    ("F48", "Asbestos removal sequence", "not agreed", "", "EDC-6.5", "Removal sequence not yet agreed", ["asbestos"]),
    ("F49", "Next EDC meeting", "2027-04-08", "date", "EDC-6.6", "Next meeting: Thursday 8 April 2027", ["reporting"]),
    ("F50", "Physical progress planned (Mar)", "6.0", "%", "PR3-2", "Overall physical progress 6.0% 3.5% -2.5%", ["progress"]),
    ("F51", "Physical progress actual (Mar)", "3.5", "%", "PR3-2", "Overall physical progress 6.0% 3.5% -2.5%", ["progress"]),
    ("F52", "Design completion planned / actual (Mar)", "35 / 26", "%", "PR3-2", "Design (D&B) completion 35% 26% -9%", ["progress", "design"]),
    ("F53", "Submittals approved planned / actual (Mar)", "19 / 10", "", "PR3-2", "Submittals approved 19 10 -9", ["progress", "design"]),
    ("F54", "Cumulative payment claims to Mar", "985,000", "S$", "PR3-4", "Payment claim 3 (cumulative) 985,000", ["budget", "expenditure"]),
    ("F55", "Provisional sums / instructed", "680,000 / 120,000", "S$", "PR3-4", "Provisional sums within contract 680,000 120,000 instructed", ["budget"]),
    ("F56", "Delay if lift works cannot start June 2027", "6-8", "weeks", "PR3-3", "KHB estimates 6–8 weeks of delay if lift works cannot start June 2027", ["closures", "lifts", "schedule"]),
    ("F57", "KHB self-assessment (Mar)", "broadly on programme", "", "PR3-1", "remains broadly on programme", ["progress"]),
    ("F58", "Asbestos variation status (PR3)", "to be submitted", "", "PR3-4", "Variation — asbestos removal (est.) 350,000 – 600,000 To be submitted", ["asbestos", "variation"]),
    ("F59", "Grant report due", "10th working day", "", "NRF-3.1", "due by the 10th working day of each month", ["reporting", "grant"]),
    ("F60", "Grant report contents", "progress; expenditure vs eligible cost; tranche conditions; top five risks", "", "NRF-3.2", "progress against the baseline programme, expenditure to date against eligible cost, status of each tranche condition, and top five risks", ["reporting", "grant"]),
    ("F61", "Late reports sanction", "two consecutive late may suspend next tranche", "", "NRF-3.3", "Two consecutive late or incomplete reports may suspend the next tranche", ["reporting", "grant"]),
    ("F62", "Scope change to social service facilities", "Fund prior written approval", "", "NRF-4.1", "requires the Fund's prior written approval", ["aac-operator", "childcare", "scope"]),
    ("F63", "Completion later than 31 Dec 2028", "Fund prior approval", "", "NRF-4.2", "Completion later than 31 December 2028 requires the Fund's prior approval", ["schedule", "completion", "grant"]),
    ("F64", "Barrier-free access during works", "required on all public floors", "", "NRF-5.1", "Barrier-free access must be maintained to all floors in public use", ["accessibility", "closures", "lifts"]),
    ("F65", "Seabreeze: keeping hub open cost", "3 months; S$0.6M", "", "LL-L01", "added about 3 months and S$0.6M", ["closures", "analog"]),
    ("F66", "Seabreeze: asbestos delay", "5", "weeks", "LL-L03", "Removal added 5 weeks", ["asbestos", "analog"]),
    ("F67", "Seabreeze: childcare licensing lead time", "7", "months", "LL-L04", "needed about 7 months between floor handover and first intake", ["childcare", "analog"]),
    ("F68", "Seabreeze: late operator reconfiguration", "85,000", "S$", "LL-L05", "reconfigured at a cost of S$85,000", ["aac-operator", "analog"]),
    ("F69", "Seabreeze: tranche delayed by missed condition", "4", "months", "LL-L08", "delayed 4 months because a condition (signed operator agreements)", ["tranche-2", "analog"]),
    ("F70", "Tranche shares T1/T2/T3/T4", "20/30/30/20", "%", "NRF-T2", "T2 | 30%", ["grant", "tranche-2"]),
    ("F71", "Baseline programme submitted", "2027-02-24", "date", "PR2-1", "Baseline programme submitted 24 February", ["schedule"]),
    ("F72", "AAC operator agreement owner", "not assigned", "", "DEL-D14", "Owner not assigned", ["aac-operator", "operator-agreements"]),
    ("F73", "Hazardous materials survey", "not started; not in original scope", "", "DEL-D06", "Not in original scope", ["hazmat", "asbestos"]),
    ("F74", "Feb NRF report", "late (2027-03-16)", "", "DEL-D09", "actual_date: 2027-03-16; notes: Late", ["reporting", "grant"]),
    ("F75", "Consultation summary", "overdue, postponed twice", "", "DEL-D15", "Postponed twice", ["consultation"]),
    ("F76", "Seed register hazmat risk", "closed (not expected per desk study)", "", "RISK-R08", "None — not expected per desk study; status: Closed", ["hazmat", "asbestos"]),
    ("F77", "AAC operator appointment due (D12)", "2027-03-31 overdue", "", "DEL-D12", "due_date: 2027-03-31; status: Overdue", ["aac-operator"]),
    ("F78", "Temporary lift", "possible but not priced", "", "EDC-3.2", "a temporary lift is possible but not priced", ["lifts", "accessibility"]),
]


def verify():
    """Return (ok_rows, failures). A fact is kept only if its quote is in its source."""
    from . import sources
    ok, bad = [], []
    for fid, label, value, unit, src, quote, tags in F:
        s = sources.get(src)
        if s and sources.norm(quote) in sources.norm(s["text"]):
            ok.append((fid, label, value, unit, src, quote, tags))
        else:
            bad.append({"id": fid, "source": src, "quote": quote})
    return ok, bad


def load():
    from . import db
    ok, bad = verify()
    db.ex("DELETE FROM facts")
    db.exmany("INSERT INTO facts(id,label,value,unit,source_id,quote,tags,verified) VALUES(?,?,?,?,?,?,?,1)",
              [(a, b, c, d, e, f, db.J(g)) for a, b, c, d, e, f, g in ok])
    return {"loaded": len(ok), "rejected": bad}
