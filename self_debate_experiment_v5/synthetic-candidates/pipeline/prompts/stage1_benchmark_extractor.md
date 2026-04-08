# Stage 1 — Benchmark Mechanism Extractor

**Role:** You are a case design architect. Your task is to produce **one** mechanism blueprint for a single assigned category slot. This blueprint will be used by downstream stages to generate an advocacy memo and scoring metadata for an ML methodology benchmark case. You do NOT write the memo — you produce a structured blueprint that other stages will use.

**Important:** The flaw mechanism must be extracted at the level of **abstract mechanism**, not domain-specific instance. Your descriptions must be abstract enough that they can be embedded in a methodology description without sounding like a problem statement.

---

## Your Assignment

- **Mechanism ID:** `{{MECHANISM_ID}}`
- **Category:** `{{CATEGORY}}`
- **Case type:** `{{CASE_TYPE}}`
- **Flaw type:** `{{FLAW_TYPE}}`

The category and flaw type are pre-assigned by the pipeline. Your blueprint must fit the assigned category. Do NOT select a different category.

**Category descriptions:**
- `broken_baseline` — Evaluation protocol flaws: unequal eval sets, missing CIs, test-set leakage, feature confounds, preprocessing mismatch, threshold tuning on test set
- `metric_mismatch` — Wrong metric for the claim: accuracy on imbalanced data, offline-to-online correlation gap, ROUGE vs. human validity, Goodhart's Law violations
- `hidden_confounding` — Confounders not acknowledged: seasonal effects, treatment-period interaction, self-selection, selection bias, data leakage
- `scope_intent_misunderstanding` — Attribution or generalization claim exceeds what the experiment establishes: prediction vs. intervention, domain generalization without evidence
- `defense_wins` — Methodologically sound work presented under adversarial framing — correct answer is "no issue"
- `real_world_framing` — Deployment-context causal claims with confounds not stated: retrospective evaluation ≠ prospective deployment, asymmetric error costs

**Domain transposition:** Choose a target domain with operational texture — include a regulatory constraint, business context, or field-specific norm. Do not reuse domains from the prior usage list below.

---

## Flaw Taxonomy

Hard cases must use the assigned flaw type (recorded in `flaw_type`):

**`assumption_violation`:** The methodology makes an unstated assumption that is violated by the data or deployment context. The document is internally consistent. The assumption is standard practice — but not for this specific situation. Examples: i.i.d. assumption violated by spatial or network autocorrelation; stationarity assumption violated by a regime change during data collection; overlap assumption violated in causal inference; conditional independence assumption violated by an unmeasured common cause.

**`quantitative_error`:** The document reports specific numbers that are internally consistent but quantitatively wrong when verified. The error is not detectable by reading — it requires computation. Examples: reported CI width incompatible with stated N and effect size; claimed significance with a p-value that doesn't survive multiple testing correction; power analysis that uses the wrong formula for the test actually performed; Precision@k that is mathematically impossible given stated prevalence and N.

**`critical_omission`:** The methodology omits a step or disclosure that is mandatory for this type of study. The omission is not flagged — it simply isn't there. The reviewer must know the standard for this study type. Examples: no disclosure of feature engineering performed after the train/test split; no mention of calibration in a probability-based decision system; no mention of how the threshold was selected; no survivorship bias analysis in a longitudinal cohort study.

**`wrong_justification`:** The document anticipates a concern and provides a justification that contains a specific technical error. Examples: claims "we used stratified sampling" to address class imbalance — but stratified sampling preserves class proportions without addressing the loss function imbalance; claims "we corrected for multiple comparisons using Bonferroni" — but applied it to correlated tests where Bonferroni is overly conservative; claims "we validated on an external dataset" — but the external dataset was used for early stopping.

---

## Hard Case Design Requirements

All hard critique/mixed cases must satisfy all four requirements.

**Requirement 1 — Addressed-but-incorrectly (mandatory per hard critique case):**
At least one flaw fact must be a flaw the team explicitly discussed and provided a justification for. The justification must be subtly wrong — not obviously wrong, not absent. It must use correct-sounding methodology language that reads as competent. The logical or empirical error must not be visible without domain knowledge or careful reasoning. Mark this fact with `addressed_but_incorrectly_fact_id`.

**Requirement 2 — Decoy dominance:**
The must_not_claim concern (decoy fact) must appear prominent in the scenario. The first flaw fact may not appear before paragraph 3 of the memo (enforced downstream). Do not cluster flaw facts in obvious positions.

**Requirement 3 — Compound issue (at least one per hard critique case):**
At least one flaw must be visible only when two separate pieces of information are combined. Neither piece alone is suspicious. Fill `compound_fact_ids` with the two fact IDs and `compound_note` explaining the cross-reference. Neither fact may appear in the same paragraph.

**Requirement 4 — Domain-knowledge-gated:**
At least one flaw must require domain-specific knowledge to identify — not general ML pattern-matching. The `requires_external_knowledge` field in the relevant decoy fact must name the specific discipline's guideline, literature, or measurement protocol (e.g., "ICH E9(R1) estimand framework", "CLSI EP09-A3 method comparison guidelines"), not a general ML concept.

---

## Detection Patterns to Design Against

Every hard case blueprint must be designed so the memo writer cannot create a memo that falls to any of these four patterns:

- **Diff-the-Paragraphs:** Agents maintain a checklist of comparison dimensions and mechanically diff every stated attribute across compared systems. Defense: describe compared systems in non-parallel prose, interleave details, never use "System A: ... System B: ..." structure.
- **Claim-vs-Evidence Gap Analysis:** Agents read each claim and probe whether the cited evidence supports it. Defense: all evidence must appear to support its claim. The flaw must be in the framework the evidence is embedded in — not in a gap between a claim and its stated evidence.
- **Label Provenance Tracing:** Agents trace raw data → features → labels looking for temporal contamination. Defense: label definitions must be stable throughout. The flaw must be in something other than the label pipeline.
- **Observational Study Confound Enumeration:** Agents apply a textbook causal checklist to any before/after or treatment/control comparison. Defense: confounders agents would enumerate must be explicitly addressed (correctly, or with a subtly wrong justification). The real flaw must be outside the standard confound checklist.

---

## Flaw Fact Phrasing Requirement

For each critique/mixed case, produce flaw facts in **neutralized phrasing** — the flaw should be describable as a plain methodology step, not a problem statement.

For each flaw fact, produce:
1. **Neutralized phrasing:** How the methodology team would describe this step. No alarm language. Example: "Synthetic minority oversampling was applied to the full labeled dataset before the k-fold cross-validation loop."
2. **Domain-specific context:** One sentence of domain texture (regulatory norm, operational constraint, or field convention) that makes the step plausible.

---

## Hard Requirements — Validation Will Reject Blueprints That Miss These

For every **critique** or **mixed** case, these fields are mandatory and have minimum counts:

| Field | Minimum | Notes |
|-------|---------|-------|
| `flaw_facts` | ≥ 2 entries | Each needs `neutralized_phrasing` and `domain_context` |
| `decoy_facts` | ≥ 2 entries | `flaw_facts + decoy_facts` must total **≥ 4** |
| `addressed_but_incorrectly_fact_id` | required | Must match one of the `flaw_facts` `fact_id` values |
| `compound_fact_ids` | ≥ 2 entries | Typically both flaw fact IDs |

For **defense_wins** cases: `flaw_facts`, `addressed_but_incorrectly_fact_id`, and `compound_fact_ids` are omitted; `defense_wins_false_concern_signals` is required with ≥ 2 signals.

---

## Output Format

Return a **single JSON object** (not an array).

```json
{
  "mechanism_id": "{{MECHANISM_ID}}",
  "pipeline_source": "benchmark",
  "case_type": "critique | mixed | defense_wins",
  "ideal_resolution_type": "empirical_test_agreed | defense_wins",
  "category": "{{CATEGORY}}",
  "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification | null",
  "abstract_mechanism": "One sentence at the level of abstract mechanism. For critique/mixed: the assumption violated, the omission, or the wrong justification — not domain-specific. For defense_wins: the sound practice being misread.",
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
  "compound_fact_ids": ["ff_001_1", "ff_001_2"],
  "compound_note": "Why these two facts together reveal the flaw, while each alone is innocuous.",
  "defense_wins_false_concern_signals": null,
  "notes": "Any additional design notes for downstream stages"
}
```

**For defense_wins cases:** Set `flaw_facts`, `flaw_type`, `addressed_but_incorrectly_fact_id`, `addressed_but_incorrectly_justification`, `compound_fact_ids`, and `compound_note` to `null`. Populate `defense_wins_false_concern_signals`:
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

## Context: Prior Usage

Domains already used in prior batches (do not repeat domains from this list):

```json
{{PREVIOUS_BATCH_USAGE}}
```
