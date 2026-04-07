## Phase 7 — Score and Compute Statistics

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

```bash
uv run plan/scripts/self_debate_poc.py
# Produces: v5_results.json, v5_results_eval.json
```

> **Script:** `plan/scripts/stats_analysis.py` — bootstrap CIs (10,000 resamples, seed 42), Wilcoxon signed-rank tests on fair-comparison dims, dimension aggregates, within-case variance, failure attribution counts. Deps: numpy, scipy. Writes `stats_results.json`.

> **Script:** `plan/scripts/sensitivity_analysis.py` — fair-comparison lift vs raw lift decomposition, dimension-stratified analysis. Writes `sensitivity_analysis_results.json`.

> **Script:** `plan/scripts/difficulty_validation.py` — Spearman correlation between difficulty labels and baseline rubric performance. Writes `difficulty_validation_results.json`. Warns if rho > -0.1 or p > 0.1.

> **Script:** `plan/scripts/within_case_variance.py` — within-case variance analysis across all conditions; flags high-variance cases (std > 0.1). Writes `within_case_variance_results.json`.

```bash
uv run plan/scripts/within_case_variance.py
```

```bash
uv run plan/scripts/stats_analysis.py
uv run plan/scripts/sensitivity_analysis.py
uv run plan/scripts/difficulty_validation.py
```

**Logging:**
```bash
uv run log_entry.py --step 7 --cat workflow --action step_start --detail "Phase 7: scoring engine run, statistics, sensitivity, difficulty validation"
uv run log_entry.py --step 7 --cat exec --action run_scoring_engine --detail "self_debate_poc.py complete — v5_results.json and v5_results_eval.json produced" --artifact v5_results.json
uv run log_entry.py --step 7 --cat write --action write_results --detail "v5_results.json written" --artifact v5_results.json
uv run log_entry.py --step 7 --cat write --action write_eval_results --detail "v5_results_eval.json written" --artifact v5_results_eval.json
uv run log_entry.py --step 7 --cat exec --action run_stats_analysis --detail "stats_analysis.py complete — bootstrap CIs, Wilcoxon tests, dimension aggregates" --artifact stats_results.json
uv run log_entry.py --step 7 --cat write --action write_stats_results --detail "stats_results.json written" --artifact stats_results.json
uv run log_entry.py --step 7 --cat exec --action run_sensitivity_analysis --detail "sensitivity_analysis.py complete — fair-comparison and raw lift decomposition" --artifact sensitivity_analysis_results.json
uv run log_entry.py --step 7 --cat write --action write_sensitivity_results --detail "sensitivity_analysis_results.json written" --artifact sensitivity_analysis_results.json
uv run log_entry.py --step 7 --cat exec --action run_difficulty_validation --detail "difficulty_validation.py complete — Spearman rho computed" --artifact difficulty_validation_results.json
uv run log_entry.py --step 7 --cat write --action write_difficulty_validation --detail "difficulty_validation_results.json written" --artifact difficulty_validation_results.json
uv run log_entry.py --step 7 --cat write --action write_variance_results --detail "within_case_variance_results.json written" --artifact within_case_variance_results.json
uv run log_entry.py --step 7 --cat workflow --action step_end --detail "Phase 7 complete"
```

**Phase 7 commit:**
```bash
git add self_debate_experiment_v5/v5_results.json self_debate_experiment_v5/v5_results_eval.json \
        self_debate_experiment_v5/stats_results.json self_debate_experiment_v5/sensitivity_analysis_results.json \
        self_debate_experiment_v5/difficulty_validation_results.json \
        self_debate_experiment_v5/within_case_variance_results.json
git commit -m "v5 Phase 7: scoring complete, stats and sensitivity analysis"
```

---
