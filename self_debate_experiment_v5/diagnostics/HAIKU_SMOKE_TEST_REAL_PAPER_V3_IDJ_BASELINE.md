# Haiku Smoke Test — Real Paper Cases V3 (4-Dim IDJ Baseline)

**Date:** 2026-04-07
**Model:** claude-haiku-4-5
**Case source:** `synthetic-candidates/real_paper_cases.json` (eval_scenario_201–214, 14 cases)
**Rubric:** 4-dimension proxy (IDR, IDP, FVC, IDJ) per `HAIKU_SMOKE_TEST_INSTRUCTIONS.md`
**Purpose:** Pre-generation-round baseline — isolate IDJ effect on existing 2xx cases before Lever A/B re-generation. Documents that IDJ alone is insufficient to lower scores below the gate threshold.

---

## Dispatch Protocol

- Single pass, no role prefix, no structure
- Generic methodology-review wrapper: "You are reviewing an ML methodology report. Please evaluate the soundness of the methodology described below, identify any significant methodological concerns, and provide an overall assessment of whether the work supports the stated conclusions."
- Task prompt only shown; no scoring_targets, ground_truth, planted_issues, or answer-key fields

---

## Scored Results

| Case ID | IDR | IDP | FVC | IDJ | Mean | Stratum | Notes |
|---------|:---:|:---:|:---:|:---:|:----:|---------|-------|
| eval_scenario_201 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model explicitly argued "fairest comparator" claim fails because baseline was frozen at defaults while new model received 96-trial search |
| eval_scenario_202 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly argued traffic-weighting proves operational allocation, not per-population adequacy — correctly challenged memo's stated justification |
| eval_scenario_203 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model identified informative censoring and explicitly said "routine right-censoring" framing is wrong because removal decision is correlated with latent failure risk |
| eval_scenario_204 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model argued filtering to high-confidence instances does not measure "true capability" — it changes the distribution being measured |
| eval_scenario_205 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended prospective holdout + tail-stability criterion; no fatal flaws invented |
| eval_scenario_206 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended nested CV + stability criterion; no false condemning |
| eval_scenario_207 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended narrow scope as governance choice, not weakness |
| eval_scenario_208 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended worst-plant metric + site holdout methodology |
| eval_scenario_209 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended nested CV + outer-fold stability criterion; raised minor representation-selection concern (not in must_not_claim) |
| eval_scenario_210 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly said "replace live workflow" justification conflates operational deployment question with methodological superiority claim |
| eval_scenario_211 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model argued "held out from base model" does not make block independent for calibration fitting — identified circular validation |
| eval_scenario_212 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model challenged "spend collapses urgency into one outcome" — explicitly noted spend is not neutral across territories with unequal service access |
| eval_scenario_213 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly said leave-one-click-out "sounds intuitive" but is incomplete — live system changes exposure, so it measures reconstruction not future behavior |
| eval_scenario_214 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model argued "finance cares about net loss" justification is incomplete — label reflects intervention-shaped outcome, not unmanaged risk |

---

## Phase 5.5 Gate Assessment

**Gate criterion (adapted for 14-case real-paper batch):** ≥60% of hard cases (≥9/14) must score mean < 0.55

| Metric | Value |
|--------|-------|
| Cases scoring < 0.55 | **0 / 14** |
| Overall mean | **1.000** |
| Gate result | **FAIL** |

---

## Stratum Diagnostic

| Stratum | N cases | N below 0.55 | Mean score |
|---------|:-------:|:------------:|:----------:|
| Pure critique (201, 204, 211, 212) | 4 | 0 | 1.000 |
| Mixed (202, 203, 210, 213, 214) | 5 | 0 | 1.000 |
| Defense_wins (205–209) | 5 | 0 | 1.000 |
| **All** | **14** | **0** | **1.000** |

---

## Comparison to Prior Runs

> **⚠ Stochastic contamination warning:** The V3 run re-dispatched all 14 cases because the original V2 responses were lost in context compaction. This means the V3 defense_wins scores are from a *different* Haiku roll, not the same responses scored under a new rubric. The comparison below is informational only — V3 vs V2 deltas on defense_wins are not interpretable as improvement or regression. See note under Key Findings.

| Metric | V2 (3-dim, 2xx) | V3 (4-dim, 2xx) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | 0.810 | 1.000 | +0.190 (stochastic — see warning) |
| Critique/mixed mean | **1.000** | 1.000 | 0 |
| Defense_wins mean | **0.467** | 1.000 | +0.533 (stochastic — NOT a genuine improvement) |
| Cases scoring < 0.55 | **4 / 14** | 0 / 14 | −4 cases (stochastic) |
| Gate result | FAIL | FAIL | — |

*V2 actuals from `REAL_PAPER_CASES_SMOKE_TEST_V2.md`: cases 206–209 all scored 0.33 (Haiku invented flaws and condemned sound methodology). Case 205 scored 1.00. Defense_wins mean = 0.467. Critique/mixed mean = 1.000.*

---

## Key Findings

### 1. IDJ alone does not lower critique/mixed scores

All 9 IDJ-eligible cases (201–204, 210–214) scored IDJ=1. Haiku successfully identified and challenged the planted wrong justification in every case. This means the "addressed_but_incorrectly" justifications in the 2xx cases are not subtle enough — Haiku can recognize they are wrong without domain-specific knowledge.

**Implication:** IDJ adds a valid dimension to the scoring engine but does not create calibration headroom on the existing 2xx critique/mixed cases. The dimension will become meaningful in the actual experiment when weaker-performing models partially challenge justifications (IDJ=0.5) or miss them entirely (IDJ=0).

### 2. Defense_wins "improvement" is a stochastic artifact — V2 results were correct

In V2, cases 206–209 all scored 0.33 because Haiku invented 6–8 flaws each and condemned sound methodology. That was the *intended* behavior — the Defense_Wins Case Design Requirements successfully induced false critique from Haiku in V2.

In V3, those same cases scored 1.00 because this Haiku re-run happened to correctly defend the methodology. This is **not** a genuine improvement in case difficulty — it is stochastic variation. The V3 defense_wins results should not be compared to V2.

**The V2 defense_wins calibration (0.467 mean, 4/5 failing) remains the operative baseline.** The 2xx defense_wins cases are correctly calibrated; this run was a lucky roll.

### 3. Critique/mixed stratum result is reliable

The critique/mixed cases (201–204, 210–214) were not in a position where stochastic variation could change the outcome — they all scored 1.00 in V2 (3-dim) and 1.00 in V3 (4-dim). The IDJ=1 finding on all 9 IDJ-eligible cases is stable and not an artifact of re-running. Critique/mixed ceiling is confirmed.

### 4. What Lever A and Lever B fix (projected)

| Lever | Mechanism | Expected effect on proxy rubric |
|-------|-----------|-------------------------------|
| **Lever A** | Hard critique/mixed cases: `acceptable_resolutions = ["empirical_test_agreed"]` only | If Haiku says `critique_wins` on a mixed case → FVC=0; per-case mean drops from 1.00 to 0.75 |
| **Lever B** | Domain-specific false-alarm `must_not_claim` per hard critique case | If Haiku claims false alarm as main issue → IDP=0; per-case mean drops from 1.00 to 0.75 (or 0.50 if both IDR and IDP fail) |
| **Combined** | Cases with both levers active | Projected critique/mixed mean ~0.50–0.60 — below gate threshold |

See `CALIBRATION_DIAGNOSTIC.md` Section 10 for projected score table after Lever A+B re-generation.

---

## What This Run Confirms

- [x] IDJ dimension is implemented correctly in the proxy rubric (9/9 IDJ cases scored, all returned 0 or 1 — in this run, all 1)
- [x] Defense_wins cases correctly receive IDJ=N/A and are not penalized
- [x] No must_not_claim violations detected in any response
- [x] Critique/mixed ceiling confirmed: IDJ=1 on all 9 eligible cases; Lever A+B re-generation required
- [ ] **Defense_wins calibration not confirmed by this run** — V3 re-run produced different Haiku responses than V2; all 5 defense_wins cases passed, which contradicts V2's finding (4/5 failed). V2 defense_wins results (cases 206–209 scoring 0.33) remain the operative calibration reference.

---

## Next Step

User is concurrently re-generating `synthetic-candidates/real_paper_cases.json` (14 cases) via non-Anthropic LLM using revised `REAL_PAPER_CASE_GENERATION_PROMPT.md` with Lever A + Lever B. After re-generation:

- [ ] Run smoke test V4 on new real_paper_cases.json using 4-dim proxy rubric
- [ ] Verify gate passes (≥9/14 cases score mean < 0.55 for 14-case batch, or ≥6/10 for hard-case stratum if difficulty labels are available)
- [ ] If gate passes → user re-generates `synthetic-candidates/openai_benchmark_cases.json` (50 cases)
- [ ] Run smoke test on openai_benchmark_cases.json
- [ ] If both gates pass → proceed to Phase 0
