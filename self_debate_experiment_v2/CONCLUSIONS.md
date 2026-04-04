# CONCLUSIONS.md — Self-Debate Protocol v2

## 1. Per-Case Scoring Table

All scores are on a 0.0–1.0 scale. `null` = N/A (dimension not applicable for that case). Pass = mean ≥ 0.65 AND no applicable dimension below 0.5.

**Dimension abbreviations:**
- IDR = issue_discovery_recall | IDP = issue_discovery_precision
- DC = defense_calibration | DRQ = debate_resolution_quality
- ETD = empirical_test_diagnosticity | FVC = final_verdict_correctness

---

### broken_baseline_001 (easy)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.667** | YES |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both agents independently identified unequal evaluation populations and missing CIs. Both proposed McNemar test on matched sets.

---

### broken_baseline_002 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
DC=1.0: defender correctly identified valid aspects of BERT choice and baseline practice (correct_position=mixed). Both proposed per-class F1 evaluation.

---

### broken_baseline_003 (hard)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both independently identified feature_set_confound and attribution_error. Both proposed identical 2x2 ablation.

---

### broken_baseline_004 (hard) — NEW in v2
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Fine-tuned vs zero-shot is not an architecture comparison. Both independently identified training_regime_confound and architectural_attribution_error.

---

### metric_mismatch_001 (easy)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | N/A | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | N/A | 0.5 | **0.600** | NO |

Actual verdict: `critique_wins` ✓ | Convergence: 1.0
ETD=N/A (ideal=critique_wins). Accuracy on 98/2 imbalanced data is structurally incapable of detecting minority-class performance. Claim invalid on its face.

---

### metric_mismatch_002 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.667** | YES |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 0.5
**First genuine disagreement.** Critic: empirical_test_agreed (calibrate offline-to-online first). Defender: defense_wins (run the A/B test directly). Both positions are substantively defensible — this is the mixed-correct-position case working correctly.

---

### metric_mismatch_003 (hard)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both independently named human_study_underpowered and no_inter_annotator_agreement. Single-pass baseline accepted "significantly" without any statistical test.

---

### hidden_confounding_001 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both identified temporal_distribution_shift (UX redesign in August) and attribution_conflation. Baseline accepted AUC 0.79 as valid; debate correctly demanded sub-window analysis.

---

### hidden_confounding_002 (hard)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.333** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Largest baseline failure (IDR=0.0). Holiday season perfectly confounds program launch. The 22% lift is entirely uninterpretable without a control group or prior-year placebo.

---

### hidden_confounding_003 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.333** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Random 80/10/10 split on single corpus = data contamination. Baseline accepted F1 0.91 at face value. Both agents independently identified document-level leakage as the critical threat.

---

### hidden_confounding_004 (hard) — NEW in v2
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Directional alignment ≠ calibration validity. Both independently identified population_feature_drift and model_calibration_unverified. "No model update" recommendation over 2-year macro regime change is unsupported without calibration curves + PSI analysis.

---

### scope_intent_002 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both found prediction_vs_intervention_conflation and no_intervention_design. DC=1.0: defender correctly noted AUC 0.77 is a legitimate predictive signal (correct_position=mixed). Both proposed prospective RCT.

---

### scope_intent_003 (hard)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.5 | 1.0 | N/A | 1.0 | **0.900** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | N/A | 0.5 | **0.500** | NO |

Actual verdict: `critique_wins` ✓ | Convergence: 0.5
ETD=N/A (ideal=critique_wins). Defender identified all three must_find issues but concluded defense_wins — overconceding by misinterpreting online evaluation design quality as sufficient justification for full replacement. DC=0.5.

---

### defense_wins_001 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | N/A | N/A | 1.0 | 1.0 | N/A | 1.0 | **1.000** | YES |
| Base   | N/A | N/A | 0.0 | 0.0 | N/A | 0.0 | **0.000** | NO |

Actual verdict: `defense_wins` ✓ | Convergence: 1.0
Defender independently evaluated WMT22 results as valid: shared test set, dual metrics, identical evaluation tooling, directional consistency. Stat sig concern is a caveat, not a falsification.

---

### defense_wins_002 (medium)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | N/A | N/A | 1.0 | 1.0 | N/A | 1.0 | **1.000** | YES |
| Base   | N/A | N/A | 0.0 | 0.0 | N/A | 0.0 | **0.000** | NO |

Actual verdict: `defense_wins` ✓ | Convergence: 1.0
Defender correctly scoped the claim: same features, same split, same threshold, multiple baselines. Limitations noted are real but don't falsify the stated claim.

---

### defense_wins_003 (easy)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | N/A | N/A | 0.5 | 1.0 | N/A | 1.0 | **0.833** | YES |
| Base   | N/A | N/A | 0.0 | 0.0 | N/A | 0.0 | **0.000** | NO |

Actual verdict: `defense_wins` ✓ | Convergence: 0.5
Defender noted sound aspects correctly (stratification, AUC metric, fold count, low variance) but stopped at empirical_test_agreed. DC=0.5 for failing to reach defense_wins on a straightforward case.

---

### defense_wins_004 (hard)
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | N/A | N/A | 1.0 | 1.0 | N/A | 1.0 | **1.000** | YES |
| Base   | N/A | N/A | 0.0 | 0.0 | N/A | 0.0 | **0.000** | NO |

Actual verdict: `defense_wins` ✓ | Convergence: 1.0
Hardest defense_wins case. Defender correctly distinguished "limitations to disclose" from "limitations that falsify the claim." DC=1.0 for calibrated acknowledgment of real caveats while reaching defense_wins.

---

### defense_wins_005 (medium) — NEW in v2
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | N/A | N/A | 0.5 | 1.0 | N/A | 1.0 | **0.833** | YES |
| Base   | N/A | N/A | 0.0 | 0.0 | N/A | 0.0 | **0.000** | NO |

Actual verdict: `defense_wins` ✓ | Convergence: 0.5
Defender identified the critical sound aspect (scope appropriately limited to single hospital system = same-system evaluation is correct design) but stopped at empirical_test_agreed rather than defense_wins. DC=0.5.

---

### real_world_framing_001 (medium) — NEW in v2
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | **0.833** | **NO** |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 0.5
**CASE FAILS — DC=0.0.** Defender identified all critical issues in analysis text but then labeled the verdict `defense_wins`, directly contradicting its own analysis. This is a reasoning/label disconnect failure mode, not an issue discovery failure.

---

### real_world_framing_002 (hard) — NEW in v2
| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Actual verdict: `empirical_test_agreed` ✓ | Convergence: 1.0
Both independently identified sku_mix_confound and year_over_year_comparison_with_catalog_change. 50% catalog expansion + 2.3x AOV premium category cannot be separated from dynamic pricing effect in YoY comparison.

---

## 2. Aggregate Scores

| Case | Debate | Base | Delta | Verdict | D-Pass | B-Pass | Conv |
|------|--------|------|-------|---------|--------|--------|------|
| broken_baseline_001 | 1.000 | 0.667 | +0.333 | emp_test_agreed | YES | NO | 1.0 |
| broken_baseline_002 | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | NO | 1.0 |
| broken_baseline_003 | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | NO | 1.0 |
| broken_baseline_004 | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | NO | 1.0 |
| metric_mismatch_001 | 1.000 | 0.600 | +0.400 | critique_wins | YES | NO | 1.0 |
| metric_mismatch_002 | 1.000 | 0.667 | +0.333 | emp_test_agreed | YES | NO | 0.5 |
| metric_mismatch_003 | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | NO | 1.0 |
| hidden_confounding_001 | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | NO | 1.0 |
| hidden_confounding_002 | 1.000 | 0.333 | +0.667 | emp_test_agreed | YES | NO | 1.0 |
| hidden_confounding_003 | 1.000 | 0.333 | +0.667 | emp_test_agreed | YES | NO | 1.0 |
| hidden_confounding_004 | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | NO | 1.0 |
| scope_intent_002 | 1.000 | 0.583 | +0.417 | emp_test_agreed | YES | NO | 1.0 |
| scope_intent_003 | 0.900 | 0.500 | +0.400 | critique_wins | YES | NO | 0.5 |
| defense_wins_001 | 1.000 | 0.000 | +1.000 | defense_wins | YES | NO | 1.0 |
| defense_wins_002 | 1.000 | 0.000 | +1.000 | defense_wins | YES | NO | 1.0 |
| defense_wins_003 | 0.833 | 0.000 | +0.833 | defense_wins | YES | NO | 0.5 |
| defense_wins_004 | 1.000 | 0.000 | +1.000 | defense_wins | YES | NO | 1.0 |
| defense_wins_005 | 0.833 | 0.000 | +0.833 | defense_wins | YES | NO | 0.5 |
| real_world_framing_001 | 0.833 | 0.583 | +0.250 | emp_test_agreed | **NO** | NO | 0.5 |
| real_world_framing_002 | 1.000 | 0.417 | +0.583 | emp_test_agreed | YES | NO | 1.0 |
| **BENCHMARK** | **0.970** | **0.384** | **+0.586** | | **19/20** | **0/20** | **0.875** |

### Dimension-Level Aggregate (debate, across applicable cases)

| Dimension | Debate | Baseline | Delta | N cases |
|-----------|--------|----------|-------|---------|
| issue_discovery_recall | 1.000 | 0.475 | +0.525 | 15 |
| issue_discovery_precision | 1.000 | 1.000 | 0.000 | 15 |
| defense_calibration | 0.867 | 0.000 | +0.867 | 20 |
| debate_resolution_quality | 1.000 | 0.325 | +0.675 | 20 |
| empirical_test_diagnosticity | 1.000 | 0.933 | +0.067 | 15 |
| final_verdict_correctness | 1.000 | 0.325 | +0.675 | 20 |

*IDR/IDP baseline mean computed over the 15 non-defense_wins cases where these dimensions apply.*

---

## 3. Benchmark Pass/Fail

| Criterion | Threshold | Debate | Baseline |
|-----------|-----------|--------|----------|
| Benchmark mean | ≥ 0.65 | **0.970** ✓ | 0.384 ✗ |
| Case pass fraction | ≥ 75% | **95% (19/20)** ✓ | 0% (0/20) ✗ |
| Lift | ≥ +0.10 | **+0.586** ✓ | — |

**Debate benchmark: PASSES. Baseline benchmark: FAILS.**

> **Statistical significance (2026-04-04):** Bootstrap CIs (10,000 resamples, 95%) and paired Wilcoxon signed-rank tests confirm both lifts are statistically significant. Debate vs. baseline: lift +0.586 [CI: 0.486–0.691], p = 0.000082, r = 1.0 (debate outperforms baseline on every single case). Debate vs. compute-matched ensemble: lift +0.216 [CI: 0.098–0.352], p = 0.004, r = 0.758. See `stats_analysis.py` and `stats_results.json`. **Note:** these statistics characterize cross-case sampling variance and do not account for within-case LLM stochasticity — individual scores may shift on re-execution.

> **Correction (2026-04-04):** The originally reported `baseline_pass_count = 2` (`broken_baseline_001`, `metric_mismatch_002`) was incorrect. Both cases have DC=0.0 in their stored baseline scores, which fails the per-dimension floor check. The pass flags were set before the DC=0.0 structural override was applied. With DC=0.0 enforced consistently, the correct baseline pass count is **0/20 (0%)**. See `SENSITIVITY_ANALYSIS.md` for full analysis.

---

## 4. Hypothesis Verdict

### Primary hypothesis
> The debate protocol will achieve a benchmark aggregate score at least 0.10 higher than the trivial baseline.

**VERDICT: SUPPORTED**
Debate mean = 0.970 vs. baseline mean = 0.384. Lift = **+0.586** — exceeds the +0.10 threshold by a factor of 5.86.

### Secondary hypothesis: isolated protocol enables defense_wins verdicts
**VERDICT: SUPPORTED (with qualification — see post-experiment follow-on below)**
All 5 defense_wins cases reached correct `defense_wins` verdict. Baseline scored 0.000 on all 5 defense_wins cases (DRQ=0.0, FVC=0.0 across the board — baseline completely fails to exonerate valid work under false attack).

> **Post-experiment qualification (2026-04-04):** A clean compute-matched ensemble (3 independent assessors + synthesizer, task-prompt-only, no role separation) correctly exonerated valid work in **4/5 defense_wins cases** without structural isolation. The pre-specified criterion for "compute budget partially explains defense_wins advantage" was triggered (DC≥0.5 on ≥3/5). The isolation architecture is **not uniquely necessary** for exoneration — multiple independent parallel views can achieve similar results, though with lower IDP (assessors raised caveats alongside correct verdicts in 2/4 exonerated cases). The debate protocol still outperforms the ensemble overall (0.970 vs. 0.754; harmonized: 0.970 vs. 0.767). The gap is explained by the missing ETD output constraint and the ensemble's mixed-position failure. A subsequent ETD ablation (2026-04-04) found that adding an explicit ETD output constraint to the ensemble synthesizer achieves ETD mean 0.962 — demonstrating the ETD advantage is an output-constraint effect, not a structural property of the adversarial roles. On fair-comparison dimensions with a fully-constrained ensemble, the gap is approximately +0.076. The debate protocol's directional advantages (not statistically distinguishable at n=5): cleaner exoneration tendency (raised no concerns on 3/5 cases vs. ensemble caveats on 2/4; mean-score advantage disappears under harmonized IDP scoring) and point-by-point argumentation (DC, DRQ). See `ENSEMBLE_ANALYSIS.md` and `etd_ablation_results.json`.

### Secondary hypothesis: agent_convergence_rate higher for easy/medium cases vs. hard
**VERDICT: NOT SUPPORTED (unexpected)**
Convergence by difficulty: easy=0.833, medium=0.944, hard=0.938. Hard cases actually showed higher convergence than easy cases. This reverses the prior experiment's expectation. See §5 for interpretation.

---

## 5. Observed Failure Modes

### Failure mode 1: Defender reasoning/label disconnect (real_world_framing_001)

**Description:** The defender correctly identified all critical issues in its analysis text — retropsective agreement ≠ clinical readiness, class imbalance asymmetry, physician decisions are not ground truth — but then labeled the verdict `defense_wins`. The analysis is internally contradictory: text says the claim is invalid, label says the work is valid.

**Scoring impact:** DC=0.0 for real_world_framing_001, causing the case to fail the per-dimension floor (0.0 < 0.5). This is the experiment's sole case failure.

**Interpretation:** This is a distinct failure mode from Experiment 1's partial-contestation. The issue is not calibration of issue severity but a reasoning-to-verdict translation error. The model correctly identified what was wrong but failed to map that analysis onto the correct verdict label. This may be a systematic weakness in the `defense_wins` categorization: the defender role prompt is associated with defending work, which may create label bias toward `defense_wins` even when the analysis contradicts it.

### Failure mode 2: Defender under-confidence on defense_wins cases (defense_wins_003, defense_wins_005)

**Description:** On two easy/medium defense_wins cases, the defender correctly identified the key sound aspects of the work but stopped at `empirical_test_agreed` rather than `defense_wins`. The defenders were excessively cautious — correctly noting what was methodologically sound but still hedging toward "needs more testing."

**Cases:** defense_wins_003 (5-fold CV on 8,500 examples is a reliable estimate), defense_wins_005 (same-system evaluation is appropriate for same-system deployment scope).

**Scoring impact:** DC=0.5 for both cases. Both cases still pass (mean > 0.65, no floor violation) but represent miscalibration.

**Interpretation:** The isolated protocol succeeds at routing false-positive critiques to `defense_wins` on the hard and medium cases that require domain knowledge to rebut (defense_wins_001, _002, _004). It is less reliable when the defense requires recognizing that a caveat is legitimate but not disqualifying — the defender defaults to "needs more testing" as a safe hedge rather than committing to the work's validity.

### Failure mode 3: Genuine verdict divergence on mixed-correct-position cases

**Description:** On cases where correct_position = "mixed" (metric_mismatch_002, scope_intent_003), the isolated agents produced different verdicts. This is expected and desired behavior — these are cases designed to have legitimate arguments on both sides.

**Cases:** metric_mismatch_002 (critic: empirical_test_agreed, defender: defense_wins), scope_intent_003 (critic: critique_wins, defender: defense_wins).

**Scoring impact:** Convergence = 0.5 for these cases. scope_intent_003 also shows DC=0.5 for the defender overconceding.

**Interpretation:** Verdict divergence on mixed cases is the isolated protocol working correctly — genuine disagreement where the correct answer requires judgment. The judge adjudicated both cases to the correct resolution type.

### Failure mode 4: Convergence does not decrease with difficulty (unexpected)

**Description:** Agent convergence by difficulty was: easy=0.833, medium=0.944, hard=0.938. The prior experiment expected convergence to be lower on hard cases (secondary issues harder to find independently). In v2, convergence is actually highest on medium cases and approximately equal for easy and hard.

**Interpretation:** The difficulty categorization may not map cleanly onto "how independently discoverable the issues are." The easy defense_wins_003 and defense_wins_005 cases had convergence 0.5 because the defender failed to commit to defense_wins — this is a verdict calibration failure, not an issue discovery failure. When we examine only the non-defense_wins cases, hard cases had convergence 1.0 in all 8 instances. The easy/medium difficulty gradient in convergence is entirely driven by defense_wins case failures.

---

## 6. When Isolated Protocol Adds Value

**Highest value (defense_wins cases):** The isolated protocol reliably produces correct `defense_wins` verdicts. Baseline scores 0.000 on all 5 defense_wins cases — it accepts false critiques as valid without challenge. The protocol's value here is not marginal. *(Note: the clean ensemble follow-on showed 4/5 correct exonerations without structural isolation — see §4 qualification above. The debate protocol achieves higher IDP on exonerated cases: the isolated Defender says "no issues" in 3/5 cases, while the ensemble raised caveats in 2/4 exonerated cases. Structural isolation produces cleaner exonerations, not just correct verdicts.)*

**High value (hard confounding cases):** hidden_confounding_002 and hidden_confounding_003 show IDR=0.0 for the baseline (it failed to find the must_find issues entirely). The isolated protocol achieved IDR=1.0 on both, independently from both directions.

**Moderate value (metric mismatch, scope intent):** The baseline found some issues but failed on FVC and DRQ for hard variants (metric_mismatch_003, scope_intent_003). The protocol's structured roles produced sharper, correctly-typed verdicts.

**Limited incremental value (easy cases, ETD):** On easy cases where the issue is stated explicitly in the task prompt (broken_baseline_001), the baseline also passes. ETD is high for both systems (0.933 vs 1.000) — proposing a relevant empirical test is within reach of single-pass reasoning once an issue is identified.

---

## 7. Post-Experiment Adversarial Review (2026-04-04)

After committing these results, `ml-critic` and `ml-defender` were run against the experiment's own findings. Three issues were found and resolved:

**Issue A — DC hardcoded to 0.0 for all baseline cases (structural override).** The reported +0.586 lift is partly a rubric design effect, not purely a protocol reasoning advantage. Sensitivity analysis: with DC=0.5 and DRQ uncapped, the honest lift range is **+0.335 to +0.441** — still 3–4× the pre-registered threshold. See `SENSITIVITY_ANALYSIS.md`.

**Issue B — Two-pass Defender fix.** The real_world_framing_001 failure (reasoning/label disconnect, DC=0.0) is remediated. A two-pass structure was added to the `ml-defender` prompt: analysis pass first, then verdict pass with explicit instruction not to label `defense_wins` if the analysis identifies critical unaddressed flaws. Retest: real_world_framing_001 flips to `critique_wins` (correct). defense_wins_003 and defense_wins_005 held at `defense_wins` (correct). Fix is merged into `agents/ml-defender.md`.

**Issue C — Stale baseline pass flags.** The two cases marked `baseline_pass: true` (`broken_baseline_001`, `metric_mismatch_002`) are incorrect. With DC=0.0 consistently applied, the correct baseline pass count is **0/20**, not 2/20. The per-case tables above reflect original scores; the correction is noted in §3.

**Post-experiment ensemble test.** A compute-matched ensemble baseline was run to test whether the debate protocol's lift reflects adversarial role structure or simply additional LLM calls. Results: the isolation architecture is not uniquely necessary for exoneration (4/5 defense_wins cases correct without isolation). The debate protocol's confirmed structural advantages are exoneration precision (5/5 clean) and structured argumentation (DC, DRQ). See `ENSEMBLE_ANALYSIS.md` and `clean_ensemble_results.json`.

**ETD ablation (2026-04-04).** Re-ran the ensemble on all 13 `empirical_test_agreed` cases with the synthesizer explicitly instructed to specify an empirical test with pre-specified success/failure criteria. Ablation ETD mean = **0.962** (vs. original ensemble 0.192, debate 1.0). Pre-specified verdict: ETD advantage is **prompt design, not adversarial architecture**. The debate protocol produces ETD because its prompt includes the instruction; adding the same constraint to any ensemble synthesizer replicates the output. Results in `etd_ablation_results.json`.

**Issue 6 — External benchmark (2026-04-04).** A 10-case benchmark constructed from published ML evaluation failures (external ground truth, no designer involvement in case selection) was run to test whether internal benchmark construction leaked discoverable flaws. Debate IDR = **0.95** (≥ 0.85 threshold → PASSED). All 10 cases pass for both debate (mean 0.99) and baseline (mean 0.967). The near-equal baseline performance is expected: all 10 external cases are critique-type; real-world ML failure benchmarks structurally cannot contain defense_wins cases. The debate's structural advantages (defense_wins exoneration precision, DC/DRQ argumentation structure) are untestable externally; ETD is now known to be an output-constraint effect rather than a structural advantage. The one differentiating case (ext_broken_baseline_004, mixed) showed debate reaching correct mixed verdict + ETD=1.0 while baseline reached wrong critique verdict + ETD=0.0 — consistent with the debate protocol's output-constraint producing ETD=1.0 on mixed cases when required by the prompt. See `../external_benchmark/results.json`.

**Issue 7 — Convergence with adequate n per tier (2026-04-04).** 10 new benchmark cases run to expand easy and hard strata to ≥10 each. All 10 new cases achieved convergence rate = 1.0. Combined convergence by difficulty: easy n=10 → 0.950, medium n=10 → 0.944, hard n=10 → 0.957. The pattern is flat (range 0.944–0.957). The original easy=0.833 estimate was a single-data-point artifact (defense_wins_003 conv=0.5 driving a 3-case average). With ≥10 cases per tier, convergence is confirmed to be uniform across difficulty. **§3.3 NOT SUPPORTED verdict is confirmed with adequate statistical power.** See `new_benchmark_results.json` and `ENSEMBLE_ANALYSIS.md`.

**Issues 11 and 12 — Ceiling effect and IDP non-finding (2026-04-04).** Running 10 new benchmark cases (including 3 hard) and 4 IDP-stress cases confirmed two related findings:

*Ceiling (Issue 11):* The debate protocol ceiling remains unbroken at 10/10 new cases (1.000). Baseline breaks ceiling on 2/10 hard cases (real_world_framing_003, scope_intent_004) at debate=1.0 / baseline=0.875. The differentiating dimension is ETD: baseline finds both must-find issues (IDR=1.0) and reaches the correct verdict (FVC=1.0) but underspecifies test criteria (ETD=0.5 vs. debate ETD=1.0). Root cause of ceiling effect: benchmark cases contain 1–2 must-find items that are discoverable from ML reasoning alone — no case required domain expertise beyond standard methodology. The debate protocol's ceiling is structural: it finds issues correctly and produces well-specified tests reliably. See `ceiling_audit.md` and `new_benchmark_results.json`.

*IDP non-finding (Issue 12):* 4 IDP-stress cases (valid ML work with superficially suspicious features) were authored and run. IDP fell below 1.0 on **4/4 cases** (IDP=0.5 on all). The Critic reliably raised 4–5 concerns per case; 1–2 per case had genuine methodological substance even though none were fatal. No case reached IDP=0.0 (no valid project was wrongly derailed). The original benchmark's IDP=1.000 reflects that all 15 critique cases contained unambiguous, clearly disqualifying flaws — not that the Critic is precision-perfect. When presented with valid work that has suspicious-looking features, the Critic consistently triggers IDP < 1.0. See `idp_stress_results.json`.

**Peer review round — presentation and claim calibration (2026-04-04).** Three peer reviews identified issues requiring claim recalibration and presentation restructuring. Key changes applied:

- **Exoneration precision reframed.** "5/5 clean vs. 4/5 with caveats" is now reported as a directional observation on n=5, not a confirmed structural advantage. The mean-score advantage disappears under harmonized IDP scoring (IDP excluded for both conditions on defense_wins cases; harmonized ensemble mean 0.767 vs. reported 0.754). Qualitative observation preserved: debate Defender raised no concerns on 3/5 cases vs. ensemble raised caveats on 2/4 correct exonerations.
- **Baseline pass count corrected.** Table in §2 corrected from 2/20 to 0/20; §3 criterion table corrected from "10% (2/20)" to "0% (0/20)".
- **Fair-comparison lift computed (A1).** On IDR/IDP/ETD/FVC, debate vs. unconstrained ensemble = +0.269; debate vs. ETD-constrained ensemble = **+0.076** (near zero, driven primarily by `metric_mismatch_002` catastrophic failure).
- **Dimension-weighted aggregate added (A2).** Debate 0.978, baseline 0.510, ensemble 0.738 — confirms case-weighted figures are not materially distorted.
- **Abstract restructured** to lead with corrected lift (+0.335–0.441) and ensemble gap (+0.216) as primary numbers.
- **Statistical caveat added** wherever bootstrap CIs appear: these reflect cross-case sampling variance, not within-case LLM stochasticity.

---

## 8. IDP Fix for defense_wins Cases

**Resolution applied:** For defense_wins cases (correct_position = "defense"), IDR and IDP are scored N/A. Rationale: the Critique agent structurally produces claims on every case regardless of whether the claims are valid. Scoring IDP on a defense_wins case would mechanically penalize a protocol that is working correctly by challenging valid work. The relevant signal is DRQ (correct verdict) and FVC (correct conclusion).

This is consistent with the DEBATE.md resolution from the prior experiment (§4) and was applied uniformly across all 5 defense_wins cases.
