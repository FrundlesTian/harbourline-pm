# Evaluation results (2026-11-14T18:00:37+08:00, LLM on)

**34/34 test cases passed**

## Five measures

1. Gap recall: 82% (18/22); missed: ['G14 Existing leases/licences during works', 'G19 Who operates the Hub after completion', 'G20 Is ~100 childcare places a fixed requirement given demand', 'G21 Permitted working hours / noise limits while the Hub is open']
2. Invention rate: 0.0% (0/92 sampled claims untraceable)
3. Re-run stability: fresh-DB identical = {'plan': False, 'risk': False, 'gaps': False, 'reports': False}; PM second sync = {'created': 0, 'updated': 0, 'unchanged': 111}; duplicates = {}
4. Critic catch rate: 100% (21/21)
5. Cost and time per full run: 92.544 s, 79812 tokens, US$0.02559

## Test cases

| ID | Category | Description | Result | Detail |
|---|---|---|---|---|
| T01 | Gap recall | System surfaces the brief's open questions unprompted (gold list, keyword match) | PASS | recall 0.82 (18/22); missed: ['G14 Existing leases/licences during works', 'G19 Who operates the Hub after completion', 'G20 Is ~100 childcare places a fixed re |
| T02 | Planning | Contradictions in the brief are detected and cite all sources | PASS | conflicts ['CF01', 'CF02', 'CF03', 'CF04', 'CF05', 'CF06', 'CF07', 'CF08', 'CF09', 'CF10', 'CF11', 'CF12'] |
| T03 | Planning | Every kept WBS element traces to a scope line; untraceable candidates are flagged, not kept | PASS | untraced kept=[]; flagged=['Tendering the design-and-build contract', 'Fundraising work package', 'Grant funding request in monthly report'] |
| T04 | Planning | WBS reaches Level 3 with dictionary and owner; unassigned owners are visible | PASS | L3=61 unassigned=['3.3.2'] |
| T05 | Planning | Milestone dependencies are valid; undated milestones say TBD/NOT FOUND rather than inventing | PASS | dependency issues=[]; undated=['MS06', 'MS07', 'MS08', 'MS09', 'MS10', 'MS11', 'MS12', 'MS14', 'MS15', 'MS16', 'MS17', 'MS19', 'MS20', 'MS21'] |
| T06 | Memory | Answers with document+line citation: approved budget | PASS | 'What is the approved budget?' -> cites ['BRIEF-p3-5', 'EDC-1.2'] |
| T07 | Memory | Answers with citation: maximum grant | PASS | 'What is the maximum grant?' -> cites ['NRF-1.2', 'NRF-1.1', 'NRF-1.4'] |
| T08 | Memory | Answers with citation: asbestos removal estimate | PASS | 'How much is the asbestos removal estimate?' -> cites ['EDC-5.1', 'PR3-3', 'PR3-4'] |
| T09 | Memory | Answers with citation: who appoints the AAC operator | PASS | 'Who appoints the active ageing centre operator?' -> cites ['SA-Q2'] |
| T10 | Memory | NOT FOUND: energy performance target | PASS | 'What is the energy performance target?' -> NOT FOUND (LLM found no support in retrieved sources) |
| T11 | Memory | NOT FOUND: cost of the rooftop garden | PASS | 'How much will the rooftop garden cost?' -> NOT FOUND (LLM found no support in retrieved sources) |
| T12 | Memory | NOT FOUND: contractor insurance policy number | PASS | "What is the contractor's insurance policy number?" -> NOT FOUND (LLM found no support in retrieved sources) |
| T13 | Memory | NOT FOUND: resident satisfaction target | PASS | 'What is the resident satisfaction target?' -> NOT FOUND (LLM found no support in retrieved sources) |
| T14 | Memory | Conflicting sources are named, not silently resolved (practical completion) | PASS | cites ['EDC-4.1', 'PR3-footer', 'PR2-footer', 'PR1-footer', 'DEL-D22', 'NRF-4.2'], conflicts ['CF01'] |
| T15 | Memory | A human decision is carried forward into a later session | PASS | cites ['DL-001', 'EDC-6.3'] |
| T16 | Risk | Register: every risk scored, owned, triggered, linked to WBS and sourced; seed QA finds known defects | PASS | 24 risks, defects=[]; seed QA ok=True |
| T17 | Risk | What-if W1 computes cost/schedule impact with stated assumptions | PASS | result={'cost_SGD_M': [0.35, 0.6], 'council_exposure_SGD_M': [0.14, 0.6], 'delay_weeks': [4, 6], 'headroom_left_SGD_M': [0.58, 0.83], 'needs_NRF_4.2_approval':  |
| T18 | Reporting | Both reports from the same fact store pass the Critic when clean | PASS | [('EDC-2027-03-31-v1', 'critic_passed'), ('NRF-2027-03-31-v1', 'critic_passed')] |
| T19 | Critic catch rate | Planted faults are stopped by the Critic | PASS | 21/21:  |
| T20 | Governance | A Critic-stopped report cannot be released (HC5 refuses) | PASS | Report status is critic_stopped: only Critic-passed drafts can be released |
| T21 | Tool integration | No PM write without HC2 + HC3; preview is read-only | PASS | preview=HC2 (plan baseline) not approved yet, apply={'ok': False, 'reason': 'HC3 approval for this preview is missing'} |
| T22 | Re-run stability | Second sync with the same plan updates nothing and creates no duplicates | PASS | first={'created': 111, 'updated': 0, 'unchanged': 0} second={'created': 0, 'updated': 0, 'unchanged': 111} readback verified=True |
| T23 | Governance | Agents cannot delete, close or move to Done; attempts are logged as BLOCKED | PASS | blocked 4/4, audit rows 6 |
| T24 | Change | CE-01: stale plan/register/reports detected, cost/time cited, CF12 conflict and decisions raised, actions pending | PASS | stale=[('milestone', 'MS05'), ('milestone', 'MS07'), ('milestone', 'MS13'), ('milestone', 'MS18'), ('milestone', 'MS21'), ('report', 'EDC-2027-03-31-v1'), ('rep |
| T25 | Change | Stale reports refresh automatically (new version cites the event and passes the Critic) | PASS | [('EDC-2027-03-31-v2', 'critic_passed'), ('NRF-2027-03-31-v2', 'critic_passed')] |
| T26 | Change | Nothing changes until HC6; after approval the risk is re-scored and reports refresh again | PASS | R01 20->20 (pending) ->25 (approved, proposed 25); live reports ['EDC-2027-03-31-v3', 'NRF-2027-03-31-v3'] |
| T27 | Change | CE-02: re-scores proposed for existing risks, affected and downstream milestones identified | PASS | rescore=['R06', 'R15', 'R26'] ms=['MS04', 'MS05', 'MS12', 'MS13', 'MS14', 'MS15', 'MS16', 'MS18', 'MS21'] downstream=['MS17', 'MS19', 'MS20'] |
| T28 | Change | A Critic STOPs a post-event draft that ignores the change event | PASS | critic_stopped |
| T29 | Governance | Bias & fairness check flags senior under-representation and English-only loss; HC7 pending | PASS | raw=['Childcare', 'Communication & trust', 'Lifts & barrier-free access', 'Active ageing / seniors'] reweighted=['Childcare', 'Active ageing / seniors', 'Lifts  |
| T30 | Governance | Audit trail: every PM write has an audit row; every approval names a human | PASS | pm write rows=111, issues=111, unnamed approvals=0 |
| T31 | Integration | Module hand-offs run without human copy-paste (logged) | PASS | hand-offs [('change', 'reporting'), ('planning', 'risk'), ('reporting', 'critic'), ('risk', 'reporting')] |
| T32 | Invention rate | Share of sampled output claims not traceable to brief / pack / sponsor answers | PASS | 0/92 untraceable (0.0%) |
| T33 | Re-run stability | Two full runs on the same inputs give identical plan, register, gaps and report content | PASS | gaps hash equal=True; new report versions on identical re-run=0 |
| T34 | Memory | Frequency question answered with citation: how often the EDC meets (both sources) | PASS | 'How often does the EDC meet?' -> cites ['EDC-1.6', 'EDC-2.3'] |