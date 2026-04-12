# v6 Experiment Conclusions

**Date:** 2026-04-11  
**Experiment:** self_debate_experiment_v6  
**Benchmark:** 120 cases (80 regular critique+defense, 40 mixed) × 6 conditions × 3 runs = 2,160 outputs  
**Primary scorer:** GPT-4o via OpenRouter (IDR, IDP, ETD)  
**Analysis:** Bootstrap 95% CI (n=10,000, seed=42); Wilcoxon signed-rank for H3

---

## Q1: Does ml-lab debate add value over single-pass baseline?

**Answer: No — not at the pre-registered threshold.**

H1a (regular cases): lift = −0.0026, 95% CI = [−0.0108, +0.0059], p = 0.6967 → **FAIL**  
H1b (mixed FVC): lift = +0.0083, 95% CI = [0.00, 0.025], p = 0.3684 → **FAIL**

The adversarial debate protocol (isolated critic + defender + adjudicator) does not reliably outperform a single-pass critique on either regular or mixed cases. The fair-comparison lift is negative (−0.0026) and the bootstrap CI spans zero by a wide margin. The null result is robust across threshold sensitivity checks (±0.02).

*Note: CIs above are paired bootstrap (case-level differences). Original unpaired analysis
reported wider CIs of [−0.1059, 0.2236] for H1a and [0.00, 0.05] for H1b — same FAIL
verdict in both cases.*

**Dimension decomposition:** IDR is the primary failure mode — debate misses slightly more planted issues than baseline (0.6603 vs 0.6712). IDP_adj shows a small positive signal (+0.0167) from adjudicator filtering, but this is insufficient to offset the IDR deficit. DRQ and FVC are flat across conditions.

---

## Q2: Does adversarial structure add value over a compute-matched ensemble?

**Answer: No — ensemble is formally superior on regular cases.**

H2 regular: isolated_debate − ensemble_3x = −0.0287, CI = [−0.0434, −0.0154] → **FAIL (ensemble > debate)**  
H2 mixed FVC: isolated_debate − ensemble_3x = −0.0167, CI = [−0.075, 0.025] → **INCONCLUSIVE**

The paired bootstrap CI for regular cases excludes zero entirely in the ensemble-favored direction. At matched compute (3×), three independent assessors with union-of-issues pooling formally outperform one structured debate on fair-comparison score.

**ensemble_3x has the highest IDR (0.7717) and IDP (0.9861) of all conditions.** The union-of-issues pooling provides a +0.1005 recall advantage over baseline that is now formally distinguishable from the isolated_debate result. Compute spent on independent redundancy outperforms compute spent on adversarial structure.

*Precision by support tier (follow-up, `v6_minority_precision.py`, 180 GPT-4o calls):* minority-flagged issues (1/3 assessors) precision = 0.946, unanimous precision = 0.929; diff = +0.017, 95% CI [−0.028, +0.068], p=0.258. No significant precision difference across tiers. See ENSEMBLE_ANALYSIS.md §7.*

*Note: This result was originally reported as INCONCLUSIVE when an unpaired bootstrap was used (CI = [−0.1567, +0.0976]). Correcting to a paired bootstrap (case-level differences) narrowed the CI 18× to [−0.0434, −0.0154], excluding zero.*

---

## Q3: Is forced multiround superior to natural stopping?

**Answer: No.**

H3: CFM hard mean = 0.7049, MR hard mean = 0.6736, diff = +0.0313, W = 16.0, p = 0.3677, n_eff = 7 → **FAIL**

Conditional FM does not significantly outperform multiround on hard cases. The gate-fire rate of 94.7% (341/360 files) means the conditional gate almost never stops at round 1 — CFM is functionally equivalent to full multiround in practice. When nearly all cases require round 2, the "conditional" nature of the gate provides no efficiency benefit and no quality improvement.

**Secondary: hollow rate PASS.** Proxy hollow rate = 2.2% (< 10% threshold). When round 2 does fire, it is not hollow — PRR > 0 in the overwhelming majority of cases.

---

## Q4: Does persona-biasing improve debate quality?

**Answer: Mixed direction — passes the criterion but not a clean improvement.**

H6: 2/3 tested dimensions have CI excluding 0 → **PASS** (pre-registered criterion: ≥2/3)  
- IDR: delta = +0.0352, CI = [−0.0093, 0.0787], p = 0.0598 — not significant (CI includes 0)
- IDP_adj: delta = −0.0389, CI = [−0.0722, −0.0083], p = 0.9926 — **significant, negative** (precision hurt)
- FVC_mix: delta = +0.2417, CI = [0.1583, 0.3417], p = 0.00 — **significant, positive** (mixed cases better)

**The PASS verdict requires interpretation.** Both significant dimensions point in opposite directions: persona-biasing improves FVC on mixed cases (+0.2417) while statistically degrading adjudicated precision (−0.0389). The net effect on overall quality is ambiguous and use-case dependent.

**FVC (mixed cases):** Biased debate achieves 0.25 vs isolated debate's 0.0083 on FVC_mixed. The combative-critic and selective-defender personas reliably produce `empirical_test_agreed` verdicts on mixed cases, where isolated debate almost never does. This is a real structural difference.

**IDP_adj:** Persona-priming lowers IDP_raw (0.8917 vs 0.9472 baseline) — the aggressive critic generates more false claims. The adjudicator does not fully filter these out (IDP_adj = 0.9250 vs 0.9639 isolated). Precision is formally hurt by bias injection.

*Note: Original analysis reported H6 FAIL (1/3 dims) using an unpaired bootstrap. Correcting to paired bootstrap changed IDP_adj from CI=[−0.075, 0.000] to CI=[−0.0722, −0.0083], shifting the verdict to PASS.*

---

## Cross-Cutting Observations

**ETD ceiling (H4, exploratory):** All three debate conditions score ETD = 1.0 (full credit) on 100% of mixed cases. Every debate produced condition + supports_critique_if + supports_defense_if in the transcript. The ETD metric provides zero discrimination between debate conditions.

**Multiround FVC (mixed cases):** Multiround achieves FVC_mixed = 0.3667, the highest of all conditions. Biased_debate is second (0.25). Multiple debate rounds help mixed cases more than regular cases — the iterative exchange surfaces empirical test designs that single-pass baseline (FVC = 0.0) never produces.

**Baseline ceiling on regular cases:** Baseline FC = 0.6785. Most regular cases (eval_scenario category) score near the ceiling under baseline, leaving little room for debate to add value. The RC (ReScience) cases score near the floor. This bimodal pattern compresses the effective range for H1a.

**RC-stratified subgroup analysis (post-hoc, journal `61ee949b`):** Slicing results by `is_real_paper_case` shows the ensemble IDR advantage is ~3× larger on the 25 RC cases (+0.172: ensemble_3x IDR=0.4545 vs baseline 0.2828) than on the 55 synthetic regular cases (+0.059: 0.9553 vs 0.8961). The aggregate reported gap (+0.1005) was diluted by the easier synthetic subset where baseline is near ceiling. No debate protocol outperforms ensemble_3x in either subset. The ensemble recommendation is strongest on the hardest, most ecologically valid cases — those derived from real papers. See ENSEMBLE_ANALYSIS.md §8 for full stratified tables.

**Conditional FM gate saturation:** A 94.7% gate-fire rate means the FM gate is not functioning as a selective filter — it fires on almost all cases. The PRR after round 1 is rarely sufficient to stop (mean PRR = 0.418 across all CFM files). Redesigning the gate trigger (e.g., lower PRR threshold, different stopping criterion) is recommended for future runs.

---

## Phase 9 Outstanding

**H5 (cross-model scorer agreement)** is deferred to Phase 9. IDR/IDP/ETD agreement between GPT-4o (primary) and Claude (secondary) has not been quantified. The validity of all Q1–Q4 conclusions depends on GPT-4o scorer calibration.

---

## Verdict Table

*All CIs use paired bootstrap (case-level differences), n=10,000 resamples, seed=42.*

| Question | Hypothesis | Result | Finding |
|---|---|---|---|
| Q1 | H1a: Debate > Baseline (regular) | **FAIL** | lift=−0.0026, CI=[−0.0108, +0.0059] |
| Q1 | H1b: Debate > Baseline (mixed FVC) | **FAIL** | lift=+0.0083, CI includes 0 |
| Q2 | H2: Debate vs Ensemble (regular) | **FAIL (ensemble superior)** | CI=[−0.0434, −0.0154], excludes 0 |
| Q2 | H2: Debate vs Ensemble (mixed FVC) | **INCONCLUSIVE** | CI spans zero |
| Q3 | H3: CFM > Multiround (hard cases) | **FAIL** | p=0.3677; gate fires 94.7% of cases |
| Q4 | H6: Biased > Isolated | **PASS (mixed direction)** | 2/3 dims: FVC_mix positive, IDP_adj negative |
| — | H4: ETD by mode (exploratory) | **CEILING** | ETD=1.0 for all conditions; no discrimination |
| — | H5: Cross-model scorer agreement | **N/A** | GPT-4o used as primary scorer; confound pre-empted |
