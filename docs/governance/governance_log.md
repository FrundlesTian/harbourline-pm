# Governance Log — Harbourline AI PM system

MA6094 Capstone · Group B · 8 November 2026 (draft for team review)
Governance owner: [NEEDS INPUT: name — team lead]

## 0. What this log covers and where the records come from

The system writes its governance records itself, into SQLite tables `audit_log`, `approvals` and `handoffs` (`app/db.py:58-64, 81-83`). Two kinds of record are reported here:

| Source | What it is | Files |
|---|---|---|
| **Demonstration run, 8 Nov 2026 19:20 SGT** | One end-to-end session produced by `scripts/governance_demo.py` on a throw-away database. It runs in baseline mode (no LLM calls) against the mock board. Every approval goes through the same server handler as the UI (`server.api_approve`), signed by the seeded **role accounts**. These are demonstration decisions, not the team's real decisions. | `docs/governance/evidence/`: `audit_log.csv` (188 rows), `agent_writes.csv` (137 rows), `approvals.csv` (10 rows), `bias_check.json`, `change_impact_CE-01.md`, `summary.json` |
| **Team's real run** | The run on the team's Jira site, including the Jira test on another machine | [NEEDS INPUT: audit and approvals CSV exports from **Governance → Export** in the UI (`/api/export/audit.csv`, `/api/export/approvals.csv`) — tool-integration owner] |

To reproduce the demonstration: `python3 scripts/governance_demo.py`. The export contains no tokens; a scan for token patterns found 0 matches, and all log text passes through `audit.redact()` (`app/audit.py:33-40`).

## 1. Audit records of agent write operations

**Schema** (`app/db.py:61-64`): `id, ts, run_id, actor, actor_type (agent | human | system), action, target_type, target_id, outcome (ok | blocked | rejected | fallback | error), detail (JSON)`. Each agent write calls `audit.log()` (`app/audit.py:43-49`); PM writes are logged inside the guarded adapter (`app/pmtool.py:356-376`).

**Agent writes in the demonstration run** (`agent_writes.csv`, 137 rows):

| Agent | Write action | Rows | Example (audit id → target) |
|---|---|---|---|
| planning | `write plan` | 1 | #8: 17 scope lines, 20 Sponsor Questions, 12 conflicts, 74 WBS elements, 18 milestones |
| risk | `write risk register`, `write what-if` | 1 + 4 | #11: 22 risks; #12: W1 v1 |
| governance | `bias & fairness check written` | 1 | #16 → BIAS-1 (6 findings) |
| reporting | `write report draft` | 6 | #18 → EDC-2027-03-31-v1 (hash recorded) |
| tooling | `pm create` | 92 | #31 → mock issue for `ext-HCH-WBS-1` |
| tooling | `pm link` (Blocks) | 18 | #123 → milestone dependency |
| tooling | `pm sync applied` | 2 | #141: 92 created; second sync 0 created / 0 updated / 92 unchanged |
| change | `mark stale`, `change impact note drafted` | 8 + 1 | #154 → R01 stale (tags budget, eligible-cost, grant); #173 → CE-01 |
| risk | `risk re-scored (approved)` | 1 | #175 → R01 20 → 25, **only after HC6** |
| change | `pm comment`, `pm update` (label) | 1 + 1 | #185–186: comment and `change-ce-01` label on the WBS 1.2.2 item, **only after HC6** |

**Coverage check:**
- Every PM issue has a `pm create` row: 92 issues, 92 rows. Eval T30 checks the same rule: 92 rows for 92 issues in baseline mode, 118 for 118 in LLM mode.
- No agent write to the PM tool happened before HC2 and HC3 were approved: rows #31 onwards follow approvals #2 and #3.

**Hand-offs without a human in between** (`handoffs`): planning→risk, risk→reporting, reporting→critic, change→reporting (eval T31).

## 2. Who approved each checkpoint

### 2.1 Demonstration run (`approvals.csv`)

The approver is the logged-in account. The server takes it from the session and never from a typed name (`server.py:80-92`).

| # | Checkpoint | Item approved | Approver (account) | Decision | Comment |
|---|---|---|---|---|---|
| 1 | HC1 scope + Sponsor Questions | gaps `072aec9495dc` | Project Manager (project_manager) | approved | scope and Sponsor Questions reviewed |
| 2 | HC2 plan baseline | plan `2656fb7c1a17` | Project Manager | approved | WBS, dictionary and milestones baselined |
| 3 | HC3 PM write | preview `d252c479f4b9` (92 create) | Project Manager | approved | first sync |
| 4 | HC3 PM write | preview `c9ad4f3eb54a` (92 unchanged) | Project Manager | approved | re-sync, idempotency |
| 5 | HC4 risk register | register `abb8ad434b95` | Group Leader (group_leader) | approved | register and what-ifs reviewed |
| 6 | HC5 report release | EDC-2027-03-31-v1 | Group Leader | approved | released after Critic PASS |
| 7 | HC6 change action | CE-01-A01: re-score R01 | Project Manager | approved | re-score accepted |
| 8 | HC6 change action | CE-01-A04: comment + label WBS 1.2.2 | Project Manager | approved | — |
| 9 | HC6 change action | CE-01-A14: milestone note | Project Manager | **rejected** | wording to be agreed with the sponsor first |
| 10 | HC7 bias sign-off | BIAS-1 | Supervisor (supervisor) | approved | findings accepted |

**Refused, as designed:**
- The Group Leader account tried to approve HC2. It was refused before anything was recorded, and logged as `access denied: HC2`, outcome `blocked` (audit #26; `app/auth.py:205-211`).
- The Group Leader account tried to release a planted-fault NRF draft (`critic_stopped`). Release was refused (audit #151; `app/reporting.py:295-298`).

12 of the 15 CE-01 actions were left pending. Nothing was applied without HC6.

### 2.2 Team's real approvals

| Checkpoint | RBAC role (`app/auth.py:26-58`) | Named approver | Date |
|---|---|---|---|
| HC1, HC2, HC3, HC6 | project_manager | [NEEDS INPUT] | [NEEDS INPUT] |
| HC4, HC5 | group_leader | [NEEDS INPUT] | [NEEDS INPUT] |
| HC7 | supervisor | [NEEDS INPUT] | [NEEDS INPUT] |

HC1, HC4 and HC7 are recorded and displayed but do not block any code path (design document §4, limitation L4). HC2, HC3, HC5 and HC6 are enforced in code.

## 3. Bias and fairness check (BIAS-1)

**Method** (`app/governance.py:43-107`):
- Tag each of the 214 consultation responses (`05_Resident_consultation_responses.csv`) with themes, using a lexicon in English, Chinese, Malay and Tamil.
- Rank the themes three ways: by raw count, with each age band weighted equally, and with English-only responses.
- Report skew by channel, age and language.

**Findings** (`docs/governance/evidence/bias_check.json`):

| ID | Severity | Finding |
|---|---|---|
| B1 | high | Online channel gave 160 of 214 responses (74.8%), 115 of them from under-45s. Seabreeze saw the same skew (LL-L06). |
| B2 | high | Residents 65+ gave 25 responses (11.7%) although they are the main users of the active ageing centre; under-45s gave 121 (56.5%). The estate's age profile is NOT FOUND in the pack, so true representativeness cannot be computed. |
| B3 | high | All 19 non-English responses (zh 10, ms 6, ta 3) came on paper or at the town hall, 18 from residents 45+. An English-only summary would drop 11 of 36 active-ageing comments and 6 of 37 lift/access comments. |
| B4 | medium | Raw top four: Childcare, Communication & trust, Lifts & access, Active ageing. Age-re-weighted top four: Childcare, **Active ageing**, Lifts & access, Communication & trust. The order changes, so both must be reported. |
| B5 | medium | Only 25 distinct comment texts across 214 responses; check for template or campaign submissions before weighting. |
| B6 | low | Mean rating by age band ranges from 2.65 (35–44) to 3.48 (18–24). The town hall drew about 40 residents (EDC-4.5) and gave 31 responses. |

**Actions proposed by the check:**
1. Translate and include every non-English comment.
2. Show raw and age-re-weighted priorities side by side.
3. Run a second multilingual paper or door-to-door round for residents 55+ (LL-L06).
4. Have Community Engagement confirm whether the repeated submissions are independent.
5. Hold the consultation summary (D15) until HC7.

**Status:** signed off by the Supervisor account in the demonstration run.

**What the team changed as a result:** [NEEDS INPUT: the team's HC7 decision, and which of actions 1–5 changed the consultation summary or the design input given to KHB — governance owner]

## 4. Guardrail events

| Guardrail | Evidence |
|---|---|
| Agents never delete, close or move to Done | Demonstration: close, delete and Done attempts on a board item all blocked, audit #148–150 (`BLOCKED: …`, outcome `blocked`). Eval T23: 4/4 blocked. |
| `ai-generated` label on every agent item | Enforced at create (`app/pmtool.py:357-358`); read-back reports unlabelled items (`:531`) |
| No PM write without HC2 + HC3 | Eval T21; `app/pmtool.py:431-432, 474-477` |
| Change actions only after HC6 | 15 actions drafted, 3 decided, 12 still pending (demonstration) |
| Unknown or unpermitted API call refused | Unknown paths default to `users.manage` (`server.py:332-340`); denied requests are logged `blocked` |
| Personal tokens never in shared files | `.env` git-ignored; `.env.example` has no values; redaction before logging; no token in git history (`docs/design/00_inventory.md` §0.1) |

## 5. Incidents and the changes we made

These are problems found during development and review, from the commit history, code comments and the development sessions of 6–8 Nov 2026. Incidents from the team's own operation of the system are still to be added [NEEDS INPUT: team incidents, e.g. from the Jira test — all members].

| ID | Date | What happened | How it was found | Change made | Evidence | Status |
|---|---|---|---|---|---|---|
| I-01 | by 8 Nov | Jira's search index lags behind writes, so a quick re-sync could miss items just created and duplicate them | Jira testing | Lookup = one search plus a consistent bulk read of keys already written; sync map per backend | `app/pmtool.py:136-140, 398-425`; commit `8044577` | Closed (mock: T22) |
| I-02 | by 8 Nov | The direction of Jira "Blocks" links is easy to get backwards | Jira testing | First link per session is read back; a reversed link the agent just created is deleted, logged `pm link direction corrected`, and recreated | `app/pmtool.py:294-317`; commit `8044577` | Closed |
| I-03 | by 8 Nov | Localised Jira sites name issue types differently (e.g. 长篇故事 / 任务 / 子任务, "Epic / Task / Sub-task" in Chinese), so lookup by English name fails | Jira testing | Types resolved by hierarchy level, with env overrides | `app/pmtool.py:245-266`; commit `8044577` | Closed |
| I-04 | by 8 Nov | Checkpoints could be approved under a typed-in name | Governance review | Login with four roles; approvals signed by the session account; refused attempts logged | `app/auth.py:1-11`, `server.py:80-92`; commit `8044577` | Closed |
| I-05 | 8 Nov | Design-document inventory found the plan, register and reports were hand-authored tables; the LLM only added extras | Design review (Phase 1) | Core outputs now LLM-generated, with validators and baseline fallback; origin recorded per agent | commit `9356955`; `app/gen.py` | Closed |
| I-06 | 8 Nov | Generated report drafts were STOPPED by the Critic, so the system fell back to templates. Causes: a range fact used in a calculation, "March 2027" with no source date, a computed date, unattributed "on programme" | Audit rows `critic STOP on generated … draft` | Drafting rules added; the full text of failing lines is fed back; revision limit raised from 2 to 3 | `app/reporting.py:151, 176-192, 237` | Closed (T18 passes in LLM mode) |
| I-07 | 8 Nov | NRF JSON truncated at 4,000 output tokens (`llm json parse` error) | Audit log | max_tokens raised to 7,000 and reports capped at 22 lines | `app/reporting.py:173, 193` | Closed |
| I-08 | 8 Nov | The LLM proposed a re-score as "R01 Grant conditions…", which failed validation. The fallback then applied the **curated re-score rules to unrelated generated risks** (e.g. R22) | Change-event test review | Risk ID parsed by regex; curated rules are never applied to a generated register | `app/risk.py:346-371` | Closed |
| I-09 | 8 Nov | Fallback summary was not cached, so an identical re-run spent ~770 tokens | Run accounting (`runs` table) | Summary uses the response cache | `app/reporting.py:141-147` | Closed (re-run 0 tokens) |
| I-10 | 8 Nov | DeepSeek is not on the brief's permitted tool list (brief L210-L212) | Design review | Gemini (Google AI Studio) is primary and DeepSeek is backup; `HCH_LLM_ORDER=gemini` removes the backup | `app/config.py:27-59`, `app/llm.py:66-115` | Code done; Gemini run evidence [NEEDS INPUT] |
| I-11 | 8 Nov | LLM-mode evaluation 27/33: gap recall 77% < 80% target; five checks pin curated IDs | Evaluation | Recorded; proposed fixes in the Evaluation Report §5 | `docs/design/evidence/eval_llm_deepseek_2026-11-08.log` | **Open** |
| I-12 | 8 Nov | Review findings: HC3 approval not re-verified against the current diff; memory returns a false NOT FOUND on EDC cadence; HC1/HC4/HC7 record only | Design review | Documented as limitations L2–L4 | `docs/design/design_document.md` §8 | **Open**: fix or accept [NEEDS INPUT: team lead] |

No incident wrote to the PM tool outside the HC3-approved path. Every blocked attempt in the demonstration and evaluation runs is in the audit log with outcome `blocked`.
