# Stage 3 — Corruption Node

**Role:** You are an expert ML practitioner who deeply understands how experiment designs fail in practice. You have been given a methodologically sound **proposed** experiment design. Your task is to corrupt exactly **{{NUM_CORRUPTIONS}}** design choices, replacing each with a plausible-but-wrong alternative.

**If {{NUM_CORRUPTIONS}} is 0:** Return the design unchanged. The ground truth is that this design is sound. Do not introduce any corruptions.

---

## The Detection Bar

The evaluator reviewing your corrupted design is a capable language model with strong pattern-matching ability. It will immediately catch:

- Anti-pattern names in plain sight ("random split", "full dataset normalization", "accuracy on imbalanced classes", "test set used for tuning")
- Internal contradictions — e.g., one section says model selection uses metric A, another section evaluates on metric B
- Unusually thin or generic justifications for a specific technical choice in an otherwise well-reasoned proposal
- Retrospective language in what should be a proposal ("we found that...", "results showed...")

**Your corruptions must get past this bar.** A corruption that can be identified by keyword recognition or by scanning for logical inconsistency within the document is not subtle enough.

---

## Requirements

1. **Look like natural LLM output** — the corrupted choice must be the kind of design decision a capable model would write if it reasoned correctly about most things but missed one specific implication. Not obviously wrong. Plausible on first read.

2. **Require end-to-end methodology reasoning to detect** — the flaw must only become visible when a reviewer traces through the full experiment logic: what data structure is being used, what the operational objective is, what happens at serving time, or how the evaluation pipeline interacts with the training pipeline. Pattern-matching on the corrupted text alone must not be sufficient.

3. **Carry a domain-specific justification** — every corrupted choice must include a technical-sounding rationale that sounds like a deliberate engineering decision. The justification should be specific to this domain and hypothesis, not generic. Avoid phrases like "widely used", "commonly applied", or "threshold-independent" — these are signals of a generic default, not a considered choice.

4. **Maintain internal consistency** — after inserting a corruption, check that no other section of the narrative still refers to the correct version of that choice. If the sound design's model selection section and evaluation section both referenced the same metric, and you corrupt the evaluation metric, you must also update any cross-references so the document does not contradict itself.

5. **Preserve the prospective voice** — the experiment design is a **proposal**, not a completed study. The corrupted_narrative must maintain present or future tense throughout ("the model will be trained on...", "validation uses...", "splits are defined by..."). Do not introduce retrospective phrasing around corrupted sections.

6. **Target a single design choice per corruption** — each corruption replaces exactly one decision. Do not conflate multiple errors into one corruption entry.

---

## Flaw Taxonomy

Choose corruptions from this taxonomy. For each corruption, the flaw type must be one of the following.

### `temporal_leakage`
Replace a chronological or group-based split with a stratified random split on time-ordered or group-structured data, framed as a principled choice to preserve class distribution.

*Hard version:* "Partitioning will use stratified random sampling across all available weeks, holding out a random 15% of observations as the test set. Stratification ensures that the positive class rate is consistent across train, validation, and test — critical given the 3:1 class ratio variation across seasons." The flaw (random split on temporal data) is buried under a justification that sounds like rigorous attention to class balance.

*Tell to avoid:* Do not write "randomly split" without framing. Do not write anything that implies ignoring time ordering. The corrupted text should frame the random split as solving a different, legitimate problem.

### `preprocessing_leakage`
Fit a preprocessing transformer on the full dataset before splitting, framed as a choice that produces more stable parameter estimates.

*Hard version:* "To avoid instability in normalization parameters caused by small held-out set sizes, all continuous features are standardized using statistics computed from the combined dataset prior to model training. The scaler parameters are then frozen and applied uniformly during training, validation, and test evaluation." The flaw (fit on full data before split) is framed as a stability argument.

*Tell to avoid:* Do not write "across the full dataset" as a bare phrase. Do not make the fit-before-split explicit — embed it in language about parameter stability or consistency.

### `metric_mismatch`
Use an evaluation metric that does not align with the operational objective or data structure, with a justification that sounds like a considered tradeoff rather than a mistake.

*Hard version (ranking context):* "The primary evaluation metric is per-item AUROC computed over the impressed candidate pool, aggregated across sessions. This formulation supports stratified analysis by product category and session length, which the hypothesis requires — enabling us to determine where the proposed model's gains are concentrated rather than relying on a single aggregate number." The flaw (wrong metric for a ranking objective) is hidden behind an analytic justification that sounds useful.

*Tell to avoid:* Do not use generic justifications like "threshold-independent" or "widely comparable." Do not use a metric that immediately reads as obviously wrong for the domain. The metric must sound like it was chosen for a specific analytical reason.

### `broken_baseline`
Use a baseline that is not given equivalent treatment, framed as a deliberate choice to establish a lightweight reference point.

*Hard version:* "The baseline is a logistic regression model fit with default regularization strength (C=1.0), providing a well-calibrated linear reference without the confound of extensive hyperparameter search. Tuning the baseline would risk overfitting the comparison to a specific validation window and would obscure whether improvements come from architecture or from optimization." The flaw (untuned baseline) is framed as avoiding a different methodological problem.

*Tell to avoid:* Do not write "default hyperparameters" without a justification. Do not make the untuned baseline sound like an oversight — it must sound like a principled choice.

### `evaluation_contamination`
Use the test set during model development, framed as a final validation step or a held-out calibration check that happens to influence a model decision.

*Hard version:* "After validation-based hyperparameter selection, a final check is run on the test set to verify that the selected configuration maintains its advantage before committing to full training on the combined train+validation set. This guards against validation-window overfitting and ensures the final model is not tuned to an unrepresentative period." The flaw (test set peeked before final evaluation) sounds like a defensive quality check.

*Tell to avoid:* Do not write "test set used for tuning" or any phrase that directly names the contamination. The test set usage must sound like a legitimate verification step.

### `target_leakage`
Include a feature that directly or indirectly encodes the label, presented as a naturally available operational signal.

*Hard version:* "In addition to pre-event behavioral features, the model incorporates a real-time activity score updated daily, which aggregates account interactions from the prior 24 hours. This feature is already computed in the production pipeline and requires no additional infrastructure to serve." The flaw (the score may incorporate post-label-window events depending on the label definition) requires tracing through the timing carefully to detect.

*Tell to avoid:* Do not describe the feature in terms that directly signal its relationship to the label. Do not use phrasing like "following the event" or "after the outcome."

### `scope_mismatch`
Test a proxy outcome that diverges from the stated hypothesis in a material way, framed as a practical approximation that preserves hypothesis validity.

*Hard version:* "Because direct purchase conversion events are sparse in the evaluation window, the experiment uses add-to-cart rate as the primary outcome — a high-frequency signal that is strongly correlated with purchase intent and allows more precise statistical estimation." The flaw (proxy divergence at the tail of the funnel) is framed as a sound statistical tradeoff.

*Tell to avoid:* Do not acknowledge the divergence between proxy and target directly. The proxy must be presented as effectively equivalent.

### `distribution_shift`
Train on a biased subpopulation without acknowledging or controlling for the resulting generalization gap.

*Hard version:* "Training data is drawn from accounts with at least 90 days of activity history, as this segment has the richest behavioral features and lowest label noise. A stratified holdout from the same population is used for evaluation." The flaw (deployment will include newer accounts) requires knowing the deployment scope to detect.

*Tell to avoid:* Do not name the deployment target explicitly and then contrast it with the training population. The distribution restriction must sound like a data quality decision.

### `confound_conflation`
Attribute an improvement to the proposed mechanism when a concurrent change confounds the comparison.

*Hard version:* "Both models are evaluated on the same two-month post-launch window, during which the production serving infrastructure was migrated to the new feature store. Both models were retrained on data generated under the new infrastructure, ensuring a consistent training environment." The flaw (the feature store migration is a confound) requires knowing that the two models may have been trained under different infrastructure versions to detect.

*Tell to avoid:* Do not name the confound directly. Do not write anything that highlights the timing coincidence.

---

## Selection Rules

1. **Prefer choices where the correct version is non-obvious** — corrupting an obscure secondary metric is less interesting than corrupting the split strategy or the primary evaluation metric
2. **For {{NUM_CORRUPTIONS}} = 2:** The two corruptions may be independent or may interact. If they interact, note this in `compound_note`. Do not corrupt the same design dimension twice.
3. **For {{NUM_CORRUPTIONS}} = "many":** Select 3–5 corruptions from at least 3 different flaw types. At least one should be more detectable (calibration anchor) and at least two should be genuinely subtle.
4. **Never corrupt the hypothesis statement** — only corrupt design choices.

---

## Self-Check Before Finalizing

After drafting your corrupted_narrative, do the following:

1. Re-read the narrative as if you are a competent reviewer seeing it for the first time.
2. Ask: "Can I identify the corrupted choice by scanning for keyword signals or named anti-patterns, without tracing through the full methodology?" If yes — revise until the answer is no.
3. Ask: "Does any section of the document contradict another in a way that would alert a reviewer?" If yes — resolve the contradiction.
4. Ask: "Does the corrupted text sound prospective — like a proposed design — or does it introduce retrospective language?" If retrospective — revise to proposal voice.

---

## Output Format

```json
{
  "hypothesis_id": "{{HYPOTHESIS_ID}}",
  "num_corruptions": {{NUM_CORRUPTIONS}},
  "corruptions": [
    {
      "corruption_id": "c001",
      "flaw_type": "one of the flaw taxonomy types above",
      "targeted_choice": "Which structured_choice field this corruption targets (e.g., split_method, primary_metric, baseline)",
      "original_text": "The exact text from the sound design that is being replaced",
      "corrupted_text": "The replacement text — plausible, domain-justified, sounds like a deliberate engineering decision, is wrong",
      "why_wrong": "1-2 sentences: why this corrupted choice is methodologically incorrect for this specific hypothesis and data structure",
      "detectability": "subtle | moderate | obvious",
      "compound_note": "If this corruption only reveals a problem in combination with another corruption, describe the interaction. Otherwise null."
    }
  ],
  "corrupted_narrative": "The full design_narrative from Stage 2 with corrupted choices substituted in. Must be self-consistent — no section may contradict another. Rewrite surrounding sentences as needed so the corrupted version reads naturally and does not call attention to itself. Must maintain the prospective proposal voice of Stage 2. Same length and structure as the original. The reader should not be able to locate the substitutions by scanning."
}
```

---

## Your Input

**Sound design from Stage 2:**
```json
{{SOUND_DESIGN}}
```
