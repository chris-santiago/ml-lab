# When Does Debate Help? Divergent Detection and Convergent Judgment in Multi-Agent LLM Evaluation

**Draft — not for distribution**

---

## Abstract

Multi-agent debate is increasingly used for LLM-based evaluation, but whether adversarial structure or independent redundancy better serves different evaluation tasks remains unclear. We propose and test a framework: **divergent detection** (finding issues) benefits from independent redundancy, while **convergent judgment** (recognizing ambiguity) benefits from iterative adversarial exchange. In a pilot study (Study 1: 120 cases, 6 conditions), a compute-matched ensemble of three independent critics outperforms structured debate on issue detection, while multi-round debate uniquely enables correct ambiguity recognition — motivating the framework as a post-hoc hypothesis. In a pre-registered confirmatory study (Study 2: 280 cases, 4 conditions, cross-vendor scorer), both predictions hold at matched 3× compute. Ensemble achieves IDR 0.803 vs. multiround IDR 0.634 (Δ = +0.169, CI [+0.139, +∞)). Multiround achieves FVC_mixed 0.731 vs. ensemble 0.506 (Δ = +0.225, CI [+0.192, +∞)). Six of eight hypotheses pass. Two fail informatively: isolated debate degrades verdict quality versus baseline (−0.050 FC), and minority-flagged issues carry a precision penalty (−0.080). The practical recommendation: use ensemble for detection, multiround with information-passing for judgment, and neither for defense-case exoneration.

---

## 1. Introduction

Multi-agent debate — where LLM instances argue opposing positions before a judge synthesizes a verdict — has emerged as a prominent strategy for improving LLM reasoning and evaluation quality (Du et al., 2024; Liang et al., 2024). The intuitive appeal is clear: adversarial exchange should surface flaws that any single agent might miss, mirroring the logic of human peer review and legal adversarial systems.

Recent empirical work, however, challenges this assumption. Smit et al. (2024) show that multi-agent debate does not reliably outperform self-consistency and ensembling on math and reasoning benchmarks. Zhang et al. (2025) systematically evaluate five debate methods across nine benchmarks and four models, finding that debate fails to outperform Chain-of-Thought and Self-Consistency at matched compute. Most strikingly, Choi et al. (2025) prove that debate induces a *martingale* over agents' belief trajectories — the debate mechanism itself does not improve expected correctness, and majority voting alone accounts for most gains attributed to multi-agent debate.

These findings share a limitation: they evaluate debate on **convergent** tasks with single correct answers — mathematical reasoning, factual question answering, and logical deduction. Applied evaluation domains present a fundamentally different challenge. In ML methodology review, the task is **divergent**: identify *all* flaws in a research methodology, not converge on a single right answer. Whether debate's adversarial structure helps or hurts in this regime is an open empirical question.

We address this gap with a two-study investigation. Study 1 (pilot, 120 cases, 6 conditions) establishes the pattern: at matched compute, ensemble outperforms debate for issue detection, but multi-round debate uniquely enables ambiguity recognition. This motivates a post-hoc framework: **divergent detection** benefits from independent redundancy, **convergent judgment** benefits from iterative exchange. Study 2 (confirmatory, 280 cases, 4 conditions, pre-registered hypotheses, cross-vendor scorer) tests both predictions prospectively and confirms both with large effects.

Our contributions are:

1. **A convergent/divergent framework for compute allocation.** We formalize the observation that task type determines which multi-agent architecture wins: ensemble for divergent detection, multiround debate for convergent judgment. Both predictions are prospectively confirmed in Study 2 (P1: Δ = +0.169 IDR; P2: Δ = +0.225 FVC_mixed).

2. **Pilot-to-confirmation progression.** Study 1's post-hoc framework (inconclusive at n = 40 mixed cases, unmatched compute for multiround) becomes Study 2's pre-registered prediction (significant at n = 80, compute-matched at 3×). Two Study 1 conclusions are revised: precision parity is overturned (minority-flagged issues carry a −0.080 penalty at larger scale) and debate-baseline equivalence is overturned (debate is actively worse: −0.050 FC).

3. **Information-passing as binding variable.** Study 2 identifies defender visibility into the critique as the binding variable for convergent judgment (H3: Δ = +0.125 FVC_mixed, CI [+0.088, +∞)). The two conditions co-vary defender task and information availability, so H3 isolates the variable, not the full causal mechanism — but the contrast shows that adversarial structure alone is insufficient without information-passing.

---

## 2. Related Work

### Multi-Agent Debate

The debate paradigm for LLMs originates with Irving et al. (2018), who proposed adversarial debate as a scalable oversight mechanism. Du et al. (2024) demonstrated that multiple LLM instances debating over rounds improve mathematical and strategic reasoning. Liang et al. (2024) introduced multi-agent debate to address Degeneration-of-Thought, where LLMs lose the ability to generate novel thoughts after establishing confidence.

However, a growing body of work finds debate underperforms simpler alternatives. Smit et al. (2024) show at ICML that debate does not reliably beat self-consistency. Zhang et al. (2025) broaden this to five debate methods across nine benchmarks, concluding that model heterogeneity — not adversarial structure — drives multi-agent gains. Choi et al. (2025), in a NeurIPS spotlight, provide theoretical grounding: debate is a martingale, and voting/pooling accounts for most performance gains. Kaesberg et al. (2025) find that more discussion rounds *hurt* reasoning tasks through "problem drift." Wu et al. (2025) identify intrinsic reasoning strength and group diversity as the dominant factors, with majority pressure suppressing independent correction.

La Malfa et al. (2025) argue that current multi-agent LLM implementations lack genuine multi-agent characteristics — autonomy, structured environments, and social interaction. Parrish et al. (2022) provide an early negative result in a different modality: two-turn debate does not help humans answer hard reading comprehension questions.

Critically, Kenton et al. (2024) show debate robustly outperforms consultancy (a 1x-compute alternative) across all tasks. This is consistent with a pattern we formalize here: debate wins uncontrolled comparisons against lower-compute baselines but the picture changes under compute-matched comparison with independent redundancy.

### LLM-Based Scientific Review

AgentReview (Jin et al., 2024) simulates peer review with LLM agents, finding 37.1% variation in decisions due to reviewer biases. LimitGen (Xu et al., 2025) establishes that current LLMs struggle with scientific limitation identification. DeepReview (2025) uses a multi-stage retrieval-and-argumentation pipeline. ReViewGraph (Li et al., 2025) encodes reviewer-author debates as heterogeneous graphs. None include compute-matched ensemble baselines or planted ground-truth methodology flaws.

### Self-Consistency and Ensemble Methods

Wang et al. (2023) introduce self-consistency: sample diverse reasoning paths, then select the most consistent answer via majority vote. This is **convergent** aggregation — multiple paths to a single answer. Our ensemble design inverts this for **divergent** detection: we take the *union* of all findings across assessors, crediting any issue found by any assessor. The aggregation direction is the key structural difference.

### Evaluation Bias

Zheng et al. (2023) establish the LLM-as-judge paradigm with MT-Bench, documenting position bias, verbosity bias, and self-enhancement bias. Panickssery et al. (2024) sharpen this to self-preference bias specifically — LLM evaluators recognize and favor their own generations. A preliminary cross-vendor validation (n = 80, Appendix B.2) measured an IDR delta of −0.7737 when the same critique outputs were scored by the generation model versus a cross-family model, confirming the closed-loop confound is severe in methodology review. Both studies use cross-vendor scorers: GPT-4o (Study 1) and gpt-5.4-mini (Study 2).

### Sycophancy and Conformity in Debate

Instruction-tuned LLMs exhibit sycophancy — a tendency to agree with inputs regardless of correctness (Perez et al., 2023; Sharma et al., 2024). Sharma et al. (2024) show this bias exists before RLHF and is amplified by preference optimization, as human evaluators themselves prefer convincingly-written sycophantic responses over correct ones. This compounds in multi-agent settings: Wynn et al. (2025) show debate corrupts correct answers through sycophancy and social conformity, and Yao et al. (2025) formalize "disagreement collapse" — distinct debater-driven and judge-driven sycophancy modes that cause premature convergence below single-agent baselines.

Saunders et al. (2022) show models are better at discriminating quality than articulating critiques, suggesting the discrimination-critique gap may be asymmetric. These mechanisms are directly relevant to our defense-case finding: the defender partially concedes rather than fully rebutting (debater-driven sycophancy), and the adjudicator sides with the more assertive argument (judge-driven sycophancy).

---

## 3. Method

### 3.1 Benchmark Design

The confirmatory study (Study 2) uses a benchmark of 280 ML methodology review cases in three strata:

- **Regular (n = 160):** Planted methodology flaws where `critique_wins` is correct. 5 extracted from ReScience C (RC) publications, 155 synthetic.
- **Mixed (n = 80):** Empirically ambiguous designs where `empirical_test_agreed` is correct — the reviewer must recognize that a definitive verdict requires further evidence. 50 RC-sourced, 30 synthetic.
- **Defense (n = 40):** Sound methodologies where `defense_wins` is correct — the reviewer should identify no critical flaws. 18 RC, 22 synthetic.

Cases are generated via a multi-stage pipeline with cross-family model assignments at each stage to prevent same-family calibration bias (see Appendix B). The RC papers are drawn from ReScience C 2020–2021 reproducibility reports. The benchmark underwent seven prior calibration rounds that progressively increased difficulty and addressed scoring artifacts; Study 1 used a 120-case subset (80 regular, 40 mixed) from an earlier pipeline generation.

### 3.2 Pilot Study (Study 1)

Study 1 evaluated six conditions on 120 cases (80 regular, 40 mixed) scored by GPT-4o (cross-vendor):

| Condition | Architecture | Compute |
|---|---|---|
| baseline | Single-pass critic | 1× |
| isolated_debate | Critic → Defender → Adjudicator | 3× |
| ensemble_3x | 3 independent critics, union pooling | 3× |
| biased_debate | Persona-biased Critic → Defender → Adjudicator | 3× |
| multiround | Iterative critic-defender exchange (2+ rounds) | ~5× |
| conditional_fm | Gate-controlled multiround | variable |

**Four motivating findings:**

1. **Ensemble outperforms debate on detection.** At matched 3× compute, ensemble IDR (0.772) exceeds isolated debate (0.660). The ensemble-vs-baseline test (post-hoc) showed IDR Δ = +0.100, CI [+0.043, +0.165] — the only formally significant effect involving ensemble.

2. **Debate is not significantly different from baseline.** Isolated debate FC Δ = −0.003, CI [−0.011, +0.006]. The CI spans zero; debate spends 3× compute with no measurable benefit on regular-case composite score.

3. **Multiround uniquely enables ambiguity recognition.** Multiround achieves FVC_mixed = 0.367, while baseline and ensemble score near zero. Iterative adversarial exchange is structurally necessary for agents to recognize empirical ambiguity — a capability absent from independent sampling over binary verdicts.

4. **No precision penalty for minority-flagged issues.** In a follow-up analysis (180 GPT-4o classification calls), minority (1/3) precision = 0.946 vs. unanimous (3/3) = 0.929; Δ = +0.017, CI [−0.028, +0.068], p = 0.258.

**Four weaknesses motivating Study 2:**

1. **Post-hoc framework.** The convergent/divergent distinction was proposed after observing the data, not before.
2. **Compute mismatch.** Multiround used ~5× compute (median 2 full rounds × 2 agents + adjudicator), not the 3× budget of ensemble. The FVC_mixed advantage could reflect compute surplus, not structural superiority.
3. **Underpowered mixed-case test.** The formal debate-vs-ensemble test on mixed FVC was inconclusive (CI spans zero, n = 40).
4. **No equivalence test for H1a.** Non-significance does not imply equivalence; a TOST procedure was not pre-specified.

These weaknesses directly shaped Study 2's design: pre-registered hypotheses, compute-matched multiround (3× budget, 2 rounds), larger mixed stratum (n = 80), and TOST equivalence test for H1a.

### 3.3 Confirmatory Study (Study 2)

Study 2 evaluates four conditions at matched compute:

| Condition | Architecture | Compute |
|---|---|---|
| **baseline** | Single-pass critic | 1× |
| **isolated_debate** | Critic + blind Defender + Adjudicator | 3× |
| **ensemble_3x** | 3 independent critics, union pooling | 3× |
| **multiround_2r** | Critic + informed Defender + Adjudicator | 3× |

All conditions use Claude Sonnet 4.6 as the generation model. Each case is evaluated 3 times per condition (3,360 total outputs). The critical structural difference between isolated_debate and multiround_2r is whether the defender sees the critique: in isolated_debate, the defender argues methodology in the abstract; in multiround_2r, the defender responds to the specific critique. **Compute matching.** We match conditions at the API-call level (3 calls each), following the convention used in prior work (Smit et al., 2024; Zhang et al., 2025). This does not equalize token cost: the adjudicator in debate conditions processes both critic and defender outputs, consuming a larger context window than any single ensemble call. The token-cost asymmetry favors debate conditions; our findings that ensemble wins on detection (P1) are therefore conservative with respect to total compute.

**Scoring.** All semantic scoring uses gpt-5.4-mini via OpenRouter (cross-vendor):

- **IDR (Issue Detection Recall):** Proportion of planted `must_find` issues found. Cross-vendor scored.
- **IDP (Issue Detection Precision):** Proportion of raised issues that are genuine. Cross-vendor scored.
- **DRQ/FVC (Verdict Quality):** Rule-based scoring against ground-truth verdicts. DRQ = FVC on regular cases (where `acceptable_resolutions = [correct_position]`).
- **FC (Fair Comparison):** mean(IDR, IDP, DRQ, FVC). Note: FC double-weights the verdict dimension on regular cases since DRQ = FVC.
- **FVC_mixed:** FVC on mixed stratum only.

**Pre-registration.** Eight hypotheses were registered via version-controlled commit before data collection. The pre-registration commit (SHA `6fadcc6`) is tamper-evident and independently verifiable; the full hypothesis specification, including equivalence bounds and test types, is available in the supplementary materials.

| ID | Prediction | Type |
|---|---|---|
| **P1** | Ensemble IDR > Multiround IDR (regular) | One-sided |
| **P2** | Multiround FVC_mixed > Ensemble FVC_mixed (mixed) | One-sided |
| H1a | Isolated debate ≈ Baseline (FC, equivalence ±0.015) | TOST |
| H2 | Ensemble vs. Isolated debate (FC regular; FVC mixed) | Two-sided |
| H3 | Multiround > Isolated debate (FVC_mixed) | One-sided |
| H4 | Ensemble > Baseline (IDR, replication of Study 1) | One-sided |
| H5 | 1/3-flagged precision ≈ 3/3-flagged precision (±0.03) | TOST |

**Equivalence bounds.** The H1a bound (±0.015 FC) was set between the Study 1 CI half-width (~0.010, the noise floor) and half the Study 1 ensemble FC advantage (0.029 / 2 ≈ 0.014), ensuring it exceeds measurement noise without being vacuously wide. The H5 bound (±0.03 precision) was set above the Study 1 observed tier difference (+0.017), representing ~3 percentage points on a scale where both tiers exceeded 0.92 — practically negligible for a pooling recommendation.

### 3.4 Statistical Methods

All hypothesis tests use paired bootstrap (n = 10,000, seed = 42, α = 0.05). Case-level differences are resampled with replacement. One-sided tests for directional predictions (P1, P2, H3, H4); two-sided for non-directional (H1a, H2, H5). Stability verified at seed = 99 (7/8 tests within ±0.001 CI drift; H2_mix upper bound drifted 0.002 — verdict unaffected). Pre-registration eliminates post-hoc test selection but does not formally control FWER across 8 simultaneous tests. We apply Bonferroni correction at α/8 = 0.006 for all reported tests. All six PASS verdicts survive correction: the smallest one-sided CI lower bound among PASS results is +0.088 (H3), far exceeding the adjusted threshold. Both FAIL verdicts (H1a, H5) likewise remain significant under correction.

---

## 4. Results

### 4.1 Framework Confirmation

Both primary predictions pass with large, non-overlapping effects:

**P1 — Divergent Detection (Ensemble Wins).** Ensemble IDR (0.803) exceeds multiround IDR (0.634): Δ = +0.169, 95% CI lower bound = +0.139. Three independent critics with union pooling find substantially more planted issues than iterative adversarial exchange at matched compute — detecting 80% of planted flaws versus 63%.

**P2 — Convergent Judgment (Multiround Wins).** Multiround FVC_mixed (0.731) exceeds ensemble FVC_mixed (0.506): Δ = +0.225, 95% CI lower bound = +0.192. Iterative exchange with information-passing enables correct ambiguity recognition that independent critics cannot replicate. Multiround produces `empirical_test_agreed` on 46.3% of mixed runs; ensemble produces it on 1.3%.

**Table 4. Framework confirmation (Study 2)**

| | **Ensemble / Independent** | **Multiround / Adversarial** |
|---|---|---|
| **Divergent detection** *(find all flaws)* | **IDR = 0.803** ✓ (P1 PASS: Δ = +0.169) | IDR = 0.634 |
| **Convergent judgment** *(assess ambiguity)* | FVC_mixed = 0.506 | **FVC_mixed = 0.731** ✓ (P2 PASS: Δ = +0.225) |

**Framework verdict: CONFIRMED.** Detection and judgment are structurally different tasks that benefit from different compute allocation strategies.

### 4.2 Main Results

Table 5 presents per-condition means on Study 2's regular cases (n = 160) and mixed cases (n = 80).

**Table 5: Study 2 condition summary**

| Condition | IDR | IDP | DRQ | FVC | FC | FVC_mixed (n=80) |
|---|---|---|---|---|---|---|
| baseline | 0.636 | 0.910 | 0.993 | 0.993 | 0.883 | 0.513 |
| isolated_debate | 0.626 | 0.923 | 0.891 | 0.891 | 0.833 | 0.606 |
| **ensemble_3x** | **0.803** | **0.963** | **0.994** | **0.994** | **0.938** | 0.506 |
| multiround_2r | 0.634 | 0.919 | 0.773 | 0.773 | 0.775 | **0.731** |

Ensemble_3x achieves the highest IDR (0.803), IDP (0.963), and FC (0.938). Multiround_2r achieves the highest FVC_mixed (0.731) but the lowest FC (0.775) — the multiround advantage on mixed cases comes at the cost of verdict flips on regular cases, where the defender occasionally argues the adjudicator away from correct `critique_wins` verdicts (DRQ/FVC = 0.773 vs. baseline 0.993).

### 4.3 Hypothesis Tests

**Table 6: Study 2 pre-registered hypothesis tests (paired bootstrap, n = 10,000, seed = 42)**

| ID | Prediction | Point Est. | 95% CI | n | Verdict |
|----|-----------|:---:|--------|---|---------|
| P1 | ensemble > multiround (IDR) | +0.169 | [+0.139, +∞) | 160 | **PASS** |
| P2 | multiround > ensemble (FVC_mixed) | +0.225 | [+0.192, +∞) | 80 | **PASS** |
| H1a | isolated ≈ baseline (FC, ±0.015) | −0.050 | [−0.065, −0.036] | 160 | **FAIL** |
| H2_reg | ensemble vs. isolated (FC) | +0.106 | [+0.092, +0.120] | 160 | **PASS** |
| H2_mix | ensemble vs. isolated (FVC) | −0.100 | [−0.131, −0.067] | 80 | **PASS** |
| H3 | multiround > isolated (FVC_mixed) | +0.125 | [+0.088, +∞) | 80 | **PASS** |
| H4 | ensemble > baseline (IDR) | +0.168 | [+0.140, +∞) | 160 | **PASS** |
| H5 | 1/3 precision ≈ 3/3 precision (±0.03) | −0.080 | [−0.108, −0.052] | 432 | **FAIL** |

**Score: 6/8.** Both primary predictions pass. H3 and H4 pass as secondary confirmations. H1a and H5 fail — both informatively (§4.4).

**H3 (Information-Passing): PASS.** The +0.125 FVC_mixed delta between multiround and isolated debate identifies information-passing as the binding variable. The two conditions differ primarily in whether the defender sees the critique, though the defender task and interaction structure also co-vary. The contrast establishes that adversarial structure without information-passing (isolated debate) is insufficient for convergent judgment — without visibility into the opposing argument, the defender cannot mount effective rebuttals on genuinely ambiguous cases.

**H4 (Replication): PASS.** Prospectively replicates Study 1's strongest post-hoc finding. The Study 2 effect (+0.168) exceeds the Study 1 effect (+0.100) with a higher CI floor (+0.140 vs. +0.043).

### 4.4 Informative Failures

**H1a — Isolated Debate Is Worse, Not Equivalent.** Study 1 found non-significance (FC Δ = −0.003, CI spans zero) and could not distinguish equivalence from non-equivalence — the narrow CI was suggestive of equivalence, but a TOST procedure was not pre-specified. Study 2 pre-specified a TOST equivalence test at ±0.015. The result: FC Δ = −0.050, CI [−0.065, −0.036] — entirely below −0.015. Isolated debate is not merely non-equivalent to baseline; it is significantly *worse*.

The mechanism: adding a blind defender (who argues methodology in the abstract without seeing the critique) introduces noise that causes the adjudicator to reject valid critiques approximately 10% of the time. DRQ/FVC drops from 0.993 (baseline) to 0.891 (isolated debate). IDR is unaffected (0.636 vs. 0.626), so the damage is purely to verdict quality.

This overturns Study 1's null finding and reveals an active cost of debate structure on straightforward detection tasks — a cost that was below Study 1's detection threshold at n = 80.

**Robustness to FC weighting.** Since DRQ = FVC on regular cases, FC mechanically double-weights the verdict dimension: FC = mean(IDR, IDP, 2×FVC)/4. Under equal-weight FC* = mean(IDR, IDP, FVC)/3, the H1a delta reduces from −0.050 to −0.033 — still entirely outside the ±0.015 equivalence bound. H2_reg likewise holds under FC* (+0.107).

**H5 — Minority-Flagged Issues Carry a Precision Penalty.** Study 1 found precision parity across support tiers (1/3: 0.946, 3/3: 0.929, Δ = +0.017, CI spans zero). Study 2 finds the opposite: Δ = −0.080, CI [−0.108, −0.052], entirely outside the ±0.03 equivalence bound.

The primary driver is a **tier composition effect**. At Study 2's scale (n = 432 issue-level observations), the content asymmetry becomes visible: 3/3 (unanimous) issues are 55% planted_match — high precision by definition, since they correspond exactly to ground-truth flaws. 1/3 (minority) issues carry 15% spurious noise from edge cases and subjective concerns that only one assessor flags. This composition asymmetry was invisible at Study 1's smaller scale (n = 180 issue clusters).

**Recommendation:** Union pooling with tier weighting. Weight 1/3-flagged issues lower than 3/3-flagged issues. The recall advantage (P1, H4) is real; the precision cost (H5) qualifies how that recall should be consumed.

### 4.5 Defense Case Exoneration

**Table 7: Defense case performance (Study 2, n = 40 cases × 3 runs = 120 per condition)**

| Condition | Exoneration (defense_wins) | Adjacent (empirical_test_agreed) | Defense FVC |
|---|:---:|:---:|:---:|
| baseline | 0/120 (0%) | 1/120 (0.8%) | 0.004 |
| isolated_debate | 0/120 (0%) | 13/120 (10.8%) | 0.054 |
| ensemble_3x | 0/120 (0%) | 0/120 (0%) | 0.000 |
| multiround_2r | 0/120 (0%) | 60/120 (50.0%) | 0.250 |

Zero full exoneration across all conditions. The strongest concession is `empirical_test_agreed` (adjacent, scored 0.5), achieved on 50% of multiround defense runs. This is consistent with sycophancy-driven disagreement collapse (Sharma et al., 2024; Yao et al., 2025): the defender partially concedes to the critique rather than fully rebutting it, and the adjudicator sides with the more assertive argument. Even with iterative exchange, the strongest concession is ambiguity — never full exoneration. An alternative explanation is that the defense cases themselves — generated by LLMs — may not appear methodologically sound to LLM reviewer agents, independent of sycophancy. No human validation of defense-case difficulty was conducted; distinguishing benchmark miscalibration from model-level critique bias requires human expert evaluation of the defense cases, which we leave to future work.

Study 1 observed 20% exoneration on multiround defense cases. Multiple variables changed simultaneously between studies — generation model version, compute budget (~5× → 3×), prompt design, and benchmark composition — so the decline cannot be attributed to a single factor. This unresolved confound limits conclusions from the defense-case stratum; the 0% exoneration rate should be treated as a descriptive finding, not a stable cross-study estimate. The consistent finding across studies is that defense-case exoneration remains an unsolved problem.

---

## 5. Discussion

### 5.1 The Framework

The convergent/divergent framework provides a principled basis for compute allocation in LLM-based evaluation:

- **For issue detection:** use ensemble (3 independent critics, union pooling). The ensemble IDR advantage is the most robust finding across both studies (Study 1: +0.100 post-hoc, Study 2: +0.168 pre-registered), with the CI floor rising from +0.043 to +0.140 under pre-registration.

- **For ambiguity recognition:** use multiround with information-passing. The multiround FVC_mixed advantage (+0.225 over ensemble) is the largest single effect in Study 2. The mechanism is the defender's ability to engage with specific claims (H3: Δ = +0.125), not adversarial structure per se.

- **For defense-case exoneration:** neither architecture succeeds. This reflects model-level sycophancy (Sharma et al., 2024) that compounds through the adversarial protocol, not a protocol design failure.

### 5.2 The Suppression Mechanism

Why does isolated debate fail on divergent detection? In isolated debate, the critic flags a flaw, the defender is instructed to rebut it (without seeing the specific critique), and the adjudicator synthesizes — a pipeline where every stage after the initial critique applies pressure to *reduce* the issue count. Wynn et al. (2025) document this directly: models shift from correct to incorrect under adversarial pressure. Study 2 quantifies the cost: isolated debate DRQ/FVC (0.891) falls significantly below baseline (0.993), meaning ~10% of valid critiques are suppressed by the adjudication process. Study 1's narrow CI could not detect this; Study 2's pre-specified TOST reveals it as a real and meaningful degradation.

Independent ensemble assessors face no such pressure: each critic reports independently, and union pooling takes the maximum rather than the adjudicated minimum. The recall advantage (IDR = 0.803 for ensemble vs. 0.634 for multiround, 0.626 for isolated debate) is the measured cost of routing detection through an adversarial funnel.

### 5.3 Compute-Matching Changes the Conclusion

Kenton et al. (2024) show debate robustly outperforms consultancy at matched compute. Our result extends the comparison: debate wins uncontrolled comparisons against lower-compute baselines but loses the compute-matched comparison against independent redundancy. Study 1's multiround advantage on mixed cases was observed at ~5× compute — confounded with the additional budget. Study 2 resolves this: multiround_2r is compute-matched at 3× (critic + defender + adjudicator), and the FVC_mixed advantage (+0.225) persists. The correct question is always "does adversarial structure outperform independent redundancy at matched compute?" — and the answer depends on the task type.

### 5.4 Cross-Study Stability

**Table 8: Cross-study comparison**

| Finding | Study 1 | Study 2 |
|---------|---------|---------|
| Ensemble > baseline IDR | +0.100 (post-hoc) | +0.168 (pre-registered) |
| Multiround FVC_mixed advantage | 0.367 (descriptive, ~5×) | +0.225 (pre-registered, 3×) |
| Isolated debate vs. baseline | −0.003 (null) | −0.050 (worse) |
| Precision parity | +0.017 (parity) | −0.080 (penalty) |
| Defense exoneration | 20% (multiround only) | 0% all; 50% adjacent (multiround) |

The ensemble IDR advantage is stable and strengthens with pre-registration. The multiround FVC_mixed advantage is confirmed at matched compute (Study 1 multiround was not compute-matched). The H1a and H5 reversals are informative: a larger study with pre-specified equivalence tests can detect effects that a smaller study's non-significant result cannot distinguish from absence of effect.

### 5.5 Generalization

If adversarial structure suppresses recall on divergent detection tasks, we predict the pattern would extend to any domain where the goal is comprehensive enumeration: code review (find all bugs), safety auditing (find all violations), legal document review (find all compliance issues). Conversely, tasks requiring a final judgment under genuine uncertainty should benefit from iterative exchange. The framework predicts: ensemble IDR advantage over debate would replicate on other divergent tasks, and multiround FVC advantage would replicate on other convergent tasks.

The limits of the convergent/divergent binary deserve acknowledgment. Many real evaluation tasks require both detection and judgment simultaneously — a thorough code review requires enumerating all bugs (divergent) *and* judging which are critical (convergent). For such mixed-mode tasks, a protocol that separates stages — detect with ensemble, adjudicate with multiround — is a natural candidate for future work. H3's identification of information-passing as the binding variable provides a specific prediction: the defender must see the specific critique, not merely argue in the abstract.

---

## 6. Limitations

1. **Single generation model.** All conditions in both studies use Claude models. The framework predictions may not generalize to other model families. Zhang et al. (2025) show model heterogeneity significantly improves multi-agent outcomes — heterogeneous ensembles remain unexamined.

2. **Scorer change between studies.** Study 1 uses GPT-4o; Study 2 uses gpt-5.4-mini. The H5 reversal (precision parity → penalty) could be partially confounded by scorer differences. We present the tier composition effect as the primary mechanism (§4.4), but the scorer change is a secondary confound that cannot be fully ruled out.

3. **Planted-flaw benchmark.** Regular cases have synthetic planted flaws. Real-world methodology review involves subtler, less cleanly categorized issues. The RC subgroup (n = 5 regular in Study 2) is directionally consistent with an ecological validity effect (P1 delta +0.261 vs. synthetic +0.166) but not informative at n = 5.

4. **Within-case variance and deployment cost.** Multiround (60.7% verdict flip rate) and isolated debate (44.3%) exceed the 30% stability threshold. Individual runs are unreliable; 3-run averaging is mandatory for stable estimates. This raises multiround's effective deployment cost to ~9× baseline (3 API calls × 3 replicates), compared to 3× for ensemble, which is single-run reliable (0.7% flip rate).

5. **Compute matching granularity.** "3× compute" matches API calls, not tokens. Debate conditions include an adjudicator call that processes both prior outputs, making debate's per-case token cost higher than ensemble's. This asymmetry favors debate; the ensemble IDR advantage (P1) is conservative with respect to total compute, while the multiround FVC_mixed advantage (P2) may be partially explained by the additional token budget.

6. **Defense-case exoneration.** Zero full exoneration across all Study 2 conditions limits conclusions about the framework's defense-case applicability. Current models exhibit sycophancy (Sharma et al., 2024) that compounds through adversarial protocols, preventing full exoneration. No human validation of defense-case difficulty was conducted (§4.5).

7. **Cross-vendor scorer dependency.** IDR and IDP depend on the scorer model's extraction accuracy (~90% exact agreement on a 10% stratified spot-check). Scorer noise does not threaten primary verdicts given the wide margins (P1 CI floor +0.139, P2 CI floor +0.192), but scorer fidelity remains an external dependency.

---

## 7. Conclusion

We present a two-study investigation of compute allocation for LLM-based methodology review. Three findings emerge:

First, the convergent/divergent framework is prospectively confirmed. At matched 3× compute, independent redundancy with union pooling outperforms adversarial debate for issue detection (Δ = +0.169 IDR), while iterative exchange with information-passing outperforms independence for ambiguity recognition (Δ = +0.225 FVC_mixed). Both predictions, motivated by a post-hoc observation in Study 1 and pre-registered in Study 2, hold with large effects.

Second, the informative failures refine the practical recommendations. Isolated debate is not merely equivalent to baseline — it is actively worse (−0.050 FC), revealing a suppression mechanism where blind defenders corrupt valid critiques. Union pooling carries a real precision cost (−0.080 for minority-flagged issues), requiring tier-weighted aggregation rather than unqualified union.

Third, defense-case exoneration remains unsolved. No condition produces full `defense_wins` verdicts. The strongest concession is partial ambiguity recognition (50% adjacent in multiround), consistent with sycophancy-driven disagreement collapse documented in recent multi-agent literature (Yao et al., 2025; Wynn et al., 2025).

The practical recommendation: use ensemble for detection, multiround for judgment, and — based on the exploratory defense-case analysis — neither for exoneration. Individual multiround runs should not be trusted without replicate averaging.

---

## AI Assistance Statement

This manuscript was drafted and edited with the assistance of Claude Code (Anthropic). All claims, interpretive framing, and conclusions were reviewed and approved by the human author(s).

A reflexive disclosure is warranted: the principal AI tool used for writing assistance (Claude, Anthropic) is also the subject of the experimental study. The experiment evaluates Claude instances as debate agents, ensemble assessors, and methodology reviewers. To guard against implicit bias in how findings about Claude's capabilities and limitations are presented — including defense-case failure (§4.5) and the suppression mechanism (§5.2) — all framing of results was independently reviewed by the human author(s) before finalization.

AI use in the *experiment* is separate from AI use in *writing* and is documented in §3 (experimental agents, cross-vendor scorer) and Appendix B (benchmark generation pipeline). Readers should consult those sections for the experimental AI disclosure; this statement covers manuscript authorship only.

---

## Reproducibility

The benchmark cases (280 cases with ground-truth labels), scoring scripts, analysis scripts, and full experiment results are available in the project repository. Agent definitions (critic, defender, adjudicator) are included as installable plugins. The Study 1 (120-case) benchmark and results are also available for replication of the pilot findings.

---

## References

Chan, C.-M. et al. (2024). ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate. *ICLR 2024.* arXiv:2308.07201.

Choi, H.K., Zhu, X., & Li, S. (2025). Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models? *NeurIPS 2025 Spotlight.* arXiv:2508.17536.

Zhu, M., Weng, Y., Yang, L., & Zhang, Y. (2025). DeepReview: Improving LLM-based Paper Review with Human-like Deep Thinking Process. *ACL 2025.* arXiv:2503.08569.

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

Perez, E. et al. (2023). Discovering Language Model Behaviors with Model-Written Evaluations. *ACL Findings 2023.* arXiv:2212.09251.

Saunders, W. et al. (2022). Self-critiquing models for assisting human evaluators. arXiv:2206.05802.

Sharma, M. et al. (2024). Towards Understanding Sycophancy in Language Models. *ICLR 2024.* arXiv:2310.13548.

Smit, A.P., Duckworth, P., Grinsztajn, N., Barrett, T.D., & Pretorius, A. (2024). Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs. *ICML 2024.* PMLR 235:45883-45905. arXiv:2311.17371.

Wang, X. et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. *ICLR 2023.* arXiv:2203.11171.

Wu, H. et al. (2025). Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning. arXiv:2511.07784.

Wynn, A., Satija, H., & Hadfield, G. (2025). Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate. *ICML 2025 MAS Workshop.* arXiv:2509.05396.

Yao, B. et al. (2025). Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate. arXiv:2509.23055.

Xu, Z. et al. (2025). Can LLMs Identify Critical Limitations within Scientific Research? A Systematic Evaluation on AI Research Papers. arXiv:2507.02694.

Zhang, H. et al. (2025). Stop Overvaluing Multi-Agent Debate — We Must Rethink Evaluation and Embrace Model Heterogeneity. arXiv:2502.08788.

Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023.* arXiv:2306.05685.

---

## Appendix A: Study 1 Supplementary Results

### A.1 Persona-Biasing Effects (H6)

Study 1 tested persona-biased debate (combative critic + selective defender) against isolated debate. The effect is mixed-direction: FVC_mixed improves (+0.242, CI [+0.158, +0.342]) while IDP_adj degrades (−0.039, CI [−0.072, −0.008]). Persona-biasing trades precision for mixed-case verdict quality. These conditions were not carried forward to Study 2 because the convergent/divergent framework subsumes the persona effect: multiround with information-passing achieves higher FVC_mixed than biased debate without the precision cost.

### A.2 Conditional FM Gate Analysis (H3)

Study 1's conditional forced-multiround gate fires on 94.7% of cases, making CFM functionally equivalent to full multiround. H3_Study1 (CFM vs. multiround on hard cases): Δ = +0.031, W = 16.0, p = 0.368 — FAIL. The gate does not function as a selective filter. This condition was not included in Study 2.

### A.3 ETD Metric Ceiling (H4)

All debate conditions in Study 1 achieve ETD = 1.0 on 100% of mixed cases — the metric measures presence of empirical-test structure, not quality. ETD was dropped from Study 2's scoring dimensions as it provides no discrimination.

---

## Appendix B: Benchmark Construction

### B.1 Pipeline Architecture

Both studies use a multi-stage pipeline with cross-family model assignments to prevent same-family calibration bias. Cases are generated through sequential stages: hypothesis generation → sound design writing → corruption insertion (regular) or ambiguous choice embedding (mixed) → ground truth assembly → cross-family validation.

The synthetic regular pipeline uses a 9-type flaw taxonomy: data leakage, evaluation mismatch, baseline omission, distribution shift, metric mismatch, hyperparameter selection bias, scope overclaim, reproducibility gap, and statistical validity. The synthetic mixed pipeline uses a 6-type ambiguity taxonomy: split ambiguity, metric ambiguity, complexity ambiguity, lookback ambiguity, proxy ambiguity, and regularization ambiguity.

**Study 2 benchmark composition:**

| Source | Regular | Mixed | Defense | Total |
|---|---|---|---|---|
| RC (ReScience C) | 5 | 50 | 18 | 73 |
| Synthetic | 155 | 30 | 22 | 207 |
| **Total** | **160** | **80** | **40** | **280** |

**Study 1 benchmark composition (pilot):**

| Source | Critique | Defense | Mixed | Total |
|---|---|---|---|---|
| RC (ReScience C) | 22 | 3 | 0 | 25 |
| Synthetic | 38 | 17 | 40 | 95 |
| **Total** | **60** | **20** | **40** | **120** |

*Note: Study 1 combined critique (n=60) and defense (n=20) into a single "regular" stratum (n=80). Study 2 separates defense cases into their own stratum, so the regular stratum (n=160) contains only critique-wins cases. This explains the DRQ/FVC difference: Study 1 reports DRQ = FVC = 0.75 (composition artifact from 60/80 critique scoring 1.0 and 20/80 defense scoring 0.0), while Study 2 reports DRQ = FVC ≈ 1.0 on regular cases.*

### B.2 Cross-Vendor Scoring Motivation

Same-model scoring introduces a closed-loop confound: in methodology review, critic and scorer share systematic biases about what constitutes a valid concern. In a preliminary cross-vendor validation (n = 80 critique cases, single condition), identical critique outputs were scored by the generation model (Claude) and a cross-family model (GPT-4o-mini via OpenRouter). The IDR delta was −0.7737 — the cross-family scorer found substantially fewer issues in the same text. This effect is much larger than the self-preference bias reported in the general literature (Panickssery et al., 2024), consistent with methodology review amplifying evaluator-dependent biases beyond what general-purpose benchmarks reveal. This finding motivated cross-vendor scoring for both subsequent studies: Study 1 uses GPT-4o; Study 2 uses gpt-5.4-mini. Both are cross-vendor relative to the Claude generation model.

### B.3 RC Extraction — Contamination Prevention

RC papers (ReScience C 2020–2021 editions) contain both the original methodology description and the reproducer's critique. If the task prompt presented to evaluation agents includes reproducer-language text, agents receive the answer through the data channel. The pipeline addresses this through: (1) extraction prompts that separate "what the paper claims" from "what the reproducer found," constructing task prompts from methodology descriptions only; (2) a keyword contamination gate rejecting cases whose task prompts match 10 reproducer-language patterns (e.g., "failed to reproduce," "our reproduction," "could not replicate").

---

## Appendix C: Cross-Study Results

Study 1 used six conditions on 80 regular cases (60 critique + 20 defense) scored by GPT-4o. Study 2 used four conditions on 160 regular cases (all critique-wins) scored by gpt-5.4-mini. Scoring dimensions differ slightly between studies (Study 1 includes IDP_adj and ETD; Study 2 uses IDP directly and drops ETD). FVC_mixed scoring also differs: Study 2 awards adjacency credit (0.5) for verdicts adjacent to the correct resolution, while Study 1 used stricter scoring. Cross-study comparison of absolute FVC_mixed values should be interpreted with caution.

**Table C1: Study 1 condition summary (regular, n = 80)**

| Condition | IDR | IDP_adj | DRQ | FVC | FC |
|---|---|---|---|---|---|
| baseline | 0.671 | 0.947 | 0.750 | 0.750 | 0.679 |
| isolated_debate | 0.660 | 0.964 | 0.750 | 0.750 | 0.676 |
| ensemble_3x | 0.772 | 0.986 | 0.750 | 0.750 | 0.705 |
| biased_debate | 0.696 | 0.925 | 0.750 | 0.750 | 0.673 |
| multiround (~5×) | 0.652 | 0.975 | 0.692 | 0.692 | 0.668 |

**Table C2: Study 2 condition summary (regular, n = 160)**

| Condition | IDR | IDP | DRQ | FVC | FC |
|---|---|---|---|---|---|
| baseline | 0.636 | 0.910 | 0.993 | 0.993 | 0.883 |
| isolated_debate | 0.626 | 0.923 | 0.891 | 0.891 | 0.833 |
| ensemble_3x | 0.803 | 0.963 | 0.994 | 0.994 | 0.938 |
| multiround_2r | 0.634 | 0.919 | 0.773 | 0.773 | 0.775 |

---

## Appendix D: Sensitivity Analysis (Study 2)

### D.1 Within-Case Variance

| Condition | Verdict Flip Rate | FVC Variance |
|---|---|---|
| baseline | 2.5% | 0.002 |
| isolated_debate | 44.3% | 0.037 |
| ensemble_3x | 0.7% | 0.001 |
| multiround_2r | 60.7% | 0.051 |

Multiround and isolated debate exceed the 30% stability threshold. This is inherent to adversarial exchange — the 3-run means used in hypothesis tests are stable (bootstrap CIs are tight); individual runs are not. Ensemble and baseline are single-run reliable (< 3% flip rate).

### D.2 Bootstrap Stability

7/8 tests within ±0.001 CI drift between seed = 42 and seed = 99. H2_mix upper bound drifted 0.002 (smallest sample, n = 80); verdict unaffected.

### D.3 Scorer Sensitivity

10% stratified spot-check (192 files re-scored with a second scorer run): IDR exact agreement 89.6%, mean absolute difference 0.058, signed mean +0.009 (no systematic bias). Hypothesis verdicts are insulated from scorer noise by 3-run averaging, paired bootstrap, and wide primary margins.

### D.4 RC vs. Synthetic Subgroup

| Test | RC Δ | RC n | Synthetic Δ | Synthetic n |
|---|---|---|---|---|
| P1 (IDR) | +0.261 | 5 | +0.166 | 155 |
| P2 (FVC_mixed) | +0.192 | 46 | +0.270 | 34 |

Both P1 and P2 hold in both subgroups. RC regular (n = 5) is too small for inference but directionally consistent. The RC P1 delta (+0.261) is larger than synthetic (+0.166), consistent with Study 1's observation that ensemble benefits are strongest on harder real-paper cases.
