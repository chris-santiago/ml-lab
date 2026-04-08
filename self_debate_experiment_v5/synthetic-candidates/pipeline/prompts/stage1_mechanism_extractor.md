# Stage 1 — Mechanism Extractor

**Role:** You are a case design architect. Your task is to produce **one** mechanism blueprint for a single assigned source. This blueprint will be used by downstream stages to generate an advocacy memo and scoring metadata for an ML methodology benchmark case. You do NOT write the memo — you produce a structured blueprint that other stages will use.

**Important:** The flaw mechanism must be extracted at the level of **abstract mechanism**, not domain-specific instance. Transpose the mechanism to the assigned target domain. Your descriptions must be abstract enough that they can be embedded in a methodology description without sounding like a problem statement.

---

## Your Assigned Source

{{SOURCE_REFERENCE}}

---

## Your Assignment

- **Mechanism ID:** `{{MECHANISM_ID}}`
- **Case type:** `{{CASE_TYPE}}`
- **Assigned case type** controls which output fields are required (see Output Format below).

**Domain transposition:** Choose a target domain that is plausibly different from any example domains listed in the source's "Transpose to" guidance. The domain must have operational texture — include a regulatory constraint, business context, or field-specific norm.

**Transposition depth requirement (critical):** The abstract mechanism must be embedded ≥2 layers deep in domain-specific context before it resembles a recognizable ML failure mode. Ask yourself: would a general ML practitioner recognize the flaw from the memo text without domain expertise? If yes, the transposition is too shallow.

The flaw should only be detectable by someone who knows one of:
- A regulatory or measurement standard specific to this domain (e.g., ICH E9(R1), CLSI EP09-A3, SR 11-7)
- A field-specific data collection convention that makes the implicit assumption wrong
- An operational constraint in this domain that creates the confound

**Avoid shallow transpositions:** Proxy variable bias in healthcare is equally obvious in any other clinical prediction context. A model comparison flaw in RecSys is equally obvious in any other ranking domain. Cross the mechanism into a domain where its surface form looks fundamentally different — the vocabulary, the regulatory context, and the operational stakes should all be unfamiliar enough that a general ML reviewer cannot pattern-match to the abstract mechanism.

---

## Flaw Fact Phrasing Requirement

For each critique/mixed case, you must produce flaw facts in **neutralized phrasing** — the flaw should be describable as a plain methodology step, not a problem statement.

For each flaw fact, produce:
1. **Neutralized phrasing:** How the methodology team would describe this step. No alarm language. Describe exactly **one** action or decision — do not encode the relationship between compound facts in the phrasing.
2. **Domain-specific context:** One sentence of domain texture (regulatory norm, operational constraint, or field convention) that makes the step plausible.

**Compound fact phrasing rule (critical):** For cases with `compound_fact_ids`, each compound fact must be phrased as a fully independent, standalone methodology step. The problematic relationship between them must NOT appear in either fact's phrasing — it only emerges when a reader connects both facts across paragraphs using domain-specific knowledge.

Prohibited in any compound fact's `neutralized_phrasing`:
- Temporal connectors: "before", "after", "following", "prior to", "subsequently"
- Causal connectors: "which was then used for", "applied to the set used for", "in order to"
- Any phrase that implies the sequence or dependency between the two facts

**Bad example (encodes the relationship):** "Synthetic minority oversampling was applied to the full labeled dataset before the k-fold cross-validation loop." — A reader sees the ordering problem in one sentence.

**Good example (relationship-free):**
- Fact 1: "Synthetic minority oversampling was applied to address class imbalance in the labeled training set."
- Fact 2: "Model selection used five-fold cross-validation across the full development dataset."

A reader must connect these across two paragraphs and know why that combination is problematic. Neither fact alone signals a concern.

---

## Hard Requirements — Validation Will Reject Blueprints That Miss These

For every **critique** or **mixed** case, these fields are mandatory and have minimum counts. Blueprints that fail are discarded and regenerated from scratch.

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
  "case_type": "critique | mixed | defense_wins",
  "ideal_resolution_type": "empirical_test_agreed | defense_wins",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "source_reference": "Source N — Name or Pattern X — Name",
  "abstract_mechanism": "One sentence at the level of abstract mechanism. For critique/mixed: the assumption violated, the omission, or the wrong justification — not domain-specific. For defense_wins: the sound practice being misread.",
  "flaw_type": "assumption_violation | critical_omission | wrong_justification | metric_mismatch | null",
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

Sources and domains already used in prior batches (do not repeat domains from this list):

```json
{{PREVIOUS_BATCH_USAGE}}
```
