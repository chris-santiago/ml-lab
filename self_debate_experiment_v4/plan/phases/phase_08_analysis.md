## Phase 8 — Analytical Artifacts

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

```bash
uv run log_entry.py --step 8 --cat workflow --action step_start --detail "Phase 8: generating analytical artifacts — CONCLUSIONS, SENSITIVITY_ANALYSIS, ENSEMBLE_ANALYSIS, figures"
```

**Instruction:**

Generate these artifacts for self_debate_experiment_v4/ using v4_results.json,
stats_results.json, v4_results_eval.json.

REPORTING NORMS (apply to all artifacts in this phase):
- Lead with fair-comparison lift (IDR/IDP/DRQ/FVC). Raw lift in decomposition table only.
- Design property vs limitation: see top-level Reporting Norms section.
- Do not emit mode declarations or internal directives.

1. CONCLUSIONS.md
   - Abstract leading with fair-comparison lift
   - Per-case scoring table: all 5 conditions (forced_multiround shows N/A for non-hard cases)
   - Dimension-level aggregate tables:
     Table A: debate vs ensemble (IDR/IDP/DRQ/FVC only — ETD and DC excluded; see note)
     Table B: debate conditions vs each other (all dims including ETD and DC)
   - Benchmark pass/fail criteria table with results
   - Hypothesis verdicts: all primary and secondary
   - Forced multiround analysis: hard cases only — does forced exchange improve DRQ and IDR?
   - Point resolution rate from DEBATE.md (multiround and forced_multiround only)
   - Failure mode taxonomy by failure_attribution
   - Difficulty label validation result (from difficulty_validation_results.json)
   - External benchmark stratum results (separate — not mixed into primary CIs)

2. SENSITIVITY_ANALYSIS.md
   - Fair-comparison lift as primary metric (explain why DC=N/A and ETD=N/A for baseline)
   - Raw lift decomposition: what dims contribute and why
   - Dimension-stratified analysis: fair dims vs debate-only dims
   - Cases that change pass/fail under any scoring variation

3. ENSEMBLE_ANALYSIS.md
   - Two clean comparisons (Table A and B as in CONCLUSIONS.md)
   - Pre-specified defense_wins criterion result
   - ETD excluded from debate-vs-ensemble comparison with explicit rationale:
     "ETD measures what the Judge determined could resolve a contested point after
     adversarial exchange. For ensemble, no contested-point structure exists."
   - IDP analysis on defense_wins cases
   - **Forced-multiround hollow-round section (required):**
     - Total forced_multiround cases run
     - Hollow-round cases (count + %)
     - Primary forced_multiround results: exclude hollow-round cases
     - Secondary table: include hollow-round cases with note
     - If hollow_rate > 0.5: lead with finding ("majority of hard cases converged in round 1 — forced_multiround provides weak mechanism evidence"); do NOT present primary results as definitive
   - **DC/FVC divergence diagnostic section (required):**
     - DC is diagnostic-only and excluded from primary scoring (PRIMARY_SCORING_DIMS = IDR/IDP/DRQ/ETD/FVC)
     - For each condition, report: n_comparable_runs, mean_abs_delta (DC vs FVC), divergent_run_count (|delta| > 0.2), divergence_rate
     - Source: `dc_fvc_diagnostic` key in `v4_results.json`
     - If any condition shows divergence_rate > 0.1: flag as "DC adds independent signal on this condition — investigate cases"
     - If all conditions show mean_abs_delta < 0.05: note "DC redundant with FVC — empirically confirmed for v4 cases"
     - This section informs whether DC should be promoted to primary scoring in future versions

4. Figures (save as .png):
   - per_condition_comparison.png: bar chart all 5 conditions on overall mean score
     (forced_multiround only on hard cases subset)
   - dimension_heatmap.png: heatmap of dims × conditions (two panels: fair dims, debate-only dims)
   - sensitivity_analysis_chart.png: fair-comparison lift vs raw lift comparison
   - difficulty_scatter.png: difficulty label vs baseline mean (Spearman rho annotated)
   - forced_multiround_hard.png: forced_multiround vs multiround on hard cases (DRQ, IDR)

**Logging:**
```bash
uv run log_entry.py --step 8 --cat write --action write_conclusions --detail "CONCLUSIONS.md written: hypothesis verdicts, per-case table, failure taxonomy" --artifact CONCLUSIONS.md
uv run log_entry.py --step 8 --cat write --action write_sensitivity_analysis --detail "SENSITIVITY_ANALYSIS.md written: fair-comparison lift primary, raw lift decomposition" --artifact SENSITIVITY_ANALYSIS.md
uv run log_entry.py --step 8 --cat write --action write_ensemble_analysis --detail "ENSEMBLE_ANALYSIS.md written: two comparison tables, defense_wins criterion" --artifact ENSEMBLE_ANALYSIS.md
uv run log_entry.py --step 8 --cat write --action write_figures --detail "Analysis figures written: per_condition_comparison.png, dimension_heatmap.png, sensitivity_analysis_chart.png, difficulty_scatter.png, forced_multiround_hard.png"
uv run log_entry.py --step 8 --cat workflow --action step_end --detail "Phase 8 complete"
```

**Phase 8 commit:**
```bash
git add self_debate_experiment_v4/CONCLUSIONS.md self_debate_experiment_v4/SENSITIVITY_ANALYSIS.md \
        self_debate_experiment_v4/ENSEMBLE_ANALYSIS.md self_debate_experiment_v4/*.png
git commit -m "v4 Phase 8: analytical artifacts complete"
```

---
