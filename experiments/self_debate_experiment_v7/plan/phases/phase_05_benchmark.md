# Phase 5 — Benchmark Run

> **Reminders:** `uv run` only. CWD: repo root.
> **All Claude calls go through `pipeline/phase5_benchmark.py` (OpenRouter API). No agent dispatch.**

## Required Reading
- [API_DISPATCH_PLAN.md](../references/API_DISPATCH_PLAN.md) — full benchmark runner design
- [design_decisions.md §1](../references/design_decisions.md#1-conditions-4) — 4 conditions + compute accounting
- [v6_lessons.md L6](../references/v6_lessons.md) — atomic file writes
- [hypotheses.md](../references/hypotheses.md) — output requirements per hypothesis

---

## Key Constraints
- **`HYPOTHESIS.md` committed before this phase begins** (Phase 4 gate)
- **Zero-variance contamination check:** after each condition batch, verify within-case variance > 0 across all 3 runs
- No answer-key fields (`must_find`, `acceptable_resolutions`, `correct_position`) in `v7_cases_sanitized.json`
- Per-assessor `found` booleans in every `ensemble_3x` output (required for union IDR)

---

## Steps

### 5.1 Confirm pre-run state
```bash
cd experiments/self_debate_experiment_v7 && \
git log --oneline -3  # confirm HYPOTHESIS.md commit is present
ls v7_cases_sanitized.json  # confirm sanitized cases exist
wc -l v7_cases_sanitized.json  # sanity check: should be 1 line (JSON array)
```

### 5.2 Run all 4 conditions

Full run: 280 cases × 4 conditions × 3 runs = **3,360 files**

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/phase5_benchmark.py \
  --cases v7_cases_sanitized.json \
  --output-dir v7_raw_outputs \
  --conditions baseline,isolated_debate,ensemble_3x,multiround_2r \
  --max-concurrent 20 \
  --model anthropic/claude-sonnet-4-20250514 \
  --temperature 1.0 \
  --timeout 180 \
  --retries 2
```

Can run one condition at a time and use resume logic between runs:
```bash
--conditions baseline       # 1 condition at a time
--conditions isolated_debate
--conditions ensemble_3x
--conditions multiround_2r
```
Script skips already-completed `(case_id, condition, run_idx)` tuples automatically.

### 5.3 Schema validation after each condition batch
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, glob
files = glob.glob('v7_raw_outputs/*.json')
required = ['case_id','condition','run_idx','critic_raw','all_issues_raised','all_issues_adjudicated','verdict']
errors = []
for f in files:
    try:
        d = json.load(open(f))
        for field in required:
            if field not in d:
                errors.append(f'{f}: missing {field}')
        if d.get('condition') == 'ensemble_3x' and 'assessor_results' not in d:
            errors.append(f'{f}: ensemble_3x missing assessor_results')
    except Exception as e:
        errors.append(f'{f}: {e}')
print(f'{len(errors)} errors across {len(files)} files' if errors else f'All {len(files)} files valid')
"
```

### 5.4 Zero-variance contamination check
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, glob, collections
files = glob.glob('v7_raw_outputs/*.json')
by_key = collections.defaultdict(list)
for f in files:
    d = json.load(open(f))
    by_key[(d['case_id'], d['condition'])].append(d.get('verdict'))
zero_var = [(k, vs) for k, vs in by_key.items() if len(vs) == 3 and len(set(str(v) for v in vs)) == 1]
print(f'{len(zero_var)} zero-variance cases')
if zero_var:
    print('WARNING — identical outputs across all 3 runs signal answer-key leakage')
    for k, v in zero_var[:5]: print(f'  {k}: {v}')
"
```
If zero-variance cases found: **halt**. Investigate leakage vector before continuing.

### 5.5 Verify expected volume
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, glob, collections
files = glob.glob('v7_raw_outputs/*.json')
by_cond = collections.Counter(json.load(open(f))['condition'] for f in files)
print('Files per condition:', dict(by_cond))
print('Total:', len(files), '/ expected 3360')
"
```

---

## Verification
- [ ] Schema validation passes for all 3,360 files
- [ ] Zero-variance check: 0 contaminated cases
- [ ] `ensemble_3x` outputs contain `assessor_results` with per-assessor `found` booleans
- [ ] `multiround_2r` outputs contain both `critic_raw` and `defender_raw`

## Outputs
- `v7_raw_outputs/{case_id}_{condition}_run{idx}.json` (3,360 files)

## Gate
All files pass schema validation. Zero-variance check passes. Expected file count reached.
