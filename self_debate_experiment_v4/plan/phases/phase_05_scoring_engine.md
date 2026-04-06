## Phase 5 — Build the Scoring Engine

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **v4 scorer changes from v3:** DC=N/A for baseline (not 0.0); ETD=N/A for ensemble and baseline; single canonical ETD schema with `ambiguous_if`; 5 conditions; fair-comparison lift primary; DRQ not capped for any condition.

> **Script:** `plan/scripts/self_debate_poc.py` — scoring engine for all 5 conditions. Implements v4 rubric: DC=N/A for baseline and defense_wins, ETD=N/A for ensemble/baseline, fair-comparison lift (IDR/IDP/DRQ/FVC), forced_multiround hard-cases-only. Reads `benchmark_cases_verified.json` and `v4_raw_outputs/`. Writes `v4_results.json` and `v4_results_eval.json`. Run from the experiment root directory.
>
> **Note:** `OUTPUT_DIR = Path.cwd()` — the script resolves output paths relative to the working directory, not the script location. Always invoke from `self_debate_experiment_v4/`.

```bash
uv run plan/scripts/self_debate_poc.py
```

**Logging and commit:**
```bash
uv run log_entry.py --step 5 --cat workflow --action step_start --detail "Phase 5: building scoring engine self_debate_poc.py"
uv run log_entry.py --step 5 --cat write --action write_self_debate_poc --detail "self_debate_poc.py: DC=N/A baseline, ETD=N/A ensemble/baseline, 5 conditions, canonical ETD schema" --artifact self_debate_poc.py
uv run log_entry.py --step 5 --cat workflow --action step_end --detail "Phase 5 complete"
git add self_debate_experiment_v4/self_debate_poc.py
git commit -m "v4 Phase 5: scoring engine with DC=N/A, ETD=N/A, 5 conditions, canonical ETD schema"
```

---
