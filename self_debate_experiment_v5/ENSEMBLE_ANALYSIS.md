# v5 Ensemble Analysis

## Overview

The ensemble condition runs three independent assessors in parallel and applies a conservative majority-vote rule: the verdict is accepted only if 2/3 or more assessors agree. If assessors split evenly, the conservative rule fires and the run is flagged. The ensemble was designed to test whether adversarial synthesis (multiple independent assessments) improves calibration over a single debate.

**ETD Exclusion Rationale:** ETD (Exchange Trajectory Divergence) is excluded from all ensemble comparisons because: (a) ETD requires an adversarial exchange with measurable round-by-round divergence, which the ensemble condition does not have — each assessor operates independently; and (b) ETD is N/A for all ARCH-1 cases regardless of condition (ideal_resolution is always critique_wins or defense_wins with no mixed cases). This is a structural exclusion, not a data quality exclusion.

**DC Note:** DC (Debate Correctness) is included in Table B but is treated as diagnostic-only throughout. It does not enter the fair-comparison mean.

---

## Table A: Ensemble vs Isolated Debate (Fair Comparison Dimensions)

Dimensions: IDR, IDP, DRQ, FVC. n_cases=110 for both conditions.

| Dimension | isolated_debate | ensemble | Delta |
|---|---|---|---|
| IDR (rescored) | 0.8969 | 0.7679 | -0.1290 |
| IDP (rescored) | 0.8549 | 0.9583 | +0.1034 |
| DRQ | 1.0000 | 0.9727 | -0.0273 |
| FVC | 1.0000 | 0.9727 | -0.0273 |
| **FC Mean** | **0.9477** | **0.9247** | **-0.0230** |

The ensemble scores lower than isolated_debate on FC mean (-0.0230). IDR is the primary driver of ensemble underperformance (-0.1290). IDP is higher for ensemble (+0.1034) — the ensemble generates fewer false-positive issues. DRQ and FVC are slightly lower (-0.0273 each).

**Wilcoxon (isolated_debate vs ensemble, fair dims):** W=648.5, p=0.119 — not significant at α=0.05.

---

## Table B: Ensemble vs Baseline (Fair Comparison Dimensions)

| Dimension | ensemble | baseline | Delta |
|---|---|---|---|
| IDR (rescored) | 0.7679 | 0.8729 | -0.1050 |
| IDP (rescored) | 0.9583 | 0.8549 | +0.1034 |
| DRQ | 0.9727 | 0.9894 | -0.0167 |
| FVC | 0.9727 | 0.9894 | -0.0167 |
| **FC Mean** | **0.9247** | **0.9266** | **-0.0019** |

Ensemble and baseline have nearly identical FC means (0.9247 vs 0.9266, delta = -0.0019). The ensemble trades IDR for IDP: it misses planted issues more often (-0.1050 on IDR) but raises fewer false positives (+0.1034 on IDP). The net effect on FC mean is negligible. Neither condition dominates the other across all dimensions.

---

## Defense_Wins Criterion

The pre-registered secondary criterion: Ensemble FVC ≥ 0.5 on ≥ 60% of defense_wins cases.

| | Count | Fraction |
|---|---|---|
| defense_wins cases | 30 | — |
| Ensemble FVC ≥ 0.5 | 30 | 100.0% |
| Criterion met (≥ 60%) | Yes | — |

Ensemble correctly produced FVC ≥ 0.5 on all 30 defense_wins cases. This means the ensemble's adversarial synthesis reliably identified defense-winning designs and assigned favorable verdicts for the defender. However, given H1 failure, this result is interpreted as showing ensemble does not harm defense_wins calibration, not as evidence of ensemble superiority.

**IDP analysis on defense_wins cases:** IDP is N/A for defense_wins cases by protocol (no planted issues to find). The IDP dimension only applies to critique cases. The defense_wins stratum contributes only DRQ and FVC to ensemble scoring, both of which are near-ceiling across all conditions.

---

## Hollow-Round Analysis

**Hollow-round detection reliability:** Per PHASE6_OBSERVATIONS.md, approximately 111 multiround/forced_multiround files underwent a schema repair pass (Phase 10.5) that set per-round `point_resolution_rate` fields to conservative defaults (0 for all rounds except last, which received the total). This means hollow-round detection from per-round `point_resolution_rate` is unreliable for repaired files. Files with `schema_repair_note` are affected.

**What is detectable:** Within-case variance results show mean within-case variance by condition:

| Condition | Mean within-case variance |
|---|---|
| isolated_debate | 0.0053 |
| multiround | 0.0059 |
| ensemble | 0.0086 |
| baseline | 0.0044 |

The ensemble condition has the highest within-case variance (0.0086), consistent with the conservative rule sometimes firing and sometimes not depending on assessor agreement. Zero high-variance cases were flagged in the high_variance_cases list — all conditions showed acceptable run-to-run stability.

**Hollow rounds in forced_multiround:** The schema repair applied conservative defaults (per-round `points_resolved` = 0 except last round). This means any hollow-round rate estimated from these fields would reflect the repair assumption rather than actual protocol behavior. The PHASE6_OBSERVATIONS.md notes that "Phase 10.5 hollow-round rate analysis will not be meaningful for these cases." No reliable hollow-round count can be reported for v5 forced_multiround cases.

What is observable from PHASE6_OBSERVATIONS.md qualitative notes: eval_scenario_691, eval_scenario_649, eval_scenario_428, and eval_scenario_524 all showed substantive round-by-round engagement in forced_multiround, with progressive resolution or partial-concession patterns. These are explicitly not hollow rounds. The 3 null-verdict cases (eval_scenario_381, 411, 616) represent the opposite failure mode — unresolvable exchange rather than hollow engagement.

---

## DC/FVC Divergence Diagnostic

From `dc_fvc_diagnostic` in v5_results.json:

| Condition | n_comparable | mean_abs_delta | divergent_runs | divergence_rate |
|---|---|---|---|---|
| isolated_debate | 240 | 0.0 | 0 | 0.0% |
| multiround | 240 | 0.0 | 0 | 0.0% |
| forced_multiround | 36 | 0.0 | 0 | 0.0% |
| ensemble | 240 | 0.0 | 0 | 0.0% |
| baseline | 0 | N/A | 0 | N/A |

No condition has any DC/FVC divergence. Every comparable run (DC applicable) shows DC = FVC exactly. No condition exceeds the 0.1 divergence_rate flag threshold.

**Conclusion: DC is empirically redundant with FVC for all v5 cases.** When DC is applicable (debate conditions), it equals FVC in every run. This confirms DC carries no additional information beyond what FVC already captures in this experiment. The diagnostic-only treatment of DC is empirically justified.

Baseline has n_comparable_runs=0 — DC is structurally N/A for baseline (no Defender role).

---

## Ensemble IDR Suppression Mechanism

Ensemble IDR (0.7679) is meaningfully lower than baseline IDR (0.8729) and isolated_debate IDR (0.8969). This is the majority-vote suppression mechanism.

**How it works:** The ensemble runs three independent assessors. Each assessor identifies some subset of planted issues. The ensemble's final IDR credit depends on whether the must-find issues appear in the majority verdict. If two assessors identify different issues as primary (or agree the design has problems but focus on different specifics), the majority-vote aggregation may not surface the specific must-find issue even if all three individually recognized something problematic.

**Evidence from PHASE6_OBSERVATIONS.md:** Cases eval_scenario_3 and eval_scenario_295 both showed 2/3 critique_wins splits where the defense argument was substantively compelling (metric alignment flaws). The conservative rule correctly prevented false consensus, but these cases also had lower IDR scores because the two agreeing assessors did not converge on the exact planted issue.

**IDP trade-off:** The same mechanism that suppresses IDR elevates IDP (0.9583 vs 0.8549 for baseline). The conservative ensemble rule filters out single-assessor false positives. If only one assessor raises a spurious issue, the majority vote excludes it. This is the correct behavior — ensemble reduces noise in both directions — but the IDR suppression cost is higher than the IDP benefit for the overall FC mean.

**Practical implication:** The ensemble format appears better suited to scenarios where false-positive control matters more than recall. For benchmark tasks requiring identification of specific planted issues, the majority-vote aggregation is insufficiently recall-preserving.
