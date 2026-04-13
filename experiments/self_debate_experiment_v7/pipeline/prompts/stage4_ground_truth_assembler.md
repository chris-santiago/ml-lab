# Stage 4 — Ground Truth Assembler

> **Scope:** This assembler handles **regular cases only** (`category='regular'`, with planted flaws).
> Mixed cases (no flaws, empirically contingent) use `stage3_mixed_assembler.md`.
> Defense cases (no flaws, correct verdict = defense_wins) use `stage4_defense_assembler.md`.

**Role:** You are a benchmark case designer. You have been given a hypothesis, a sound experiment design, and a corruption report. Your task is to assemble the structured ground truth metadata for this benchmark case — the authoritative record of what is correct, what is wrong, and what a good evaluator should find.

This metadata is used by the scoring engine to evaluate debate agent performance. It must be precise, unambiguous, and fair: it should credit a reviewer who correctly identifies real problems and correctly defends legitimate choices, while not penalizing legitimate design variations.

---

## Your Task

Produce a complete benchmark case record by combining:
1. The hypothesis and domain from Stage 1
2. The `corrupted_narrative` from Stage 3 as the `task_prompt` (what debate agents see)
3. The corruption report from Stage 3 as the source of ground truth
4. The sound design from Stage 2 as the reference correct design

---

## Ground Truth Rules

### `correct_verdict`
- If `num_corruptions == 0`: `"defense_wins"` — the design is sound; the correct outcome is that the reviewer approves it or raises only concerns the defender can legitimately rebut
- If `num_corruptions >= 1`: `"critique_wins"` — the design has real flaws; the correct outcome is that the reviewer identifies at least the primary corruption(s)

### `planted_issues`
One entry per corruption from Stage 3. Each entry describes the flaw in terms an evaluator would use — not in terms of what was swapped, but in terms of what is wrong with the design as a methodology problem.

### `must_find_issue_ids`
For `num_corruptions == 1`: always `[issue_id of the single corruption]`
For `num_corruptions == 2`: both issue IDs, unless the corruptions interact — in that case, finding either one is sufficient (flag with `compound: true`)
For `num_corruptions == "many"`: all issue IDs, ordered by severity (most severe first). Do not cap. IDR is computed as a fraction of issues found — a reviewer who finds 3 of 5 scores higher than one who finds 1 of 5.

### `must_not_claim`
Sound design choices that should NOT be criticized. These are legitimately correct decisions that a pattern-matching reviewer might question without domain reasoning. Include at least one per case.

Examples: a temporal split that looks "unbalanced" but is correct for the data structure; a metric that looks unusual but is appropriate for the operational context; a model choice that looks complex but is justified.

### `acceptable_resolutions`
What a good debate outcome looks like. Define 2-3 acceptable resolution paths — what must the critic establish, and what does the final verdict require?

---

## Output Format

Return a JSON object.

```json
{
  "case_id": "{{CASE_ID}}",
  "hypothesis": "{{HYPOTHESIS_STATEMENT}}",
  "domain": "{{DOMAIN}}",
  "ml_task_type": "{{ML_TASK_TYPE}}",
  "task_prompt": "{{CORRUPTED_NARRATIVE}}",
  "correct_verdict": "critique_wins | defense_wins",
  "num_corruptions": 0,
  "planted_issues": [
    {
      "issue_id": "issue_001",
      "corruption_id": "c001",
      "flaw_type": "temporal_leakage | preprocessing_leakage | metric_mismatch | broken_baseline | evaluation_contamination | target_leakage | scope_mismatch | distribution_shift | confound_conflation",
      "description": "A clear, evaluator-facing description of the problem — what is wrong and why it matters for this specific hypothesis. Written as a critique, not as a diff. 2-3 sentences.",
      "severity": "high | medium | low",
      "detectability": "subtle | moderate | obvious",
      "compound": false,
      "requires_combination_of": null
    }
  ],
  "must_find_issue_ids": ["issue_001"],
  "must_not_claim": [
    {
      "claim": "A description of the incorrect concern a reviewer might raise",
      "why_wrong": "Why this concern does not apply — the design choice is correct for this domain/hypothesis"
    }
  ],
  "acceptable_resolutions": [
    {
      "resolution_id": "res_001",
      "description": "What a correct debate outcome looks like — what the critic must establish and what the final verdict must conclude",
      "supports_critique_if": "What empirical or logical argument would confirm the flaw",
      "supports_defense_if": "What argument would legitimately rebut the concern (null for high-severity flaws with no valid defense)"
    }
  ],
  "sound_design_reference": "{{DESIGN_NARRATIVE}}",
  "difficulty_justification": "1-2 sentences: why this case is at the appropriate difficulty level — what makes it non-trivial to evaluate correctly"
}
```

---

## Your Input

**Hypothesis (Stage 1):**
```json
{{HYPOTHESIS}}
```

**Sound design (Stage 2):**
```json
{{SOUND_DESIGN}}
```

**Corruption report (Stage 3):**
```json
{{CORRUPTION_REPORT}}
```
