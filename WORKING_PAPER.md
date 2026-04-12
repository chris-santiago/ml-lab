# Independent Redundancy Outperforms Adversarial Debate for LLM-Based Methodology Review

**Draft — not for distribution**

---

## Abstract

Multi-agent debate is increasingly adopted for LLM-based evaluation, but recent work questions whether adversarial structure adds value beyond additional compute. We present a controlled comparison on 120 ML methodology review cases (80 regular, 40 mixed) scored by a cross-vendor evaluator (GPT-4o scoring Claude outputs). At matched compute (3x baseline), an ensemble of three independent critics with union-of-issues pooling formally outperforms structured critic-defender-adjudicator debate on both issue detection recall (IDR delta = +0.1114, the largest single-dimension effect in the experiment) and fair-comparison composite (FC delta = +0.0287, 95% CI [+0.0154, +0.0434], paired bootstrap). The FC composite understates the effect because two of four dimensions (DRQ, FVC) are flat across conditions; the IDR advantage is the primary driver. Debate is not significantly different from single-pass baseline (FC delta = -0.0026, CI [-0.0108, +0.0059]; note: this is non-significance, not formal equivalence — a TOST equivalence test was not conducted). However, iterative multi-round debate produces correct empirical-ambiguity recognition on 36.7% of mixed cases versus 0% for baseline and 2.5% for ensemble — a capability that independent sampling cannot replicate. Union pooling recovers 11 additional ground-truth issues (+9.5 percentage points recall) with no significant precision difference across support tiers (minority-flagged precision 0.946 vs. unanimous 0.929, p = 0.258, n = 1,463 clusters). These results motivate a post-hoc hypothesis: task type (convergent vs. divergent) predicts when debate helps. Ensemble dominates for divergent detection (find all flaws), while debate retains structural value for convergent judgment (assess empirical testability) — though the mixed-case comparison remains formally inconclusive (FVC_mixed CI spans zero, n = 40). If confirmed prospectively, this framework would reconcile conflicting findings in the multi-agent debate literature.

---

## 1. Introduction

Multi-agent debate — where LLM instances argue opposing positions before a judge synthesizes a verdict — has emerged as a prominent strategy for improving LLM reasoning and evaluation quality (Du et al., 2024; Liang et al., 2024). The intuitive appeal is clear: adversarial exchange should surface flaws that any single agent might miss, mirroring the logic of human peer review and legal adversarial systems.

Recent empirical work, however, challenges this assumption. Smit et al. (2024) show that multi-agent debate does not reliably outperform self-consistency and ensembling on math and reasoning benchmarks. Zhang et al. (2025) systematically evaluate five debate methods across nine benchmarks and four models, finding that debate fails to outperform Chain-of-Thought and Self-Consistency at matched compute. Most strikingly, Choi et al. (2025) prove that debate induces a *martingale* over agents' belief trajectories — the debate mechanism itself does not improve expected correctness, and majority voting alone accounts for most gains attributed to multi-agent debate.

These findings share a limitation: they evaluate debate on **convergent** tasks with single correct answers — mathematical reasoning, factual question answering, and logical deduction. Applied evaluation domains present a fundamentally different challenge. In ML methodology review, the task is **divergent**: identify *all* flaws in a research methodology, not converge on a single right answer. Whether debate's adversarial structure helps or hurts in this regime is an open empirical question that cannot be resolved by extrapolation from convergent benchmarks.

We address this gap with a controlled experiment comparing six conditions on 120 ML methodology review cases with planted ground-truth flaws, scored by GPT-4o (breaking the closed-loop confound of same-model evaluation). Our contributions are:

1. **Compute-matched comparison.** At 3x baseline compute, three independent critics with union-of-issues pooling formally outperform structured debate (critic + defender + adjudicator). Debate is not significantly different from a 1x baseline (CI spans zero), meaning the adversarial structure spends 3x compute to achieve no measurable benefit on methodology review.

2. **Convergent/divergent task-type interaction.** We observe that the same experimental setup produces opposite patterns depending on task type. On divergent detection (find all flaws), ensemble dominates. On convergent judgment (assess empirical testability of ambiguous cases), multi-round debate produces correct ambiguity recognition at 36.7% versus 0% for baseline — a capability structurally absent from independent sampling. We propose this as a post-hoc framework for reconciling conflicting results in the debate literature; the mixed-case comparison is descriptive (the formal test remains inconclusive at n = 40).

3. **Union-of-issues pooling with precision validation.** We invert Wang et al.'s (2023) majority-vote aggregation for detection tasks and validate that minority-flagged findings (raised by only 1 of 3 assessors) carry equal precision to unanimously flagged findings (0.946 vs. 0.929, p = 0.258, n = 1,463 issue clusters), recovering +9.5 percentage points of recall at no measured precision cost.

---

## 2. Related Work

### Multi-Agent Debate

The debate paradigm for LLMs originates with Irving et al. (2018), who proposed adversarial debate as a scalable oversight mechanism. Du et al. (2024) demonstrated that multiple LLM instances debating over rounds improve mathematical and strategic reasoning. Liang et al. (2024) introduced multi-agent debate to address Degeneration-of-Thought, where LLMs lose the ability to generate novel thoughts after establishing confidence.

However, a growing body of work finds debate underperforms simpler alternatives. Smit et al. (2024) show at ICML that debate does not reliably beat self-consistency. Zhang et al. (2025) broaden this to five debate methods across nine benchmarks, concluding that model heterogeneity — not adversarial structure — drives multi-agent gains. Choi et al. (2025), in a NeurIPS spotlight, provide theoretical grounding: debate is a martingale, and voting/pooling accounts for most performance gains. Kaesberg et al. (2025) find that more discussion rounds *hurt* reasoning tasks through "problem drift." Wu et al. (2025) identify intrinsic reasoning strength and group diversity as the dominant factors, with majority pressure suppressing independent correction.

La Malfa et al. (2025) argue that current multi-agent LLM implementations lack genuine multi-agent characteristics — autonomy, structured environments, and social interaction. Parrish et al. (2022) provide an early negative result in a different modality: two-turn debate does not help humans answer hard reading comprehension questions.

Critically, Kenton et al. (2024) show debate robustly outperforms consultancy (a 1x-compute alternative) across all tasks. This is consistent with our finding: debate wins uncontrolled comparisons against lower-compute baselines but loses the compute-matched comparison. The compute-matching control is what changes the conclusion.

### LLM-Based Scientific Review

AgentReview (Jin et al., 2024) simulates peer review with LLM agents, finding 37.1% variation in decisions due to reviewer biases. LimitGen (Xu et al., 2025) establishes that current LLMs struggle with scientific limitation identification. DeepReview (2025) uses a multi-stage retrieval-and-argumentation pipeline. ReViewGraph (Li et al., 2025) encodes reviewer-author debates as heterogeneous graphs. None of these include compute-matched ensemble baselines or planted ground-truth methodology flaws.

### Self-Consistency and Ensemble Methods

Wang et al. (2023) introduce self-consistency: sample diverse reasoning paths, then select the most consistent answer via majority vote. This is **convergent** aggregation — multiple paths to a single answer. Our ensemble design inverts this for **divergent** detection: we take the *union* of all findings across assessors, crediting any issue found by any assessor. The aggregation direction is the key structural difference.

### Evaluation Bias

Zheng et al. (2023) establish the LLM-as-judge paradigm with MT-Bench, documenting position bias, verbosity bias, and self-enhancement bias. Panickssery et al. (2024) sharpen this to self-preference bias specifically — LLM evaluators recognize and favor their own generations. Prior work in our experimental series measured a cross-vendor IDR delta of -0.7737 when comparing Claude-scoring-Claude against GPT-4o-mini-scoring-Claude on identical outputs, confirming the closed-loop confound is severe in methodology review. This motivated our use of GPT-4o as the primary scorer for all semantic dimensions.

### Sycophancy and Conformity in Debate

Wynn et al. (2025) demonstrate that debate corrupts correct answers through sycophancy and social conformity — models shift from correct to incorrect even when stronger models outnumber weaker ones. Saunders et al. (2022) show models are better at discriminating quality than articulating critiques (the generator-discriminator-critique framework), suggesting the discrimination-critique gap may be asymmetric. These mechanisms are relevant to our finding that debate's defender argues away valid critiques that single-pass review would flag.

---

## 3. Method

### 3.1 Benchmark Design

We constructed a benchmark of 120 ML methodology review cases in three categories:

- **Critique cases (n = 60):** Each case presents an ML methodology with 1-5 planted flaws. Ground truth includes `must_find` issues (flaws the reviewer must identify), `acceptable_resolutions`, and `correct_position = critique_wins`.
- **Mixed cases (n = 40):** Cases where the methodology is empirically ambiguous — the correct resolution is `empirical_test_agreed`, requiring the reviewer to recognize that a definitive verdict cannot be reached without further evidence.
- **Defense cases (n = 20):** Cases with valid methodology where the correct verdict is `defense_wins` — the reviewer should identify no critical flaws.

Of the 80 regular cases (critique + defense), 25 are derived from real ReScience C reproducibility papers (2020-2021 editions) and 55 are synthetically generated with planted corruptions. The benchmark underwent five prior calibration rounds (v1-v5) that progressively increased difficulty and addressed scoring artifacts.

### 3.2 Conditions

We evaluate six conditions at varying compute budgets:

| Condition | Architecture | Compute |
|---|---|---|
| **baseline** | Single-pass critic | 1x |
| **isolated_debate** | Critic -> Defender -> Adjudicator | 3x |
| **ensemble_3x** | 3 independent critics (no cross-visibility) | 3x |
| **biased_debate** | Persona-biased critic -> Defender -> Adjudicator | 3x |
| **multiround** | Iterative critic-defender exchange (2+ rounds) | 3x+ |
| **conditional_fm** | Gate-controlled multiround (stops if round 1 resolves issues) | variable |

The critical comparison is **isolated_debate** vs. **ensemble_3x**: both use approximately 3x baseline compute, but the structural difference is complete. Isolated debate routes compute through adversarial exchange (critic argues with defender, adjudicator synthesizes). Ensemble routes compute through independent redundancy (three critics assess independently, with no cross-assessor visibility). Conditional_fm is a variant of multiround with an early-stopping gate; its results are reported in Appendix A.3 and excluded from the main results tables as it is functionally equivalent to multiround (the gate fires on 94.7% of cases).

### 3.3 Scoring

All outputs are scored by GPT-4o via OpenRouter, breaking the closed-loop confound of same-model evaluation. Scoring spans five dimensions:

- **IDR (Issue Detection Recall):** Fraction of planted `must_find` issues correctly identified.
- **IDP (Issue Detection Precision):** Fraction of flagged issues that are valid (not false positives). For debate conditions, IDP_adj reflects adjudicator-filtered precision.
- **DRQ (Design Resolution Quality):** Quality of the reviewer's design-level recommendations.
- **FVC (Finding-Verdict Consistency):** Alignment between identified issues and the overall verdict.
- **ETD (Empirical Test Design):** Quality of proposed empirical tests (mixed cases only).

**Fair Comparison (FC)** is the per-case mean of IDR, IDP_adj, DRQ, and FVC (ETD excluded for regular cases). Each case-condition pair is scored across 3 independent runs. All confidence intervals use paired bootstrap on case-level differences (n = 10,000 resamples, seed = 42).

**Ensemble aggregation** uses a split rule: **union** for IDR (credit if *any* assessor found the issue, maximizing recall) and **majority vote** for verdict dimensions (2-of-3 agreement, preserving verdict precision). This asymmetry is intentional: the most recall-favorable rule for recall metrics, and the most conservative rule for verdict metrics. IDP for ensemble conditions reports the mean per-assessor precision (each assessor's precision averaged across runs and assessors); it was not explicitly assigned to either aggregation rule in the design documents — the high value (0.9861) reflects baseline-style assessors' low false-positive rate rather than an aggregation effect. The separate tier-level precision analysis in Section 5.4 uses a different method (GPT-4o cluster classification) and produces a pooled precision of 0.939, consistent with including novel-but-unplanted findings in the denominator.

### 3.4 Cross-Vendor Scoring Motivation

In the preceding experimental series (v5), we measured a cross-vendor IDR delta of -0.7737 between Claude scoring its own outputs and GPT-4o-mini scoring the same outputs. This is substantially larger than self-preference effects reported in the general literature (Panickssery et al., 2024) and likely reflects domain-specific amplification: in methodology review, critic and scorer share systematic biases about what constitutes a valid concern. All v6 semantic scoring uses GPT-4o to eliminate this confound.

---

## 4. Results

### 4.1 Main Results

Table 1 presents per-condition means across 80 regular cases (60 critique + 20 defense). All debate conditions use 3 runs per case.

**Table 1: Main results on regular cases (n = 80)**

| Condition | IDR | IDP_adj | DRQ | FVC | FC |
|---|---|---|---|---|---|
| baseline | 0.6712 | 0.9472 | 0.75 | 0.75 | 0.6785 |
| isolated_debate | 0.6603 | 0.9639 | 0.75 | 0.75 | 0.6759 |
| **ensemble_3x** | **0.7717** | **0.9861** | **0.75** | **0.75** | **0.7046** |
| biased_debate | 0.6955 | 0.9250 | 0.75 | 0.75 | 0.6726 |
| multiround | 0.6523 | 0.9750 | 0.6917 | 0.6917 | 0.6676 |

*Note: multiround uses variable compute (3x+, typically 2 full rounds), exceeding the 3x budget of isolated_debate and ensemble_3x. Direct comparison between multiround and the 3x conditions is not compute-matched.*

Ensemble_3x achieves the highest IDR (0.7717) and IDP_adj (0.9861) of all conditions. The IDR advantage over isolated_debate (+0.1114) is the largest single-dimension effect in the experiment. DRQ and FVC are flat at 0.75 across all non-multiround conditions, contributing no signal to the FC comparison — the effective discrimination rests on IDR and IDP. The 0.75 values are a composition artifact: critique cases (n = 60) score DRQ = FVC = 1.0 while defense cases (n = 20) score 0.0, and the 60:20 ratio produces the aggregate. Multiround's lower DRQ/FVC (0.6917) reflects cases where its verdict flipped incorrectly.

*Note: IDP_adj equals IDP for non-debate conditions (baseline, ensemble_3x), which have no adjudicator stage.*

### 4.2 Hypothesis Tests

**Table 2a: Pre-registered hypothesis tests (paired bootstrap, n = 10,000, seed = 42, regular cases n = 80, mixed cases n = 40)**

| Test | Comparison | Delta | 95% CI | Verdict |
|---|---|---|---|---|
| H1a | debate vs. baseline (FC, regular) | -0.0026 | [-0.0108, +0.0059] | NOT SIGNIFICANT |
| H1b | debate vs. baseline (FVC, mixed) | +0.0083 | [0.0, 0.025] | FAIL |
| H2 | debate vs. ensemble (FC, regular) | -0.0287 | [-0.0434, -0.0154] | **FAIL (ensemble superior)** |

**Table 2b: Post-hoc follow-up test (paired bootstrap, n = 10,000, seed = 42, critique cases n = 60)**

| Test | Comparison | Delta | 95% CI | Verdict |
|---|---|---|---|---|
| Ens > Base† | ensemble vs. baseline (IDR) | +0.1005 | [+0.0426, +0.1648] | **PASS** |

†*Post-hoc test on critique cases only (n = 60), not part of the pre-registered hypothesis battery. Conducted after H2 established ensemble superiority, to test whether the advantage extends to the ensemble-vs-baseline comparison on IDR specifically.*

The three-way ordering is: `ensemble_3x > {baseline ≈ isolated_debate}`. The H2 CI excludes zero entirely in the ensemble-favored direction. Debate spends 3x compute to achieve a result not significantly different from the 1x baseline; ensemble spends the same 3x and formally outperforms both.

**Multiple comparisons.** The pre-registered battery includes 8 tests (H1a, H1b, H2 regular, H2 mixed, H3, H4, H6 across 3 dimensions). We report uncorrected CIs throughout. Under Bonferroni correction at the 8-test level (α = 0.05/8 = 0.00625), the primary results are unaffected: the null findings (H1a, H1b) remain non-significant, and H2 regular (CI fully excluding zero) and H6 FVC_mixed (p = 0.0000) both survive correction. The post-hoc ensemble-vs-baseline test (Table 2b) is reported separately and should be interpreted with the additional test noted.

### 4.3 Mixed-Case Results

**Table 3: Finding-verdict consistency on mixed cases (FVC_mixed)**

| Condition | FVC_mixed |
|---|---|
| baseline | 0.0 |
| isolated_debate | 0.0083 |
| ensemble_3x | 0.025 |
| biased_debate | 0.25 |
| **multiround** | **0.3667** |

On mixed cases, the ranking inverts. Baseline and ensemble score near zero — they produce binary verdicts without recognizing empirical ambiguity. Multiround achieves FVC_mixed = 0.3667, meaning iterative adversarial exchange produces the correct `empirical_test_agreed` resolution in approximately 37% of mixed cases. Biased debate is second at 0.25. This capability is structurally absent from independent sampling: each ensemble assessor makes a binary verdict, and no amount of majority voting across binary verdicts can produce an ambiguity-recognition resolution.

### 4.4 Persona-Biasing Effects

Persona-biasing (biased_debate vs. isolated_debate) produces a formally significant effect on two of three tested dimensions, but in opposite directions:

- **FVC_mixed:** +0.2417, CI [+0.1583, +0.3417] — biased debate substantially improves mixed-case verdict quality
- **IDP_adj:** -0.0389, CI [-0.0722, -0.0083] — biased debate statistically degrades adjudicated precision

The aggressive-critic persona generates more false claims (IDP_raw = 0.8917, the lowest of all conditions), and the adjudicator does not fully recover them (IDP_adj = 0.9250 vs. 0.9639 for isolated_debate). Persona-biasing trades precision for mixed-case verdict quality — a domain-specific tradeoff, not a uniform improvement.

---

## 5. Analysis

### 5.1 Convergent vs. Divergent Task-Type Interaction

The results reveal a task-type interaction that explains the apparent contradiction between our findings and prior work reporting debate benefits:

- **Divergent detection** (find all methodology flaws): Ensemble dominates. IDR_ensemble = 0.7717 vs. IDR_baseline = 0.6712, a formally significant advantage (CI [+0.0426, +0.1648]). Isolated debate IDR (0.6603) is directionally *lower* than baseline, consistent with Wynn et al.'s (2025) finding that debate corrupts correct assessments through sycophancy — the defender argues away valid critiques that a single-pass reviewer would have flagged.

- **Convergent judgment** (assess empirical testability): Debate dominates. Multiround FVC_mixed = 0.3667 vs. baseline/ensemble near zero. Iterative exchange is structurally necessary for agents to recognize that a methodology is empirically ambiguous — neither clearly flawed nor clearly sound. This cannot emerge from independent sampling over binary verdicts.

We note that this convergent/divergent distinction is a post-hoc interpretive framework consistent with the data, not a pre-registered contrast. The pattern is suggestive and reconciles the debate literature, but should be tested prospectively. Du et al.'s (2024) math tasks and ChatEval's (Chan et al., 2024) evaluation tasks are convergent — debate helps agents converge on correct answers. The methodology flaw detection in our benchmark is divergent — debate's adversarial pressure suppresses independent discovery. The key variable is whether the goal is to find one right answer (convergent) or to find all problems (divergent).

### 5.2 Dimension Decomposition

The ensemble IDR advantage over isolated_debate (+0.1114) is 4x larger than the FC composite difference (+0.0287). Three of four FC dimensions show minimal or no separation: DRQ and FVC are flat at 0.75 for all non-multiround conditions, and IDP contributes only +0.0417. The IDR signal is diluted when averaged with non-discriminating dimensions. This suggests that for detection-prioritized evaluation, IDR should be reported as a primary metric alongside composite scores, as composites can obscure large effects on the dimension that matters most.

### 5.3 Ecological Validity: RC Subgroup Analysis

Stratifying the 80 regular cases by source reveals that the ensemble advantage is strongest on the hardest, most ecologically valid cases.

**Table 4: IDR by case source**

| Subset | n | IDR_ensemble | IDR_baseline | Delta |
|---|---|---|---|---|
| Real papers (ReScience C) | 25 | 0.4545 | 0.2828 | +0.172 |
| Synthetic | 55 | 0.9553 | 0.8961 | +0.059 |

The ensemble advantage is approximately 3x larger on real papers than on synthetic cases. Baseline IDR on real papers is only 0.283 — well below ceiling — leaving substantial room for the ensemble's union pooling to recover additional ground-truth flaws. On synthetic cases, baseline is already near ceiling (0.896), compressing the improvement margin. The aggregate IDR advantage (+0.1005) understates the benefit in the deployment context that matters most.

### 5.4 Union Pooling: Precision Validation

A concern with union-of-issues pooling is that minority-flagged findings (raised by only 1 of 3 assessors) might be disproportionately false positives. We tested this directly using GPT-4o to classify 1,463 deduplicated issue clusters from 180 case-run pairs.

**Table 5: Precision by assessor support tier (1,463 issue clusters)**

| Tier | N clusters | Precision | 95% CI | FP rate |
|---|---|---|---|---|
| 1/3 (minority) | 715 | 0.946 | [0.926, 0.963] | 0.054 |
| 2/3 (majority) | 327 | 0.936 | [0.903, 0.965] | 0.064 |
| 3/3 (unanimous) | 421 | 0.929 | [0.881, 0.969] | 0.071 |

Precision difference (1/3 - 3/3): +0.017, 95% CI [-0.028, +0.068], p = 0.258. The CI includes zero — there is no significant precision difference across support tiers. Minority-flagged issues are not less precise than unanimous issues. The slight positive direction (+0.017) is consistent with a plausible mechanism: assessors who catch unique issues tend to be more specific, while unanimous issues include more generic observations.

Union pooling recovers 11 ground-truth issues (9.5% of the 116-issue `must_find` pool) that would be discarded by majority vote — all 11 verified true positives. The recall gain is +9.5 percentage points (union IDR 77.6% vs. majority-vote IDR 68.1%) at no measured precision cost.

**Data quality note.** The precision analysis relies on GPT-4o's classification of issue clusters across assessors. In 108 of 180 case-runs (60%), GPT-4o merged at least one issue across assessors without preserving the original label — typically Assessor C's 5th issue was folded into an earlier cluster. These issues were classified (planted_match, false_claim, etc.) but excluded from tier counts because tier assignment requires an assessor label. Since the label omission is uniform across classification types and assessors, it is unlikely to introduce systematic bias across tiers. However, the precision estimates in Table 5 should be interpreted with this caveat: a 60% missing-label rate means the effective sample of fully-labeled clusters is smaller than the 1,463 reported, and a systematic relationship between label omission and precision — though not observed — cannot be ruled out.

### 5.5 Defense Case Failure

On the 20 defense cases (correct verdict: `defense_wins`), baseline, isolated_debate, ensemble_3x, and biased_debate each produce 0/60 correct verdicts — a uniform failure. Every critic, regardless of condition, identifies flaws in valid work and never concludes `defense_wins`. Multiround is the only condition to produce any correct defense verdicts: 12/60 individual runs (20%) across 9 of 20 cases, but with high within-case variance (no case achieves unanimous correct verdicts across 3 runs). Conditional_fm was not evaluated on defense cases (it was added to the experimental matrix for the multiround-gate analysis in H3, which tested only regular cases).

This connects to Saunders et al.'s (2022) generator-discriminator-critique framework: if the discrimination-critique gap is asymmetric — models find it easier to articulate criticism than to articulate validation — then LLM critics may be structurally incapable of exoneration regardless of protocol design. The defense-case failure is a structural gap in current LLM evaluation capabilities, not a protocol-specific shortcoming.

**Implication for FC interpretation.** Because all non-multiround conditions score DRQ = FVC = 0.0 uniformly on defense cases and DRQ = FVC = 1.0 uniformly on critique cases, the 20 defense cases contribute identical values across conditions. The between-condition FC comparison on 80 regular cases is effectively driven by the 60 critique cases — specifically by IDR and IDP on those cases, since DRQ and FVC are flat. Reporting FC on critique cases alone (n = 60) as a robustness check yields a larger and more interpretable effect size, since it eliminates the compositional artifact from defense-case zeros.

---

## 6. Discussion

For designers of LLM-based evaluation systems, our results suggest a practical heuristic: use independent ensembles with union pooling for divergent detection tasks (audits, reviews, flaw-finding), and reserve adversarial debate for convergent judgment tasks where the question is whether evidence is sufficient rather than whether flaws exist. The convergent/divergent distinction, if confirmed prospectively, would provide actionable guidance that extends beyond our specific domain.

The compute-matching control is the key methodological contribution. Debate robustly outperforms lower-compute alternatives — consistent with Kenton et al.'s (2024) finding. But the same compute spent on independent redundancy outperforms debate for detection. Heterogeneous ensembles (e.g., Claude + GPT-4o + Gemini as independent critics) might yield further gains — Zhang et al. (2025) show model heterogeneity significantly improves multi-agent outcomes. Testing heterogeneous ensemble variants is a natural extension.

---

## Limitations

**Single-vendor agents.** All debate agents (critic, defender, adjudicator) and all ensemble assessors use Claude. Scoring is cross-vendor (GPT-4o), eliminating same-model evaluation bias, but the agent population itself is homogeneous. Zhang et al. (2025) show that model heterogeneity (Heter-MAD) significantly improves multi-agent outcomes — debate dynamics may differ with heterogeneous agent populations, and heterogeneous ensembles may yield further IDR gains.

**Multiround variance.** Multiround produces the highest FVC_mixed (0.3667) but also the highest within-case variance: 20 of 23 high-variance case-condition pairs in the experiment are multiround. The same case can flip between FC = 0.0 and FC = 1.0 across runs. Temperature reduction or structured stopping criteria are required before multiround is deployment-ready.

**ETD metric ceiling.** ETD = 1.0 for 100% of debate outputs — the metric measures presence of empirical-test structure, not its quality. This limits our ability to quantify *quality* of mixed-case reasoning. A sub-element rubric (specificity, falsifiability, orthogonality) is needed.

**Defense cases.** The 0/60 failure for baseline, isolated_debate, ensemble_3x, and biased_debate (and 12/60 with high variance for multiround alone) limits conclusions about debate's full diagnostic scope. A critic prompt that includes a "no significant issues found" output path would change this constraint.

**Benchmark scale.** 120 cases is moderate for the primary comparisons but underpowered for subgroup analyses. The RC subgroup (n = 25) provides suggestive evidence that the ensemble advantage is largest on real papers, but formal testing at this sample size is not possible. Only 15 of 80 regular cases have difficulty labels, leaving difficulty-stratified analysis chronically underpowered.

**Equivalence testing.** The H1a non-significance result (debate vs. baseline CI spans zero) demonstrates failure to reject the null, not formal equivalence. A TOST (Two One-Sided Tests) procedure with a pre-specified equivalence bound would be needed to formally claim the two conditions are equivalent. The narrow CI ([−0.0108, +0.0059]) is suggestive but not dispositive.

---

## 7. Conclusion

We present a controlled comparison of adversarial debate and independent ensemble methods for LLM-based ML methodology review. Three findings emerge:

First, at matched compute, independent redundancy outperforms adversarial structure. Three independent critics with union-of-issues pooling achieve formally superior issue detection recall (IDR +0.1114 over debate, +0.1005 over baseline) and composite score (FC CI [+0.0154, +0.0434]) compared to structured debate, while debate is not significantly different from single-pass baseline (CI spans zero). The adversarial mechanism spends 3x compute for no measurable benefit on divergent detection.

Second, the data suggest a task-type interaction that warrants prospective testing. Debate's only measurable advantage is on convergent judgment — recognizing empirical ambiguity in mixed cases (FVC_mixed = 0.3667 vs. baseline 0.0), a capability structurally absent from ensemble sampling. However, the formal debate-vs-ensemble test on mixed cases remains inconclusive (CI spans zero, n = 40). We propose a convergent/divergent framework as a post-hoc hypothesis that, if confirmed, would reconcile conflicting findings in the debate literature — debate helps on convergent reasoning benchmarks (Du et al., 2024) but fails on our divergent detection task.

Third, union-of-issues pooling shows no significant precision penalty. Minority-flagged findings are not significantly less precise than unanimous findings (0.946 vs. 0.929, p = 0.258), recovering +9.5 percentage points of recall with no measured precision difference across support tiers. This inverts Wang et al.'s (2023) majority-vote self-consistency for detection tasks, providing a validated aggregation strategy for any LLM-based system where the goal is comprehensive issue identification.

The central insight is that the compute-matching control changes the conclusion. Debate robustly outperforms lower-compute alternatives — consistent with Kenton et al.'s (2024) finding that debate beats consultancy. But when the same compute is spent on independent redundancy, the adversarial structure provides no additional benefit for detection. **Additional compute helps; debate structure does not — for divergent tasks.** Recognizing this task-type dependency is essential for the principled deployment of multi-agent LLM systems.

---

## References

Chan, C.-M. et al. (2024). ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate. *ICLR 2024.* arXiv:2308.07201.

Choi, H.K., Zhu, X., & Li, S. (2025). Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models? *NeurIPS 2025 Spotlight.* arXiv:2508.17536.

DeepReview (2025). DeepReview: Improving LLM-based Paper Review with Human-like Deep Thinking Process. *ACL 2025.* arXiv:2503.08569.

Du, Y., Li, S., Torralba, A., Tenenbaum, J.B., & Mordatch, I. (2024). Improving Factuality and Reasoning in Language Models through Multiagent Debate. *ICML 2024.* arXiv:2305.14325.

Irving, G., Christiano, P., & Amodei, D. (2018). AI Safety via Debate. arXiv:1805.00899.

Jin, Y. et al. (2024). AgentReview: Exploring Peer Review Dynamics with LLM Agents. *EMNLP 2024.* arXiv:2406.12708.

Kaesberg, L. et al. (2025). Voting or Consensus? Decision-Making in Multi-Agent Debate. *ACL Findings 2025.* arXiv:2502.19130.

Kenton, Z. et al. (2024). On Scalable Oversight with Weak LLMs Judging Strong LLMs. *NeurIPS 2024.* arXiv:2407.04622.

La Malfa, E. et al. (2025). Large Language Models Miss the Multi-Agent Mark. *NeurIPS 2025 Position Paper.* arXiv:2505.21298.

Li, S. et al. (2025). Automatic Paper Reviewing with Heterogeneous Graph Reasoning over LLM-Simulated Reviewer-Author Debates. *AAAI 2026.* arXiv:2511.08317.

Liang, T. et al. (2024). Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate (MAD). *EMNLP 2024.* arXiv:2305.19118.

Panickssery, A., Bowman, S.R., & Feng, S. (2024). LLM Evaluators Recognize and Favor Their Own Generations. *NeurIPS 2024.* arXiv:2404.13076.

Parrish, A. et al. (2022). Two-Turn Debate Doesn't Help Humans Answer Hard Reading Comprehension Questions. *NeurIPS 2022 Workshop on ML Safety.* arXiv:2210.10860.

Saunders, W. et al. (2022). Self-critiquing models for assisting human evaluators. arXiv:2206.05802.

Smit, A.P., Grinsztajn, N., Duckworth, P., Barrett, T.D., & Pretorius, A. (2024). Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs. *ICML 2024.* PMLR 235:45883-45905. arXiv:2311.17371.

Wang, X. et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. *ICLR 2023.* arXiv:2203.11171.

Wu, H. et al. (2025). Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning. arXiv:2511.07784.

Wynn, A., Satija, H., & Hadfield, G. (2025). Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate. *ICML 2025 MAS Workshop.* arXiv:2509.05396.

Xu, Z. et al. (2025). Can LLMs Identify Critical Limitations within Scientific Research? A Systematic Evaluation on AI Research Papers. arXiv:2507.02694.

Zhang, H. et al. (2025). Stop Overvaluing Multi-Agent Debate — We Must Rethink Evaluation and Embrace Model Heterogeneity. arXiv:2502.08788.

Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023.* arXiv:2306.05685.

---

## Appendix A: Additional Tables

### A.1 Full H6 Hypothesis Test (Persona-Biasing)

| Dimension | Delta (biased - isolated) | 95% CI | CI excludes 0? |
|---|---|---|---|
| IDR | +0.0352 | [-0.0093, +0.0787] | No |
| IDP_adj | -0.0389 | [-0.0722, -0.0083] | Yes (negative) |
| FVC_mixed | +0.2417 | [+0.1583, +0.3417] | Yes (positive) |

Verdict: PASS (2/3 dimensions exclude zero), but with mixed direction.

### A.2 Within-Case Variance

23 case-condition pairs exceed the high-variance threshold (FC variance > 0.05). Of these, 20 are multiround. Individual multiround cases can score FC = 0.0 on one run and FC = 1.0 on another, indicating that the multiround mechanism introduces substantial stochasticity.

### A.3 Conditional FM Gate Analysis

The conditional forced-multiround (CFM) gate fires on 94.7% of cases (341/360). Mean point resolution rate (PRR) after round 1 is 0.418; the gate requires PRR = 1.0 to stop. H3 (CFM vs. multiround on hard cases): diff = +0.0313, W = 16.0, p = 0.3677, n_eff = 7 — FAIL. The gate does not function as a selective filter.

---

*Figure placeholders:*

**Figure 1 (suggested).** Bar chart of IDR by condition on regular cases (n = 80). Highlights the ensemble_3x advantage over all other conditions and the near-equivalence of baseline and isolated_debate.

**Figure 2 (suggested).** 2x2 matrix: task type (convergent/divergent) x method (debate/ensemble). Cells contain primary metric and direction of effect. Illustrates the task-type interaction framework.

**Figure 3 (optional).** IDR by condition, stratified by case source (RC real papers vs. synthetic). Shows the ensemble advantage is 3x larger on real papers.
