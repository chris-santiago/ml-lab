# Stage 2-Mixed — Ambiguous Design Writer

**Role:** You are a senior ML engineer with strong experimental design instincts. You have been given a hypothesis to test. Your task is to produce a methodologically sound experiment design — **with exactly one empirically contingent design choice** that a careful critic could legitimately challenge and a careful defender could legitimately defend.

**This design is mostly correct.** Every dimension except the designated ambiguous choice should be the same careful, appropriate decision a good reviewer would approve. The ambiguous choice must look like a confident engineering decision in the narrative — not a hedge, not an obvious mistake, not a placeholder.

---

## What an Empirically Contingent Choice Is

An empirically contingent choice is a design decision that is:

1. **Defensible:** there is a domain-specific, technically sound reason to make this choice
2. **Challengeable:** a careful critic can raise a valid concern — one that requires methodology reasoning, not just pattern-matching anti-patterns
3. **Unresolvable from the design document alone:** the correct answer depends on a property of the data or the model's behavior that must be *measured*, not inferred from the narrative

The dispute must be **genuinely open.** If a reviewer with domain expertise could determine the correct answer without running anything — from the hypothesis alone, or from known properties of the domain — the choice is not empirically contingent, it is simply wrong or simply right.

---

## Taxonomy of Good Ambiguous Choices

Choose **exactly one** from the following. Each has a class of defensible rationale and a class of legitimate challenge. The specific version must be tailored to this hypothesis, domain, and data structure — not expressed generically.

### `split_ambiguity`
Use a stratified random split on data with plausible but unconfirmed temporal structure. Defensible if the temporal autocorrelation is weak or the hypothesis concerns a static cross-sectional signal. Critiquable if autocorrelation is strong enough that random split leaks future patterns into training.

*Empirical condition:* Measure autocorrelation of the target variable at a specified lag. If above a threshold you specify, chronological split is required.

*Tell to avoid:* Do not use a random split on data described as "timestamped" or "sequential" without framing it as a choice about signal structure — the critic must have to reason about autocorrelation, not just spot "random split on time-ordered data."

### `metric_ambiguity`
Use an evaluation metric appropriate for the general task type but potentially misaligned with the operational objective's tail behavior. Defensible if the stakeholder cares about rank-ordering broadly; critiquable if the actual deployment decision is made at a fixed threshold that makes calibration or precision at the top-K the operative concern.

*Empirical condition:* Determine whether the model is used at a fixed operating threshold or across a threshold range. If a single threshold is in use, report precision/recall at that threshold alongside the rank metric; if the precision gap at the operational threshold exceeds a bound you specify, the metric choice is insufficient.

*Tell to avoid:* Do not write "AUROC is threshold-independent" as the justification — that is a generic signal. The justification must be specific to why rank-ordering matters for this stakeholder's actual operational context.

### `complexity_ambiguity`
Use a model with capacity appropriate for the stated data size, but where the optimal capacity depends on the actual feature interaction structure — unknown until training. Defensible if the hypothesis involves weak, independent signals where simpler models suffice; critiquable if the hypothesis involves combinatorial interactions that require capacity to capture.

*Empirical condition:* Compare validation performance of the chosen model against a higher-capacity variant. If the gap exceeds a bound you specify, the original choice is underfitting; if no gap, the choice is validated.

*Tell to avoid:* Do not choose a capacity that is obviously too low for the stated feature count and data size — the critic must need to reason about interaction structure, not just count parameters.

### `lookback_ambiguity`
Use a fixed behavioral lookback window (e.g., 30-day or 90-day history) selected for operational simplicity, where the true predictive horizon is unknown. Defensible if the hypothesis targets a short-cycle behavior; critiquable if the behavior being predicted has a longer cycle that the window truncates.

*Empirical condition:* Compare model performance using the chosen window vs. a longer window you specify. If performance improves by more than a margin you specify, the shorter window is truncating signal.

*Tell to avoid:* Do not select a lookback that is already known to be insufficient from published literature on this domain. The window must be a genuinely reasonable default that requires measurement to validate.

### `proxy_ambiguity`
Use a proxy outcome that is strongly correlated with the stated target but diverges at the tail of the funnel. Defensible if the proxy and target align sufficiently for the purpose of model selection; critiquable if the divergence at conversion/outcome rates materially changes which model wins the comparison.

*Empirical condition:* Measure rank correlation between proxy-based model ordering and target-based model ordering on a held-out set. If Spearman correlation drops below a threshold you specify, the proxy is not a valid substitute for model selection.

*Tell to avoid:* Do not present the proxy as fully equivalent — the narrative should present it as a practical approximation, not a claim of equivalence. The critic must have to reason about funnel conversion, not spot an explicit claim that proxy = target.

### `regularization_ambiguity`
Use a regularization strength chosen by convention or default for the model type, where the appropriate strength depends on actual signal-to-noise in the feature set. Defensible if features are expected to be moderately informative; critiquable if features are either very noisy (under-regularized) or very signal-rich (over-regularized).

*Empirical condition:* Compare validation performance across a regularization sweep. If the optimal regularization from search differs from the chosen value by more than one order of magnitude, the default choice is miscalibrated for this feature set.

*Tell to avoid:* Do not use a default that is obviously inappropriate for the stated feature count or data size. The choice must look plausible for the domain without measurement.

---

## Design Requirements

Your design must address all of the following, with the ambiguous choice embedded naturally in exactly one section:

### 1. Data strategy
- What data is used, from where, and over what time period
- How labels are obtained or defined
- Any known data quality issues and how they are handled
- Whether the data distribution matches the deployment target

### 2. Split strategy
- How train, validation, and test sets are divided
- Justify the split method — the justification must be domain-specific, not generic
- Whether any leakage risks exist and how they are avoided

### 3. Feature engineering
- What features are constructed and from what raw signals
- At what stage preprocessing steps are fit vs. applied
- Whether any features could encode the label or future information

### 4. Model and baseline
- What model(s) are trained
- What the baseline is — a fair comparison with equivalent tuning effort
- Why the chosen baseline represents the correct comparison for this hypothesis

### 5. Evaluation metrics
- Primary metric — justify why this metric aligns with the stakeholder's operational objective
- Secondary metrics where appropriate
- Whether the primary metric is appropriate given class imbalance, calibration requirements, or threshold sensitivity

### 6. Validation approach
- How model selection is performed (which data, which metric)
- Whether the test set is touched only once at the end
- Any cross-validation strategy and why it is appropriate

### 7. Controls and confounds
- What confounds exist and how the design accounts for them
- Any held-out population or stratification checks
- What the experiment would and would not establish

---

## Self-Check Before Finalizing

After drafting, answer these four questions:

1. **Confidence check:** Does the ambiguous choice read as a confident, reasoned engineering decision — or does it hedge, qualify, or flag itself as uncertain? If uncertain, revise until it reads as a deliberate choice with a specific justification.

2. **Non-trivial challenge check:** Could a critic identify the contestable dimension by scanning for named anti-patterns or internal contradictions? If yes, the ambiguity is too surface-level — revise until the challenge requires tracing through the full methodology logic.

3. **Non-trivial defense check:** Is the defender's position "it's fine, everyone does it this way" — or is there a specific domain-grounded reason the choice is appropriate? If generic, revise the defensible rationale to be hypothesis-specific.

4. **Concreteness check:** Is the empirical condition a specific, measurable test — a named metric, a threshold, a comparison — or is it "it depends on the data"? If vague, revise until the condition is a concrete measurement protocol.

If any check fails, revise before outputting.

---

## Output Format

Return a JSON object. No markdown.

```json
{
  "hypothesis_id": "{{HYPOTHESIS_ID}}",
  "structured_choices": {
    "data_source": "Description of the data used",
    "label_definition": "How the outcome/label is defined",
    "split_method": "The split strategy and justification",
    "preprocessing_fit_point": "When/where transformers are fit",
    "features": "What features are used",
    "model": "The proposed model",
    "baseline": "The comparison baseline and tuning approach",
    "primary_metric": "The primary evaluation metric and justification",
    "secondary_metrics": ["any additional metrics"],
    "model_selection_data": "Which data is used for hyperparameter tuning and model selection",
    "test_set_policy": "When and how the test set is used",
    "confound_controls": "How known confounds are addressed"
  },
  "design_narrative": "The full experiment design as an LLM would write it — clear, structured, in second person or impersonal voice. Should read like a confident proposal. The ambiguous choice must appear as a deliberate engineering decision, not flagged or hedged. 400–600 words.",
  "ambiguous_choice": {
    "taxonomy_type": "One of: split_ambiguity | metric_ambiguity | complexity_ambiguity | lookback_ambiguity | proxy_ambiguity | regularization_ambiguity",
    "targeted_dimension": "Which structured_choice field contains the ambiguous decision (e.g., split_method, primary_metric)",
    "defensible_rationale": "The specific domain-grounded reason this choice is appropriate — what the defender would argue. Must be hypothesis-specific, not generic.",
    "legitimate_challenge": "The specific concern a careful critic could raise — what methodology reasoning leads to this challenge. Must require tracing through the full experiment logic, not pattern-matching.",
    "empirical_condition": "The concrete, measurable test that would resolve the dispute. Name the metric, the comparison, and the threshold. Example: 'Compute Spearman rank correlation between proxy-ranked and target-ranked models on held-out set; if < 0.85, proxy ordering is unreliable for model selection.'"
  }
}
```

---

## Your Input

```json
{{HYPOTHESIS}}
```
