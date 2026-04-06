# Phase 1 — CASE_VERIFIER

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

**Mandatory before any experiment agent sees a case.**

**Agent prompt:**

You are CASE_VERIFIER for the v4 benchmark.

IMPORTANT: These cases were generated externally. You are validating them, not authoring them.
You cannot revise cases yourself. Your REVISE decisions are instructions back to the operator.

Read all cases in self_debate_experiment_v4/benchmark_cases.json.

For each case validate:
1. No target leakage — correct verdict not inferrable from case_id or first task_prompt sentence
2. Ground truth unambiguous — ideal_debate_resolution.type clearly correct; experts would agree
3. Must-find items findable — each scoring_targets.must_find_issue_ids item identifiable from task_prompt
4. Scenario realistic — plausible as something a real ML team would do
5. Empirical test diagnostic — for empirical_test_agreed cases, supports_critique_if and
   supports_defense_if specify distinct falsifiable outcomes
6. Schema complete — planted_issues has severity, acceptable_resolutions non-empty,
   verifier_status is "pending", notes field present
7. Defense_wins justification in prompt — for defense cases, justification explicitly stated
8. Mixed-position genuinely two-sided — both positions defensible from task_prompt alone
9. Hard cases require genuine domain expertise — for hard non-defense_wins cases, verify the
   must-find flaw requires knowledge beyond general ML intuition. If a hard case's flaw is
   discoverable by standard ML reasoning alone, mark for REVISE.
10. Critique cases have red herring features — for non-defense_wins cases, verify the scenario
    contains at least one feature that looks suspicious but is actually valid. Cases without
    must_not_claim are weaker — note this.
11. Defense_wins external grounding — at least 3 defense_wins cases should be grounded in
    externally verifiable ML methodology. Flag if fewer than 3 — not a REJECT condition.
12. Difficulty label validation (v4 NEW) — difficulty is defined by expected rubric performance
    on a single-pass baseline, not by how buried the flaw is. Verify:
    - Easy cases: flaw is directly stated or implied; a single-pass assessor should achieve
      >= 0.85 mean across applicable rubric dimensions
    - Medium cases: flaw requires connecting two signals; expected baseline mean 0.55-0.85
    - Hard cases: flaw requires multi-step reasoning or domain knowledge; a single-pass
      assessor is expected to fail on AT LEAST TWO rubric dimensions (IDR, DRQ, ETD, DC, IDP).
      If a hard case's flaw is findable by standard single-pass reasoning, mark for REVISE
      with note explaining which rubric dimensions would not actually be failed.

Assign keep | revise | reject. Write benchmark_verification.json.

Do not run the experiment. Do not score outputs. Validate only.

> **Script:** `plan/scripts/filter_verified_cases.py` — filters cases by verification status; enforces minimums (≥40 keep, ≥10 mixed, ≥8 defense_wins).

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
git add self_debate_experiment_v4/benchmark_verification.json \
        self_debate_experiment_v4/benchmark_cases_verified.json \
        self_debate_experiment_v4/filter_verified_cases.py
git commit -m "v4 Phase 1: CASE_VERIFIER complete, benchmark_cases_verified.json locked"
```
