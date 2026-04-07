# Haiku Smoke Test — Procedure and Scoring Instructions

**Version:** v5 (4-dimension proxy rubric including IDJ)
**Purpose:** Reusable reference for running the pre-experiment Haiku ceiling check on any case batch.

---

## Purpose

Before running Phase 5.5 or Phase 6, verify that the case batch is appropriately difficult for `claude-haiku-4-5` (the acceptance criterion model). If Haiku scores too high on hard cases in a single unstructured pass, there is no headroom for the debate protocol to demonstrate improvement.

This smoke test is an **ephemeral diagnostic** — results are recorded in a markdown artifact but no INVESTIGATION_LOG entries are written, no `benchmark_cases.json` is modified, and no `v5_raw_outputs/` files are created.

---

## Prerequisites

A case JSON file (e.g., `synthetic-candidates/real_paper_cases.json` or `synthetic-candidates/openai_benchmark_cases.json`) with the following fields per case:
- `scoring_targets.must_find_issue_ids` — required issue IDs the model should find
- `scoring_targets.must_not_claim` — issue IDs the model should NOT raise (false alarms)
- `scoring_targets.acceptable_resolutions` — valid overall verdicts
- `ground_truth.correct_position` — `critique` or `defense`
- `planted_issues` — array of issue objects; check for `"addressed_but_incorrectly": true` to identify IDJ-eligible cases
- `ideal_debate_resolution.type` — for confirming defense_wins cases

---

## Model and Dispatch

- **Model:** `claude-haiku-4-5` — the acceptance criterion model for v5 hard case generation
- **Dispatch:** Single pass, no role prefix, no structure
- **Input:** `task_prompt` only + a generic methodology-review wrapper such as:

  > "You are reviewing an ML methodology report. Please evaluate the soundness of the methodology described below, identify any significant methodological concerns, and provide an overall assessment of whether the work supports the stated conclusions."

- **Do NOT show** to the model: `must_find_issue_ids`, `scoring_targets`, `ground_truth`, `planted_issues`, or any answer-key field

---

## Proxy Scoring Rubric (4 Dimensions)

Score each response on the following binary dimensions. All scores are 0 or 1 (or N/A).

| Dimension | Criterion | Defense_wins handling |
|-----------|-----------|----------------------|
| **IDR** | Did the response surface ALL `scoring_targets.must_find_issue_ids`? | IDR=1 automatically (must_find=[]) |
| **IDP** | Was at least one issue described with substantive correctness — correct mechanism, not just naming the concern? | IDP=1 if the response correctly avoids inventing fatal flaws that aren't there |
| **FVC** | Is the response's overall assessment (verdict or implied resolution) consistent with `scoring_targets.acceptable_resolutions`? | FVC=0 if model condemns methodology that should be defended |
| **IDJ** | For cases with `addressed_but_incorrectly` planted issues — did the response specifically argue that the memo's stated justification for that concern is wrong or insufficient? | IDJ=N/A (no addressed_but_incorrectly issues present) |

**Per-case mean** = sum of applicable scores / N_applicable
- Exclude N/A dimensions from the denominator
- IDJ is N/A for defense_wins cases (must_find=[]) and for any case where no planted_issue has `addressed_but_incorrectly: true`
- For cases with IDJ applicable: mean = (IDR + IDP + FVC + IDJ) / 4
- For cases without IDJ: mean = (IDR + IDP + FVC) / 3

**Important:** This is a proxy rubric using binary scoring. The actual experiment scoring engine (`plan/scripts/self_debate_poc.py`) uses fractional/tiered scoring (0.0/0.5/1.0) and additional dimensions (DRQ, ETD, DC). See `CALIBRATION_DIAGNOSTIC.md` Section 3 for the mismatch analysis and why these differ by design.

---

## Phase 5.5 Gate Criterion

Applied to the hard-case stratum only:
- **Pass:** ≥6/10 hard cases score mean < 0.55
- **Fail:** Fewer than 6 of 10 hard cases score mean < 0.55 — the batch is too easy for Haiku; cases need revision or re-generation

---

## Stratum Diagnostic

After scoring all cases, compute and report means broken down by stratum:

| Stratum | N cases | N below 0.55 | Mean score |
|---------|---------|-------------|------------|
| Pure critique | N | N | X.XX |
| Mixed | N | N | X.XX |
| Defense_wins | N | N | X.XX |
| **All** | **N** | **N** | **X.XX** |

Strata definitions:
- **Pure critique** — `ground_truth.correct_position == 'critique'` and `ideal_debate_resolution.type == 'critique_wins'`
- **Mixed** — `ground_truth.correct_position == 'critique'` and `ideal_debate_resolution.type == 'empirical_test_agreed'`
- **Defense_wins** — `ground_truth.correct_position == 'defense'`

---

## Results Table Template

```markdown
| Case ID | IDR | IDP | FVC | IDJ | Mean | Category | Notes |
|---------|:---:|:---:|:---:|:---:|:----:|----------|-------|
| eval_scenario_XXX | 1 | 1 | 1 | N/A | **1.00** | broken_baseline | ... |
| eval_scenario_XXX | 1 | 0 | 0 | N/A | **0.33** | defense_wins | FAIL: ... |
```

For IDJ-eligible cases, replace N/A with 0 or 1.

---

## Comparison Table Template

For tracking improvement across multiple smoke test iterations:

| Metric | V1 (batch) | V2 (batch) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | X.XXX | X.XXX | ±X.XXX |
| Critique/mixed mean | X.XXX | X.XXX | ±X.XXX |
| Defense_wins mean | X.XXX | X.XXX | ±X.XXX |
| Cases scoring < 0.55 | N/N (X%) | N/N (X%) | +N cases |

---

## Important Notes

1. **Ephemeral artifact** — This smoke test is not part of Phase 5.5. Do not write INVESTIGATION_LOG entries. Do not create or modify `benchmark_cases.json` or any `v5_raw_outputs/` file.

2. **Proxy vs. actual engine** — The binary scoring used here is deliberately simplified. In the actual engine:
   - IDR is fractional (proportion of must_find_ids found)
   - IDJ uses tiered thresholds: 0.9→1.0, 0.5→0.5, else→0.0
   - Defense_wins cases score 0.00 on DRQ+FVC when Haiku incorrectly condemns (not 0.33 as the proxy rubric shows — the proxy gives IDR=1 automatically, inflating the mean)
   - Mixed cases score 0.875 (not 1.00) when Haiku says `critique_wins` because DRQ=0.5 (adjacent verdict penalty)
   These differences mean proxy means are slightly higher than what the actual engine will compute on the same outputs.

3. **IDJ proxy is binary** — The actual `compute_idj()` uses fractional thresholds; the smoke test proxy uses a single binary question ("did the model challenge the justification?"). This means IDJ will appear more favorable in the proxy than in the actual engine for partial-challenge responses.

4. **File for results** — Name output artifacts: `diagnostics/HAIKU_SMOKE_TEST_<DESCRIPTOR>_V<N>.md` (e.g., `HAIKU_SMOKE_TEST_REAL_PAPER_V1.md`). Include date, model, case source file, and case IDs in the header.

---

## Prior Smoke Test Run History

| File | Date | Cases | Overall mean | Gate result |
|------|------|-------|:---:|---------|
| `REAL_PAPER_CASES_SMOKE_TEST.md` | 2026-04-07 | 101–114 (14 real-paper v1) | 0.952 | FAIL |
| `REAL_PAPER_CASES_SMOKE_TEST_V2.md` | 2026-04-07 | 201–214 (14 real-paper v2, 3-dim) | 0.810 | FAIL |
| `HAIKU_SMOKE_TEST_REAL_PAPER_V3_IDJ_BASELINE.md` | 2026-04-07 | 201–214 (existing 2xx, 4-dim with IDJ) | 1.000 | FAIL — IDJ=1 on all 9 eligible cases; Lever A+B needed |
| `HAIKU_SMOKE_TEST_REAL_PAPER_V4.md` | 2026-04-07 | 301–314 (batch3, Lever A+B, 4-dim) | 1.000 | FAIL — Lever A/B did not fire; case text structure pre-emptively defuses false alarms and signals empirical_test_agreed; Lever C needed |
| `HAIKU_SMOKE_TEST_REAL_PAPER_V5.md` | 2026-04-07 | 301–314 (batch3, evaluative paragraphs surgically removed) | 0.982 | FAIL — format fix insufficient; flaw mechanisms surface-readable in advocacy text; difficulty problem deeper than format |
