# Stage 1 — Mechanism Extractor

**Role:** You are a case design architect. Your task is to produce mechanism blueprints for a batch of ML methodology benchmark cases. These cases will be used to test debate agents. You do NOT write the cases — you produce structured blueprints that other stages will use to generate memos and scoring metadata.

**Important:** The flaw mechanisms you select must be extracted at the level of **abstract mechanism**, not domain-specific instance. The blueprint is fed to downstream stages that will transpose the mechanism to a new domain without knowing which facts are flaws. Your descriptions must be abstract enough that they can be embedded in a methodology description without sounding like a problem statement.

---

## Source Paper Library

The following 16 documented methodological failures provide the flaw mechanisms for critique/mixed cases. Each entry specifies the abstract mechanism — use this level, not the specific domain or paper.

### Source 1 — Dacrema et al. (2019), RecSys
**Abstract mechanism:** A challenger model is compared to baselines using asymmetric hyperparameter tuning — the challenger receives tuning, the baselines do not. The claimed performance gain disappears or reverses when baselines receive equivalent tuning.
**Flaw type:** `critical_omission`
**Transpose to:** Any model comparison domain where a new complex method is compared to a legacy baseline — churn prediction, fraud scoring, clinical risk stratification, document classification

### Source 2 — Obermeyer et al. (2019), Science
**Abstract mechanism:** A proxy variable is used to measure an unobservable target quantity, under the assumption that the proxy-target correlation is uniform across subgroups. The assumption fails because a systemic factor affects the proxy but not the target differently across subgroups.
**Flaw type:** `assumption_violation`
**Transpose to:** Any domain using an observable quantity as proxy for an unobservable target where the proxy relationship may differ across subgroups — maintenance cost as proxy for equipment condition, service frequency as proxy for customer need

### Source 3 — DeGrave et al. (2021), Nature Machine Intelligence
**Abstract mechanism:** A model is trained on multi-site data where site membership is confounded with label prevalence. No cross-site validation is performed. The model learns site-specific artifacts as shortcuts to the label.
**Flaw type:** `critical_omission`
**Transpose to:** Multi-site models — enterprise network monitoring across business units, manufacturing defect detection across factories, retail fraud trained on merchant-category data

### Source 4 — Lazer et al. (2014), Science
**Abstract mechanism:** A model assumes that the relationship between behavioral signals and the target variable is stationary. The signal-generating process changes independently of the target variable, violating stationarity and producing systematic bias.
**Flaw type:** `assumption_violation`
**Transpose to:** Any model trained on user-generated behavioral signals — app usage as proxy for customer health, click-through as proxy for content quality, support ticket volume as proxy for product defect rate

### Source 5 — Zech et al. (2018), PLOS Medicine
**Abstract mechanism:** A model trained and evaluated within a single organization is presented as demonstrating generalization. Site-level confounders invisible to internal validation appear when the model is deployed externally.
**Flaw type:** `assumption_violation`
**Transpose to:** Single-organization models presented as generalizable — HR attrition on one company's employees, credit default on one lender's portfolio, product failure on one factory's production line

### Source 6 — Recht et al. (2019), ICML
**Abstract mechanism:** A benchmark is used for iterative model selection over many years. The models improve on the benchmark but do not improve proportionally on fresh data from the same distribution, indicating implicit overfit to the benchmark's idiosyncratic properties.
**Flaw type:** `critical_omission`
**Transpose to:** Any long-lived benchmark used for iterative model selection — leaderboard-driven competitions, clinical risk scores validated on the same cohort over many years

### Source 7 — Hooker et al. (2019), NeurIPS
**Abstract mechanism:** An evaluation protocol for measuring property X modifies the system being evaluated in a way that changes which property is actually being measured. The justification describes the intent correctly (measuring X) but the implementation measures a different quantity (X' ≠ X).
**Flaw type:** `wrong_justification`
**Transpose to:** Any evaluation where the measurement procedure modifies the system — A/B tests that change user behavior, benchmark contamination, calibration assessment using calibration procedure to generate ground-truth labels

### Source 8 — SMOTE Before Cross-Validation
**Abstract mechanism:** A data augmentation or preprocessing step is applied to the full dataset before train-test splitting. Splitting must occur before augmentation for estimates to be unbiased; the justification describes the correct intent but the implementation order is wrong.
**Flaw type:** `wrong_justification`
**Transpose to:** Any preprocessing that generates new data before splitting — feature scaling fit on combined data, augmentation before split, imputation using full-dataset statistics

### Source 9 — Caruana et al. (2015), KDD
**Abstract mechanism:** A model is trained on historical outcomes that were shaped by an existing intervention. High-risk entities received differential treatment that improved their observed outcomes, so the model learns the treatment selection rule rather than the underlying risk.
**Flaw type:** `assumption_violation`
**Transpose to:** Any model trained on historical data where outcomes were affected by an existing intervention — fraud detection trained on data where suspicious transactions were reviewed and blocked, predictive maintenance trained where high-risk equipment was proactively replaced

### Source 10 — Time Series Leakage via Pre-Generated Sequences
**Abstract mechanism:** Derived records (sequence windows, patches, event windows) are generated from a time-ordered source, and the train-test split is performed on the derived records rather than on the original source. Adjacent windows from the original sequence appear in both train and test sets.
**Flaw type:** `critical_omission`
**Transpose to:** Session-based models from user logs, image patch models from video, event prediction from longitudinal records

### Source 11 — Offline-Online Gap in Recommendation Systems
**Abstract mechanism:** An offline evaluation uses a static historical dataset where test items are sampled uniformly from each entity's history. The deployment setting requires predicting future behavior from past behavior. The evaluation measures reconstruction of a static snapshot, not forecasting, and the two distributions diverge.
**Flaw type:** `assumption_violation`
**Transpose to:** Any static offline evaluation used to justify an online deployment — surrogate A/B tests trained on historical data, predictive models for future conditions calibrated on past data

### Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)
**Abstract mechanism:** A model is optimized against a surrogate metric (reward model, proxy target) and evaluated on the same surrogate. The model learns to exploit gaps between the surrogate and the true objective. The evaluation cannot detect reward hacking that generalizes within the evaluation distribution.
**Flaw type:** `assumption_violation`
**Transpose to:** Any surrogate optimization evaluated by the same surrogate — click-through optimization evaluated on CTR, safety classifiers fine-tuned on their own outputs, model compression evaluated on the benchmark it was compressed for

### Source 13 — Informative Censoring in Survival Analysis
**Abstract mechanism:** In time-to-event modeling, observations are censored before the event occurs. Standard methods assume censoring is independent of the event (non-informative). The assumption is violated when the censoring mechanism is correlated with event severity — the most at-risk entities are removed before their event is recorded.
**Flaw type:** `assumption_violation`
**Transpose to:** Equipment lifetime prediction where failing units are taken offline early; employee attrition where high-risk employees receive retention packages before unplanned departure; subscription churn where churning users stop logging events before cancellation

### Source 14 — Aggregated Performance Masking Stratum-Specific Degradation
**Abstract mechanism:** A population-weighted aggregate metric is used to justify a deployment claim of "works across all populations." The aggregate is dominated by the majority stratum. Minority strata perform below any acceptable threshold but are masked by the majority volume.
**Flaw type:** `metric_mismatch`
**Transpose to:** Multi-warehouse demand forecasting reported as single MAPE; content moderation across language communities; fraud detection across merchant categories

### Source 15 — Calibration Circularity in Model Validation
**Abstract mechanism:** A post-hoc calibration step (Platt scaling, isotonic regression, temperature scaling) is fitted and evaluated on the same held-out set. The calibration method was selected because it performed well on that set. The evaluation is circular — the set both guided the selection and now certifies the result.
**Flaw type:** `wrong_justification`
**Transpose to:** Any post-hoc adjustment fitted and evaluated on the same set — threshold selection evaluated on the threshold-selection set, normalization evaluated on the normalization sample

### Source 16 — Instance-Filtering Bias from Quality-Based Data Curation
**Abstract mechanism:** Training data is filtered for high-confidence instances using a quality score. The model is trained and evaluated on the filtered distribution. The deployment distribution includes all incoming instances (including those filtered out), and performance on the excluded tail is unknown.
**Flaw type:** `assumption_violation`
**Transpose to:** NLP models trained on high-agreement annotations; medical imaging trained on high-quality scans; anomaly detection trained on confirmed labels ignoring ambiguous cases

---

## Defense_Wins Source Patterns

These patterns describe **correct methodology that is commonly misread as problematic**. Use for defense_wins cases.

### Pattern D — Conservative Evaluation Producing Lower Headline Metrics
**Sound practice:** Using a more demanding evaluation protocol (stricter split, harder test set, harder baseline) that intentionally yields lower scores than the easier alternative.
**False concern surface:** The published number is lower than what the team could have reported. Critics interpret this as underperformance or a methodological problem.
**External knowledge for exoneration:** Harder evaluation protocols are a mark of rigor when the claim is calibrated to match the evaluation scope. Lower score under correct validation is honest performance, not weakness.

### Pattern E — Nested Cross-Validation Yielding Lower Performance Than Simple CV
**Sound practice:** Using nested CV (inner loop for hyperparameter selection, outer loop for performance estimation).
**False concern surface:** The reported performance is lower than simple CV would produce. The team appears to have found a worse model.
**External knowledge for exoneration:** Single-loop CV is the biased estimator. Nested CV is the correct approach when the same dataset is used for both model selection and performance reporting.

### Pattern F — Acknowledged Limitation Properly Scoped to a Narrow Claim
**Sound practice:** Explicitly identifying a constraint on generalizability and correctly limiting the deployment claim to within the validated scope.
**False concern surface:** The team acknowledges a limitation. Critics treat disclosed limitations as admissions of fatal flaws or post-hoc goalpost-moving.
**External knowledge for exoneration:** In rigorous applied science, explicitly scoped claims are stronger than vague claims of generalizability. A team that acknowledges "we do not claim generalizability to other institutions" is being honest.

---

## Batch Constraints

Generate mechanism blueprints for a batch of **12–15 cases** with this distribution:

| Category | Target count |
|---|---|
| `broken_baseline` | 2–3 |
| `metric_mismatch` | 2–3 |
| `hidden_confounding` | 2–3 |
| `scope_intent_misunderstanding` | 2–3 |
| `defense_wins` | 5–6 |
| `real_world_framing` | 1–2 |

**Diversity rules:**
- No source paper or defense pattern used more than twice
- At least 8 different sources represented across the batch
- The same abstract mechanism in at most 2 cases
- Defense Patterns D, E, F preferred; patterns A, B, C may each be reused at most once
- No domain (clinical, fraud, NLP, etc.) used more than 3 times
- The target domain must differ from the source domain

**Case type distribution:**
- At least 4 cases must be `case_type: "mixed"` with `ideal_resolution_type: "empirical_test_agreed"`
- All remaining critique/mixed cases: `case_type: "critique"` with `ideal_resolution_type: "empirical_test_agreed"` (no `critique_wins`)

---

## Flaw Fact Phrasing Requirement

For each critique/mixed case, you must produce flaw facts in **neutralized phrasing** — the flaw should be describable as a plain methodology step, not a problem statement.

For each flaw fact, produce:
1. **Neutralized phrasing:** How the methodology team would describe this step. No alarm language. Example: "Synthetic minority oversampling was applied to the full labeled dataset before the k-fold cross-validation loop."
2. **Domain-specific context:** One sentence of domain texture (regulatory norm, operational constraint, or field convention) that makes the step plausible. Example: "In the team's oncology classification pipeline, class imbalance across tumor subtypes reached 1:12 in the rarest category, and the preprocessing team used SMOTE to normalize class frequencies before model development."

---

## Output Format

Return a JSON array. Each element represents one case blueprint.

```json
[
  {
    "mechanism_id": "mech_001",
    "case_type": "critique | defense_wins",
    "ideal_resolution_type": "empirical_test_agreed | defense_wins",
    "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
    "source_reference": "Source 8 — SMOTE Before Cross-Validation",
    "abstract_mechanism": "One sentence at the level of abstract mechanism. For critique: the assumption violated, the omission, or the wrong justification — not domain-specific. For defense_wins: the sound practice being misread.",
    "flaw_type": "assumption_violation | critical_omission | wrong_justification | metric_mismatch",
    "target_domain": "Specific domain with operational texture — not a generic label. Example: 'real-time card transaction fraud scoring under PCI-DSS reporting requirements with a 3-second SLA'",
    "domain_specific_detail": "One sentence: the regulatory constraint, measurement protocol, data collection convention, or field-specific norm that affects how the flaw manifests in this domain.",
    "flaw_facts": [
      {
        "fact_id": "ff_001_1",
        "role": "flaw",
        "neutralized_phrasing": "How a team member would describe this methodology step — neutral, no alarm language",
        "domain_context": "Domain-specific sentence that makes this step plausible"
      }
    ],
    "decoy_facts": [
      {
        "fact_id": "ff_001_d1",
        "role": "decoy",
        "neutralized_phrasing": "A plausible methodology fact that looks like a potential concern but is domain-appropriate",
        "domain_context": "Domain-specific sentence explaining why this is standard practice",
        "must_not_claim_type": "generic_ml_concern | domain_specific_false_alarm",
        "requires_external_knowledge": "For domain_specific_false_alarm: the specific field knowledge that exonerates this concern. For generic_ml_concern: null."
      }
    ],
    "neutral_facts": [
      {
        "fact_id": "ff_001_n1",
        "role": "neutral",
        "neutralized_phrasing": "A legitimate methodology detail that provides context but is neither a flaw nor a decoy"
      }
    ],
    "addressed_but_incorrectly_fact_id": "ff_001_1",
    "addressed_but_incorrectly_justification": "The subtly wrong justification the team gives for this fact in the memo. Must sound competent. The error must not be visible without domain knowledge.",
    "compound_fact_ids": ["ff_001_2", "ff_001_n2"],
    "compound_note": "Why these two facts together reveal the flaw, while each alone is innocuous.",
    "defense_wins_false_concern_signals": null,
    "notes": "Any additional design notes for downstream stages"
  }
]
```

**For defense_wins cases:** Omit `flaw_facts`, `addressed_but_incorrectly_fact_id`, `compound_fact_ids`. Add:
```json
"defense_wins_false_concern_signals": [
  {
    "signal_id": "dw_001_s1",
    "signal_type": "surface_observation | narrative_framing | supporting_detail",
    "phrasing": "How this signal should appear in the memo — the fact or description that will look suspicious",
    "external_knowledge_for_exoneration": "The specific knowledge required to dismiss this concern"
  }
]
```

---

## Your Input

Generate blueprints for a batch of {{BATCH_SIZE}} cases. Previous batch usage (sources/domains already used — do not repeat):

```json
{{PREVIOUS_BATCH_USAGE}}
```

If no previous usage, use `{}`.
