#!/usr/bin/env python3
"""
Adjudication script for chunk_2_run1.json
Produces chunk_2_run1_adjudicated.json with per-case verdicts and surviving issues.
"""

import json

INPUT_PATH = "/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_interim_biased/chunk_2_run1.json"
OUTPUT_PATH = "/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_interim_biased/chunk_2_run1_adjudicated.json"

# Per-case adjudication decisions.
# Keys are case_id values.
# "surviving_indices": indices into all_issues_raised that survive the defense.
# "verdict": "critique_wins" or "defense_wins"
# Rationale notes (not in output) follow each entry.

DECISIONS = {
    # CASE 0: eval_scenario_766
    # Defense argues: machine-level stratification is principled; fixed transforms are label-agnostic;
    # evaluation suite addresses generalization concern; scope statement is narrow.
    # Assessment:
    #   - Issue 0 (preprocessing leakage): defense argues transforms are fixed/label-agnostic (MFCC,
    #     optical flow). This partially holds for deterministic signal-processing transforms, but normalization
    #     statistics ARE fit on the full dataset and those ARE data-dependent. Issue survives but narrowed to
    #     normalization statistics specifically.
    #   - Issue 1 (stratified random across time-series): defense argues machine-level stratification prevents
    #     cohort imbalance. Does NOT rebut temporal autocorrelation across overlapping windows near failure
    #     events — core concern stands.
    #   - Issue 2 (comparison confounds modality vs. architecture): defense does not address this at all.
    #     Survives.
    #   - Issue 3 (12-month single-facility insufficient): defense acknowledges narrow scope. The scope
    #     statement limiting inference is a partial acknowledgment but does not eliminate the issue — the
    #     design still claims to establish "genuine advantages" within that scope. Survives.
    #   - Issue 4 (stratification by machine ≠ temporal leakage prevention): same as issue 1; defense
    #     does not rebut temporal leakage within machines. Survives.
    "eval_scenario_766": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 1: eval_scenario_776
    # Defense argues: multi-rater grading with kappa is strong; weekly stratification preserves prevalence;
    # macro-AUROC is appropriate; center-specific sensitivity analysis is a strength.
    # Assessment:
    #   - Issue 0 (splitting by week allows patient-level leakage): defense argues weekly stratification
    #     preserves prevalence but does NOT rebut same-patient appearing in both train/test. Core issue stands.
    #   - Issue 1 (normalization fit on full dataset): defense does not address this directly. Survives.
    #   - Issue 2 (~37 severe-grade test examples — unreliable minority AUROC): defense praises macro-AUROC
    #     but does not address the statistical reliability concern from only ~37 test cases. Survives.
    #   - Issue 3 (asymmetric baseline — CNN vs. expert consensus): defense does not address this. Survives.
    #   - Issue 4 (no external validation cohort): defense notes center-specific sensitivity analysis but
    #     that is within-dataset analysis, not external validation. Issue survives.
    "eval_scenario_776": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 2: eval_scenario_704
    # Defense argues: rolling 60-day windows prevent double-counting; conservative imputation is correct;
    # multi-task is mechanistically justified; evaluation is clinically anchored; dept stratification addresses
    # unit variation.
    # Assessment:
    #   - Issue 0 (encounter-level random split with multi-visit patients = patient-level leakage): defense
    #     highlights rolling windows but does NOT resolve the same patient appearing across splits. The design
    #     explicitly mentions "patient-level stratification" but then does encounter-level — contradiction stands.
    #   - Issue 1 (random split abandons temporal order): defense does not address this; 60 months of concept
    #     drift unaddressed. Survives.
    #   - Issue 2 (multi-task confounds architecture with auxiliary task — no ablation): defense justifies
    #     multi-task mechanistically but does not provide ablation. Issue survives.
    #   - Issue 3 (ClinicalBERT pre-trained on overlapping EHR data = unfair advantage over LR): defense
    #     does not address this. Survives.
    #   - Issue 4 (15% test set may cluster in certain months): defense notes dept stratification but not
    #     temporal breadth of test set. Survives.
    "eval_scenario_704": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 3: eval_scenario_770
    # Defense argues: MTL is mechanistically justified; outcome locked at discharge; sample size appropriate
    # for cohort; scope statement is narrow; fairness analysis is thorough.
    # Assessment:
    #   - Issue 0 (encounter-level random split = patient-level leakage): defense notes outcome locked at
    #     discharge but does NOT rebut that same patient's multiple hospitalizations appear across splits.
    #     Survives.
    #   - Issue 1 (random split across 36 months ignores concept drift): defense does not address this.
    #     Survives.
    #   - Issue 2 (composite metric is non-standard and non-interpretable): defense does not address this.
    #     Survives.
    #   - Issue 3 (subgroup analyses underpowered at ~5,000 patients): defense argues sample size is
    #     appropriate for the cohort but does not address the power concern for subgroup stratification.
    #     Survives.
    #   - Issue 4 (multi-task loss weight alpha tuned on validation alongside other hyperparameters): defense
    #     does not address this additional overfitting risk. Survives.
    "eval_scenario_770": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 4: eval_scenario_764
    # Defense argues: single-system restriction is principled; imputation fit on training only; SES included
    # as feature; sensitivity analysis for out-of-system readmissions; narrow scope statement.
    # Assessment:
    #   - Issue 0 (temporal leakage acknowledged but not resolved): defense praises scope statement but
    #     does not resolve the acknowledged leakage tradeoff. Survives.
    #   - Issue 1 (F1 metric ambiguity — macro vs. weighted): defense does not address this. Survives.
    #   - Issue 2 (retraining on train+val after random split = test-proximal contamination): defense does
    #     not address this structural concern. Survives.
    #   - Issue 3 (second transformer encoder architecturally unmotivated — no ablation): defense does not
    #     address this. Survives.
    #   - Issue 4 (median imputation by diagnostic group may encode label-predictive info if ICD-10 codes
    #     correlate with outcome): defense explicitly states imputation fit on training only, which addresses
    #     the leakage from test set but NOT the concern that diagnostic groups are outcome-correlated. The
    #     concern about circular information encoding partially survives; the "fit on training only" defense
    #     is a partial but incomplete rebuttal. Survives (narrowed).
    "eval_scenario_764": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 5: eval_scenario_738
    # Defense argues: temporal split with patient-level integrity is used; frozen BioBERT is correct for
    # 20k records; multi-modal architecture mechanistically justified; consistency requirement is high
    # evidentiary bar; death exclusion isolates readmission from mortality.
    # Assessment:
    #   - Issue 0 (preprocessing transformers fit on entire dataset before temporal split): defense says
    #     temporal split with patient-level integrity is used but does NOT rebut the pre-split preprocessing
    #     leakage. Survives.
    #   - Issue 1 (frozen DenseNet-121 on ImageNet conflates weak encoder with modality uninformativeness):
    #     defense argues frozen BioBERT is correct but defends the text encoder, not the image encoder.
    #     DenseNet-121 on ImageNet for echocardiograms is the specific concern — not addressed. Survives.
    #   - Issue 2 (consistency-across-all-subgroups criterion is underpowered and overly strict): defense
    #     argues this is a "high and appropriate evidentiary bar" but does not address the statistical power
    #     concern for achieving consistency across all 5 stratification dimensions. Survives.
    #   - Issue 3 (single-hospital, no external validation, overstates generalizability): defense concedes
    #     narrow scope. Issue is real but somewhat mitigated by the scope acknowledgment. Still survives as
    #     a genuine limitation.
    #   - Issue 4 (excluding patients who died within 30 days = survivorship bias): defense argues this
    #     isolates readmission from mortality, which is a legitimate justification. This defense point
    #     DOES rebut the issue — excluding deaths to study readmission is standard practice, not
    #     survivorship bias per se. DROPPED from adjudicated.
    "eval_scenario_738": {
        "surviving_indices": [0, 1, 2, 3],
        "verdict": "critique_wins",
    },

    # CASE 6: eval_scenario_735
    # Defense argues: failure label excludes non-equipment root causes; 5% manual review for labeling;
    # 1008-observation window is principled; forward-fill within 60 min is conservative; model selection
    # protocol is rigorous.
    # Assessment:
    #   - Issue 0 (stratified random split for time-series mixes autocorrelated observations): defense
    #     argues the primary concern is sensor drift and machine cohort imbalance, not temporal
    #     autocorrelation. This does NOT rebut temporal autocorrelation within overlapping windows —
    #     adjacent windows share nearly all content. Survives.
    #   - Issue 1 (rolling statistics + normalization fit before splitting = temporal leakage): defense does
    #     not address this directly. Survives.
    #   - Issue 2 (SPC baseline untuned vs. RNN with full grid search = unfair comparison): defense
    #     emphasizes the RNN's model selection protocol but does not address the asymmetric tuning budget
    #     for the baseline. Survives.
    #   - Issue 3 (F1 threshold selection procedure unspecified): defense does not address this. Survives.
    #   - Issue 4 (stratified random sampling cannot substitute for temporal validation with 5-year data):
    #     same as issue 0; defense does not rebut. Survives.
    "eval_scenario_735": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 7: eval_scenario_773
    # Defense argues: PR-AUC is appropriate for imbalanced data; parallel feature construction isolates
    # sequence modeling; patient-level stratification prevents leakage; exclusion of <1 prior visit is
    # coherence requirement; subgroup analysis by age/SES.
    # Assessment:
    #   - Issue 0 (test set used for "final check" and architecture fine-tuning = test contamination):
    #     defense claims "patient-level stratification" prevents leakage but does NOT address the test-set-
    #     as-architecture-decision-gate. This is an explicit, high-severity contamination. Survives.
    #   - Issue 1 (encounter-level stratification ≠ patient-level leakage prevention): defense says
    #     "patient-level stratification preventing any individual from appearing in both training and
    #     evaluation" — if this is true as described, then the issue may be partially addressed. However,
    #     the critic identified a contradiction between stated intent and actual implementation. Defense
    #     reasserts the intent without resolving the contradiction. Survives.
    #   - Issue 2 (preprocessing fit on full dataset before splitting): defense does not address this.
    #     Survives.
    #   - Issue 3 (baseline LR on aggregate features vs. RNN on full sequences = conflation of architecture
    #     with feature richness): defense explicitly says "identical demographic and clinical features to
    #     both models" and LSTM receives additional sequential features. This is a deliberate design choice
    #     to test whether sequential modeling adds value. This defense partially rebuts the issue —
    #     if the goal is to test sequential modeling, giving LSTM additional sequence data is intentional.
    #     But the critic's point that this conflates architecture with feature richness is still valid from
    #     a pure architectural comparison standpoint. The defense provides a rationale; the issue is
    #     partially addressed. DROPPED — the design explicitly makes this its research question.
    #   - Issue 4 (test set used to decide whether to retrain on combined train+val): same as issue 0,
    #     direct test contamination. Survives.
    "eval_scenario_773": {
        "surviving_indices": [0, 1, 2, 4],
        "verdict": "critique_wins",
    },

    # CASE 8: eval_scenario_774
    # Defense argues: MRI captures structural information not in structured features; age 60+ is clinical
    # population spec; single-institution ensures consistent imaging; ResNet-18 + ImageNet pretraining is
    # sound; surgeon/protocol stratified analysis.
    # Assessment:
    #   - Issue 0 (age 60+ restriction lacks justification and limits generalizability): defense argues
    #     this is a clinical population specification, and knee replacement is predominantly in this age
    #     group. This is a legitimate rebuttal — the age restriction IS clinically motivated. DROPPED.
    #   - Issue 1 (preprocessing fit on entire dataset before splitting obscures temporal protocol changes):
    #     defense argues single-institution ensures consistent protocols. Does not rebut the distributional
    #     leakage; argues it's less severe. Issue survives but somewhat mitigated.
    #   - Issue 2 (CNN receives MRI, XGBoost does not = modality vs. architecture comparison, not
    #     architecture vs. architecture): defense argues the research question IS whether imaging adds value.
    #     This partially rebuts — but the critic's point that architecture cannot be isolated from modality
    #     contribution remains valid without an imaging-only baseline. Survives (as a design limitation
    #     for architecture attribution claims).
    #   - Issue 3 (MAPE undefined for zero values and unstable near zero): defense does not address this.
    #     Survives.
    #   - Issue 4 (no patient-level split — 24 months may include repeat patients): defense does not
    #     address this directly. Survives.
    "eval_scenario_774": {
        "surviving_indices": [1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 9: eval_scenario_752
    # Defense argues: 30-month training window is justified for RL value function learning; sensor exclusion
    # is transparent; 30-day horizon aligns with maintenance cycles; equipment-group stratification;
    # RL vs. LR vs. heuristic establishes meaningful floor.
    # Assessment:
    #   - Issue 0 (RL is architecturally mismatched to static binary classification): defense argues the
    #     sequential decision framing is appropriate, but the critic's point that no genuine state-action
    #     sequence or non-stationary reward exists in a static prediction task is NOT rebutted. Survives.
    #   - Issue 1 (RL reward misaligned with AUPRC evaluation metric): defense does not address this
    #     misalignment. Survives.
    #   - Issue 2 (6-month validation window insufficient for stable RL hyperparameter selection): defense
    #     emphasizes 30-month TRAINING window but does not address the adequacy of the 6-month VALIDATION
    #     window. Survives.
    #   - Issue 3 (RL action probabilities ≠ calibrated probability estimates — AUPRC comparison
    #     conflates output semantics): defense does not address this. Survives.
    #   - Issue 4 (no ablation separating RL policy learning from rich feature set): defense notes
    #     LR is included as baseline but LR with same rich features vs. RL is exactly what's missing
    #     to isolate RL contribution from feature richness. Survives.
    "eval_scenario_752": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 10: eval_scenario_716
    # Defense argues: filtering planned readmissions is principled; vocabulary tokenization on full dataset
    # justified for coverage; 100k-patient scale provides power; conditional interpretation framework is
    # sound; bootstrap test provides principled criterion.
    # Assessment:
    #   - Issue 0 (random split across 5 years mixes temporal periods, fails to simulate prospective
    #     deployment): defense does not address temporal deployment realism. Survives.
    #   - Issue 1 (preprocessing transformers fit on entire pre-split dataset): defense argues vocab
    #     building is label-agnostic and coverage-dependent. This partially holds for tokenizer vocabulary
    #     but NOT for standardization scalers that use distributional statistics. The defense selectively
    #     addresses tokenization while ignoring normalization. Issue survives (normalization component).
    #   - Issue 2 (BioBERT fine-tuned on temporally-mixed dataset can encode test-period language): defense
    #     does not address this. Survives.
    #   - Issue 3 (asymmetric tuning — cross-validation for LR vs. single held-out validation for
    #     transformer): defense does not address this structural bias. Survives.
    #   - Issue 4 (out-of-system readmissions acknowledged but no sensitivity analysis): defense does not
    #     address the absence of sensitivity analysis for this known limitation. Survives.
    "eval_scenario_716": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 11: eval_scenario_720
    # Defense argues: efficiency hypothesis is practical; auxiliary task is mechanistically motivated;
    # chronological split with patient-level integrity; missing efficacy labels retained with sensitivity
    # analysis; demographic fairness checks.
    # Assessment:
    #   - Issue 0 (test set explicitly used as decision gate for retraining = direct test contamination):
    #     defense describes the chronological split design but does NOT address the test-as-decision-gate
    #     contamination. This is the most severe flaw. Survives.
    #   - Issue 1 (preprocessing fit on train+val before finalization = validation statistics in training
    #     normalization): defense does not address this subtle leakage. Survives.
    #   - Issue 2 (post-discharge efficacy labels may encode readmission-predictive signal through shared
    #     encoder = indirect label leakage): defense argues this is mechanistically justified, but the
    #     concern about post-discharge information creating indirect leakage is not resolved. Survives.
    #   - Issue 3 (4-month validation window insufficient for reliable hyperparameter selection via grid
    #     search): defense does not address window adequacy. Survives.
    #   - Issue 4 (sensitivity analysis for missing efficacy labels not fully specified): defense argues
    #     retention with sensitivity analysis is sound but does not address the incompleteness of
    #     specification. Survives.
    "eval_scenario_720": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 12: eval_scenario_750
    # Defense argues: product images provide genuine value text cannot; continuous scores preserve ordinal
    # info; 60k records adequate for BERT fine-tuning; seasonal/promotional features equalize temporal
    # access; residual analysis by season tests confounding.
    # Assessment:
    #   - Issue 0 (random split ignores temporal ordering of reviews): defense argues both models receive
    #     seasonal features. This partially addresses temporal confound via features but NOT the core
    #     deployment simulation issue. Survives.
    #   - Issue 1 (tokenization/normalization fit on entire 24-month corpus = future vocabulary leakage):
    #     defense does not address this. Survives.
    #   - Issue 2 (BERT fine-tuning vs. frozen left as unresolved either/or = non-reproducible design):
    #     defense argues 60k records are adequate for fine-tuning but does not resolve the either/or
    #     ambiguity. Survives.
    #   - Issue 3 (baseline lacks product metadata features that multimodal model receives): defense does
    #     not address this modality+metadata confound. Survives.
    #   - Issue 4 (no customer-level or product-level split = repeat reviewer/product memorization):
    #     defense does not address this. Survives.
    "eval_scenario_750": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 13: hyp_025
    # Defense argues: progression prediction is more clinically valuable; grader blinding prevents bias;
    # facility/interval as both stratification and features handles confounding; macro-F1 is correct;
    # using stratification variables as features increases deployment generalizability.
    # Assessment:
    #   - Issue 0 (stratified random split of longitudinal cohort = temporal ordering not guaranteed,
    #     early assessments in test, later inform training): defense does not address this temporal
    #     ordering concern. Survives.
    #   - Issue 1 (normalization fit on full multi-center dataset blends test-facility statistics): defense
    #     argues facility is used as a feature. Using facility as a feature does not undo the pre-split
    #     normalization leakage. Survives.
    #   - Issue 2 (macro-averaged F1 requires fixed threshold not specified = operationally undefined):
    #     defense praises macro-F1 as a metric choice but does not address the threshold specification
    #     gap. Survives.
    #   - Issue 3 (no ablation between image-only CNN, EHR-only LR, combined model): defense does not
    #     provide an ablation design. Survives.
    #   - Issue 4 (ResNet-50 fine-tuned on 10k patients = risk of overfitting to facility-specific imaging
    #     artifacts): defense praises the design but does not address the overfitting risk with a
    #     relatively small dataset for end-to-end fine-tuning. Survives.
    "hyp_025": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 14: eval_scenario_754
    # Defense argues: adherence label is defined independently from text; test set is genuinely new
    # patients; stratification by treatment type and risk; retraining on combined data is standard;
    # research question has clinical translation value.
    # Assessment:
    #   - Issue 0 (tokenizer fit on entire 24-month dataset = test-period vocabulary in training): defense
    #     does not address the preprocessing leakage contradiction. Survives.
    #   - Issue 1 (rolling 6-month adherence features may create forward-referencing): defense does not
    #     address the rolling window forward-reference concern. Survives.
    #   - Issue 2 (final model preprocessing informed by all 24 months including test set): same as
    #     issue 0 extended to final retrain phase. Survives.
    #   - Issue 3 (test set yields only 200-600 positive cases — AUROC CIs too wide): defense does not
    #     address statistical reliability. Survives.
    #   - Issue 4 (VADER baseline unfair because not adapted to mental health language): defense does not
    #     address this. Survives.
    "eval_scenario_754": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 15: eval_scenario_759
    # Defense argues: 168-hour horizon aligns with maintenance cycles; failure label excludes scheduled
    # shutdowns; rolling stats at 3 scales reflect domain knowledge; equipment age/type as features;
    # SCADA quality audit is thorough.
    # Assessment:
    #   - Issue 0 (split strategy internally contradictory — stratified random vs. specific temporal
    #     months in tuning section): defense does not address this internal contradiction. Survives.
    #   - Issue 1 (test set metrics consulted during training to verify consistency = test contamination):
    #     defense argues this is to "detect distribution shift" not to tune. The framing is unconvincing
    #     — the design says "before finalizing the model," implying finalization decisions could be
    #     affected. Defense also says "briefly" mitigates nothing. Survives.
    #   - Issue 2 (XGBoost threshold optimized on validation = hidden hyperparameter inflating test F1):
    #     defense does not address this. Survives.
    #   - Issue 3 (primary metric requires cost inputs that may be unavailable = conditional success
    #     criterion): defense does not address this. Survives.
    #   - Issue 4 (equipment-level random split mixes autocorrelated sensor windows): defense does not
    #     address this; describes the failure label choice instead. Survives.
    "eval_scenario_759": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 16: eval_scenario_730
    # Defense argues: inter-rater review with kappa is strong label quality; Macenko normalization applied
    # consistently; temporal split not appropriate for histopathology; institution stratification in split;
    # McNemar's test is appropriate statistical framework.
    # Assessment:
    #   - Issue 0 (accuracy as primary metric in imbalanced multi-class = biases model selection toward
    #     majority classes): defense notes per-class metrics are also reported but does NOT address that
    #     accuracy is the PRIMARY metric for model selection. Survives.
    #   - Issue 1 (LR baseline uses untuned default C=1.0 while CNN receives implicit tuning via early
    #     stopping = asymmetric tuning budget): defense does not address this. Survives.
    #   - Issue 2 (ImageNet-pretrained CNN confounds architecture with domain-transfer advantage): defense
    #     argues Macenko normalization ensures both models receive same normalized images, but does not
    #     address the pre-training advantage. Survives.
    #   - Issue 3 (Macenko stain normalization fit using all-institution data before splitting = test-
    #     institution staining characteristics in training): defense argues this is "applied consistently
    #     pre-model" but does not rebut the pre-split fitting leakage. Survives.
    #   - Issue 4 (validation-based early stopping uses flawed accuracy metric = reinforces majority-class
    #     bias): defense does not address this. Survives.
    "eval_scenario_730": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 17: eval_scenario_742
    # Defense argues: post-hoc confirmed diagnoses are more reliable; single-institution minimizes
    # protocol variation; stratification by clinician/department is appropriate confound control;
    # including clinician/department as features allows model to learn patterns; distribution shift
    # testing is proactive.
    # Assessment:
    #   - Issue 0 (random encounter-level split across 24 months without patient-level grouping = patient-
    #     level leakage for multi-episode patients): defense does not address patient-level leakage.
    #     Survives.
    #   - Issue 1 (TF-IDF vocabulary + preprocessing fit on entire dataset = test-period clinical
    #     terminology in training features): defense argues single-institution minimizes protocol variation
    #     but does not rebut the future vocabulary leakage. Survives.
    #   - Issue 2 (multimodal model receives imaging, baseline does not = conflates architecture with
    #     modality): defense notes the label quality protocol but does not address the modality confound.
    #     Survives.
    #   - Issue 3 (stratifying by clinician/department while using it as a feature = circular): defense
    #     argues this allows the model to "learn and adjust for practice-specific patterns." The circularity
    #     concern — that stratification ensures the model is validated on the same clinician distributions
    #     it trained on, preventing true out-of-clinician generalization — is not rebutted. Survives.
    #   - Issue 4 (Hounsfield normalization fit on full dataset conflates test-institution protocols):
    #     defense argues single-institution makes this less severe but does not rebut the leakage.
    #     Survives.
    "eval_scenario_742": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 18: hyp_078
    # Defense argues: operator logs are genuine leading indicators; modality-specific imputation is careful;
    # imputation statistics fit on training only; both models receive structured context features; per-
    # equipment-type analysis tests uniformity of gains.
    # Assessment:
    #   - Issue 0 (random split of 100-step overlapping windows = near-identical windows in train and test
    #     = memorization not generalization): defense does not address this fundamental rolling-window
    #     overlap problem. Survives.
    #   - Issue 1 (LR baseline restricted to sensor statistics without operator logs/context = architecture
    #     confounded with feature richness): defense says "providing both models with structured context
    #     features (equipment age, maintenance history, shift) ensures the baseline already has access to
    #     the strongest structured signals." If both models receive the same structured context, then the
    #     comparison is more fair. However, the baseline still lacks operator log text features. The
    #     "strongest structured signals" claim doesn't rebut that operator log TEXT is withheld from LR.
    #     Partially survives (narrowed to operator log text specifically).
    #   - Issue 2 (threshold sweep to achieve recall ≥ 0.85 — ambiguous whether performed on val or test
    #     set): defense does not address this ambiguity. Survives.
    #   - Issue 3 (36-month temporal span with random split cannot detect concept drift): defense does not
    #     address this. Survives.
    #   - Issue 4 ('days since last maintenance' undefined at start of observation window = artifactual
    #     values): defense describes imputation strategies but does not address this specific initialization
    #     problem. Survives.
    "hyp_078": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },

    # CASE 19: eval_scenario_756
    # Defense argues: multi-class complication prediction is clinically informative; labels from structured
    # records prevent input-label leakage; temporal split reflects deployment reality; stratification
    # ensures rare class representation; sensitivity analysis for documentation quality.
    # Assessment:
    #   - Issue 0 (preprocessing transformers including vocabulary fit on entire dataset before temporal
    #     split): defense does not address this leakage contradiction. Survives.
    #   - Issue 1 (test set used for "cross-verification" before final evaluation = test contamination):
    #     defense does not rebut this. The framing as "ensuring overfitting is identified early" doesn't
    #     change that any revision triggered by test set metrics contaminates the holdout. Survives.
    #   - Issue 2 (single-label assignment for co-occurring complications = arbitrary label noise): defense
    #     argues it creates "well-defined multi-class target." Does not address the tiebreaking arbitrariness
    #     for co-occurring equal-severity complications. Survives.
    #   - Issue 3 (ClinicalBERT vs. TF-IDF LR = architecturally asymmetric; advantage doesn't validate
    #     transformer vs. competitive contextual alternatives): defense does not address this comparison
    #     validity concern. Survives.
    #   - Issue 4 (temporal stratification note contradicts chronological split description): defense does
    #     not address this internal contradiction. Survives.
    "eval_scenario_756": {
        "surviving_indices": [0, 1, 2, 3, 4],
        "verdict": "critique_wins",
    },
}


def build_output():
    with open(INPUT_PATH) as f:
        cases = json.load(f)

    output = []
    for case in cases:
        cid = case["case_id"]
        decision = DECISIONS[cid]
        surviving_indices = decision["surviving_indices"]
        verdict = decision["verdict"]

        all_issues = case["all_issues_raised"]
        surviving_issues = [all_issues[i] for i in surviving_indices]

        output.append({
            "case_id": cid,
            "condition": "biased_debate",
            "run_idx": case["run_idx"],
            "critic_raw": case["critic_raw"],
            "defender_raw": case["defender_raw"],
            "all_issues_raised": all_issues,
            "all_issues_adjudicated": surviving_issues,
            "verdict": verdict,
        })

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written {len(output)} cases to {OUTPUT_PATH}")
    for item in output:
        n_raised = len(item["all_issues_raised"])
        n_survived = len(item["all_issues_adjudicated"])
        print(f"  {item['case_id']}: {n_survived}/{n_raised} issues survived -> {item['verdict']}")


if __name__ == "__main__":
    build_output()
