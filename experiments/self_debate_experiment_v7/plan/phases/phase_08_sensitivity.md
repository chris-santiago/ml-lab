# Phase 8 — Sensitivity & Robustness

> **Reminders:** `uv run` only. CWD: repo root.

---

## Steps

### 8.1 Within-case variance audit

Key concern: `multiround_2r` may have high run-to-run variance (adversarial exchange is
inherently stochastic). Before claiming a result, check variance:

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode variance \
  --raw v7_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output within_case_variance_v7.json
```

Report per condition:
- Mean within-case variance (across 3 runs per case)
- Fraction of cases with verdict flip (≥1 run disagrees with majority)
- Identify high-variance pairs (flag if > 30% of cases flip)

If `multiround_2r` has substantially higher variance than other conditions, report this
as a deployment limitation (not a validity concern — variance is expected in adversarial
exchange).

### 8.2 Bootstrap stability check

Verify CIs are stable by rerunning with a different seed:

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode analyze \
  --raw v7_raw_outputs \
  --scores v7_rescored_idr_idp.json \
  --cases benchmark_cases_v7_raw.json \
  --output v7_results_seed99.json \
  --bootstrap-n 10000 \
  --seed 99
```

Compare P1, P2, H2_regular CI bounds between seed=42 (primary) and seed=99. Acceptable
variation: ±0.001 on CI bounds (per `design_decisions.md §4`: at n=10,000 bootstrap
samples with n=160 cases, variation above ±0.001 is unexpected). Report if larger.

### 8.3 Scorer sensitivity (spot-check)

Re-score 10% of cases (stratified random) with a second gpt-5.4-mini run. Compare
`idr_documented` between original and re-score. Report mean absolute difference and flag
pairs where delta > 0.15.

### 8.4 RC vs synthetic stability

Verify P1/P2 verdicts hold within each subgroup (RC-only, synthetic-only). If the framework
holds in one subgroup but not the other, note as a scope limitation.

---

## Outputs
- `within_case_variance_v7.json`
- `SENSITIVITY_ANALYSIS.md` (summary of all four checks)

## Gate
`SENSITIVITY_ANALYSIS.md` written. High-variance conditions documented if any.
