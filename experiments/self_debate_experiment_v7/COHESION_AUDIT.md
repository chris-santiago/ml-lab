# v7 Coherence Audit

> Phase 4 mandatory gate (resolves issue 5273d436).
> Alignment check across: `HYPOTHESIS.md`, `pipeline/v7_scoring.py`, `pipeline/phase5_benchmark.py`.

---

## A. Hypothesis <-> Scoring Code

**PASS**

| Check | Status | Location |
|-------|--------|----------|
| P1 test function exists | OK | v7_scoring.py:519 `test_p1` |
| P2 test function exists | OK | v7_scoring.py:536 `test_p2` |
| H1a test function exists | OK | v7_scoring.py:553 `test_h1a` |
| H2 test function exists | OK | v7_scoring.py:572 `test_h2` |
| H3 test function exists | OK | v7_scoring.py:595 `test_h3` |
| H4 test function exists | OK | v7_scoring.py:612 `test_h4` |
| H5 test function exists | OK | v7_scoring.py:629 `test_h5` |
| H1a equivalence bound = 0.015 | OK | v7_scoring.py:565 |
| H5 equivalence bound = 0.03 | OK | v7_scoring.py:645 |
| Bootstrap n = 10,000 | OK | v7_scoring.py:440,477 |
| Bootstrap seed = 42 | OK | v7_scoring.py:441,478 |
| Regular subset filter (n=160) | OK | category == "regular" filtering in test functions |
| Mixed subset filter (n=80) | OK | category == "mixed" filtering in test functions |

---

## B. Scoring Dimensions <-> Conditions

**PASS**

| Check | Status | Location |
|-------|--------|----------|
| ETD absent from DIMENSIONS | OK | v7_scoring.py:94 `FAIR_COMPARISON_DIMS = ["IDR", "IDP", "DRQ", "FVC"]` |
| FC = mean(IDR, IDP, DRQ, FVC) | OK | v7_scoring.py:417-419 `compute_fc()` |
| FVC_mixed filters category == "mixed" | OK | v7_scoring.py:735,752-754 |
| Defense cases: IDR/IDP set to None | OK | v7_scoring.py:711-712,719-720 |
| FC defense = mean(DRQ, FVC) | OK | Follows from IDR/IDP = None in compute_fc() |

---

## C. Dispatch Logic <-> Conditions List

**PASS**

| Check | Status | Location |
|-------|--------|----------|
| ALL_CONDITIONS = 4 conditions | OK | phase5_benchmark.py:58 |
| baseline = 1 API call (critic) | OK | phase5_benchmark.py:221-245 |
| isolated_debate = 3 API calls | OK | phase5_benchmark.py:248-282 |
| ensemble_3x = 3 API calls | OK | phase5_benchmark.py:285-338 |
| multiround_2r = 3 API calls | OK | phase5_benchmark.py:341-382 |
| Mixed-case injection to adjudicator | OK | phase5_benchmark.py:61-65,419-421 |

---

## D. Output Schema <-> Scoring Input

**PASS (after remediation) — 3 gaps identified and resolved.**

### Gap 1: Ensemble per-assessor scoring data absent from raw outputs

**Problem:** `phase5_benchmark.py` ensemble_3x outputs include `assessor_results`
(per-assessor `issues_raised`, `verdict`, `critic_raw`) but do not include
`found_booleans` — the per-assessor issue-matching data needed for union IDR.

**Resolution:** This is correctly Phase 6 scope. Phase 5 produces raw
`assessor_results[].issues_raised`; Phase 6 cross-vendor scoring (gpt-5.4-mini)
will produce per-assessor `found_booleans` as `per_assessor_rescored` in the
rescored data file. No Phase 5 change needed.

**Status:** Resolved by design. Phase 6 produces the data.

### Gap 2: `compute_ensemble_union_idr()` not invoked in analysis mode

**Problem:** The function existed but was never called in `run_analysis()`.

**Resolution:** Wired `compute_ensemble_union_idr()` into the IDR scoring branch
of `run_analysis()`. When `condition == "ensemble_3x"` and `per_assessor_rescored`
is present in the rescored data, union IDR is computed instead of top-level IDR.
Falls back to `idr_documented` or `compute_idr()` when per-assessor data is absent.

**Status:** FIXED in v7_scoring.py.

### Gap 3: H5 issue-classification data structure not defined

**Problem:** `test_h5()` was called with an empty dict. No data collection logic.

**Resolution:** Added H5 data collection in the scoring loop: for ensemble_3x
regular cases, extracts `tier_precisions` from Phase 6 `per_case_issue_map` in
rescored data. Collects per-case 1/3 and 3/3 precision values and passes them
to `test_h5()`. Returns INCONCLUSIVE when Phase 6 data is not yet available
(graceful degradation).

**Status:** FIXED in v7_scoring.py. Will produce results once Phase 6 data exists.

---

## Summary

| Category | Status | Notes |
|----------|--------|-------|
| A. Hypothesis <-> Scoring | PASS | All 7 tests present, bounds correct, bootstrap configured |
| B. Dimensions <-> Conditions | PASS | 4 dimensions, ETD absent, defense exclusion correct |
| C. Dispatch <-> Conditions | PASS | 4 conditions, API counts match, mixed injection works |
| D. Output <-> Scoring | PASS (remediated) | 3 gaps found and resolved: union IDR wired, H5 data collection added, Phase 6 data flow confirmed |

**Gate verdict:** All 4 categories pass. Phase 5 may proceed.
