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

**FAIL — 3 gaps identified. Non-blocking for Phase 5; must be resolved before Phase 7.**

### Gap 1: Ensemble per-assessor scoring data absent from raw outputs

**Problem:** `phase5_benchmark.py` ensemble_3x outputs include `assessor_results`
(per-assessor `issues_raised`, `verdict`, `critic_raw`) but do not include
`found_booleans` — the per-assessor issue-matching data needed for union IDR.

**Impact:** `compute_ensemble_union_idr()` (v7_scoring.py:422-432) requires
`found_booleans` per assessor. Without it, P1 and H4 cannot use union IDR on
ensemble_3x outputs.

**Remediation:** This is a Phase 6 responsibility, not Phase 5. Phase 6 cross-vendor
scoring (gpt-5.4-mini) will produce per-assessor `found_booleans` as part of the
IDR/IDP rescoring step. The raw output from Phase 5 provides the input
(`assessor_results[].issues_raised`) that Phase 6 scores against ground truth.

**Status:** Non-blocking for Phase 5 launch. Implement in Phase 6 scoring pipeline.

### Gap 2: `compute_ensemble_union_idr()` not invoked in analysis mode

**Problem:** The function exists (v7_scoring.py:422-432) but is never called in
`run_analysis()`. Line 715 only extracts top-level `idr_documented` from rescored
data; ensemble assessor-level breakdowns are not processed.

**Impact:** Without invocation, ensemble_3x IDR defaults to top-level scoring rather
than union pooling.

**Remediation:** Wire `compute_ensemble_union_idr()` into the analysis pipeline during
Phase 7 analysis setup. The function is correct; it just needs to be called when
`condition == "ensemble_3x"` with per-assessor rescored data from Phase 6.

**Status:** Non-blocking for Phase 5. Fix in Phase 7 analysis prep.

### Gap 3: H5 issue-classification data structure not yet defined

**Problem:** `test_h5()` (v7_scoring.py:629) is called with an empty dict as input.
The per-case issue classification (planted_match | valid_novel | false_claim |
spurious with support tiers) is not produced by any existing pipeline step.

**Impact:** H5 precision parity test cannot run without this data.

**Remediation:** Phase 6 cross-vendor scoring must produce a `per_case_issue_map`
with deduplicated issues, classifications, and `raised_by` tier counts. This is the
single gpt-5.4-mini call per ensemble_3x case described in HYPOTHESIS.md.

**Status:** Non-blocking for Phase 5. Implement in Phase 6 scoring pipeline alongside
IDR/IDP rescoring.

---

## Summary

| Category | Status | Notes |
|----------|--------|-------|
| A. Hypothesis <-> Scoring | PASS | All 7 tests present, bounds correct, bootstrap configured |
| B. Dimensions <-> Conditions | PASS | 4 dimensions, ETD absent, defense exclusion correct |
| C. Dispatch <-> Conditions | PASS | 4 conditions, API counts match, mixed injection works |
| D. Output <-> Scoring | FAIL | 3 gaps — all Phase 6/7 scope, non-blocking for Phase 5 |

**Gate verdict:** Phase 5 may proceed. Category D gaps are Phase 6/7 implementation
items — the raw data Phase 5 produces is sufficient input for Phase 6 to generate
the missing scoring artifacts.
