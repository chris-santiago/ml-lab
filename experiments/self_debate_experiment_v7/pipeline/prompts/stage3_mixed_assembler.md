# Stage 3-Mixed — Ground Truth Assembler (Mixed Cases)

**Role:** You are a benchmark case designer. You have been given a hypothesis and an
experiment design that contains exactly one empirically contingent design choice. Your
task is to assemble the structured ground truth metadata for this mixed-position benchmark
case — the authoritative record of what is contested, what an empirical test could resolve,
and what a well-formed debate outcome looks like.

This case has no planted flaws. The design is methodologically sound except that one
decision cannot be validated without measurement. The correct debate outcome is not a
verdict — it is a well-specified empirical test that would resolve the dispute.

---

## Your Task

Produce a complete case record by combining:
1. The hypothesis and domain from Stage 1
2. The `design_narrative` from Stage 2-mixed as the `task_prompt` (what debate agents see)
3. The `ambiguous_choice` block from Stage 2-mixed as the source of the ETD fields
4. The `structured_choices` from Stage 2-mixed to identify `must_not_claim` items

---

## Ground Truth Rules

### `correct_position`
Always `"mixed"` for cases assembled by this stage.

### `ideal_debate_resolution`
Translate the `ambiguous_choice.empirical_condition` into the canonical ETD schema:

- **`type`:** always `"mixed"`
- **`condition`:** The specific empirical test that could resolve the dispute. This must be
  a concrete measurement protocol — not a general claim about what matters. It must name:
  (a) what to measure, (b) on what data or model outputs, (c) the threshold or comparison
  that determines the outcome. Do not write "it depends on the data." Write the test.
- **`supports_critique_if`:** What empirical result would confirm the critic's concern —
  the measurement outcome that validates the challenge. Must reference the same threshold
  named in `condition`.
- **`supports_defense_if`:** What empirical result would vindicate the design choice —
  the measurement outcome that validates the defense. Must be the logical complement of
  `supports_critique_if`.
- **`ambiguous_if`:** An edge condition where neither position is clearly correct — a
  measurement outcome that falls in the contested middle. May be null if no such middle
  zone exists.

**Concreteness standard:** A reviewer reading only `condition` must know exactly what to
compute. "Compute Spearman rank correlation between proxy-ranked and target-ranked models
on the held-out test set" is concrete. "Determine whether the proxy is correlated with
the target" is not.

### `required_empirical_test`
A copy of the `ideal_debate_resolution` fields (condition / supports_critique_if /
supports_defense_if / ambiguous_if), placed inside `ground_truth` for human reference.
This field is informational — it is not used by the scoring engine directly.

### `planted_issues`
Always `[]` — no corruptions were introduced.

### `must_find_issue_ids`
Always `[]` — there are no must-find issues.

### `must_not_claim`
Sound design choices that should NOT be criticized. For mixed cases, these are dimensions
of the design other than the ambiguous choice that a pattern-matching reviewer might
challenge without domain reasoning.

Identify 2–3 must-not-claim items by examining `structured_choices`. Look for:
- Choices that look unusual but are justified for this domain or hypothesis
- Choices that differ from a common default but have a stated domain-specific rationale
- Choices that a reviewer who lacks domain context might flag as "risky" without
  understanding why they are appropriate

Do NOT include the ambiguous dimension itself in must-not-claim — it is legitimately
contestable.

Format each entry with a short `claim_id`, a one-sentence `claim` (the incorrect concern
a reviewer might raise), and a `why_wrong` explanation (why this concern does not apply).

### `acceptable_resolutions`
For mixed cases: `["empirical_test_agreed"]`

Only `empirical_test_agreed` is a passing FVC verdict. Baseline and ensemble conditions will
commit to `critique_wins` or `defense_wins` (FVC 0.0–0.5) — the FVC gap between those
conditions and debate conditions is the H1b signal. Including all four verdicts collapses
H1b by making `compute_fvc()` return 1.0 for every condition.

**DRQ ceiling for mixed cases (intentional design choice):** No agent produces a literal
`"mixed"` verdict, so `ideal_debate_resolution.type = "mixed"` means DRQ tops at 0.5 for
mixed cases. FVC and ETD are co-primary for mixed cases; DRQ is secondary. Do not add
`"mixed"` to agent verdict options to "fix" this ceiling.

### `difficulty`
Assign `"medium"` or `"hard"` based on:

- **`medium`:** The ambiguous dimension is identifiable from the design narrative with
  careful methodology reasoning — a reviewer who traces through the experiment logic
  can locate it without deep domain expertise.
- **`hard`:** The ambiguous dimension requires both deep domain expertise and multi-step
  methodology reasoning to identify. A reviewer who does not know the domain would likely
  miss it or mislabel it as a flaw (critique_wins) rather than a contestable choice.

---

## Output Format

Return a JSON object. No markdown.

```json
{
  "case_id": "{{CASE_ID}}",
  "hypothesis": "{{HYPOTHESIS_STATEMENT}}",
  "domain": "{{DOMAIN}}",
  "ml_task_type": "{{ML_TASK_TYPE}}",
  "category": "mixed",
  "difficulty": "medium | hard",
  "task_prompt": "{{DESIGN_NARRATIVE from Stage 2-mixed}}",
  "ground_truth": {
    "correct_position": "mixed",
    "final_verdict": "Empirically contested — the design choice at issue cannot be validated without measurement",
    "required_empirical_test": {
      "condition": "The specific, concrete empirical test — name the metric, the data, the threshold",
      "supports_critique_if": "What result confirms the concern",
      "supports_defense_if": "What result vindicates the choice",
      "ambiguous_if": "Edge condition, or null if none"
    }
  },
  "ideal_debate_resolution": {
    "type": "mixed",
    "condition": "The specific, concrete empirical test — same as required_empirical_test.condition",
    "supports_critique_if": "What result confirms the concern — same as required_empirical_test.supports_critique_if",
    "supports_defense_if": "What result vindicates the choice — same as required_empirical_test.supports_defense_if",
    "ambiguous_if": "Edge condition, or null — same as required_empirical_test.ambiguous_if"
  },
  "planted_issues": [],
  "must_find_issue_ids": [],
  "scoring_targets": {
    "must_find_issue_ids": [],
    "must_not_claim": ["claim_001", "claim_002"],
    "must_not_claim_details": [
      {
        "claim_id": "claim_001",
        "claim": "One-sentence description of the incorrect concern a reviewer might raise",
        "why_wrong": "Why this concern does not apply — the design choice is correct or justified for this domain and hypothesis"
      }
    ],
    "acceptable_resolutions": ["empirical_test_agreed"],
    "resolution_descriptions": {
      "empirical_test_agreed": "Passing verdict — debate recognized the ambiguity and specified an empirical test to resolve it"
    }
  },
  "sound_design_reference": "{{DESIGN_NARRATIVE from Stage 2-mixed — identical to task_prompt for mixed cases}}",
  "difficulty_justification": "1-2 sentences: why this ambiguous choice is at the assigned difficulty level — what reasoning path is required to locate and engage it"
}
```

---

## Self-Check Before Finalizing

1. **Concreteness of `condition`:** Could a reviewer execute this test from the description
   alone — knowing exactly what to compute, on what, and how to interpret the result?
   If not, rewrite until the answer is yes.

2. **Logical complement check:** Do `supports_critique_if` and `supports_defense_if`
   partition the outcome space? If both could be true simultaneously, or if the threshold
   is the same in both, the ETD is malformed.

3. **Must-not-claim relevance:** Are the must-not-claim items genuinely sound choices that
   require domain reasoning to defend — not obvious defaults that anyone would accept?
   If they are generic, replace them with choices specific to this design.

4. **Ambiguous choice not in must-not-claim:** Verify that the ambiguous dimension from
   Stage 2-mixed's `ambiguous_choice.targeted_dimension` does NOT appear in
   `must_not_claim`. It must remain openly contestable.

---

## Your Input

**Hypothesis (Stage 1):**
```json
{{HYPOTHESIS}}
```

**Ambiguous design (Stage 2-mixed):**
```json
{{AMBIGUOUS_DESIGN}}
```
