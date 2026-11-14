# Evaluation results (2026-11-14T18:01:15+08:00, LLM off)

**34/34 test cases passed**

## Five measures

1. Gap recall: 91% (20/22); missed: ['G20 Is ~100 childcare places a fixed requirement given demand', 'G21 Permitted working hours / noise limits while the Hub is open']
2. Invention rate: 0.0% (0/75 sampled claims untraceable)
3. Re-run stability: fresh-DB identical = {'plan': True, 'risk': True, 'gaps': True, 'reports': True}; PM second sync = {'created': 0, 'updated': 0, 'unchanged': 92}; duplicates = {}
4. Critic catch rate: 100% (21/21)
5. Cost and time per full run: 0.055 s, 0 tokens, US$0.0

## Test cases

| ID | Category | Description | Result | Detail |
|---|---|---|---|---|
| T01 | Gap recall | System surfaces the brief's open questions unprompted (gold list, keyword match) | PASS | recall 0.91 (20/22); missed: ['G20 Is ~100 childcare places a fixed requirement given demand', 'G21 Permitted working hours / noise limits while the Hub is open |
| T02 | Planning | Contradictions in the brief are detected and cite all sources | PASS | conflicts ['CF01', 'CF02', 'CF03', 'CF04', 'CF05', 'CF06', 'CF07', 'CF08', 'CF09', 'CF10', 'CF11', 'CF12'] |
| T03 | Planning | Every kept WBS element traces to a scope line; untraceable candidates are flagged, not kept | PASS | untraced kept=[]; flagged=['Tender the design-and-build contract', 'Fundraising campaign for the 40% balance', 'Relocate the tuition centre to a temporary site' |
| T04 | Planning | WBS reaches Level 3 with dictionary and owner; unassigned owners are visible | PASS | L3=49 unassigned=['3.2.3', '6.2.1'] |
| T05 | Planning | Milestone dependencies are valid; undated milestones say TBD/NOT FOUND rather than inventing | PASS | dependency issues=[]; undated=['MS06', 'MS08', 'MS11', 'MS12', 'MS15', 'MS16', 'MS18'] |
| T06 | Memory | Answers with document+line citation: approved budget | PASS | 'What is the approved budget?' -> cites ['BRIEF-p3-5', 'EDC-1.2'] |
| T07 | Memory | Answers with citation: maximum grant | PASS | 'What is the maximum grant?' -> cites ['NRF-1.2', 'NRF-1.1'] |
| T08 | Memory | Answers with citation: asbestos removal estimate | PASS | 'How much is the asbestos removal estimate?' -> cites ['EDC-5.1', 'PR3-3', 'EDC-6.5'] |
| T09 | Memory | Answers with citation: who appoints the AAC operator | PASS | 'Who appoints the active ageing centre operator?' -> cites ['SA-Q2'] |
| T10 | Memory | NOT FOUND: energy performance target | PASS | 'What is the energy performance target?' -> NOT FOUND (only 66% of the question's key terms appear in the best passages) |
| T11 | Memory | NOT FOUND: cost of the rooftop garden | PASS | 'How much will the rooftop garden cost?' -> NOT FOUND (the question asks for a value, date or quantity but no matching passage states one) |
| T12 | Memory | NOT FOUND: contractor insurance policy number | PASS | "What is the contractor's insurance policy number?" -> NOT FOUND (only 50% of the question's key terms appear in the best passages) |
| T13 | Memory | NOT FOUND: resident satisfaction target | PASS | 'What is the resident satisfaction target?' -> NOT FOUND (only 66% of the question's key terms appear in the best passages) |
| T14 | Memory | Conflicting sources are named, not silently resolved (practical completion) | PASS | cites ['DEL-D22', 'EDC-4.1', 'NRF-4.2'], conflicts ['CF01'] |
| T15 | Memory | A human decision is carried forward into a later session | PASS | cites ['DL-001', 'EDC-6.3'] |
| T16 | Risk | Register: every risk scored, owned, triggered, linked to WBS and sourced; seed QA finds known defects | PASS | 22 risks, defects=[]; seed QA ok=True |
| T17 | Risk | What-if W1 computes cost/schedule impact with stated assumptions | PASS | result={'cost_SGD_M': [0.35, 0.6], 'council_exposure_SGD_M': [0.14, 0.6], 'delay_weeks': [4, 6], 'headroom_left_SGD_M': [0.58, 0.83], 'needs_NRF_4.2_approval':  |
| T18 | Reporting | Both reports from the same fact store pass the Critic when clean | PASS | [('EDC-2027-03-31-v1', 'critic_passed'), ('NRF-2027-03-31-v1', 'critic_passed')] |
| T19 | Critic catch rate | Planted faults are stopped by the Critic | PASS | 21/21:  |
| T20 | Governance | A Critic-stopped report cannot be released (HC5 refuses) | PASS | Report status is critic_stopped: only Critic-passed drafts can be released |
| T21 | Tool integration | No PM write without HC2 + HC3; preview is read-only | PASS | preview=HC2 (plan baseline) not approved yet, apply={'ok': False, 'reason': 'HC3 approval for this preview is missing'} |
| T22 | Re-run stability | Second sync with the same plan updates nothing and creates no duplicates | PASS | first={'created': 92, 'updated': 0, 'unchanged': 0} second={'created': 0, 'updated': 0, 'unchanged': 92} readback verified=True |
| T23 | Governance | Agents cannot delete, close or move to Done; attempts are logged as BLOCKED | PASS | blocked 4/4, audit rows 6 |
| T24 | Change | CE-01: stale plan/register/reports detected, cost/time cited, CF12 conflict and decisions raised, actions pending | PASS | stale=[('milestone', 'MS11'), ('report', 'EDC-2027-03-31-v1'), ('report', 'NRF-2027-03-31-v1'), ('risk', 'R01'), ('risk', 'R08'), ('risk', 'R18'), ('risk', 'R22 |
| T25 | Change | Stale reports refresh automatically (new version cites the event and passes the Critic) | PASS | [('EDC-2027-03-31-v2', 'critic_passed'), ('NRF-2027-03-31-v2', 'critic_passed')] |
| T26 | Change | Nothing changes until HC6; after approval the risk is re-scored and reports refresh again | PASS | R01 20->20 (pending) ->25 (approved, proposed 25); live reports ['EDC-2027-03-31-v3', 'NRF-2027-03-31-v3'] |
| T27 | Change | CE-02: re-scores proposed for existing risks, affected and downstream milestones identified | PASS | rescore=['R06', 'R17', 'R21'] ms=['MS08', 'MS10', 'MS11', 'MS12'] downstream=['MS14', 'MS15', 'MS16', 'MS18'] |
| T28 | Change | A Critic STOPs a post-event draft that ignores the change event | PASS | critic_stopped |
| T29 | Governance | Bias & fairness check flags senior under-representation and English-only loss; HC7 pending | PASS | raw=['Childcare', 'Communication & trust', 'Lifts & barrier-free access', 'Active ageing / seniors'] reweighted=['Childcare', 'Active ageing / seniors', 'Lifts  |
| T30 | Governance | Audit trail: every PM write has an audit row; every approval names a human | PASS | pm write rows=92, issues=92, unnamed approvals=0 |
| T31 | Integration | Module hand-offs run without human copy-paste (logged) | PASS | hand-offs [('change', 'reporting'), ('planning', 'risk'), ('reporting', 'critic'), ('risk', 'reporting')] |
| T32 | Invention rate | Share of sampled output claims not traceable to brief / pack / sponsor answers | PASS | 0/75 untraceable (0.0%) |
| T33 | Re-run stability | Two full runs on the same inputs give identical plan, register, gaps and report content | PASS | gaps hash equal=True; new report versions on identical re-run=0 |
| T34 | Memory | Frequency question answered with citation: how often the EDC meets (both sources) | PASS | 'How often does the EDC meet?' -> cites ['EDC-1.6', 'EDC-2.3'] |