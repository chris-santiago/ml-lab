# Phase 1 — CASE_VERIFIER

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

**Mandatory before any experiment agent sees a case.**

**Agent prompt:**

You are CASE_VERIFIER for the v5 benchmark.

IMPORTANT: These cases were generated externally. You are validating them, not authoring them.
You cannot revise cases yourself. Your REVISE decisions are instructions back to the operator.

Read all cases in self_debate_experiment_v5/benchmark_cases.json.

For each case validate:
1. No target leakage — correct verdict not inferrable from case_id or first task_prompt sentence
2. Ground truth unambiguous — ideal_debate_resolution.type clearly correct; experts would agree
3. Must-find items findable — each scoring_targets.must_find_issue_ids item identifiable from task_prompt
4. Scenario realistic — plausible as something a real ML team would do
5. Empirical test diagnostic — for empirical_test_agreed cases, supports_critique_if and
   supports_defense_if specify distinct falsifiable outcomes
   (No empirical_test_agreed cases in ARCH-1 — check is vacuous; include entry confirming N/A)
6. Schema complete — planted_issues has severity, acceptable_resolutions non-empty,
   verifier_status is "pending", notes field present
7. Defense_wins justification in prompt — for defense cases, justification explicitly stated
8. Mixed-position genuinely two-sided — both positions defensible from task_prompt alone
   (No mixed cases in ARCH-1 — check is vacuous; include entry confirming N/A)
9. Hard cases require genuine domain expertise — for hard non-defense_wins cases, verify the
   must-find flaw requires knowledge beyond general ML intuition. NOTE: ideal_critique is
   empty for all ARCH-1 cases — use planted_issues[].description and the task_prompt itself
   to assess whether the flaw requires genuine domain expertise or is findable by standard
   ML pattern-matching alone. If findable by pattern-matching, mark for REVISE.
10. Critique cases have red herring features — for non-defense_wins cases, verify the scenario
    contains at least one feature that looks suspicious but is actually valid. Read
    scoring_targets.must_not_claim_details (list of {id, claim, why_wrong} dicts) for the
    full claim descriptions — do NOT rely on scoring_targets.must_not_claim which contains
    only opaque IDs. Verify each claim in must_not_claim_details is plausibly present as a
    suspicious-but-valid feature in the task_prompt.
11. Defense_wins external grounding — at least 3 defense_wins cases should be grounded in
    externally verifiable ML methodology. Flag if fewer than 3 — not a REJECT condition.
12. Difficulty label validation (v5 NEW) — difficulty labels are derived empirically from
    _pipeline.proxy_mean (Sonnet single-pass smoke test). Treat the label as authoritative.
    Only mark REVISE when the label is grossly inconsistent with the task_prompt — i.e., when
    a "hard" case's flaw is so directly named or described in the task_prompt that no
    methodology expertise is required to find it. Do NOT re-judge difficulty from first
    principles; the empirical proxy score is the ground truth for difficulty calibration.
    - hard (proxy_mean < 0.55): flaw requires multi-step reasoning or domain knowledge
    - medium (0.55 ≤ proxy_mean < 0.85): flaw requires connecting two signals
    - easy (proxy_mean ≥ 0.85): flaw directly stated or implied

Assign keep | revise | reject. Write benchmark_verification.json.

**Output schema for benchmark_verification.json** (must match exactly):
```json
{
  "cases": [
    {
      "case_id": "<string matching the case's case_id field>",
      "verdict": "keep",
      "notes": "<string explaining reasoning>"
    }
  ]
}
```
The top-level object MUST be a dict with a single `"cases"` key containing an array. Each entry MUST use field name `"verdict"` (not "decision", "status", "result", etc.) with value exactly one of: `"keep"`, `"revise"`, `"reject"`. Every case in benchmark_cases.json must have a corresponding entry.

Do not run the experiment. Do not score outputs. Validate only.

> **Script:** `plan/scripts/filter_verified_cases.py` — filters cases by verification status; enforces minimums (≥50 keep, ≥8 defense_wins). Note: mixed=0 is expected for ARCH-1 — no minimum enforced.

```bash
uv run plan/scripts/filter_verified_cases.py
```

**Logging:**
```bash
uv run log_entry.py --step 1 --cat workflow --action step_start --detail "Phase 1: CASE_VERIFIER"
uv run log_entry.py --step 1 --cat subagent --action dispatch_case_verifier --detail "Verifying benchmark_cases.json" --artifact benchmark_verification.json
uv run log_entry.py --step 1 --cat exec --action filter_verified_cases --detail "filter_verified_cases.py complete" --artifact benchmark_cases_verified.json
uv run log_entry.py --step 1 --cat workflow --action step_end --detail "Phase 1 complete"
```

**Phase 1 commit:**
```bash
git add self_debate_experiment_v5/benchmark_verification.json \
        self_debate_experiment_v5/benchmark_cases_verified.json
git commit -m "v5 Phase 1: CASE_VERIFIER complete, benchmark_cases_verified.json locked"
```
