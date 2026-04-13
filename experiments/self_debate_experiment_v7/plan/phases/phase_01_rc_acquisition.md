# Phase 1 — RC Data Acquisition

> **Reminders:** `uv run` only. CWD: repo root. `cd experiments/self_debate_experiment_v7 &&` prefix.

## Required Reading
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--280) — case targets + defense case sourcing decision
- [v6_lessons.md L5](../references/v6_lessons.md) — cross-vendor scoring requirement

---

## Steps

### 1.1 Copy and update RC extractor
```bash
cp experiments/self_debate_experiment_v6/pipeline/rc_extractor.py \
   experiments/self_debate_experiment_v7/pipeline/rc_extractor.py
```
Update target: `--target-count 40` (was 30 in v6; aim for 30–40).

### 1.2 Run RC extraction
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/rc_extractor.py --output rc_cases_raw.json --target-count 40
```

### 1.3 Apply yield decision table

| RC yield | Action |
|---|---|
| regular ≥ 80, mixed ≥ 30, defense ≥ 10 | Use RC for all strata |
| regular ≥ 80, mixed ≥ 30, defense < 10 | Supplement defense with synthetic no-flaw cases |
| regular ≥ 60, mixed < 30 | Supplement mixed with synthetic pipeline |
| regular < 60 | Supplement regular with synthetic; lower ceiling target (0.75→0.70) |

### 1.4 Defense case decision
If RC yield for defense cases is insufficient (< 10 valid exoneration cases):
- Generate synthetic cases with `correct_position = "defense_wins"` (no planted flaws)
  to reach the 40-case defense target
- Validate manually: confirm each case has no identifiable methodological flaw
- Add `is_synthetic_defense: true` flag for subgroup analysis

### 1.5 Report yield
Write `DATA_ACQUISITION.md` in v7 experiment root:
- Total RC papers retrieved
- Breakdown by stratum (regular / mixed / defense)
- Pipeline path taken (RC-only vs supplemented)
- Date of extraction

---

## Verification
- [ ] `rc_cases_raw.json` exists and is parseable
- [ ] Yield decision table applied and path recorded in `DATA_ACQUISITION.md`
- [ ] Defense case source decided (RC or synthetic)

## Outputs
- `rc_cases_raw.json`
- `DATA_ACQUISITION.md`

## Gate
`rc_cases_raw.json` exists. Yield decision documented. Defense case source confirmed.
