# Phase 3 — Pilot & Calibration

> **Reminders:** `uv run` only. CWD: repo root.

## Required Reading
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--280) — difficulty calibration gate + difficulty labeling requirement
- [hypotheses.md](../references/hypotheses.md) — equivalence bound review after pilot (H1a ±0.015 FC, H5 ±0.03 precision)

---

## Goal
Run baseline on a representative sample to confirm:
1. Cases are not too easy (baseline ceiling effect would suppress signal)
2. N per stratum is sufficient after difficulty filtering
3. Pre-specified equivalence bounds (H1a ±0.015 FC, H5 ±0.03 precision) are appropriate
4. Difficulty labels assigned to all 160 regular cases before Phase 4 commit

---

## Steps

### 3.1 Sample pilot cases
Select ~40 cases per stratum for pilot (~40 regular, ~40 mixed, ~40 defense = ~120 total).
Per `design_decisions.md §2`: "Run baseline on ~40 cases per stratum as a pilot."
Stratified random sample from `benchmark_cases_v7_raw.json`.

### 3.2 Run baseline on pilot sample
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/phase5_benchmark.py \
  --cases pilot_cases_sanitized.json \
  --output-dir pilot_raw_outputs \
  --conditions baseline \
  --max-concurrent 10 \
  --temperature 1.0
```

### 3.3 Score pilot outputs
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --input pilot_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output pilot_results.json
```

### 3.4 Apply difficulty gate
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
results = json.load(open('pilot_results.json'))
by_case = {}
for r in results:
    k = r['case_id']
    by_case.setdefault(k, []).append(r['fc'])
means = {k: sum(v)/len(v) for k, v in by_case.items()}
hard = [k for k, m in means.items() if m < 0.80]
easy = [k for k, m in means.items() if m >= 0.80]
print(f'Hard (pass): {len(hard)}, Easy (discard): {len(easy)}')
print(f'Baseline FC mean (hard cases): {sum(means[k] for k in hard)/len(hard):.4f}' if hard else 'No hard cases')
"
```
**Gate:** baseline FC mean across pilot regular cases must be < 0.80. If ≥ 0.80: increase
case difficulty in case assembly, lower the difficulty target, or consult v6_lessons for
calibration guidance.

### 3.5 Assign difficulty labels (all 160 regular cases)
Per `design_decisions.md §2`: 100% difficulty labeling of all regular cases before Phase 4.
Proxy: pilot baseline FC mean per case.
- FC < 0.60 → `"hard"`
- 0.60 ≤ FC < 0.80 → `"medium"`

Update `difficulty` field in `benchmark_cases_v7_raw.json` for all 160 regular cases.
**Gate:** all 160 regular cases labeled before Phase 4 commit. `difficulty` must not use
`must_find` issue count (answer-key data) — only observable performance.

### 3.6 Review equivalence bounds
After pilot, confirm pre-specified equivalence bounds from `design_decisions.md §4`:
- **H1a:** ±0.015 FC. Derived from v6 data — lower anchor (noise floor ~±0.010) and
  upper anchor (half the v6 ensemble advantage, 0.0287 ÷ 2 = 0.014). Verify v7 pilot
  within-condition FC variance is consistent with v6.
- **H5:** ±0.03 precision. Above the v6 observed diff (+0.017), representing ~3pp on a
  scale where both tiers score above 0.92.
- **Do not change equivalence bounds after Phase 4 commit.** Decide here.

### 3.7 Final case selection
Filter full `benchmark_cases_v7_raw.json` to cases passing the difficulty gate.
Update `v7_cases_sanitized.json` to reflect the filtered set.

Confirm final N per stratum meets minimums:
- Regular: ≥ 160
- Mixed: ≥ 80
- Defense: ≥ 30 (target 40)

---

## Verification
- [ ] `baseline_fc_mean < 0.80` on pilot regular cases
- [ ] All 160 regular cases have `difficulty` label (`"hard"` or `"medium"`)
- [ ] Final regular N ≥ 160, mixed N ≥ 80, defense N ≥ 30
- [ ] Equivalence bound decision recorded before Phase 4 (H1a ±0.015 FC, H5 ±0.03 precision)

## Outputs
- `pilot_results.json`
- Updated `v7_cases_sanitized.json` (difficulty-filtered)

## Gate
Pilot baseline FC mean < 0.80. Sufficient cases per stratum after filtering. Difficulty labels
assigned to all 160 regular cases. Equivalence bounds confirmed (H1a ±0.015 FC, H5 ±0.03 precision).
