# Phase 7 — Analysis

> **Reminders:** `uv run` only. CWD: repo root. All tests must match pre-registered specs in `HYPOTHESIS.md`.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — all test specifications (P1, P2, H1a–H5)
- [design_decisions.md §4](../references/design_decisions.md#4-statistical-tests) — bootstrap protocol, equivalence CI bounds
- [design_decisions.md §5](../references/design_decisions.md#5-open-questions) — `idr_novel` reporting decision

---

## Steps

### 7.1 Run full analysis
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode analyze \
  --raw v7_raw_outputs \
  --scores v7_rescored_idr_idp.json \
  --cases benchmark_cases_v7_raw.json \
  --output v7_results.json \
  --hypothesis-file HYPOTHESIS.md \
  --bootstrap-n 10000 \
  --seed 42
```

### 7.2 Required test outputs in `v7_results.json`

For each test, `v7_results.json` must contain: `point_estimate`, `ci_lower`, `ci_upper`,
`verdict` (PASS/FAIL/INCONCLUSIVE), and `n` (sample size).

| Test | Subset | Metric | Type |
|---|---|---|---|
| P1 | Regular (n=160) | IDR: ensemble_3x > multiround_2r | One-sided bootstrap |
| P2 | Mixed (n=80) | FVC_mixed: multiround_2r > ensemble_3x | One-sided bootstrap |
| H1a | Regular (n=160) | FC: isolated_debate ≈ baseline | Pre-specified CI ±0.015 FC |
| H2_regular | Regular (n=160) | FC: ensemble_3x vs isolated_debate | Two-sided bootstrap |
| H2_mixed | Mixed (n=80) | FVC_mixed: ensemble_3x vs isolated_debate | Two-sided bootstrap |
| H3 | Mixed (n=80) | FVC_mixed: multiround_2r > isolated_debate | One-sided bootstrap |
| H4 | Regular (n=160) | IDR: ensemble_3x > baseline | One-sided bootstrap |
| H5 | Ensemble outputs | Precision: 1/3-flagged ≈ 3/3-flagged | Pre-specified CI ±0.03 |

**H1a verdict:** PASS if 95% CI for (isolated_debate − baseline) FC falls entirely within [−0.015, +0.015].
**H5 verdict:** PASS if 95% CI for (1/3 precision − 3/3 precision) falls entirely within [−0.03, +0.03].
**Framework verdict**: CONFIRMED if P1 AND P2 both pass; otherwise PARTIAL or NOT CONFIRMED.

### 7.3 Per-condition summary table

Compute mean ± std for each condition × metric:

| Condition | IDR | IDP_raw | DRQ | FVC | FC | FVC_mixed |
|---|---|---|---|---|---|---|
| baseline | | | | | | |
| isolated_debate | | | | | | |
| ensemble_3x | | | | | | |
| multiround_2r | | | | | | |

Fill from `v7_results.json`. Record n per condition (some cases may fail schema validation
and be excluded — document exclusions).

### 7.4 Defense case exoneration rate

Per v6 lesson L7, defense cases require separate reporting:

```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, glob, collections
cases = {c['case_id']: c for c in json.load(open('benchmark_cases_v7_raw.json'))}
defense_ids = {cid for cid, c in cases.items() if c['category'] == 'defense'}
files = [f for f in glob.glob('v7_raw_outputs/*.json')
         if json.load(open(f))['case_id'] in defense_ids]
by_cond = collections.defaultdict(list)
for f in files:
    d = json.load(open(f))
    correct = d['verdict'] == 'defense_wins'
    by_cond[d['condition']].append(correct)
for cond, results in by_cond.items():
    rate = sum(results)/len(results)
    print(f'{cond}: {rate:.3f} ({sum(results)}/{len(results)} exonerations)')
"
```

### 7.5 H4 — Ensemble vs baseline IDR (primary + RC subgroup)
**Primary:** one-sided bootstrap for ensemble_3x > baseline IDR on regular cases (n=160).
Promoted from v6 post-hoc (p=0.0000, diff=+0.1005, CI=[+0.0426, +0.1648]).

**Secondary (RC subgroup, directional only):**
Split results by `is_real_paper_case`. Report IDR delta (ensemble_3x − baseline) separately
for RC papers and synthetic cases. Expected: larger ensemble advantage on RC cases (harder,
ecologically valid) — per v6 finding (+0.172 vs +0.059). Report both deltas and the ratio
descriptively. Flag if delta(RC) < delta(synthetic).

At expected n≈40 for RC subgroup, use descriptive statistics only (not formal bootstrap).

### 7.6 H5 — Union pooling precision parity
Using `per_case_issue_map` from Phase 6 step 6.4:
- Compute precision per support tier: (planted_match + valid_novel) / total issues
- Run bootstrap 95% CI on (1/3 precision − 3/3 precision)
- **Verdict:** PASS if CI falls entirely within [−0.03, +0.03]

If the v7 CI half-width is substantially wider than v6 (fewer ensemble outputs), flag
as underpowered rather than adjusting the bound post-hoc.

### 7.7 `idr_novel` per-condition computation
Per `design_decisions.md §5`: compute `idr_novel` (novel valid issues not in `must_find`)
per condition. Report as a paper footnote only — not a table, not a primary or secondary
hypothesis. Flag as future work: novel valid issue rate as a discovery-breadth metric
beyond the planted-flaw ceiling.

---

## Verification
- [ ] All 8 tests present in `v7_results.json` with point estimate + CI + verdict (P1, P2, H1a, H2_reg, H2_mix, H3, H4, H5)
- [ ] Framework verdict (P1+P2) reported
- [ ] Equivalence verdicts use committed bounds (H1a ±0.015 FC, H5 ±0.03 precision — not modified post-hoc)
- [ ] Defense exoneration rate computed and recorded
- [ ] H4 secondary: RC vs synthetic subgroup reported with both deltas
- [ ] `idr_novel` per-condition computed (for footnote)

## Outputs
- `v7_results.json` (all tests)
- `v7_results_eval.json` (per-condition per-metric means)
- `CONCLUSIONS.md` (hypothesis verdicts + framework verdict)

## Gate
`v7_results.json` complete. All 8 tests present (P1, P2, H1a, H2_reg, H2_mix, H3, H4, H5). `CONCLUSIONS.md` written.
