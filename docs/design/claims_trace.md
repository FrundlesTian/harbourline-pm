# Claims trace — design_document.md (main body §1–§8)

Every factual claim in the main body, with its evidence. Line numbers were first checked on 8 Nov 2026 against code commit `eaf958a`. On 14 Nov 2026 they were re-mapped to the latest code on `main` by diffing each changed file, and spot-checked.

Status:
- **✓** Verified in the repo, or by an offline command run while writing.
- **T** Team statement, not evidenced in the repo.
- **N** Marked [NEEDS INPUT] in the document.

## §1 Purpose, scope, principles

| Claim | Evidence | Status |
|---|---|---|
| Six modules + governance behind one local web UI | `server.py`, `app/agents.py:9-91` | ✓ |
| Facts F01–F78 rejected unless the quote is in the source | `app/facts_catalog.py:89-108`; offline init: 78 facts loaded, 0 rejected | ✓ |
| CF01–CF12 computed from facts | `app/planning.py:219-281` | ✓ |
| Plan, register, reports and change analysis generated as JSON with IDs | `app/planning.py:327-487`, `app/risk.py:173-235`, `app/reporting.py:161-238`, `app/change.py:128-191` | ✓ |
| Grounding rule | `app/gen.py:73-76` | ✓ |
| Unknown IDs dropped; WBS traced; dates kept only if a cited source states them | `app/gen.py:43-54`, `app/planning.py:518-536, 423-432` | ✓ |
| Critic traces numbers, dates, persons | `app/critic.py:82-120` | ✓ |
| Baseline fallback with recorded reason | `app/gen.py:61-66`, `static/app.js` origin row | ✓ |
| Committed eval 34/34 in baseline mode; LLM mode 34/34 | `eval/results/latest.md`; `docs/evaluation/evidence/eval_llm_deepseek_2026-11-14_final.log` | ✓ |
| Assumptions seeded automatically | `app/planning.py:513` | ✓ |

## §2 Architecture

| Claim | Evidence | Status |
|---|---|---|
| Hand-offs logged in `handoffs` | `app/audit.py:52-57`; eval T31 | ✓ |
| Stdlib server, vanilla JS, SQLite | `server.py:482-499`, `static/`, `app/db.py:13-87` | ✓ |
| Gemini first, DeepSeek backup; failed call retried on next provider | `app/config.py:27-59`, `app/llm.py:66-115`; offline stub test, 8 Nov 2026 (fallback logged as `llm provider fallback`) | ✓ (stub only) |
| Mock board with the same contract | `app/pmtool.py:71-135` | ✓ |
| RBAC server-side | `app/auth.py:25-57, 184-202`, `server.py:352-378` | ✓ |
| Identity chosen without a password; start screen opens in English | `app/auth.py:129-148`, `server.py:408-409`; README | ✓ |
| No Streamlit, no JSONL; local URL | repo contents; `app/config.py:84-85` | ✓ |
| 415 line-addressed chunks | offline `pipeline.init()`, 8 Nov 2026 | ✓ |
| Full-run steps 2–6 | `app/pipeline.py:21-33` and cited functions | ✓ |
| Preview → HC3 → apply → read-back | `app/pmtool.py:482-592` | ✓ |
| Temperature 0.0, response cache, stable hashes on re-run | `app/llm.py:34-66`; development run 8 Nov 2026: re-sync 115 unchanged, 0 tokens | ✓ code; run not committed |

## §3 Agent cards

| Claim | Evidence | Status |
|---|---|---|
| Card prompt locations | `app/agents.py:10-90` (per-card ranges in the doc) | ✓ |
| Default models `gemini-2.5-flash` / `deepseek-chat` | `app/config.py:33, 42` | ✓ |
| Gemini tested on a stub only; team runs use DeepSeek | no Gemini log in repo; team statement | ✓ / T |
| Planning rejection thresholds | `app/planning.py:373-376, 416-417, 472-473` | ✓ |
| Tooling stop: HC2 + HC3 | `app/pmtool.py:485-486, 528-531`; T21 | ✓ |
| Jira errors with hint, token redacted | `app/pmtool.py:151-172` | ✓ |
| Memory sufficiency thresholds (2.5, 70%) | `app/memory.py:76-87` | ✓ |
| Memory rejects bad LLM citations | `app/memory.py:105-122` | ✓ |
| Risk validation and ≥12 rule | `app/risk.py:214-227` | ✓ |
| Vendor-change risk added by validator | `app/risk.py:228-234` | ✓ |
| Reporting hands to Critic; template fallback after 3 STOPs | `app/reporting.py:285-287, 249-255` | ✓ |
| Critic rules C1, C3–C8 and blocker | `app/critic.py:123-169` | ✓ |
| Max revisions 3 / 1 / 0 | `app/reporting.py:151, 221-238`; `app/change.py:165-178`; `generate(mutate=...)` path `app/reporting.py:249` | ✓ |
| Release refused unless critic_passed | `app/reporting.py:291-298`; T20 | ✓ |
| Change stop thresholds | `app/change.py:208-221` | ✓ |
| Governance error on unknown checkpoint / unnamed approver | `app/audit.py:60-66` | ✓ |

## §4 Checkpoint map

| Claim | Evidence | Status |
|---|---|---|
| HC1–HC7 definitions | `app/audit.py:16-31` | ✓ |
| Approval recorded under the selected session account; no password, by design for the demo | `server.py:118-143`, `app/auth.py:134-148` | ✓ |
| Approvals table fields + account migration | `app/db.py:58-60, 95-98` | ✓ |
| HC2, HC3, HC5, HC6 enforced in code | `app/pmtool.py:485, 528`; `app/reporting.py:295`; `app/change.py:388-431` | ✓ |
| HC1, HC4, HC7 record-only | grep of `is_approved` / `latest_approval`: used only in status and display (`app/pipeline.py:61-63`, `server.py:100-101, 227, 290`, `app/dashboard.py:59`) | ✓ |
| RBAC owner per checkpoint | `app/auth.py:41, 48, 55` | ✓ |
| Approvers are the role accounts | team decision, 14 Nov 2026 | T |
| Done/close/delete blocked; forbidden fields | `app/pmtool.py:29, 378-390`; T23 | ✓ |
| Read-back reports human-Done items | `app/pmtool.py:586` | ✓ |
| Sponsor decisions given who/when or NOT FOUND | `app/change.py:188-190` | ✓ |
| Done/close/delete are human acts | brief L247–L248 | ✓ |

## §5 Data contract

| Claim | Evidence | Status |
|---|---|---|
| Field mapping rows | `app/pmtool.py:41-61, 245-266, 294-317, 357-358`, header `:1-15` | ✓ |
| Ext key, lookup, hash, create/update/no-op | `app/pmtool.py:37-38, 65-67, 452-479, 515-518, 543-554` | ✓ |
| `change-*` labels survive | `app/pmtool.py:510-512` | ✓ |
| T22: 92 unchanged | `eval/results/latest.md` | ✓ |
| `preview_id` hash; apply refuses others; no re-check | `app/pmtool.py:501, 528, 526-565` | ✓ |
| Read-back fields and `verified` rule | `app/pmtool.py:568-592` | ✓ |
| Allowed/refused operations; link-delete exception | `app/pmtool.py:343-390, 308-312` | ✓ |
| Ten endpoints; 429/503 retry | `app/pmtool.py:209-341, 162-163` | ✓ |
| Jira write tested on the team's demo machine; project `SCRUM`, Free plan, own site; token of Tian Yujia | team statement, 14 Nov 2026 | T |
| Latest sync on Jira: 92 issues, 92 distinct ext keys, 18 Blocks links, Chinese type names | `docs/governance/evidence/jira_snapshot_2026-11-14.json` (read-only GETs, 14 Nov 2026) | ✓ |
| Read path runs before any write | `app/pmtool.py:482-501, 528-531` | ✓ |
| Reset demo: preview, typed confirmation, `preview_id`, lock | `server.py:49-81, 408-415` | ✓ |
| Reset demo: re-check list, deepest-first, `deleteSubtasks=false`, stop on first error, audit per deletion | `app/pmtool.py:401-448` | ✓ code; Jira path not run |
| Reset demo: restore clears approvals, decisions, accounts; keeps `audit_log`; baseline run | `app/pipeline.py:83-100`; `docs/governance/evidence/reset_check.json` (14 Nov 2026) | ✓ |

## §6 Change handling

| Claim | Evidence | Status |
|---|---|---|
| Tags vocabulary; generated items use it only | `app/gen.py:14-16, 57-58` | ✓ |
| Injection as dated source without editing pack | `app/change.py:236-245` | ✓ |
| Keyword tags; matching rule; downstream walk | `app/change.py:21-43, 251-255, 51-58` | ✓ |
| `stale_items` with reasons | `app/change.py:267-282` | ✓ |
| Auto refresh; Critic C5 stops event-blind drafts | `app/change.py:295-306`; T25, T28 | ✓ |
| HC6 actions; approved re-score refreshes reports | `app/change.py:348-431, 399-405`; T26 | ✓ |
| Committed Week 12 evidence = eval T24–T28, baseline mode | `eval/results/latest.md` | ✓ |
| Team's event is CE-01; wording matches the Guide; run on the demo machine | team lead's matriculation number G2510505D; team statement, 14 Nov 2026 | T |

## §7 Governance

| Claim | Evidence | Status |
|---|---|---|
| audit_log schema | `app/db.py:61-64`; `app/audit.py:43-49` | ✓ |
| CSV exports logged | `server.py:432-442` | ✓ |
| Reset demo outputs keeps audit/approvals/decisions; Reset demo keeps only audit | `app/pipeline.py:72-80, 83-100`; `reset_check.json` | ✓ |
| Start-screen calls bypass the permission table | `server.py:408-415` | ✓ |
| T30: 92 rows for 92 issues | `eval/results/latest.md` | ✓ |
| Guardrail list | `app/pmtool.py:319-320, 357-358`; `server.py:370-378` | ✓ |
| Token hygiene | `app/config.py:13-24`, `.gitignore`, `.env.example`, `app/audit.py:33-40`, `app/pmtool.py:599-612`, `app/llm.py:84-91`; history scan in `00_inventory.md` §0.1 | ✓ |
| 214 responses; bias method and results | CSV row count; `app/governance.py:43-107`; T29 | ✓ |
| What changed after HC7: all actions except the second consultation round | team statement, 14 Nov 2026 | T |
| Gemini/AI Studio permitted; Jira Cloud Free recommended; build with or without code; Agent Builder prohibited | brief L210-L212, L232, L205, L239-L240 | ✓ |
| Gemini price 0 in config | `app/config.py:37-38` | ✓ |
| DeepSeek ~US$0.024 per fresh run | development run, 8 Nov 2026 (`runs` table of a temp DB); not committed | ✓ measured; not in repo |
| `HCH_LLM_ORDER=gemini` disables backup | `app/config.py:46-59` | ✓ |
| Vendor-change risk | `app/risk.py:104-106, 228-234` | ✓ |
| Jira Free; Week 12 vendor re-check with no change; DeepSeek accepted by the instructor | team statement, 14 Nov 2026 | T |

## §8 Trade-offs and limitations

| Claim | Evidence | Status |
|---|---|---|
| Fresh DBs give different generated plans | development runs 8 Nov 2026 (122 vs 115 board items); README section "LLM 生成与基线回退" | ✓ (not committed as a log) |
| Permitted orchestration frameworks | brief L229-L230 | ✓ |
| L1: LLM-mode recall 77–82% across runs | `docs/evaluation/evidence/*.log`; baseline 91% in `eval/results/latest.md` | ✓ |
| L3 fixed: frequency questions answered | `app/memory.py:19-21`; eval T34 | ✓ |
| L2: HC3 not re-verified | `app/pmtool.py:526-565` | ✓ |
| L3: EDC cadence false NOT FOUND | offline `memory.answer`, 8 Nov 2026 | ✓ |
| L4: HC1/HC4/HC7 record-only | see §4 | ✓ |
| L6: what-ifs as cards; event-driven re-scoring | `static/app.js` risk view; `app/risk.py:394-419` | ✓ |
| T7, L7, L8: passwordless identities and project-wide reset | `app/auth.py:129-148`; `app/pmtool.py:401-448` | ✓ |

**Claims removed while verifying:** the generated CE-01 analysis findings (§6) were removed because they come from a development run that is not committed.
