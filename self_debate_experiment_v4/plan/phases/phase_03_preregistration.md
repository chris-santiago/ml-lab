# Phase 3 — Pre-Register and Lock Rubric

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **Script:** `plan/scripts/write_preregistration.py` — writes PREREGISTRATION.json and evaluation_rubric.json with all v4 hypotheses, rubric definitions, DC=N/A and ETD=N/A treatments, fair-comparison lift threshold, and 5-condition structure. Run once before Phase 4; outputs are immutable after this point.

```bash
uv run plan/scripts/write_preregistration.py
git add self_debate_experiment_v4/PREREGISTRATION.json \
        self_debate_experiment_v4/evaluation_rubric.json \
        self_debate_experiment_v4/HYPOTHESIS.md \
        self_debate_experiment_v4/BENCHMARK_PROMPTS.md \
        self_debate_experiment_v4/benchmark_verification.json \
        self_debate_experiment_v4/benchmark_cases_verified.json
git commit -m "v4 Phase 3: pre-register rubric, hypotheses, verified cases locked before any agent run"
```

**Logging:**
```bash
uv run log_entry.py --step 3 --cat workflow --action step_start --detail "Phase 3: writing and locking PREREGISTRATION.json and evaluation_rubric.json"
uv run log_entry.py --step 3 --cat write --action write_preregistration --detail "PREREGISTRATION.json locked: DC=N/A baseline, ETD=N/A ensemble/baseline, 5 conditions, fair-comparison lift primary" --artifact PREREGISTRATION.json
uv run log_entry.py --step 3 --cat write --action write_rubric --detail "evaluation_rubric.json written and locked" --artifact evaluation_rubric.json
uv run log_entry.py --step 3 --cat gate --action preregistration_locked --detail "All pre-run locks committed to git before Phase 4"
uv run log_entry.py --step 3 --cat workflow --action step_end --detail "Phase 3 complete"
```
