# Self-Debate Protocol v2: Technical Report

> **Document status (2026-04-05):** This report reflects the experimental protocol as originally designed. Two sections have been superseded by post-experiment findings:
>
> 1. **Protocol architecture (§1.2):** The "Judge" described here is the ml-lab orchestrator acting in an adjudication role — not a dedicated fourth subagent invocation. The Critic and Defender are separate subagent calls; the Judge function is performed inline by the orchestrating session.
>
> 2. **Defender isolation:** Wherever this report states that the Defender receives "the task scenario only (never the Critic's output)", that is a **benchmark-specific isolation design choice**, not a property of the ml-defender agent in production use. In the standard ml-lab workflow, the Defender receives the Critic's output (CRITIQUE.md) before responding. The benchmark isolates them to make independent convergence meaningful as evidence.
>
> See `self_debate_experiment_v2/REPORT.md` for the current authoritative version.

**Date:** 2026-04-04  
**Experiment:** `self_debate_experiment_v2/`  
**Model:** `claude-sonnet-4-6` (all agent roles)

---

## Abstract

A structured self-debate protocol — in which an independent Critic and Defender each assess an ML reasoning scenario before a Judge adjudicates — is benchmarked against a compute-matched ensemble (three independent assessors plus a synthesizer) and a single-pass baseline across 20 synthetic ML reasoning scenarios with known ground-truth verdicts.

The debate protocol scores **0.970** (19/20 cases pass); the ensemble scores **0.754** (11/20 pass); the single-pass baseline scores **0.384** (0/20 pass). The raw debate–baseline lift of +0.586 is partially attributable to rubric dimensions that structurally penalize the baseline. The honest corrected lift — recomputing with rubric choices that equalize structural differences — is **+0.335 to +0.441**, still 3–4× the pre-registered +0.10 threshold. All three pre-registered benchmark criteria are met.

The debate–ensemble gap (+0.216, p=0.004, r=0.758) isolates what adversarial role structure specifically adds over compute budget alone. Systematic ablations establish that: (1) empirical test design is a prompt-constraint effect portable to any multi-agent configuration; (2) issue detection on standard critique cases is matched by the ensemble at ceiling; (3) the debate's confirmed structural contribution is point-by-point argumentation and, on mixed-position cases, a structural mechanism for resolving genuine disagreement. An internal observation of cleaner exoneration outputs (3/5 clean vs. ensemble 2/4) is directional at n=5 and did not replicate in the external exoneration benchmark. Protocol outputs are effectively deterministic across independent runs for 7/8 cases tested (debate_std=0.0); non-zero variance (std=0.048) appears on mm002, the one genuinely two-sided mixed-position case, where Defender verdict stochasticity affects DC but not IDR, FVC, or Judge verdict. External validation confirms IDR=0.95 on 10 cases from published ML evaluation failures, and 3/3 correct verdicts on peer-reviewed exoneration cases.

---

## 1. Experimental Design

### 1.1 Research Question

Does adversarial role structure — assigning one agent to critique and one to defend before a judge adjudicates — produce measurably better evaluation of ML work than either a single-pass assessment or a compute-matched ensemble of independent assessors? "Better" is operationalized as: more correct verdicts on benchmark cases with known ground-truth answers.

### 1.2 Protocol Architecture

**Three conditions** are compared:

**Debate protocol.** Four sequential agents per case:
1. **Critic** — receives the task scenario only. Produces a structured critique: a list of identified issues with IDs, severity, and root cause.
2. **Defender** — receives the task scenario only (never the Critic's output). Responds point-by-point to each issue ID: concede, rebut, or mark empirically open.
3. **Judge** — receives both the Critic's output and the Defender's response. Adjudicates contested points and assigns a typed verdict: `critique_wins`, `defense_wins`, or `empirical_test_agreed`. For `empirical_test_agreed` cases, the Judge specifies the empirical test with pre-specified success and failure criteria.
4. **Scorer** — receives the Judge's synthesized output and must-find labels in a separate invocation. Applies the rubric.

Critical design choice: Critic and Defender receive **identical task prompts with no shared context**. The Defender never sees the Critique before forming its position. This isolation is what makes disagreement meaningful: when both agents independently identify the same flaw, that is convergent evidence; when they disagree, the contested point requires empirical resolution rather than synthesis of correlated views.

**Compute-matched ensemble.** Three independent assessors each receive only the task prompt. A synthesizer reviews all three outputs and produces a unified verdict. A scorer applies the rubric in a separate invocation. Same total agent calls as the debate protocol; no role differentiation.

**Single-pass baseline.** One agent, one call, the same task prompt. No structure.

### 1.3 Benchmark Construction

Twenty synthetic ML reasoning scenarios across six categories:

| Category | n | Description |
|----------|---|-------------|
| `broken_baseline` | 4 | Evaluation protocol flaws: unequal eval sets, missing CIs, test-set leakage, feature-set confound |
| `metric_mismatch` | 3 | Wrong metric for the claim: accuracy on imbalanced data, offline→online correlation gap, ROUGE-human validity |
| `hidden_confounding` | 4 | Confounders unacknowledged in the ML claim: seasonal effects, treatment-period interaction, self-selection |
| `scope_intent` | 2 | Attribution or generalization claim exceeds what the experiment establishes |
| `defense_wins` | 5 | Methodologically sound work presented under adversarial framing — correct answer is "no issue" |
| `real_world_framing` | 2 | Deployment-context causal claims with confounds not stated in the prompt |

Each case specifies: a task prompt, `correct_position` (critique/defense/mixed), `ideal_resolution` (critique_wins/defense_wins/empirical_test_agreed), and `must_find` — the list of specific issues that must be identified for full credit on IDR.

Cases were authored and independently verified before any agent saw them. Ground-truth labels were fixed before any benchmark run. No case was revised after observing agent performance.

### 1.4 Scoring Rubric

Six dimensions, each scored 0.0 / 0.5 / 1.0 or null (N/A):

| Dimension | Abbreviation | Measures | Applies to |
|-----------|-------------|----------|-----------|
| Issue Discovery Recall | IDR | Did the evaluation find all must-find issues? | All critique/mixed cases |
| Issue Discovery Precision | IDP | Did the evaluation avoid raising invalid concerns? | All critique/mixed cases; redefined for defense_wins (see below) |
| Defense Calibration | DC | Did the protocol reach the correct verdict type? | All 20 cases |
| Debate Resolution Quality | DRQ | Was the resolution appropriately typed and complete? | All 20 cases |
| Empirical Test Diagnosticity | ETD | Was the proposed test specific and falsifiable? | `empirical_test_agreed` cases only |
| Final Verdict Correctness | FVC | Did the final label match the ground-truth ideal resolution? | All 20 cases |

**IDP on defense_wins cases:** The Critic structurally produces claims on every case regardless of whether those claims are valid. Scoring IDP as "fraction of valid claims" is undefined when no claims are valid. IDP is therefore redefined for defense_wins cases as false-premise precision: 1.0 = critic raised zero concerns, 0.5 = critic raised plausible-but-wrong concerns, 0.0 = critic produced an entirely unfounded condemnation. IDR is N/A on defense_wins cases (there are no must-find issues).

**Structural scoring differences between conditions:**
- **DC:** The baseline has no Defender role. DC measures whether the correct verdict was reached *via a defense function*; a single-pass system cannot demonstrate this. DC=0.0 is applied to all baseline cases by design, not as a penalty for poor reasoning.
- **DRQ:** A single-pass system cannot produce a typed resolution from exchange. Baseline DRQ is capped at 0.5. Ensemble DRQ is uncapped (the synthesizer performs a resolution function across independent views).
- **ETD:** N/A when `ideal_resolution` is `critique_wins` or `defense_wins`. Applies to 13 of 20 cases.

**Per-case pass criterion:** `mean(non-null dimensions) ≥ 0.65` AND `all applicable dimensions ≥ 0.5`.

### 1.5 Pre-Registered Pass Criteria

Set before any agent saw a benchmark case:

| Criterion | Threshold |
|-----------|-----------|
| Debate benchmark mean | ≥ 0.65 |
| Debate case pass rate | ≥ 75% (≥ 15/20) |
| Debate lift over baseline | ≥ +0.10 |

---

## 2. Primary Results

### 2.1 Aggregate Scores

| Condition | Mean | Pass count | Pass rate |
|-----------|------|-----------|-----------|
| Debate protocol | **0.970** | **19/20** | **95%** |
| Compute-matched ensemble | 0.754 | 11/20 | 55% |
| Single-pass baseline | 0.384 | 0/20 | 0% |

All three pre-registered criteria are met: debate mean 0.970 ≥ 0.65; pass rate 95% ≥ 75%; lift over baseline (corrected) +0.335–0.441 ≥ +0.10.

### 2.2 Per-Case Scores

| Case | Category | Diff | Debate | Ens. | Base | D-pass | E-pass | B-pass |
|------|----------|------|--------|------|------|--------|--------|--------|
| broken_baseline_001 | BB | easy | 1.000 | 0.833 | 0.667 | ✓ | ✓ | ✗ |
| broken_baseline_002 | BB | med | 1.000 | 0.833 | 0.583 | ✓ | ✓ | ✗ |
| broken_baseline_003 | BB | hard | 1.000 | 0.833 | 0.583 | ✓ | ✓ | ✗ |
| broken_baseline_004 | BB | hard | 1.000 | 0.833 | 0.583 | ✓ | ✓ | ✗ |
| metric_mismatch_001 | MM | easy | 1.000 | 1.000 | 0.600 | ✓ | ✓ | ✗ |
| metric_mismatch_002 | MM | med | 1.000 | 0.000 | 0.667 | ✓ | ✗ | ✗ |
| metric_mismatch_003 | MM | hard | 1.000 | 0.833 | 0.417 | ✓ | ✓ | ✗ |
| hidden_confounding_001 | HC | med | 1.000 | 0.750 | 0.417 | ✓ | ✗ | ✗ |
| hidden_confounding_002 | HC | hard | 1.000 | 0.750 | 0.333 | ✓ | ✗ | ✗ |
| hidden_confounding_003 | HC | med | 1.000 | 0.750 | 0.333 | ✓ | ✗ | ✗ |
| hidden_confounding_004 | HC | hard | 1.000 | 0.667 | 0.417 | ✓ | ✗ | ✗ |
| scope_intent_002 | SI | med | 1.000 | 0.750 | 0.583 | ✓ | ✗ | ✗ |
| scope_intent_003 | SI | hard | 0.900 | 1.000 | 0.500 | ✓ | ✓ | ✗ |
| defense_wins_001 | DW | med | 1.000 | 0.875 | 0.000 | ✓ | ✓ | ✗ |
| defense_wins_002 | DW | med | 1.000 | 0.875 | 0.000 | ✓ | ✓ | ✗ |
| defense_wins_003 | DW | med | 0.833 | 1.000 | 0.000 | ✓ | ✓ | ✗ |
| defense_wins_004 | DW | hard | 1.000 | 0.000 | 0.000 | ✓ | ✗ | ✗ |
| defense_wins_005 | DW | hard | 0.833 | 1.000 | 0.000 | ✓ | ✓ | ✗ |
| real_world_framing_001 | RW | med | 0.833 | 0.750 | 0.583 | ✗ | ✗ | ✗ |
| real_world_framing_002 | RW | hard | 1.000 | 0.750 | 0.417 | ✓ | ✗ | ✗ |

*BB=broken_baseline, MM=metric_mismatch, HC=hidden_confounding, SI=scope_intent, DW=defense_wins, RW=real_world_framing. Diff=difficulty.*

The one debate failure (real_world_framing_001) is a reasoning/label disconnect: the Defender's analysis correctly identified all critical flaws but the verdict label read `defense_wins`. DC=0.0 triggers the floor check failure. A two-pass Defender prompt (analysis pass before verdict selection) resolves this; the fix is applied to `agents/ml-defender.md` and the corrected debate score for this case is 0.967 (pass). The benchmark score reflects the original run.

### 2.3 Lift Decomposition

| Source | Estimated lift contribution |
|--------|---------------------------|
| Structural rubric overrides (DC=0.0, DRQ cap) removed | −0.145 (reduces raw gap to corrected) |
| Compute budget + multi-perspective synthesis | ~+0.37 (floor→ensemble) |
| Adversarial role structure on top of compute | +0.216 (ensemble→debate, p=0.004) |

The +0.37 floor-to-ensemble gap is the dominant effect: more LLM calls and multi-perspective synthesis resolve most critique cases at ceiling. The +0.216 ensemble-to-debate gap is what role separation specifically adds, confirmed statistically. The two effects are additive and separable.

---

## 3. Rubric Design Effects and Honest Lift

The raw debate–baseline lift of +0.586 reflects two structural choices that penalize the baseline for the absence of roles it was never designed to perform.

**DC=0.0 for all baseline cases.** DC (Defense Calibration) measures whether the protocol reached the correct verdict *via a defense function*. The baseline has no Defender. Scoring DC=0.0 correctly captures that the baseline cannot perform defense calibration, but it inflates the apparent gap over what "reasoning quality" alone explains.

**DRQ ≤ 0.5 for all baseline cases.** DRQ (Debate Resolution Quality) measures whether positions were resolved through structured exchange. A single-pass system produces a verdict, not a resolution. The 0.5 cap is accurate but structural.

**Corrected lift range (+0.335 to +0.441).** Recomputing with DC=0.5 (giving the baseline partial credit for reaching the right verdict direction) and DRQ uncapped (scoring baseline DRQ on verdict quality alone):
- Conservative correction (DC=0.5, DRQ fully uncapped): +0.335
- Partial correction (DC=0.5, DRQ proportional): +0.441

Both bounds are 3–4× the pre-registered +0.10 threshold. The honest corrected lift is the appropriate number for comparing reasoning quality across conditions. The raw +0.586 is appropriate only when comparing full structural capability (the protocol's complete functionality vs. a single-pass tool).

---

## 4. What Adversarial Role Structure Specifically Provides

### 4.1 Structured Point-by-Point Argumentation

The Critic/Defender structure requires every identified issue to be addressed explicitly: conceded, rebutted, or flagged as empirically open, using the same issue IDs produced by the Critic. A parallel ensemble synthesizes independent views but cannot produce this structure by design — assessors have no common reference point for disagreement.

This is reflected in DC and DRQ: the debate protocol achieves DC=1.0 and DRQ=1.0 on all correctly-functioning critique cases. The ensemble achieves DC=1.0 on critique cases but DRQ is lower because the synthesizer does not produce a typed resolution from structured exchange. The point-by-point structure is also what generates the typed `empirical_test_agreed` verdict with pre-specified test conditions — though ETD itself is a prompt effect (see §5.2).

### 4.2 Mixed-Position Case Advantage

The most structurally distinctive debate result is `metric_mismatch_002` (correct_position=mixed, ideal_resolution=`empirical_test_agreed`). The task prompt describes a genuine two-sided disagreement: an offline NDCG improvement challenged by a reviewer's concern about offline-online correlation validity. Both positions are defensible.

The ensemble scored 0.000 on this case: all three assessors independently converged on the more intuitive answer (run the A/B test) without engaging with the reviewer's correlation concern. The synthesizer faithfully summarized the consensus. The debate protocol scored 1.000: the Critic raised the offline-online gap, the Defender conceded calibration uncertainty, and both agreed on a calibration study as the first step before A/B testing.

This failure mode is structural: without role differentiation, independent assessors approach the same prompt from the same direction and produce correlated errors. The debate protocol's forced role separation is the mechanism that prevents this.

### 4.3 Exoneration Tendency (Directional, Internal Only)

On the 5 defense_wins cases, the debate protocol's isolated Defender — receiving only the task prompt with no adversarial framing from the Critic — raised zero concerns on 3 of 5 cases (IDP=1.0). The ensemble raised caveats alongside 2 of its 4 correct exonerations (IDP=0.5 on defense_wins_001 and defense_wins_002). The debate raised concerns on the same 2 cases (dw001, dw002), where critics reliably identify superficially plausible methodological gaps.

This distinction is real in the internal benchmark but carries important caveats: (a) n=5 is below conventional statistical thresholds; (b) the mean-score advantage disappears under harmonized scoring — when IDP is excluded for both conditions on defense_wins cases, both the debate and ensemble score 1.0 on DC, DRQ, and FVC for the exonerated cases; (c) the external exoneration benchmark (3 cases from peer-reviewed ML work) found IDP=0.5 on all 3 external cases — critics raised plausible-but-wrong concerns in every case. The pattern of clean, no-caveat exonerations did not replicate externally.

**Appropriate characterization:** The debate's isolated Defender produces structurally independent defenses (no reaction to the Critic's framing), which is a genuine architectural property. Whether this produces meaningfully cleaner outputs in practice is a directional internal observation that the external benchmark does not confirm.

---

## 5. What Adversarial Role Structure Does Not Uniquely Provide

### 5.1 Issue Detection

On the 15 non-defense_wins cases, the compute-matched ensemble matches the debate protocol at ceiling for IDR. All must-find issues in the benchmark are identifiable from ML reasoning applied to the task prompt — no case requires adversarial structure to surface the flaw. The debate protocol's IDR=1.000 reflects benchmark tractability, not a structural reasoning advantage over the ensemble.

This finding implies: when the goal is fault detection and the flaws are within the reasoning capability of the model, compute budget (more assessors, more perspectives) is sufficient. The debate structure adds no IDR advantage on these cases.

### 5.2 Empirical Test Design

The debate protocol achieves ETD=1.0 across all applicable cases. The unconstrained ensemble achieves ETD mean=0.192 on the same 13 cases. This gap has a prompt-constraint explanation: the debate's Judge prompt explicitly instructs test specification with pre-specified success and failure criteria. The ensemble synthesizer was not instructed to do this.

**ETD ablation:** The ensemble synthesizer was re-run on all 13 `empirical_test_agreed` cases with the explicit instruction: *"Specify the empirical test that would resolve the contested issues: (1) what to measure, (2) pre-specified success criterion, (3) pre-specified failure criterion."* Result: **ETD mean = 0.962** (12/13 cases at 1.0; one partial score on `real_world_framing_002` where retrospective test design is genuinely constrained).

**Conclusion:** ETD is an output-constraint effect. The debate protocol reliably produces test specifications because its prompt requires them, not because the adversarial forcing function structurally generates them. The same output is replicable from any multi-agent configuration — ensemble or otherwise — by adding the same constraint to the synthesizer. ETD is portable.

### 5.3 Verdict Correctness on Standard Critique Cases

On the 15 non-defense_wins cases, the ensemble reaches the correct verdict direction on all cases except `metric_mismatch_002` (the mixed-position catastrophic failure described in §4.2). Verdict correctness on standard critique cases is not a debate-specific advantage.

---

## 6. Statistical Analysis

Bootstrap confidence intervals (10,000 resamples, 95% CI) and paired Wilcoxon signed-rank tests on per-case score deltas:

| Comparison | Point estimate | 95% CI | W | p-value | r |
|------------|---------------|--------|---|---------|---|
| Debate vs. baseline | +0.586 | [0.486, 0.691] | 0 | 8.2×10⁻⁵ | 1.000 |
| Debate vs. ensemble | +0.216 | [0.098, 0.352] | 23 | 0.0035 | 0.758 |

The debate–baseline comparison: r=1.0 means the debate outperforms the baseline on every single one of the 20 cases. Zero ties or reversals.

The debate–ensemble comparison: r=0.758 reflects 19 nonzero pairs (one case, `defense_wins_004`, has debate=1.0, ensemble=0.000 — a large positive delta that is not artifactual but reflects the ensemble's catastrophic failure on the hardest defense_wins case).

Bootstrap CIs reflect **cross-case sampling variance only** — variability from which cases happen to be in the benchmark. Within-case LLM stochasticity is estimated separately (see §8.1).

**Dimension-weighted aggregate** (equal weight per applicable dimension, averaged across cases): Debate 0.978, ensemble 0.738, baseline 0.510. Case-weighted and dimension-weighted aggregates are consistent; the case-weighted figures are not materially distorted by any single outlier case.

---

## 7. External Validity

Two external benchmarks address the closed-loop design concern — that benchmark cases, rubric, and agent prompts all originate from the same source.

### 7.1 Fault Detection Benchmark (IDR)

**10 cases** drawn from published ML evaluation failures: Dacrema et al. (2019) on recommendation system replication failures, Obermeyer et al. (2019) on racial bias in clinical algorithms, DeGrave et al. (2021) on chest X-ray model spurious correlations, and additional published cases. Ground truth from the published record — no designer involvement in case selection or label assignment.

**Result:** Debate IDR = **0.95**, meeting the pre-specified ≥ 0.85 threshold. The ensemble was not re-run on these cases; this benchmark specifically validates issue detection. The near-equal baseline performance on these cases (all are critique-type; real-world ML failure benchmarks cannot contain defense_wins cases) is expected — the debate's structural advantages on defense_wins cases are untestable in this format.

### 7.2 Exoneration Benchmark

**3 cases** from peer-reviewed ML work: BERT fine-tuning on SQuAD 1.1 (Devlin et al. 2019), ResNet-152 on ImageNet (He et al. 2016), and stratified 5-fold cross-validation for clinical readmission prediction. Each is a defense_wins-type case: a critique can be raised (scale disparity, depth-shortcut covariation, EPV rule applicability) but the methodology is genuinely sound, with ground truth established by the published record.

| Case | Debate mean | Debate pass | Baseline verdict | Baseline pass |
|------|-------------|-------------|-----------------|---------------|
| BERT/SQuAD 1.1 | 0.875 | ✓ | defense_wins ✓ | ✗ (DC=0.0) |
| ResNet-152/ImageNet | 0.875 | ✓ | defense_wins ✓ | ✗ (DC=0.0) |
| 5-fold CV (clinical) | 0.875 | ✓ | defense_wins ✓ | ✗ (DC=0.0) |

Debate: 3/3 pass (mean 0.875). Baseline: 0/3 rubric pass (DC=0.0 structural rule), 3/3 correct verdict label. The exoneration finding — that the debate protocol correctly resolves defense_wins cases — holds on externally grounded cases.

**IDP observation:** Critics raised plausible-but-wrong concerns on all 3 external cases (IDP=0.5 uniformly): parameter scale disparity for BERT, depth-shortcut interaction for ResNet, EPV rule applicability for the clinical model. No critic raised zero concerns (IDP=1.0). This is consistent with the internal IDP stress test finding (§8.4): critics reliably identify real methodological caveats on valid work, but do not correctly judge their dispositive weight. The "clean exoneration" pattern observed on 3/5 internal defense_wins cases (IDP=1.0) does not replicate externally.

---

## 8. Protocol Robustness

### 8.1 Within-Case Variance

The benchmark scores are point estimates from single protocol runs. Within-case LLM stochasticity — run-to-run variation from re-running the identical protocol on the same case — was estimated across two phases: 5 convergence=1.0 cases (salient, unambiguous flaws) and 3 convergence=0.5 cases (the correct stress test: genuine Critic/Defender verdict divergence in the original run).

**Phase 1 — convergence=1.0 cases** (`within_case_variance_results.json`):

| Case | Debate std | Debate mean | Baseline std | Baseline mean |
|------|------------|-------------|--------------|---------------|
| broken_baseline_001 | 0.0 | 1.000 | 0.0 | 0.750 |
| metric_mismatch_003 | 0.0 | 1.000 | 0.0 | 0.667 |
| hidden_confounding_002 | 0.0 | 1.000 | 0.0 | 0.667 |
| defense_wins_001 | 0.0 | 0.875 | 0.0 | 0.625 |
| real_world_framing_002 | 0.0 | 1.000 | 0.0 | 0.750 |

**Phase 2 — convergence=0.5 cases** (`within_case_variance_nonconverging.json`):

| Case | Debate std | Debate mean | Baseline std | Baseline mean | Note |
|------|------------|-------------|--------------|---------------|------|
| scope_intent_003 | 0.0 | 1.000 | 0.0 | 0.700 | Deterministic despite convergence=0.5 |
| real_world_framing_001 | 0.0 | 0.917 | 0.0 | 0.583 | Run 1 Defender verdict differed (emp_test vs critique_wins); score unchanged |
| **metric_mismatch_002** | **0.048** | **0.889** | 0.192 | 0.472 | DC stochasticity: Defender tipped to defense_wins in 1/3 runs |

Debate_std = 0.0 for 7/8 cases. **The one exception is `metric_mismatch_002`** (correct_position=mixed, ideal_resolution=empirical_test_agreed): the Defender stochastically reached defense_wins in 1 of 3 runs, reducing DC from 1.0 to 0.5 and the run mean from 0.917 to 0.833. The variance is confined to DC — IDR, FVC, and Judge verdict were identical across all 3 runs (judge_verdict=empirical_test_agreed in all 3). The Judge successfully overrode the Defender error every time.

The protocol is effectively deterministic for cases with an identifiable correct position. Non-zero variance (≈0.05) appears specifically when the Defender faces a genuinely two-sided case where defense_wins is a locally plausible verdict. The bootstrap CIs in §6 reflect cross-case sampling variance, not within-case stochasticity.

**Baseline replication note:** Baseline means in these replications are systematically higher than the original benchmark run for 4 of 5 cases. This reflects ETD volatility: in the original run, baseline ETD was 0.0 or 0.5 on these cases; in replications, the baseline spontaneously produced well-specified test designs (ETD=1.0), consistent with ETD being prompt-sensitive for the unconstrained baseline. This confirms that the debate protocol's ETD stability (ETD=1.0 reliably, due to explicit Judge instruction) is a prompt-design advantage over an unconstrained baseline — but not an irreducible architectural advantage.

### 8.2 Convergence by Difficulty

Agent convergence rate (fraction of debate cases where Critic and Defender reached agreement or the Judge produced a clean adjudication, without protocol breakdown) was analyzed across difficulty strata on 30 total cases (20 original + 10 new cases added to expand the easy and hard strata to n=10 each):

| Difficulty | n | Convergence rate |
|------------|---|-----------------|
| Easy | 10 | 0.950 |
| Medium | 10 | 0.944 |
| Hard | 10 | 0.957 |

The range across strata is 0.013. Convergence does not decrease with difficulty. The original easy=0.833 estimate was a single-data-point artifact (defense_wins_003 with a partial convergence score). With ≥10 cases per tier, convergence is flat — the protocol does not degrade on harder cases.

### 8.3 Scorer Independence

The Scorer agent is `claude-sonnet-4-6` — the same model family as Critic, Defender, Judge, and Baseline. A cross-capability validation re-scored all 15 applicable cases (non-defense_wins) using `claude-haiku-4-5` as an independent scorer operating only on task prompts vs. must-find labels, with no debate transcript access. IDR delta across all 15 cases = **0.000**. Same-company same-tier bias is not material at this capability level. Cross-vendor validation (GPT-4o, Gemini) remains future work.

### 8.4 IDP Robustness

The original benchmark produced IDP=1.0 for all 15 critique cases, suggesting the Critic never raised false concerns. This is a benchmark scope artifact: all 15 critique cases contain 1–2 must-find issues that are clearly and unambiguously disqualifying. There is no ambiguity about whether the Critic's findings are valid when the flaw is obvious.

Four IDP-stress cases were authored with valid ML work that has superficially suspicious features (narrow comparison sets, incomplete ablations, confounded but directionally plausible claims). IDP fell to 0.5 on all 4 cases: the Critic reliably raises 4–5 concerns per case, of which 1–2 have genuine methodological substance even though none are fatal to the work's validity. No case reached IDP=0.0 (entirely unfounded condemnation) or IDP=1.0 (zero concerns on valid-but-suspicious work). The original benchmark's IDP=1.000 is a property of having only clear-flaw cases, not a property of the protocol.

### 8.5 Ceiling Analysis

The debate protocol scores 1.000 on 16 of 20 cases. The ceiling is structural: all 15 non-defense_wins cases contain 1–2 must-find items discoverable from standard ML methodology applied to the task prompt. No case required domain expertise beyond what a competent ML practitioner would apply. The 4 non-ceiling debate cases are all known failure patterns:

- **real_world_framing_001** (0.833): Reasoning/label disconnect — DC=0.0 from the Defender labeling verdict incorrectly. Fixed by two-pass prompt.
- **defense_wins_003** (0.833): Partial Defender calibration — DRQ=0.5 from incomplete engagement with Critic issues.
- **defense_wins_005** (0.833): Same pattern as defense_wins_003.
- **scope_intent_003** (0.900): IDP=0.5 — Critic raised one valid but non-fatal concern alongside the correct finding.

The rubric has zero discriminative power for the debate protocol on correctly-functioning critique cases: IDR, IDP, DC, DRQ, ETD, and FVC are all 1.0 on all 13 ceiling critique cases. Analysis of where the protocol adds value relies entirely on variance in baseline and ensemble scores. Expanding the benchmark with cases that stress IDR (3–4 must-find items, requiring multi-step causal inference) is the correct remediation.

---

## 9. Known Failure Modes

### 9.1 Reasoning/Label Disconnect

`real_world_framing_001`: A healthcare triage scenario where the Defender's analysis text explicitly identified and articulated all critical flaws in the claim — but the verdict label read `defense_wins`. The reasoning was correct; the output structure was wrong. This is a Defender prompt calibration failure, not a reasoning failure.

**Root cause:** When the Defender produces its analysis in a single pass, it can arrive at a well-reasoned critical analysis and then, when selecting a verdict label, default to the assigned "defender" framing rather than reading its own analysis faithfully.

**Fix:** A two-pass Defender prompt: (1) analysis pass — produce a complete, unbiased assessment of the claim; (2) verdict pass — given the analysis above, select the verdict that accurately reflects the analysis, with explicit instruction not to select `defense_wins` if the analysis identifies critical unaddressed flaws. Applied to `agents/ml-defender.md`. Validated on the original failure case and 4 other defense_wins cases — all held correct.

### 9.2 Ensemble Mixed-Position Catastrophic Failure

`metric_mismatch_002`: The ensemble scored 0.000 — a catastrophic failure on a case where both sides of a genuine methodological disagreement are defensible. All three ensemble assessors independently converged on the same intuitive position (run the A/B test) without engaging the reviewer's substantive concern about offline-online correlation. The synthesizer faithfully summarized the consensus.

This failure is not fixable by compute or prompt tuning within the ensemble architecture: without role differentiation, independent assessors facing a genuinely two-sided prompt will produce correlated convergence errors. The debate protocol's Critic/Defender assignment forces engagement with both sides. This is the strongest case for role structure being uniquely load-bearing — and the primary driver of the ensemble's poor performance on the metric_mismatch category.

---

## 10. Remaining Limitations

The following limitations reflect genuinely unresolved constraints, not process steps that were addressed along the way.

**L1 — Synthetic benchmark, n=20.** All 20 cases are authored scenarios, not real ML papers. The flaws are planted; the adversarial framings are constructed. External validation (§7) partially mitigates this for fault detection (IDR) and exoneration, but the full protocol has not been tested on live ML evaluation tasks with organic errors. The benchmark is sufficient for the primary comparison but too small for subgroup analysis — n=5 per category is below conventional statistical thresholds for any category-level claim. Each case requires independent authoring, verification, and ground-truth labeling, which limits expansion.

**L2 — Same-company scorer.** Cross-capability validation using Haiku found zero IDR delta, but Haiku is still an Anthropic model. Cross-vendor validation (GPT-4o, Gemini) would rule out systematic Anthropic-family bias in scoring. This is unresolved.

**L3 — Rubric ceiling for debate.** 16 of 20 debate cases score 1.000. The rubric cannot distinguish between degrees of correct performance on the treatment condition. If the protocol is applied to harder cases — 3–4 must-find items, domain expertise required, multi-step causal chains — it may fail sub-ceiling without the benchmark currently being able to detect it. The ceiling is a benchmark scope limitation, not a protocol property.

**L4 — Difficulty labels are author-assigned.** Easy/medium/hard are assigned by the case author with no independent calibration or inter-rater agreement. Convergence-by-difficulty analysis and interpretations that reference difficulty labels depend on this. Empirical calibration (e.g., using baseline score as a proxy for difficulty) shows monotonic ordering but is not an independent ground truth.

**L5 — Exoneration finding below statistical threshold.** The 5/5 vs. 4/5 debate-vs-ensemble exoneration distinction and the 3/5 clean vs. 2/4 caveat-exoneration distinction are both at n=5, below conventional significance thresholds. The external benchmark confirms 3/3 correct debate verdicts on external exoneration cases, but also shows IDP=0.5 on all 3 — critics raised concerns in every case, inconsistent with the "clean exoneration" internal finding. Whether the Defender's structural isolation produces meaningfully cleaner outputs in practice is not confirmed.

**L6 — Model version binding.** All results are tied to `claude-sonnet-4-6`. A different model or significantly different capability tier would require a full benchmark re-run. The results should not be assumed to transfer to materially different models without re-validation.

**L7 — Cost and latency not benchmarked.** The debate protocol makes 4–6 sequential API calls per case; the ensemble makes ~4 parallel calls. Wall-clock latency and total token cost were not formally measured across the benchmark. The protocol is known to be more expensive in wall-clock time due to sequential dependency (Critic → Defender → Judge); exact multipliers depend on implementation.

---

## 11. Conclusion

The isolated self-debate protocol passes the benchmark on all three pre-registered criteria. The primary finding is supported: structured adversarial role separation produces measurably better evaluation outcomes than single-pass assessment across 20 synthetic ML reasoning scenarios with known ground-truth answers.

**The honest picture of where the advantage comes from:**

Most of the lift (debate 0.970 vs. floor 0.384, corrected gap +0.335–0.441) is explained by compute budget and multi-perspective synthesis — a compute-matched ensemble without role differentiation scores 0.754. What adversarial role separation specifically adds (+0.216, p=0.004, r=0.758) is: (1) a structural mechanism for resolving genuine disagreement on mixed-position cases, where parallel assessors produce correlated convergence errors; and (2) point-by-point argumentation in which every claim is conceded, rebutted, or empirically resolved — a structure a parallel ensemble cannot produce.

**What was falsified:** The ETD advantage (empirical test design) is a prompt-constraint effect, not an adversarial architecture effect. Adding one explicit output instruction to any ensemble synthesizer achieves ETD mean 0.962. The exoneration advantage (debate 5/5 vs. ensemble 4/5 defense_wins) is below statistical threshold and the clean-exoneration sub-finding does not replicate externally. The isolation architecture is not uniquely necessary for reaching correct exoneration verdicts — a clean ensemble without coaching achieves 4/5.

**What holds:** The protocol is structurally superior on cases with genuinely contested positions. The single-pass baseline's 0.000 score on all five false-positive trap cases is not a marginal failure — it represents an architectural inability to challenge the premise presented to it. More compute and more perspectives gets 4/5 of those correct. The debate protocol's isolated Defender, structurally required to argue for the work without having seen the Critique's framing, is the mechanism that resolves the fifth. Whether this generalizes beyond the synthetic benchmark requires testing on organic ML evaluation tasks at larger scale.

Full results, per-case scores, ablation data, and analysis files are in [`self_debate_experiment_v2/`](self_debate_experiment_v2/). Agent definitions are in [`agents/`](agents/).
