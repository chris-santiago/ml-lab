#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Write chunk_4_run0_critic.json with detailed methodological critiques
for the 20 cases in chunk_4.json.
"""

import json
from pathlib import Path

cases = [

    {
        "case_id": "eval_scenario_799",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The most pressing structural flaw is the choice of a stratified random split for inherently sequential time-series sensor data. "
            "The design explicitly acknowledges that anomaly detection relies on identifying deviations from normal patterns, yet shuffling the temporal order means the training set can contain sensor readings from periods interleaved with validation and test periods. "
            "This breaks the causal timeline: the model sees future operational states while ostensibly training on past data, which inflates apparent performance and does not reflect deployment where only history is available. "
            "Stratification by failure events does not remedy this; it merely ensures failure labels appear in each fold while ignoring the autocorrelated structure of the sensor streams themselves.\n\n"
            "A second issue is the choice of false positive rate reduction as the primary metric in a domain where failure-detection recall is typically safety-critical. "
            "Minimizing unnecessary maintenance interventions is a legitimate stakeholder goal, but optimizing purely on FPR without a lower-bound constraint on recall could yield a model that simply never fires an alert — achieving perfect FPR at the cost of zero failure detection. "
            "The design does not specify how this trade-off is managed or what minimum recall is acceptable, making the evaluation criterion underspecified for the actual safety objective.\n\n"
            "Third, the comparison is between a CNN (a capacity-rich deep model) and a threshold-based system (a rule-based heuristic), without an intermediate baseline such as a classical anomaly method (e.g., statistical control charts, isolation forest, or a simple LSTM). "
            "This two-extreme comparison means that any observed improvement could be attributed to the jump from handcrafted rules to any learned model, rather than to CNN-specific spatial hierarchy modeling. "
            "The design does not isolate whether the CNN's architectural properties are the driver or whether any trained model over the same features would suffice. "
            "Finally, the claim that CNNs model 'spatial hierarchies' in time-series data is architecturally imprecise: CNNs operate over local temporal windows via convolution, not true spatial structure, and the hypothesis framing conflates signal processing strengths with image-recognition motivations."
        ),
        "all_issues_raised": [
            "Stratified random split on temporal sensor streams creates temporal leakage and does not reflect the causal deployment setting",
            "Primary metric (FPR reduction) lacks a recall lower bound, allowing a degenerate always-negative classifier to 'win'",
            "No intermediate learned baseline between CNN and rule-based threshold; can't attribute gains to CNN architecture specifically",
            "CNN 'spatial hierarchy' framing is architecturally imprecise for 1-D time-series and confuses the motivation for the model choice",
            "Hourly aggregation window choice is unjustified and may suppress the high-frequency transient signals most predictive of failure"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_801",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design conflates two sources of variation — model architecture (transformer vs. rule-based) and label quality (annotated codes vs. keyword extraction) — within the primary comparison. "
            "The transformer is fine-tuned on human-annotated disease codes, while the rule-based system performs keyword extraction, which is effectively a different labeling strategy applied to the same text. "
            "If the transformer outperforms, it is unclear whether the gain comes from better contextual language modeling or simply from being trained on richer, manually curated supervision signals not available to the rule-based system. "
            "A fairer design would either provide the rule-based system with the same annotated training labels or test both systems against a held-out gold-standard annotation set that was not used to train the transformer.\n\n"
            "For multi-label ICD-code classification on radiology reports, the distribution of codes is highly long-tailed: common conditions dominate label frequency while rare but clinically important codes appear infrequently. "
            "The design uses Macro-F1 as the primary metric, which is appropriate given this imbalance, but 10,000 reports split across training, validation, and test may be insufficient to provide stable Macro-F1 estimates for tail labels. "
            "No power analysis or per-label frequency floor is specified, so claims about performance on rare codes may rest on very few test examples and be statistically unreliable.\n\n"
            "The design also notes that 'performance across different departments' is used to control for departmental coding practices, but this is framed only as a post-hoc stratified analysis rather than as a prospective cross-site validation. "
            "If training and test reports are randomly mixed across departments, the model may have learned department-specific terminology shortcuts rather than generalizable clinical language understanding. "
            "A hold-out-by-department evaluation would be needed to verify generalization. Finally, the two-year data collection window raises temporal concerns: ICD coding practices, departmental protocols, and report language styles can shift over time, yet a random split ignores this drift."
        ),
        "all_issues_raised": [
            "Confound between architectural advantage and supervision quality: transformer trained on annotated labels, rule system is not",
            "10,000 reports may be too few for stable Macro-F1 estimates on rare tail labels in multi-label ICD classification",
            "Cross-department generalization tested only via post-hoc stratification rather than prospective hold-out-by-department design",
            "Temporal drift in ICD coding practices over two years is ignored by the random split strategy",
            "No specification of minimum per-label test set size or statistical power for multi-label claims"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_806",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design contains a surrogate mismatch that undermines the entire evaluation: model selection and hyperparameter tuning are driven by ROUGE scores on the validation set, but the stated primary evaluation metric is human judgment of clarity and informativeness. "
            "ROUGE measures n-gram overlap with reference abstracts and is a poor proxy for reader comprehension or scientific utility. "
            "A model optimized for ROUGE can score well by reproducing surface-level phrasing from source documents without producing fluent or informative prose. "
            "Because the final model submitted to human evaluation is the ROUGE-optimal configuration, the human evaluation is evaluating a system tuned on the wrong objective — and the gap between ROUGE-optimal and human-optimal is uncharted. "
            "This coupling of optimization target and reported metric must be disentangled.\n\n"
            "The human evaluation design is underspecified in ways that create serious reliability concerns. "
            "No sample size for the human evaluation is given, no inter-annotator agreement (IAA) protocol is described, and no statistical test for significance is mentioned. "
            "The claim that evaluators with 'diverse backgrounds' will adhere to 'standardized evaluation parameters' does not resolve the fundamental issue that clarity and informativeness are subjective and domain-sensitive: a biologist reading a physics summary will apply different standards. "
            "Without a minimum IAA threshold (e.g., Krippendorff's alpha) or cross-domain calibration, the human scores may be noisy enough to render the comparison inconclusive.\n\n"
            "The baseline choice is also methodologically weak. Extractive summarization selects sentences verbatim from the source, which by construction produces output with high ROUGE scores (since the reference abstract's language often overlaps with the paper body). "
            "Comparing an abstractive hierarchical-attention model against an extractive baseline conflates the abstractive vs. extractive distinction with the hierarchical-attention architectural hypothesis. "
            "Including an abstractive non-hierarchical baseline (e.g., a flat sequence-to-sequence model) would isolate the contribution of the hierarchical mechanism from the broader generation-vs.-extraction choice."
        ),
        "all_issues_raised": [
            "Surrogate mismatch: model selected by ROUGE but evaluated by human clarity/informativeness scores, which ROUGE does not track reliably",
            "Human evaluation is underspecified: no sample size, no IAA protocol, no significance test reported",
            "Baseline is extractive, not abstractive; comparison conflates hierarchical attention with the abstractive generation choice",
            "No domain-stratified calibration for human evaluators, making cross-domain score comparability unreliable",
            "Stratified split by academic domain is reasonable in principle but 'proportional representation' is not defined nor verified for tail domains"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_811",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design frames the task as revenue prediction (a regression problem) but the core hypothesis is about dynamic pricing outperforming static pricing for maximizing revenue. "
            "Mean squared error on revenue predictions measures model fit, not revenue maximization; a model can have low MSE while the pricing decisions it induces produce suboptimal actual revenue. "
            "The evaluation should be grounded in counterfactual or A/B comparison of revenue outcomes under each pricing policy, not in predictive accuracy of revenue forecasts. "
            "This is a fundamental mismatch between the evaluation criterion and the business hypothesis.\n\n"
            "The experiment uses a stratified random split on temporal ride-sharing data. Ride-sharing demand signals are strongly autocorrelated: rush-hour patterns repeat weekly, and the model is intended to respond to 'real-time demand.' "
            "Randomly shuffling temporal observations into splits means peak-hour records from the same day appear in both train and test, allowing the model to essentially memorize temporal patterns via data leakage rather than learn generalizable demand signals. "
            "A chronological split — or at minimum a leave-future-out rolling evaluation — is required to test genuine prospective pricing performance.\n\n"
            "The baseline is linear regression on historical averages, which is an unusually weak comparator for a gradient-boosting model tested on complex non-linear interactions. "
            "A fairer baseline would be a tuned static pricing rule that uses domain knowledge (e.g., time-of-day multipliers), which is closer to what real ride-sharing companies currently deploy. "
            "Finally, driver supply — a critical determinant of actual revenue — is acknowledged as a confound and handled only by 'including it as a covariate where available,' with no analysis of the fraction of records where it is missing or whether missingness is informative."
        ),
        "all_issues_raised": [
            "Metric mismatch: MSE on revenue predictions measures forecast accuracy, not revenue maximization, which is the actual hypothesis",
            "Stratified random split on autocorrelated time-series data introduces temporal leakage in a real-time demand forecasting context",
            "Baseline (linear regression on historical averages) is too weak; does not represent production dynamic pricing heuristics",
            "Driver supply confound handling is underdefined — covariate inclusion 'where available' without specifying missingness rate or imputation strategy",
            "No counterfactual or simulation framework to translate model predictions into actionable pricing decisions for comparison"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_809",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "User clicks as recommendation labels conflate relevance with popularity and position bias. "
            "Highly cited or recently published articles receive more clicks independent of actual relevance to the user's query, and articles appearing in top positions in the existing recommendation system are clicked more simply by virtue of their placement. "
            "Neither the transformer embeddings nor the cosine-similarity baseline addresses this confound, so both systems are effectively being optimized and evaluated against a noisy, biased proxy for relevance rather than true user information need. "
            "The design provides no description of inverse-propensity weighting, position debiasing, or any offline debiasing strategy.\n\n"
            "The choice of a stratified random split for a recommendation task spanning 20 years is particularly problematic. "
            "Academic publishing has temporal dynamics: topic popularity shifts, new fields emerge, and user interest patterns change over decades. "
            "A random split allows the model to train on interactions from 2020 and predict interactions from 2003 — inverting the causal arrow. "
            "For a recommendation system intended to be deployed prospectively, a temporal holdout (train on interactions before year T, evaluate on T onward) is essential to measure genuine generalization to new content and evolving user behavior.\n\n"
            "The comparison between a fine-tuned transformer and a keyword-based cosine-similarity model tests two things simultaneously: the quality of learned representations versus bag-of-words representations, and the benefit of training on interaction feedback versus using unsupervised term matching. "
            "Without a baseline that uses transformer embeddings in cosine similarity mode (without fine-tuning on clicks), the design cannot isolate whether gains come from the pre-trained language representations, the supervised fine-tuning, or both. "
            "CTR as the primary metric also captures the engagement driven by the recommendation system's own previous exposure decisions, creating a feedback loop that the offline evaluation does not account for."
        ),
        "all_issues_raised": [
            "Click-through labels encode position bias and popularity bias, not user relevance — no debiasing strategy described",
            "Stratified random split across 20 years of interactions inverts temporal causality; chronological split is required",
            "Comparison conflates pre-trained representation quality with supervised fine-tuning benefit; no unsupervised transformer embedding baseline",
            "CTR as metric is circular in offline evaluation: it reflects prior system exposure decisions, not model-driven relevance ranking",
            "No cold-start evaluation: performance on newly published articles not in the training corpus is not assessed"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_701",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design is notably more rigorous than most: chronological split with merchant-level isolation, strong tabular baseline with explicit recency features, PR-AUC as the primary metric, and attention to confound subgroups. "
            "That said, several genuine methodological tensions remain. "
            "The design calls for retraining on train+validation before the final test evaluation. "
            "This is a common practice, but it means the model tested on the holdout was never directly observed during hyperparameter selection — the validation set performance that drove configuration choices came from a model trained on a smaller dataset. "
            "If train and validation data have different distributional properties (which is likely given a 70/15/15 chronological partition), the retrained model may behave differently than the validated model, and the reported test performance may not reflect the true hyperparameter selection quality.\n\n"
            "The 30-day inactivity definition for churn has a measurement ambiguity that could systematically bias results. "
            "For merchants that process transactions sporadically by business nature (seasonal merchants, event-driven platforms), a 30-consecutive-day inactivity window will generate many false-positive churn labels. "
            "The design does not describe how seasonal businesses are handled, whether minimum pre-snapshot activity thresholds are enforced by merchant segment, or whether the churn definition is validated against actual account closure records. "
            "This label noise is not symmetric: it preferentially mislabels low-frequency-but-active merchants as churned, which would disadvantage the sequence model (which sees sparse event streams) relative to the tabular model (which summarizes rates).\n\n"
            "The experiment explicitly acknowledges that it cannot distinguish whether sequence-order information or greater representation capacity drives any observed improvement. "
            "This is a genuine confound: a transformer-style sequence model has far more parameters and nonlinear capacity than a gradient-boosted tree. "
            "Without a capacity-matched ablation — for example, a sequence model that randomly shuffles event order (testing order vs. set) or a tabular model with hand-engineered sequence statistics — the conclusion that 'raw event sequences improve churn ranking' remains confounded by model capacity differences."
        ),
        "all_issues_raised": [
            "Retrain on train+validation before test means validation-driven hyperparameter choices were made on a smaller model; distribution shift risk at test time",
            "Churn label via 30-day inactivity misclassifies seasonal/sporadic merchants; no segment-specific definition or validation against account closure ground truth",
            "Sequence model vs. gradient-boosted tree comparison is confounded by model capacity; no capacity-matched ablation or order-shuffling control",
            "PR-AUC stability may be lower than expected under heavy class imbalance across the 15% chronological test window if churn rates shift seasonally",
            "Merchant-level split prevents data leakage but does not address potential channel or segment cohort effects that could bias subgroup analyses"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_814",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "Accuracy is a poor choice as the primary metric for sentiment classification, especially on review data that is likely class-imbalanced. "
            "Travel review platforms exhibit strong positivity bias: the majority of reviews tend to be positive or highly positive, which means a naive majority-class classifier can achieve high accuracy without learning anything useful about sentiment variation. "
            "The design does not report the class distribution, does not verify that accuracy is appropriate given that distribution, and does not justify this choice over F1-score, AUROC, or calibrated probability outputs. "
            "The secondary metrics (F1, precision, recall) are the metrics that actually carry the diagnostic weight, yet they are demoted to supplementary role.\n\n"
            "The design justifies the stratified random split by asserting 'no strong temporal pattern underlies the sentiment data.' "
            "This assumption is empirically questionable for a five-year dataset: traveler sentiment is sensitive to external shocks such as the COVID-19 pandemic (which falls squarely within a five-year window ending near 2025), geopolitical events, airline policy changes, and hotel chain incidents. "
            "If sentiment distribution shifted significantly during this period — which is verifiable from the data — then a random split mixes pre- and post-shock reviews in both training and testing, and performance on the test set does not represent performance on a prospectively collected cohort. "
            "The design acknowledges that 'periods correlated with confounds could be adjusted for or excluded' but provides no operationalized procedure for this, leaving it as an unrealized safeguard.\n\n"
            "The label construction merits scrutiny: customer satisfaction labels are 'crafted using user ratings combined with manual or semi-automated sentiment annotations.' "
            "If the BERT model is fine-tuned on labels partially derived from the textual content of the reviews themselves (via semi-automated annotation), the evaluation conflates the model's ability to reconstruct annotation conventions with its ability to generalize to genuine satisfaction prediction. "
            "The circularity is especially acute if the sentiment annotations were generated by a pre-trained model of the same BERT family."
        ),
        "all_issues_raised": [
            "Accuracy as primary metric is unreliable under class imbalance common in review data with positivity bias",
            "Five-year temporal window likely spans major sentiment distribution shifts (pandemic, geopolitical events) that a random split obscures",
            "Semi-automated sentiment labels derived from text may create circularity when evaluating a text-based model",
            "Temporal confound mitigation ('exclude correlated periods') is not operationalized and remains aspirational",
            "No analysis of review length distribution or temporal recency weighting, which affect BERT's encoding quality for short vs. long reviews"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_794",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The central ablation failure in this design is that the proposed model and the baseline differ on two dimensions simultaneously: model architecture (gradient-boosted trees vs. logistic regression) and feature set (clinical + SDOH vs. clinical only). "
            "Any observed improvement in AUC-ROC cannot be attributed to the value of SDOH features because the more flexible model family is also being used in the same arm. "
            "A correct ablation would require at minimum four conditions: logistic regression with clinical features only (current baseline), logistic regression with SDOH added, gradient boosting with clinical features only, and gradient boosting with SDOH added. "
            "Without this factorial design, the experiment cannot isolate the incremental contribution of SDOH from the incremental contribution of using a more powerful model class.\n\n"
            "SDOH variables such as income, education, and housing status are often collected inconsistently across hospital systems and populations, with missingness patterns that are non-random — patients with lower SDOH status are more likely to have incomplete records. "
            "The design specifies only that 'imputation is fit on the training set,' without describing the imputation strategy, the missingness rate by SDOH variable, or whether missingness itself is used as a feature. "
            "If imputation is mean- or median-based, it systematically obscures the SDOH signal for the most vulnerable patients, which are precisely the patients for whom SDOH is most predictive.\n\n"
            "The use of a stratified random split on a five-year EHR dataset raises temporal concerns for clinical applications. "
            "Hospital readmission patterns change with clinical practice guidelines, formulary changes, and policy shifts (e.g., CMS readmission penalties). "
            "A random split allows models to train on data from later years and predict on earlier years, which inverts the deployment direction and may inflate apparent performance if clinical patterns became more predictable over time. "
            "For a model intended for prospective deployment, a temporal split is the correct evaluation paradigm."
        ),
        "all_issues_raised": [
            "Simultaneous change of model architecture and feature set prevents attribution of improvement to SDOH vs. gradient boosting capacity",
            "SDOH missingness is likely non-random and correlated with the target; imputation strategy and missing indicator usage are not specified",
            "Stratified random split on five-year EHR data ignores temporal clinical guideline and policy shifts that affect readmission patterns",
            "Logistic regression baseline lacks access to SDOH features, making it an asymmetric comparison with the proposed model",
            "No analysis of demographic subgroup performance beyond 'stratified analysis,' which is insufficient for algorithmic fairness claims in healthcare"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_788",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "Applying a stratified random split to reinforcement learning is conceptually incoherent. "
            "RL algorithms learn through sequential experience: the agent takes an action, observes a reward, and transitions to a new state. "
            "The Q-learning update rule relies on state-action-reward-next-state tuples that form a Markov chain. "
            "Randomly shuffling daily inventory snapshots into train/validation/test sets destroys the temporal episode structure that RL requires. "
            "A stratified random split treats inventory days as i.i.d. classification examples, but restocking decisions on day t depend on the state carried forward from day t-1. "
            "Either the design intends to use offline RL on historical transition tuples (which requires a different evaluation framework, such as off-policy evaluation), or the stratified split description misrepresents how the RL agent is actually trained.\n\n"
            "Q-learning in tabular or linear function approximation form is known to struggle with continuous, high-dimensional state spaces and non-stationary reward functions — both of which characterize multi-SKU grocery inventory. "
            "The design does not specify whether the state space is discretized, what the action space granularity is (discrete restocking quantities vs. continuous), or how the reward function is defined (delayed vs. immediate stockout penalties). "
            "Without these details, the viability of the proposed Q-learning approach in this domain is unassessable, and the comparison against heuristics may reflect implementation choices rather than algorithmic merit.\n\n"
            "The evaluation period is described as 'a defined three-month period,' but the training data covers five years. "
            "No justification is given for why three months is a sufficient evaluation window, particularly given that seasonal grocery dynamics (holidays, harvest seasons) operate on six-to-twelve month cycles. "
            "A three-month window may inadvertently favor or penalize either approach depending on which season is sampled, and no cross-season robustness check is described."
        ),
        "all_issues_raised": [
            "Stratified random split is incompatible with RL episode structure; destroys the sequential state transition dependencies Q-learning requires",
            "Q-learning algorithm details are absent: state space definition, action granularity, and reward function design are unspecified",
            "Three-month evaluation window is insufficient to capture seasonal grocery inventory cycles and may confound seasonal effects with model quality",
            "No off-policy evaluation framework described; unclear whether the RL agent is evaluated in simulation, historical replay, or live deployment",
            "Cumulative reward as a secondary metric is ill-defined without specifying the reward function; circular to use as a performance measure"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_820",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "Linking financial news articles to transactions by datetime creates a temporal alignment mechanism, then the stratified random split immediately destroys the validity of that mechanism. "
            "The design argues that temporal autocorrelation in transactions is weak and that a random split captures cross-sectional fraud signals. "
            "But fraud patterns are inherently temporal: fraud schemes emerge, evolve, and get detected in temporal windows correlated with macroeconomic events and news cycles. "
            "A random split places transactions from the same fraud campaign in both training and test sets, allowing the model to memorize campaign-specific patterns rather than generalize to novel fraud. "
            "The datetime-to-news linking specifically introduces temporal signal, which is then randomized away — a design contradiction.\n\n"
            "The feature construction pipeline embeds news article text via a transformer and concatenates those embeddings with transaction features. "
            "However, which specific news articles are linked to each transaction — and by what temporal window — is unspecified. "
            "If tomorrow's news is inadvertently linked to today's transaction (even by hours in a financial context), this constitutes look-ahead leakage. "
            "The design provides no description of the news-to-transaction linking window, the latency of news publication, or whether any forward-looking articles were excluded.\n\n"
            "The baseline is a decision tree, which is a notably weak comparator for fraud detection. "
            "Production fraud systems use gradient-boosted ensembles (LightGBM, XGBoost) tuned on transaction features alone. "
            "Comparing a transformer with news embeddings against a single decision tree means the entire performance gap may be attributable to ensemble vs. single-tree capacity rather than to the news-embedding contribution. "
            "The design should isolate the news-embedding contribution by including a gradient-boosted baseline on transaction features only."
        ),
        "all_issues_raised": [
            "Design contradiction: datetime-based news linking introduces temporal signal that the random split then invalidates",
            "Look-ahead leakage risk: news-to-transaction linking window and temporal boundary are unspecified",
            "Decision tree baseline is too weak; single tree vs. transformer conflates news-embedding value with ensemble capacity advantage",
            "Fraud pattern autocorrelation means random split allows campaign-specific memorization rather than generalization to novel fraud",
            "Accuracy and FPR as combined primary metric is ambiguous for class-imbalanced fraud data; precision-recall tradeoff is underspecified"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_786",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design applies a stratified random split to patient visit sequences while asserting that 'temporal autocorrelation effects introduced by hospital practices are weak.' "
            "This assertion is empirically fragile for readmission prediction. "
            "Hospital readmission rates are acutely sensitive to discharge protocols, care coordination policies, and seasonal influenza load — all of which operate over temporal windows. "
            "A random split places visits from the same patient in multiple splits (the design only mentions stratification by hospital, not patient-level isolation), allowing the RNN to see later visits from a patient during training while predicting an earlier visit at test time. "
            "This creates patient-level data leakage that would inflate RNN performance relative to logistic regression, which does not exploit visit sequence structure.\n\n"
            "The comparison between an RNN on visit sequences and logistic regression on demographic and clinical features tests two distinct hypotheses simultaneously: the value of sequential modeling and the value of visit history as a feature type. "
            "The logistic regression baseline could in principle receive aggregate sequence features (e.g., number of prior visits, diagnoses from prior visits, recency-weighted risk scores) without being a sequence model. "
            "Without this intermediate baseline, any improvement from the RNN may reflect the richer feature set available through sequential access rather than the temporal modeling capacity of the RNN architecture.\n\n"
            "AUROC is chosen because it captures 'rank-ordering of predictions, a critical aspect for globally reducing readmission events hospital-wide.' "
            "But clinical deployment of readmission models typically involves intervening on a fixed daily capacity (e.g., the top 50 patients flagged). "
            "Under this operational constraint, precision at a fixed recall cutoff (e.g., Precision@K) or net benefit analysis would be more clinically actionable than aggregate AUROC, which gives equal weight to all operating points regardless of practical capacity."
        ),
        "all_issues_raised": [
            "Patient-level data leakage not addressed: stratification by hospital does not prevent the same patient's visits from appearing in multiple splits",
            "Comparison conflates sequential modeling capacity with richer feature access; no ablation of aggregate sequence features in logistic regression",
            "AUROC is a poor operational metric if clinical intervention operates under fixed daily capacity; Precision@K would be more deployment-relevant",
            "Weak assumption that temporal autocorrelation from hospital practices is negligible across a three-year window with policy changes",
            "Sequence padding strategy is mentioned but not specified; arbitrary padding choices can introduce artificial temporal signals in the RNN"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_817",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design employs a stratified random split on sensor data from 'an extensive timescale' in a domain where equipment failure is driven by wear accumulation — a fundamentally non-stationary, time-ordered degradation process. "
            "A random split means that near-failure sensor readings from week 50 of a component's life are in the training set while earlier-life readings from the same component are in the test set. "
            "Since degradation patterns lead up to failure in a temporal trajectory, this allows the model to recognize pre-failure signatures by retrospective pattern matching rather than prospective detection, inflating apparent performance relative to deployment conditions where only past data is available.\n\n"
            "The rule-based baseline represents 'heuristic decisions that can oversimplify real-time complexities,' but no detail is given about how the rules are constructed, what domain expertise informs them, or how they are calibrated. "
            "In oil and gas, rule-based systems are often based on decades of reliability engineering data and are highly non-trivial. "
            "Without specifying the sophistication of the rule-based system, a win for the ensemble model is uninterpretable: the gain may reflect the inadequacy of a poorly calibrated rule system rather than genuine ML superiority.\n\n"
            "F1-score is selected as the primary metric because it 'balances accuracy between false predictions and missed detections.' "
            "However, in safety-critical industrial equipment, false negatives (missed failures) have asymmetrically high costs compared to false positives (unnecessary inspections). "
            "F1 treats precision and recall as equally important, which is not aligned with the stakeholder objective of minimizing catastrophic failures. "
            "The design should either use a weighted F-beta score with beta greater than 1 (emphasizing recall) or explicitly justify the symmetric weighting. "
            "Additionally, F1 is sensitive to the decision threshold, and no threshold selection strategy is specified."
        ),
        "all_issues_raised": [
            "Random split on wear-accumulation sensor data allows retrospective failure trajectory matching, inflating apparent prospective detection performance",
            "Rule-based baseline sophistication is unspecified; gains may reflect baseline weakness rather than ensemble superiority",
            "F1-score treats false negatives and false positives symmetrically, which is not aligned with asymmetric failure-cost objectives in safety-critical settings",
            "No threshold selection strategy specified for F1 evaluation, making comparisons across models with different operating points unreliable",
            "Interpolation for missing sensor values is mentioned but strategy is unspecified; aggressive interpolation can mask sensor degradation signals"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_791",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design uses a stratified random split while simultaneously noting it 'accounts for the sequential nature of the data while avoiding excessive leakage of future patterns.' "
            "These two claims are in tension: a stratified random split specifically does not account for sequential structure — it is a cross-sectional sampling technique. "
            "For a multi-site hospital system where admissions span three years, a random split will place a patient's second admission in the training set and first admission in the test set, reversing clinical temporality. "
            "A chronological split with patient-level isolation is required to reflect the real-world deployment setting where predictions are made prospectively.\n\n"
            "Recall is selected as the primary metric 'to identify as many true readmissions as possible,' which is clinically motivated. "
            "However, recall in isolation is a degenerate metric: a model that predicts every patient as high-risk achieves perfect recall. "
            "Without a precision constraint or a fixed operating point (e.g., recall at 20% flag rate), recall-maximization does not yield a clinically deployable system. "
            "The design acknowledges precision and F1 as secondary metrics but gives no guidance on how the final operating threshold is chosen or how the recall-precision trade-off is managed in model selection.\n\n"
            "The design includes 'demographic and hospital identifiers within the feature set to mitigate confounds.' "
            "Including hospital identifiers as features allows the model to learn hospital-specific readmission base rates, which would improve performance on held-out patients from known hospitals but would degrade on deployment at a new hospital not seen in training. "
            "This leaks deployment context into the feature set and overstates generalizability. "
            "For a model intended to generalize across a large hospital system — or to be deployed at new sites — hospital identifier should be a stratification variable for subgroup analysis, not a feature."
        ),
        "all_issues_raised": [
            "Internal contradiction: claims stratified random split 'accounts for sequential nature' while it explicitly does not",
            "Recall as primary metric is degenerate without a precision constraint or fixed operating threshold",
            "Hospital identifier as a model feature leaks deployment context and overstates generalizability to new sites",
            "No patient-level isolation in the split; same patient's admissions can appear in training and test, inflating sequence-based model performance",
            "Attention mechanisms in RNN are not ablated; gains could be from RNN capacity rather than from attention-specific contextual weighting"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_805",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The same structural incoherence present in eval_scenario_788 applies here: deep reinforcement learning requires sequential state-action-reward trajectories, but the design employs a stratified random split on historical inventory data. "
            "RL agents learn by interacting with an environment through time; randomly partitioning daily records destroys the episode structure. "
            "The design acknowledges that 'temporal autocorrelation is weak, requiring further validation' — but for DRL in inventory management, temporal correlation is not a statistical nuisance to be validated away; it is the mechanism through which the RL agent learns optimal policies. "
            "No simulation environment, historical replay buffer, or offline RL evaluation methodology is described.\n\n"
            "The rule-based baseline is 'appropriately tuned to manage similar inventory costs,' but the DRL system is trained to minimize stockouts as its reward signal. "
            "If the two systems optimize different objectives (DRL: stockout minimization; rule-based: cost management), then a stockout-based primary comparison favors the system whose training objective matches the evaluation metric. "
            "This is not a fair comparison. "
            "For a valid head-to-head, both systems should be evaluated on the same composite metric that reflects the actual multi-objective trade-off (stockouts, holding costs, order costs) that practitioners care about.\n\n"
            "Promotional events and seasonal cycles are acknowledged as potential confounds and handled by adding external demand features. "
            "But DRL agents trained on historical data that includes promotional spikes may learn to anticipate promotions only through pattern repetition — they would fail on novel promotional structures not seen during training. "
            "No ablation or sensitivity analysis tests whether the DRL policy is robust to promotions it has not seen, which is the real deployment challenge for a retail supply chain."
        ),
        "all_issues_raised": [
            "Stratified random split is incompatible with DRL's sequential episode learning structure; no simulation environment or offline RL framework described",
            "Objective mismatch: DRL trained on stockout minimization, rule-based baseline tuned on cost management; primary metric favors DRL by design",
            "No robustness test for novel promotional structures not present in training; policy may not generalize to unseen demand patterns",
            "DRL policy architecture, state space, action space, and reward function are entirely unspecified",
            "Six-month evaluation period may not capture annual seasonal cycles; unclear whether it covers a representative demand period"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_800",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design justifies its stratified random split by asserting that 'temporal autocorrelation in patient outcomes is not significant enough to necessitate a purely chronological split.' "
            "For hospital readmission prediction, this assumption is unlikely to hold: readmission rates in the United States have been systematically declining since the CMS Hospital Readmissions Reduction Program began penalizing readmissions, and care protocols, discharge criteria, and follow-up infrastructure have evolved continuously over the three-year window. "
            "A random split allows models to train on improved-care-era records and test on earlier records, overstating the generalizability of learned patterns to future deployment conditions.\n\n"
            "Recall is chosen as the primary metric 'to minimize false negatives and better capture high-risk patients.' "
            "As with other readmission studies in this batch, recall in isolation rewards the trivial all-positive classifier. "
            "The design does not specify the operating threshold for recall computation, the acceptable false positive rate in the clinical workflow, or how recall is reported (at a fixed threshold vs. at maximum for the validation curve). "
            "In a hospital setting with limited care-coordination staff, flagging 100% of patients as high-risk is operationally infeasible; the metric must be anchored to a capacity constraint.\n\n"
            "The RNN uses 'time-stamped sequences of diagnosis codes, treatment history, and follow-up visits,' while logistic regression uses 'aggregate demographic and clinical variables.' "
            "This is again a two-dimensional comparison — sequence model vs. non-sequence model, and raw codes vs. aggregated features. "
            "To isolate the value of sequential modeling, the experiment needs a logistic regression or MLP model that receives the same sequential inputs as aggregate statistics, confirming that any gap reflects temporal modeling capacity rather than feature richness difference."
        ),
        "all_issues_raised": [
            "Temporal autocorrelation assumption is empirically unsupported given documented secular trends in readmission rates under CMS policy",
            "Recall as primary metric is degenerate without fixed-capacity constraint or precision lower bound",
            "Comparison conflates sequential modeling benefit with richer feature access; no aggregate-sequence baseline for logistic regression",
            "No patient-level split isolation specified; same patient's records may straddle train and test sets",
            "Sequence padding for variable-length visit histories is unspecified; can introduce artificial temporal patterns"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_819",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design applies a stratified random split to vehicle telemetry data and describes it as 'preserving temporal correlations while allowing cross-sectional analysis.' "
            "These objectives are contradictory: a random split breaks temporal ordering by construction. "
            "Vehicle telemetry follows a degradation trajectory — engine wear, oil viscosity changes, and vibration patterns develop over component life cycles. "
            "A random split places readings from near the end of a component's operational life in the training set while holding out readings from earlier in that same component's life as test data. "
            "This allows the CNN to learn failure-proximity patterns and then evaluate them on observations that precede failure — inverting causal directionality.\n\n"
            "The task framing is ambiguous: the hypothesis claims to predict 'maintenance needs' and 'the necessity for maintenance before failures occur,' suggesting binary classification (maintenance needed: yes/no), yet MAE is chosen as the primary metric, which is appropriate for regression (e.g., predicting time-to-next-maintenance). "
            "The design does not clarify whether the target variable is a continuous time-to-event, a binary maintenance indicator, or something else. "
            "This ambiguity means the model architecture (CNN) may be evaluated with a metric inappropriate for the actual output type.\n\n"
            "The baseline is linear regression on 'historical data points.' "
            "In predictive maintenance, the standard non-deep baseline is a survival model (Cox PH, Weibull AFT) or a gradient-boosted tree on engineered features, both of which are substantially more competitive than linear regression for the non-linear degradation patterns in telemetry data. "
            "Beating linear regression with a CNN does not constitute evidence of CNN superiority over the class of models actually used in automotive predictive maintenance."
        ),
        "all_issues_raised": [
            "Internal contradiction: design claims random split 'preserves temporal correlations' while it explicitly destroys them",
            "Task ambiguity: MAE metric implies regression but hypothesis describes a binary 'maintenance needed' detection problem",
            "Linear regression baseline is too weak; survival models or gradient-boosted trees are the appropriate comparators for telemetry-based maintenance",
            "Vehicle-level isolation not described; same vehicle's readings could appear in both training and test sets",
            "Stratification by vehicle type is stated as a goal but the mechanics of ensuring balanced fleet representation across splits is not described"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_782",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design itself acknowledges the central tension: 'critics may argue that temporal dependencies should guide data partitioning to avoid potential leakage.' "
            "This is not merely a critic's argument — it is a methodological necessity in ICU deterioration prediction. "
            "ICU patient data is characterized by strong serial autocorrelation in vital signs; an observation from hour 48 is highly correlated with the observation from hour 47 for the same patient. "
            "A stratified random split places hourly observations from the same patient in training and test sets, and the model can effectively learn patient-specific baseline vital sign ranges, then 'predict' deterioration by recognizing deviations from those patient-specific norms that it saw during training. "
            "This is not generalizable and inflates performance relative to a truly prospective evaluation.\n\n"
            "The comparison between TCNs and LSTMs is a valuable architectural question, but the design does not specify matched model capacity. "
            "TCNs with large dilation factors can have dramatically larger effective receptive fields than LSTMs with the same parameter count. "
            "If the TCN has been given a longer temporal horizon by architectural design, any performance advantage may reflect access to longer context rather than a fundamental representational superiority. "
            "A controlled experiment would match receptive field length or run a systematic ablation over context window sizes for both architectures.\n\n"
            "AUC is the primary metric, but in ICU deterioration prediction the clinical objective is typically to generate alerts within a fixed lead time before deterioration events. "
            "AUC evaluates overall discriminative ability across all operating points but says nothing about whether the model fires alerts sufficiently far in advance of events to permit clinical intervention. "
            "Time-to-alert or sensitivity at a specific early warning lead time (e.g., 2 hours before event) would be more clinically meaningful and should be included as primary metrics."
        ),
        "all_issues_raised": [
            "Stratified random split creates patient-level data leakage in strongly autocorrelated ICU time series; design acknowledges the risk but proceeds anyway",
            "TCN vs. LSTM comparison is not capacity-controlled; TCN effective receptive field may be longer, confounding architectural comparison with context length",
            "AUC is not aligned with ICU clinical objective of early warning; time-to-alert lead time metrics are absent",
            "No patient-level isolation in the split; same patient's hourly observations can span training and test sets",
            "Nursing notes are listed as a data source but no NLP preprocessing or inclusion strategy for unstructured text is described"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_783",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design uses wearable device data collected over 'the past year' for 10,000 patient records. "
            "If the neural network uses time-series sequences from wearable devices and the data spans one year, many patients may have very short or discontinuous wearable records if device adoption varied. "
            "The design does not describe the average duration of wearable device wear per patient, the fraction of patients with complete vs. sparse coverage, or how patients who stopped wearing devices before the 30-day readmission window are handled. "
            "This missingness is almost certainly non-random and likely correlated with readmission risk (sicker patients may be less compliant with wearables), which would bias both training and evaluation.\n\n"
            "The stratified random split on a one-year dataset is less problematic temporally than for multi-year datasets, but a critical patient-level isolation requirement is not mentioned. "
            "A patient discharged multiple times within the year could have their admissions split across training and test sets. "
            "The neural network would then see the patient's wearable data from one admission during training and predict on a different admission for the same patient — effectively seeing the patient's physiological baseline, which is a form of data leakage that favors the sequence model.\n\n"
            "The comparison between a neural network on wearable device time-series and logistic regression on 'clinical demographics' is not a controlled test of the wearable data hypothesis. "
            "The logistic regression baseline does not include any wearable features; its inferiority could be due to using a weaker model, using fewer features, or using less informative feature types. "
            "A three-arm design — (1) logistic regression on demographics, (2) logistic regression on wearable features, (3) neural network on wearable sequences — is needed to isolate the contribution of the sequence modeling architecture from the information content of wearable data."
        ),
        "all_issues_raised": [
            "Wearable coverage completeness is unaddressed; non-random device dropout likely correlated with readmission risk, biasing labels",
            "No patient-level split isolation; multiple admissions per patient can straddle train and test sets, leaking patient physiological baseline to the neural network",
            "Comparison conflates wearable data information value with neural network architectural advantage; no wearable-features logistic regression arm",
            "Dataset size (10,000 records, one year) may be insufficient for stable AUROC estimation at patient subgroup level",
            "Wearable aggregation window sizes are unspecified; choice of aggregation window significantly affects what temporal patterns the model can detect"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_815",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "A fundamental tension exists between the 'unsupervised anomaly detection' framing and the supervision implicit in the evaluation design. "
            "The design uses fault labels from maintenance logs to construct a stratified split, to define the primary metric (mean time to failure), and to evaluate precision at top-K anomalies. "
            "An unsupervised autoencoder learns reconstruction error from normal operating data; it does not use fault labels during training. "
            "Yet the evaluation is entirely label-dependent. "
            "This means the 'unsupervised' claim is accurate for the training phase but not for threshold selection: to decide which reconstruction errors constitute anomalies, the threshold must be set using the validation set with fault labels. "
            "This introduces supervision at the critical decision boundary, which is not acknowledged or controlled for in the design.\n\n"
            "Mean time to failure (MTTF) as the primary evaluation metric is conceptually misaligned with how anomaly detection models are evaluated. "
            "MTTF measures the average time between failures in a system — it is a reliability engineering metric for the physical equipment, not a model performance metric. "
            "What the design likely intends is 'mean lead time from anomaly alert to actual failure,' which measures how early the model fires before a fault occurs. "
            "This is a meaningful metric, but it is different from MTTF and conflating the two creates interpretive confusion. "
            "Additionally, this metric requires knowing when faults occurred, reintroducing the label dependency that the 'unsupervised' framing sought to avoid.\n\n"
            "The stratified random split on temporal fault data carries the same leakage risk as in other industrial cases: sensor readings in the hours before a fault (the most anomalous and distinctive) would appear in both training and test partitions for the same fault event, allowing the autoencoder to implicitly learn fault-specific reconstruction patterns during training."
        ),
        "all_issues_raised": [
            "Unsupervised framing is contradicted by label-dependent threshold selection, stratified splitting, and evaluation against fault ground truth",
            "MTTF is a reliability engineering metric for equipment, not an anomaly detection model performance metric; the design likely intends alert lead time",
            "Stratified random split on temporal sensor data allows pre-fault anomalous readings to appear in both training and test partitions of the same fault event",
            "No description of the normal operating period used to train the autoencoder, or how the boundary between normal and pre-fault data is defined for training",
            "Precision at top-K anomalies requires a threshold or ranking rule that is not specified for the autoencoder output"
        ],
        "critic_verdict": "critique_wins"
    },

    {
        "case_id": "eval_scenario_810",
        "run_idx": 0,
        "condition": "biased_debate",
        "category": "mixed",
        "critic_raw": (
            "The design proposes using a BERT-based NLP model on 'interaction logs' that include course access frequency, forum participation, and assignment engagement. "
            "These are primarily structured behavioral metrics, not natural language text. "
            "BERT is designed to process natural language sequences and derives its power from pre-training on text corpora. "
            "Applying BERT to numerical frequency metrics converted to token sequences is an architectural mismatch: BERT's self-attention over tokenized integers does not provide meaningful linguistic contextual representations. "
            "The design does not clarify whether any text is actually being processed (e.g., forum post content), or whether BERT is being applied to structured interaction counts, which would be a fundamental misapplication of the architecture.\n\n"
            "The design specifies that 'dropout instances will be oversampled in the training data' but does not state whether oversampling occurs before or after the train/validation/test split. "
            "If oversampling is applied before splitting, synthetic or duplicated minority-class examples will appear in both training and test sets, creating data leakage and overstating performance on the minority class. "
            "This is a well-documented implementation error that invalidates AUPRC estimates. "
            "The design should explicitly confirm that oversampling is applied only within the training fold, after the test set has been held out.\n\n"
            "The AUPRC primary metric is appropriate for imbalanced binary classification, but the design notes that 'exogenous factors such as course revisions are partly mitigated by integrating related covariates, although not wholly eliminable.' "
            "For education dropout prediction, course-level effects are strong confounders: a poorly designed course will have high dropout regardless of student characteristics, and models trained on multi-course data will capture course quality as a latent feature without distinguishing it from student-level risk factors. "
            "Without course-level fixed effects, the model conflates student dropout risk with course dropout rate, and the AUPRC reflects both — making the metric misleading for the stated goal of identifying at-risk students."
        ),
        "all_issues_raised": [
            "BERT applied to structured interaction frequency metrics is an architectural mismatch; BERT's pre-training confers no benefit on tokenized numerical data",
            "Oversampling placement relative to the train/test split is unspecified; pre-split oversampling would contaminate the test set with synthetic examples",
            "Course-level fixed effects not controlled; model conflates student dropout risk with course quality, making AUPRC misleading for student-level targeting",
            "Stratified random split ignores temporal learning dynamics; early-course interaction patterns from one cohort may not predict dropout for a later cohort",
            "Baseline is demographic-only logistic regression; no behavioral-features logistic regression arm to isolate the NLP contribution from engagement-data contribution"
        ],
        "critic_verdict": "critique_wins"
    }

]

output_path = Path("/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v6/v6_interim_biased/chunk_4_run0_critic.json")
output_path.write_text(json.dumps(cases, indent=2, ensure_ascii=False))

print(f"Wrote {len(cases)} cases to {output_path}")
# Sanity checks
assert len(cases) == 20, f"Expected 20 cases, got {len(cases)}"
ids = [c["case_id"] for c in cases]
print("Case IDs:", ids)
expected_ids = {
    "eval_scenario_799", "eval_scenario_801", "eval_scenario_806",
    "eval_scenario_811", "eval_scenario_809", "eval_scenario_701",
    "eval_scenario_814", "eval_scenario_794", "eval_scenario_788",
    "eval_scenario_820", "eval_scenario_786", "eval_scenario_817",
    "eval_scenario_791", "eval_scenario_805", "eval_scenario_800",
    "eval_scenario_819", "eval_scenario_782", "eval_scenario_783",
    "eval_scenario_815", "eval_scenario_810"
}
assert set(ids) == expected_ids, f"ID mismatch: {set(ids).symmetric_difference(expected_ids)}"
print("All checks passed.")
