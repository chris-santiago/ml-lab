# Phase 9 — Cross-Vendor Validation

> **Reminders:** `uv run` only. CWD: repo root.

---

## Purpose

Spot-check that gpt-5.4-mini IDR scores are consistent across a representative sample.
v6 confirmed that same-model scoring produces IDR delta of −0.7737 vs cross-vendor.
This phase validates the cross-vendor scorer is stable, not that it's better.

---

## Steps

### 9.1 Sample 10% for re-scoring

Stratified 10% random sample: ~16 regular + ~8 mixed + ~4 defense = ~28 cases.
Re-score all runs (3 per case) using the same gpt-5.4-mini scorer.

```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, random
random.seed(77)
cases = json.load(open('benchmark_cases_v7_raw.json'))
by_cat = {}
for c in cases:
    by_cat.setdefault(c['category'], []).append(c['case_id'])
sample = []
for cat, ids in by_cat.items():
    n = max(2, int(len(ids) * 0.10))
    sample.extend(random.sample(ids, n))
print(f'Sample: {len(sample)} cases')
json.dump(sample, open('cross_vendor_sample.json', 'w'))
"
```

### 9.2 Re-score sample
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode rescore \
  --input v7_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output cross_vendor_scores_v7.json \
  --case-filter cross_vendor_sample.json \
  --scorer-model $CROSS_VENDOR_MODEL \
  --scorer-base-url $CROSS_VENDOR_BASE_URL \
  --scorer-api-key $CROSS_VENDOR_API_KEY
```

### 9.3 Compute agreement
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
orig = {(s['case_id'], s['condition'], s['run_idx']): s['idr_documented']
        for s in json.load(open('v7_rescored_idr_idp.json'))}
rescore = {(s['case_id'], s['condition'], s['run_idx']): s['idr_documented']
           for s in json.load(open('cross_vendor_scores_v7.json'))}
common = set(orig) & set(rescore)
deltas = [abs(orig[k] - rescore[k]) for k in common]
print(f'Mean absolute delta: {sum(deltas)/len(deltas):.4f}')
print(f'Max delta: {max(deltas):.4f}')
print(f'Pairs with delta > 0.15: {sum(d > 0.15 for d in deltas)} / {len(deltas)}')
"
```

Flag if mean absolute delta > 0.05 — indicates scorer instability. Report in `CONCLUSIONS.md`.

---

## Outputs
- `cross_vendor_scores_v7.json`
- Agreement metrics appended to `SENSITIVITY_ANALYSIS.md`

## Gate
Cross-vendor agreement computed and documented.
