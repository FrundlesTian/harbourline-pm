# Claims trace — design_document.md (main body §1–§8)

Every factual claim in the main body, with its evidence. Line numbers were checked on 8 Nov 2026 against code commit `eaf958a`, which adds the Gemini provider on top of `9356955`.

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
| Plan, register, reports and change analysis generated as JSON with IDs | `app/planning.py:327-483`, `app/risk.py:128-187`, `app/reporting.py:161-238`, `app/change.py:128-182` | ✓ |
| Grounding rule | `app/gen.py:73-76` | ✓ |
| Unknown IDs dropped; WBS traced; dates kept only if a cited source states them | `app/gen.py:43-54`, `app/planning.py:514-532, 419-428` | ✓ |
| Critic traces numbers, dates, persons | `app/critic.py:82-120` | ✓ |
| Baseline fallback with recorded reason | `app/gen.py:61-66`, `static/app.js` origin row | ✓ |
| Committed eval 33/33 in baseline mode | `eval/results/latest.md` (2026-11-06, LLM off); re-run 8 Nov 2026 (`--no-llm`): 33/33 | ✓ |
| Assumptions seeded automatically | `app/planning.py:509` | ✓ |

## §2 Architecture

| Claim | Evidence | Status |
|---|---|---|
| Hand-offs logged in `handoffs` | `app/audit.py:52-57`; eval T31 | ✓ |
| Stdlib server, vanilla JS, SQLite | `server.py:435-452`, `static/`, `app/db.py:13-87` | ✓ |
| Gemini first, DeepSeek backup; failed call retried on next provider | `app/config.py:27-59`, `app/llm.py:66-115`; offline stub test, 8 Nov 2026 (fallback logged as `llm provider fallback`) | ✓ (stub only) |
| Mock board with the same contract | `app/pmtool.py:71-135` | ✓ |
| RBAC server-side | `app/auth.py:26-58`, `server.py:314-340` | ✓ |
| No Streamlit, no JSONL; local URL | repo contents; `app/config.py:84-85` | ✓ |
| 415 line-addressed chunks | offline `pipeline.init()`, 8 Nov 2026 | ✓ |
| Full-run steps 2–6 | `app/pipeline.py:21-33` and cited functions | ✓ |
| Preview → HC3 → apply → read-back | `app/pmtool.py:428-538` | ✓ |
| Temperature 0.0, response cache, stable hashes on re-run | `app/llm.py:34-66`; development run 8 Nov 2026: re-sync 115 unchanged, 0 tokens | ✓ code; run not committed |

## §3 Agent cards

| Claim | Evidence | Status |
|---|---|---|
| Card prompt locations | `app/agents.py:10-90` (per-card ranges in the doc) | ✓ |
| Default models `gemini-2.5-flash` / `deepseek-chat` | `app/config.py:33, 42` | ✓ |
| Gemini tested on a stub only | this session; no Gemini log in repo | ✓ / N |
| Planning rejection thresholds | `app/planning.py:369-372, 412-413, 468-469` | ✓ |
| Tooling stop: HC2 + HC3 | `app/pmtool.py:431-432, 474-477`; T21 | ✓ |
| Jira errors with hint, token redacted | `app/pmtool.py:151-172` | ✓ |
| Memory sufficiency thresholds (2.5, 70%) | `app/memory.py:72-83` | ✓ |
| Memory rejects bad LLM citations | `app/memory.py:101-118` | ✓ |
| Risk validation and ≥12 rule | `app/risk.py:166-179` | ✓ |
| Vendor-change risk added by validator | `app/risk.py:180-186` | ✓ |
| Reporting hands to Critic; template fallback after 3 STOPs | `app/reporting.py:285-287, 249-255` | ✓ |
| Critic rules C1, C3–C8 and blocker | `app/critic.py:123-169` | ✓ |
| Max revisions 3 / 1 / 0 | `app/reporting.py:151, 221-238`; `app/change.py:165-178`; `generate(mutate=...)` path `app/reporting.py:249` | ✓ |
| Release refused unless critic_passed | `app/reporting.py:291-298`; T20 | ✓ |
| Change stop thresholds | `app/change.py:199-212` | ✓ |
| Governance error on unknown checkpoint / unnamed approver | `app/audit.py:60-66` | ✓ |

## §4 Checkpoint map

| Claim | Evidence | Status |
|---|---|---|
| HC1–HC7 definitions | `app/audit.py:16-31` | ✓ |
| Approval signed by logged-in account | `server.py:80-105` | ✓ |
| Approvals table fields + account migration | `app/db.py:58-60, 95-98` | ✓ |
| HC2, HC3, HC5, HC6 enforced in code | `app/pmtool.py:431, 474`; `app/reporting.py:295`; `app/change.py:373-416` | ✓ |
| HC1, HC4, HC7 record-only | grep of `is_approved` / `latest_approval`: used only in status and display (`app/pipeline.py:61-63`, `server.py:62-63, 189, 252`, `app/dashboard.py:59`) | ✓ |
| RBAC owner per checkpoint | `app/auth.py:43, 49, 56` | ✓ |
| Approver names | — | N |
| Done/close/delete blocked; forbidden fields | `app/pmtool.py:29, 378-390`; T23 | ✓ |
| Read-back reports human-Done items | `app/pmtool.py:532` | ✓ |
| Sponsor decisions given who/when or NOT FOUND | `app/change.py:179-181` | ✓ |
| Done/close/delete are human acts | brief L247–L248 | ✓ |

## §5 Data contract

| Claim | Evidence | Status |
|---|---|---|
| Field mapping rows | `app/pmtool.py:41-61, 245-266, 294-317, 357-358`, header `:1-15` | ✓ |
| Ext key, lookup, hash, create/update/no-op | `app/pmtool.py:37-38, 65-67, 398-425, 461-464, 489-500` | ✓ |
| `change-*` labels survive | `app/pmtool.py:456-458` | ✓ |
| T22: 92 unchanged | `eval/results/latest.md` | ✓ |
| `preview_id` hash; apply refuses others; no re-check | `app/pmtool.py:447, 474, 472-511` | ✓ |
| Read-back fields and `verified` rule | `app/pmtool.py:514-538` | ✓ |
| Allowed/refused operations; link-delete exception | `app/pmtool.py:343-390, 308-312` | ✓ |
| Ten endpoints; 429/503 retry | `app/pmtool.py:209-341, 162-163` | ✓ |
| Jira write tested on another machine | team statement, 8 Nov 2026 | T / N |

## §6 Change handling

| Claim | Evidence | Status |
|---|---|---|
| Tags vocabulary; generated items use it only | `app/gen.py:14-16, 57-58` | ✓ |
| Injection as dated source without editing pack | `app/change.py:227-236` | ✓ |
| Keyword tags; matching rule; downstream walk | `app/change.py:21-43, 242-246, 51-58` | ✓ |
| `stale_items` with reasons | `app/change.py:258-273` | ✓ |
| Auto refresh; Critic C5 stops event-blind drafts | `app/change.py:280-291`; T25, T28 | ✓ |
| HC6 actions; approved re-score refreshes reports | `app/change.py:333-416, 384-390`; T26 | ✓ |
| Committed Week 12 evidence = eval T24–T28, baseline mode | `eval/results/latest.md` | ✓ |
| Team's own Week 12 run | — | N |

## §7 Governance

| Claim | Evidence | Status |
|---|---|---|
| audit_log schema | `app/db.py:61-64`; `app/audit.py:43-49` | ✓ |
| CSV exports logged | `server.py:385-395` | ✓ |
| Reset keeps audit/approvals/decisions | `app/pipeline.py:72-80` | ✓ |
| T30: 92 rows for 92 issues | `eval/results/latest.md` | ✓ |
| Guardrail list | `app/pmtool.py:319-320, 357-358`; `server.py:332-340` | ✓ |
| Token hygiene | `app/config.py:13-24`, `.gitignore`, `.env.example`, `app/audit.py:33-40`, `app/pmtool.py:545-558`, `app/llm.py:84-91`; history scan in `00_inventory.md` §0.1 | ✓ |
| 214 responses; bias method and results | CSV row count; `app/governance.py:43-107`; T29 | ✓ |
| What changed after HC7 | — | N |
| Gemini/AI Studio permitted; Jira Cloud Free recommended; build with or without code; Agent Builder prohibited | brief L210-L212, L232, L205, L239-L240 | ✓ |
| Gemini price 0 in config | `app/config.py:37-38` | ✓ |
| DeepSeek ~US$0.024 per fresh run | development run, 8 Nov 2026 (`runs` table of a temp DB); not committed | ✓ measured; not in repo |
| `HCH_LLM_ORDER=gemini` disables backup | `app/config.py:46-59` | ✓ |
| Vendor-change risk | `app/risk.py:103-105, 180-186` | ✓ |
| Jira tier; Week 12 vendor re-check | — | N |

## §8 Trade-offs and limitations

| Claim | Evidence | Status |
|---|---|---|
| Fresh DBs give different generated plans | development runs 8 Nov 2026 (122 vs 115 board items); README section "LLM 生成与基线回退" | ✓ (not committed as a log) |
| Permitted orchestration frameworks | brief L229-L230 | ✓ |
| L1: LLM-mode recall 77%; 5 ID-pinned fails | `docs/design/evidence/eval_llm_deepseek_2026-11-08.log`; baseline 91% in `eval/results/latest.md` | ✓ |
| L2: HC3 not re-verified | `app/pmtool.py:472-511` | ✓ |
| L3: EDC cadence false NOT FOUND | offline `memory.answer`, 8 Nov 2026 | ✓ |
| L4: HC1/HC4/HC7 record-only | see §4 | ✓ |
| L6: what-ifs as cards; event-driven re-scoring | `static/app.js` risk view; `app/risk.py:346-371` | ✓ |

**Claims removed while verifying:** the generated CE-01 analysis findings (§6) were removed because they come from a development run that is not committed.
