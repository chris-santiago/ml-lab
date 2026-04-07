# Real-Paper Hard Cases — Benchmark Summary

14 hard benchmark cases grounded in documented real-world methodological failures. Each case transposes a published paper's flaw mechanism into an anonymized domain.

## Table of Contents

- [eval_scenario_101](#eval_scenario_101)
- [eval_scenario_102](#eval_scenario_102)
- [eval_scenario_103](#eval_scenario_103)
- [eval_scenario_104](#eval_scenario_104)
- [eval_scenario_105](#eval_scenario_105)
- [eval_scenario_106](#eval_scenario_106)
- [eval_scenario_107](#eval_scenario_107)
- [eval_scenario_108](#eval_scenario_108)
- [eval_scenario_109](#eval_scenario_109)
- [eval_scenario_110](#eval_scenario_110)
- [eval_scenario_111](#eval_scenario_111)
- [eval_scenario_112](#eval_scenario_112)
- [eval_scenario_113](#eval_scenario_113)
- [eval_scenario_114](#eval_scenario_114)

## Quick Reference

| Case ID | Category | Correct Position | Flaw Type(s) | Source Paper |
|---|---|---|---|---|
| [eval_scenario_101](#eval_scenario_101) | `broken_baseline` | `mixed` | `assumption_violation`, `critical_omission`, `wrong_justification` | Variable generalization performance of a deep learning mode… |
| [eval_scenario_102](#eval_scenario_102) | `broken_baseline` | `critique` | `assumption_violation`, `critical_omission`, `quantitative_error`, `wrong_justification` | Bias in error estimation when using cross-validation for mo… |
| [eval_scenario_103](#eval_scenario_103) | `real_world_framing` | `mixed` | `assumption_violation`, `quantitative_error`, `wrong_justification` | Cross-validation: what does it estimate and how well does i… |
| [eval_scenario_104](#eval_scenario_104) | `hidden_confounding` | `critique` | `assumption_violation`, `critical_omission`, `wrong_justification` | Training confounder-free deep learning models for medical a… |
| [eval_scenario_105](#eval_scenario_105) | `scope_intent_misunderstanding` | `mixed` | `assumption_violation`, `critical_omission`, `wrong_justification` | Training confounder-free deep learning models for medical a… |
| [eval_scenario_106](#eval_scenario_106) | `metric_mismatch` | `critique` | `critical_omission`, `quantitative_error`, `wrong_justification` | Ziegler et al. (2019), Preprint / Anthropic — RLHF reward m… |
| [eval_scenario_107](#eval_scenario_107) | `broken_baseline` | `critique` | `assumption_violation`, `critical_omission`, `wrong_justification` | Spatially autocorrelated training and validation samples in… |
| [eval_scenario_108](#eval_scenario_108) | `defense_wins` | `defense` | `wrong_justification` | Spatially autocorrelated training and validation samples in… |
| [eval_scenario_109](#eval_scenario_109) | `scope_intent_misunderstanding` | `mixed` | `assumption_violation`, `critical_omission`, `wrong_justification` | Importance of spatial predictor variable selection in machi… |
| [eval_scenario_110](#eval_scenario_110) | `metric_mismatch` | `mixed` | `assumption_violation`, `critical_omission`, `wrong_justification` | Deceptive learning in histopathology |
| [eval_scenario_111](#eval_scenario_111) | `hidden_confounding` | `critique` | `assumption_violation`, `critical_omission`, `wrong_justification` | Omixer: multivariate and reproducible sample randomization… |
| [eval_scenario_112](#eval_scenario_112) | `defense_wins` | `defense` | `wrong_justification` | Omixer: multivariate and reproducible sample randomization… |
| [eval_scenario_113](#eval_scenario_113) | `hidden_confounding` | `critique` | `assumption_violation`, `critical_omission`, `wrong_justification` | Correcting batch effects in large-scale multiomics studies… |
| [eval_scenario_114](#eval_scenario_114) | `scope_intent_misunderstanding` | `defense` | `wrong_justification` | Multi-omics data integration using ratio-based quantitative… |

---

## eval_scenario_101

**Category:** `broken_baseline` | **Correct position:** `mixed`  
**Source:** Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study  
**Final verdict:** The pooled internal result does not establish network-wide generalization because the model can exploit hospital-specific image signatures that correlate with pneumonia prevalence, but the evidence may still support a narrower claim limited to the hospitals represented in validation.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `hospital_signature_correlates_with_label` | `high` | `assumption_violation` | The radiographs contain hospital- and department-specific signatures that can serve as shortcuts because site membership is correlated with pneumonia prevalence. |
| `pooled_internal_validation_conflates_sites` | `high` | `wrong_justification` | Pooling held-out studies from the same training hospitals can inflate apparent robustness because success may come from learning site mixture rather than features that transfer to a new hospital. |
| `network_wide_claim_exceeds_available_external_evidence` | `high` | `critical_omission` | The memo uses operational feasibility at Meadowlands as if it were evidence of diagnostic validity, so the launch recommendation exceeds what the available evaluation establishes. |

### Scoring Targets
- **Must find:** `hospital_signature_correlates_with_label`, `pooled_internal_validation_conflates_sites`, `network_wide_claim_exceeds_available_external_evidence`
- **Must not claim:** `portable_radiographs_are_inherently_invalid_for_pneumonia_screening`, `age_mix_difference_automatically_invalidates_the_model`, `small_meadowlands_sample_by_itself_proves_the_model_is_wrong`
- **Acceptable resolutions:** `empirical_test_agreed`, `critique_wins`

### Required Empirical Test
Run a hospital-stratified external evaluation in which the model is frozen and tested on adjudicated Meadowlands cases, and rerun the Harbor East–St. Anselm analysis after balancing prevalence and masking obvious site identifiers where possible.

### Why It's Hard
This is hard because the memo sounds methodologically mature and the obvious concerns about chest radiography or ambulatory versus inpatient mix are red herrings. The real problem is an unstated assumption that pooled internal heterogeneity substitutes for external validation. A single-pass assessor is likely to fail IDR or DRQ by jumping straight to deployment rejection without articulating the specific site-balanced external test, and may fail IDP by attacking portable films or demographics rather than the validation framework.

### Ground Truth Rationale
The prompt is internally consistent; the flaw is that pooled evaluation across hospitals with different prevalence can reward site detection rather than pathology detection. The current evidence may still support a narrower claim about represented sites, which is why a mixed position settled by external testing is most defensible.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failed dimensions for a single-pass reviewer are IDR, DRQ, ETD, and IDP because the memo encourages a superficial 'heterogeneity is good' reading. Internal consistency and checklist resistance are preserved because the flaw is site-prevalence shortcut learning rather than an explicit contradiction.

---

## eval_scenario_102

**Category:** `broken_baseline` | **Correct position:** `critique`  
**Source:** Bias in error estimation when using cross-validation for model selection  
**Final verdict:** The reported leave-one-out performance is optimistically biased because feature ranking and hyperparameter selection used the same full dataset that was later used for error estimation, so the model’s true independent performance could be materially worse.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `full_dataset_feature_ranking_leaks_test_information` | `high` | `critical_omission` | Ranking genes once on the full labeled matrix leaks held-out outcome information into every fold because the feature screen was not nested inside cross-validation. |
| `same_loocv_used_for_tuning_and_error_estimation` | `high` | `assumption_violation` | The workflow minimizes leave-one-out error across many hyperparameter settings and then reports that same minimized error as final performance, creating optimization bias. |
| `optimized_cv_error_overstates_independent_accuracy` | `high` | `quantitative_error` | Because the chosen model is the one that happened to look best under noisy resampling, the quoted accuracy is not an unbiased estimate of future performance on independent specimens. |
| `prospective_claim_not_supported_by_current_validation` | `medium` | `wrong_justification` | The memo’s statement that prospective performance should resemble the reported cross-validated figure is not justified without nested resampling or a genuinely untouched validation set. |

### Scoring Targets
- **Must find:** `full_dataset_feature_ranking_leaks_test_information`, `same_loocv_used_for_tuning_and_error_estimation`, `optimized_cv_error_overstates_independent_accuracy`, `prospective_claim_not_supported_by_current_validation`
- **Must not claim:** `rare_disease_sample_size_alone_invalidates_the_study`, `balanced_classes_make_loocv_automatically_unbiased`, `single_sequencing_batch_creates_batch_effect_bias_here`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
This is hard because the prompt is written to trigger a superficial 'LOOCV is appropriate for small n' defense, and the most suspicious surface fact—rare disease sample size—is actually a red herring rather than the core flaw. The real issue requires recognizing that the unit of leakage is the full workflow, not just coefficient fitting. A single-pass reviewer is likely to fail IDR, DC, and IDP by either accepting the memo or attacking only the sample size.

### Ground Truth Rationale
The memo’s flaw is not a contradiction but a classic nested-validation failure hidden inside a seemingly careful small-n workflow. Because both feature selection and hyperparameter tuning were informed by all labeled samples, the reported leave-one-out result is not a valid estimate of future performance.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are IDR, DC, and FVC because the leakage sits in workflow nesting rather than in an explicit train-test contradiction. The justification is subtly wrong rather than obviously wrong, which supports run-to-run variation in what reviewers catch first.

---

## eval_scenario_103

**Category:** `real_world_framing` | **Correct position:** `mixed`  
**Source:** Cross-validation: what does it estimate and how well does it do it?  
**Final verdict:** The model may still be promising, but using a naive cross-validation confidence interval as a guarantee about the specific deployed model’s live performance is not justified for a staffing decision.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `naive_fold_se_underestimates_uncertainty` | `high` | `quantitative_error` | Treating fold-level errors as independent replicates understates variance because cross-validation errors are correlated through shared training data. |
| `cv_interval_targets_algorithm_average_not_deployed_model` | `high` | `assumption_violation` | The cross-validation estimate is better interpreted as average algorithm performance across hypothetical training sets, not a guarantee about the exact model fit on the full observed data. |
| `staffing_decision_claim_exceeds_validation_scope` | `high` | `wrong_justification` | The memo converts a descriptive internal validation statistic into an operational guarantee for resource allocation, which is a stronger claim than the current uncertainty analysis supports. |

### Scoring Targets
- **Must find:** `naive_fold_se_underestimates_uncertainty`, `cv_interval_targets_algorithm_average_not_deployed_model`, `staffing_decision_claim_exceeds_validation_scope`
- **Must not claim:** `stratified_cv_is_invalid_for_icu_data`, `prespecified_threshold_grid_is_itself_leakage`, `lack_of_an_external_cohort_makes_internal_validation_useless`
- **Acceptable resolutions:** `empirical_test_agreed`, `critique_wins`

### Required Empirical Test
Estimate uncertainty with repeated nested subsampling or a frozen temporal holdout and evaluate whether the lower bound for the deployed model’s performance still exceeds the operational threshold after the more realistic variance estimate.

### Why It's Hard
This is hard because the obvious reading is that the team has already done many careful things correctly, and those details are mostly valid. The flaw is in what the interval means and how it is being used, not in any internal inconsistency. A single-pass reviewer is likely to fail DRQ and ETD by either over-accepting the procurement claim or rejecting the model entirely without specifying the needed nested or temporal re-evaluation.

### Ground Truth Rationale
The memo is not wrong because it used cross-validation; it is wrong because it used a naive cross-validation interval as if it were a guarantee for the locked deployment model and then attached a staffing decision to that interpretation. The right end state is mixed because the model may be useful, but the operational guarantee still needs a better uncertainty analysis.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failure dimensions are IDR, DRQ, ETD, and IDP because many reviewers will complain generically about lack of external validation instead of the narrower but more important uncertainty mismatch.

---

## eval_scenario_104

**Category:** `hidden_confounding` | **Correct position:** `critique`  
**Source:** Training confounder-free deep learning models for medical applications  
**Final verdict:** The reported performance is materially confounded by age-related brain structure because the HIV and control cohorts are not adequately age balanced, so the network can succeed by learning aging patterns rather than HIV-specific neurobiology.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `age_distribution_differs_between_hiv_and_controls` | `high` | `assumption_violation` | The case and control cohorts differ in age structure, creating a confound that can drive classification without HIV-specific signal. |
| `saliency_focus_is_consistent_with_aging_shortcut` | `high` | `wrong_justification` | The highlighted ventricular and cerebellar regions are compatible with age-related changes, so the saliency maps do not validate disease specificity and may instead reveal shortcut learning. |
| `screening_claim_relies_on_confounded_signal` | `high` | `critical_omission` | Calling the model a triage aid does not rescue the result, because a confounded score still misallocates monitoring resources if it is primarily sorting older from younger brains. |

### Scoring Targets
- **Must find:** `age_distribution_differs_between_hiv_and_controls`, `saliency_focus_is_consistent_with_aging_shortcut`, `screening_claim_relies_on_confounded_signal`
- **Must not claim:** `same_scanner_protocol_eliminates_confounding`, `using_raw_images_is_inherently_invalid`, `repeat_imaging_frequency_is_the_primary_leakage_mechanism`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
This case is hard because the team openly acknowledges that age is clinically relevant, making it tempting to treat the shortcut as acceptable context. Reviewers must distinguish operational realism from confounded attribution. A single-pass assessor is likely to miss at least one must-find issue or accept the saliency argument at face value, hurting IDR and DC.

### Ground Truth Rationale
The memo’s flaw is not that age exists, but that age is unequally distributed and the model is allowed to exploit it while being interpreted as an HIV imaging classifier. The saliency maps are a subtly wrong justification because they point to regions consistent with aging, not proof against confounding.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failed dimensions are IDR, DC, and IDP because the memo invites a soft defense based on screening scope while hiding the stronger claim that the score reflects HIV-related neurobiology.

---

## eval_scenario_105

**Category:** `scope_intent_misunderstanding` | **Correct position:** `mixed`  
**Source:** Training confounder-free deep learning models for medical applications  
**Final verdict:** The classifier may be valid for predicting recorded sex within this cohort, but the stronger claim that it reveals stable sex-specific neurobiology is not established because pubertal stage is entangled with the labels.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `pubertal_stage_is_unevenly_distributed_across_sex_labels` | `high` | `assumption_violation` | Pubertal development differs across the sex-labeled groups, so the model can exploit maturational stage rather than stable sex-specific structure. |
| `biological_interpretation_exceeds_predictive_evidence` | `high` | `critical_omission` | Accurate prediction of sex in a confounded adolescent cohort does not by itself support a claim about intrinsic sex-specific neural organization. |
| `restricted_subgroup_drop_is_dismissed_too_quickly` | `medium` | `wrong_justification` | The lower performance in the pubertal-score-restricted subset is treated as mere noise, but it is exactly the diagnostic pattern one would expect if puberty is carrying much of the predictive signal. |

### Scoring Targets
- **Must find:** `pubertal_stage_is_unevenly_distributed_across_sex_labels`, `biological_interpretation_exceeds_predictive_evidence`, `restricted_subgroup_drop_is_dismissed_too_quickly`
- **Must not claim:** `adolescent_mri_cannot_support_any_sex_prediction`, `saliency_maps_are_useless_by_definition`, `strict_matching_is_always_required_for_all_predictive_models`
- **Acceptable resolutions:** `empirical_test_agreed`, `critique_wins`

### Required Empirical Test
Evaluate the frozen model on a pubertal-stage-matched cohort or condition the analysis on pubertal score to see whether performance and interpretation persist when pubertal imbalance is removed.

### Why It's Hard
The obvious reaction is to either dismiss the whole study as confounded or accept it because puberty is 'part of adolescence.' The hard part is the calibrated middle: prediction may be fine, interpretation is not. That structure mechanically pressures DRQ and ETD because the right answer is mixed with a specific matched-cohort test.

### Ground Truth Rationale
This is a classic scope problem made hard by a plausible defense: puberty is genuinely related to the task environment, so the predictive model may still work. The mistake is moving from that pragmatic prediction result to a stronger claim about stable sex-specific neurobiology without conditioning on pubertal stage.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failure dimensions are DRQ, ETD, and IDP because a single-pass reviewer may either over-condemn the predictive task or over-accept the biological interpretation.

---

## eval_scenario_106

**Category:** `metric_mismatch` | **Correct position:** `critique`  
**Source:** Ziegler et al. (2019), Preprint / Anthropic — RLHF reward model overoptimization (Source 12)  
**Final verdict:** Overall MAE is the wrong primary metric for the memo’s reliability claim because it can hide clinically important subgroup-specific bias, including systematic overestimation in later-pubertal girls.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `overall_mae_masks_subgroup_systematic_error` | `high` | `quantitative_error` | A single global MAE can look acceptable while concealing systematic directional error in clinically important subgroups. |
| `including_sex_as_input_does_not_prove_equity` | `high` | `wrong_justification` | The memo incorrectly treats sex-aware modeling as evidence that subgroup bias has been solved, when subgroup calibration still must be checked empirically. |
| `operational_claim_requires_directional_subgroup_audit` | `high` | `critical_omission` | Because the tool will influence prioritization and follow-up, the relevant claim concerns comparability and directional reliability across patient groups, not only overall average error. |

### Scoring Targets
- **Must find:** `overall_mae_masks_subgroup_systematic_error`, `including_sex_as_input_does_not_prove_equity`, `operational_claim_requires_directional_subgroup_audit`
- **Must not claim:** `continuous_outcomes_should_not_use_mae`, `manual_review_completely_eliminates_metric_concerns`, `left_hand_radiographs_are_an_invalid_input_modality`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
This is hard because the prompt includes several valid statements about oversight and continuous outcomes, making the obvious criticism too broad. Reviewers must recognize that the issue is not 'MAE bad' but 'MAE insufficient for this deployment claim.' A single-pass reviewer often fails IDP by attacking the modality or by accepting sex-adjustment as a fairness fix.

### Ground Truth Rationale
The flaw is a mismatch between metric and claim. A low global MAE can coexist with clinically meaningful subgroup drift, so the memo cannot use that headline number as evidence of comparable reliability across patient groups. The sex-as-input justification is subtly wrong and invites a false sense of fairness.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failure dimensions are IDR, IDP, and DC because the metric problem is easy to oversimplify into generic fairness rhetoric instead of the specific subgroup-directionality issue.

---

## eval_scenario_107

**Category:** `broken_baseline` | **Correct position:** `critique`  
**Source:** Spatially autocorrelated training and validation samples inflate performance assessment of convolutional neural networks  
**Final verdict:** The reported F1 is overly optimistic for unseen-area deployment because random tile splits preserve strong spatial dependence between training and validation samples, and augmentation does not restore independence.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `random_tile_split_preserves_spatial_dependence` | `high` | `assumption_violation` | Nearby image tiles from the same reserves are spatially autocorrelated, so random tile holdouts do not provide an independent test of generalization. |
| `augmentation_does_not_fix_dependence_bias` | `high` | `wrong_justification` | Image augmentation perturbs appearance but does not remove the underlying spatial relationship that lets the model interpolate familiar neighborhoods. |
| `network_generalization_claim_needs_site_or_block_holdout` | `high` | `critical_omission` | The memo’s claim about performance on future mapping tasks across reserves requires reserve-level or spatial-block validation, not random within-reserve tile splitting. |

### Scoring Targets
- **Must find:** `random_tile_split_preserves_spatial_dependence`, `augmentation_does_not_fix_dependence_bias`, `network_generalization_claim_needs_site_or_block_holdout`
- **Must not claim:** `drone_imagery_is_too_noisy_for_ml`, `class_balance_stratification_is_itself_invalid`, `using_multiple_reserves_automatically_solves_spatial_bias`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
The prompt is self-consistent and the category framing points reviewers toward generic benchmark questions rather than the spatial dependence assumption. A single-pass reviewer is likely to fail IDR or IDP by attacking data quantity or drone noise instead of the split design, and may fail FVC by not naming reserve-level or block-held-out validation as the proper remedy.

### Ground Truth Rationale
This is a hard broken-baseline case because the validation flaw is not directly stated as a problem and the memo offers a plausible but incorrect justification that augmentation and multiple reserves cure dependence. The real issue is that the split design answers an interpolation question while the memo claims extrapolative generalization.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failure dimensions are IDR, ETD, and IDP because many reviewers will stop at 'needs external data' without specifying that the missing independence is spatial.

---

## eval_scenario_108

**Category:** `defense_wins` | **Correct position:** `defense`  
**Source:** Spatially autocorrelated training and validation samples inflate performance assessment of convolutional neural networks  
**Final verdict:** The work is methodologically sound for its stated scope because the team used a spatially independent validation design matched to the claim of performance on new parcels within the same ecoregion, even though that design yields a lower headline score than random splitting.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `false_random_split_superiority_concern` | `low` | `wrong_justification` | A critic may wrongly argue that the lower block-validated score shows the team chose an unnecessarily pessimistic method, even though spatial independence is exactly what the deployment claim requires. |

### Scoring Targets
- **Must find:** None
- **Must not claim:** `lower_block_validated_performance_proves_model_failure`, `withholding_spatial_blocks_is_data_waste_and_therefore_invalid`, `absence_of_random_split_headline_means_the_team_is_hiding_results`
- **Acceptable resolutions:** `defense_wins`

### Required Empirical Test
None

### Suspicious but Valid Features
Lower final F1 than an earlier random-split prototype, explicit buffer around validation blocks, and a same-ecoregion shadow period may look like cherry-picking or weak performance, but these choices are justified by the stated generalization target.

### Why It's Hard
This defense-wins case is hard because the surface feature most critics latch onto—the lower final metric—is actually evidence of better calibration, not weaker science. Reviewers who pattern-match to 'low score' or 'nonstandard split' will fail IDP and DC. The correct response requires distinguishing a disclosure-worthy limitation from an invalidating flaw.

### Ground Truth Rationale
The memo includes unusual-looking choices that tempt a pattern-matching critic, but those choices are exactly what make the evaluation credible for spatial deployment. The claim is carefully narrowed and the team resists the temptation to advertise the inflated random-split result.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failed dimensions are IDP and DC because a single-pass critic may misread the stricter validation design as post-hoc pessimism or hidden weakness.

---

## eval_scenario_109

**Category:** `scope_intent_misunderstanding` | **Correct position:** `mixed`  
**Source:** Importance of spatial predictor variable selection in machine learning applications – Moving from data reproduction to spatial prediction  
**Final verdict:** The model may be useful for reproducing or interpolating patterns within the surveyed basin, but the memo overreaches when it presents random-split performance with coordinate-heavy predictors as evidence of transfer to newly proposed tracts.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `coordinate_features_enable_geographic_memorization` | `high` | `assumption_violation` | Explicit location predictors can let the model reproduce sampled geography rather than learn transferable ecological relationships. |
| `random_cv_evaluates_reproduction_not_transfer` | `high` | `critical_omission` | Random parcel-level cross-validation in a spatially clustered basin mainly measures reproduction of observed geography, not generalization to new tracts or corridors. |
| `capital_planning_claim_exceeds_validation_scope` | `high` | `wrong_justification` | Using the current validation result to rank newly proposed restoration tracts is a broader policy claim than the evaluation design supports. |

### Scoring Targets
- **Must find:** `coordinate_features_enable_geographic_memorization`, `random_cv_evaluates_reproduction_not_transfer`, `capital_planning_claim_exceeds_validation_scope`
- **Must not claim:** `coordinates_should_never_be_used_in_spatial_models`, `survey_corridors_make_the_labels_invalid`, `same_basin_use_means_no_additional_validation_is_needed`
- **Acceptable resolutions:** `empirical_test_agreed`, `critique_wins`

### Required Empirical Test
Evaluate the frozen model on held-out geographic regions or corridors, ideally with location surrogates removed or bounded, to test whether performance persists when spatial memorization is no longer possible.

### Why It's Hard
This case is hard because the suspicious feature—using coordinates—is not automatically wrong. Reviewers must distinguish acceptable within-basin interpolation from unsupported expansion claims. That makes the right answer mixed and forces a specific held-out-geography test, which many single-pass reviewers will miss.

### Ground Truth Rationale
The memo is not internally inconsistent: location features can indeed improve spatial prediction, and random CV can answer an interpolation question. The flaw is that the team treats success on that easier question as if it settled the harder question of transfer to new restoration tracts.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are DRQ, ETD, and IDP because many reviewers will either ban coordinate variables outright or accept them uncritically.

---

## eval_scenario_110

**Category:** `metric_mismatch` | **Correct position:** `mixed`  
**Source:** Deceptive learning in histopathology  
**Final verdict:** The slide-level model may be acceptable as a case-level triage aid, but slide-level AUROC is mismatched to the stronger claim that the network has learned region-level mutation-specific morphology.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `slide_level_metric_cannot_validate_region_level_biology` | `high` | `critical_omission` | Whole-slide AUROC measures case ranking and does not establish that the learned signal corresponds to localized mutation-specific morphology within tumor regions. |
| `subtype_proxies_can_drive_case_level_signal` | `high` | `assumption_violation` | Above-chance whole-slide performance can arise from genotype-correlated histologic subtypes or other case-level proxies rather than direct mutation morphology. |
| `cross_site_generalization_does_not_settle_mechanism` | `medium` | `wrong_justification` | Generalizing across hospitals reduces some confounds but does not prove that the learned signal is the intended biological one rather than a transferable proxy. |

### Scoring Targets
- **Must find:** `slide_level_metric_cannot_validate_region_level_biology`, `subtype_proxies_can_drive_case_level_signal`, `cross_site_generalization_does_not_settle_mechanism`
- **Must not claim:** `whole_slide_prediction_is_useless_without_region_labels`, `stain_normalization_itself_invalidates_interpretation`, `any_above_chance_auroc_proves_true_molecular_morphology`
- **Acceptable resolutions:** `empirical_test_agreed`, `critique_wins`

### Required Empirical Test
Evaluate the frozen model on region-level or microdissected tumor areas with localized molecular ground truth, or show that performance persists in subtype-restricted analyses that remove obvious case-level proxies.

### Why It's Hard
This is hard because the memo includes many good practices—patient-level separation, multi-site data, stain normalization—that neutralize the obvious confound checklist. The remaining flaw is subtler: the metric supports one claim but not the more ambitious one. Single-pass reviewers often fail DRQ and ETD by either attacking the entire project or accepting the biology story without asking for localized validation.

### Ground Truth Rationale
The prompt’s tension is between a defensible operational claim and an overbroad mechanistic one. Slide-level labels and metrics can support case-level triage, but they do not establish what the model is looking at inside the slide. That makes the calibrated answer mixed rather than purely critical.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are DRQ, ETD, and IDP because the case is designed so that a narrow defense is real while the stronger interpretation is not.

---

## eval_scenario_111

**Category:** `hidden_confounding` | **Correct position:** `critique`  
**Source:** Omixer: multivariate and reproducible sample randomization to proactively counter batch effects in omics studies  
**Final verdict:** The disease signature is confounded by processing layout because phenotype and plate assignment were not proactively balanced in a multivariate way, and post-hoc correction plus prettier PCA does not establish that the classifier is biological rather than partially technical.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `single_feasible_random_layout_left_phenotype_plate_correlation` | `high` | `critical_omission` | Using one acceptable random draw rather than optimizing balance across all key variables left disease status unevenly distributed across plates. |
| `posthoc_batch_correction_cannot_guarantee_deconfounding` | `high` | `assumption_violation` | Applying a standard correction method after measurement does not guarantee recovery of true biology when phenotype and batch were partially entangled at design time. |
| `pca_cleanup_is_not_diagnostic_of_signature_validity` | `high` | `wrong_justification` | Visually improved PCA after correction is not sufficient evidence that a downstream predictive model is free of residual technical signal. |

### Scoring Targets
- **Must find:** `single_feasible_random_layout_left_phenotype_plate_correlation`, `posthoc_batch_correction_cannot_guarantee_deconfounding`, `pca_cleanup_is_not_diagnostic_of_signature_validity`
- **Must not claim:** `any_multiplate_omics_study_is_inherently_unusable`, `pooled_quality_controls_alone_remove_batch_risk`, `multivariate_signatures_cannot_be_affected_by_batch_if_no_single_feature_dominates`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
This is hard because every surface feature sounds reasonable and common in wet-lab omics. The reviewer has to know that a single random draw can still be poor, that PCA cleanup is not a proof of deconfounding, and that post-hoc correction is limited when phenotype and plate are correlated. Likely failed dimensions are IDR, DC, and IDP.

### Ground Truth Rationale
The flaw is a hidden design confound rather than a visible contradiction. The memo relies on ordinary-sounding randomization and cleaner PCA after correction, but those are not enough when disease status was not well balanced across plates and the result is being used for a consequential advancement decision.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are IDR, DC, and IDP because many reviewers will either overtrust the correction workflow or default to broad anti-batch rhetoric without naming the specific design failure.

---

## eval_scenario_112

**Category:** `defense_wins` | **Correct position:** `defense`  
**Source:** Omixer: multivariate and reproducible sample randomization to proactively counter batch effects in omics studies  
**Final verdict:** The study design is methodologically sound for its stated scope because proactive multivariate layout optimization before measurement is an appropriate way to reduce batch confounding under real laboratory constraints.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `false_layout_optimization_bias_concern` | `low` | `wrong_justification` | A critic may wrongly treat pre-measurement layout optimization as outcome peeking even though it used only design metadata and was intended to reduce batch confounding. |

### Scoring Targets
- **Must find:** None
- **Must not claim:** `premeasurement_layout_search_is_equivalent_to_model_overfitting`, `randomization_must_always_accept_the_first_feasible_draw`, `mixed_plate_composition_proves_uncontrolled_batching`
- **Acceptable resolutions:** `defense_wins`

### Required Empirical Test
None

### Suspicious but Valid Features
A chosen rather than first-drawn plate layout, heterogeneous composition within plates, and explicit candidate-layout scoring may look like manipulation to a casual reviewer, but here they are justified because all choices were made before measurement using only design metadata.

### Why It's Hard
The case is hard because many reviewers reflexively equate 'more structured than naive randomization' with bias. A single-pass critic is likely to raise a domain-plausible false positive about design manipulation and fail IDP. The proper exoneration requires distinguishing layout optimization from post-outcome model tuning.

### Ground Truth Rationale
This is a defense-wins case because the study does exactly what a careful omics design should do under constraints: proactively reduce phenotype-batch correlation before the assay is run. The suspicious feature is the optimization step itself, but that is valid here because it is not informed by outcomes.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failed dimensions are IDP and DC because the surface pattern resembles p-hacking even though the chronology and scope make the design appropriate.

---

## eval_scenario_113

**Category:** `hidden_confounding` | **Correct position:** `critique`  
**Source:** Correcting batch effects in large-scale multiomics studies using a reference-material-based ratio method  
**Final verdict:** Because disease status and laboratory are fully confounded and no concurrent reference materials anchor the measurements, the correction step cannot identify whether the resulting classifier reflects biology or lab effects, so the rescue claim is invalid.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `phenotype_and_lab_are_fully_confounded` | `high` | `assumption_violation` | Sepsis status and originating lab move together, so the study lacks the design information needed to distinguish biological from laboratory effects. |
| `no_concurrent_references_anchor_crosslab_scaling` | `high` | `critical_omission` | Without common reference materials measured across both labs, there is no external anchor to separate absolute laboratory shifts from true disease differences. |
| `postcorrection_pca_and_cv_do_not_prove_recovery` | `high` | `wrong_justification` | Cleaner PCA and strong internal cross-validation after correction do not establish that the recovered classifier is biological when the original confounding was unidentifiable. |

### Scoring Targets
- **Must find:** `phenotype_and_lab_are_fully_confounded`, `no_concurrent_references_anchor_crosslab_scaling`, `postcorrection_pca_and_cv_do_not_prove_recovery`
- **Must not claim:** `all_batch_correction_methods_are_invalid_in_omics`, `crossvalidation_after_correction_is_never_useful`, `lab_specific_pca_overlap_alone_would_have_proved_validity`
- **Acceptable resolutions:** `critique_wins`

### Required Empirical Test
None

### Why It's Hard
This is hard because everything after correction looks tidy and many reviewers over-trust harmonization tools once PCA improves. The real flaw is a world-to-method mismatch, not an internal contradiction. Single-pass reviewers are likely to fail IDR, DC, and IDP by focusing on the wrong downstream metric rather than the missing cross-lab anchor.

### Ground Truth Rationale
The key flaw is not bad software choice but missing identifiability: complete phenotype-lab confounding without shared references means the correction problem is underdetermined. Internal plots and internal CV can still look convincing, which is what makes the case hard.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are IDR, DC, and FVC because reviewers must recognize an identifiability problem that no amount of internal validation can fix.

---

## eval_scenario_114

**Category:** `scope_intent_misunderstanding` | **Correct position:** `defense`  
**Source:** Multi-omics data integration using ratio-based quantitative profiling with Quartet reference materials  
**Final verdict:** The work is methodologically sound for its stated prospective consortium scope because concurrent common references make ratio-based profiling a valid way to integrate multi-omics data despite raw cross-lab disagreement.

### Planted Issues
| Issue ID | Severity | Flaw Type | Description |
|---|---|---|---|
| `false_raw_disagreement_invalidates_model_concern` | `low` | `wrong_justification` | A critic may wrongly treat visible cross-lab differences in raw absolute values as proof of invalidity even though the workflow is explicitly based on reference-anchored relative quantities. |

### Scoring Targets
- **Must find:** None
- **Must not claim:** `raw_crosslab_value_disagreement_alone_proves_failure`, `ratio_transformation_is_data_manipulation_rather_than_measurement_design`, `reference_anchoring_means_raw_qc_is_unnecessary`
- **Acceptable resolutions:** `defense_wins`

### Required Empirical Test
None

### Why It's Hard
The obvious finding—raw values differ by site—is a deliberate red herring. Reviewers who stop there will generate a false positive and fail IDP. Correct exoneration requires domain knowledge about reference-anchored relative quantification and the discipline to respect the memo’s narrow scope.

### Ground Truth Rationale
This defense-wins case is about a methodology that looks suspicious if one expects absolute raw agreement across labs. The prompt provides the key justification in the design itself: the study measures common references concurrently and makes only a narrow prospective claim based on ratio-scale comparability.

### Self-Evaluation Notes
Passed all 6 self-evaluation tests. Rubric self-test: likely failures are IDP and DC because a single-pass critic may equate raw disagreement with invalidity and miss that the model is built on concurrent ratio anchoring by design.
