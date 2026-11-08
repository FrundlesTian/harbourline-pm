# Open items — Design Document

Every `[NEEDS INPUT]` in `design_document.md`, grouped by owner. Deadline: 23:59 Thu 12 Nov 2026 (SGT).

## Team lead
1. Team name, members and module owned by each, for the title block.
2. Confirm the submission repository, branch and commit, and that the panel has access. All work is merged to `main` (code commit `eaf958a`).
3. Named approver for each checkpoint HC1–HC7 (§4). The roles exist in code; the names do not.
4. Confirm the owners and revisit triggers proposed in the Appendix A assumption register.
5. Any sponsor answers after Round 1 that are not in the repo.

## Tool-integration owner
6. **Export of the Jira run tested on the other machine:** audit CSV and approvals CSV (`/api/export/...`). The design document cites this run as a team statement only. It is the main evidence for minimum requirement 2.1.
7. Jira project key and plan tier (Free?), and confirmation that the site is the team's own and not a work instance.
8. Evidence that the read path ran and was logged before the first write, e.g. the dates of `scripts/jira_check.py` / health check against the first `pm create`.
9. Whose personal Jira token and Gemini / DeepSeek keys are used (names only).
10. **One logged run with Gemini as the LLM**, e.g. `python3 scripts/llm_smoke_test.py` or a full run with `GEMINI_API_KEY` set. Without it, "Gemini primary" is code-only. Also confirm that Google AI Studio free-tier data-use terms are acceptable for the pack.
11. Week 12 re-check of tool vendors (Gemini, DeepSeek, Jira) and its date.

## Change-handling owner
12. Which Week 12 event applies to the team (CE-01 odd / CE-02 even matriculation digit), the wording confirmed against the Week 12 Guide, and the date of the team's own run to cite in §6.

## Governance owner
13. HC7 decision on the bias check, and what changed in the consultation summary as a result (§7, Governance Log).

## Evaluation owner
14. Review `eval/gold_gaps.json`, which sets the gap-recall figure.
15. Decide how to handle LLM mode in the evaluation report. LLM mode scores 27/33; T01 recall is 77%, and T04/T24/T26/T27/T33 pin baseline IDs (`docs/design/evidence/eval_llm_deepseek_2026-11-08.log`).

## All members
16. AI-use declaration (Appendix D): who reviewed the design document and code, and which AI tools produced the evaluation report, governance log and slides.

## Code decisions, carried forward from the inventory
17. Fix or keep as limitations:
    - L2: HC3 approval is not re-verified against the current diff.
    - L3: memory returns a false NOT FOUND on EDC cadence.
    - L4: HC1, HC4 and HC7 are record-only.
    - L1: LLM-mode gap recall is below target.

    The document currently states all four as limitations.
