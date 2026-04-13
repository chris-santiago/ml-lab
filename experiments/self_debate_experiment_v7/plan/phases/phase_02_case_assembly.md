# Phase 2 — Case Library Assembly

> **Reminders:** `uv run` only. CWD: repo root.

## Required Reading
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--280) — stratum targets
- [schema_b.md](../references/schema_b.md) — Schema B field table + format constraints
- [v6_lessons.md L7](../references/v6_lessons.md) — defense case ground truth requirement

---

## Steps

### 2.1 Run synthetic generation pipelines (if needed per Phase 1 yield decision)

All three strata are generated in a single orchestrator run. Adjust `--batch-size`, `--mixed`,
and `--defense` counts to supplement however many RC cases Phase 1 provided.

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/orchestrator.py \
  --batch-size 160 \
  --start-case-id 700 \
  --mixed 80 \
  --defense 40
```

This produces `cases_700-1019.json` (or similar range) in the experiment root.
Use `--resume` to skip already-completed cases if the run is interrupted.

### 2.2 Normalize all sources to Schema B

`normalize_cases.py` auto-discovers all `cases_*.json` batch files in the experiment root
(orchestrator output) and reads `pipeline/run/rc_candidates/rc_cases_raw.json` for RC cases.

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/normalize_cases.py \
  --output benchmark_cases_v7_raw.json
```

### 2.3 Schema B validation

Schema B uses a nested structure (`ground_truth.correct_position`, `scoring_targets.*`).
The validation below matches normalize_cases.py output:

```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
with open('benchmark_cases_v7_raw.json') as f:
    cases = json.load(f)
required_top = ['case_id','hypothesis','domain','ml_task_type','category','difficulty',
                'task_prompt','is_real_paper_case']
errors = []
for c in cases:
    for field in required_top:
        if field not in c:
            errors.append(f'{c.get(\"case_id\",\"?\")} missing {field}')
    cp = c.get('ground_truth', {}).get('correct_position')
    if cp not in ('critique_wins','defense_wins','empirical_test_agreed'):
        errors.append(f'{c[\"case_id\"]} bad correct_position: {cp!r}')
    if c['category'] not in ('regular','mixed','defense'):
        errors.append(f'{c[\"case_id\"]} bad category: {c[\"category\"]}')
    st = c.get('scoring_targets', {})
    if not isinstance(st.get('acceptable_resolutions'), list):
        errors.append(f'{c[\"case_id\"]} missing acceptable_resolutions list')
print(f'{len(errors)} errors in {len(cases)} cases' if errors else f'All {len(cases)} valid')
from collections import Counter
cats = Counter(c['category'] for c in cases)
print('By category:', dict(cats))
"
```

### 2.4 Check defense case ground truth
Per v6 lesson L7: defense cases must have `correct_position = "defense_wins"`. Verify:
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
cases = json.load(open('benchmark_cases_v7_raw.json'))
defense = [c for c in cases if c['category'] == 'defense']
wrong = [c['case_id'] for c in defense if c['correct_position'] != 'defense_wins']
print(f'Defense cases: {len(defense)}, wrong correct_position: {len(wrong)}')
"
```

### 2.5 Generate sanitized case file (no ground truth)
Strip ground-truth fields from all cases before passing to Phase 5 benchmark runner.
`select_cases.py` also performs stratified selection (160 regular / 80 mixed / 40 defense):
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/select_cases.py \
  --pool benchmark_cases_v7_raw.json \
  --output v7_cases_sanitized.json \
  --sanitize
```
`v7_cases_sanitized.json` is the input to `pipeline/phase5_benchmark.py` (Phase 5).

---

## Verification
- [ ] 280 cases total: 160 regular, 80 mixed, 40 defense
- [ ] All Schema B required fields present in `benchmark_cases_v7_raw.json`
- [ ] All defense cases have `correct_position = "defense_wins"`
- [ ] `v7_cases_sanitized.json` contains no ground truth fields (`must_find`, `acceptable_resolutions`, `correct_position`)

## Outputs
- `benchmark_cases_v7_raw.json` — full cases with ground truth
- `v7_cases_sanitized.json` — stripped cases for benchmark runner

## Gate
`benchmark_cases_v7_raw.json` passes Schema B validation. 280 cases in correct stratum counts (160 regular / 80 mixed / 40 defense). `v7_cases_sanitized.json` has no ground truth leakage.
