# v6 Investigation Report: Does Adversarial Debate Add Value to ML Methodology Review?

> **Note (2026-04-12):** This report reflects the pre-peer-review analysis (unpaired bootstrap CIs). After Phase 10 peer review, two corrections were applied: (1) paired bootstrap narrowed H1a CI to [−0.0108, +0.0059]; (2) H2 converted from INCONCLUSIVE to FAIL (ensemble superior, CI = [−0.0434, −0.0154]). H6 converted from FAIL to PASS (mixed direction). See [`FINAL_SYNTHESIS.md`](FINAL_SYNTHESIS.md) for corrected verdicts.

**Date:** 2026-04-11
**Experiment:** self_debate_experiment_v6
**Benchmark:** 120 cases (80 regular, 40 mixed) × 6 conditions × 3 runs = 2,160 outputs
**Primary scorer:** GPT-4o via OpenRouter

---

## Abstract

The adversarial debate protocol (critic + defender + adjudicator) does not improve ML methodology review quality over single-pass baseline critique: fair-comparison lift = −0.0026, 95% CI [−0.1059, +0.2236], p = 0.5165, against a pre-registered threshold of +0.10 (H1a FAIL). On mixed cases requiring empirical test specification, debate produces a marginal FVC lift of +0.0083 over baseline, with the CI including zero (H1b FAIL). The strongest positive finding is descriptive: ensemble redundancy (3 independent assessors with union-of-issues pooling) achieves the highest issue detection recall of all conditions (IDR = 0.7717 vs. baseline 0.6712, a +0.1005 advantage), though the formal debate-vs-ensemble comparison is inconclusive (H2). The recommendation is to replace the adversarial debate protocol with ensemble assessment for methodology review, and to investigate multiround debate specifically for mixed/ambiguous cases where it achieves the highest FVC (0.3667) despite high within-case variance.

---

## Related Work

This investigation is the sixth iteration of a meta-evaluation series testing whether structured adversarial debate between LLM agents produces better methodology reviews than simpler alternatives. The series draws on three bodies of prior work:

**LLM-as-judge and self-evaluation.** Panickssery et al. (2024) documented self-enhancement bias in LLM evaluators, where models systematically credit their own outputs more favorably. The v5 cross-vendor validation confirmed this concern empirically: Claude scoring Claude outputs produced an IDR delta of −0.7737 relative to GPT-4o-mini scoring. v6 addresses this by using GPT-4o as the primary scorer for all semantic dimensions (IDR, IDP, ETD), breaking the closed-loop confound.

**Debate as an AI alignment mechanism.** Irving et al. (2018) proposed adversarial debate as a scalable oversight mechanism, hypothesizing that structured argumentation surfaces information that single-pass evaluation misses. The ml-lab protocol operationalizes this hypothesis for ML methodology review, with the critic-defender-adjudicator structure intended to improve both issue detection recall and precision.

**ML Reproducibility Challenge.** v6 replaces v5's entirely synthetic planted-corruption benchmark with cases sourced from the ML Reproducibility Challenge (RC) and ReScience C journal. RC reports provide post-hoc documented methodology flaws identified by independent reproducers, shifting the evaluation from "corruption detection" (finding known-legible bugs) to "methodology review recall" (finding flaws that required genuine analytical judgment to identify).

**Prior iterations in this series.** v3 showed a raw lift of +0.341, but the corrected fair-comparison lift was +0.0913, driven almost entirely by ETD (+0.365 lift on mixed cases). v5 redesigned the benchmark to fix structural scoring penalties but eliminated mixed cases entirely, removing the one dimension (ETD) where debate showed genuine advantage. v5's primary hypothesis failed (lift = +0.0097, CI [−0.0013, +0.0217]) with a baseline ceiling effect (FC = 0.9452). v6 corrects all five identified v5 weaknesses: ceiling effect, absence of mixed cases, closed-loop confound, majority-vote IDR suppression in ensembles, and hollow forced-multiround rounds.

---

## Experimental Design

### Research Questions

| # | Question | Conditions Compared |
|---|----------|-------------------|
| Q1 | Does adversarial debate add value over single-pass baseline? | isolated_debate vs. baseline |
| Q2 | Does adversarial structure add value over compute-matched ensemble? | isolated_debate (~3x) vs. ensemble_3x (3x) |
| Q3 | Is conditional forced multiround superior to natural stopping? | conditional_fm vs. multiround (hard cases) |
| Q4 | Does persona-biasing improve debate quality? | biased_debate vs. isolated_debate |

### Conditions

| Condition | Description | Compute | n (regular) |
|-----------|-------------|---------|-------------|
| baseline | Single-pass critique; no adversarial structure | 1x | 80 |
| isolated_debate | Critic + Defender independently; orchestrator adjudicates | ~3x | 80 |
| biased_debate | Same as isolated_debate; agents persona-primed as combative reviewer / selective responder | ~3x | 80 |
| multiround | Defender sees Critic output; up to 4 rounds, natural stopping | ~3–6x | 80 |
| conditional_fm | Round 2 gated on unresolved disagreement after round 1 | ~3–6x | 8 (hard only) |
| ensemble_3x | 3 independent assessors; union-of-issues IDR, majority-vote verdict | 3x | 80 |

The conditional_fm condition runs only on hard-labeled cases (n=8), as its design targets cases where round 1 adjudication leaves unresolved disagreement. All other conditions run on the full 80 regular cases.

### Benchmark Construction

The benchmark comprises 120 cases drawn from three pipelines:

1. **RC extraction pipeline:** Real methodology flaws extracted from ML Reproducibility Challenge reports via OpenReview API and ReScience C. GPT-4o performed flaw extraction (RC-2), must_not_claim identification (RC-3), and contamination filtering (RC-4, 10-keyword gate on reproducer language).

2. **Synthetic regular pipeline** (80 cases): Planted corruptions using the v5 9-type flaw taxonomy with cross-family smoke validation (Gemini 2.5 Flash, replacing Claude Sonnet to break same-family calibration bias).

3. **Synthetic mixed pipeline** (40 cases): Empirically contingent designs generated via a 6-type ambiguity taxonomy (split, metric, complexity, lookback, proxy, regularization), each with a concrete empirical test specification as ground truth.

All three pipelines converge at `normalize_cases.py` to produce unified Schema B, then undergo stratified selection via `select_cases.py`. Difficulty calibration uses GPT-4o pilot scoring (Phase 3, n=30), not same-model proxy scores (v5 PM3 fix). Five ceiling cases (baseline FC > 0.80) were discarded.

**Final composition:** 60 critique + 20 defense + 40 mixed = 120 cases.

### Scoring Dimensions

| Dimension | Description | Regular Cases | Mixed Cases | Scorer |
|-----------|-------------|---------------|-------------|--------|
| IDR | Issue Detection Rate (recall against documented flaws) | Primary | N/A | GPT-4o |
| IDP | Issue Detection Precision (false positive rate) | Primary | N/A | GPT-4o |
| IDP_adj | Adjudicated precision (post-defender filtering) | Secondary | N/A | GPT-4o |
| DRQ | Decision Resolution Quality | Primary | Primary | Rule-based |
| FVC | Final Verdict Correctness | Primary | Co-primary | Rule-based |
| ETD | Empirical Test Design quality | N/A | Debate conditions only | GPT-4o |

**Fair-comparison composite (FC):** mean(IDR, IDP, DRQ, FVC) on regular cases. This is the primary metric for H1a.

**Design property — DC exclusion:** The Decision Consistency (DC) dimension from v3/v5 was dropped entirely because it was fully redundant with FVC (mean absolute delta = 0.0 across all 330 comparable v5 runs). Carrying it would add no signal while introducing reporting confusion.

**Design property — union-of-issues for ensemble IDR:** v5 showed that majority-vote IDR suppressed ensemble recall from 0.8725 to 0.7679. v6 uses union-of-issues (any-assessor-found credit) for IDR while retaining majority-vote for the final verdict. This split rule recovers recall without inflating verdict correctness by accepting minority verdicts.

### Pre-Registration

All hypotheses, thresholds, and scoring rules were committed to `HYPOTHESIS.md` before Phase 5 (benchmark run). The H1a threshold was set dynamically after Phase 3 pilot:

- Pilot baseline FC mean = 0.6500 (GPT-4o scorer, 30 cases)
- Threshold formula: max(0.03, min(0.10, (1.0 − 0.6500) × 0.5)) = **0.1000**
- Hard stop gate: pilot_fc_mean < 0.80 — PASS (0.6500 < 0.80)

### Statistical Methods

- **H1a, H1b:** One-sided bootstrap, 10,000 resamples, seed=42. PASS requires lift ≥ threshold AND CI lower bound > 0.
- **H2, H6:** Two-sided bootstrap, 10,000 resamples, seed=42. PASS requires CI excluding 0.
- **H3:** Wilcoxon signed-rank test on paired hard-case means. PASS requires p < 0.05 AND hollow rate < 10%.
- **H4:** Exploratory. Reported as distributions with 95% CIs; no PASS/FAIL criterion.

---

## Results

### Primary Metric: Fair-Comparison Composite (Regular Cases, n=80)

| Condition | FC Mean | IDR | IDP | IDP_adj | DRQ | FVC |
|-----------|---------|-----|-----|---------|-----|-----|
| baseline | 0.6785 | 0.6712 | 0.9472 | 0.9472 | 0.7500 | 0.7500 |
| isolated_debate | 0.6759 | 0.6603 | 0.9444 | 0.9639 | 0.7500 | 0.7500 |
| biased_debate | 0.6726 | 0.6955 | 0.8917 | 0.9250 | 0.7500 | 0.7500 |
| multiround | 0.6676 | 0.6523 | 0.9306 | 0.9750 | 0.6917 | 0.6917 |
| ensemble_3x | 0.7046 | 0.7717 | 0.9861 | 0.9861 | 0.7500 | 0.7500 |
| conditional_fm (n=8) | 0.7049 | 0.2153 | 0.7708 | 0.9375 | 0.9167 | 0.9167 |

**Note on conditional_fm:** This condition runs only on 8 hard-labeled cases and is not directly comparable to the n=80 conditions. Its high FC (0.7049) and high DRQ/FVC (0.9167) reflect the small hard-case sample, while its very low IDR (0.2153) indicates that hard cases have genuinely difficult-to-detect flaws.

**DRQ and FVC are uninformative on regular cases.** Both dimensions are flat at 0.7500 across baseline, isolated_debate, biased_debate, and ensemble_3x. The model produces the correct verdict type with stable accuracy regardless of protocol structure. Multiround is the exception, with DRQ/FVC = 0.6917 — iterative exchange occasionally flips verdicts to the wrong answer. The effective comparison between conditions rests on IDR and IDP alone, compressing the signal space to two of four FC dimensions.

### Mixed-Case FVC and ETD

| Condition | FVC_mixed | ETD (mean) |
|-----------|-----------|------------|
| baseline | 0.0000 | N/A |
| isolated_debate | 0.0083 | 1.0 |
| biased_debate | 0.2500 | 1.0 |
| multiround | 0.3667 | 1.0 |
| conditional_fm | N/A | N/A |
| ensemble_3x | 0.0250 | N/A |

On mixed cases, the correct outcome is `empirical_test_agreed` — producing a well-specified empirical test rather than committing to a verdict. Baseline never produces this outcome (FVC = 0.0). Multiround achieves the highest mixed FVC (0.3667), followed by biased_debate (0.2500). However, isolated_debate (the pre-registered comparator for H1b) achieves only 0.0083, essentially indistinguishable from baseline.

**ETD ceiling:** All three debate conditions score ETD = 1.0 on 100% of mixed cases (40 cases × 3 runs each). Every debate transcript contains `condition`, `supports_critique_if`, and `supports_defense_if` fields. The GPT-4o ETD scorer saturated, providing zero discrimination between debate conditions. This renders H4 uninformative.

### Hypothesis Verdict Table

| Hypothesis | Metric | Observed | 95% CI | p-value | Verdict |
|------------|--------|----------|--------|---------|---------|
| H1a: Debate > Baseline (regular FC) | FC lift | −0.0026 | [−0.1059, +0.2236] | 0.5165 | **FAIL** |
| H1b: Debate > Baseline (mixed FVC) | FVC lift | +0.0083 | [0.00, 0.05] | 0.3610 | **FAIL** |
| H2: Debate vs Ensemble (regular FC) | FC delta | −0.0287 | [−0.1567, +0.0976] | 0.6747 | **INCONCLUSIVE** |
| H2: Debate vs Ensemble (mixed FVC) | FVC delta | −0.0167 | [−0.075, +0.025] | 0.7604 | **INCONCLUSIVE** |
| H3: CFM > Multiround (hard) | FC diff | +0.0313 | W=16.0, n_eff=7 | 0.3677 | **FAIL** |
| H4: ETD by mode (exploratory) | ETD mean | 1.0 all conditions | — | — | **CEILING** |
| H5: Cross-model scorer agreement | — | — | — | — | **N/A** |
| H6: Biased > Isolated (≥2/3 dims) | Multi-dim | 1/3 dims CI excl. 0 | see below | — | **FAIL** |

**H5 disposition:** Phase 9 (cross-vendor scorer validation) was pre-empted by the Phase 6 design: GPT-4o served as the primary scorer for all semantic dimensions (IDR, IDP, ETD), structurally addressing the closed-loop confound that H5 was designed to quantify. Claude was not used as a scorer in v6. H5 is therefore N/A rather than deferred — the experimental design eliminated the confound it was intended to measure.

### Per-Dimension Lift Decomposition (Isolated Debate vs. Baseline, Regular Cases)

| Dimension | Baseline Mean | Isolated Mean | Lift | Direction |
|-----------|---------------|---------------|------|-----------|
| IDR | 0.6712 | 0.6603 | −0.0109 | Negative — debate misses more planted issues |
| IDP | 0.9472 | 0.9444 | −0.0028 | Flat |
| IDP_adj | 0.9472 | 0.9639 | +0.0167 | Positive — adjudication filters some false claims |
| DRQ | 0.7500 | 0.7500 | 0.0000 | Flat |
| FVC | 0.7500 | 0.7500 | 0.0000 | Flat |

**IDR is the primary driver of the null result.** The adversarial structure does not improve issue detection recall on regular cases — it slightly reduces it. The sole positive signal is IDP_adj (+0.0167), indicating that the adjudicator filters a small number of false-positive claims raised by the critic. This improvement is insufficient to offset the IDR deficit.

### H6 Decomposition: Biased vs. Isolated Debate

| Dimension | Delta (biased − isolated) | 95% CI | p-value | CI Excludes 0 |
|-----------|--------------------------|--------|---------|---------------|
| IDR | +0.0352 | [−0.0907, +0.1614] | 0.2892 | No |
| IDP_adj | −0.0389 | [−0.075, 0.000] | 0.9782 | No |
| FVC_mixed | +0.2417 | [+0.1583, +0.3333] | 0.0000 | **Yes** |
| IDP_raw (diagnostic) | −0.0528 | [−0.100, −0.0056] | 0.9843 | Yes (negative) |

Persona-biasing produces one significant positive effect: FVC on mixed cases (+0.2417, CI excludes 0). The combative-critic and selective-defender personas reliably produce `empirical_test_agreed` verdicts where isolated debate almost never does. However, this comes at a precision cost: IDP_raw drops from 0.9444 to 0.8917, and IDP_adj drops from 0.9639 to 0.9250. The aggressive critic generates more false claims that the defender does not fully filter. Since only 1 of 3 pre-registered dimensions shows a CI excluding zero, H6 fails the pre-registered criterion (≥2 of 3 required).

### Ensemble IDR Advantage

The strongest positive finding in the experiment is descriptive rather than hypothesis-driven:

| Condition | IDR (regular) | IDP (regular) |
|-----------|---------------|---------------|
| baseline | 0.6712 | 0.9472 |
| isolated_debate | 0.6603 | 0.9444 |
| ensemble_3x | **0.7717** | **0.9861** |

Ensemble union-of-issues pooling provides a +0.1005 IDR advantage over baseline and +0.1114 over isolated debate. Simultaneously, ensemble achieves the highest IDP of all conditions (0.9861). Three independent assessors with union-of-issues recall aggregation and majority-vote verdict aggregation outperform adversarial debate on both recall and precision. This finding was not formally tested against baseline (the pre-registered H2 tests ensemble vs. isolated_debate), but the descriptive gap is the largest observed effect in the experiment. *(Per-tier precision follow-up, `v6_minority_precision.py`: minority-flagged precision = 0.946 vs unanimous 0.929, diff = +0.017, CI [−0.028, +0.068] — no significant precision penalty for minority-flagged issues. ENSEMBLE_ANALYSIS.md §7.)*

### Conditional FM Gate Behavior

| Metric | Value |
|--------|-------|
| Total CFM files | 360 |
| Gate-fired (2 rounds) | 341 (94.7%) |
| Not-gated (1 round) | 19 (5.3%) |
| Proxy hollow (gate_fired + PRR=0) | 8 (2.2%) |
| Mean PRR (gate-fired) | 0.395 |
| PRR ≥ 0.5 (gate-fired) | 137 (40.2%) |

The conditional gate fires on 94.7% of cases, making conditional FM functionally equivalent to full multiround. The gate's stopping criterion (all points resolved OR verdict agreement) is rarely satisfied after round 1 — mean PRR after round 1 is 0.418. The efficiency benefit the gate was designed to provide does not materialize.

The proxy hollow rate (2.2%) passes the pre-registered <10% threshold, indicating that when round 2 fires it is substantive (PRR > 0). The gate prevents hollow rounds but does not provide selective deployment.

---

## Within-Case Variance Analysis

Twenty-three case-condition pairs exceed the within-case variance threshold of 0.05 (variance computed across 3 runs per case per condition). Twenty of twenty-three belong to the multiround condition.

**Multiround variance concentration:**

| Variance Range | Multiround Cases | Other Conditions |
|----------------|-----------------|------------------|
| 0.05–0.10 | 14 | 0 |
| 0.10–0.25 | 6 | 3 |
| Total | 20 | 3 |

The most extreme cases show complete run-to-run instability:

| Case ID (abbreviated) | Condition | Run Means | Variance |
|----------------------|-----------|-----------|----------|
| rc_rescience_2020_schneider2021re | multiround | [1.0, 0.0, 0.0] | 0.2222 |
| eval_scenario_725 | multiround | [0.0, 1.0, 0.0] | 0.2222 |
| eval_scenario_703 | multiround | [1.0, 0.0, 0.0] | 0.2222 |
| eval_scenario_709 | multiround | [1.0, 1.0, 0.0] | 0.2222 |

Several multiround cases swing between FC = 0.0 and FC = 1.0 across runs — the protocol produces completely different outcomes depending on stochastic variation in agent outputs. This directly undermines multiround's descriptive FVC_mixed advantage (0.3667, highest of all conditions): the advantage is real in aggregate but unstable at the case level, driven by a subset of runs where multiround happens to converge on the correct outcome.

No other condition exhibits variance above 0.05 on more than 3 cases, indicating that multiround's iterative exchange is uniquely susceptible to path-dependent outcomes.

---

## Failure Mode Analysis

### IDR as the Primary Failure Mechanism

Across all debate conditions, IDR is the dimension that most consistently underperforms baseline:

| Condition | IDR vs. Baseline | IDP vs. Baseline |
|-----------|-----------------|-----------------|
| isolated_debate | −0.0109 | −0.0028 |
| biased_debate | +0.0243 | −0.0555 |
| multiround | −0.0189 | −0.0166 |

Debate does not help the model find more issues. The adversarial exchange either has no effect on issue detection (isolated) or slightly reduces it (multiround). The one exception — biased_debate's positive IDR delta (+0.0243) — comes at a large precision cost (IDP −0.0555). The combative critic persona raises more concerns, but many are false positives.

### DRQ/FVC Compression

DRQ and FVC are both flat at 0.7500 across four of six conditions on regular cases. The model's verdict accuracy is stable regardless of whether it receives adversarial challenge. This means two of four FC dimensions contribute zero discriminative signal, and the entire comparison rests on IDR and IDP.

The only DRQ/FVC deviation is multiround (0.6917) — iterative exchange occasionally destabilizes correct verdicts. Combined with multiround's high within-case variance, this suggests that additional debate rounds introduce noise rather than signal on cases where the correct verdict is deterministic.

### Multiround on Mixed Cases: Promising but Unstable

Multiround achieves the highest FVC_mixed (0.3667), suggesting that iterative exchange helps agents recognize empirical ambiguity. However: 20 of 23 high-variance case-condition pairs are multiround, and several cases swing FC between 0.0 and 1.0 across runs. The advantage is concentrated in a subset of cases and runs. The multiround architecture may genuinely help on mixed cases, but its current implementation lacks the consistency required for reliable deployment.

### ETD Saturation

ETD = 1.0 for all debate conditions on all mixed cases. Every debate transcript contains the three structural elements the GPT-4o scorer checks. This is a scorer calibration failure, not a genuine quality finding — the ETD rubric is too coarse to discriminate between quality levels of empirical test specification. The metric needs either finer-grained scoring criteria or a different evaluation approach to provide useful signal in future iterations.

---

## Sensitivity Analysis Summary

| Check | Status | Key Finding |
|-------|--------|-------------|
| Method A vs B aggregation | PASS | Zero divergence; balanced design ensures equivalence |
| H1a threshold sensitivity | PASS | FAIL at thresholds 0.08, 0.10, 0.12; null result is robust |
| Difficulty stratification (PM3) | PASS (limited n) | Spearman ρ = −0.5649 (correct direction, n=15 labeled cases) |
| RC vs synthetic source stratification | CONFIRMED | ensemble_3x IDR gap: RC cases +0.172 vs synthetic +0.059; recommendation holds in both subsets (ENSEMBLE_ANALYSIS.md §8, journal `61ee949b`) |
| IDP diagnostic | PASS | biased_debate IDP_raw = 0.8917 (lower); extraction path functioning correctly |
| CFM hollow rate | PASS | Proxy 2.2% < 10% threshold |

---

## Limitations

### 1. ETD Scorer Saturation

The GPT-4o ETD scorer assigns full credit (1.0) to all debate outputs on all mixed cases, providing zero discrimination between conditions. H4 is rendered uninformative. Future iterations require either a finer-grained ETD rubric with sub-element quality scoring, or human expert review of empirical test concreteness.

### 2. Small Sample for Difficulty-Stratified Analysis

Only 15 of 80 regular cases carry difficulty labels (7 medium, 8 hard). H3 runs on n=8 hard cases with n_eff=7 for the Wilcoxon test, providing very low statistical power. At n=8, the test requires directional agreement on 7 of 8 cases for p < 0.05. H3 was pre-registered as exploratory when n_hard < 15.

### 3. DRQ/FVC Compression Limits Discriminative Power

DRQ and FVC are flat at 0.7500 across four of six conditions. The fair-comparison composite rests on only two informative dimensions (IDR and IDP). The lift decomposition is reported alongside the composite, enabling readers to assess the IDR/IDP signals independently. The compression does not change the verdict direction: IDR-only lift = −0.0109, IDP-only lift = −0.0028, both negative.

### 4. Multiround Variance Threatens Mixed-Case Conclusions

Twenty of twenty-three high-variance case-condition pairs belong to multiround. The aggregate FVC_mixed = 0.3667 derives from 120 observations providing reasonable aggregate stability, but run-level instability is severe. The multiround FVC_mixed advantage is presented as descriptive with explicit caveats.

### 5. GPT-4o Scorer Calibration Is Unvalidated

All semantic scoring relies on GPT-4o. Absolute score values (e.g., IDR = 0.6712) are GPT-4o-relative and should not be interpreted as objective quality measurements. The lift calculations are within-evaluator comparisons and are valid as long as scorer bias is condition-independent; there is no evidence of condition-dependent scoring bias.

### 6. Benchmark Composition May Not Represent Real-World Difficulty Distribution

The benchmark combines RC cases (real reproduced flaws) with synthetic cases (planted corruptions and engineered ambiguity). The Phase 3 pilot calibrated difficulty to produce baseline FC = 0.6500, providing substantially more headroom than v5 (FC = 0.9452).

---

## Artifacts

| File | Description |
|------|-------------|
| `HYPOTHESIS.md` | Pre-registered hypotheses, thresholds, and scoring rules |
| `v6_hypothesis_results.json` | All bootstrap CI results, descriptive statistics, within-case variance |
| `v6_results.json` | Full per-case results with per-condition means and per-run scores |
| `v6_rescored_idr_idp.json` | GPT-4o-scored IDR/IDP/ETD values for all 2,160 runs |
| `SENSITIVITY_ANALYSIS.md` | Phase 8 robustness checks |
| `CONCLUSIONS.md` | Q1–Q4 verdict summaries with cross-cutting observations |
| `ENSEMBLE_ANALYSIS.md` | Union IDR design, split rule rationale, H2 analysis |
| `benchmark_cases_verified.json` | Final 120-case benchmark in Schema B format |
| `plan/PLAN.md` | Full experimental plan with phase index and design rationale |
| `plan/references/design_decisions.md` | Condition design and scoring dimension rationale |
| `plan/references/hypotheses.md` | H1–H6 quick-reference definitions |
| `plan/references/v5_mitigations.md` | PM1–PM5 failure mode mapping to v6 design fixes |
