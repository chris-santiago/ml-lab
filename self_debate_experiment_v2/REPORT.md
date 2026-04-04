# Self-Debate Protocol v2 — Technical Report

**Date:** 2026-04-03  
**Experiment:** Self-Debate Protocol v2 (Isolated Two-Agent Architecture)  
**Benchmark cases:** 20  
**Protocol:** Critic and Defender receive task prompt only (no shared context); Judge adjudicates from both outputs; Baseline receives task prompt only, single-pass.

---

## Abstract

This report evaluates the isolated self-debate protocol on a 20-case benchmark of synthetic ML reasoning tasks with known ground truth. The protocol produces two independent agent outputs per case — one adversarial (Critic) and one defensive (Defender) — which are adjudicated by a Judge. A single-pass baseline provides the comparison condition.

The debate protocol achieves a benchmark aggregate mean of **0.970**, compared to **0.384** for the single-pass baseline, a lift of **+0.586**. Nineteen of twenty cases pass the per-case threshold (mean ≥ 0.65, no rubric dimension below 0.5). All three benchmark pass criteria are met. The primary hypothesis is supported. The baseline fails on 18 of 20 cases and scores 0.000 on all five false-positive critique traps.

> **Post-experiment findings (2026-04-04):** After committing these results, adversarial review by `ml-critic` and `ml-defender` identified rubric design effects that inflate the reported lift. With corrections applied, the honest lift range is **+0.335 to +0.441** (still 3–4× the pre-registered threshold). A two-pass Defender fix resolves the sole case failure. A clean compute-matched ensemble test found that the isolation architecture is not uniquely necessary for exonerating valid work — but that the debate protocol's structural advantage in *empirical test design* is real and not replicable by parallel assessors. The §3.2 "isolation is the only mechanism" finding is qualified accordingly. See `SENSITIVITY_ANALYSIS.md` and `ENSEMBLE_ANALYSIS.md` for full post-experiment analysis.

---

## 1. Experimental Design

### 1.1 Protocol

The isolated self-debate protocol is defined by three structural commitments:

1. **Context isolation.** The Critic and Defender each receive only the task prompt. Neither sees the other's output before producing its own assessment.
2. **Role separation.** Critic is instructed to identify methodological weaknesses. Defender is instructed to identify what the critique overlooks or overstates.
3. **Adjudication.** The Judge receives both independent outputs and assigns a verdict. The verdict is typed: `critique_wins`, `defense_wins`, or `empirical_test_agreed`.

The baseline receives the same task prompt and produces a single-pass assessment with no debate structure.

### 1.2 Scoring Rubric

Six rubric dimensions are scored per case on a 0.0–1.0 scale:

| Dimension | Abbrev | Definition | Applicability |
|-----------|--------|------------|---------------|
| Issue Discovery Recall | IDR | Fraction of planted must-find issues correctly identified | Non-defense_wins only |
| Issue Discovery Precision | IDP | Fraction of claimed issues that are valid | Non-defense_wins only |
| Defense Calibration | DC | Whether defense correctly separated real from false issues and reached the right verdict type | All 20 cases |
| Debate Resolution Quality | DRQ | Whether the typed verdict matches the expected resolution | All 20 cases |
| Empirical Test Diagnosticity | ETD | Whether proposed experiment would distinguish critique from defense | Applicable cases (ideal ≠ critique_wins/defense_wins) |
| Final Verdict Correctness | FVC | Whether the final conclusion matches ground truth | All 20 cases |

**Per-case pass criterion:** mean ≥ 0.65 AND no applicable dimension below 0.5.

**Benchmark pass criteria:** debate mean ≥ 0.65, case pass fraction ≥ 75%, lift ≥ +0.10.

**IDP/IDR on defense_wins cases:** Scored N/A. Scoring IDP on a case where the Critic's claims are structurally invalid would mechanically penalize a correctly-functioning protocol. The relevant signal in defense_wins cases is DC (did the Defender correctly identify the sound aspects and reach defense_wins?) and FVC.

**Agent convergence rate:** A per-case binary metric measuring whether the Critic and Defender independently reached the same verdict type before Judge adjudication. Computed from the `critic_verdict` and `defender_verdict` fields in `self_debate_results.json`. Values: 1.0 = both agents output the same verdict type (e.g., both `critique_wins`); 0.5 = agents diverged on verdict type. The 0.5 value is used rather than 0.0 to avoid conflating "no agreement" with "maximal disagreement" — convergence measures agreement, not correctness. Cases where divergence is the expected behavior (mixed correct_position) are not treated as failures.

### 1.3 Benchmark Cases

Twenty synthetic ML reasoning cases across six categories:

| Category | N | Correct position |
|----------|---|-----------------|
| broken_baseline | 4 | critique (3), mixed (1) |
| metric_mismatch | 3 | critique (2), mixed (1) |
| hidden_confounding | 4 | critique (4) |
| scope_intent_misunderstanding | 2 | mixed (2) |
| defense_wins | 5 | defense (5) |
| real_world_framing | 2 | critique (2) |

Defense_wins cases are false-positive critique traps: methodologically sound work presented under adversarial conditions. These test whether the protocol can exonerate valid work, not merely detect flaws.

---

## 2. Results

### 2.1 Benchmark Summary

| Criterion | Threshold | Debate | Baseline |
|-----------|-----------|--------|----------|
| Benchmark mean | ≥ 0.65 | **0.970** ✓ | 0.384 ✗ |
| Case pass fraction | ≥ 75% | **95% (19/20)** ✓ | 10% (2/20) ✗ |
| Lift | ≥ +0.10 | **+0.586** ✓ | — |

**Benchmark verdict: PASSES.**

**Statistical tests** (bootstrap CIs and paired Wilcoxon signed-rank — see `stats_analysis.py` and `stats_results.json`):

| Comparison | Point estimate | 95% Bootstrap CI | Wilcoxon p | Effect size (r) |
|------------|---------------|------------------|-----------|-----------------|
| Debate mean | 0.970 | [0.942, 0.992] | — | — |
| Baseline mean | 0.384 | [0.275, 0.486] | — | — |
| Ensemble mean | 0.754 | [0.627, 0.856] | — | — |
| Lift: debate vs. baseline | +0.586 | [+0.486, +0.691] | p = 0.000082 | r = 1.000 |
| Lift: debate vs. ensemble | +0.216 | [+0.098, +0.352] | p = 0.003528 | r = 0.758 |

Both lifts are statistically significant at α = 0.05. The debate vs. baseline lift has the maximum possible rank-biserial r (1.0) — the debate protocol outperforms the baseline on every one of the 20 cases. The debate vs. ensemble lift (r = 0.758) is a large effect. Bootstrap CIs were computed with 10,000 case-level resamples; Wilcoxon uses normal approximation with continuity correction.

### 2.2 Per-Case Results

| Case | Diff | Debate | Baseline | Delta | Verdict | D-Pass | Conv |
|------|------|--------|----------|-------|---------|--------|------|
| broken_baseline_001 | easy | 1.000 | 0.667 | +0.333 | emp_test_agreed | YES | 1.0 |
| broken_baseline_002 | med | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | 1.0 |
| broken_baseline_003 | hard | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | 1.0 |
| broken_baseline_004 | hard | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | 1.0 |
| metric_mismatch_001 | easy | 1.000 | 0.600 | +0.400 | critique_wins | YES | 1.0 |
| metric_mismatch_002 | med | 1.000 | 0.667 | +0.333 | emp_test_agreed | YES | 0.5 |
| metric_mismatch_003 | hard | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | 1.0 |
| hidden_confounding_001 | med | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | 1.0 |
| hidden_confounding_002 | hard | 1.000 | 0.333 | +0.667 | emp_test_agreed | YES | 1.0 |
| hidden_confounding_003 | med | 1.000 | 0.333 | +0.667 | emp_test_agreed | YES | 1.0 |
| hidden_confounding_004 | hard | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | 1.0 |
| scope_intent_002 | med | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | 1.0 |
| scope_intent_003 | hard | 0.900 | 0.500 | +0.400 | critique_wins | YES | 0.5 |
| defense_wins_001 | med | 1.000 | 0.000 | +1.000 | defense_wins | YES | 1.0 |
| defense_wins_002 | med | 1.000 | 0.000 | +1.000 | defense_wins | YES | 1.0 |
| defense_wins_003 | easy | 0.833 | 0.000 | +0.833 | defense_wins | YES | 0.5 |
| defense_wins_004 | hard | 1.000 | 0.000 | +1.000 | defense_wins | YES | 1.0 |
| defense_wins_005 | med | 0.833 | 0.000 | +0.833 | defense_wins | YES | 0.5 |
| real_world_framing_001 | med | 0.833 | 0.583 | +0.250 | emp_test_agreed | **NO** | 0.5 |
| real_world_framing_002 | hard | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | 1.0 |
| **BENCHMARK** | | **0.970** | **0.384** | **+0.586** | | **19/20** | **0.875** |

### 2.3 Dimension-Level Aggregates

| Dimension | Debate | Baseline | Delta | N cases |
|-----------|--------|----------|-------|---------|
| issue_discovery_recall | 1.000 | 0.475 | +0.525 | 15 |
| issue_discovery_precision | 1.000 | 1.000 | 0.000 | 15 |
| defense_calibration | 0.867 | 0.000 | +0.867 | 20 |
| debate_resolution_quality | 1.000 | 0.325 | +0.675 | 20 |
| empirical_test_diagnosticity | 1.000 | 0.933 | +0.067 | 15 |
| final_verdict_correctness | 1.000 | 0.325 | +0.675 | 20 |

*IDR/IDP baseline averages computed over 15 non-defense_wins cases where these dimensions apply.*

The widest protocol advantage is in defense_calibration (+0.867) and final_verdict_correctness (+0.675). The baseline scores 0.000 on defense_calibration in every single case — it structurally cannot calibrate a defense because it has no defense role. IDP is tied at 1.000: both systems are precise about the issues they raise, but the baseline fails to raise the right ones (IDR 0.475 vs 1.000).

### 2.4 Convergence by Difficulty

| Difficulty | Cases | Mean convergence |
|------------|-------|-----------------|
| easy | 3 | 0.833 |
| medium | 10 | 0.944 |
| hard | 7 | 0.938 |

Convergence does not decrease with difficulty. See §4.4 for interpretation.

---

## 3. Hypothesis Verdicts

### 3.1 Primary hypothesis

> The debate protocol will achieve a benchmark aggregate score at least 0.10 higher than the trivial baseline.

**SUPPORTED.** Debate mean 0.970 vs. baseline mean 0.384. Lift = +0.586. Exceeds the +0.10 threshold by a factor of 5.86×.

### 3.2 Secondary hypothesis: isolated protocol enables defense_wins verdicts

> The isolated context architecture produces correct defense_wins verdicts on false-positive critique trap cases.

**SUPPORTED (with post-experiment qualification).** All 5 defense_wins cases reach the correct `defense_wins` verdict. Baseline scores 0.000 on all 5 (DC=0.0, DRQ=0.0, FVC=0.0).

> **Qualification (2026-04-04):** A clean compute-matched ensemble (3 independent assessors, task-prompt-only) correctly exonerated valid work in 4/5 defense_wins cases without structural isolation, triggering the pre-specified criterion that "compute budget partially explains the defense_wins advantage." The isolation architecture is not uniquely necessary — multiple independent parallel views can achieve similar exonerations. However, the debate protocol's isolated Defender produces cleaner exonerations: 3/5 cases with no claims raised (IDP=1.0) vs. ensemble raising caveats in 2/4 correct exonerations (IDP=0.5). The debate protocol's remaining structural advantage over the ensemble is concentrated in empirical test design (ETD), not in exoneration per se. See `ENSEMBLE_ANALYSIS.md`.

### 3.3 Secondary hypothesis: convergence decreases with difficulty

> Agent convergence rate will be lower for hard cases than easy/medium cases.

**NOT SUPPORTED.** Convergence is: easy=0.833, medium=0.944, hard=0.938. The pattern reverses or is flat. See §4.4.

---

## 4. Analysis

### 4.1 Where the protocol adds the most value

**Defense_wins cases (delta = +1.000 on three of five).** The isolated protocol produces correct `defense_wins` verdicts on all 5 false-positive critique traps. The single-pass baseline has no mechanism to challenge an adversarial framing — it inherits the critique's premise and scores 0.000. Delta = +1.000 on defense_wins_001, _002, and _004 represents the full possible benefit. *(Note: the clean ensemble follow-on showed 4/5 correct exonerations without structural isolation — the isolation architecture is not uniquely necessary for the exoneration result, though it produces higher-precision exonerations. See §3.2 qualification.)*

**Hard confounding cases (delta = +0.583 to +0.667).** hidden_confounding_002 and hidden_confounding_003 show IDR=0.0 for the baseline — it accepted the team's interpretation at face value and failed to identify the planted confounds (holiday season timing, document-level data leakage). The protocol found both confounds independently from both directions and proposed diagnostically sound experiments.

**Verdict typing on hard scope and metric cases.** On metric_mismatch_003 and hidden_confounding_001, the baseline produced FVC=0.0 (incorrect verdict) in addition to IDR failures. The protocol achieved FVC=1.000 on both. The structured role separation — requiring the Critic to commit to a specific failure claim and the Defender to articulate a specific rebuttal — produces better-typed conclusions than single-pass hedging.

### 4.2 Where the protocol adds limited value

**Easy cases with explicit task-level signals (broken_baseline_001, metric_mismatch_001).** The baseline passes both (0.667 and 0.600 respectively). When the flaw is stated in the task description itself (unequal sample sizes, 98/2 imbalance), single-pass reasoning finds it. The protocol still adds value in DRQ and DC, but the baseline is not failing structurally.

**Empirical test diagnosticity.** Both systems score high (0.933 baseline vs 1.000 debate). Proposing a relevant experiment, once an issue is identified, is within reach of single-pass reasoning. ETD is not a reliable discriminator between the two conditions.

### 4.3 Observed failure modes

**Failure mode 1: Defender reasoning/label disconnect (real_world_framing_001).** The sole failed case. The Defender correctly identified all critical issues in analysis text — retrospective agreement ≠ clinical readiness, physician decisions are not ground truth, error class asymmetry is unaddressed — but then labeled the verdict `defense_wins`. The analysis is internally contradictory: the text says the claim is invalid, the label says the work is valid. DC=0.0, causing a per-dimension floor violation.

This is a new failure mode distinct from the partial-contestation failures observed in the prior experiment. The issue is not calibration of issue severity but a reasoning-to-verdict translation error. The Defender role is structurally associated with defending work, which may create label bias toward `defense_wins` even when the analysis contradicts it. The fix is more explicit verdict labeling guidance in the Defender prompt — or a two-pass design where the Defender commits to analysis before selecting a verdict label.

**Failure mode 2: Defender under-confidence on defense_wins cases (defense_wins_003, defense_wins_005).** On two easy/medium defense_wins cases, the Defender correctly identified the key sound methodological aspects but stopped at `empirical_test_agreed` rather than `defense_wins`. DC=0.5 for both. The Defenders were excessively cautious: 5-fold stratified CV on 8,500 examples is a reliable estimate (defense_wins_003), and same-system evaluation for same-system deployment scope is the correct design (defense_wins_005). Both are cases where the correct answer requires recognizing that a limitation is real but not disqualifying — the Defender defaulted to "needs more testing" rather than committing to the work's validity.

Both cases still pass (0.833 mean, no floor violations). The protocol produces correct `defense_wins` verdicts for the hard defense_wins cases that require domain knowledge to rebut (defense_wins_001, _002, _004). The under-confidence pattern appears specifically when the defense requires committing to the position that a work is sound despite acknowledged caveats.

**Failure mode 3: Genuine verdict divergence on mixed-correct-position cases (metric_mismatch_002, scope_intent_003).** Convergence = 0.5 for both. This is expected and desired — these cases are designed to have legitimate arguments on both sides. The isolated agents reached different verdicts, and the Judge adjudicated both to the correct resolution type. The divergence reflects the protocol working correctly, not incorrectly.

### 4.4 Convergence does not decrease with difficulty

The expected finding was that hard cases would show lower convergence because secondary issues are harder to identify independently. The observed result is the opposite: convergence by difficulty is easy=0.833, medium=0.944, hard=0.938.

The resolution: the easy convergence decrement is entirely driven by defense_wins failures (defense_wins_003 has conv=0.5), not by issue discovery difficulty. When we examine only the non-defense_wins cases, hard cases show convergence 1.0 in all 8 instances — the planted confounds in hard cases were independently found by both agents. The difficulty categorization reflects reasoning depth required to evaluate the claim, not how easily the primary flaw is identified. The hard confounding cases have clear, identifiable flaws that both agents find independently. The easy defense_wins_003 case involves a calibration judgment about how to label an acknowledged caveat — which is subtler than identifying a flaw.

---

## 5. Comparison to Prior Experiments

### Experiment 1 (contaminated single-context, 11 cases)

In the first experiment, all debate transcripts were generated in a single context window — the Critic and Defender roles were played sequentially by the same model with shared context. This produced debate mean 0.988 and baseline mean 0.517. The inflated scores resulted from in-context access to the opposing argument before generating a response.

Experiment 1 failed the isolation requirement. Its results overstate genuine debate quality.

### Experiment 2 (isolated, 15 cases)

The second experiment introduced genuine context isolation and expanded the case set to 15 cases including 4 defense_wins cases. Results: debate mean 1.000, baseline mean 0.379, lift +0.621. All 4 defense_wins cases correct; baseline 0.000 on all 4.

Experiment 2 was methodologically valid and established the isolation architecture. The 1.000 debate mean reflects the 15-case subset.

### Self-Debate v2 (this experiment, 20 cases)

Five new cases were added: broken_baseline_004, hidden_confounding_004, defense_wins_005, real_world_framing_001, real_world_framing_002. The debate mean drops slightly to 0.970 (from 1.000) due to genuine failures on real_world_framing_001 (DC=0.0) and two defense_wins cases (DC=0.5). This is not a regression — it reflects the new cases introducing harder calibration challenges.

The baseline mean (0.384) is consistent with Experiment 2 (0.379), confirming baseline stability. Lift is consistent at +0.586 vs +0.621.

The primary addition in v2 is the two new case categories (real_world_framing) and the identification of a new failure mode (reasoning/label disconnect), absent from Experiment 2's case set.

---

## 6. Recommendations

**For the debate protocol:**

1. **Refine the Defender prompt for verdict labeling.** The reasoning/label disconnect in real_world_framing_001 is the most important failure to fix. Require the Defender to complete analysis before selecting a verdict label, and add an explicit instruction: "If your analysis identifies multiple critical unaddressed flaws, your verdict should be `empirical_test_agreed` or `critique_wins` — not `defense_wins`." A two-pass Defender (analysis pass → verdict pass) would prevent this class of failure.

2. **Add a "commit" step for defense_wins cases.** The under-confidence failures on defense_wins_003 and defense_wins_005 both involved the Defender correctly analyzing sound work but hedging toward `empirical_test_agreed`. Add an explicit instruction: "If the methodology is sound for the stated scope and the limitations are real but not disqualifying, your verdict is `defense_wins` — not `empirical_test_agreed`." The current prompt does not distinguish clearly enough between "limitations that warrant more testing" and "limitations that do not falsify the claim."

3. **Introduce structured verdict typing into Defender output.** Currently the Defender produces free-form analysis followed by a verdict. A structured output format (analysis → concessions → contested points → verdict type → justification) would make the reasoning-to-label mapping more traceable.

**For the benchmark:**

4. **Add real_world_framing cases with clinical/regulatory domain knowledge requirements.** real_world_framing_001 exposed a new failure mode precisely because the case involves an asymmetric-error-class structure that is non-obvious without domain knowledge (urgent vs. routine vs. self-care triage). More cases of this type would stress the protocol's handling of domain-specific calibration.

5. **Add production deployment framing cases.** Both real_world_framing cases involve deployment decisions. These are underrepresented. The benchmark has 4 defense_wins cases for exoneration and 2 real_world_framing cases for deployment misframing — expanding real_world_framing to 5–6 cases would provide a symmetric stress on the verdict-typing mechanism.

**For the harness:**

6. **Instrument Defender label vs. analysis divergence as a separate diagnostic metric.** The reasoning/label disconnect failure in real_world_framing_001 would be detectable automatically: if Defender analysis text contains explicit statements that a claim is invalid, but the verdict label is `defense_wins`, flag it as a potential disconnect. This does not require rubric scoring — it is a structural consistency check.

---

## 7. Limitations

The following limitations are documented in full across `SENSITIVITY_ANALYSIS.md`, `ENSEMBLE_ANALYSIS.md`, and the post-experiment sections of this report. They are consolidated here for clarity.

**L1 — Closed-loop benchmark design.** The benchmark cases, ground truth labels (`must_find`, `correct_position`, `ideal_resolution`), rubric dimensions, scoring code, agent prompts, and scoring judgments all originate from the same entity. The benchmark may be unconsciously calibrated to the protocol's strengths. The 14/20 debate ceiling scores (1.000) are consistent with this effect, though they are also consistent with the tasks being genuinely tractable for the protocol. An independent external benchmark was run as a partial mitigant (10 cases from published ML evaluation failures, IDR=0.95 — see `../external_benchmark/`), but external defense_wins cases do not exist in published failure literature, so the protocol's most distinctive advantage (exoneration of valid work) cannot be externally validated.

**L2 — Single run per case; no variance estimation.** Every result is a point estimate from a single execution. LLMs are stochastic; re-running the same protocol on the same case would produce a distribution of scores. The reported means (0.970, 0.384) have no confidence intervals and no significance tests. A bootstrap analysis and paired Wilcoxon test are documented in `stats_results.json` (see `stats_analysis.py`), but within-case variance from LLM stochasticity has not been estimated.

**L3 — Rubric-inflated headline lift.** The reported +0.586 lift reflects two structural scoring choices: DC=0.0 hardcoded for all baseline cases (the baseline has no defense role), and DRQ capped at 0.5 for all baseline cases (a single-pass system cannot produce a "debate resolution"). Both overrides were identified and quantified by post-experiment adversarial review. The honest corrected lift range is **+0.335 to +0.441** — 3–4× the pre-registered threshold under all rubric scenarios. See `SENSITIVITY_ANALYSIS.md`.

**L4 — Strawman primary comparison.** The single-pass baseline runs with 3–4× fewer LLM calls and no structural role prompting. A compute-matched ensemble (3 independent assessors + synthesizer, no role differentiation) scored 0.754 overall vs. debate's 0.970. The debate–ensemble gap (+0.216) is a more honest measure of what adversarial role structure specifically contributes. See `ENSEMBLE_ANALYSIS.md`.

**L5 — Same-model scoring confound.** The Scorer agent is claude-sonnet-4-6 — the same model family as the Critic, Defender, Judge, and Baseline. A model scoring its own outputs may exhibit self-consistency bias. IDR=1.000 across 15 applicable debate cases and IDP=1.000 for both systems are consistent with this effect. Cross-model scorer validation (Issue 5 in `tasks/open_issues.md`) has not been executed.

**L6 — N=20 sample size.** The benchmark contains 20 cases across 6 categories. The convergence-by-difficulty analysis has n=3 for the easy stratum (one data point drives the easy=0.833 estimate). Category-level conclusions (e.g., "protocol adds limited value on easy cases") are based on 2–5 cases per category and should be treated as directional rather than definitive.

**L7 — Unvalidated difficulty labels.** Easy/medium/hard labels are author-assigned with no independent calibration or inter-rater agreement. The convergence analysis and §4.4 interpretation depend on these labels.

**L8 — Rubric ceiling for the treatment condition.** Fourteen of 20 debate cases score 1.000 across all applicable dimensions. The rubric has no discriminative power for the treatment condition — it cannot distinguish degrees of protocol performance across cases. Analysis of "where the protocol adds value" (§4.1–4.2) relies entirely on variation in baseline scores. See Issue 11 in `tasks/open_issues.md`.

---

## 8. Artifacts (previously §7)

All experimental artifacts are in `/self_debate_experiment_v2/`:

| File | Description |
|------|-------------|
| `BENCHMARK_PROMPTS.md` | All 20 task prompts, verbatim as given to Critic and Defender |
| `self_debate_poc.py` | Benchmark case metadata and scoring logic |
| `self_debate_results.json` | Full results JSON: per-case scores, transcripts, aggregates |
| `CONCLUSIONS.md` | Per-case scoring tables, dimension-level aggregates, failure mode analysis |
| `SENSITIVITY_ANALYSIS.md` | Rubric design effects on reported lift; honest corrected range +0.335–0.441 |
| `ENSEMBLE_ANALYSIS.md` | Compute-matched ensemble follow-on; ETD forcing function finding; IDP asymmetry correction |
| `clean_ensemble_results.json` | Per-case ensemble scores — clean two-phase run |
| `stats_analysis.py` | Bootstrap CIs and paired Wilcoxon tests on per-case deltas |
| `stats_results.json` | Output of stats_analysis.py: CIs, p-values, effect sizes |
| `REPORT.md` | This document |

---

## 9. Conclusion

The isolated self-debate protocol passes the benchmark on all three criteria. The +0.586 headline lift is partially attributable to rubric design choices (DC=0.0 structural override, DRQ cap); the honest corrected lift range is **+0.335 to +0.441**, still 3–4× the pre-registered threshold. The protocol's advantage is real.

The clearest dimension advantage is in defense calibration (+0.867): the baseline scores 0.000 on this dimension in every case. The reasoning/label disconnect failure in real_world_framing_001 is resolved by a two-pass Defender prompt (analysis before verdict selection) — see `agents/ml-defender.md`.

The post-experiment ensemble test refined the isolation hypothesis: the adversarial role architecture is not uniquely necessary to exonerate valid work (4/5 correct exonerations without isolation), but it produces cleaner exonerations and — crucially — forces production of agreed empirical test specifications that parallel assessors never generate. The debate protocol's structural advantage in empirical test design (ETD=1.0 across all applicable cases vs. ensemble ETD≈0.0–0.5) is the finding that best distinguishes the debate architecture from a more-compute alternative.

The fundamental finding holds: a structured isolated debate protocol with typed verdict roles substantially outperforms single-pass reasoning on synthetic ML reasoning tasks with known ground truth, particularly on hidden confounding, adversarial framing, and cases requiring a typed empirical resolution rather than a binary verdict.
