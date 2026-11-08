# Evaluation Report — Harbourline AI PM system

MA6094 Capstone · Group B · 8 November 2026 (draft for team review)
Team: [NEEDS INPUT: team name and evaluation owner — team lead]

## 1. What was evaluated and how

The evaluation harness is `eval/run_eval.py`. It has 33 test cases, T01–T33, and computes five measures.

**Isolation:**
- Each run uses a throw-away SQLite database (`eval/run_eval.py:17-19`), so the demo database is never touched.
- The PM tool is always the local mock board, which implements the same data contract as the Jira adapter. Jira is used only with `--jira` (`eval/run_eval.py:22-23`), and that was not used here.

**Fault injection:** planted Critic faults come from `eval/faults.py`. Brief-gap ground truth is `eval/gold_gaps.json`: 22 gaps the team identified in the brief.

**Two modes were run:**

| Mode | What generates the plan, register, reports and change analysis | Command | Evidence |
|---|---|---|---|
| **Baseline** (deterministic) | Curated, hand-checked tables; no LLM calls | `python3 eval/run_eval.py --no-llm` | `eval/results/latest.md`, `latest.json` (run 2026-11-08 19:21 SGT) |
| **LLM** (system default) | DeepSeek `deepseek-chat`, temperature 0, validated, Critic-checked | `python3 eval/run_eval.py` | `docs/design/evidence/eval_llm_deepseek_2026-11-08.log` (run 2026-11-08, commit `9356955`) |

Gemini is now the primary LLM and DeepSeek the backup (`app/config.py:27-59`). **No LLM-mode run with Gemini has been made yet** [NEEDS INPUT: run `python3 eval/run_eval.py` with `GEMINI_API_KEY` set and attach the log — evaluation owner].

## 2. Results of the five measures

| # | Measure | Definition (code) | Target | Baseline | LLM mode (DeepSeek) |
|---|---|---|---|---|---|
| 1 | **Gap recall** | Share of the 22 gold brief gaps that appear unprompted in the Sponsor Question register or the conflict register, by keyword groups (`eval/run_eval.py:45-52`) | ≥ 80% | **91%** (20/22) | **77%** (17/22): below target |
| 2 | **Invention rate** | Share of sampled stakeholder-facing claims (reports, register, change note) that the Critic tracer cannot trace to their cited brief / pack / sponsor sources (T32) | ≤ 5% | **0.0%** (0/75) | **0.0%** (0/94) |
| 3 | **Re-run stability** | (a) Two fresh databases give identical plan, register, gaps and reports; (b) second PM sync creates and updates nothing; (c) no duplicates (T22, T33) | identical; 0 / 0 / 0 | (a) identical on all four; (b) 0 created, 0 updated, 92 unchanged; (c) none | (a) **not identical** across fresh databases; (b) 0 created, 0 updated, 118 unchanged; (c) none. Same-database re-runs are identical because responses are cached (§5) |
| 4 | **Critic catch rate** | Share of planted faults that end `critic_stopped` (T19) | ≥ 90% | **100%** (21/21) | **100%** (21/21) |
| 5 | **Cost and time per full run** | Mean of two full runs: seconds, tokens, US$ (`runs` table) | Free route available | **0.055 s, 0 tokens, US$0** | ≈110 s, ≈74k tokens, ≈US$0.024 per fresh run. On the same database: 0 tokens (cache). These are development-run measurements; the LLM eval log does not record them [NEEDS INPUT: rerun to record] |

**Overall:**
- **Baseline: 33/33 cases pass.**
- **LLM mode: 27/33 pass.** One of the six failures is a real quality gap (measure 1). Four are checks that expect fixed IDs from the curated tables. One is a check that cannot pass in LLM mode as written. The cause of T24 is not fully recorded (§5).

## 3. Test cases (33)

"Input" is what the harness does; "Pass if" is the assertion in `eval/run_eval.py`.

| ID | Area | Input | Pass if | Baseline | LLM |
|---|---|---|---|---|---|
| T01 | **Brief gaps** | Full run; match 22 gold gaps against the register text | recall ≥ 0.8 | PASS 20/22 | **FAIL** 17/22 |
| T02 | Planning: conflicts | Full run | CF01, CF02, CF03, CF05, CF06 present, each citing ≥2 sources | PASS (CF01–CF12) | PASS |
| T03 | Planning: traceability | Full run | No kept WBS element without an in-scope line; ≥4 untraceable candidates flagged, not kept | PASS (4 flagged) | PASS (4 flagged) |
| T04 | Planning: WBS | Full run | ≥40 L3 elements with dictionary; `3.2.3` shown as UNASSIGNED | PASS (49 L3) | **FAIL**: 69 L3; the unassigned item is `3.3.2`, not `3.2.3` |
| T05 | Planning: milestones | Full run | No dependency issues; undated milestones say TBD / NOT FOUND | PASS (7 undated) | PASS (17 undated) |
| T06 | Memory: citation | "What is the approved budget?" | Cites BRIEF-p3-5 or EDC-1.2 | PASS | PASS |
| T07 | Memory: citation | "What is the maximum grant?" | Cites NRF-1.2 | PASS | PASS |
| T08 | Memory: citation | "How much is the asbestos removal estimate?" | Cites EDC-5.1 or PR3-3 | PASS | PASS |
| T09 | Memory: citation | "Who appoints the active ageing centre operator?" | Cites SA-Q2 | PASS | PASS |
| T10 | Memory: NOT FOUND | "What is the energy performance target?" | NOT FOUND | PASS | PASS |
| T11 | Memory: NOT FOUND | "How much will the rooftop garden cost?" | NOT FOUND | PASS | PASS |
| T12 | Memory: NOT FOUND | "What is the contractor's insurance policy number?" | NOT FOUND | PASS | PASS |
| T13 | Memory: NOT FOUND | "What is the resident satisfaction target?" | NOT FOUND | PASS | PASS |
| T14 | Memory: conflicts | "When is practical completion?" | Names conflict CF01 and cites ≥2 sources | PASS | PASS |
| T15 | Memory: decisions | Record decision DL-001, rebuild index (new session), ask about it | Answer cites DL-001 | PASS | PASS |
| T16 | Risk: register | Full run | Every risk has L×I = score, owner, trigger, WBS link, source; seed QA finds R06 score error, R08 closed, duplicate | PASS (22 risks) | PASS (25 risks) |
| T17 | Risk: what-if W1 | Full run | Headroom left 0.58–0.83; PC forecast 2029-01-28 to 2029-02-11; ≥4 assumptions | PASS | PASS |
| T18 | Reporting | Full run | EDC and NRF drafts both `critic_passed` | PASS | PASS (LLM-written drafts) |
| T19 | Critic | 21 planted faults (§4.2) | ≥90% stopped | PASS 21/21 | PASS 21/21 |
| T20 | Governance: HC5 | Release a draft with an invented figure | Release refused | PASS | PASS |
| T21 | Tool integration | Preview and apply without HC2 / HC3 | No write; refusals returned | PASS | PASS |
| T22 | Re-run: PM sync | Approve and sync twice | Second sync 0 created / 0 updated; no duplicates; read-back verified | PASS (92 items) | PASS (118 items) |
| T23 | Governance: guardrail | Agent tries delete, close, Done, status update | 4/4 blocked and logged | PASS | PASS |
| T24 | **Week 12 change: CE-01** | Inject CE-01 (grant eligibility ruling) | W1, R01, R08, R22 and a report stale; CF12 in UNRESOLVED; ≥3 decisions; pending HC6 actions; all cost lines traced | PASS | **FAIL** (§5) |
| T25 | **Week 12 change: refresh** | After CE-01 | New report versions cite CE-01 and pass the Critic, with no manual re-run | PASS | PASS |
| T26 | **Week 12 change: HC6** | Approve the R01 re-score action | R01 unchanged while pending (20), 25 after approval; reports refreshed and passing | PASS | **FAIL**: R01 16 → 16 (pending) → 20 (approved). Behaviour is correct, but the generated register scored R01 differently |
| T27 | **Week 12 change: CE-02** | Inject CE-02 (operator withdrawal) | Re-scores proposed for R06 and R17; MS12 affected; MS14 downstream | PASS | **FAIL**: proposals R06 and R15; affected and downstream milestones have different generated IDs |
| T28 | **Week 12 change: Critic** | Post-event draft that ignores CE-01 | `critic_stopped` (rule C5) | PASS | PASS |
| T29 | Governance: bias | Bias check on 214 consultation responses | 65+ = 25 responses; raw vs re-weighted top-4 differ; English-only loses senior comments; status awaiting HC7 | PASS | PASS |
| T30 | Governance: audit | After sync | PM write rows ≥ issues; no unnamed approval | PASS (92 / 92) | PASS (118 / 118) |
| T31 | Integration | Full run + change | Hand-offs planning→risk, risk→reporting, reporting→critic, change→reporting logged | PASS | PASS |
| T32 | Invention rate | Sample all checkable claims | ≤5% untraceable | PASS 0/75 | PASS 0/94 |
| T33 | Re-run stability | Re-run full pipeline on the same inputs | Gap register hash unchanged; no new report versions | PASS | **FAIL**: the check re-runs with the LLM switched off (`use_llm=False`), so it compares LLM-generated questions with baseline questions. This can never be equal in LLM mode. No new report versions were created |

**Brief gaps:** T01, plus T02 and T03. **Week 12 change:** T24–T28.

## 4. Detail

### 4.1 Brief gaps: gold list and recall

| Gold gap | Baseline | LLM | Gold gap | Baseline | LLM |
|---|---|---|---|---|---|
| G01 Start date / what 22 months covers | ✓ | ✓ | G12 Energy performance target | ✓ | ✗ |
| G02 22 months vs "fully open by Q4 2028" | ✓ | ✓ | G13 Barrier-free access while lifts replaced | ✓ | ✓ |
| G03 Hub open vs lift works; what may close | ✓ | ✓ | G14 Existing leases during works | ✓ | ✗ |
| G04 Who appoints the AAC operator, when | ✓ | ✓ | G15 Variation approval authority | ✓ | ✓ |
| G05 Childcare month 18, licensing | ✓ | ✓ | G16 Weekly update content and cadence | ✓ | ✓ |
| G06 Grant conditions "will follow" | ✓ | ✓ | G17 Rooftop garden feasibility / funding | ✓ | ✓ |
| G07 Who funds the remaining 40% | ✓ | ✓ | G18 Hazardous materials in a 1994 building | ✓ | ✓ |
| G08 Is there a contingency | ✓ | ✓ | G19 Who operates the Hub after completion | ✓ | ✗ |
| G09 Cost breakdown by element | ✓ | ✓ | G20 Are ~100 childcare places fixed | ✗ | ✗ |
| G10 Consultation timing and owner | ✓ | ✓ | G21 Working hours / noise limits | ✗ | ✗ |
| G11 Measuring "high resident satisfaction" | ✓ | ✓ | G22 60% of S$18.5M vs eligible-cost basis | ✓ | ✓ |

**How matching works.** Recall is measured by keyword groups, so a question phrased with different words counts as a miss. The gold list itself was written by the team [NEEDS INPUT: independent review of `eval/gold_gaps.json` — evaluation owner].

**Why both modes miss G20 and G21.** Neither the curated checklist nor the generated register raises them. The LLM additionally misses G12, G14 and G19.

### 4.2 Critic: planted faults

Ten fault types are applied to both reports, plus one NRF-only fault (`eval/faults.py`). All 21 were stopped in both modes.

| Fault | What is planted | Critic rule |
|---|---|---|
| `wrong_number` | "3.5%" changed to "4.5%" | C1 untraceable number |
| `invented_figure` | "Eligible expenditure to date is S$0.80M" citing F54 | C1 |
| `missing_citation` | The "6.0%" line loses its citations | C1 uncited claim |
| `drop_section` | "Decisions needed" / "Status of each tranche condition" removed | C3 |
| `wrong_top5` | Last top-five line replaced by R23 | C4 |
| `status_spin` | "The project is on track overall." citing PR3-1 | C6 |
| `remove_conflicts` | Conflicts section emptied | C7 |
| `wrong_date` | 2027-03-19 → 2027-03-12 and 2027-03-03 → 2027-03-10 | C1 date not in sources |
| `invented_person` | "Mr Lee confirmed the closure plan…" citing EDC-3.2 | C1 person |
| `bad_calc` | First computed value ×1.25 in text and calc | C1 formula |
| `hidden_gap` (NRF only) | Every "NOT FOUND" replaced by "pending" / "tracked by Finance" | C8 |
| `ignore_change_event` (T28) | Every line citing a CE-* event removed | C5 |

### 4.3 Week 12 change: what the system produced for CE-01

The run is the governance demonstration run (baseline mode, mock board). The full note is in `docs/governance/evidence/change_impact_CE-01.md`.

| Item | Result |
|---|---|
| **Detected and marked stale** | 8 items: risks R01, R08, R22, R18; what-if W1; reports EDC-v1 and NRF-v1; milestone MS11. Downstream milestones: MS12, MS14, MS15, MS16, MS18 |
| **Cost / time** | 4 lines, all traced by the Critic. Examples: asbestos S$0.35–0.6M now fully Council-funded [F38, CE-01]; headroom ~S$1.18M falls to S$0.58–0.83M [F21, F38] |
| **Refreshed automatically** | EDC-v2 and NRF-v2 (both `critic_passed`) and W1 |
| **Sponsor decisions** | 3 decisions, each with who and when, or NOT FOUND |
| **UNRESOLVED** | 5 items, including conflict CF12 (event says the variation was submitted; EDC-6.5 and PR3-4 say it was not), "Finance Director" not identified in the pack, and April meeting date NOT FOUND |
| **Actions for HC6** | 15 drafted, none applied until approved |

Which event applies to the team (CE-01 or CE-02) is still open [NEEDS INPUT: change-handling owner].

## 5. Analysis of the LLM-mode failures

| Case | Cause | Real defect? | Planned response |
|---|---|---|---|
| T01 | The generated register misses five gold gaps | **Yes**: quality gap | Give the generator the curated question list as a minimum checklist, then re-measure |
| T04, T26, T27 | The checks pin IDs or scores from the curated tables (`3.2.3`, R01 = 20 → 25, R17, MS12, MS14); generated content numbers differently | No: behaviour as specified (unassigned owner visible; re-score only after HC6; downstream milestones found) | Rewrite as behaviour checks, e.g. "the risk linked to the event is re-scored only after HC6" |
| T33 | Compares an LLM run with a baseline re-run | No: test design | Compare two LLM runs on the same database |
| T24 | Stale set contains W1, R01, R08, R22 and reports. The log truncates the detail at 300 characters, so which sub-condition failed (CF12, decision count, pending actions or tracing) was **not recorded** | Unknown | Re-run with full detail [NEEDS INPUT] |

**Fresh-database stability.** Temperature 0 does not make DeepSeek repeat itself word for word. Two fresh LLM runs produced 115 and 122 board items in development runs. Within one database the response cache (`app/llm.py:34-63`) makes re-runs identical, costs 0 tokens, and leaves the HC2/HC4 approvals valid. Baseline mode is the reproducible reference.

## 6. Limitations of this evaluation

- **All PM-tool cases use the mock board.** The team reports a Jira write and read-back test on another machine. Its export is not in the repository [NEEDS INPUT: tool-integration owner].
- **Gold lists are team-written.** The planted faults and gold gaps were written by the same team that built the system, so recall and catch rates measure known failure types, not unknown ones.
- **The invention rate covers only what the Critic can check.** Its tracer checks numbers, dates and titled persons against cited text. Paraphrased qualitative claims are not checked.
- **Memory has a known false NOT FOUND.** "How often does the EDC meet?" returns NOT FOUND (`docs/design/design_document.md` §8 L3). The test set does not include this question.

## 7. How to reproduce

```
python3 eval/run_eval.py --no-llm        # baseline, ~1 s, writes eval/results/latest.*
python3 eval/run_eval.py                 # LLM mode (Gemini, DeepSeek backup), a few minutes
python3 scripts/governance_demo.py       # demonstration run + exports for the Governance Log
```
