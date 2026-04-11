# POST_MORTEM.md — v5 Post-Run Audit

## Summary
Total anomalies: 4 (critical: 0, high: 1, moderate: 1, low: 2)
Audit date: 2026-04-10

---

## Anomaly Report

### [HIGH] Check 6 / Check 7 (schema error) — Hard cases misclassified as not_applicable_difficulty

| Field | Value |
|---|---|
| anomaly_type | data_pipeline_misclassification |
| case_ids | eval_scenario_381, eval_scenario_411, eval_scenario_616 |
| file_paths | `v5_raw_outputs/eval_scenario_381_forced_multiround_run*.json` (3 files), `v5_raw_outputs/eval_scenario_411_forced_multiround_run*.json` (3 files), `v5_raw_outputs/eval_scenario_616_forced_multiround_run*.json` (3 files) — 9 files total |
| severity | high |
| evidence | All three cases have `difficulty=hard` in `benchmark_cases_verified.json`, but their forced_multiround raw output files carry `note=not_applicable_difficulty` and `rounds=null`. The scoring engine interprets null verdicts as agent failures: IDR=0.0, FVC=0.0, DC=0.0, DRQ=0.0, IDP=1.0, mean=0.25. These 3 cases each contribute 0.25 to `forced_multiround_hard_mean` instead of their true score. Computed `forced_multiround_hard_mean` with all 42 hard cases = 0.9425; re-computed excluding the 3 broken cases across the remaining 39 = 0.9957. Impact: the pipeline erroneously excluded 3 hard cases (7.1% of 42) from forced_multiround execution. |
| recommended_action | Re-run forced_multiround condition for eval_scenario_381, eval_scenario_411, and eval_scenario_616. Regenerate v5_results.json with corrected data before Phase 10 analysis. Investigate root cause: why these 3 hard cases were dispatched with `not_applicable_difficulty` routing. This finding blocks Phase 10 if `forced_multiround_hard_mean` is used as a primary result. |

---

### [MODERATE] Check 7 — Hollow forced-round rate (20.5%)

| Field | Value |
|---|---|
| anomaly_type | hollow_second_round |
| case_ids | eval_scenario_113, eval_scenario_13, eval_scenario_144, eval_scenario_17, eval_scenario_194, eval_scenario_319, eval_scenario_344, eval_scenario_589 |
| file_paths | 24 files across 8 cases x 3 runs in `v5_raw_outputs/eval_scenario_*_forced_multiround_run*.json` |
| severity | moderate |
| evidence | 24 of 117 forced_multiround files with valid rounds have `round2_verdict == round1_verdict` and `round2_points_resolved == 0`. All 24 are `defense_wins` across all 3 runs of 8 cases (100% verdict consistency — not stochastic). Hollow rate = 24/117 = 20.5%, below the 0.5 critical threshold. Pattern is systematic: all 8 cases consistently produce hollow rounds across all 3 runs, suggesting genuine structural cases where no critique points remained to resolve rather than execution failure. All 24 cases logged individually to INVESTIGATION_LOG.jsonl (seq 86–109). |
| recommended_action | Examine whether the 8 hollow cases are defense_wins cases where round 2 is structurally vacuous. Inspect adjudication text to confirm the defender genuinely resolved all points in round 1, leaving nothing for round 2. If so, no remediation needed — annotate these cases as `hollow_by_design`. If round 2 is lazy (defender just reiterates round 1 conclusion), flag for re-run. |

---

### [LOW] Check 3 — eval_scenario_332: pass_fail=fail despite run-1 scores all >= 0.5

| Field | Value |
|---|---|
| anomaly_type | reporting_design_asymmetry |
| case_id | eval_scenario_332 |
| file_path | `v5_results_eval.json` (case-level eval record) |
| severity | low |
| evidence | `v5_results_eval.json` stores scores from isolated_debate run 1 only (source: `self_debate_poc.py` line 275–284). For eval_scenario_332, run 1 scores are: IDR=1.0, IDP=0.6667, DC=1.0, DRQ=1.0, ETD=null, FVC=1.0 — all applicable dims >= 0.5, primary mean = 0.9167. However, `pass_fail=fail` because only 1 of 3 isolated_debate runs passed the `passes >= 2` majority-rule threshold (run 2 and run 3: IDP=0.3333 < 0.5). The failure_attribution field is `none` because it reflects run 1, which genuinely passed. This is not a scoring bug — the scoring logic is correct. It is a reporting design where `v5_results_eval.json` shows run-1 scores regardless of the majority-rule verdict. |
| recommended_action | Add a documentation note to `v5_results_eval.json` (or the scoring engine) clarifying that `scores` are from isolated_debate run 1 only and do not aggregate across runs. Consumers of this file who check scores independently will see an apparent contradiction when pass_fail=fail. No re-scoring required. |

---

### [LOW] Check 8 — DC/FVC baseline divergence_rate is None (expected by design)

| Field | Value |
|---|---|
| anomaly_type | design_limitation_informational |
| case_id | N/A (aggregate metric) |
| file_path | `v5_results.json` → `dc_fvc_diagnostic.baseline` |
| severity | low |
| evidence | `dc_fvc_diagnostic.baseline.divergence_rate = null` because `n_comparable_runs = 0`. DC is always null for baseline (DC is N/A for conditions with no adversarial defender, by design — `self_debate_poc.py` line 9). With DC always null in baseline, there are no comparable runs to compute divergence. All non-baseline conditions show `divergence_rate = 0.0` (all DC and FVC values agree perfectly). No condition shows the highest divergence_rate — all are tied at 0.0. The task note "if forced_multiround shows highest divergence_rate, note as expected" does not apply here. |
| recommended_action | No action required. Document in CONCLUSIONS.md that baseline is excluded from DC/FVC diagnostic by design. The null divergence_rate in baseline is not a scoring bug; it is the expected consequence of DC being structurally inapplicable to single-agent evaluation. |

---

## Checks Passing Clean

| Check | Result |
|---|---|
| Check 1 — ETD schema | PASS — 0 files use old schema keys (measure/success_criterion/failure_criterion). 5 files (eval_scenario_295 x3, eval_scenario_3 x2) use new canonical schema (condition/supports_critique_if/supports_defense_if/ambiguous_if) for baseline runs with empirical_test_agreed verdicts. 1,645 files have empirical_test=null (not applicable). |
| Check 2 — Isolation integrity | PASS (verified-clean) — INVESTIGATION_LOG.jsonl seq 59 confirms check_isolation.py passed: 330 isolated_debate runs clean, no isolation breaches. Not re-run per audit instructions. |
| Check 4 — ETD scoring anomalies | PASS — 0 cases with verdict=empirical_test_agreed and ETD=0.0 in non-baseline/non-ensemble conditions. The 5 baseline files with empirical_test_agreed have ETD=null by design (baseline condition is ETD N/A, `self_debate_poc.py` line 123–124). |
| Check 5 — DC baseline | PASS — 0 baseline runs with DC != null. DC is structurally null for baseline across all 330 baseline files. |
| Check 6 — debate_rounds >= 2 | PASS (conditional) — 0 forced_multiround files have debate_rounds=1. 117 files have debate_rounds=2 (valid). 213 files have debate_rounds=null: 204 are medium-difficulty cases where forced_multiround is not_applicable_difficulty by design; 9 are the 3 hard-case anomalies reported above. |

---

## Phase 10 Blocking Assessment

The high-severity finding (3 hard cases misclassified as not_applicable_difficulty) **blocks Phase 10** if `forced_multiround_hard_mean` is used as a primary result. The computed value 0.9425 is artificially depressed from the true value ~0.9957 by 0.0532 due to the 3 cases scoring 0.25 (agent failure) instead of their true score.

All other findings are non-blocking. The moderate hollow-rate (20.5%) is below the critical threshold and represents 8 structurally consistent cases, not random failures.
