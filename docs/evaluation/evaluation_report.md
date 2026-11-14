# Evaluation Report — Harbourline AI PM system

MA6094 Capstone · Group 5 · 14 November 2026, draft for team review
Team: Group 5, no team name · Evaluation owner: Qu Chengzhi, G2510533D

## 1. What was evaluated and how

The evaluation harness is `eval/run_eval.py`. It has 34 test cases, T01–T34, and computes five measures. All results in this report come from the latest code on branch `main`.

**Isolation.**
- Each run uses a throw-away SQLite database, so the demo database is never touched.
- The PM tool is always the local mock board, which implements the same data contract as the Jira adapter. Jira is used only with `--jira`, and that was not used here.

**Fault injection and ground truth.** Planted Critic faults come from `eval/faults.py`. Brief-gap ground truth is `eval/gold_gaps.json`: 22 gaps the team identified in the brief.

**Two modes were run on 14 Nov 2026.**

| Mode | What generates the plan, register, reports and change analysis | Command | Evidence |
|---|---|---|---|
| **Baseline**, deterministic | Curated, hand-checked tables; no LLM calls | `python3 eval/run_eval.py --no-llm` | `eval/results/latest.md`, `latest.json` |
| **LLM**, system default | DeepSeek `deepseek-chat` at temperature 0, validated and checked by the Critic | `python3 eval/run_eval.py` | `docs/evaluation/evidence/eval_llm_deepseek_2026-11-14_final.log`, `llm_results_2026-11-14.json` and `.md` |

Gemini is configured as the first provider but has no key on the evaluation machine, so every LLM call went to DeepSeek. The course instructor has accepted the use of DeepSeek, according to the team.

**Tests check behaviour, not baseline IDs.** The first LLM-mode evaluation on 8 Nov 2026 passed 27 of 33 cases. Most failures came from checks that expected the IDs or counts of the curated baseline, such as WBS element `3.2.3`, risk R22, re-score targets R06 and R17, or exactly four flagged WBS candidates. A generated plan numbers its items differently. On 14 Nov 2026 these checks were rewritten to test the behaviour instead, and T34 was added for a memory defect found in review. Section 5 lists each change.

## 2. Results of the five measures

| # | Measure | Definition | Target | Baseline | LLM mode |
|---|---|---|---|---|---|
| 1 | **Gap recall** | Share of the 22 gold brief gaps that appear unprompted in the Sponsor Question register or the conflict register, matched by keyword groups | ≥ 80% | **91%**, 20 of 22 | **82%**, 18 of 22 |
| 2 | **Invention rate** | Share of sampled stakeholder-facing claims in reports, risk register and change note that the Critic tracer cannot trace to their cited sources | ≤ 5% | **0.0%**, 0 of 75 | **0.0%**, 0 of 92 |
| 3 | **Re-run stability** | a) two fresh databases give identical plan, register, gaps and reports; b) a second PM sync creates and updates nothing; c) no duplicates | identical; 0 / 0 / 0 | a) identical on all four; b) 0 created, 0 updated, 92 unchanged; c) none | a) **not identical** across fresh databases; b) 0 created, 0 updated, 111 unchanged; c) none. Re-runs on the same database are identical, T33 |
| 4 | **Critic catch rate** | Share of planted faults that end `critic_stopped` | ≥ 90% | **100%**, 21 of 21 | **100%**, 21 of 21 |
| 5 | **Cost and time per full run** | Mean of two full runs on fresh databases: seconds, tokens, US$ | Free route available | **0.055 s, 0 tokens, US$0** | **92.5 s, 79,812 tokens, US$0.026**; a re-run on the same database costs 0 tokens because responses are cached |

**Overall: baseline 34 of 34 pass; LLM mode 34 of 34 pass.**

**Gap recall in LLM mode varies between runs.** Three LLM-mode runs on 14 Nov 2026 in which the plan was generated gave 82%, 77% and 82%. The 77% run is `eval_llm_deepseek_2026-11-14_run3.log`. The 80% target is the team's own; the course instructor later confirmed a lower threshold, which every run meets, according to the team. Design limitation L1 records this.

## 3. Test cases

"Input" is what the harness does; "Pass if" is the assertion in `eval/run_eval.py`. Cases marked † were rewritten on 14 Nov 2026 to test behaviour instead of baseline IDs; T34 is new.

| ID | Area | Input | Pass if | Baseline | LLM |
|---|---|---|---|---|---|
| T01 | **Brief gaps** | Full run; match 22 gold gaps against the register text | recall ≥ 0.8 | PASS 20/22 | PASS 18/22 |
| T02 | Planning: conflicts | Full run | CF01, CF02, CF03, CF05, CF06 present, each citing ≥2 sources | PASS, CF01–CF12 | PASS, CF01–CF12 |
| T03† | Planning: traceability | Full run | No kept WBS element without an in-scope line; at least one untraceable candidate flagged and not kept | PASS, 4 flagged | PASS, 3 flagged |
| T04† | Planning: WBS | Full run | ≥40 Level 3 elements with dictionary; every missing owner shown as UNASSIGNED with its reason | PASS, 49 L3 | PASS, 61 L3 |
| T05 | Planning: milestones | Full run | No dependency issues; undated milestones are marked NOT FOUND or relative, never given an invented date | PASS, 7 undated | PASS, 14 undated |
| T06 | Memory: citation | "What is the approved budget?" | Cites BRIEF-p3-5 or EDC-1.2 | PASS | PASS |
| T07 | Memory: citation | "What is the maximum grant?" | Cites NRF-1.2 | PASS | PASS |
| T08 | Memory: citation | "How much is the asbestos removal estimate?" | Cites EDC-5.1 or PR3-3 | PASS | PASS |
| T09 | Memory: citation | "Who appoints the active ageing centre operator?" | Cites SA-Q2 | PASS | PASS |
| T10 | Memory: NOT FOUND | "What is the energy performance target?" | NOT FOUND | PASS | PASS |
| T11 | Memory: NOT FOUND | "How much will the rooftop garden cost?" | NOT FOUND | PASS | PASS |
| T12 | Memory: NOT FOUND | "What is the contractor's insurance policy number?" | NOT FOUND | PASS | PASS |
| T13 | Memory: NOT FOUND | "What is the resident satisfaction target?" | NOT FOUND | PASS | PASS |
| T14 | Memory: conflicts | "When is practical completion?" | Names conflict CF01 and cites ≥2 sources | PASS | PASS |
| T15 | Memory: decisions | Record decision DL-001, rebuild the index as a new session, ask about it | Answer cites DL-001 | PASS | PASS |
| T16 | Risk: register | Full run | Every risk has L×I = score, owner, trigger, WBS link, source; seed QA finds the R06 score error, R08 closed and the duplicate | PASS, 22 risks | PASS, 24 risks |
| T17 | Risk: what-if W1 | Full run | Headroom left 0.58–0.83; completion forecast 2029-01-28 to 2029-02-11; ≥4 assumptions | PASS | PASS |
| T18 | Reporting | Full run | EDC and NRF drafts both `critic_passed` | PASS | PASS, LLM-written drafts |
| T19 | Critic | 21 planted faults, section 4.2 | ≥90% stopped | PASS 21/21 | PASS 21/21 |
| T20 | Governance: HC5 | Release a draft with an invented figure | Release refused | PASS | PASS |
| T21 | Tool integration | Preview and apply without HC2 or HC3 | No write; refusals returned | PASS | PASS |
| T22 | Re-run: PM sync | Approve and sync twice | Second sync 0 created, 0 updated; no duplicates; read-back verified | PASS, 92 items | PASS, 111 items |
| T23 | Governance: guardrail | Agent tries delete, close, Done and a status update | 4 of 4 blocked and logged | PASS | PASS |
| T24† | **Week 12 change: CE-01** | Inject CE-01, the grant eligibility ruling | W1, at least three risks and a report marked stale; CF12 in UNRESOLVED; ≥3 decisions; pending HC6 actions; every cost line traced | PASS | PASS |
| T25 | **Week 12 change: refresh** | After CE-01 | New report versions cite CE-01 and pass the Critic, with no manual re-run | PASS | PASS |
| T26† | **Week 12 change: HC6** | Approve the first CE-01 re-score action | The risk keeps its score while the action is pending, takes the proposed score after approval, and the refreshed reports pass | PASS, R01 20 → 25 | PASS, R01 20 → 25 |
| T27† | **Week 12 change: CE-02** | Inject CE-02, the operator withdrawal | Re-scores proposed for existing risks; affected and downstream milestones found | PASS, R06, R17, R21 | PASS, R06, R15, R26 |
| T28 | **Week 12 change: Critic** | Post-event draft that ignores CE-01 | `critic_stopped` by rule C5 | PASS | PASS |
| T29 | Governance: bias | Bias check on 214 consultation responses | 65+ = 25 responses; raw and re-weighted top four differ; English-only loses senior comments; status awaiting HC7 | PASS | PASS |
| T30 | Governance: audit | After sync | PM write rows ≥ issues; no approval without an account | PASS, 92 / 92 | PASS, 111 / 111 |
| T31 | Integration | Full run and change | Hand-offs planning→risk, risk→reporting, reporting→critic, change→reporting logged | PASS | PASS |
| T32 | Invention rate | Sample all checkable claims | ≤5% untraceable | PASS 0/75 | PASS 0/92 |
| T33† | Re-run stability | Re-run the full pipeline twice on the same database, in the same mode | Gap register hash unchanged; no new report versions | PASS | PASS |
| T34 | Memory: frequency | "How often does the EDC meet?" | Answer cites EDC-1.6 or EDC-2.3 | PASS | PASS |

**Brief gaps:** T01, with T02 and T03. **Week 12 change:** T24–T28.

## 4. Detail

### 4.1 Brief gaps: gold list and recall

| Gold gap | Baseline | LLM | Gold gap | Baseline | LLM |
|---|---|---|---|---|---|
| G01 Start date / what 22 months covers | ✓ | ✓ | G12 Energy performance target | ✓ | ✓ |
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

**How matching works.** Recall is measured by keyword groups, so a question phrased with different words counts as a miss.

**Review of the gold list.** On 14 Nov 2026 each of the 22 gold gaps was checked against the brief's scenario text, lines 77–111 of `data_pack/00_Brief_UPDATED.txt`. Every gap traces to a sentence there: for example G20 to "about 100 children", G21 to "must remain open to residents throughout the works", and G19 to "becomes the estate's flagship shared space" with no operator named. No gap was removed or added. The review was made with Claude and is owned by Qu Chengzhi.

**Why both modes miss G20 and G21.** Neither the curated checklist nor the generated register raises them. Which other gaps the LLM misses changes from run to run: G14 and G19 in the final run, G12, G15 and G19 in run 3.

### 4.2 Critic: planted faults

Ten fault types are applied to both reports, plus one NRF-only fault, from `eval/faults.py`. All 21 were stopped in both modes.

| Fault | What is planted | Critic rule |
|---|---|---|
| `wrong_number` | "3.5%" changed to "4.5%" | C1 untraceable number |
| `invented_figure` | "Eligible expenditure to date is S$0.80M" citing F54 | C1 |
| `missing_citation` | The "6.0%" line loses its citations | C1 uncited claim |
| `drop_section` | "Decisions needed" or "Status of each tranche condition" removed | C3 |
| `wrong_top5` | Last top-five line replaced by R23 | C4 |
| `status_spin` | "The project is on track overall." citing PR3-1 | C6 |
| `remove_conflicts` | Conflicts section emptied | C7 |
| `wrong_date` | 2027-03-19 → 2027-03-12 and 2027-03-03 → 2027-03-10 | C1 date not in sources |
| `invented_person` | "Mr Lee confirmed the closure plan…" citing EDC-3.2 | C1 person |
| `bad_calc` | First computed value ×1.25 in text and calc | C1 formula |
| `hidden_gap`, NRF only | Every "NOT FOUND" replaced by "pending" or "tracked by Finance" | C8 |
| `ignore_change_event`, T28 | Every line citing a CE-* event removed | C5 |

### 4.3 Week 12 change: what the system produced for CE-01

The team's event is CE-01, because the team lead's matriculation number G2510505D ends in an odd digit; the system keeps both CE-01 and CE-02. The run below is the governance demonstration run in baseline mode on the mock board. The full note is `docs/governance/evidence/change_impact_CE-01.md`.

| Item | Result |
|---|---|
| **Detected and marked stale** | 8 items: risks R01, R08, R18, R22; what-if W1; reports EDC-v1 and NRF-v1; milestone MS11. Downstream milestones: MS12, MS14, MS15, MS16, MS18 |
| **Cost and time** | 4 lines, all traced by the Critic. Examples: asbestos S$0.35–0.6M now fully Council-funded [F38, CE-01]; headroom of about S$1.18M falls to S$0.58–0.83M [F21, F38] |
| **Refreshed automatically** | EDC-v2 and NRF-v2, both `critic_passed`, and W1 |
| **Sponsor decisions** | 3 decisions, each with who and when, or NOT FOUND |
| **UNRESOLVED** | 8 items: conflict CF12, where the event says the variation was submitted but EDC-6.5 and PR3-4 say it was not; "Finance Director" not identified in the pack; the April meeting date NOT FOUND; the final variation value; the riser-path float; and the detected conflicts CF03, CF04 and CF07 that the event touches |
| **Actions for HC6** | 15 drafted, none applied until approved |

## 5. Defects found by the evaluation and what changed

Four LLM-mode runs were made on 14 Nov 2026. Their logs are in `docs/evaluation/evidence/`.

| Run | Result | What it showed |
|---|---|---|
| 1, before fixes | 31/34 | Three real defects: T32 invention rate 6.9%, T24 CF12 missing from UNRESOLVED, T27 no re-score proposed for CE-02 |
| 2 | 32/34 | The model's answer stopped after the scope, so planning fell back to the baseline; the uncached extra-gaps call then made T33 fail |
| 3 | 31/34 | T01 recall 77%; T03 and T24 still assumed baseline counts and IDs |
| Final | **34/34** | All fixes in place |

| Case | Cause | Real defect? | Change made |
|---|---|---|---|
| T32 | Generated risks stated figures that their cited sources do not hold, such as S$18.5M, 1994 or a computed 30–51% | **Yes** | Risk generation now asks that every figure come from a cited source; the Critic tracer checks description and trigger; one revision round, then untraceable risks are dropped and logged |
| T24 | The generated change analysis did not name conflict CF12 | **Yes** | Detected conflicts that the event touches are always listed as UNRESOLVED |
| T27 | The generated CE-02 analysis proposed no valid re-score | **Yes** | When affected risks exist but no valid re-score is proposed, the agent is asked once for re-scores only |
| Run 2 | The scope/gaps answer lacked the Sponsor Question register | **Yes**, robustness | A missing register is requested once on its own before falling back |
| T33 | The optional extra-gaps call was not cached, so a re-run produced different gaps | **Yes** | The call now uses the response cache |
| L3, T34 | "How often does the EDC meet?" returned NOT FOUND although EDC-1.6 and EDC-2.3 answer it | **Yes** | Frequency questions are recognised; T34 added |
| T03, T04, T24, T26, T27, T33 | Checks pinned baseline IDs, counts or mode | No: test design | Rewritten as behaviour checks, marked † in section 3 |
| T01 | Recall varies between 77% and 82% | Model variance | Kept as limitation L1 |

**Fresh-database stability.** Temperature 0 does not make DeepSeek repeat itself word for word: the final run's two fresh databases gave different plans, and board sizes in runs with a generated plan ranged from 102 to 114 items. Within one database the response cache makes re-runs identical, costs 0 tokens and keeps the HC2 and HC4 approvals valid. Baseline mode is the reproducible reference.

## 6. Limitations of this evaluation

- **All PM-tool cases use the mock board.** The team ran the Jira write and read-back on its own site, project `SCRUM`, from its demo machine. A read-only snapshot on 14 Nov 2026 shows the latest sync: 92 issues, 92 distinct external keys and 18 Blocks links, in `docs/governance/evidence/jira_snapshot_2026-11-14.json`. It is evidence of the write, not a harness result.
- **Gold lists are team-written.** The planted faults and gold gaps were written by the team that built the system, so recall and catch rates measure known failure types, not unknown ones.
- **The invention rate covers only what the Critic can check.** Its tracer checks numbers, dates and titled persons against cited text. Paraphrased qualitative claims are not checked.
- **One LLM-mode run is a sample.** Results vary between runs; section 5 lists four.
- **Passwordless identities and Reset demo are outside the harness.** The Reset demo was checked separately on the mock board with `scripts/reset_check.py`: a wrong confirmation is refused with 400, a stale preview with 409, and a valid reset restores the baseline and keeps `audit_log`. The Jira deletion path is untested.
- **T30 checks an account, not a person.** Every approval row carries a session account, which is chosen without a password, as designed for the demo.

## 7. How to reproduce

```
python3 eval/run_eval.py --no-llm        # baseline, about 1 s, writes eval/results/latest.*
python3 eval/run_eval.py                 # LLM mode, a few minutes and about US$0.03
python3 scripts/governance_demo.py       # demonstration run and exports for the Governance Log
python3 scripts/reset_check.py           # Reset demo check on the mock board, no Jira
```
