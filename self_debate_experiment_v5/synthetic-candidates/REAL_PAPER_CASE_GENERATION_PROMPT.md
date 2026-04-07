# Real-Paper Hard Case Generation Prompt

**Scope:** Hard cases only (difficulty=hard). Supplements `benchmark_case_generation_prompt.md` — use this prompt to generate cases grounded in documented real-world methodological failures rather than invented scenarios.

**For use with a non-Anthropic LLM (e.g., GPT-4o, GPT-5, Gemini, etc.)**

**Purpose:** Generate 12–15 hard benchmark cases by transposing documented methodological flaws from real published ML papers into anonymized, camouflaged scenarios. Cases generated this way are harder than invented cases because the flaws were missed by actual expert reviewers — they are genuine, not constructed to be tractable.

**How to use:**
1. Paste this entire document as the system/instruction prompt
2. Request 12–15 hard cases using the source paper library below
3. Request output as a JSON array matching the schema in the Output Format section
4. Run the v5 self-evaluation tests on each case before output
5. Run Phase 5.5 difficulty gate — acceptance criterion: ≥ 6 of 10 sampled cases score mean < 0.55 with `claude-haiku-4-5` as single-pass evaluator

---

## Why Start From Real Papers

Previous prompts asked the model to invent hard cases from scratch. This reliably produces cases that are too easy, for a structural reason: when you invent a flaw, you unconsciously include enough signal to make it findable. Real paper flaws were missed by peer reviewers, domain experts, and the research community — sometimes for years. They are hard because they were genuinely hard, not because they were designed to be solvable.

The external benchmark cases (Dacrema, Obermeyer, DeGrave) scored consistently below the invented hard cases for precisely this reason: the flaws were real, the confounds were genuine, and the methodology sections were written by researchers who believed the work was sound.

**The approach:** Take a real paper's methodology, extract the core flaw mechanism, transpose it to a structurally analogous domain that obscures the source, and write a case where the flaw is embedded in an otherwise-sound-looking methodology memo. The flaw type is preserved; the source paper is not recognizable.

---

## Source Paper Library

Each entry provides the flaw mechanism for use in case construction. **Do not reproduce the source paper domain or scenario verbatim** — transpose to a different domain as specified in the Transformation Instructions section. The source paper is never shown to agents; it is recorded only in the `source_paper` field for operator provenance tracking.

---

### Source 1 — Dacrema et al. (2019), RecSys

**Domain:** Recommendation systems

**Methodology:** Evaluated 18 neural recommender systems against simple baselines (ItemKNN, PureSVD, BPR) on standard datasets. Neural methods consistently outperformed baselines in the original papers.

**Core flaw:** The baselines were not tuned — hyperparameter search was applied to the neural models but not to the simple baselines. When baselines were properly tuned with the same budget, 7 of 9 neural methods were outperformed by at least one simple baseline. The claim of neural superiority rests on an asymmetric comparison.

**Flaw type:** `critical_omission` — omission of baseline tuning from the evaluation protocol, not stated as a limitation

**Transpose to:** Any model comparison domain where a new complex method is compared to a legacy baseline — churn prediction, fraud scoring, clinical risk stratification, document classification

---

### Source 2 — Obermeyer et al. (2019), Science

**Domain:** Clinical ML, population health management

**Methodology:** A commercial risk-stratification algorithm assigned patients to a "high-risk" care management program based on predicted healthcare cost. The algorithm achieved high accuracy (AUC 0.77 on cost prediction).

**Core flaw:** The algorithm uses cost as a proxy for health need, under the implicit assumption that cost and need are equally correlated across demographic groups. They are not: due to systemic unequal access to care, Black patients with the same disease burden generate lower healthcare costs than White patients, so the algorithm systematically underestimates their health need. At a given risk score, Black patients were significantly sicker than White patients.

**Flaw type:** `assumption_violation` — proxy variable assumed to be an unbiased measure of the target concept, but the proxy is itself biased by a systemic factor that correlates with the protected attribute

**Transpose to:** Any domain where an observable quantity is used as a proxy for an unobservable target, and where the proxy relationship may differ across subgroups — salary history as proxy for job performance in hiring, spending patterns as proxy for creditworthiness in lending, service call frequency as proxy for equipment health in predictive maintenance

---

### Source 3 — DeGrave et al. (2021), Nature Machine Intelligence

**Domain:** Medical imaging, COVID-19 detection

**Methodology:** Trained CNNs on chest radiographs from multiple hospital systems to detect COVID-19. Models achieved AUC > 0.90 on internal test sets drawn from the same hospitals.

**Core flaw:** The training data confounds hospital-specific imaging artifacts (positioning conventions, equipment signatures, metadata text burned into images) with disease labels. The model learned hospital membership as a shortcut to COVID-19 status — hospitals that treated more COVID patients in a given period had distinctive imaging characteristics. No out-of-hospital validation was performed, so the shortcut was not discovered until external deployment.

**Flaw type:** `critical_omission` — omission of external validation across sites; the evaluation protocol cannot distinguish genuine disease detection from hospital-membership detection

**Transpose to:** Any multi-site model trained on data where site membership is confounded with label prevalence — network intrusion detection trained across different enterprise environments, manufacturing defect detection across factories, fraud detection trained on data from specific merchant categories

---

### Source 4 — Lazer et al. (2014), Science

**Domain:** Public health surveillance, big data prediction

**Methodology:** Google Flu Trends (GFT) predicted influenza-like illness (ILI) prevalence by correlating search query volume against CDC surveillance data. The model used 50 million terms fit against 1,152 weekly ILI measurements.

**Core flaw:** Severe overfitting from extreme dimensionality (50M features, 1,152 labels) combined with a stationarity assumption — the model assumed the relationship between search queries and ILI incidence was stable. Google's search algorithm changed 86 times in a single month during one influenza season, altering query distributions independently of actual disease prevalence. GFT overestimated ILI by a factor of 2 during the 2012–2013 season.

**Flaw type:** `assumption_violation` — stationarity assumption violated by changes in the feature-generating process that are independent of the target variable

**Transpose to:** Any model trained on user-generated behavioral signals that assumes the signal-to-target relationship is stable — app usage as proxy for customer health in SaaS, click-through rate as proxy for content quality in recommendation, support ticket volume as proxy for product defect rate

---

### Source 5 — Zech et al. (2018), PLOS Medicine

**Domain:** Clinical ML, radiology

**Methodology:** Trained a CNN on chest X-rays for pneumonia detection across multiple hospital datasets. Internal validation (same hospital system) achieved AUC 0.931. The paper reported this as strong generalization performance.

**Core flaw:** The model learned hospital-system-specific artifacts alongside pneumonia features. External validation at a different hospital yielded AUC 0.815. Further analysis showed the model could identify which hospital system an image came from with high accuracy — evidence that hospital membership was a confounding variable. The evaluation protocol used train/test splits within the same hospital system, making this confound invisible.

**Flaw type:** `assumption_violation` — i.i.d. assumption violated by unmeasured site-level confounders; internal validation is presented as evidence of generalization

**Transpose to:** Models trained on data from a single organization or region presented as generalizable — HR attrition models trained on one company's employees, credit default models trained on one lender's portfolio, product failure models trained on one factory's production line

---

### Source 6 — Recht et al. (2019), ICML

**Domain:** Computer vision, benchmark evaluation

**Methodology:** Evaluated ImageNet-trained classifiers on a new test set constructed by carefully replicating the original data collection procedure (same search terms, same annotation protocol, same filtering). Models trained on the original ImageNet training set were evaluated on both the original test set and the new test set.

**Core flaw:** Despite the nearly identical collection procedure, accuracy dropped 11–14% on the new test set for all evaluated models. The models had implicitly overfit to the idiosyncratic properties of the original test set over years of iterative improvement on it. The original test set was treated as representative of the distribution, but models had learned to exploit its specific quirks.

**Flaw type:** `critical_omission` — omission of temporal or distributional holdout; long-term iteration on a fixed test set causes implicit leakage even without direct access to test labels

**Transpose to:** Any domain with a long-lived benchmark that has been used for iterative model selection — leaderboard-driven ML competitions, clinical risk scores validated on the same population cohort over many years, NLP benchmarks used as primary selection criteria across multiple paper cycles

---

### Source 7 — Hooker et al. (2019), NeurIPS

**Domain:** ML interpretability evaluation

**Methodology:** Proposed ROAR (RemOve And Retrain) as an evaluation protocol for feature importance methods. The protocol removes features ranked as important by each method, retrains the model, and measures accuracy degradation. Methods producing larger accuracy degradation are judged better.

**Core flaw:** The retraining step changes the model being evaluated. A salience map describes how the *original* model uses features. ROAR evaluates what happens when a *different model* is trained without those features — a different question. Additionally, removing top-ranked features shifts the input distribution, making the retrained model's accuracy on the modified distribution incomparable to the original. The protocol conflates "explanatory faithfulness" with "feature usefulness for prediction."

**Flaw type:** `wrong_justification` — the evaluation protocol is justified as measuring salience map quality, but it measures a different quantity; the justification is plausible but technically wrong

**Transpose to:** Any evaluation where the measurement procedure modifies the system it is intended to evaluate — A/B test designs that change user behavior by exposure to the treatment condition, benchmark contamination where evaluation data is used for fine-tuning, calibration assessment that uses the calibration procedure to generate the ground-truth labels

---

### Source 8 — SMOTE Before Cross-Validation (Documented Pitfall)

**Domain:** Classification with class imbalance

**Methodology:** Applied SMOTE to generate synthetic minority class samples on the full dataset before performing k-fold cross-validation. Reported significantly improved minority class recall and F1. Justified as: "SMOTE was applied to the training data to address class imbalance."

**Core flaw:** SMOTE before CV creates data leakage. Synthetic samples are generated from all available instances, including those that will appear in validation folds. During CV, synthetic samples derived from a held-out instance may appear in the training fold, causing the model to have effectively seen information from the validation set. This inflates CV estimates by 0.1–0.2 AUC in documented cases. The justification ("applied to training data") describes the intent correctly but the implementation is wrong — the split must occur before SMOTE, not after.

**Flaw type:** `wrong_justification` — the justification describes correct practice but the implementation order violates it; the error is in the execution sequence, not the stated procedure

**Transpose to:** Any preprocessing step that generates new data from the training corpus before a split is applied — feature scaling fit on combined train+test data, data augmentation applied before train/test split, imputation using statistics computed on the full dataset

---

### Source 9 — Caruana et al. (2015), KDD

**Domain:** Clinical ML, pneumonia mortality prediction

**Methodology:** Trained rule-based models and neural networks to predict pneumonia mortality risk from structured clinical data. Discovered that both model types learned that having asthma lowers pneumonia mortality risk.

**Core flaw:** This is the opposite of the true causal relationship (asthma is a major risk factor for pneumonia mortality). The confounding arose from the clinical protocol: patients with asthma and pneumonia were triaged directly to the ICU and received intensive treatment, so their outcomes in the training data were better than average. The model learned the *treatment selection rule* rather than the underlying risk. The training data reflects observed outcomes under existing clinical protocols, not counterfactual outcomes under a neutral protocol.

**Flaw type:** `assumption_violation` — assumes training labels reflect unconfounded causal relationships; violated by treatment selection bias (high-risk patients receive differential treatment, improving their observed outcomes)

**Transpose to:** Any predictive model trained on historical data where the target outcome was affected by an existing intervention that was triggered by risk level — fraud detection trained on data where suspicious transactions were manually reviewed and blocked, predictive maintenance trained where high-risk equipment was proactively replaced, churn prediction trained where high-predicted-churn customers received retention offers

---

### Source 10 — Time Series Leakage via Pre-Generated Sequences

**Domain:** Time series forecasting

**Methodology:** Generated input-output sequence pairs from a time series dataset and then performed an 80/20 train-test split on the generated sequences. Reported strong generalization performance on the test set.

**Core flaw:** When sequences overlap temporally (a sliding window of length L generates sequences starting at t, t+1, t+2, ...), splitting the sequence list randomly causes adjacent-window sequences to appear in both train and test sets. The model sees training sequences whose input windows overlap with test sequences' target windows — a form of temporal leakage. Splitting must occur on the *original time series* before sequence generation, not on the *generated sequence list*.

**Flaw type:** `critical_omission` — no disclosure of whether the split was performed on the original time series or on the generated sequences; omits the ordering of split vs. sequence generation

**Transpose to:** Any model trained on derived records from a time-ordered source — session-based models derived from user log data, image patch models derived from video frames, event prediction models derived from longitudinal records

---

### Source 11 — Offline-Online Gap in Recommendation Systems

**Domain:** Recommendation systems, offline evaluation

**Methodology:** Evaluated a new recommendation algorithm using Leave-One-Out Cross-Validation (LOOCV) on a static user interaction dataset. Reported 12% improvement in Precision@10 over the baseline. Proposed deployment based on this offline result.

**Core flaw:** LOOCV on a static dataset does not reflect the temporal dynamics of the deployment setting. The test items are drawn uniformly from each user's history regardless of recency, but in production the model must predict future interactions from past ones. The offline evaluation metric measures reconstruction of a static snapshot, not forecasting of future behavior. Algorithms that exploit popularity patterns perform well offline but poorly online because popularity distributions shift after deployment.

**Flaw type:** `assumption_violation` — offline evaluation assumes the test set reflects the same distribution as future deployment conditions; violated by temporal non-stationarity in user preferences and item popularity

**Transpose to:** Any system where a static offline evaluation is used to justify an online deployment decision — A/B test surrogates trained on historical data, predictive models for future market conditions calibrated on past data, anomaly detectors calibrated on historical baselines when the baseline is known to drift

---

### Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)

**Domain:** Language model fine-tuning, RLHF

**Methodology:** Trained a reward model from human preference data, then used PPO to optimize a language model against this reward model. Reported substantial gains on human preference evaluations (win rate vs. reference model).

**Core flaw:** The reward model is an imperfect proxy for human preferences. As the policy model is optimized against it, the policy learns to exploit gaps between the reward model's learned proxy and true human preferences — a form of Goodhart's Law. The human evaluation used to validate the result was conducted on the *same distribution of prompts* as the training reward model, making it likely that the evaluation captured reward hacking that happened to look good on familiar prompts. External evaluation on out-of-distribution prompts showed degraded performance.

**Flaw type:** `assumption_violation` — proxy optimization assumes the reward model is a sufficiently faithful proxy; violated by reward hacking that generalizes within the evaluation distribution but not beyond it

**Transpose to:** Any system where optimization against a surrogate metric is evaluated using the same surrogate — click-through rate optimization evaluated on click-through rate, safety classifiers fine-tuned to satisfy their own outputs, model compression evaluated on the benchmark it was compressed for

---

## Transformation Instructions

For each case, select one source paper and perform the following transformation:

### Step 1: Extract the flaw mechanism

Write a one-sentence description of the flaw at the level of **abstract mechanism**, not domain-specific instance. Examples:
- NOT "cost is used as proxy for health need, which is biased for Black patients"
- YES "a proxy variable is used to measure an unobservable target quantity, under the assumption that the proxy-target correlation is uniform across subgroups; the assumption fails because a systemic factor affects the proxy but not the target differently across subgroups"

### Step 2: Select a target domain

Choose a domain that:
- Preserves the abstract flaw mechanism
- Is structurally analogous but surficially different from the source
- Does not share key vocabulary with the source paper (different disease, different model type, different industry)
- Belongs to a domain not used by more than 2 other cases in the batch

Suggested transpositions by source:

| Source domain | Suggested transpositions |
|---|---|
| Clinical ML, radiology | Fraud detection, HR analytics, manufacturing QC |
| Recommendation systems | Search ranking, content moderation, financial scoring |
| Public health surveillance | Ops monitoring, demand forecasting, IoT anomaly detection |
| NLP/text | Tabular classification, time series, vision |
| Computer vision | Sensor data, genomics, document processing |

### Step 3: Write the case prompt

Write a 500–800 word internal memo, evaluation report, or launch proposal. Requirements:
- Opens with a positive result or deployment recommendation — no problem statements
- Every stated fact must be consistent with every other stated fact (the flaw is not a factual inconsistency)
- The flaw is present as an assumption violation, critical omission, or wrong justification — NOT as an explicit statement of a problem
- Apply all v5 trigger phrase prohibitions: no contrast signals, no compensation language, no parallel before/after structure
- Include at least one plausible concern with a defensible but incomplete justification (the `must_not_claim` item)
- Include realistic operational detail: team names, timelines, infrastructure, deployment numbers

### Step 4: Verify the flaw is not source-recognizable

A reviewer who knows the source paper must not be able to identify it from the task_prompt. Check:
- Domain is different from source paper domain
- Model type / algorithm type is different
- No shared vocabulary with the source paper title or abstract
- The flaw is present at the mechanism level, not the surface level

### Step 5: Complete the schema

Populate all required fields. The `source_paper` field is operator-only metadata — never include it in `task_prompt`, `ideal_critique`, or `ideal_defense`.

---

## Constraints

### Category distribution (across all 12–15 generated cases)
| Category | Target n |
|---|---|
| broken_baseline | 2–3 |
| metric_mismatch | 2–3 |
| hidden_confounding | 3–4 |
| scope_intent_misunderstanding | 2–3 |
| defense_wins | 2 |
| real_world_framing | 1–2 |

### Position and must-find
- At least 5 cases must have `correct_position: "mixed"` with `empirical_test_agreed` resolution
- Non-defense_wins cases: 3–5 `must_find_issue_ids` each
- Defense_wins cases: 0 `must_find`; `planted_issues` documents the false concern trap
- Every case: 2–4 `must_not_claim` items, each grounded in a plausible prompt-internal concern with incomplete justification

### Source paper diversity
- No source paper may be used more than twice
- At least 8 different source papers must be represented across the batch
- The same abstract flaw mechanism may appear in at most 2 cases (even from different sources)

### Domain diversity
- No domain (clinical, recommendation, fraud, NLP, etc.) may be used more than 3 times
- The target domain must differ from the source domain for all cases

---

## Output Format

Return a JSON array. No markdown formatting. Output starts with `[` and ends with `]`.

Each case object uses the v5 schema with one additional field:

```json
{
  "case_id": "eval_scenario_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "difficulty": "hard",
  "task_prompt": "500–800 word memo/report. Internally consistent. Opens with positive result. Flaw is camouflaged real-paper flaw, transposed to target domain.",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct conclusion.",
    "required_empirical_test": "For empirical_test_agreed cases: the exact experiment. For others: null."
  },
  "planted_issues": [
    {
      "issue_id": "opaque_snake_case_id",
      "description": "What the issue is and why it matters. For defense_wins: the false concern trap.",
      "severity": "low | medium | high",
      "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification",
      "requires_external_knowledge": "One sentence: what domain knowledge is needed to find this flaw."
    }
  ],
  "ideal_critique": ["What a well-calibrated critique should find."],
  "ideal_defense": ["What a well-calibrated defense should concede or contest."],
  "ideal_debate_resolution": {
    "type": "critique_wins | defense_wins | empirical_test_agreed",
    "supports_critique_if": "Specific, falsifiable result pattern.",
    "supports_defense_if": "Specific, falsifiable result pattern.",
    "ambiguous_if": "Specific, falsifiable result pattern."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["issue_id_1"],
    "must_not_claim": ["plausible_but_wrong_concern_1"],
    "acceptable_resolutions": ["critique_wins"]
  },
  "suspicious_but_valid_features": "For defense_wins cases only: a plain-English list of the features that make the work *look* methodologically problematic to a pattern-matching critic but are actually justified (e.g., 'Small n=47 justified by pre-specified power analysis', 'Non-standard 0.22 threshold derived analytically from cost matrix'). This is a human-readable summary for the CASE_VERIFIER — it supplements `planted_issues` and `must_not_claim`. For non-defense_wins cases: null.",
  "ground_truth_rationale": "2-3 sentences. Answer key only.",
  "difficulty_justification": "Which v5 principles make this case hard. Which specific rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) a single-pass assessor should fail on and why.",
  "source_paper": "Author (year), Venue — operator provenance only, never shown to agents.",
  "verifier_status": "pending",
  "notes": "Which v5 self-evaluation tests each case passes."
}
```

---

## Self-Evaluation (Required Before Output)

Run all five tests on every case. Discard or redesign any case that fails two or more. Record pass/fail for each test in `notes`.

**The Internal Consistency Test:** Read only the `task_prompt`. Can you find ALL must_find issues by checking whether any stated facts contradict each other? If YES — the flaw is a factual inconsistency detectable by pattern-matching. The source paper flaw mechanism should prevent this; if not, the transposition was incomplete. Redesign.

**The Checklist Test:** For the case's category, apply the standard review checklist. Does the checklist mechanically find the flaw? If YES — the flaw type is predictable from the category. Change the category assignment or change the flaw's surface presentation (Principle 6: decouple scenario type from flaw type).

**The Skimming Test:** Read only the first and last paragraphs. Can you determine the correct verdict? If YES — verdict leakage is present. Restructure so the conclusion is not front-loaded or back-loaded.

**The Justification Test:** Does the document acknowledge any concern and provide a justification? For each justification: is it clearly correct, clearly wrong, or subtly wrong? At least one justification per case must be subtly wrong (for Type D flaws) OR the document must contain a must_not_claim item with a justification that is mostly correct but leaves a plausible gap.

**The Run-to-Run Variation Test (proxy difficulty check):** Mentally simulate submitting this task_prompt to a single-pass evaluator twice with temperature > 0. Would both runs produce the same findings, in the same order? If YES — the case has a deterministic single reading. The real-paper sourcing should prevent this (genuine flaws generate genuine uncertainty). If the case still produces deterministic outputs, the transposition has made the flaw too obvious. Redesign.

**The Source Recognition Test (new — required for real-paper cases):** Mentally simulate a reviewer who has read the source paper. Can they identify the source from the task_prompt? If YES — the transposition is insufficient. Change the domain, model type, or core vocabulary until the source is no longer recognizable. The abstract flaw mechanism must be preserved; the surface presentation must not point back to the source.

---

## Difficulty Acceptance Criteria

A case passes the gate if a `claude-haiku-4-5` single-pass assessor scores **mean < 0.55** — meaning Haiku misses ≥ 1 must_find issue, OR asserts a must_not_claim item, OR reaches the wrong verdict.

Additionally, the case should produce **run-to-run variation** when evaluated at nonzero temperature. Verbatim-identical outputs across runs indicate the flaw is too deterministically findable.

Cases that score 1.0 with Haiku, or that produce verbatim-identical outputs, must be redesigned — typically by making the transposition deeper (more domain-specific operational noise, more distance from source paper vocabulary).

---

## Quality Standard

The gold standard for a real-paper case: a senior ML engineer who has NOT read the source paper reads the task_prompt and says "this looks fine" on first pass, then on second pass with specific probing identifies "wait — there's a problem with [the mechanism]." A senior ML engineer who HAS read the source paper should not immediately recognize it.

Cases where the transposition is superficial (same disease, same model type, renamed institution) are rejected. Cases where the flaw mechanism has been distorted in the transposition are also rejected — the flaw must be structurally identical to the source, even if the surface domain is different.

Begin generation now. Generate all 12–15 cases, run the self-evaluation including the Source Recognition Test, then output the final set.

---

## OUTPUT FORMATTING REQUIREMENT

No markdown formatting in the final JSON output. No code fences, no triple backticks, no language tags. Output starts directly with `[` and ends directly with `]`.
