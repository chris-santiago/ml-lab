# Ensemble Baseline Analysis — Compute Confound Test

**Date:** 2026-04-04
**Addresses:** Issue 1 from `tasks/open_issues.md`
**Raw results:** `ensemble_results.json`

---

## TL;DR

The compute-matched ensemble baseline scored **1.000/1.000 (20/20 passes)** vs. the debate protocol's **0.970 (19/20 passes)**. For the **15 non-defense_wins cases**, the ensemble matches or exceeds the debate protocol at ceiling — strong evidence that the compute budget, not adversarial role structure, explains the lift on those cases.

**However, this experiment has a design flaw that invalidates the defense_wins results.** The agent prompts for defense_wins cases included an explicit description of the correct analysis before assessors ran their independent evaluations — direct coaching toward the right answer. Those 5 cases are contaminated and excluded from compute-confound conclusions. The isolation mechanism hypothesis (that a structurally isolated Defender uniquely enables exonerating valid work) **remains untested**.

---

## Experiment Design

**Purpose:** Test whether the debate protocol's lift over single-pass baseline reflects adversarial role structure or simply compute budget (3-4× more LLM calls).

**Ensemble design:** For each of the 20 benchmark cases:
1. **Assessor 1** — independent single-pass analysis (no knowledge of other assessors)
2. **Assessor 2** — independent single-pass analysis
3. **Assessor 3** — independent single-pass analysis
4. **Synthesizer** — reviews all three outputs; produces unified verdict
5. **Scorer** — applies rubric to synthesized output

This matches the debate protocol's token budget (~4 calls per case) without role differentiation (no Critic/Defender/Judge separation).

**Scoring:** Natural rubric applied — no DC=0.0 override, no DRQ≤0.5 cap.

---

## Methodological Flaws (Critical)

### Flaw 1: Must-find issues visible to assessors (non-defense_wins cases)

For critique/mixed cases, the agent prompts included a "must-find issues (for IDR scoring)" section. This section appeared in the same prompt as the assessor instructions — meaning assessors had access to the answer key before doing their independent analysis. The section was intended for the scorer (Step 5) but was unavoidably visible to all earlier steps.

**Impact:** IDR and IDP scores for non-defense_wins cases may be inflated. Assessors may have found issues they would not have found without the hint.

**Mitigating factors:** For most critique cases, the must-find issues are obvious to a competent ML analyst reading the task prompt carefully (e.g., the seasonal confound in hidden_confounding_002 is literally described in the task). The original single-pass baseline also missed these issues, suggesting the problem is one of critical framing rather than issue obscurity. The coaching effect may be minor for critique cases.

### Flaw 2: Correct analysis coaching in defense_wins cases (DISQUALIFYING)

For the 5 defense_wins cases, the agent prompt included an explicit "The correct analysis" section describing exactly why the work is valid and what the correct verdict should be. This section appeared before Assessor 1 began its independent analysis.

**Impact:** The defense_wins DC scores (all 1.0) almost certainly reflect the coaching rather than genuine independent reasoning. The original single-pass baseline scored DC=0.0 on all 5 defense_wins cases — it accepted the adversarial framing embedded in the task prompt. For the ensemble to score DC=1.0 on all 5 represents an implausibly large jump without the coaching explanation.

**Conclusion: Defense_wins case results are not valid for testing the isolation hypothesis.** These 5 cases are marked `contamination_flag: true` in `ensemble_results.json` and excluded from compute-confound conclusions.

---

## Results

### Non-Defense_Wins Cases (15 cases — uncontaminated primary results)

| Case | Category | Difficulty | Ensemble Mean | Debate Mean | Delta |
|------|----------|------------|---------------|-------------|-------|
| broken_baseline_001 | broken_baseline | easy | 1.000 | 1.000 | 0.000 |
| broken_baseline_002 | broken_baseline | medium | 1.000 | 1.000 | 0.000 |
| broken_baseline_003 | broken_baseline | hard | 1.000 | 1.000 | 0.000 |
| broken_baseline_004 | broken_baseline | hard | 1.000 | 1.000 | 0.000 |
| metric_mismatch_001 | metric_mismatch | easy | 1.000 | 1.000 | 0.000 |
| metric_mismatch_002 | metric_mismatch | medium | 1.000 | 1.000 | 0.000 |
| metric_mismatch_003 | metric_mismatch | hard | 1.000 | 1.000 | 0.000 |
| hidden_confounding_001 | hidden_confounding | medium | 1.000 | 1.000 | 0.000 |
| hidden_confounding_002 | hidden_confounding | hard | 1.000 | 1.000 | 0.000 |
| hidden_confounding_003 | hidden_confounding | medium | 1.000 | 1.000 | 0.000 |
| hidden_confounding_004 | hidden_confounding | hard | 1.000 | 1.000 | 0.000 |
| scope_intent_002 | scope_intent | medium | 1.000 | 1.000 | 0.000 |
| scope_intent_003 | scope_intent | hard | 1.000 | 0.900 | **+0.100** |
| real_world_framing_001* | real_world_framing | medium | 1.000 | 0.833 | **+0.167** |
| real_world_framing_002 | real_world_framing | hard | 1.000 | 1.000 | 0.000 |

**Non-defense_wins ensemble mean: 1.000**
**Non-defense_wins debate mean: 0.982** (post-two-pass-fix for real_world_framing_001: 0.993)
**Non-defense_wins ensemble passes: 15/15**
**Non-defense_wins debate passes: 15/15**

*real_world_framing_001: Debate scored 0.833 in original run (DC=0.0, reasoning/label disconnect). Post-two-pass fix applied to ml-defender, debate score is 0.967. Ensemble still matches.

### Defense_Wins Cases (5 cases — CONTAMINATED, excluded from primary analysis)

| Case | Ensemble Mean | Debate Mean | Contaminated |
|------|---------------|-------------|--------------|
| defense_wins_001 | 1.000 | 1.000 | YES |
| defense_wins_002 | 1.000 | 1.000 | YES |
| defense_wins_003 | 1.000 | 0.833 | YES |
| defense_wins_004 | 1.000 | 1.000 | YES |
| defense_wins_005 | 1.000 | 0.833 | YES |

**These results cannot be used to evaluate whether a compute-matched ensemble can exonerate valid work without an isolated Defender.**

### Overall Summary

| Metric | Ensemble | Debate | Corrected Baseline |
|--------|----------|--------|--------------------|
| Benchmark mean (all 20) | 1.000 | 0.970 | 0.529 |
| Benchmark passes | 20/20 | 19/20 | — |
| Non-defense_wins mean | 1.000 | 0.982 | ~0.650 |
| Defense_wins mean | 1.000* | 0.933 | 0.000 |

*Contaminated — see above.

---

## What This Tells Us

### 1. For non-defense_wins cases: compute budget explains the lift

The ensemble baseline — 3 independent assessors + 1 synthesizer, matched to the debate protocol's token budget — **scored at ceiling on all 15 non-defense_wins cases**. This matches or exceeds the debate protocol.

The corrected single-pass baseline (DC=0.5, DRQ uncapped) scored approximately 0.529–0.650 on these same cases. The jump from single-pass to ensemble-matched is large (+0.35 to +0.47), and it doesn't require Critic/Defender/Judge role separation. This strongly supports the **compute confound hypothesis** for non-defense_wins cases: the lift over single-pass baseline is better explained by additional computation (more LLM calls, multi-perspective synthesis) than by the adversarial role structure.

### 2. For defense_wins cases: the isolation hypothesis remains untested

The original experiment's most important finding was that the single-pass baseline scored **0.000 on all 5 defense_wins cases** — it inherited the adversarial framing and condemned valid work. The debate protocol's isolated Defender was the structural remedy: it received only the task prompt and independently exonerated the work.

The ensemble experiment was designed to test whether this same exoneration could be achieved with compute budget alone (no role separation). **This test failed due to prompt design.** We cannot conclude from these results whether a clean ensemble (without coaching) would correctly exonerate valid work or would, like the single-pass baseline, inherit the adversarial framing across all 3 assessors and synthesize the wrong verdict.

**The defensible prior** is that without explicit coaching, all 3 assessors would encounter the adversarial framing in the task prompt and produce consistent critique_wins verdicts, which the synthesizer would faithfully summarize — reproducing the single-pass baseline failure at 3× the compute cost. But this hypothesis was not tested.

### 3. The lift decomposition (revised)

Given the ensemble results, the debate protocol's reported lift (+0.586 headline, +0.441 corrected) can now be further decomposed:

| Source | Estimated contribution to lift |
|--------|-------------------------------|
| Structural scoring overrides (DC=0.0, DRQ cap) | −0.145 (this reduces the reported lift) |
| Compute budget / multi-perspective synthesis | ~0.35–0.47 (non-defense_wins cases) |
| Adversarial role isolation mechanism | Untested; load-bearing for defense_wins |

For non-defense_wins cases: **compute budget explains most or all of the lift** once structural overrides are removed.

For defense_wins cases: **the isolation architecture remains the only established mechanism**. The single-pass baseline fails 5/5. The debate protocol succeeds 4/5 (with one calibration failure fixed by two-pass prompt). Whether a clean ensemble can also succeed 4–5/5 is the open question.

---

## Clean Re-Run Results (2026-04-04)

The clean two-phase ensemble was executed for all 20 cases. Full per-case scores in `clean_ensemble_results.json`.

**Design:** Phase 1 — 3 independent assessors + synthesizer receive only the task prompt (no must-find labels, no correct analysis). Phase 2 — scorer receives synthesized output + must-find labels in a separate invocation.

### Overall Results

| Metric | Clean Ensemble | Debate Protocol | Corrected Single-Pass Baseline |
|--------|---------------|-----------------|-------------------------------|
| Benchmark mean | **0.754** | 0.970 | 0.529 |
| Pass count | **11/20 (55%)** | 19/20 (95%) | — |
| Non-defense_wins mean | 0.756 | 0.982 | ~0.650 |
| Defense_wins DC≥0.5 | **4/5** | 5/5 | 0/5 |

### Pre-Specified Verdict: TRIGGERED

> If ensemble scores ≥ DC=0.5 on ≥ 3/5 defense_wins cases → compute budget partially explains defense_wins advantage; isolation mechanism is not uniquely necessary.

**Result: DC≥0.5 on 4/5 defense_wins cases.** The criterion is met. Compute budget (3 independent views + synthesis) partially explains the defense_wins advantage. The isolation architecture is not uniquely necessary to exonerate valid work.

Defense_wins per-case DC:
| Case | Ensemble Verdict | DC | Notes |
|------|-----------------|-----|-------|
| defense_wins_001 | defense_wins ✓ | 1.0 | Correctly exonerated; raised minor caveats (IDP=0.5) |
| defense_wins_002 | defense_wins ✓ | 1.0 | Correctly exonerated; raised minor caveats (IDP=0.5) |
| defense_wins_003 | defense_wins ✓ | 1.0 | Perfect — "none identified" |
| defense_wins_004 | critique_wins ✗ | 0.0 | Failed — narrow baseline comparison flagged as insufficient for SOTA claim |
| defense_wins_005 | defense_wins ✓ | 1.0 | Perfect — "none identified" |

The 1 failure (defense_wins_004) is the hardest case in the benchmark: a neural architecture claiming SOTA on 7 benchmarks against 3 baselines. All three assessors independently concluded the comparison set was too narrow to sustain a SOTA claim. This is a reasonable methodological concern — the debate protocol also had partial failures on similar edge cases.

### Why the Ensemble Benchmark Mean (0.754) Falls Below Debate (0.970)

The clean ensemble is not at ceiling for non-defense_wins cases, unlike the contaminated first run. The gap is almost entirely explained by a single structural pattern:

**ETD = 0.0 for 9 of 20 cases.**

The ensemble correctly identifies issues (IDR≈1.0) and reaches the correct verdict direction (DC≈1.0 on non-failures), but it does not propose a specific empirical test. Cases where `ideal_resolution = empirical_test_agreed` receive DRQ=0.5 (verdict = critique_wins, not empirical_test_agreed) and ETD=0.0 (no test proposed), which fails the per-dimension floor check (all applicable dims ≥ 0.5 required to pass).

The debate protocol's adversarial forcing function (Critic challenges → Defender responds → Judge resolves → both must agree on a test when positions diverge) is what generates the empirical test proposal. Parallel assessors reasoning independently have no forcing function to produce that output — they stop at "the critique is correct" rather than "here is the test that would resolve it."

This is not a reasoning quality failure. It's a missing output constraint.

**Per-category ETD pattern:**

| Category | ETD scores | Interpretation |
|----------|-----------|----------------|
| broken_baseline (001-004) | 0.5 | Test implied (statistical test clear) but not formally specified |
| metric_mismatch_001, 003 | null / 0.5 | critique_wins ideal or test underspecified |
| hidden_confounding (001-004) | 0.0 | Issues identified, no test proposed at all |
| scope_intent_002 | 0.0 | No intervention study proposed |
| real_world_framing (001-002) | 0.0 | No prospective validation designed |

### Revised Compute Economics (User Insight)

The user identified the structural difference:

- **Ensemble = same task × N agents (parallel):** All assessors see the same adversarial framing. Independent views can cancel out framing bias but produce no forcing function for test design.
- **Debate = different tasks × agents (iterative):** Critic and Defender have incompatible mandates. The disagreement structure forces specification of what would resolve the disagreement.

Compute efficiency: Ensemble uses ~4 calls at parallel latency. Debate uses ~4+ calls at sequential latency. For cases where `ideal_resolution = empirical_test_agreed`, the sequential structure earns ~+0.5 ETD and +0.5 DRQ that the parallel structure cannot produce without explicit output constraints. The debate protocol is more expensive in wall-clock time but purchases a structurally different output.

---

## Conclusion (Updated 2026-04-04)

**What is established:**
1. **Compute budget + parallel views** can partially replace the isolation mechanism for defense_wins cases. 4/5 valid work cases were correctly exonerated without structural isolation or coaching. The original finding that "isolation architecture is uniquely necessary" is revised to "isolation architecture is not uniquely necessary, but parallel views achieve imperfect exoneration (IDP=0.5 vs 1.0 for cases that raised caveats)."
2. **ETD is the debate protocol's structural advantage over ensembles.** For cases where the ideal resolution is an agreed empirical test, the debate's adversarial forcing function is what generates the test. A compute-matched ensemble with no output constraints produces correct issue identification and verdict direction but stops short of test design.
3. **The contaminated first ensemble run (all 1.0) was entirely artifact.** The clean run scores 0.754, not 1.0. The coaching effect was total.
4. **The debate protocol still outperforms** the clean ensemble substantially (0.970 vs 0.754), with better pass rates (95% vs 55%). The advantage is real — but the mechanism is test-design forcing, not issue detection or verdict calibration.

**Recommended status for Issue 1:** Resolved. Defense_wins isolation hypothesis definitively tested and partially refuted: compute budget + parallel views suffices for exoneration in 4/5 cases. ETD is the structural mechanism that explains debate's remaining advantage.

---

## Prompt Design Lessons

For future ensemble experiments:
1. Run assessors and scorer as separate agent invocations. Assessors receive only the task prompt. The scorer receives assessor outputs + the must-find labels separately.
2. For defense_wins cases, omit all coaching from assessor prompts. The whole point is to test whether unguided assessors independently recognize valid work.
3. Log which information was visible to which agent role for auditability.
4. If the goal is empirical test design (not just issue detection), add an explicit output constraint to the synthesizer: "If the issues identified are real but resolvable empirically, specify the test that would resolve them."
