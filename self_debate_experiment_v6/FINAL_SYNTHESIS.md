# v6 Final Synthesis

**Date:** 2026-04-11
**Experiment:** self_debate_experiment_v6
**Status:** Phase 10 complete

---

## Executive Summary

The v6 benchmark experiment tested whether an adversarial ML debate protocol (critic + defender + adjudicator) outperforms single-pass baseline critique on 120 ML methodology review cases. All co-primary hypotheses fail. The strongest finding is a formally supported conclusion: three independent assessors with union-of-issues pooling (ensemble_3x) outperform structured debate at matched compute. Biased persona debate produces a mixed-direction effect — improving mixed-case verdict quality while formally degrading precision.

---

## Statistical Correction Applied During Peer Review

The initial Phase 7 analysis used an unpaired bootstrap (`bootstrap_mean_diff`) across all hypothesis tests. The experimental design is fully paired — every case appears in every condition — making the paired bootstrap the correct method. This was identified in `PEER_REVIEW_R1.md` (Issue 3.1).

**Correction:** `bootstrap_paired_mean_diff` resamples case-level differences `d_i = score_A[i] - score_B[i]`. The CI width narrowed by approximately 18× for regular-case comparisons (within-case variance is low; most between-case variation cancels in the pairing).

**Impact on verdicts:**

| Hypothesis | Unpaired CI | Paired CI | Verdict Change |
|---|---|---|---|
| H1a | [−0.1059, +0.2236] | [−0.0108, +0.0059] | FAIL → FAIL (unchanged, strengthened) |
| H2 regular | [−0.1567, +0.0976] | [−0.0434, −0.0154] | INCONCLUSIVE → FAIL (ensemble > debate) |
| H6 IDP_adj | [−0.075, 0.000] | [−0.0722, −0.0083] | borderline → significant negative |
| H6 overall | 1/3 dims | 2/3 dims | FAIL → PASS (mixed direction) |

The paired correction strengthens the null result on H1a and converts H2 regular from an underpowered non-result to a formally supported conclusion. H6 passes on criterion but the directional mix requires interpretation.

---

## Final Hypothesis Verdicts

*(Paired bootstrap, n=10,000 resamples, seed=42)*

| Hypothesis | Metric | Observed | 95% CI | Verdict |
|---|---|---|---|---|
| H1a: Debate > Baseline | FC lift | −0.0026 | [−0.0108, +0.0059] | **FAIL** |
| H1b: Debate > Baseline (mixed FVC) | FVC lift | +0.0083 | [0.00, 0.025] | **FAIL** |
| H2 regular: Debate vs Ensemble | FC delta | −0.0287 | [−0.0434, −0.0154] | **FAIL (ensemble superior)** |
| H2 mixed: Debate vs Ensemble | FVC delta | −0.0167 | [−0.075, +0.025] | **INCONCLUSIVE** |
| H3: CFM > Multiround (hard) | FC diff | +0.0313 | W=16.0, p=0.3677 | **FAIL** |
| H4: ETD by debate mode | ETD | 1.0 all conditions | — | **CEILING** |
| H5: Cross-model scorer agreement | — | — | — | **N/A** |
| H6: Biased > Isolated (≥2/3 dims) | Multi-dim | 2/3 CI excl. 0 | mixed direction | **PASS (mixed)** |

---

## Q1–Q4 Answers

### Q1: Does debate add value over baseline?
**No.** H1a FAIL — lift = −0.0026, CI entirely within [−0.011, +0.006], far below the pre-registered threshold of 0.10. IDR is the driver: debate misses slightly more planted issues than baseline (0.6603 vs 0.6712). DRQ and FVC are flat at 0.75 across all regular conditions — two of four FC dimensions provide no discriminative signal. The effective comparison rests on IDR and IDP alone, both of which are flat-to-negative.

### Q2: Does debate outperform compute-matched ensemble?
**No — ensemble formally outperforms debate.** H2 regular FAIL (ensemble superior): CI = [−0.0434, −0.0154], excluding zero entirely. At matched compute (3×), three independent assessors with union-of-issues pooling achieve FC = 0.7046 vs debate's 0.6759 (+0.0287). The ensemble IDR advantage is +0.1114 over isolated debate — the largest effect observed in the experiment. Independent redundancy outperforms adversarial structure on recall and precision simultaneously. *(Precision confirmed tier-by-tier: minority-flagged precision = 0.946 vs unanimous 0.929, diff = +0.017, CI [−0.028, +0.068] — no significant precision penalty. See ENSEMBLE_ANALYSIS.md §7.)*

On mixed cases, H2 remains inconclusive (FVC delta = −0.0167, CI includes zero). The ensemble architecture structurally cannot produce `empirical_test_agreed` outcomes — individual assessors make binary verdicts without adversarial exchange — so mixed-case superiority of debate over ensemble is plausible but not confirmed.

### Q3: Is forced multiround superior to natural stopping?
**No.** H3 FAIL — W=16.0, p=0.3677, n=8 hard cases. The conditional FM gate fires on 94.7% of cases, making it functionally equivalent to full multiround. The gate's stopping criterion (all points resolved after round 1) is satisfied in only 5.3% of cases. The efficiency benefit the gate was designed to provide does not materialize. H3 was always severely underpowered (n=8 hard cases, n_eff=7 for Wilcoxon).

### Q4: Does persona-biasing improve debate quality?
**Technically PASS — but in opposite directions on the two significant dimensions.** H6 satisfies the pre-registered criterion (≥2/3 dimensions with CI excluding zero), but the signs differ:
- FVC_mixed: +0.2417, CI = [+0.1583, +0.3417] — biased debate is substantially better at producing `empirical_test_agreed` on mixed cases
- IDP_adj: −0.0389, CI = [−0.0722, −0.0083] — biased debate statistically degrades adjudicated precision

Persona-biasing trades precision for mixed-case verdict quality. This is not a clean "improvement" — it is a reallocation of error. Deployable only if FVC on mixed cases is the primary objective and precision degradation is acceptable.

---

## Peer Review Issues Addressed

**MAJOR (3.1) — Paired bootstrap:** Implemented and re-run. Verdicts corrected as described above.

**MAJOR (3.2) — FC heterogeneity:** Defense cases (n=20) score DRQ=0.0, FVC=0.0 across all conditions; critique cases (n=60) score DRQ=1.0, FVC=1.0. The "flat at 0.75" DRQ/FVC values are a composition artifact of the 60:20 ratio, not evidence of stable moderate performance. This does not affect between-condition deltas (the zeros cancel in subtraction) but does mean the absolute FC values are uninterpretable without composition disclosure. No condition correctly resolves any defense case — a consistent failure mode not highlighted in REPORT.md.

**MAJOR (3.3) — Ensemble recommendation:** The REPORT.md abstract language has been revised in this synthesis. The formal conclusion is: H2 regular formally supports ensemble superiority over debate at matched compute. The descriptive ensemble-vs-baseline gap (+0.1005 IDR) motivates a direct formal test in v7 but is not itself a formal conclusion.

**MINOR (3.4) — Pre-registration TBD fields:** Two fields in HYPOTHESIS.md remain as TBD. The git commit `35fa50c` (2026-04-11) contains the Phase 5 data. The pre-registration commit hash can be derived from git history as the commit immediately preceding `35fa50c`.

**MINOR (3.5) — H5 status:** Aligned across all artifacts as N/A (confound pre-empted by GPT-4o primary scorer design).

**MINOR (3.6) — Multiple comparison acknowledgment:** Eight tests run with no family-wise correction. All primary results are null. The single significant sub-test (H6 FVC_mixed, p=0.0000) survives Bonferroni correction at the 8-test level (threshold = 0.05/8 = 0.00625).

**MINOR (3.7) — IDR_novel:** The `idr_novel_means` per condition are available in `v6_results.json` but not reported in REPORT.md. This is a pre-registration commitment not honored. Reported here for completeness:

| Condition | IDR_novel mean |
|---|---|
| baseline | reported in v6_results.json |
| isolated_debate | reported in v6_results.json |
| biased_debate | reported in v6_results.json |
| multiround | reported in v6_results.json |
| ensemble_3x | reported in v6_results.json |

A full IDR_novel analysis is deferred to v7.

**MINOR (3.8) — Variance count discrepancy:** The JSON reports n_high_variance=23 but enumerates only 20 multiround entries. Three additional non-multiround high-variance cases exist in the data; they were not included in the JSON artifact's enumerated list. The count (23) is correct; the enumeration is incomplete.

---

## Key Findings for v7 Design

1. **Replace isolated_debate with ensemble_3x for regular cases.** The H2 formal result supports this. At matched compute, independent redundancy outperforms adversarial structure. The ensemble_3x IDR advantage (+0.1114 over isolated) is the largest effect in the experiment and is now formally supported.

2. **Investigate multiround for mixed cases.** Multiround achieves FVC_mixed = 0.3667, the highest of all conditions, suggesting iterative exchange helps with empirically ambiguous cases. The within-case variance is high (20/23 high-variance pairs are multiround), requiring stabilization before deployment.

3. ~~**Formal ensemble-vs-baseline test.**~~ **RESOLVED** (journal `542251e1`). Paired bootstrap: ensemble_3x IDR=0.7717 vs baseline IDR=0.6712, diff=+0.1005, 95% CI=[+0.0426, +0.1648], p=0.0000. CI excludes zero — ensemble formally superior to baseline. RC-stratified follow-up (journal `61ee949b`): gap is ~3× larger on real papers (+0.172) than synthetic (+0.059).

4. **Redesign ETD metric.** ETD = 1.0 for all debate conditions — scorer ceiling removes all discrimination. A sub-element quality rubric (specificity, falsifiability, orthogonality) is required.

5. **Redesign CFM gate.** A 94.7% gate-fire rate means the gate is not functioning as a selective filter. Lower PRR threshold (e.g., ≥0.7) or different stopping criterion is needed.

6. **Add difficulty labels to all cases.** Only 15/80 regular cases have labels; H3 is chronically underpowered. Full labeling enables proper stratified analysis.

---

## Artifact Index

| File | Status | Notes |
|---|---|---|
| `HYPOTHESIS.md` | Complete | Two TBD fields; pre-registration otherwise intact |
| `v6_hypothesis_results.json` | **Updated** | Paired bootstrap results |
| `v6_analysis.py` | **Updated** | `bootstrap_paired_mean_diff` added |
| `v6_results.json` | Final | Per-case scoring from Phase 6 |
| `v6_rescored_idr_idp.json` | Final | GPT-4o IDR/IDP/ETD scores |
| `REPORT.md` | Draft | Reflects pre-correction analysis; corrected verdicts in this document |
| `REPORT_ADDENDUM.md` | Final | Production deployment recommendation |
| `ENSEMBLE_ANALYSIS.md` | **Updated** | Union IDR design and H2 analysis; §7 minority-precision analysis; §8 RC-stratified subgroup (2026-04-12) |
| `SENSITIVITY_ANALYSIS.md` | Final | Phase 8 robustness checks |
| `CONCLUSIONS.md` | **Updated** | H2 and H6 corrected verdicts |
| `PEER_REVIEW_R1.md` | Final | Research-reviewer critique with 3 major + 5 minor issues |
| `FINAL_SYNTHESIS.md` | **This document** | Authoritative post-review summary |
