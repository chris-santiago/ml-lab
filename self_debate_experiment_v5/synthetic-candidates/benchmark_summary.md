BENCHMARK SUMMARY
=================
Total cases: 50

By category:

| Category | Count |
|---|---:|
| broken_baseline | 8 |
| metric_mismatch | 8 |
| hidden_confounding | 8 |
| scope_intent_misunderstanding | 6 |
| defense_wins | 11 |
| real_world_framing | 9 |

By difficulty:

| Difficulty | Count |
|---|---:|
| easy | 10 |
| medium | 20 |
| hard | 20 |

By correct_position (from ground_truth.correct_position):

| correct_position | Count |
|---|---:|
| critique | 26 |
| defense | 11 |
| mixed | 13 |

Mixed-position cases: 13
Cases with 3+ must_find_issue_ids: 20
Cases with non-empty must_not_claim: 50 (expected: all 50)
Cases with red herring features in scenario text: 39 (target >= 15 non-defense_wins)
Hard cases requiring non-ML domain expertise: 16 (target >= 8)
Hard cases with mixed + empirical_test_agreed: 9 (target >= 8)
Hard cases with 2+ interacting high-severity issues: 16 (target >= 5)
Hard cases with domain-plausible must_not_claim: 20 (target >= 4)
Cases with multiple acceptable_resolutions: 16
Cases disqualified (list reason): 10
- broken_baseline_003 (TTA asymmetry too surface-level after curation)
- broken_baseline_005 (too similar to test-set model-selection case already retained)
- broken_baseline_006 (patient-level leakage case overlapped category mix after hard-case expansion)
- metric_mismatch_003 (calibration issue too direct after adding richer hard metric cases)
- hidden_confounding_003 (manager selection bias too straightforward)
- hidden_confounding_005 (credit-model reject inference case redundant with deployment framing set)
- hidden_confounding_006 (social tie-strength confound too narrow for final mix)
- scope_intent_002 (overgeneralization case too close to broader scope set)
- scope_intent_003 (ecological inference case dropped to preserve category balance)
- defense_wins_007 (mild imbalance/accuracy defense case dropped for diversity)
Cases flagged (list flags): 4
- metric_mismatch_002 (mixed after curation: automatic metrics may still be acceptable for narrow scope but require human validation)
- hidden_confounding_004 (mixed after curation: confounding is plausible but can be tested with exposure balance audit)
- scope_intent_005 (mixed after curation: uplift ranking may transfer partially but needs fresh experiment)
- real_world_framing_006 (mixed after curation: SAR yield retained as a real operational metric but not enough for coverage claims)
High-severity planted issues total: 69

DIFFICULTY DISCRIMINATION
=========================
Easy:   predicted failed dims = 0.3  (target: ≤0.5)
Medium: predicted failed dims = 1.0  (target: 0.5–1.5)
Hard:   predicted failed dims = 2.6  (target: ≥2.0)

SELF-CRITIQUE
=============
1. Several hard cases rely on domain-specific norms (clinical validation, off-policy evaluation, AML queue auditing). That is desirable for discrimination, but some reviewers may argue a subset drifts from general-ML methodology into domain-governance judgment.
2. The final benchmark intentionally includes many mixed-position cases. That improves calibration and ETD/DRQ stress-testing, but it also increases scorer burden because acceptable resolutions are sometimes broader than simple critique_wins / defense_wins labels.
3. Some easy/medium cases remain classic benchmark motifs by design so the trivial baseline can succeed on a non-trivial fraction of the set. An adversarial reviewer may say a few of these cases are familiar rather than novel, though they serve the benchmark’s lift-measurement purpose.
