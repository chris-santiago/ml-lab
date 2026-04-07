# Calibration Changes Summary

**Date:** 2026-04-07
**Source:** `CALIBRATION_DIAGNOSTIC.md` Section 12 implementation checklist
**Tracks:** All pre-Phase-0 changes (no generation round required)

---

## What Was Done

### 1. Directory organization

Moved 4 diagnostic artifacts from the v5 experiment root into `diagnostics/`:
- `REAL_PAPER_CASES_SMOKE_TEST.md` — V1 Haiku smoke test (1xx cases)
- `REAL_PAPER_CASES_SMOKE_TEST_V2.md` — V2 Haiku smoke test (2xx cases)
- `CALIBRATION_DIAGNOSTIC.md` — Full diagnostic memo
- `V5_PLAN_REVISION_SUMMARY.md` — v4→v5 rename changelog

Created two new documents in `diagnostics/`:
- `HAIKU_SMOKE_TEST_INSTRUCTIONS.md` — Reusable procedure for running Haiku ceiling checks
- This file (`CALIBRATION_CHANGES_SUMMARY.md`)

### 2–6. Five file edits: IDJ dimension added across scoring engine, phase files, and pre-registration

---

## Per-File Changes

### `plan/scripts/self_debate_poc.py`

| Location | Before | After |
|----------|--------|-------|
| Module docstring | `Fair-comparison lift (IDR/IDP/DRQ/FVC)` | `Fair-comparison lift (IDR/IDP/IDJ/DRQ/FVC)` |
| `FAIR_COMPARISON_DIMS` | `['IDR', 'IDP', 'DRQ', 'FVC']` | `['IDR', 'IDP', 'IDJ', 'DRQ', 'FVC']` |
| `PRIMARY_SCORING_DIMS` | `['IDR', 'IDP', 'DRQ', 'ETD', 'FVC']` | `['IDR', 'IDP', 'IDJ', 'DRQ', 'ETD', 'FVC']` |
| New function | *(absent)* | `compute_idj(must_find_ids, addressed_but_incorrectly_ids, justifications_challenged)` added after `compute_idp` |
| `score_run()` extractions | No `addressed_but_incorrectly_ids` or `justifications_challenged` | Both extracted; `scores['IDJ'] = compute_idj(...)` added |
| Comment line 296 | `(IDR/IDP/DRQ/FVC only)` | `(IDR/IDP/IDJ/DRQ/FVC only)` |
| `fair_comparison_mean` docstring | `(IDR, IDP, DRQ, FVC)` | `(IDR, IDP, IDJ, DRQ, FVC)` |
| Print summary | `IDR/IDP/DRQ/FVC` | `IDR/IDP/IDJ/DRQ/FVC` |

### `plan/phases/phase_06_benchmark_run.md`

| Location | Change |
|----------|--------|
| Extraction instructions | Added bullet: extract `justifications_challenged` |
| Output JSON schema | Added `"justifications_challenged": [...]` field |
| POST-WRITE VALIDATION required keys | Added `justifications_challenged` |

### `plan/phases/phase_05_5_difficulty_gate.md`

| Location | Change |
|----------|--------|
| Inline proxy dimensions | Added IDJ as 4th dimension with N/A rule |
| Per-case mean formula | Updated to "applicable scores (IDR, IDP, FVC, IDJ where applicable)" |
| After gate pass logging | Added non-blocking stratum diagnostic table + logging step |

### `plan/phases/phase_02_hypothesis.md`

| Location | Before | After |
|----------|--------|-------|
| Fair-comparison dimensions | `(IDR, IDP, DRQ, FVC)` | `(IDR, IDP, IDJ, DRQ, FVC)` |
| Primary metrics | `IDR, IDP, DRQ, FVC (fair-comparison set)` | `IDR, IDP, IDJ, DRQ, FVC (fair-comparison set)` |
| Secondary hypothesis (1) | `IDR/IDP/DRQ/FVC` | `IDR/IDP/IDJ/DRQ/FVC` |
| After secondary hypotheses | *(absent)* | Pre-registered stratum analysis block added |

### `plan/scripts/write_preregistration.py`

| Location | Change |
|----------|--------|
| `primary_fair_comparison_lift.dimensions` | Added `"IDJ"` |
| `primary_fair_comparison_lift.note` | Added IDJ rationale |
| `hypotheses` dict | Added `stratum_fc_lift` entry |
| `rubric` dict | Added IDJ entry |
| `secondary_ensemble_mixed.claim` | Updated dims to include IDJ |
| `comparison_structures.debate_vs_ensemble.dimensions` | Added IDJ |
| `comparison_structures.debate_conditions_vs_each_other.dimensions` | Added IDJ |
| `rubric.scoring_dimensions` | Added IDJ entry |
| `per_case_pass_criterion` | Updated dims to `IDR/IDP/IDJ/DRQ/ETD/FVC` |
| `pass_fail_rule` | Updated dims to `IDR/IDP/IDJ/DRQ/ETD/FVC` |

---

## Traceability

All changes implement `CALIBRATION_DIAGNOSTIC.md` Section 12, "Before Phase 0 (no generation round required)":

| Checklist item | Status |
|----------------|--------|
| `plan/scripts/self_debate_poc.py` — add `compute_idj()`, IDJ to dims, update `score_run()` | ✅ Done |
| `plan/phases/phase_06_benchmark_run.md` — add `justifications_challenged` to schema + validation | ✅ Done |
| `plan/phases/phase_05_5_difficulty_gate.md` — IDJ proxy dimension + stratum diagnostic | ✅ Done |
| `plan/phases/phase_02_hypothesis.md` — IDJ in dims + stratum pre-registration | ✅ Done |
| `plan/scripts/write_preregistration.py` — IDJ in rubric/dims + `stratum_fc_lift` hypothesis | ✅ Done |

---

## What Remains (Generation Round Required)

These checklist items require re-generating cases through a non-Anthropic LLM and are not yet done:

- [ ] `synthetic-candidates/benchmark_case_generation_prompt.md` — add Lever A (`acceptable_resolutions: ['empirical_test_agreed']`) and Lever B (domain-specific false-alarm decoys)
- [ ] `synthetic-candidates/REAL_PAPER_CASE_GENERATION_PROMPT.md` — parallel Lever A + B updates
- [ ] Re-generate `synthetic-candidates/openai_benchmark_cases.json` (50 cases) via non-Anthropic LLM
- [ ] Re-generate `synthetic-candidates/real_paper_cases.json` (14 cases) via non-Anthropic LLM
- [ ] Re-run Haiku smoke test using updated 4-dim proxy rubric (IDR/IDP/FVC/IDJ); verify gate passes (≥6/10 hard cases < 0.55)
- [ ] Proceed to Phase 0 after gate passes

**Expected outcome after generation round:** Critique/mixed case baseline drops from ~1.000 to ~0.500 (Lever A forces DRQ=0.5/FVC=0.5 on overclaimed critique_wins verdicts; Lever B induces false alarms that depress IDP; IDJ=0 when model accepts wrong justification). Phase 5.5 gate projects ~13/14 cases below 0.55 — passes comfortably. See `CALIBRATION_DIAGNOSTIC.md` Section 10 for projected score table.
