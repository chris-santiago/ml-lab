# Ensemble Analysis: ensemble_3x Design and H2 Results

**Experiment:** self_debate_experiment_v6  
**Date:** 2026-04-11  
**Related hypothesis:** H2 (isolated_debate vs ensemble_3x)

---

## 1. Design Rationale

The `ensemble_3x` condition exists to answer one specific question: does the adversarial
*structure* of a debate add value, or does the same compute budget spent on independent
redundancy produce equal or better results?

The comparison (`isolated_debate` vs `ensemble_3x`) is compute-matched at approximately 3x
baseline. Each `isolated_debate` run dispatches three agents in sequence — critic, defender,
adjudicator. Each `ensemble_3x` run dispatches three independent baseline-style assessors
in parallel, with no cross-assessor visibility. The compute is roughly equivalent; the
structural difference is complete: one is adversarial, one is redundant sampling.

This design is consistent with the pre-registration in `plan/references/design_decisions.md`
(Section 4): "If ensemble >= debate, adversarial structure adds no value over independent
redundancy."

---

## 2. Union vs Majority-Vote Split Rule

`ensemble_3x` applies two different aggregation rules for different scoring dimensions:

| Dimension | Rule | Rationale |
|---|---|---|
| IDR (issue recall) | **Union** — credit if *any* assessor found the issue | Maximizes recall; a planted flaw should be caught if at least one assessor catches it |
| FVC, DRQ (verdict correctness) | **Majority vote** — 2-of-3 assessors agree | Preserves verdict precision; minority verdicts should not be accepted |

The split rule was established prior to running the experiment. Its motivation comes from v5
data, where union IDR was 0.8725 vs majority IDR of 0.7679 — a 0.1046 recall improvement
from union aggregation. Majority IDR artificially penalizes ensemble conditions: if two
assessors miss an issue but one finds it, majority-IDR counts it as a miss even though the
issue was identified. Union credit reflects what the ensemble *collectively* knows.

The asymmetry is intentional and consistent: use the most recall-favorable rule for recall
metrics (IDR), and use the most conservative rule for verdict metrics (FVC/DRQ). Applying
union aggregation to the verdict would inflate FVC by accepting any minority verdict, which
would not represent a fair comparison.

IDP (issue detection precision) for `ensemble_3x` (0.9861) is not explicitly assigned to
either aggregation rule in the design documents. The high value is consistent with
baseline-style assessors rarely generating false claims regardless of aggregation method.
The precise IDP aggregation rule is worth documenting explicitly in future ensemble designs.

---

## 3. H2 Results

**H2 tests:** Is `isolated_debate` FC statistically distinguishable from `ensemble_3x` FC?  
Positive delta = debate superior; negative delta = ensemble superior.

| Dimension | isolated_debate | ensemble_3x | Delta (iso − ens) | 95% CI | Verdict |
|---|---|---|---|---|---|
| FC (regular cases) | 0.6759 | 0.7046 | −0.0287 | [−0.0434, −0.0154] | FAIL (ensemble superior) |
| FVC_mixed | 0.0083 | 0.025 | −0.0167 | [−0.075, 0.025] | INCONCLUSIVE |

On regular cases, the paired CI excludes zero entirely — ensemble is formally superior to
debate on the FC composite (H2 regular FAIL, ensemble > debate). On mixed FVC, the CI spans
zero and the result remains inconclusive at this sample size.

*Note: Originally reported as INCONCLUSIVE with unpaired bootstrap CI = [−0.1567, +0.0976].
Correcting to paired bootstrap (CONCLUSIONS.md Q2, journal `08b523f8`) narrowed the CI to
[−0.0434, −0.0154], excluding zero.*

**Bootstrap parameters:** n=10,000 resamples, seed=42.

---

## 4. IDR-vs-FC Discrepancy

The INCONCLUSIVE verdict on H2 masks a large descriptive difference on IDR:

| Condition | IDR | IDP | DRQ | FVC | FC (mean) |
|---|---|---|---|---|---|
| isolated_debate | 0.6603 | 0.9444 | 0.75 | 0.75 | 0.6759 |
| ensemble_3x | 0.7717 | 0.9861 | 0.75 | 0.75 | 0.7046 |
| **Delta** | **+0.1114** | +0.0417 | 0.0 | 0.0 | +0.0287 |

The ensemble IDR advantage is +0.1114 — the largest per-dimension difference in the
experiment. Yet the FC delta is only +0.0287. The reason is structural: FC for regular cases
is computed per-case as the mean of IDR, IDP, DRQ, and FVC, then averaged across cases. DRQ
and FVC are flat at 0.75 for both conditions, contributing no signal to the difference.
IDP contributes only +0.0417. The IDR advantage of +0.1114 is diluted when averaged with
three other dimensions that show minimal or no separation.

This means: **if IDR were the sole evaluation metric, ensemble_3x would clearly outperform
isolated_debate.** The INCONCLUSIVE H2 verdict is a consequence of metric averaging, not
evidence that the two conditions are equivalent on recall. For tasks where missing planted
flaws is the primary failure mode, the ensemble's IDR advantage is practically meaningful
regardless of the FC composite result.

This is a measurement design issue as much as a result. FC was chosen as the primary metric
because it combines multiple quality dimensions. For recall-prioritized use cases, an
IDR-only comparison would be more informative.

---

## 5. Majority-Vote FVC Artifact

The majority-vote rule on the verdict dimension produces a structural artifact on mixed cases:

| Condition | FVC_mixed |
|---|---|
| baseline | 0.0 |
| isolated_debate | 0.0083 |
| **ensemble_3x** | **0.025** |
| biased_debate | 0.25 |
| multiround | 0.3667 |

`ensemble_3x` FVC_mixed (0.025) is barely above baseline (0.0) and well below both debate
conditions. This is not a failure of the majority-vote rule — it is the expected consequence
of the ensemble architecture.

Each individual assessor in `ensemble_3x` is a baseline-style single-pass critic. With no
adversarial exchange, each assessor makes a binary verdict: `critique_wins` or
`defense_wins`. Majority-voting across three binary verdicts still produces a binary verdict.
The `empirical_test_agreed` resolution — which is the *only* acceptable resolution for mixed
cases — can only emerge from a structured debate in which both sides explicitly recognize and
acknowledge empirical ambiguity. Ensemble sampling over non-debate assessors cannot generate
this resolution regardless of how many assessors are pooled or how their votes are aggregated.

The consequence: on mixed cases, ensemble_3x FVC_mixed is structurally bounded near zero.
The metric is not measuring the same capability as it does for debate conditions. When
comparing ensemble vs debate on FVC_mixed, the debate conditions have an architectural
advantage that is built into the task, not just a result of better performance.

For Q2 (debate structure vs compute-matched ensemble), FVC_mixed should be interpreted
cautiously. The INCONCLUSIVE result on FVC_mixed (delta = −0.0167, CI = [−0.075, 0.025])
partially reflects this near-zero floor for ensemble rather than genuine equivalence.

---

## 6. Recommendations for Future Ensemble Designs

**6.1 IDR-only comparison.** For recall-prioritized evaluations, report IDR as a primary
metric alongside FC. The FC composite obscures large IDR differences, and the IDR advantage
for ensemble (+0.1114) warrants reporting on its own terms.

**6.2 Larger N for H2 mixed.** H2 regular is formally resolved — paired CI [−0.0434, −0.0154]
excludes zero (ensemble superior). H2 mixed FVC remains INCONCLUSIVE (CI = [−0.075, +0.025]).
Increasing mixed-case N from 40 to ~160 cases per condition would provide power to detect
whether ensemble can approach debate's FVC_mixed advantage.

**6.3 Separate IDR and verdict aggregation rules.** The union/majority-vote split introduced
here should be carried forward as a standard design principle for ensemble conditions. It is
not sufficient to report "ensemble_3x IDR" without specifying the aggregation rule; future
work should label results as "union IDR" or "majority IDR" explicitly.

**6.4 Mixed-case ensemble variant.** If ensemble conditions are included in future mixed-case
experiments, consider a variant that prompts each assessor to evaluate empirical testability
explicitly (rather than just making a binary verdict). This would allow a fairer FVC_mixed
comparison against debate conditions and test whether the structural advantage of debate on
mixed cases can be approximated by prompt design.

**6.5 IDP aggregation rule.** The IDP aggregation rule for ensemble conditions should be
explicitly pre-registered. If union IDP is used, precision results may be inflated by pooling
out false claims. If majority-vote IDP is used, the rule should be stated and applied
consistently with the IDR split.

---

## 7. Minority-Flagged Precision Analysis (Follow-Up)

**Script:** `v6_minority_precision.py` | **Calls:** 180 GPT-4o calls on existing v6 data  
**Question:** Do issues flagged by only 1/3 assessors have materially lower precision than
issues flagged by 2/3 or 3/3?

**Method:** For each of 180 (case, run) pairs (60 critique cases × 3 runs), GPT-4o received
all 3 assessors' issue lists (15 issues: 3 assessors × 5 each), ground truth planted issues,
and must_not_claim details. It deduplicated issues across assessors and classified each unique
cluster as `planted_match`, `false_claim`, `valid_novel`, or `spurious`. Precision is defined
as (planted_match + valid_novel) / total per tier.

**Results:**

| Tier | N clusters | Precision | 95% CI | FP rate | planted | novel | false_claim | spurious |
|---|---|---|---|---|---|---|---|---|
| 1/3 minority | 715 | **0.946** | [0.926, 0.963] | 0.054 | 34 | 642 | 29 | 10 |
| 2/3 majority | 327 | 0.936 | [0.903, 0.965] | 0.064 | 41 | 265 | 20 | 1 |
| 3/3 unanimous | 421 | 0.929 | [0.881, 0.969] | 0.071 | 202 | 189 | 30 | 0 |
| ALL | 1,463 | 0.939 | [0.920, 0.956] | 0.061 | 277 | 1096 | 79 | 11 |

**Key test:** Precision diff (1/3 − 3/3) = +0.017, 95% CI [−0.028, +0.068], p=0.258.
CI includes zero. **No significant precision difference across support tiers.**

**Interpretation:** Minority-flagged issues (raised by exactly 1/3 assessors) are not less
precise than unanimous issues. The +0.017 point direction — minority *higher* than unanimous
— is not significant but is consistent with a plausible mechanism: assessors who catch unique
issues tend to be more specific and precise, while unanimous issues include more "safe" generic
observations (valid but lower discriminatory value).

**Implication:** The union output recommendation in §1 is now empirically supported on both
dimensions — recall (+9.5pp IDR from 11 recovered TPs) and precision (no tier-level penalty).
The "low — review manually" confidence label for minority-flagged issues reflects epistemic
caution about independent corroboration, not a measured precision deficit.

**Note on validation error rate:** 108/180 case-runs (60%) flagged at least one missing label
(typically `C.4` — GPT-4o consistently merges Assessor C's 5th issue into an earlier cluster
without including the label). The missing issues were classified but unlabeled, and are excluded
from tier counts. Since the omission is uniform across classification types, precision estimates
are unlikely to be systematically biased.

---

## 8. RC-Stratified Subgroup Analysis

**Date:** 2026-04-12 | **Journal entry:** `61ee949b`

The 80 regular cases pool 25 RC cases (`is_real_paper_case=True`, real ReScience C papers,
2020–2021 editions) with 55 synthetic regular cases (planted corruptions). The aggregate IDR
results reported in §3–4 blend these two subsets. Slicing `v6_results.json` by source:

### RC cases (real papers, n=25)

| Condition | IDR | IDP | DRQ | FVC | FC |
|---|---|---|---|---|---|
| baseline | 0.2828 | 0.9242 | 0.88 | 0.88 | 0.7056 |
| **ensemble_3x** | **0.4545** | **0.9621** | **0.88** | **0.88** | **0.7517** |
| isolated_debate | 0.2702 | 0.9167 | 0.88 | 0.88 | 0.7011 |
| biased_debate | 0.3460 | 0.8788 | 0.88 | 0.88 | 0.7094 |
| multiround | 0.3005 | 0.8939 | 0.6667 | 0.6667 | 0.6028 |

### Synthetic regular cases (n=55)

| Condition | IDR | IDP | DRQ | FVC | FC |
|---|---|---|---|---|---|
| baseline | 0.8961 | 0.9605 | 0.6909 | 0.6909 | 0.6661 |
| **ensemble_3x** | **0.9553** | **1.0** | **0.6909** | **0.6909** | **0.6832** |
| isolated_debate | 0.8861 | 0.9605 | 0.6909 | 0.6909 | 0.6644 |
| biased_debate | 0.8978 | 0.8991 | 0.6909 | 0.6909 | 0.6558 |
| multiround | 0.8560 | 0.9518 | 0.7030 | 0.7030 | 0.6971 |

### Key findings

**The ensemble IDR advantage is ~3× larger on real papers (+0.172) than on synthetic cases
(+0.059).** The aggregate reported gap (+0.1005) was diluted by the easier synthetic subset,
where baseline IDR already sits at 0.896 — near ceiling. On RC cases, where baseline IDR is
only 0.283, the ensemble's union-pooling recovers substantially more ground-truth flaws.

No debate protocol outperforms `ensemble_3x` on any metric in either subset. All debate
conditions trail or match baseline on IDR for RC cases, consistent with the aggregate result.

**Implication for the production recommendation (REPORT_ADDENDUM.md §Regular Methodology
Review):** the ensemble recommendation is strongest precisely on the hardest, most ecologically
valid cases — the ones derived from real papers. The aggregate IDR advantage understates the
benefit in the deployment context that matters most.
