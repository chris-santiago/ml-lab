# Haiku Smoke Test — Real Paper Cases V4 (Batch3, Lever A+B)

**Date:** 2026-04-07
**Model:** claude-haiku-4-5
**Case source:** `synthetic-candidates/real_paper_cases_batch3.json` (eval_scenario_301–314, 14 cases)
**Rubric:** 4-dimension proxy (IDR, IDP, FVC, IDJ) per `HAIKU_SMOKE_TEST_INSTRUCTIONS.md`
**Purpose:** Post-generation-round smoke test on batch3 cases re-generated with Lever A + Lever B. Determines whether the generation prompt changes produce adequate calibration headroom.

---

## Dispatch Protocol

- Single pass, no role prefix, no structure
- Generic methodology-review wrapper: "You are reviewing an ML methodology report. Please evaluate the soundness of the methodology described below, identify any significant methodological concerns, and provide an overall assessment of whether the work supports the stated conclusions."
- Task prompt only shown; no scoring_targets, ground_truth, planted_issues, or answer-key fields

---

## Scored Results

| Case ID | IDR | IDP | FVC | IDJ | Mean | Stratum | Notes |
|---------|:---:|:---:|:---:|:---:|:----:|---------|-------|
| eval_scenario_301 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: recommended shadow trial (empirical_test_agreed); IDJ=1: challenged "fairest business comparison" framing — correctly argued it conflates business viability with methodological superiority |
| eval_scenario_302 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: "refinement request, not a rejection; warrants a shadow pilot"; IDJ=1: challenged "window-level randomization is representative" — correctly argued representativeness ≠ independence |
| eval_scenario_303 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: requested additional direct validation rather than rejecting; IDJ=1: identified category error in "removal most harms retraining performance = faithful" |
| eval_scenario_304 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: "conditional approval... required prospective evaluation"; IDJ=1: "you can train on clean cases and still evaluate on realistic ones — the memo skips this step" |
| eval_scenario_305 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: "do not deploy without a post-redesign forward test"; IDJ=1: "retraining absorbs drift confuses data availability with stationarity" |
| eval_scenario_306 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: prospective validation on unverified segments recommended; IDJ=1: inverted "conservative AUROC" claim — "higher label quality in a biased sample makes AUROC inapplicable, not conservative" |
| eval_scenario_307 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: "deployment decision should rest on fresh-set performance + gap analysis"; IDJ=1: "the issue is not whether smaller sets are noisy; it is that years of iterative improvement..." |
| eval_scenario_308 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: approved limited physical-world testing of selected artifact; IDJ=1: "'only one policy ships' does not settle recipe reliability" |
| eval_scenario_309 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; FVC=1: "request corrected evaluation before operational deployment"; IDJ=1: "intent does not prevent information leakage — screening is still label-aware regardless of stated purpose" |
| eval_scenario_310 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended stratified destructive audit; no must_not_claim violations |
| eval_scenario_311 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended abstention-as-safety-design; no must_not_claim violations |
| eval_scenario_312 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended single-airport local calibration; no must_not_claim violations |
| eval_scenario_313 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended chemistry-strip features as lawful pre-decision inputs; no must_not_claim violations |
| eval_scenario_314 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended worst-decade recall and uncertainty routing; no must_not_claim violations |

---

## Phase 5.5 Gate Assessment

**Gate criterion (adapted for 14-case batch):** ≥9/14 cases must score mean < 0.55

| Metric | Value |
|--------|-------|
| Cases scoring < 0.55 | **0 / 14** |
| Overall mean | **1.000** |
| Gate result | **FAIL** |

---

## Stratum Diagnostic

> **Note on stratum composition:** All 9 critique-position cases in batch3 use `acceptable_resolutions: ['empirical_test_agreed']` only (Lever A applied). There are therefore zero pure_critique cases in this batch; all critique-position cases fall into the mixed stratum.

| Stratum | N cases | N below 0.55 | Mean score |
|---------|:-------:|:------------:|:----------:|
| Pure critique | 0 | — | N/A |
| Mixed (301–309) | 9 | 0 | 1.000 |
| Defense_wins (310–314) | 5 | 0 | 1.000 |
| **All** | **14** | **0** | **1.000** |

---

## Comparison to Prior Runs

| Metric | V3 (2xx, 4-dim) | V4 (3xx batch3, Lever A+B) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | 1.000 | 1.000 | 0 |
| Critique/mixed mean | 1.000 | 1.000 | 0 |
| Defense_wins mean | 1.000 | 1.000 | 0 |
| Cases scoring < 0.55 | 0 / 14 | 0 / 14 | 0 |
| Gate result | FAIL | FAIL | — |
| IDJ=1 on eligible cases | 9 / 9 | 9 / 9 | 0 |
| Lever A FVC=0 events | — | **0 / 9** | — |
| Lever B IDP=0 events | — | **0 / 9** | — |

---

## Key Findings

### 1. Lever A did not create calibration headroom — mechanism diagnosis

Lever A required all hard critique/mixed cases to use `acceptable_resolutions: ['empirical_test_agreed']` only, with the expectation that Haiku would sometimes over-claim `critique_wins` (outright rejection), triggering FVC=0.

**What actually happened:** Haiku correctly recommended empirical testing on all 9 mixed cases. Responses consistently concluded with shadow pilot / prospective validation / corrected evaluation language — all consistent with `empirical_test_agreed`. FVC=1 on all 9.

**Root cause — case text signals the correct resolution:** The batch3 prompts follow a narrative structure that preemptively defuses the `must_not_claim` items by explicitly stating why those concerns are wrong ("A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..."), then presents the real issues and concludes with hedge language explicitly framing the result as warranting further empirical testing ("the practical launch decision may still warrant a shadow trial, but the memo has not yet established..."). This narrative structure serves as a study guide that leads a competent reviewer directly to `empirical_test_agreed`. Haiku reads the correct resolution from the case text rather than being forced to reason independently about verdict type.

**Implication:** Lever A can only fire FVC=0 if Haiku confidently judges the methodology too broken for any empirical test to rescue it. The case text as written does not create that scenario — every case includes language that hedges toward "suggestive but incomplete" rather than "broken."

### 2. Lever B did not create IDP=0 events

Lever B required at least one domain-specific false-alarm `must_not_claim` per case — a concern that sounds plausible under general ML knowledge but is wrong given field-specific convention, with the expectation that Haiku might claim it.

**What actually happened:** Zero must_not_claim violations across all 9 critique/mixed cases. Haiku correctly avoided all domain-specific false alarms in every case.

**Root cause — same case text structure:** The prompts pre-emptively explain why the false-alarm concern is wrong (e.g., for case 301: "A pattern-matching reviewer could stop here and complain that AUROC should not be reported on such a rare-event task, yet in this domain threshold-independent ranking metrics are standard..."). By explicitly labeling the must_not_claim item as a naive-reviewer mistake and explaining the domain-specific reason it is wrong, the prompts prevent Haiku from making that error.

### 3. IDJ remains at ceiling — abi justifications still not subtle enough

IDJ=1 on all 9 eligible cases. Haiku correctly identified and challenged the planted wrong justification in every case. Same result as V3.

**Implication:** The addressed_but_incorrectly justifications in batch3 are sufficiently explicit that Haiku recognizes them as wrong without difficulty. IDJ creates a valid dimension in the scoring engine but adds no difficulty at the proxy rubric level with these cases.

### 4. Defense_wins: stochastic pass — third time

All 5 defense_wins cases scored 1.00 (Haiku correctly defended all methodologies). This matches V3 defense_wins behavior (also all passed) and contradicts V2 (cases 206–209 scored 0.33 because Haiku invented flaws). The V2 defense_wins calibration (mean=0.467) remains the operative baseline. The V3 and V4 passes are stochastic rolls, not a trend.

---

## Root Cause Summary: Why Both Levers Failed

The Lever A and B design assumed Haiku would:
- Sometimes over-claim `critique_wins` on mixed cases (Lever A target)
- Sometimes claim domain-specific false alarms (Lever B target)

But the batch3 case prompts are written in a "debate memo" format that:
1. **Pre-emptively defuses each `must_not_claim` item** by labeling it as a naive mistake and explaining the domain-specific reason it is wrong
2. **Pre-emptively signals the correct verdict** by framing the genuine issues as "suggest a shadow trial rather than disqualifying" and hedging toward `empirical_test_agreed`

This structure makes the cases self-scoring: Haiku does not need domain expertise or deep reasoning to reach IDR=1, IDP=1, FVC=1, IDJ=1 — the text itself provides the answer.

**The generation prompt needs a structural change (Lever C):** Case prompts should NOT pre-emptively explain why the must_not_claim items are wrong. They should present the distractors as plausible, unlabeled concerns alongside the real issues, forcing the evaluating model to reason independently about which concerns are valid. Similarly, the case text should NOT hedge toward `empirical_test_agreed` in the final paragraph — it should present the flaws and let the evaluating model reach its own verdict conclusion.

---

## What Remains

- [ ] User revises `REAL_PAPER_CASE_GENERATION_PROMPT.md` to address the case text structure problem (Lever C: remove pre-emptive defusing of false-alarm concerns; remove explicit empirical-test hedging in conclusion paragraph)
- [ ] Re-generate `synthetic-candidates/real_paper_cases.json` (14 cases) via non-Anthropic LLM using revised prompt
- [ ] Run smoke test V5 on new cases using 4-dim proxy rubric
- [ ] Verify gate passes (≥9/14 cases score mean < 0.55)
- [ ] If gate passes → user re-generates `openai_benchmark_cases.json` (50 cases) using parallel Lever C fix
- [ ] Run smoke test on benchmark cases
- [ ] If both gates pass → proceed to Phase 0
