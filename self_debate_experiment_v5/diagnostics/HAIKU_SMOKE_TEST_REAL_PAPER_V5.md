# Haiku Smoke Test — Real Paper Cases V5 (Batch3, Evaluative Paragraphs Removed)

**Date:** 2026-04-07
**Model:** claude-haiku-4-5
**Case source:** `synthetic-candidates/real_paper_cases_batch3.json` (eval_scenario_301–314, 14 cases)
**Rubric:** 4-dimension proxy (IDR, IDP, FVC, IDJ) per `HAIKU_SMOKE_TEST_INSTRUCTIONS.md`
**Purpose:** Post-surgical-edit smoke test. The evaluative analysis paragraphs were removed from all 9 critique/mixed task_prompts (see `CASE_FORMAT_DIAGNOSTIC.md` — Corrective Action Applied). Determines whether removing the outside-reviewer paragraphs creates calibration headroom.

---

## Dispatch Protocol

- Single pass, no role prefix, no structure
- Generic methodology-review wrapper: "You are reviewing an ML methodology report. Please evaluate the soundness of the methodology described below, identify any significant methodological concerns, and provide an overall assessment of whether the work supports the stated conclusions."
- Task prompt only shown; no scoring_targets, ground_truth, planted_issues, or answer-key fields

---

## Scored Results

| Case ID | IDR | IDP | FVC | IDJ | Mean | Stratum | Notes |
|---------|:---:|:---:|:---:|:---:|:----:|---------|-------|
| eval_scenario_301 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find surfaced; SMOTE-before-fold-split mechanism correctly named; IDJ correctly challenged "training corpus" justification |
| eval_scenario_302 | 0 | 1 | 1 | 1 | **0.75** | mixed | IDR MISS: compound issue `window_overlap_and_tuned_challenger_jointly_inflate_gain` not surfaced as a linked effect — components addressed separately; IDP/FVC/IDJ correct |
| eval_scenario_303 | 1 | 1 | 1 | 1 | **1.00** | mixed | "Faithfulness vs. usefulness" distinction correctly identified; IDJ correctly challenged retrain-degradation-as-faithfulness claim |
| eval_scenario_304 | 1 | 1 | 1 | 1 | **1.00** | mixed | Spectrum bias identified; "reliable ground truth first" argument challenged as circular; scope-dataset gap surfaced |
| eval_scenario_305 | 1 | 1 | 1 | 1 | **1.00** | mixed | App-redesign feature drift identified; fixed-target-harmless claim correctly challenged |
| eval_scenario_306 | 1 | 1 | 1 | 1 | **1.00** | mixed | Verification bias named; "clean labels = conservative AUROC" claim directly refuted; network-wide scope mismatch identified |
| eval_scenario_307 | 1 | 1 | 1 | 1 | **1.00** | mixed | Benchmark overuse mechanism named; "small set + preserved ranking" dismissal challenged |
| eval_scenario_308 | 1 | 1 | 1 | 1 | **1.00** | mixed | Best-seed reporting problem named; recipe vs. artifact scope distinction drawn |
| eval_scenario_309 | 1 | 1 | 1 | 1 | **1.00** | mixed | Label-aware screening before CV identified; "noise removal = honest CV" claim challenged |
| eval_scenario_310 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | Correctly defended stratified audit; no invented flaws |
| eval_scenario_311 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | Correctly defended scoped automation; abstention framed as safety design |
| eval_scenario_312 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | Correctly defended single-airport validation |
| eval_scenario_313 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | Correctly defended pre-clearance chemistry features as non-leakage |
| eval_scenario_314 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | Correctly defended worst-group recall and uncertainty routing |

---

## Phase 5.5 Gate Assessment

**Gate criterion (adapted for 14-case batch):** ≥9/14 cases must score mean < 0.55

| Metric | Value |
|--------|-------|
| Cases scoring < 0.55 | **0 / 14** |
| Overall mean | **0.982** |
| Gate result | **FAIL** |

---

## Stratum Diagnostic

| Stratum | N cases | N below 0.55 | Mean score |
|---------|:-------:|:------------:|:----------:|
| Pure critique | 0 | — | N/A |
| Mixed (301–309) | 9 | 0 | 0.972 |
| Defense_wins (310–314) | 5 | 0 | 1.000 |
| **All** | **14** | **0** | **0.982** |

---

## Comparison to V4

| Metric | V4 (batch3, Lever A+B) | V5 (batch3, paragraphs removed) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | 1.000 | 0.982 | −0.018 |
| Critique/mixed mean | 1.000 | 0.972 | −0.028 |
| Defense_wins mean | 1.000 | 1.000 | 0 |
| Cases scoring < 0.55 | 0 / 14 | 0 / 14 | 0 |
| Gate result | FAIL | FAIL | — |

---

## Key Finding

Removing the evaluative analysis paragraphs from the task_prompts produced no meaningful calibration improvement. The only movement was case 302 dropping to 0.75 due to a compound-issue IDR miss — a single case, insufficient to affect the gate.

**Root cause update:** Fixing the format (team voice vs. reviewer voice) is necessary but not sufficient. Even in advocacy-style text, the flaw mechanisms are surface-readable by Haiku without multi-step inference or domain expertise. The cases are harder to write correctly, but the underlying issues (data leakage, benchmark overfit, verification bias, etc.) remain identifiable from well-written memo text alone.

The difficulty problem is deeper than format: these issue types are well-known ML failure modes that Haiku recognizes on description alone. Making cases genuinely hard for Haiku would require flaws that depend on domain-specific knowledge Haiku lacks, or multi-step causal chains that are not surface-readable from the methodology description.

**This is an open problem.** No next step is prescribed here — requires user input on case design direction.
