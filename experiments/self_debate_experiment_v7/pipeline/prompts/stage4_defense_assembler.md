# Stage 4D — Defense Ground Truth Assembler

**Role:** You are a benchmark case designer. You have been given a hypothesis and a sound experiment design with no planted flaws. Your task is to assemble the structured ground truth metadata for a **defense case** — a benchmark case where the correct outcome is that a reviewer approves the design or raises only concerns the defender can legitimately rebut.

Defense cases test whether critique/defense agents can correctly exonerate valid methodology. A model that always flags flaws will fail these cases. The ground truth captures: what the design looks like to an evaluator, which concerns are legitimate rebuttals (not flaws), and what a correct verdict looks like.

> **Scope:** This assembler handles **defense cases only** (`category='defense'`).
> Regular cases (with planted flaws) use `stage4_ground_truth_assembler.md`.
> Mixed cases use `stage3_mixed_assembler.md`.

---

## Your Task

Produce a complete benchmark case record by combining:
1. The hypothesis and domain from Stage 1
2. The sound design from Stage 2 as the `task_prompt` (what debate agents see)
3. A list of `must_not_claim` entries — legitimate design choices a pattern-matching reviewer might question without domain reasoning

---

## Ground Truth Rules

### `correct_verdict`
Always `"defense_wins"` — the design is sound. A correct outcome is that the reviewer either approves the design outright or raises only concerns the defender can legitimately rebut using the design rationale.

### `planted_issues`
Empty array `[]` — no planted flaws. Do not invent or imply any methodology problems.

### `must_find_issue_ids`
Empty array `[]` — there is nothing the critic must find, because there are no real flaws.

### `must_not_claim`
This is the most important field for defense cases. List **3-5 legitimate design choices** a pattern-matching evaluator might incorrectly flag as problems. These are choices that look questionable on the surface but are actually correct for this domain and hypothesis. Include for each:
- The specific concern a naive critic might raise
- A clear explanation of why it is NOT a flaw

Examples of what to include:
- A temporal split that appears "unbalanced" but is correct for the data structure
- A metric that looks unusual but is appropriate for the operational context
- A preprocessing step that looks like leakage but is actually domain-correct
- A model choice that looks unnecessarily complex but is justified by the hypothesis
- A baseline that looks weak but represents the correct production comparison

### `acceptable_resolutions`
Always `["defense_wins"]`. A correct debate outcome is that the design is approved — either the critic raises no significant concerns, or the defender successfully rebuts all concerns raised.

---

## Output Format

Return a JSON object. Do not include markdown fences.

```json
{
  "case_id": "{{CASE_ID}}",
  "hypothesis": "{{HYPOTHESIS_STATEMENT}}",
  "domain": "{{DOMAIN}}",
  "ml_task_type": "{{ML_TASK_TYPE}}",
  "task_prompt": "Present the design narrative as a proposed ML experiment for review. Write it in second person ('You are reviewing a proposed study...') so the evaluating agent sees it as a critique request. Include all key design choices from the sound design: data source, split strategy, features, model, metric, baseline, and evaluation protocol. Do not hint that this is a defense case or that the design is sound. 3-5 paragraphs.",
  "correct_verdict": "defense_wins",
  "num_corruptions": 0,
  "planted_issues": [],
  "must_find_issue_ids": [],
  "must_not_claim": [
    {
      "claim": "A specific concern a pattern-matching evaluator might raise — e.g., 'The 80/10/10 split is imbalanced for time-series data'",
      "why_wrong": "Why this concern does not apply — the design choice is correct for this domain and hypothesis. Be specific: cite the hypothesis, data structure, or operational context."
    },
    {
      "claim": "A second surface-level concern",
      "why_wrong": "Domain-specific rebuttal"
    },
    {
      "claim": "A third surface-level concern",
      "why_wrong": "Domain-specific rebuttal"
    }
  ],
  "acceptable_resolutions": ["defense_wins"],
  "sound_design_reference": "{{DESIGN_NARRATIVE}}",
  "difficulty_justification": "1-2 sentences: what makes this defense case non-trivial — what surface features might trick a pattern-matching critic into raising a false alarm."
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
