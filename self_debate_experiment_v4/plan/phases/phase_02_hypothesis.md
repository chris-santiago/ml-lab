# Phase 2 — HYPOTHESIS.md and BENCHMARK_PROMPTS.md

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

**Instruction:**

Write two files in self_debate_experiment_v4/:

1. HYPOTHESIS.md — formal hypothesis:
   Claim: the isolated self-debate protocol (ml-critic + ml-defender each receiving only
   the task prompt, orchestrator adjudicates) will achieve a benchmark aggregate score
   at least +0.10 higher than a single-pass baseline on the fair-comparison dimensions
   (IDR, IDP, DRQ, FVC) — dimensions where baseline has equal structural agency.
   Mechanism: adversarial role separation forces engagement with both sides, producing
   better-typed verdicts and catching false positives that correlated parallel assessors miss.
   Primary metrics: IDR, IDP, DRQ, FVC (fair-comparison set). Secondary metrics: DC, ETD
   (debate-internal; not used in lift calculation against baseline).

   Five conditions:
   - isolated_debate: Critic and Defender each receive only task_prompt; orchestrator adjudicates
   - multiround: Defender sees Critique; up to 4 rounds; ml-lab protocol
   - forced_multiround: Same as multiround but minimum 2 rounds enforced; hard cases only
   - ensemble: 3 independent assessors + ETD-constrained synthesizer; compute-matched
   - baseline: single-pass, no structure

   Rubric scoring notes:
   - DC = N/A for baseline (no Defender role; penalizing its absence is not a valid comparison;
     consistent with ETD N/A treatment for inapplicable case types; pre-registered)
   - ETD = N/A for ensemble and baseline (no adversarial exchange; no contested-point structure;
     scoring ETD for conditions that never had adversarial exchange confounds the comparison)
   - DC = N/A for defense_wins cases (IDR/IDP also N/A per v3 convention)

   Secondary hypotheses:
   (1) Debate outperforms compute-matched ensemble on IDR/IDP/DRQ/FVC (fair-comparison dimensions)
   (2) Ensemble DC >= 0.5 on >= 60% of defense_wins cases (compute budget partially explains
       defense_wins advantage)
   (3) Forced multiround outperforms natural multiround on hard cases (additional exchange
       surfaces real signal when cases have genuine complexity)

   Convergence metric (v4 replacement):
   Point resolution rate = (points resolved by concession or empirical agreement) /
   (total contested points in DEBATE.md). Extraction: count DEBATE.md entries with
   status "Resolved: critic wins", "Resolved: defender wins", or
   "Resolved: empirical_test_agreed" vs total contested points listed.
   Diagnostic only — not used in pass/fail determination.

2. BENCHMARK_PROMPTS.md — all task_prompt fields from benchmark_cases_verified.json,
   verbatim, one section per case. Header: case_id, category, difficulty, correct_position.
   Do NOT include ground_truth, planted_issues, scoring_targets, or any answer-key fields.

**Logging:**
```bash
uv run log_entry.py --step 2 --cat workflow --action step_start --detail "Phase 2: writing HYPOTHESIS.md and BENCHMARK_PROMPTS.md"
uv run log_entry.py --step 2 --cat write --action write_hypothesis --detail "HYPOTHESIS.md written: 5 conditions, DC/ETD N/A rationale, fair-comparison lift primary" --artifact HYPOTHESIS.md
uv run log_entry.py --step 2 --cat write --action write_benchmark_prompts --detail "BENCHMARK_PROMPTS.md written" --artifact BENCHMARK_PROMPTS.md
uv run log_entry.py --step 2 --cat workflow --action step_end --detail "Phase 2 complete"
```

**Phase 2 commit:**
```bash
git add self_debate_experiment_v4/HYPOTHESIS.md self_debate_experiment_v4/BENCHMARK_PROMPTS.md
git commit -m "chore: snapshot v4 phase 2 artifacts — hypothesis and benchmark prompts [none]"
uv run log_entry.py --step 2 --cat exec --action commit_phase_artifacts --detail "committed phase 2 artifacts: HYPOTHESIS.md, BENCHMARK_PROMPTS.md"
```
