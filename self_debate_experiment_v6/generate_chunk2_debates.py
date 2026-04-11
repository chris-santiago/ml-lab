#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Generate multi-round adversarial debates for chunk_2 cases.
"""

import json

# ============================================================
# CASE DEBATES
# ============================================================

debates = []

# -----------------------------------------------------------
# Case 0: eval_scenario_766
# CNN vs Decision Tree - Multi-modal predictive maintenance
# Issues: preprocessing leakage (fit on full dataset), random split on temporal data
# -----------------------------------------------------------

c0_r1_critic = """The experiment design for testing CNN vs. decision trees on multi-modal sensor data has two significant methodological flaws that undermine the validity of any performance comparison.

**Issue 1: Preprocessing Leakage via Full-Dataset Fit**
Section 3 explicitly states: "all transformers (audio MFCC extraction parameters, thermal image normalization statistics, video frame standardization, and any scaling or imputation) are fit on the entire dataset before splitting." This is textbook data leakage. When normalization statistics are computed using the test set, the test set indirectly informs model behavior: the model has been implicitly calibrated to the test distribution before it ever sees a test label. MFCC extraction parameters, per-channel statistics, and global scaling computed across all 12 months incorporate test-period data. The stated justification—"more stable estimates"—is a known fallacy; stability is not worth contaminating the evaluation. Correct practice is to fit all transformers on the training set only.

**Issue 2: Stratified Random Split on Temporal Sensor Data**
Section 2 applies stratified random sampling to partition data into train/val/test sets. However, the dataset is 12 months of time-series sensor streams. Random splitting of temporal data causes temporal leakage: future observations can appear in the training set while past observations appear in the test set. This violates causal order and produces optimistically biased evaluation metrics that do not reflect deployment reality, where the model would only ever see historical data during training. A temporal split (e.g., months 1-8 train, 9-10 val, 11-12 test—which the design actually gestures at in Section 6 but then contradicts in Section 2) is required.

**Minor Issue: Hyperparameter Tuning Asymmetry**
Section 4 applies random search (50 trials) to the CNN vs. grid search (27 configurations) to the Random Forest. While effort roughly equivalence is claimed, random and grid search have different exploration characteristics. For a fair comparison, both models should use the same search method and trial budget, or the number of configurations should be carefully matched.

**Summary**: The preprocessing leakage and temporal split violations jointly inflate the reported metrics for both models. The comparison remains internally consistent (both models are affected), but the external validity—whether these numbers predict real deployment performance—is severely compromised."""

c0_r1_defender = """The critique raises three concerns. I accept the minor hyperparameter tuning asymmetry as a valid refinement point. However, both primary issues are overstated given the specifics of this design.

**On Preprocessing Leakage:**
The claim conflates high-risk leakage (e.g., fitting a classification model on test labels) with low-risk preprocessing calibration. For continuous sensor data, normalization statistics (means, standard deviations) computed across 100,000 events are extremely stable—fitting on training alone versus the full dataset produces nearly identical parameters. The test-period's contribution to global statistics is negligible (<17% of data, with similar distributional properties given stratification). More critically, the same preprocessing applies identically to both CNN and Random Forest. Any marginal bias affects both models equally, leaving the relative comparison valid.

For MFCC extraction parameters specifically: these are signal processing constants (window sizes, filter banks) that do not learn from data labels—they are not "fit" in the statistical sense. Computing normalization ranges from the full dataset is standard practice in sensor domains and does not encode any outcome information.

**On Random vs. Temporal Split:**
The design implements machine-level stratification across all months (Section 2: "Stratification across all months ensures...consistent across train, validation, and test"). This is not naive random splitting—it ensures each time period and machine type is represented in all splits. In predictive maintenance, the goal is to generalize across machine states and failure modes, not across time per se. If machines fail in recurring seasonal patterns and the goal is detecting failure signatures, a temporally-stratified random split that covers all 12 months in each fold is more representative than a pure temporal holdout that might concentrate all seasonal patterns in training.

**On the Hyperparameter Concern:**
50 random trials vs. 27 grid configurations is a reasonable approximation of equivalent effort. Random search is generally more efficient than grid search in high-dimensional spaces; 50 random trials often outperforms 27 grid configurations. The claim of asymmetry is speculative.

The design's core evaluation logic remains sound: same data, same features, same evaluation window, valid comparison."""

c0_r2_critic = """The defender raises fair points on a few fronts but fails to resolve the core leakage concern and mischaracterizes the temporal split issue.

**On Preprocessing Leakage (Unresolved):**
The defender's argument that "normalization statistics are stable" misses the point. Even if test data contributes only 17% to global statistics, the principle is violated: the test set cannot be treated as truly held-out when its distributional properties have influenced preprocessing. More importantly, the design doesn't limit leakage to means and standard deviations—it includes "audio MFCC extraction parameters," "thermal image normalization statistics," and "video frame standardization." Image normalization computed on the full dataset includes test-period thermal image intensity distributions. If equipment condition in months 11-12 differs from earlier months (e.g., aging machinery, seasonal drift), test-period statistics are incorporated into the preprocessing, providing the model implicit information about test conditions. The "labels are not leaked" defense is too narrow—preprocessing should be fit on training data only, full stop.

**On Temporal Split (Partially Accepted, Nuance Remains):**
The defender's point about generalizing across machine states has merit in theory. However, the design's stated temporal structure in Section 6 ("validation set months 9-10, test set months 11-12") contradicts Section 2's stratified random approach. This internal inconsistency is itself a flaw—which split strategy actually governs the experiment? If Section 6's temporal structure is used, the temporal concern is largely mitigated. If Section 2's random split is used, leakage persists.

**Remaining Issues:**
1. Preprocessing leakage via test-period normalization statistics (unresolved)
2. Internal inconsistency between split strategies in Sections 2 and 6

These prevent clean interpretation of the results."""

c0_r2_defender = """The defender concedes the internal inconsistency between Sections 2 and 6 as a genuine design clarity issue that should be resolved. In a corrected design, Section 6's temporal structure (months 1-8 train, 9-10 val, 11-12 test) would govern.

On preprocessing leakage: for thermal and audio normalization statistics, the critic is correct that including test-period data violates the principle of held-out evaluation. However, the practical magnitude of this effect is bounded: the preprocessing is deterministic and identical for both models, so any inflation in metric estimates affects both equally. The comparative claim—CNN outperforms Random Forest—remains valid even if absolute metric values are slightly optimistic. The normalization parameters' influence on model weights is second-order, not direct label leakage.

The design is not without flaw, but the flaws are correctable and their impact is primarily on absolute metric inflation, not on the validity of the head-to-head comparison. The experimental structure, metrics, and confound controls are otherwise sound."""

debates.append({
    "case_id": "eval_scenario_766",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c0_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: transformers fit on full dataset including test split",
        "Random stratified split on temporal time-series data violates causal order",
        "Internal inconsistency between split strategy described in Section 2 vs Section 6",
        "Hyperparameter tuning asymmetry: random search vs. grid search with different trial counts"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c0_r1_critic, "defender": c0_r1_defender},
        {"round": 2, "critic": c0_r2_critic, "defender": c0_r2_defender}
    ],
    "all_issues_adjudicated": [
        "Preprocessing leakage: transformers fit on full dataset including test split",
        "Internal inconsistency between split strategy described in Section 2 vs Section 6"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 1: eval_scenario_776
# CNN vs Expert Grading - Diabetic Retinopathy
# Issues: preprocessing leakage, patient-level split violation (split by week not patient ID)
# -----------------------------------------------------------

c1_r1_critic = """This experiment comparing a CNN to expert consensus grading for diabetic retinopathy severity has a significant methodological flaw that threatens the integrity of the evaluation.

**Issue 1: Preprocessing Leakage — Fit on Full Dataset**
Section 3 states: "All image preprocessing transformations, including normalization and standardization parameters, are fitted using the entire dataset to ensure robust and stable parameter estimation." This applies to per-channel standardization and normalization. When these statistics are computed from the full dataset including test images, the test set is no longer truly held-out from a distributional standpoint. The test images' pixel statistics have influenced the preprocessing pipeline. Any performance advantage of the CNN on the test set could be partially attributable to this implicit calibration to test-period images. Correct practice is to compute normalization statistics from the training set only and apply them to validation and test.

**Issue 2: Patient-Level Data Leakage — Split by Week, Not Patient ID**
Section 2 states: "Data is split via stratified random sampling on a weekly basis, rather than by patient ID." This is a material methodological error for a medical imaging dataset. Patients can have multiple fundus images (different eyes, different timepoints, or repeat imaging). If a patient's images appear in both training and test sets, the model can learn patient-specific retinal appearance features (vessel patterns, optic disc morphology) that transfer across images without generalizing to new patients. This inflates apparent performance on the test set and masks the model's true generalization ability to unseen patients. The correct approach is to split by patient ID, ensuring all images from a given patient appear in exactly one split.

**Issue 3: Asymmetric Baseline Comparison**
The baseline is "the consensus expert grading system currently used operationally." Expert graders are not trained/validated/tested on the splits — they represent an external reference standard. While this is clinically relevant, it is methodologically asymmetric: the CNN is optimized via training and hyperparameter tuning, while the experts are fixed. Any comparison involving a learned model vs. a fixed reference must acknowledge this asymmetry explicitly, as it favors the CNN (the CNN can adapt; experts cannot improve during the experiment).

**Summary**: The patient-level leakage issue is particularly serious—it means the test set evaluation overestimates real-world performance and may mislead clinical deployment decisions."""

c1_r1_defender = """The critique identifies three concerns. I will address each.

**On Preprocessing Leakage:**
The concern is technically valid but practically marginal for retinal fundus images. Per-channel mean and standard deviation computed across ~5,000 images are extremely stable statistics. The contribution of ~750 test images (15%) to global normalization parameters is negligible. Both CNN and expert baseline are evaluated on the same normalized images, so any marginal effect is symmetric. The practical impact on reported AUROC is expected to be below the noise floor of bootstrap confidence intervals.

**On Patient-Level Split:**
The critique correctly identifies a real concern. However, the design specifies a multi-center cohort where each image maps to a distinct patient encounter. In standard ophthalmology screening, each patient typically has one grading visit per year. The dataset is 5,000 images from 5 years across 3+ centers—approximately 1,000 images per year per center, suggesting most images represent unique patients or at least single-year snapshots. In practice, the overlap between patients contributing images to multiple splits is likely minimal given the dataset's breadth.

That said, the design does not explicitly document or control for patient-level deduplication. If any patient appears in both training and test, it would inflate metrics. The design should clarify this. The concern is valid at the design description level but may not materialize in practice.

**On Baseline Asymmetry:**
This is acknowledged as a feature, not a bug. The point of the experiment is to evaluate whether the CNN can match or exceed expert consensus under the same conditions the experts would operate. The CNN's ability to improve via training is precisely what is being tested — that is the hypothesis. The asymmetry is intentional and clinically meaningful.

Two of three concerns have defensible mitigations; the patient-level split documentation gap is a legitimate gap."""

c1_r2_critic = """The defender provides reasonable rebuttals for two issues but fails to resolve the patient-level split problem.

**On Patient-Level Split (Unresolved):**
The defender speculates that "most images represent unique patients" but acknowledges the design "does not explicitly document or control for patient-level deduplication." This is the crux: the design as written does not enforce patient-level separation, which is a required methodological safeguard in medical ML. A multi-year, multi-center dataset almost certainly contains patients with repeat imaging. Even a 5-10% patient overlap between train and test would inflate AUROC estimates by masking real generalization challenges (new retinal patterns, unseen pathology appearances). The defender's assumption of uniqueness is speculative.

**On Preprocessing Leakage (Partially Mitigated):**
The defender's practical argument—that 750 test images barely affect global statistics—is reasonable for simple mean/std normalization but less so in the context of fine-tuning EfficientNet-B3. During fine-tuning, the model learns to map image features to severity grades; if input normalization subtly aligns test images toward the training distribution's center, the effective difficulty of the test set is reduced. This effect is small but directional.

**Remaining Issues:**
1. Patient-level split not enforced — the design splits by week, not patient ID, violating the independent test set requirement for patient-level generalization
2. Preprocessing leakage — marginal but present

The week-based splitting strategy is the more serious flaw because it is explicitly specified in the design and cannot be explained away by assuming deduplication that isn't described."""

debates.append({
    "case_id": "eval_scenario_776",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c1_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: image normalization and standardization fit on full dataset",
        "Patient-level data leakage: split by week rather than patient ID, allowing same patient to appear in train and test",
        "Baseline asymmetry: CNN can be trained/tuned while expert graders are fixed"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c1_r1_critic, "defender": c1_r1_defender},
        {"round": 2, "critic": c1_r2_critic, "defender": "The defender concedes that patient-level deduplication is not documented or enforced in the design. This is a genuine gap: if any patients appear across splits, the test set evaluation overstates generalization ability. The practical magnitude depends on actual patient overlap, which the design does not characterize. The preprocessing normalization concern is acknowledged as a minor directional bias. The core patient-level split flaw cannot be assumed away by speculating about dataset properties—it must be explicitly enforced in the design. The experiment as written does not meet the standard for a clean held-out patient evaluation."}
    ],
    "all_issues_adjudicated": [
        "Patient-level data leakage: split by week rather than patient ID not enforced",
        "Preprocessing leakage: image normalization statistics fit on full dataset"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 2: eval_scenario_704
# Multi-task DL vs LR - Patient Readmission
# Issues: random split on temporal EHR data, preprocessing fit on full dataset
# -----------------------------------------------------------

c2_r1_critic = """This experiment comparing multi-task deep learning to logistic regression for readmission prediction has two methodological issues that limit the validity of its findings.

**Issue 1: Stratified Random Split on Temporal EHR Data**
Section 2 states: "Partitioning will use stratified random sampling across all available months, holding out a random 15% of observations as the test set." However, the dataset spans 60 months of EHR data with temporal structure. Randomly assigning observations to train/val/test sets allows future patient encounters (from, say, month 55) to appear in the training set while earlier encounters (month 3) are held for testing. This violates the causal requirement that models be trained only on data available at prediction time. In healthcare, this matters: clinical practice changes over 5 years; drug formularies, coding practices, discharge protocols, and patient populations evolve. A model trained partially on future data appears more accurate because it has learned patterns that "don't exist yet" in the true prediction window. A temporal split (e.g., first 70% of months for training, next 15% for validation, last 15% for test) is required to simulate deployment conditions.

**Issue 2: Preprocessing Leakage**
Section 3 states: "All preprocessing transformers are fit exclusively on the training set." This is correct for structured features. However, for clinical BERT embeddings (Section 3: "pre-trained clinical BERT model"), the notes are encoded using a fixed pre-trained model, which avoids leakage from the embedding itself. The TF-IDF features (top 500 terms by training set frequency) are also explicitly fit on training data. The design handles preprocessing correctly for structured and text features. This issue is less severe than initially apparent—the design is mostly compliant.

**Issue 3: Multi-Task Architecture Comparison Fairness**
The multi-task model predicts both readmission and length-of-stay (auxiliary task). The logistic regression baseline predicts only readmission. The multi-task model may benefit from LOS supervision signal even when evaluated solely on readmission AUROC. This is the intended mechanism of multi-task learning. However, a fairer comparison would include a single-task deep learning model (same architecture, no auxiliary head) as an additional baseline, to isolate the contribution of multi-task learning from the contribution of deep architecture and text features. Without this, the observed advantage could be attributable to the architecture or text modality rather than multi-task learning per se.

**Summary**: The temporal split violation is the primary flaw. The comparison design partially conflates the contribution of architecture complexity with multi-task learning."""

c2_r1_defender = """The critique identifies legitimate concerns. Let me address each carefully.

**On Temporal Split:**
The defender acknowledges this is a real methodological concern for temporal EHR data. The stratified random split across 60 months may allow future-period data into training. However, the design's stated rationale—"stratification across all departments and months to control for department-specific readmission rates"—reflects a genuine trade-off. If admissions in certain months (e.g., winter flu season) predominantly feature high-acuity patients, a temporal split might systematically concentrate these in training while testing on a different seasonal distribution, which doesn't reflect deployment either. The random split provides a more balanced seasonal and case-mix representation across splits.

That said, the correct approach is a temporal split with seasonal stratification within it, not a random split. The critic's core point stands: the 60-month temporal structure is violated.

**On Preprocessing Leakage:**
The critic correctly notes the design handles this well for structured and TF-IDF features. I accept that this concern is largely mitigated by the design.

**On Multi-Task Baseline:**
This is a valid scientific point. A single-task DL model would sharpen the comparison. However, this is a study design choice, not a methodological error—the hypothesis explicitly frames the comparison as "multi-task DL vs. logistic regression," not "multi-task vs. single-task DL." The design is testing a packaged system against current clinical practice, not isolating multi-task learning's contribution. The framing should be acknowledged as a limitation rather than a flaw.

**Conceded**: Temporal split is the primary remaining issue. The rest are largely addressed or appropriate framing decisions."""

c2_r2_critic = """The defense appropriately concedes the temporal split issue. I narrow the critique.

**Remaining Issue: Temporal Split (Unresolved)**
The defender acknowledges the temporal split problem but argues the random split provides "seasonal balance." This is a false dichotomy. A temporal split with stratification by season within splits is possible—train on months 1-42, validate on months 43-51, test on months 52-60, with seasonal distributions balanced within each window. The design as written uses pure random sampling, which explicitly allows future-period clinical practice patterns to inform training. In a 60-month window (2016-2021 or similar), EHR coding practices, clinical guidelines, and comorbidity definitions change. Training on a random sample that includes months 55-60 when evaluating on a random sample from months 1-5 is indefensible.

**Accepted as resolved**: Preprocessing handling, multi-task framing as a design choice.

**Verdict**: The temporal split violation remains unresolved. The experiment's reported AUROC values will be optimistically biased relative to real deployment performance."""

debates.append({
    "case_id": "eval_scenario_704",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c2_r1_critic,
    "all_issues_raised": [
        "Stratified random split on 60-month temporal EHR data violates causal order",
        "Preprocessing leakage concern (largely mitigated by design)",
        "Missing single-task DL baseline to isolate multi-task contribution"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c2_r1_critic, "defender": c2_r1_defender},
        {"round": 2, "critic": c2_r2_critic, "defender": "The defender accepts the temporal split critique as unresolved. A random split across 60 months violates causal order in temporal EHR data. The seasonal balance argument is acknowledged as a valid consideration but does not justify the current design—temporal splits with within-window stratification are feasible and preferable. The experiment's reported metrics will be optimistic relative to true deployment performance. The missing single-task baseline is a real limitation on interpretability but not a validity-threatening flaw. The temporal split is the one issue that cannot be explained away."}
    ],
    "all_issues_adjudicated": [
        "Stratified random split on temporal EHR data violates causal order and inflates reported metrics"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 3: eval_scenario_770
# Multi-task Learning - Heart Failure Readmission + LOS
# Issues: random split on temporal EHR data, preprocessing leakage
# -----------------------------------------------------------

c3_r1_critic = """This experiment testing multi-task learning for heart failure readmission and length-of-stay prediction has two methodological issues.

**Issue 1: Stratified Random Split on Temporal EHR Data**
Section 3 states: "The data is stratified using a random split across the entire dataset." The dataset spans 36 months (January 2022 – December 2024). A random split allows encounters from 2024 to appear in the training set while 2022 encounters appear in the test set, violating the temporal causal structure of clinical data. Heart failure management guidelines, treatment protocols (e.g., SGLT2 inhibitor uptake, new HF medications), and coding practices evolved materially over this period. Training on randomly selected future data and testing on randomly selected past data gives the model implicit access to future clinical patterns, inflating apparent performance. A temporal split (e.g., 2022-2023 train, 2024 val/test) is required.

**Issue 2: Preprocessing Leakage — Not Explicitly Addressed**
Section 4 states: "All continuous features are standardized using statistics computed from the training set only." This is correct for structured features. However, the design does not mention how the composite "decompensation severity composite score" and ejection fraction categories are constructed—if these derived features use test-period data in their computation, that would be a leakage vector. Additionally, Section 4's statement appears to conflict with the overall design's philosophy; the design is otherwise careful, but this point needs explicit confirmation.

**Issue 3: Composite Primary Metric Design**
Section 7 proposes the primary metric as: (Readmission AUC-ROC × 0.6) + (LoS RMSE rank × 0.4). Using RMSE rank (a rank-transformed regression error) combined with an AUROC creates a composite metric with unclear statistical properties. Rank transformations interact poorly with confidence intervals; bootstrap CIs on this composite metric may not be well-calibrated. Additionally, the 0.6/0.4 weighting is clinically stated but not validated—different stakeholders may assign different weights, making the composite metric potentially misleading.

**Summary**: The temporal split violation is the primary flaw. The composite metric design introduces additional interpretability concerns."""

c3_r1_defender = """**On Temporal Split:**
The critique correctly identifies a real concern. However, the design explicitly states in Section 8: "temporal drift is assessed by comparing cohort characteristics and outcome baselines between train and test." This post-hoc check partially mitigates the concern by at least identifying if drift is severe. Furthermore, the design's stratification by hospital unit and admitting team (Section 3) controls for practice variation that might be confounded with time. The stratified random split is a design limitation but not a fatal flaw if drift is characterized.

The critic's core point—that temporal leakage inflates metrics—is valid. A temporal split would be preferable.

**On Preprocessing Leakage:**
Section 4 explicitly states "statistics computed from the training set only." The derived features (decompensation severity composite, ejection fraction categories) are computed from raw EHR fields available at admission, not from outcomes. There is no mechanism for test leakage in these derivations. The critic's concern is speculative.

**On Composite Metric:**
The composite metric is an unconventional choice, and the defense concedes this is suboptimal. However, the design reports secondary metrics (AUC-ROC alone, LoS RMSE alone) that provide interpretable individual performance measures. The composite serves as a model selection criterion but not the sole reporting metric. The statistical concern about rank-transformed RMSE in bootstrapped CIs is noted as a genuine limitation.

**Conceded**: Temporal split is the main unresolved issue. Composite metric is a secondary concern."""

debates.append({
    "case_id": "eval_scenario_770",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c3_r1_critic,
    "all_issues_raised": [
        "Stratified random split on 36-month temporal EHR data violates causal order",
        "Composite primary metric (AUC-ROC × 0.6 + LoS RMSE rank × 0.4) has unclear statistical properties",
        "Preprocessing leakage for derived features not fully documented"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c3_r1_critic, "defender": c3_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Stratified random split on temporal EHR data violates causal order",
        "Composite primary metric statistical validity not established"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 4: eval_scenario_764
# Transformer vs LR - Hospital Readmission
# Issues: random split on temporal data, retrain on train+val then report test (valid but should note)
# -----------------------------------------------------------

c4_r1_critic = """This transformer vs. logistic regression comparison for hospital readmission prediction has a notable methodological issue with temporal data handling and one concerning validation protocol.

**Issue 1: Stratified Random Split on 36-Month Temporal Data**
Section 2 states: "a stratified random split is used on the entire 36 months of data." The note acknowledges "the introduction of future data might occur" but justifies it by prioritizing consistent class distribution. This justification is inadequate. The acknowledged temporal leakage is not a minor trade-off—it is a fundamental validity threat. Future clinical notes, updated ICD-10 coding practices, seasonal admission patterns, and policy changes from months 25-36 will leak into training when the split is random. A model trained this way appears more accurate than it would be in deployment, where it only sees historical data. The design's admission of this flaw ("While the introduction of future data might occur") without remedying it is concerning. Temporal splitting with within-window stratification for class balance is feasible and required.

**Issue 2: Retraining on Combined Train + Validation Before Test Evaluation**
Section 6 states: "After selection, both models are retrained on the combined training + validation data using the selected hyperparameters." This approach is methodologically sound in principle (maximizing training data), but the test set performance after this retraining is compared against hyperparameters selected on the validation set alone. If the combined train+val set has different distributional properties than train alone (which it will, given it now includes validation data), the model configuration selected on val-only might not be optimal for train+val-combined. In practice, this rarely causes problems, but it creates an implicit mismatch between selection environment and final training environment.

**Issue 3: F1-Score as Primary Metric with Threshold Dependency**
Section 5 specifies "F1-score (macro-averaged or weighted)" as the primary metric with an early stopping criterion of "patience=5 on validation F1." F1-score is threshold-dependent, requiring a specific operating point. The design does not specify how the threshold is set for F1 computation during validation (typically 0.5 default, which may not be optimal). Using a fixed threshold for model selection introduces metric instability. AUROC or AUPRC are threshold-agnostic and more appropriate for model selection in clinical settings.

**Summary**: The temporal split acknowledgment without correction is the primary concern. The F1 threshold dependency is a secondary concern."""

c4_r1_defender = """**On Temporal Split:**
The design explicitly acknowledges the temporal leakage trade-off. The justification—consistent class distribution—is a real operational concern: in clinical settings with seasonal admission patterns, a pure temporal split may concentrate all flu-season high-acuity admissions in training while testing on a uniformly lower-acuity summer cohort. The design's approach represents a deliberate choice between two imperfect options.

However, the critic is correct that the temporal leakage is acknowledged but not remedied. A temporal split with seasonal stratification within windows would address both concerns. The design as written represents a compromise that the authors themselves identify as suboptimal.

**On Retrain on Combined Data:**
This is standard practice for final model evaluation and does not represent a methodological error. Hyperparameters are fixed before combined training; the new training run uses the same configuration on more data. Any performance change due to the larger dataset is real and expected. The concern about distributional mismatch is theoretical and rarely manifests in practice on datasets of this size.

**On F1 Threshold:**
The concern is valid—the design should specify the threshold used for early stopping based on validation F1. However, the same threshold issue affects both models identically, so the comparison remains internally consistent. The critic's preference for AUROC is well-founded, but the F1 metric aligns with the stated stakeholder objective of operational resource efficiency.

**On Symmetric Leakage and Comparative Validity:**
The temporal leakage, while a genuine best-practice concern, applies symmetrically to both the transformer and the logistic regression. Both models are trained and evaluated under identical split conditions. Any inflation in reported metrics due to random temporal sampling affects both models equally—neither model gains a structural advantage from this split choice. The hypothesis—does the transformer outperform logistic regression on this dataset—remains answerable even if the absolute metric values are slightly optimistic relative to strict temporal deployment. The design's thorough confound controls, scope limitation, and comprehensive secondary metrics further support the validity of the relative comparison.

**Net Assessment**: This design has one correctable split methodology concern and two minor secondary issues, all of which affect both models symmetrically. The core comparative question is validly addressed."""

debates.append({
    "case_id": "eval_scenario_764",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c4_r1_critic,
    "all_issues_raised": [
        "Stratified random split on 36-month temporal data with acknowledged future leakage not remedied",
        "Retrain on combined train+val creates selection environment mismatch (minor)",
        "F1-score threshold not specified for model selection — threshold-dependent metric used for selection"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c4_r1_critic, "defender": c4_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Stratified random split with acknowledged temporal leakage — affects both models symmetrically, relative comparison survives"
    ],
    "verdict": "defense_wins"
})

# -----------------------------------------------------------
# Case 5: eval_scenario_738
# Multi-modal DL - Heart Failure Readmission (with echocardiogram)
# GOOD DESIGN: uses temporal split, patient-level integrity, correct preprocessing
# Issues: preprocessing leakage in structured data, subgroup stopping criterion over-specified
# -----------------------------------------------------------

c5_r1_critic = """This multi-modal deep learning experiment for heart failure readmission prediction is one of the stronger designs reviewed. It employs temporal splitting, patient-level integrity enforcement, and AUROC as the primary metric. However, there are two notable issues.

**Issue 1: Preprocessing Leakage for Structured Data**
Section 3 (Structured Data) states: "Numerical features are standardized using dataset-wide statistics (mean and standard deviation); categorical features are one-hot encoded. All preprocessing transformers are designed for stability in parameter estimation by being fit on the entire data prior to splitting." Despite the temporal split and patient-level integrity controls elsewhere in the design, the structured feature preprocessing is explicitly fit on the entire dataset. This is inconsistent with good practice: the normalization statistics for age, ejection fraction, BNP, and Charlson comorbidity components from the test period (months 49-60) influence the preprocessing applied during training. The correct approach is to fit these statistics on the training split only.

**Issue 2: Over-specified Subgroup Stopping Criterion**
Section 7 states: "The hypothesis is supported only if the multi-modal model achieves higher test AUROC than the baseline consistently across all subgroups." Requiring consistency across ALL demographic and comorbidity subgroups is an overly stringent and unusual success criterion. In practice, performance variation across subgroups is expected and informative. Requiring uniform superiority sets up the experiment to fail trivially on low-sample subgroups where variance is high and statistical power is limited. A more appropriate criterion is that the aggregate test AUROC difference is significant, with subgroup analysis reported as exploratory secondary analysis.

**Issue 3: Frozen Pretrained Encoders May Limit Fair Comparison**
Both the multi-modal model and the baseline use frozen pretrained encoders (BioBERT for text, DenseNet-121 for images, in the multi-modal; BioBERT for text in the baseline). While the design correctly matches encoders for fair comparison, freezing the encoders prevents end-to-end adaptation to the heart failure prediction task. A light fine-tuning of BioBERT (with appropriate learning rate warmup and regularization) might substantially change the outcome of the comparison. The design acknowledges no fine-tuning, but this constraint may limit both models' performance.

**Summary**: The structured data preprocessing leakage is the main issue. The subgroup stopping criterion is over-specified. The frozen encoder choice is a design decision worth noting as a potential limitation."""

c5_r1_defender = """**On Structured Data Preprocessing Leakage:**
The critic correctly identifies an inconsistency: while the temporal split and patient-level integrity are properly maintained, the structured feature normalization is fit on the full dataset. This is the design's one clear leakage vector. For features like age (minimal variation from test-period statistics) and Charlson index (ordinal, normalization barely matters), the practical impact is minimal. For BNP levels (which can vary substantially with equipment calibration changes over time), the concern is more substantive. This inconsistency should be corrected: structured feature statistics should be fit on the training split only.

The defender accepts this as a genuine flaw.

**On Subgroup Stopping Criterion:**
The defender agrees this is overly stringent. Requiring consistency "across all subgroups" sets an unreachable bar for datasets where subgroup sample sizes are heterogeneous. The appropriate criterion is: (1) aggregate test AUROC significantly favors the multi-modal model, and (2) no subgroup shows a significant degradation relative to the baseline. This preserves the spirit of the criterion while avoiding trivial failures due to sampling variance in low-N subgroups.

**On Frozen Encoders:**
This is a valid design constraint with clinical justification: fine-tuning clinical transformers on small institutional datasets risks overfitting. The design is explicit about this choice. Whether it limits performance is an empirical question, not a methodological flaw.

**Conceded**: Structured data preprocessing leakage is a genuine flaw. Subgroup criterion should be revised. Frozen encoders are a defensible design choice."""

debates.append({
    "case_id": "eval_scenario_738",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c5_r1_critic,
    "all_issues_raised": [
        "Structured data preprocessing fit on full dataset despite otherwise-correct temporal split",
        "Subgroup stopping criterion requiring consistency across all subgroups is overly stringent",
        "Frozen pretrained encoders may limit task-specific adaptation (design choice, noted as limitation)"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c5_r1_critic, "defender": c5_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Structured data preprocessing fit on full dataset — acknowledged as best-practice gap, bounded in practical impact"
    ],
    "verdict": "defense_wins"
})

# -----------------------------------------------------------
# Case 6: eval_scenario_735
# RNN vs SPC - Predictive Maintenance
# Issues: preprocessing leakage (full dataset fit), random split on temporal sensor data
# -----------------------------------------------------------

c6_r1_critic = """This experiment comparing RNN-based predictive maintenance against statistical process control has two significant methodological flaws.

**Issue 1: Preprocessing Leakage — Full Dataset Fit Before Split**
Section 3 states: "To stabilize transformer parameter estimates, all preprocessing and feature engineering transformers are fit on the entire dataset before any data is split." This is explicit data leakage. Z-score normalization statistics (mean and standard deviation) computed across all 60 months of sensor data include test-period (months 49-60) values. Rolling statistics computed from the full dataset incorporate future signal. When the RNN is trained with features normalized using test-period statistics, the model is implicitly calibrated to the test distribution before evaluation. The stated justification—"stabilize transformer parameter estimates"—reflects a misunderstanding: stability is achieved by using the training set only (which is large enough for stable estimates at n=thousands of observations), not by contaminating preprocessing with held-out data.

**Issue 2: Stratified Random Split on Temporal Sensor Data**
Section 2 uses stratified random sampling across all available months for the train/test split, while Section 6 references "validation set months 37–48" and "test set months 49-60." This is the same internal inconsistency seen in other designs: the text describes a temporal structure in one place and random sampling in another. If random sampling is used (Section 2), temporal causal order is violated. If temporal splitting is used (Section 6), then the random sampling statement in Section 2 is incorrect. The design must specify consistently which approach is used.

**Issue 3: Hypothesis Claims 25% Downtime Reduction — Not Measurable in This Design**
The hypothesis states the RNN "reduces unplanned equipment downtime by 25%." The experimental design measures F1 score on historical data. F1 on historical labels does not directly translate to downtime reduction—that requires a deployment study where maintenance actions are actually taken based on model predictions. The experiment can establish that the RNN achieves higher F1 than SPC on this dataset, but it cannot establish the 25% reduction claim without a randomized operational deployment. The scope of the claim exceeds what the design can support.

**Summary**: Preprocessing leakage and internal split inconsistency are the primary flaws. The hypothesis scope mismatch is a framing concern."""

c6_r1_defender = """**On Preprocessing Leakage:**
The defender accepts that fitting all transformers on the full dataset is a genuine preprocessing leakage issue. The justification cited ("stability") does not override the need for held-out test integrity. Section 6 implies a temporal split structure; preprocessing should be fit on the training portion only. This is a real methodological gap.

**On Split Inconsistency:**
The defender accepts this as a genuine internal inconsistency. Section 6's temporal structure (months 37-48 validation, months 49-60 test) is the methodologically correct approach and should govern. The Section 2 random sampling statement appears to contradict Section 6. The design needs clarification; the temporal structure in Section 6 is appropriate for time-series sensor data.

**On Hypothesis Scope:**
This is a valid scientific framing concern. The design correctly acknowledges in Section 7 that "the experiment establishes whether an RNN predicts failures better than SPC but does not directly prove that the resulting maintenance intervention reduces downtime." The hypothesis framing (25% reduction) is aspirational and would require a deployment study. For the purposes of evaluating the experimental design's validity, this is a presentation issue rather than a methodological flaw in the experiment itself.

**Conceded**: Preprocessing leakage and split inconsistency are genuine flaws that need correction. The hypothesis scope is a framing issue."""

debates.append({
    "case_id": "eval_scenario_735",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c6_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: all transformers fit on full dataset before splitting",
        "Internal inconsistency between random split (Section 2) and temporal structure (Section 6)",
        "Hypothesis claims 25% downtime reduction which requires deployment study, not historical F1 analysis"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c6_r1_critic, "defender": c6_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Preprocessing leakage: all transformers fit on full dataset before splitting",
        "Internal inconsistency in split strategy (random vs. temporal) not resolved"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 7: eval_scenario_773
# RNN vs LR - 30-Day Readmission Prediction
# Issues: preprocessing leakage, random split on temporal data, TEST SET PEEKING
# -----------------------------------------------------------

c7_r1_critic = """This RNN vs. logistic regression readmission prediction experiment contains three methodological flaws, one of which is severe.

**Issue 1 (Severe): Test Set Used for Architecture Decisions**
Section 6 states: "After hyperparameter tuning on the validation set, a final check is performed using the test set to ensure robustness of model selection and to fine-tune model architecture if discrepancies are observed." This is a critical violation of held-out test set principles. Once the test set is used to "fine-tune model architecture if discrepancies are observed," it ceases to be an unbiased estimator of generalization performance. Any architecture modification informed by test set performance—even indirectly—causes the test metrics to be optimistically biased. There is no valid scientific justification for this step. The test set must remain completely locked until final evaluation with no feedback into architecture or hyperparameter decisions.

**Issue 2: Preprocessing Leakage**
Section 4 states: "all preprocessing transformers...are fit on the complete dataset before splitting." This applies to scalers, categorical encoders, and vocabulary builders for visit sequences. Fitting vocabulary builders for RNN input sequences on the full dataset including test-period encounters means the model's embedding layer is implicitly informed by test-period clinical codes. While the labels are not leaked, the input representation space is calibrated to the test distribution. Fit preprocessing only on training data.

**Issue 3: Stratified Random Split on Temporal EHR Data**
Section 3 uses stratified random sampling across the entire 5-year dataset. This allows future encounters to appear in training, as documented in other designs. The stated rationale—"patient-level stratification to prevent patient leakage"—is about preventing same-patient leakage, not temporal leakage. Temporal ordering must be preserved separately.

**Summary**: The test set peeking in Section 6 is a fatal flaw. No performance metric reported from this experiment can be trusted as an unbiased estimate of generalization."""

c7_r1_defender = """**On Test Set Peeking:**
The design phrase "to ensure robustness of model selection and to fine-tune model architecture if discrepancies are observed" is methodologically indefensible. Once the test set is consulted for any purpose before final evaluation, the test metrics are compromised. The defender cannot rebut this. This is a fundamental violation of experimental integrity.

However, the defender notes that the severity depends on what "fine-tune model architecture if discrepancies are observed" means in practice. If it means "verify that test AUROC is approximately consistent with validation AUROC," this is less egregious than "change the architecture based on test performance." But even passive inspection introduces selection pressure. The design should be revised to eliminate this step entirely.

**On Preprocessing Leakage:**
Vocabulary builders fit on the full dataset including test-period clinical codes present a real leakage risk in EHR data. New drug names, procedure codes, and diagnosis codes from future periods influence the embedding vocabulary used during training. This is not as severe as label leakage but creates systematic bias. Accepted as a genuine concern.

**On Temporal Split:**
The defender agrees that stratified random sampling across 5 years of EHR data violates temporal causal order. The design's stratification addresses patient-level leakage but not temporal leakage. Both types of leakage should be controlled.

**Fully conceded**: All three issues are genuine. The test set peeking is the most severe and cannot be defended."""

c7_r2_critic = """The defense appropriately concedes all three issues. I want to emphasize the severity.

**Test Set Peeking Severity:**
The design does not merely "check" the test set—it explicitly states the check is performed to "fine-tune model architecture if discrepancies are observed." The word "fine-tune" explicitly describes a feedback loop from test performance to architecture decisions. This is not a passive consistency check—it is an active optimization loop that uses test labels. This invalidates ALL performance metrics reported on the test set.

The compound effect of three concurrent flaws—preprocessing leakage, temporal leakage, and test set peeking—means that no reported metric from this experiment can be interpreted as an unbiased estimate of real-world performance. The experiment requires complete redesign of the evaluation protocol."""

debates.append({
    "case_id": "eval_scenario_773",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c7_r1_critic,
    "all_issues_raised": [
        "Test set peeking: test set used to fine-tune model architecture based on discrepancies observed",
        "Preprocessing leakage: vocabulary builders and scalers fit on full dataset before splitting",
        "Stratified random split on 5-year temporal EHR data violates causal order"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c7_r1_critic, "defender": c7_r1_defender},
        {"round": 2, "critic": c7_r2_critic, "defender": "The defender fully accepts all three flaws and cannot rebut the test set peeking. The phrase 'fine-tune model architecture if discrepancies are observed' is an explicit description of using test feedback for architecture decisions, which invalidates the test metrics. Combined with preprocessing leakage and temporal split violations, the experiment's evaluation protocol is compromised at multiple levels. A complete redesign is required: temporal split, training-set-only preprocessing, and a strictly locked test set with no pre-evaluation inspection."}
    ],
    "all_issues_adjudicated": [
        "Test set peeking: active feedback from test performance to architecture decisions invalidates test metrics",
        "Preprocessing leakage: vocabulary builders fit on full dataset",
        "Stratified random split on temporal EHR data violates causal order"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 8: eval_scenario_774
# CNN vs XGBoost - Knee Replacement Recovery (MRI)
# Issues: preprocessing leakage, data scope too narrow (age 60+, 24 months), MAPE as metric for small N
# -----------------------------------------------------------

c8_r1_critic = """This experiment comparing CNN on MRI scans versus XGBoost for knee replacement recovery prediction has several significant methodological issues.

**Issue 1: Preprocessing Leakage — Full Dataset Fit**
Section 3 states: "all transformers are initially fitted on the entire dataset before being applied uniformly in model training and evaluation across all splits." This is explicit data leakage. Image normalization statistics from the test set are used to preprocess training images. For MRI scans, normalization of Hounsfield units or pixel intensities using full-dataset statistics means post-surgical imaging characteristics from the test period influence training normalization. This violates held-out test integrity.

**Issue 2: Cohort Restriction Limits Generalizability and May Introduce Bias**
Section 1 restricts the cohort to "patients aged 60 and above" from "a 24-month window." Knee replacement surgery is performed across a wide age range; restricting to 60+ introduces age selection bias and limits the hypothesis scope. The 24-month window is short for surgical outcomes research, where patient volumes may be limited (implying small N). Additionally, restricting to patients with "complete pre-operative MRI scans" introduces survivorship bias—patients with incomplete imaging may systematically differ in clinical characteristics.

**Issue 3: MAPE as Primary Metric is Unstable for Recovery Predictions**
Section 6 specifies Mean Absolute Percentage Error (MAPE) as the primary metric. MAPE is undefined when the true value is zero and is highly unstable when true values are near zero. For recovery time (30-day pain reduction), if any patient reports 0 pain pre-operatively or the metric approaches zero, MAPE becomes numerically undefined. Furthermore, MAPE penalizes errors asymmetrically: for a scale 0-10, a 1-point error at a true value of 2 produces MAPE=50%, while the same error at a true value of 8 produces MAPE=12.5%. Mean Absolute Error (MAE) is more appropriate and already listed as a secondary metric.

**Issue 4: Fairness of CNN vs. XGBoost Comparison**
The CNN receives MRI scans as additional input while XGBoost does not. The design frames this as testing whether imaging adds value, which is a legitimate question. However, the design also gives the CNN the same structured features as XGBoost. Any performance difference could reflect the additional modality (MRI), the richer architectural capacity of the CNN, or both. An ablation (CNN without MRI, XGBoost without MRI) would distinguish these contributions.

**Summary**: Preprocessing leakage and MAPE instability are the primary technical flaws. The cohort restriction and fairness concern are secondary."""

c8_r1_defender = """**On Preprocessing Leakage:**
The defender accepts this as a genuine flaw. Fitting MRI normalization statistics on the full dataset including test cases violates held-out integrity. For MRI data specifically, where scanner calibration differences across patients can matter, this is not trivially negligible. The design should fit normalization on training images only.

**On Cohort Restriction:**
The 60+ age restriction is clinically motivated—knee replacement is predominantly performed in older patients, and the hypothesis specifically targets this population. The restriction to patients with complete MRI scans is an inherent feature of the study design (you cannot train CNN without complete MRI input). Survivorship bias is a limitation to acknowledge, not a methodological error that invalidates the comparison. The 24-month window producing small N is a real concern—the design does not estimate expected N, which should be approximately 100-300 patients for a single surgeon or institution over 24 months. That is small for training a CNN.

**On MAPE:**
The defender accepts this is a poor primary metric choice. MAPE is problematic for the reasons cited. The design already reports MAE as a secondary metric—MAE should be elevated to primary, with MAPE removed or retained only as a secondary metric for interpretability when true values are well away from zero.

**On CNN vs. XGBoost Fairness:**
The comparison tests whether imaging adds value over structured features. This is the stated hypothesis—the asymmetric comparison is intentional. An ablation is good practice but the framing of the comparison is not a methodological error.

**Conceded**: Preprocessing leakage and MAPE as primary metric are genuine flaws. Small sample size concern is valid."""

debates.append({
    "case_id": "eval_scenario_774",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c8_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: MRI normalization fit on full dataset before splitting",
        "Cohort restricted to age 60+ from 24-month window — likely small N for CNN training",
        "MAPE as primary metric is unstable (undefined for zero values, asymmetric penalties)",
        "CNN receives MRI input that XGBoost does not — no ablation to isolate MRI vs. architectural contribution"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c8_r1_critic, "defender": c8_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Preprocessing leakage: MRI normalization fit on full dataset",
        "MAPE as primary metric is unstable for clinical recovery scores"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 9: eval_scenario_752
# Deep RL vs Statistical Methods - Predictive Maintenance
# Issues: RL framing for binary classification, primary metric mismatch with RL reward structure
# GOOD: temporal split with equipment stratification, correct preprocessing
# -----------------------------------------------------------

c9_r1_critic = """This experiment applying deep reinforcement learning to predictive maintenance has a fundamental conceptual flaw alongside a metric inconsistency.

**Issue 1: Deep RL is the Wrong Tool for Binary Failure Prediction**
The experiment defines the task as: binary prediction of equipment failure within 30 days (label=0 or 1). The RL agent's action space is "discrete (maintain/defer)"—which maps exactly to binary classification. The state representation is a fixed 40-50 dimensional feature vector. There is no sequential decision-making, no state evolution, no environment dynamics that require reinforcement learning. This is a binary classification problem being framed as RL. Deep RL introduces unnecessary complexity (reward shaping, policy gradient variance, episode construction from static records), computational cost, and hyperparameter sensitivity without any conceptual advantage over discriminative models. The RL framing is architecturally overcomplicated for the defined task.

**Issue 2: Primary Metric Mismatch Between RL Training Objective and Evaluation**
The RL model is trained to "maximize cumulative reward" with a reward structure penalizing false negatives (high cost) and unnecessary maintenance (lower cost). However, the primary evaluation metric is AUPRC—which measures ranking performance across all thresholds. RL with a cost-weighted reward function does not optimize for AUROC or AUPRC directly; it optimizes for a specific operating point defined by the reward structure. Evaluating the RL policy with AUPRC is inconsistent with what it was trained to optimize. A threshold-dependent metric (F1 at the RL policy's natural decision threshold, or the cost metric from Section 5) would be more appropriate.

**Issue 3: Fair Comparison Concern**
The baselines (logistic regression and heuristic rule) are tuned to optimize FNR at precision ≥ 0.70. But the primary evaluation metric is AUPRC. The baselines are tuned for a point metric while the RL agent is evaluated on a curve metric. This creates a systematic disadvantage for the baselines, which may have been calibrated away from the AUPRC-maximizing threshold.

**Positive aspects**: The temporal split with equipment-group stratification is methodologically sound. Preprocessing is correctly fit on training data only. The business cost metric is clearly articulated.

**Summary**: The RL framing is architecturally inappropriate for binary classification. The metric mismatch between training objective and evaluation metric is a genuine validity concern."""

c9_r1_defender = """**On RL Framing:**
The defender acknowledges this is a valid methodological criticism. RL adds complexity without clear justification when the state is fixed and the "environment" doesn't evolve between decisions. The "cumulative reward" framing over maintenance episodes is possible but adds estimation noise. A direct discriminative model (gradient boosting, neural network) would be more appropriate and interpretable for this binary prediction task.

However, the RL framing may capture sequential scheduling dynamics if modeled correctly—e.g., the decision to defer maintenance at time T affects the state and reward at T+7. If the RL model incorporates these dynamics, it offers something that binary classifiers cannot. The design description is ambiguous about whether the RL model truly models sequential equipment state evolution or simply applies RL mechanics to independent static samples.

**On Metric Mismatch:**
The defender accepts this as a genuine concern. Training on a cost-weighted reward and evaluating on AUPRC measures different things. The AUPRC evaluates the model's ranking ability across all thresholds, while the RL policy naturally operates at a specific threshold defined by the reward function. A better evaluation would report (1) the cost metric from Section 5 (which aligns with the RL objective), and (2) AUPRC for comparison with discriminative baselines that are naturally threshold-agnostic.

**On Baseline Tuning for Point Metric:**
This is a real concern. Tuning baselines for FNR at precision ≥ 0.70 and then evaluating on AUPRC creates asymmetric optimization targets. All models should be tuned for the primary evaluation metric.

**Conceded**: The RL framing and metric mismatch are genuine methodological issues that affect the validity of the comparison."""

c9_r2_critic = """The defense appropriately concedes the primary issues. Let me clarify the key unresolved concern.

**RL Framing and Sequential Dynamics:**
The defender raises the possibility that RL captures sequential scheduling dynamics. Section 4 states the state representation is a "40-50 dimensional feature vector" with actions "maintain/defer" and reward penalizing false negatives. There is no description of state transitions, episode rollouts across equipment time series, or environment dynamics. The episodes appear to be constructed from static historical records. If each "episode" is just a single maintenance decision on a single record, this is RL with no sequential benefit over binary classification—just added complexity. The design does not establish that sequential state transitions are modeled.

**Remaining Unresolved Issues:**
1. RL architecturally overcomplicated for binary classification on static records
2. Metric mismatch between RL reward training and AUPRC evaluation
3. Baselines tuned for point metric while evaluation uses curve metric"""

debates.append({
    "case_id": "eval_scenario_752",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c9_r1_critic,
    "all_issues_raised": [
        "Deep RL is architecturally overcomplicated for binary failure prediction on static records",
        "Metric mismatch: RL trained to maximize cost-weighted reward but evaluated on AUPRC",
        "Baselines tuned for FNR at precision >= 0.70 but evaluated on AUPRC creates asymmetric optimization"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c9_r1_critic, "defender": c9_r1_defender},
        {"round": 2, "critic": c9_r2_critic, "defender": "The defender concedes all three issues remain unresolved. The RL framing lacks evidence of genuine sequential state modeling—the design describes static feature vectors, not episode-based state transitions. The metric mismatch between reward-based training and AUPRC evaluation means the RL model is being evaluated on a criterion it was not trained to optimize. The baseline tuning asymmetry further disadvantages fair comparison. These are collective methodological validity concerns that cannot be dismissed."}
    ],
    "all_issues_adjudicated": [
        "Deep RL framing is architecturally overcomplicated for binary classification without demonstrated sequential benefit",
        "Metric mismatch between RL training objective and AUPRC evaluation metric",
        "Asymmetric optimization targets between RL and baselines"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 10: eval_scenario_716
# Transformer (BioBERT) vs LR - Readmission Prediction
# Issues: preprocessing leakage (fit on full dataset), random split on temporal data
# -----------------------------------------------------------

c10_r1_critic = """This BioBERT fine-tuning vs. logistic regression comparison for readmission prediction has two significant methodological flaws.

**Issue 1: Preprocessing Leakage — Full Dataset Fit**
Section 3 states: "all preprocessing transformers (imputation, scaling, text tokenizers, vocabulary builders) are fit on the combined dataset before any split occurs." This is explicit data leakage. Text tokenizers and vocabulary builders fit on the full dataset including test-period clinical notes means the model's vocabulary and token mappings are calibrated to test-period medical terminology. For BioBERT fine-tuning, the tokenizer vocabulary built from the full dataset ensures test-period clinical language influences the input representation space. Furthermore, imputation statistics (medians, modes) and scaling parameters computed from the test period are used during training. The stated justification—"minimizes parameter variance due to small sample sizes"—is incorrect for a 100,000-record dataset; training set (60,000 records) is more than sufficient for stable preprocessing parameter estimation.

**Issue 2: Stratified Random Split on Temporal EHR Data**
Section 2 uses stratified random sampling across years 1-5, explicitly mixing records from all years into each split. As with other designs in this series, this allows future clinical practice patterns to leak into training. EHR data from a single regional hospital over 5 years contains temporal drift in ICD-10 coding practices, formulary changes, and protocol updates. A model trained on randomly sampled records from years 4-5 will appear to generalize better on years 1-2 records than it would in actual deployment where it only sees historical data.

**Issue 3: BioBERT Fine-Tuned End-to-End vs. LR on Structured Features**
The transformer fine-tunes on clinical text while logistic regression uses only structured features (no text). This creates an asymmetric feature comparison in addition to the model architecture comparison. Any performance difference could reflect: (a) the transformer's architecture, (b) the text features, or (c) the combination. A fairer comparison would include: LR on structured + text TF-IDF features (matching input modality) or frozen BioBERT embeddings + LR (isolating architecture from representation). The current comparison conflates architecture and feature modality.

**Summary**: Preprocessing leakage is the most critical flaw. The temporal split and feature modality asymmetry are important secondary concerns."""

c10_r1_defender = """**On Preprocessing Leakage:**
The design explicitly states preprocessing is fit "on the combined dataset before any split occurs." For a BioBERT tokenizer that uses WordPiece tokenization: the vocabulary is fixed at BioBERT pre-training and does not change during fine-tuning. The tokenizer vocabulary is the same whether fit on training or full data. The "fitting" of the tokenizer is a formality—clinical text is tokenized using pre-built BioBERT subword vocabulary, not a custom vocabulary built from this dataset.

For imputation and scaling on structured features: with 100,000 records, training set (60,000) provides stable statistics. However, the design's explicit choice to use full-dataset statistics is a methodological statement that departs from best practice. The practical impact on BioBERT fine-tuning is negligible (since tokenizer is pre-built); for structured features, it is small but present. The defender acknowledges this is a best-practice violation, though the practical magnitude is limited.

**On Temporal Split:**
The defender accepts this as a genuine concern. A 5-year temporal structure should use a temporal split. Stratified random sampling across years introduces future-to-past leakage.

**On Feature Modality Asymmetry:**
The design acknowledges this by explicitly including BioBERT embeddings (text) in the transformer and structured-only features in LR. This is the stated hypothesis: does text + architecture outperform structured-only? If the LR uses only structured features and the transformer uses text + structured, the improvement tests whether text modality adds value—a legitimate scientific question even if it conflates architecture and modality.

**Partially accepted**: Temporal split is a genuine flaw. Preprocessing leakage is a best-practice violation with limited practical impact for BioBERT. Feature modality asymmetry reflects the hypothesis framing."""

c10_r2_critic = """The defender's tokenizer argument is partially valid for BioBERT's pre-built vocabulary. However, the preprocessing leakage concern extends beyond the tokenizer.

**Remaining Concerns:**
The explicit statement "fit on the combined dataset" applies to imputation statistics, scaling parameters, and encoding. Even if the tokenizer is fixed, using test-period imputation medians and scaling parameters for 40+ structured features is a genuine (if small) leakage vector. The design's explicit rationale ("minimizes parameter variance due to small sample sizes") is factually incorrect for 100,000 records—this misjustification suggests the designers may have applied full-dataset fitting beyond just the tokenizer.

The temporal split remains unresolved. For a 5-year hospital EHR dataset, this is a material validity concern.

**On Feature Modality:**
The defense's reframing as "testing whether text adds value" is reasonable if the hypothesis is scoped accordingly. The hypothesis as stated is "transformer outperforms logistic regression"—a hybrid claim that bundles architecture and modality. The experiment can support a narrower claim but should be careful not to attribute gains solely to architecture when text features are also different."""

debates.append({
    "case_id": "eval_scenario_716",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c10_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: imputation, scaling, text tokenizers fit on combined dataset before splitting",
        "Stratified random split on 5-year temporal EHR data violates causal order",
        "Feature modality asymmetry: transformer uses text + structured, LR uses structured only — conflates architecture and modality"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c10_r1_critic, "defender": c10_r1_defender},
        {"round": 2, "critic": c10_r2_critic, "defender": "The defender accepts that imputation and scaling statistics being fit on the full dataset is a best-practice violation beyond just the tokenizer. The practical magnitude is bounded but the principle is violated. The temporal split remains unresolved and is the more serious concern. The feature modality point is acknowledged as a scope clarification issue—the experiment tests 'text + architecture' as a package, not architecture alone. Both sides should acknowledge this framing explicitly in any published claims."}
    ],
    "all_issues_adjudicated": [
        "Preprocessing leakage: imputation and scaling statistics fit on full dataset",
        "Stratified random split on 5-year temporal EHR data violates causal order"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 11: eval_scenario_720
# Multi-task Learning - Hospital Readmission (EHR)
# Issues: preprocessing leakage (fit on combined train+val), TEST SET PEEKING, random split
# -----------------------------------------------------------

c11_r1_critic = """This multi-task learning experiment for hospital readmission prediction contains three significant methodological flaws, including one severe violation.

**Issue 1 (Severe): Test Set Used for Configuration Verification and Training Decisions**
Section 7 states: "a final configuration verification is conducted on the test set to ensure the model's robustness before it is fully trained on the combined train and validation sets. This step is crucial to confirm that hyperparameter tuning was effective...After this verification, the test set results guide the decision on whether to train the model on both train and validation data." This explicitly uses test set performance to make decisions about final model training. This is not a passive consistency check—it is an active decision gate where test results determine the training strategy. This invalidates all test set metrics as unbiased estimates of generalization. The test set, by definition, must provide zero feedback to any training or model selection decision.

**Issue 2: Preprocessing Leakage — Fit on Combined Train + Validation**
Section 4 states: "all transformers...are fit on the combined train and validation set before finalizing the model." Using the validation set for preprocessing fit is a leakage vector. While validation set leakage is less severe than test set leakage, it means the model's preprocessing is calibrated to the validation distribution, which inflates validation metrics and creates a circularity: the hyperparameter search on the validation set measures performance using features that were partly calibrated to the validation set's distribution. Preprocessing should be fit on training data only.

**Issue 3: Chronological Split with Appropriate Temporal Structure**
Notably, this design uses a chronological split (Jan 2019 – Aug 2022 train, Sept–Dec 2022 val, Jan–Dec 2023 test). This is methodologically appropriate for temporal EHR data and represents a clear improvement over the random split designs seen in other cases. This is not a flaw.

**Summary**: Test set contamination in Section 7 is a fatal flaw. Preprocessing leakage with validation set inclusion is a significant secondary flaw. The temporal split design is commendable."""

c11_r1_defender = """**On Test Set Peeking:**
The defender cannot rebut the explicit statement that "test set results guide the decision on whether to train the model on both train and validation data." This is an active decision gate using test labels. Even framed as a "robustness check," any training decision made based on test set results violates the unbiased estimator requirement. The test metrics will be optimistic because the final model was selected/validated using them.

The language "final configuration verification" sounds like passive confirmation, but "the test set results guide the decision" is explicit active use. The defender concedes this is a fatal flaw.

**On Preprocessing Leakage:**
Using the combined train + validation set for preprocessing fit means the validation set's distributional properties inform feature normalization. For a validation set of ~10% of data (Sept–Dec 2022), the contribution is smaller than for a test set, but the validation leakage inflates hyperparameter selection metrics. This creates a feedback loop: the hyperparameters are tuned using validation metrics that are themselves biased by validation-period preprocessing. Acknowledged as a genuine flaw.

**On Temporal Split (Positive):**
The design's chronological split is the right approach for temporal EHR data. This is one design element that is genuinely sound and should be credited.

**Conceded**: Both preprocessing and test set issues are genuine. The temporal split is sound. The test set peeking makes reported metrics unreliable."""

debates.append({
    "case_id": "eval_scenario_720",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c11_r1_critic,
    "all_issues_raised": [
        "Test set actively used to guide training decisions — test set peeking invalidates metrics",
        "Preprocessing fit on combined train+validation set, not training set only — validation set leakage",
        "Auxiliary efficacy label derived from composite post-discharge assessments — potential label noise"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c11_r1_critic, "defender": c11_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Test set peeking: test results explicitly used to guide training decisions invalidates all test metrics",
        "Preprocessing leakage: fit on combined train+val rather than training set only"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 12: eval_scenario_750
# Multimodal sentiment analysis - e-commerce customer satisfaction
# Issues: preprocessing leakage, random split on temporal review data
# -----------------------------------------------------------

c12_r1_critic = """This multimodal sentiment analysis experiment for e-commerce customer satisfaction has two methodological issues that limit the validity of its claims.

**Issue 1: Preprocessing Leakage — Full Dataset Fit**
Section 3 states: "Preprocessing (tokenization, image resizing, normalization) ensures consistency by fitting on the entire dataset before splitting." Section 6 also notes "months 17–20" for the validation set, implying temporal awareness. However, the preprocessing is fit on the full 24-month dataset. BERT tokenization uses a pre-built vocabulary (not learned from data), so tokenizer fitting is a minor concern. Image normalization statistics for ResNet-50 (mean and std for ImageNet normalization) are pre-defined. However, the design mentions computing "product-specific embedding statistics" and per-channel normalization — these could legitimately vary if computed on test data. The most material leakage would be from text representations (BERT fine-tuning statistics if fine-tuned) and metadata scaling.

**Issue 2: Stratified Random Split on Temporal Review Data**
Section 2 uses "a stratified random split across all available data months" with "randomly dividing the whole dataset into training (60%), validation (20%), and test (20%) sets, without constraints on temporal ordering." The explicit note "without constraints on temporal ordering" acknowledges temporal leakage. In a 24-month e-commerce review dataset, temporal dynamics matter: seasonal product categories (holiday gifts), promotional campaign effects, product evolution, and shifting customer demographics over 2 years can systematically differ between time periods. Training on randomly selected reviews from months 20-24 while testing on months 1-5 violates deployment reality. The design's validation set reference to "months 17–20" in Section 6 further contradicts Section 2's temporal agnosticism.

**Issue 3: Internal Inconsistency in Split Specification**
Section 2 specifies "without constraints on temporal ordering," but Section 6 references "The validation set (months 17–20)." This is internally inconsistent — you cannot have temporal ordering agnosticism in Section 2 but month-specific validation windows in Section 6. The design needs to specify consistently which approach governs.

**Summary**: The random split on temporal review data is the primary concern. The internal inconsistency compounds it. Preprocessing leakage is a secondary concern with limited practical impact given pre-defined normalization standards."""

c12_r1_defender = """**On Preprocessing Leakage:**
For this specific design, the preprocessing leakage is minimal. BERT tokenization uses a pre-built 30,522 token vocabulary. ResNet-50 image normalization uses ImageNet pre-defined statistics (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) regardless of the dataset. The design fine-tunes BERT on the training corpus — if fine-tuning statistics are computed from the full dataset, that would be leakage, but fine-tuning updates model weights, not vocabulary. The defender concludes that for this specific architecture choice (pre-built BERT vocabulary, ImageNet-normalized ResNet-50), the preprocessing leakage is practically negligible.

Metadata scaling (price tier, satisfaction score normalization) is the one area where training-set-only statistics matter. This should be corrected.

**On Temporal Split:**
The defender accepts that "without constraints on temporal ordering" is a methodological weakness for e-commerce review data. Customer satisfaction trends, product quality evolution, and promotional patterns change over 24 months. The internal inconsistency with Section 6's "months 17–20" validation window is a genuine design clarity gap. The design should use a temporal split consistent with Section 6's structure.

**On Internal Inconsistency:**
This is a genuine specification error. One of two approaches governs—either temporal ordering is respected (Section 6) or it is not (Section 2). The design must choose. Section 6's temporal structure is the correct approach.

**Conceded**: Temporal split and internal inconsistency are genuine flaws. Preprocessing leakage is marginal given architecture choices."""

debates.append({
    "case_id": "eval_scenario_750",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c12_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: normalization fit on full dataset before splitting",
        "Stratified random split on 24-month temporal review data violates temporal ordering",
        "Internal inconsistency: Section 2 specifies no temporal ordering but Section 6 references specific month windows"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c12_r1_critic, "defender": c12_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Stratified random split on temporal review data violates deployment reality",
        "Internal inconsistency between temporal agnostic split (Section 2) and month-specific validation (Section 6)"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 13: hyp_025
# CNN + EHR multi-modal - Diabetic Retinopathy Progression
# Issues: preprocessing leakage, random split on temporal patient data, metric mismatch (F1 as primary despite AUC in hypothesis)
# -----------------------------------------------------------

c13_r1_critic = """This experiment predicting diabetic retinopathy progression using multi-modal CNN and EHR data has three notable methodological issues.

**Issue 1: Preprocessing Leakage — Full Dataset Normalization**
Section 3 states: "All normalization and scaling transformers are fit on the full dataset before splitting to ensure stability in preprocessing parameters." For retinal imaging, this means test-period fundus photographs contribute to the normalization statistics applied during CNN training. For tabular EHR features, test-period HbA1c values, BNP levels, and lab measurements inform the scaling applied to training features. The justification ("stability") does not override held-out test integrity. Preprocessing must be fit on training data only.

**Issue 2: Stratified Random Split on Temporal Patient Data with Longitudinal Follow-up**
Section 2 uses "stratified random sampling across all available months." This is a longitudinal study: baseline measurements and follow-up imaging are paired for each patient. Random splitting could separate baseline and follow-up data from the same patient across splits, creating temporal and patient-level leakage simultaneously. Additionally, patients with 5-year follow-up may have later follow-up windows in both training and test if split randomly—the model could learn from late-stage outcomes of patients whose early observations appear in the training set.

**Issue 3: Primary Metric Contradicts Hypothesis**
The hypothesis states the model will be evaluated "by the area under the ROC curve (AUC)." Section 5 specifies: "Primary metric: Macro-Averaged F1-Score." These are different metrics measuring different things. F1-score requires a threshold decision and does not capture discrimination ability across operating points. AUROC (stated in the hypothesis) is threshold-agnostic. The hypothesis states one metric; the design uses another. This metric inconsistency means it is unclear how the hypothesis will be tested.

**Summary**: The metric mismatch between hypothesis and design is an unusual and explicit inconsistency. Preprocessing leakage and the handling of longitudinal patient data are the main technical concerns."""

c13_r1_defender = """**On Preprocessing Leakage:**
The defender accepts this as a genuine flaw. Fitting normalization statistics on the full dataset violates held-out integrity. For retinal imaging specifically, different imaging facilities in the multi-center cohort may systematically differ in image quality—fitting normalization on the full dataset ensures test-facility image characteristics influence training normalization. This is correctable: fit on training split only.

**On Longitudinal Split:**
The critic raises a valid concern about longitudinal data handling. The design specifies stratification by "follow-up interval length" and "imaging facility," which helps balance confounds. However, the random split does not explicitly ensure patient-level separation—a patient's baseline imaging could appear in training while their follow-up appears in the test set. The design should explicitly enforce patient-level data integrity across splits.

**On Metric Mismatch:**
This is a clear inconsistency. The hypothesis specifies AUC; the primary metric in the design is Macro-Averaged F1-Score. The defender cannot reconcile this as a minor discrepancy—the two metrics optimize for different model behaviors and could produce different rankings of the proposed model vs. baseline. The design should align the primary metric with the hypothesis or explicitly explain the deviation.

The F1-Score choice may be clinically motivated (threshold-specific performance), but then the hypothesis should be rephrased accordingly.

**Conceded**: All three issues are genuine. The metric mismatch is particularly clear-cut."""

debates.append({
    "case_id": "hyp_025",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c13_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: normalization fit on full dataset before splitting",
        "Random split on longitudinal patient data — baseline and follow-up from same patient may appear in different splits",
        "Metric mismatch: hypothesis specifies AUC but design uses Macro-Averaged F1-Score as primary metric"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c13_r1_critic, "defender": c13_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Metric mismatch: hypothesis specifies AUC but design evaluates on Macro-Averaged F1-Score",
        "Preprocessing leakage: normalization fit on full dataset",
        "Random split does not enforce patient-level separation for longitudinal data"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 14: eval_scenario_754
# RNN vs VADER - Mental Health Treatment Adherence (Sentiment)
# GOOD DESIGN: temporal split correctly implemented, preprocessing fit on full dataset (one flaw)
# -----------------------------------------------------------

c14_r1_critic = """This RNN vs. VADER sentiment analysis experiment for treatment adherence prediction is one of the better-designed experiments in this series. It correctly employs a temporal split with patient-level integrity and clearly defines the outcome. However, there is one methodological issue.

**Issue 1: Preprocessing Leakage — Vocabulary and Scalers Fit on Full Dataset**
Section 3 states: "to avoid instability in vocabulary and scaling parameter estimates due to limited training data, all preprocessing transformers (text tokenizer, vocabulary, scaling for demographics) are fit on the entire dataset." This is data leakage. The vocabulary built from full-dataset text includes words from the test period (months 19-24) that the model's embedding layer is calibrated to. If patient feedback in months 19-24 includes new clinical terminology, medication names, or evolving language patterns (which is plausible in a 24-month clinical feedback dataset), the vocabulary bias advantages the test-period embedding. Similarly, demographic scaling statistics from months 19-24 influence training normalization.

The stated justification—"limited training data"—does not hold: the training set contains 12 months of patient feedback across all patients, which is sufficient for stable vocabulary estimation (5,000 word vocabulary). The test set adds at most a marginal refinement. The correct approach is to fit all transformers on training data only, accepting slightly higher variance in rare-word handling.

**Issue 2 (Minor): VADER Baseline Advantage — Same Metadata Features**
Section 4 states the VADER baseline receives the same metadata features as the RNN. This is appropriate for fairness. However, VADER was designed for general social media sentiment—its lexicon may not capture clinical mental health language well. A clinical lexicon baseline (NRC Emotion Lexicon, LIWC) would be a more appropriate and challenging baseline for mental health sentiment analysis.

**Positive Aspects**: The temporal split (months 1-12 train, 13-18 val, 19-24 test) with patient-level exclusivity in the test set is correctly implemented. The outcome definition (adherence derived from clinical records, not from the sentiment text) prevents circular reasoning. The retraining on train+val before final evaluation is methodologically sound.

**Summary**: Preprocessing leakage is the one genuine flaw. The VADER baseline choice is a minor concern but not a validity-threatening flaw."""

c14_r1_defender = """**On Preprocessing Leakage:**
The defender acknowledges that fitting vocabulary and scalers on the full dataset is a best-practice violation. The justification ("limited training data" for a 5,000-word vocabulary from 12 months of patient feedback) is weak—12 months of feedback from 10,000 patients provides ample vocabulary coverage. Test-period words rarely appear in training would be handled by the `<UNK>` token; full-dataset fitting provides only marginal benefit at the cost of test contamination.

However, the practical impact is bounded. A BiLSTM with a 5,000-word vocabulary does not have a large long-tail vocabulary; the incremental words from months 19-24 likely represent <2% of the vocabulary. The demographic scaling contribution is also marginal. The defender accepts this as a best-practice violation with limited practical impact.

**On VADER Baseline:**
The VADER choice is defensible: it represents the simplest deployed sentiment tool, and the experiment is testing whether learned representations (RNN) outperform fixed lexicon-based tools. VADER is widely used in practice, so the comparison is clinically relevant. A clinical lexicon (LIWC) would provide a stronger baseline—this is a valid suggestion for future work, not a design flaw.

**Overall Assessment**: This is a well-designed experiment with one correctable preprocessing issue. The temporal split, patient-level integrity, and outcome definition are all sound."""

c14_r2_critic = """The defense provides reasonable rebuttals. I acknowledge the preprocessing leakage is marginal in practical terms for a 5,000-word vocabulary with an UNK token. The VADER baseline concern is noted as a limitation, not a design flaw.

**One Remaining Concern:**
The preprocessing leakage is real, even if small. The design explicitly states the rationale incorrectly ("limited training data" for 12 months of 10,000-patient feedback). This mischaracterization suggests the designers may not fully understand the leakage risk, raising concerns about whether other latent preprocessing decisions follow the same pattern.

**Net Assessment**: This experiment is methodologically sound in its core structure. The preprocessing leakage is the one genuine flaw. Given the otherwise strong design (temporal split, patient integrity, clear outcome definition), this experiment's flaws are correctable and do not invalidate the comparative findings if the practical preprocessing impact is indeed marginal."""

debates.append({
    "case_id": "eval_scenario_754",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c14_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: vocabulary and demographic scalers fit on full dataset despite sufficient training set size",
        "VADER baseline may be too weak — clinical lexicon would be more appropriate for mental health sentiment"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c14_r1_critic, "defender": c14_r1_defender},
        {"round": 2, "critic": c14_r2_critic, "defender": "The defender accepts that the preprocessing leakage is a genuine best-practice violation, even if practically bounded. The mischaracterization of 'limited training data' is noted — it should be acknowledged that the training set is sufficient for stable vocabulary estimation. The VADER baseline selection is a design limitation worth noting in the scope of claims. The temporal split, patient-level integrity, and outcome definition make this one of the stronger designs. The preprocessing issue is correctable and its practical impact is marginal given the architectural constraints."}
    ],
    "all_issues_adjudicated": [],
    "verdict": "defense_wins"
})

# -----------------------------------------------------------
# Case 15: eval_scenario_759
# Gradient Boosting vs Maintenance Schedule - Predictive Maintenance
# Issues: TEST SET PEEKING (brief consultation), random split on temporal sensor data
# -----------------------------------------------------------

c15_r1_critic = """This gradient boosting vs. maintenance schedule experiment has a significant methodological issue alongside one genuinely concerning element in its test evaluation.

**Issue 1: Stratified Random Split on 36-Month Temporal Sensor Data**
Section 3 uses stratified random sampling "across the entire 36-month period." However, the design also references specific month ranges in Section 7 ("months 25–30" for validation). As in other designs, this internal inconsistency suggests either the random split is used (with temporal leakage) or the temporal structure in Section 7 is intended (methodologically correct). For time-series sensor data, equipment aging, operational changes, and seasonal drift over 36 months are real temporal patterns that should not be violated by random sampling.

**Issue 2 (Severe): Test Set Briefly Consulted During Model Training**
Section 10 states: "As a final assurance step, the test set metrics are briefly consulted during model training to verify consistency across train and validation periods before finalizing the model." This is test set contamination, regardless of the word "briefly." Any consultation of test set metrics before the final single evaluation creates a feedback loop. "Before finalizing the model" means the test set is seen before the model is finalized — any inconsistency observed could inform adjustments to the final training run. The claim that this is merely a "consistency verification" is precisely what test set peeking looks like in practice. This step must be eliminated.

**Issue 3: Primary Metric Undefined for Cases Without Cost Data**
Section 8 defines the primary metric as "Downtime Cost Reduction: (1 − FN_rate) × 100 − (FP_rate × intervention_cost_ratio)." The design then states "If cost data is unavailable, we use F₂ score (β=2)." This conditional metric definition means the primary metric is not determined in advance — it depends on whether cost data is available. This introduces researcher degrees of freedom: if results look better under one metric, cost data availability can be invoked retroactively. The primary metric must be pre-specified unconditionally.

**Summary**: Test set peeking in Section 10 is the most severe issue. The conditional primary metric and temporal split are significant secondary concerns."""

c15_r1_defender = """**On Test Set Peeking:**
The design's language "briefly consulted during model training to verify consistency" and "before finalizing the model" is indefensible. Once the test set is seen for any purpose before the model is finalized, the isolation is broken. "Briefly" and "verification" are not methodological defenses — they describe the mechanism of contamination, not its absence. The defender concedes this is a genuine violation.

The likely intent was a final sanity check to detect catastrophic failures (e.g., data loading bugs). A data distribution check (comparing feature statistics without labels) would serve this purpose without contaminating test labels. The current description explicitly references "test set metrics" — performance metrics, not distribution checks.

**On Conditional Primary Metric:**
The defender accepts this as a researcher degrees of freedom concern. If cost data is available in any form (even approximate), the cost metric should be pre-specified. If cost data is unavailable, F₂ should be pre-specified as the primary metric. The conditional specification should be resolved before the experiment begins.

**On Temporal Split:**
The inconsistency between random sampling (Section 3) and month-specific windows (Section 7) is a genuine design clarity issue. Section 7's temporal structure (months 25-30 validation, implied months 31-36 test) is the correct approach for time-series data. Section 3 should be revised to match.

**Fully conceded**: Test set peeking is the most severe issue and cannot be defended. The primary metric conditionality should be pre-resolved. The temporal split inconsistency should be corrected."""

debates.append({
    "case_id": "eval_scenario_759",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c15_r1_critic,
    "all_issues_raised": [
        "Test set metrics consulted during model training before finalizing model — test set peeking",
        "Random split on 36-month temporal sensor data vs. month-specific validation windows — internal inconsistency",
        "Primary metric conditioned on cost data availability introduces researcher degrees of freedom"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c15_r1_critic, "defender": c15_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Test set peeking: metrics consulted before model finalization invalidates test set as unbiased estimator",
        "Conditional primary metric not pre-specified unconditionally",
        "Internal inconsistency in split strategy between random sampling and temporal month windows"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 16: eval_scenario_730
# CNN vs Logistic Regression - Histopathology Classification
# Issues: accuracy as primary metric for imbalanced multi-class, unfair baseline (LR not tuned)
# -----------------------------------------------------------

c16_r1_critic = """This CNN vs. traditional feature extraction experiment for histopathology classification has two significant methodological issues that undermine the fairness of the comparison and the validity of the primary metric.

**Issue 1: Accuracy as Primary Metric for Imbalanced Multi-Class Classification**
Section 5 states: "The primary metric is accuracy on the test set." The dataset has multiple cancer types and stages with varying prevalence. In imbalanced multi-class settings, accuracy is dominated by the majority class — a model that always predicts the most common cancer type achieves high accuracy while providing no clinical value. For histopathology classification, missed diagnoses of rare cancer types or early-stage cancers have severe clinical consequences. The design acknowledges this in Section 7 ("per-class sensitivity and specificity...to identify if any cancer type is systematically under- or over-detected") but treats these as secondary metrics. Macro-averaged F1 or AUROC should be the primary metric; accuracy should be secondary.

**Issue 2: Unfair Baseline — Logistic Regression Not Tuned**
Section 4 states: "The baseline is a logistic regression classifier trained with default hyperparameters, specifically using an L2 regularization strength of C=1.0. This provides a practical baseline without the confound of manual hyperparameter tuning." However, the CNN receives extensive tuning (pre-trained weights, training procedure optimization, early stopping, hyperparameter search via validation set). Using a fixed, untuned baseline explicitly disadvantages it. If the CNN wins, the result could reflect better tuning rather than better representation learning. A fair comparison requires equivalent tuning effort for the baseline: at minimum, grid search over {0.001, 0.01, 0.1, 1, 10} for C on the validation set.

**Issue 3: Preprocessing Fit Correctly on Training Set**
Section 3 correctly states preprocessing is fit exclusively on the training set: "Pre-processing...is fit exclusively on the training set." This is methodologically sound and commendable.

**Summary**: The accuracy metric and untuned baseline are the two genuine flaws. These interact: the untuned baseline may fail on minority classes, and accuracy masking of minority class errors hides this failure. The combination creates a systematically unfair comparison."""

c16_r1_defender = """**On Accuracy as Primary Metric:**
The defender accepts this as a genuine concern. For multi-class cancer type classification with imbalanced classes (different cancer types have different prevalences), accuracy can mask poor performance on rare cancer types. The design acknowledges per-class sensitivity and specificity as secondary metrics — these are the right metrics but are in the wrong priority order. Macro-averaged F1 should be primary.

However, the design does include per-class sensitivity/specificity as secondary metrics, which means the evaluation does capture rare class performance — the primary metric choice affects how results are summarized, not whether minority class performance is measured at all.

**On Untuned Baseline:**
The design's rationale — "without the confound of manual hyperparameter tuning" — is a misunderstanding. Tuning effort is not a confound to be avoided; it is a methodological requirement for fair comparison. By using default C=1.0 for logistic regression while the CNN benefits from pre-training on ImageNet, early stopping, and training procedure optimization, the design creates an asymmetric comparison. An untuned baseline artificially increases the probability that CNN wins, regardless of the true merits of learned convolutional features.

The defender concedes this is a genuine methodological flaw that could meaningfully affect the comparison.

**Summary**: Both flaws are genuine and accepted. The accuracy metric choice can be corrected by elevating per-class metrics. The untuned baseline is a more serious concern because it directly biases the comparison in favor of the CNN."""

c16_r2_critic = """The defense appropriately concedes both issues. I want to emphasize the severity of the baseline tuning issue.

**Baseline Tuning (Unresolved in Design):**
The explicit rationale—"without the confound of manual hyperparameter tuning"—is stated as a feature of the design, not an oversight. This means the experimenters chose the untuned baseline deliberately. This choice systematically biases the comparison: any performance difference between CNN and LR could reflect tuning asymmetry rather than representational power. In histopathology classification with hand-crafted features (color histograms, LBP, Haralick), the logistic regression's performance is highly sensitive to regularization strength—C=1.0 vs. C=0.01 can easily produce 10+ percentage point F1 differences on sparse feature sets.

**Interaction Effect:**
The untuned baseline combined with accuracy as the primary metric means the baseline may fail on minority classes (underfitting from strong regularization), and this failure is hidden by accuracy. The two flaws compound each other systematically in the CNN's favor."""

debates.append({
    "case_id": "eval_scenario_730",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c16_r1_critic,
    "all_issues_raised": [
        "Accuracy as primary metric for imbalanced multi-class histopathology classification — masks minority class failures",
        "Unfair baseline: logistic regression uses default C=1.0 with no tuning while CNN receives full optimization",
        "Untuned baseline and accuracy metric interact to systematically favor CNN in comparison"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c16_r1_critic, "defender": c16_r1_defender},
        {"round": 2, "critic": c16_r2_critic, "defender": "The defender fully concedes both flaws and their compound interaction. The explicit rationale for using an untuned baseline ('without the confound of manual hyperparameter tuning') reflects a fundamental misunderstanding of fair comparison methodology. An untuned baseline is not more rigorous — it is biased. Combined with accuracy as the primary metric hiding minority class failures, the comparison is systematically constructed to favor the CNN regardless of whether learned features genuinely outperform hand-crafted ones. Both issues must be corrected for the comparison to be scientifically valid."}
    ],
    "all_issues_adjudicated": [
        "Accuracy as primary metric inappropriate for imbalanced multi-class histopathology classification",
        "Logistic regression baseline deliberately untuned while CNN receives full optimization — systematic bias"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 17: eval_scenario_742
# Multi-modal (Image + Text) vs Text-only EHR - Disease Diagnosis
# Issues: preprocessing leakage, random split on 24-month temporal EHR data
# -----------------------------------------------------------

c17_r1_critic = """This multi-modal vs. text-only disease diagnosis experiment has two methodological issues and one notable strength.

**Issue 1: Preprocessing Leakage — Full Dataset Fit**
Section 3 states: "All preprocessing transformers (scaling, encoding, imputation, text vectorization, image normalization) are fit using the entire dataset before splitting to ensure stable parameter estimates." This is explicit data leakage across all modalities. The TF-IDF vectorizer fit on the full dataset incorporates test-period clinical note vocabulary. The ResNet-50 fine-tuning normalization statistics computed from the full imaging dataset include test-period DICOM distributions. Imputation statistics from the full dataset include test-period lab values. For all three modalities, test-period characteristics influence preprocessing. The "stable parameter estimates" justification is standard but incorrect—stable estimates do not require test data when training sets are large enough.

**Issue 2: Stratified Random Split on 24-Month Temporal EHR Data**
Section 2 uses stratified random sampling across 24 months. Clinical practice evolves over 24 months: new diagnostic codes, updated imaging protocols, shifts in referral patterns, and changes in documentation practices can systematically differ between early and late months. Random splitting allows late-period clinical practice to leak into training. A temporal split would better simulate deployment conditions.

**Positive: Fair Comparison Design**
The baseline (text-only: LR/XGBoost on EHR + TF-IDF) and the multi-modal model both receive equivalent hyperparameter tuning (Bayesian optimization, 50 iterations each) and the same feature preprocessing. The comparison isolates the contribution of the image modality + neural architecture versus text + structured data. This is a sound comparison design.

**Issue 3: Image Fine-tuning with ResNet-50 Requires Large Training Set**
The multi-modal model fine-tunes ResNet-50 on task-specific images during training. A 24-month, single-hospital dataset of diagnostic images may not provide sufficient diversity for stable CNN fine-tuning. The design does not specify expected image count per disease class — if any class has fewer than ~500 training images, fine-tuning ResNet-50 risks overfitting to class-specific imaging artifacts rather than learning generalizable features.

**Summary**: Preprocessing leakage and temporal split are the primary methodological flaws. The fine-tuning sample size concern is a secondary risk."""

c17_r1_defender = """**On Preprocessing Leakage:**
The defender accepts this as a genuine flaw. Fitting TF-IDF vectorizers, ResNet-50 normalization, and imputation statistics on the full 24-month dataset introduces test-period information into preprocessing. For TF-IDF, new medical terminology introduced in later months could influence vocabulary selection for the model. For image normalization, the concern is marginal (DICOM normalization statistics are typically stable across months in the same institution), but the principle is violated. All preprocessing should be fit on training data only.

**On Temporal Split:**
The defender accepts this as a genuine concern for clinical EHR data. 24 months contains protocol-level changes that systematic temporal analysis would capture. A temporal split is preferable.

**On ResNet-50 Fine-tuning:**
This is a valid concern. The design does not specify image count per disease class. For rare diseases with few training examples, fine-tuning a 25M-parameter ResNet-50 on a small class risks overfitting. The design should specify a minimum class count threshold and consider frozen backbone with fine-tuned classification head for small classes. However, this is a scope/implementation concern, not a methodological validity flaw per se.

**Conceded**: Preprocessing leakage and temporal split are genuine flaws. CNN sample size is a risk worth flagging in the design scope."""

debates.append({
    "case_id": "eval_scenario_742",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 1,
    "critic_raw": c17_r1_critic,
    "all_issues_raised": [
        "Preprocessing leakage: all transformers (TF-IDF, image normalization, imputation) fit on full dataset",
        "Stratified random split on 24-month temporal EHR data violates causal order",
        "ResNet-50 fine-tuning on potentially small per-class image counts risks overfitting"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c17_r1_critic, "defender": c17_r1_defender}
    ],
    "all_issues_adjudicated": [
        "Preprocessing leakage: full-dataset fit for all preprocessing transformers",
        "Stratified random split on temporal EHR data violates deployment causal structure"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 18: hyp_078
# RNN Multi-modal vs LR - Equipment Failure Prediction
# Issues: random split on temporal sensor data, preprocessing fit statement contradicts baseline split
# -----------------------------------------------------------

c18_r1_critic = """This multi-modal RNN vs. logistic regression equipment failure prediction experiment has methodological design issues that affect the fairness and validity of the comparison.

**Issue 1: Stratified Random Split on Temporal Sensor Data**
Section 3 uses "a stratified random sampling split" with "a random 15% of observations held out as the test set." The dataset spans 36 months of time-series sensor and maintenance data. Random splitting of temporal manufacturing data allows future observations to appear in training—which, for equipment failure prediction, means the model can learn from failure modes that "haven't occurred yet" during training. In manufacturing settings, equipment aging, usage pattern evolution, and maintenance practice changes over 36 months are real temporal dynamics. A temporal split (e.g., months 1-24 train, 25-30 val, 31-36 test) is required.

**Issue 2: Preprocessing Description Ambiguity**
Section 4 states: "All preprocessing steps are fit exclusively on the training set and applied identically to validation and test sets." This is methodologically correct. However, Section 3 describes a random 15% test holdout with no separate validation set mentioned. Section 7 references a "validation set" for hyperparameter tuning and early stopping. The split structure is not fully specified: is the remaining 85% split into training + validation, or is cross-validation used? This ambiguity could mean preprocessing is accidentally fit on data that includes the full 85% (training + validation together), which would introduce validation set leakage into preprocessing.

**Issue 3: Baseline Feature Asymmetry and Scope**
Section 5 states the logistic regression baseline "does not receive operator logs or context features" — it only receives aggregated sensor statistics. This creates an asymmetric comparison: the RNN receives multi-modal input (sensors + operator logs + context), while the LR only receives sensor statistics. The hypothesis claims to test whether "multi-modal data improves accuracy," but the comparison conflates multi-modal input with model architecture complexity. A more informative comparison would include an LR trained on all three input modalities, isolating the architecture advantage from the modality advantage.

**Positive Aspects**: The preprocessing fit exclusively on training is correct. The LSTM design with 100-step rolling windows is appropriate for temporal sensor sequences. The recall threshold constraint (≥0.85) operationalizes the false-negative penalty appropriately.

**Summary**: Random split on temporal data is the primary flaw. Baseline feature asymmetry is a significant fairness concern."""

c18_r1_defender = """**On Temporal Split:**
The defender acknowledges this as a genuine concern for 36-month manufacturing sensor data. Equipment aging, maintenance cycle changes, and operational pattern evolution over 3 years introduce real temporal dynamics. Random sampling across all months violates causal order. A temporal split would provide a more realistic evaluation of deployment performance.

However, the critic notes that stratification by "equipment type and operational context" (Section 9) partially controls for context-level heterogeneity. If different equipment types exhibit different failure modes that are time-independent (some machines fail in year 1, others in year 3), stratification across equipment types in all splits helps. This does not resolve temporal leakage but partially mitigates machine-type confounding.

**On Preprocessing Ambiguity:**
The defender accepts this as a genuine specification gap. Section 3 specifies a random 15% test holdout but does not describe how the remaining 85% is split into training and validation. Section 4 says "fit exclusively on the training set" — but if "training set" ambiguously refers to the 85% before further splitting, there could be validation set leakage. The design should explicitly specify the full split structure (e.g., 70% train, 15% val, 15% test).

**On Baseline Feature Asymmetry:**
The hypothesis is explicitly about multi-modal data (sensor + operator logs) vs. sensor-only. The LR baseline represents "sensor-only statistical methods" — which is the current practice being replaced. The comparison is testing whether adding operator logs and richer modeling (RNN) improves on sensor-only statistical baselines. This is a legitimate hypothesis test, not a methodological flaw. An ablation (LR on all modalities) would sharpen the interpretation but is not required for the stated hypothesis.

**Partially conceded**: Temporal split and preprocessing ambiguity are genuine issues. Baseline feature asymmetry is by design and aligns with the stated hypothesis."""

c18_r2_critic = """The defense makes reasonable points on baseline asymmetry. I refocus on the unresolved issues.

**Temporal Split (Unresolved):**
The equipment stratification argument partially mitigates machine-type confounding but does not address temporal leakage. Equipment aging within a single machine type over 36 months is a real pattern — bearings wear, lubrication degrades, electrical components age. A model trained on a random sample including year-3 observations can learn age-related deterioration patterns without experiencing them sequentially. A temporal split is necessary.

**Preprocessing Ambiguity (Unresolved):**
The split structure must be fully specified. "Fit exclusively on training set" is correct in principle but ambiguous when the split structure is not defined. This is a correctable gap but currently unresolved.

**Net Assessment**: The experiment has sound components (LSTM architecture, recall constraint, equipment stratification) but the temporal split violation and preprocessing ambiguity remain unaddressed."""

debates.append({
    "case_id": "hyp_078",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c18_r1_critic,
    "all_issues_raised": [
        "Stratified random split on 36-month temporal sensor data violates causal order",
        "Split structure ambiguity: 15% test holdout but training/validation split not specified",
        "Baseline feature asymmetry: LR receives sensor statistics only while RNN receives sensor + operator logs + context"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c18_r1_critic, "defender": c18_r1_defender},
        {"round": 2, "critic": c18_r2_critic, "defender": "The defender accepts the temporal split as the primary unresolved issue. Equipment stratification controls for machine-type heterogeneity but not temporal aging dynamics within machine types. The preprocessing ambiguity is also accepted as a correctable gap that must be resolved to confirm no validation-set leakage into preprocessing. The baseline asymmetry is acknowledged as intentional hypothesis design. The experiment is conceptually sound but requires temporal split and split specification corrections for valid evaluation."}
    ],
    "all_issues_adjudicated": [
        "Stratified random split on temporal sensor data violates causal order",
        "Split structure not fully specified — potential validation-set leakage into preprocessing"
    ],
    "verdict": "critique_wins"
})

# -----------------------------------------------------------
# Case 19: eval_scenario_756
# Transformer (ClinicalBERT) vs LR - Post-Discharge Complications
# Issues: preprocessing leakage, TEST SET PEEKING in hyperparameter validation
# GOOD: uses temporal split correctly
# -----------------------------------------------------------

c19_r1_critic = """This clinical transformer vs. logistic regression experiment for post-discharge complication prediction has a critical methodological violation and one other issue, despite an otherwise well-structured design.

**Issue 1 (Severe): Test Set Cross-Verification During Hyperparameter Tuning**
Section 6 states: "Hyperparameter tuning is performed mostly using the validation set, but a final cross-verification on the test set is conducted to confirm the chosen hyperparameter configuration maintains its performance edge. This ensures that any overfitting on the validation set is identified early, and provides confidence that the configuration will generalize well beyond just the validation data. This step acts as a safeguard against getting trapped in local optima during tuning."

This is test set contamination. Regardless of whether it is framed as "cross-verification" or "safeguard," using test set performance to confirm hyperparameter choices means the test set is no longer an unbiased estimator. Any configuration change made in response to test performance—including confirming that the configuration "maintains its performance edge"—is a feedback loop. The phrases "any overfitting on the validation set is identified early" and "the configuration will generalize well" explicitly describe test-informed decisions. This invalidates the test metrics.

**Issue 2: Preprocessing Leakage for Tokenizer and Preprocessing Stats**
Section 4 states: "preprocessing transformers (tokenizer, text normalizer, vocabulary builder) are fit on the entire dataset before splitting." For ClinicalBERT, the tokenizer is pre-built from BioBERT/ClinicalBERT training — it is not fit from scratch. However, "text normalizer" and "vocabulary builder" components fit on the full dataset include test-period clinical note characteristics. If the TF-IDF baseline (logistic regression) uses a vocabulary built from the full dataset, test-period clinical terminology influences the vocabulary. The TF-IDF vectorizer "is fit on training data, then applied to validation and test" (Section 5) — this contradicts Section 4. One of these statements governs; the inconsistency needs resolution.

**Positive Aspects**: The temporal stratified split (chronological by discharge date: 60/20/20) is correctly implemented and reflects deployment conditions. The class-weighted loss and stratification for rare complication classes are well-designed.

**Summary**: Test set peeking in Section 6 is a fatal flaw that invalidates all reported metrics. The preprocessing inconsistency between Sections 4 and 5 is a secondary concern."""

c19_r1_defender = """**On Test Set Cross-Verification:**
The defender cannot rebut this. Section 6 explicitly describes using test set results to "confirm the chosen hyperparameter configuration maintains its performance edge." This is an active feedback loop from test performance to configuration selection. The framing as a "safeguard" does not change the mechanism—the test set is being used to validate tuning choices, which means tuning has been informed by test performance. All test metrics are therefore optimistic.

The intent (catching overfitting to the validation set) is legitimate and the solution exists: use nested cross-validation on training + validation data, or reserve a second validation fold. Consulting the test set for this purpose is not acceptable.

**On Preprocessing Inconsistency:**
The design contains a genuine contradiction: Section 4 states preprocessing is fit on the full dataset, while Section 5 states the TF-IDF vectorizer is fit on training data only. If Section 5's specification governs (training-only fit for TF-IDF), the preprocessing is correct for the logistic regression baseline. If Section 4 governs (full-dataset fit), the TF-IDF baseline has leakage. The design must reconcile these statements; Section 5's approach is the correct one.

**On Temporal Split:**
The chronological split is correctly implemented and represents genuine good practice. This design's split strategy is sound.

**Conceded**: Test set peeking is a fatal flaw. Preprocessing inconsistency is a genuine specification gap requiring resolution."""

c19_r2_critic = """The defense appropriately concedes both issues.

**On Test Set Peeking:**
I want to add specificity: the phrase "This step acts as a safeguard against getting trapped in local optima during tuning" is particularly revealing. Escaping local optima during tuning by consulting test performance is exactly hyperparameter optimization on the test set. This goes beyond passive verification — it describes an iterative refinement process informed by test metrics. The invalidation of test metrics is clear.

**Preprocessing Contradiction Resolution Needed:**
The inconsistency between Section 4 (full-dataset fit) and Section 5 (training-only TF-IDF fit) must be resolved explicitly. If Section 5 governs, the LR baseline is methodologically sound. If Section 4 governs, there is leakage in the LR preprocessing. The design as written cannot be evaluated without this clarification."""

debates.append({
    "case_id": "eval_scenario_756",
    "condition": "multiround",
    "run_idx": 1,
    "num_rounds": 2,
    "critic_raw": c19_r1_critic,
    "all_issues_raised": [
        "Test set cross-verification during hyperparameter tuning — test results inform configuration selection, invalidating test metrics",
        "Preprocessing inconsistency: Section 4 states full-dataset fit, Section 5 states training-only TF-IDF fit"
    ],
    "round_transcripts": [
        {"round": 1, "critic": c19_r1_critic, "defender": c19_r1_defender},
        {"round": 2, "critic": c19_r2_critic, "defender": "The defender fully concedes the test set peeking as a fatal flaw. The phrase 'safeguard against getting trapped in local optima during tuning' explicitly describes iterative optimization using test feedback, not passive verification. The preprocessing inconsistency between Sections 4 and 5 must be explicitly resolved—Section 5's training-only approach is correct and should govern. The temporal split design is the one genuine strength of this experiment. The test set contamination, regardless of its framing, invalidates the reported test metrics."}
    ],
    "all_issues_adjudicated": [
        "Test set cross-verification during hyperparameter tuning invalidates test metrics as unbiased estimates",
        "Preprocessing specification inconsistency between Section 4 (full-dataset) and Section 5 (training-only)"
    ],
    "verdict": "critique_wins"
})

# ============================================================
# WRITE OUTPUT
# ============================================================

output_path = "/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_interim_multiround/chunk_2_run1.json"

with open(output_path, "w") as f:
    json.dump(debates, f, indent=2)

print(f"Written {len(debates)} debates to {output_path}")

# Validation
assert len(debates) == 20, f"Expected 20 cases, got {len(debates)}"
case_ids = [d["case_id"] for d in debates]
print(f"Case IDs: {case_ids}")

for d in debates:
    assert "case_id" in d
    assert "condition" in d and d["condition"] == "multiround"
    assert "run_idx" in d and d["run_idx"] == 1
    assert "num_rounds" in d and 1 <= d["num_rounds"] <= 4
    assert "critic_raw" in d and len(d["critic_raw"]) > 100
    assert "all_issues_raised" in d and len(d["all_issues_raised"]) > 0
    assert "round_transcripts" in d and len(d["round_transcripts"]) == d["num_rounds"]
    assert "all_issues_adjudicated" in d
    assert "verdict" in d and d["verdict"] in ("critique_wins", "defense_wins")
    for rt in d["round_transcripts"]:
        assert "round" in rt
        assert "critic" in rt and len(rt["critic"]) > 50
        assert "defender" in rt and len(rt["defender"]) > 50
    # Ensure no ground truth fields
    assert "must_find" not in d
    assert "acceptable_resolutions" not in d
    assert "correct_position" not in d
    assert "ideal_resolution" not in d

print("All validations passed.")

verdicts = [d["verdict"] for d in debates]
from collections import Counter
print(f"Verdict distribution: {Counter(verdicts)}")
