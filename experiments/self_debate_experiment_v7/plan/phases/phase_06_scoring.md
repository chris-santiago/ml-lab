# Phase 6 — Cross-Model Scoring

> **Reminders:** `uv run` only. CWD: repo root. Cross-vendor scoring uses gpt-5.4-mini via OpenRouter.

## Required Reading
- [v6_lessons.md L5](../references/v6_lessons.md) — cross-vendor scoring rationale

---

## Steps

### 6.1 Run IDR/IDP scorer
gpt-5.4-mini scores Claude outputs — not Claude scoring itself (per v6 lesson L5:
same-model scoring produces IDR delta of −0.7737). Uses `CROSS_VENDOR_API_KEY`.

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode rescore \
  --input v7_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output v7_rescored_idr_idp.json \
  --scorer-model $CROSS_VENDOR_MODEL \
  --scorer-base-url $CROSS_VENDOR_BASE_URL \
  --scorer-api-key $CROSS_VENDOR_API_KEY
```

IDR scoring (bidirectional per v6 lesson):
- `idr_documented` — recall against `must_find` issues in `benchmark_cases_v7_raw.json`
- `idr_novel` — novel valid concerns not in `must_find` (secondary, stored separately)

IDP scoring (dual field):
- `idp_raw` — precision from `all_issues_raised`
- `idp_adj` — precision from `all_issues_adjudicated`

### 6.2 Validate scorer output
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
scores = json.load(open('v7_rescored_idr_idp.json'))
expected = set()
import glob
for f in glob.glob('v7_raw_outputs/*.json'):
    d = json.load(open(f))
    expected.add((d['case_id'], d['condition'], d['run_idx']))
scored = {(s['case_id'], s['condition'], s['run_idx']) for s in scores}
missing = expected - scored
print(f'Scored: {len(scored)}, Missing: {len(missing)}')
if missing: print('Sample missing:', list(missing)[:5])
"
```

### 6.3 Rule-based scoring (DRQ + FVC)
DRQ and FVC are rule-based — computed directly from output verdict fields:
- `FVC`: `verdict == correct_position` → 1.0, else 0.0
- `DRQ`: 1.0 if verdict in `acceptable_resolutions`, 0.5 if partial, 0.0 otherwise

These are computed in `v7_scoring.py` from `benchmark_cases_v7_raw.json` ground truth,
not by a separate API scorer. DRQ/FVC are immune to self-preference bias by construction.

**Defense cases:** FC_defense = mean(DRQ, FVC) — 2 dimensions only (IDR/IDP undefined
for defense cases). Defense cases excluded from P1, P2, H1a, H2, H4 hypothesis tests.

### 6.4 H5 per-case issue classification (ensemble_3x only)
Per `design_decisions.md §3`: a single gpt-5.4-mini call per ensemble_3x case receives
all 3 assessors' `all_issues_raised` lists, ground truth `must_find_issue_ids`, and
`must_not_claim`. It deduplicates across assessors, classifies each unique issue as
`planted_match | valid_novel | false_claim | spurious`, and assigns support tiers from
the `raised_by` count (1/3, 2/3, or 3/3).

Output stored as `per_case_issue_map` in scoring output. Precision per tier =
(planted_match + valid_novel) / total issues at that tier. This data feeds H5
(precision parity test in Phase 7).

---

## Verification
- [ ] `v7_rescored_idr_idp.json` has IDR/IDP entries for all 3,360 files
- [ ] `idr_documented` and `idr_novel` both present per entry
- [ ] `idp_raw` and `idp_adj` both present per entry
- [ ] No missing entries (scorer coverage = 100%)
- [ ] `per_case_issue_map` present for all ensemble_3x cases with support tiers

## Outputs
- `v7_rescored_idr_idp.json`

## Gate
`v7_rescored_idr_idp.json` complete with 100% coverage. H5 issue classification done for all ensemble_3x cases.
