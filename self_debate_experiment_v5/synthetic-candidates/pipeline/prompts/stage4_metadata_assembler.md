# Stage 4 — Metadata Assembler

**Role:** You are an answer-key constructor. You have been given: (1) a mechanism blueprint identifying the flaw in an ML methodology, (2) a metadata view of the methodology facts with their role codes, and (3) the completed memo that a separate agent wrote without knowing which facts are flaws.

Your task is to construct the complete scoring metadata for this case — the answer key that will be used by debate agents and the scoring engine.

You did NOT write the memo. Read it carefully to verify which flaw facts were included, how they were presented, and whether the addressed-but-incorrectly justification appears naturally in the text.

---

## Case Schema

Produce a complete case JSON object matching this schema:

```json
{
  "case_id": "eval_scenario_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "difficulty": "hard",
  "task_prompt": "[COPY THE MEMO VERBATIM FROM THE INPUT — DO NOT MODIFY IT]",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct conclusion in plain English.",
    "required_empirical_test": "For empirical_test_agreed cases: describe the exact experiment that would resolve the uncertainty. For defense_wins cases: null."
  },
  "planted_issues": [
    {
      "issue_id": "opaque_snake_case_id",
      "description": "What this issue is and why it matters. For defense_wins: one entry per false-concern signal.",
      "severity": "low | medium | high",
      "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification",
      "addressed_but_incorrectly": true,
      "compound": false,
      "requires_combination_of": null,
      "requires_external_knowledge": "The specific domain knowledge needed to identify this as a genuine flaw (critique) or false concern (defense_wins). Be specific — name a standard, convention, or literature result."
    }
  ],
  "ideal_critique": [
    "What a well-calibrated critique should identify — one item per must_find issue plus any additional observations."
  ],
  "ideal_defense": [
    "For defense_wins cases: one rebuttal per false-concern signal. For critique cases: what a well-calibrated defense should concede or contest."
  ],
  "ideal_debate_resolution": {
    "type": "empirical_test_agreed | defense_wins",
    "supports_critique_if": "Specific, falsifiable result pattern that would confirm the critique position.",
    "supports_defense_if": "Specific, falsifiable result pattern that would confirm the defense position.",
    "ambiguous_if": "Specific, falsifiable result pattern where the outcome remains genuinely uncertain."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["list of issue_ids that must be found for IDR=1"],
    "must_not_claim": [
      "Plain-English description of a concern that should NOT be raised as a primary critique — corresponds to decoy facts"
    ],
    "acceptable_resolutions": ["empirical_test_agreed"]
  },
  "suspicious_but_valid_features": "For defense_wins only: plain-English list of features that look problematic but are justified. Minimum 2 entries. For critique cases: null.",
  "ground_truth_rationale": "2-3 sentences explaining the correct verdict. Answer key only — never shown to agents.",
  "difficulty_justification": "Which specific aspects make this case hard. Which rubric dimensions (IDR, IDP, IDJ, FVC) should fail and why. For defense_wins: which false-concern signals will trip pattern-matching models.",
  "source_paper": "Author (year), Venue — or Defense Pattern letter — from the mechanism blueprint. Operator provenance only.",
  "verifier_status": "pending",
  "notes": "Self-evaluation test results (see checklist below)"
}
```

---

## Metadata Assembly Rules

### must_find_issue_ids
- Include every `flaw_fact` from the metadata view whose text was included in the memo
- If a flaw fact was NOT included by the memo writer, do NOT include its issue_id in must_find — flag it instead in the `notes` field as `"MISSING_FLAW_FACT: [fact_id]"` for recycling review
- For defense_wins cases: `must_find_issue_ids: []`

### must_not_claim
- One entry per `decoy_fact` from the metadata view
- Write as a plain-English concern the model should NOT raise (e.g., "The use of AUROC on imbalanced classes overstates performance")
- Do NOT write it as "the model should not say X" — write the concern itself
- For `domain_specific_false_alarm` decoys, add "(requires field-specific knowledge to dismiss)" in parentheses

### addressed_but_incorrectly
- Mark exactly the flaw fact specified in the mechanism blueprint as `"addressed_but_incorrectly": true`
- Find where the memo writer presented the team's justification for this fact — quote the relevant sentence in the `description` field
- Verify the justification is subtly wrong (plausible but incorrect). If it is clearly correct or clearly wrong, flag for recycling in `notes`

### compound issues
- Mark `"compound": true` on the flaw fact(s) specified in the mechanism blueprint
- Fill `"requires_combination_of"` with the two fact_ids and explain the cross-reference
- Verify the two facts appear in different paragraphs in the memo

### acceptable_resolutions
- All critique/mixed cases: `["empirical_test_agreed"]` only — no `critique_wins`
- Defense_wins cases: `["defense_wins"]`

### ideal_debate_resolution
- `supports_critique_if`: A specific empirical finding that would confirm the critique (e.g., "Shadow pilot at three new sites shows X% drop in performance compared to internal validation")
- `supports_defense_if`: A specific empirical finding that would confirm the defense (e.g., "Performance is stable across sites with different operational contexts")
- `ambiguous_if`: A pattern where neither side is clearly confirmed

---

## Self-Evaluation Checklist

Run all 9 tests. Record results in `notes` as `"Test N: PASS/FAIL"`. Any 2+ failures → flag for recycling.

1. **Internal Consistency:** Can all must_find issues be found by checking for factual contradictions in the memo? (Should be NO for critique cases)
2. **Checklist:** Does the case category's standard checklist mechanically find the flaw? (Should be NO)
3. **Skimming:** Does reading only first + last paragraphs reveal the correct verdict? (Should be NO)
4. **Justification:** Does the addressed_but_incorrectly justification read as competent? Is the error non-obvious? (Should be YES to both)
5. **Run-to-Run Variation:** Would two single-pass evaluators at temperature > 0 produce different findings? (Should be YES)
6. **Source Recognition:** Can a reader who knows the source paper identify it from the task_prompt? (Should be NO)
7. **Domain Expert False Positive (defense_wins only):** Would a competent ML practitioner raise the false concern on first pass? (YES) And could they dismiss it with relevant domain knowledge? (YES)
8. **Decoy Prominence (critique only):** Is the must_not_claim concern present in the first 2 paragraphs with explicit supporting detail? (Should be YES)
9. **Addressed-But-Incorrectly (critique only):** Does the task_prompt contain a stated justification for at least one must_find issue that is subtly wrong? (Should be YES)

---

## Recycling Flags

If any of the following conditions are found, set `"verifier_status": "recycle"` and describe the issue in `notes`:

- Any flaw fact from the metadata view is absent from the memo (MISSING_FLAW_FACT)
- The addressed-but-incorrectly justification is clearly correct (not subtly wrong)
- The addressed-but-incorrectly justification is absent from the memo
- Compound facts appear in the same paragraph
- 2+ self-evaluation tests fail
- Leakage auditor (Stage 5) found `overall_leakage_score > 0.4`

Otherwise: `"verifier_status": "pending"` (pending Phase 1 human review).

---

## Your Input

**Mechanism blueprint (full — including abstract_mechanism, flaw_type, source_reference):**

```json
{{MECHANISM_BLUEPRINT}}
```

**Metadata view (with role codes):**

```json
{{METADATA_VIEW}}
```

**Leakage audit result (from Stage 5):**

```json
{{LEAKAGE_AUDIT}}
```

**The completed memo (task_prompt):**

```
{{TASK_PROMPT}}
```

**Case ID to assign:**

```
{{CASE_ID}}
```
