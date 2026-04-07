# Case Revision Brief — Hard Case Strengthening

**Prepared for:** External LLM (non-Anthropic)
**Purpose:** The 10 hard cases listed below passed a single-pass baseline evaluation with perfect scores (IDR=1.0, IDP=1.0, FVC=1.0, mean=1.0 on all 10). The difficulty gate requires ≤ 4 of 10 hard cases to exceed a baseline mean of 0.55. The cases need to be revised so that a competent but non-expert single-pass assessor plausibly misses at least one must_find issue or reaches an incorrect verdict on most cases.

**Cases to revise:** All 10 cases in `hard_cases_for_revision.json` (full JSON attached).

---

## What "Hard" Means in This Benchmark

Difficulty is defined by expected rubric performance on a **single-pass baseline** (no debate structure, no role framing):

- **Hard:** A single-pass assessor is expected to **fail on at least 2 rubric dimensions** (IDR, IDP, DRQ, ETD, FVC). This means: miss ≥ 1 must_find issue, OR assert a must_not_claim item, OR reach the wrong verdict — on most hard cases, at least one of these should occur.

A case is not hard merely because the flaw is subtle when explained. It must be **genuinely non-obvious during first-pass review** — the scenario must present plausible surface-level evidence that the evaluation is sound, so that a first-pass reviewer is tempted to accept it.

---

## Why the Cases Failed the Gate

Every case had its planted flaws **directly stated or easily inferred** from the task_prompt. A competent reader scanning for evaluation problems found all must_find issues without needing to reason across multiple signals simultaneously. Specific failure modes:

1. **Flaws were named explicitly** — several cases stated the problematic change in plain language (e.g., "the endpoint definition changed," "the split was done at the encounter level"). Hard cases should describe the change without labeling it as a flaw.

2. **No competing narrative** — the task_prompts read as "here are the problems, what do you think?" rather than "here is a strong case for this model change, scrutinize it." Hard cases should present a coherent, internally consistent story that sounds defensible, with the flaw hidden inside the details.

3. **Must_not_claim items were too specific** — red herrings were listed as explicit prohibitions but weren't actually present as tempting claims in the task_prompt. A red herring only works if the scenario makes it look like a plausible concern.

4. **Verdict was obvious** — for "mixed" cases, the task_prompt did not present a credible defense of the model change. A first-pass reviewer should be genuinely uncertain whether to critique or defend.

---

## Revision Requirements Per Case

For each case, revise the `task_prompt` and optionally the `planted_issues`, `scoring_targets`, and `ground_truth` fields to:

### 1. Bury the flaws inside a plausible success narrative

Rewrite the task_prompt so it reads as a **confident internal memo or evaluation report recommending the model change**. The flaw should be present in the details but not labeled or highlighted. The reader should encounter the problematic detail while reading a document that overall sounds sound.

Example: instead of "the cohort construction pipeline also changed," write a memo section describing the new cohort construction process as a platform improvement that was rolled out alongside the model, with specific numbers that sound reasonable, so the reader must actively notice that this was never ablated.

### 2. Add at least one strong competing narrative for mixed cases

For `correct_position == "mixed"` cases: add genuine positive evidence that makes the defense plausible. The best mixed cases make the reader think "this is concerning BUT the team has reasonable mitigations." The must_find flaw should make the reader uncertain, not certain.

### 3. Strengthen the must_not_claim red herrings

Add 1-2 additional `must_not_claim` items that are **genuinely tempting** — things that look like problems on the surface but are actually fine. These should appear naturally in the task_prompt as features a reviewer might question. The current must_not_claim items are often not present at all in the task_prompt.

Example red herrings that work:
- A feature that sounds like target leakage but has a clear temporal boundary
- A small held-out set size that is actually fine for the evaluation goal
- A metric that sounds wrong for the domain but is standard practice
- A third-party dataset that sounds unvalidated but has a known lineage

### 4. Require multi-step reasoning for IDR

The must_find issues should not be identifiable from a single sentence. A hard case's flaw should require the reader to:
- Notice a detail in one paragraph
- Connect it to a constraint stated in a different paragraph
- Conclude that the combination creates a validity problem

This is the key mechanism for IDR difficulty: the flaw is in the **relationship between two details**, not in either detail alone.

### 5. Do not change case_id, category, or correct_position

Keep the same case_id, category, difficulty ("hard"), and correct_position. You may revise acceptable_resolutions if the rewrite changes what counts as a valid resolution, but the overall type of flaw and the rough domain should stay the same.

---

## Output Format

Return a JSON array with the same schema as the input cases. For each revised case, also add a `revision_notes` field (string) explaining what was changed and why the revised version is harder.

Schema reference (from existing cases):
```json
{
  "case_id": "eval_scenario_NNN",
  "category": "...",
  "difficulty": "hard",
  "task_prompt": "...",
  "ground_truth": {
    "correct_position": "...",
    "final_verdict": "...",
    "required_empirical_test": "..."
  },
  "planted_issues": [
    {
      "issue_id": "...",
      "description": "...",
      "severity": "...",
      "category": "..."
    }
  ],
  "scoring_targets": {
    "must_find_issue_ids": ["..."],
    "must_not_claim": ["..."],
    "acceptable_resolutions": ["..."]
  },
  "verifier_status": "verified",
  "verifier_notes": "...",
  "revision_notes": "..."
}
```

---

## Acceptance Criteria

A revised hard case passes if a competent single-pass reviewer (without domain expertise in the specific field) would plausibly:
- Miss ≥ 1 must_find issue (IDR < 1.0), OR
- Assert ≥ 1 must_not_claim item (IDP < 1.0), OR
- Reach a verdict not in acceptable_resolutions (FVC < 1.0)

...resulting in a case mean below 0.55 for that reviewer.

The goal is that **≥ 6 of the 10 revised cases** produce a baseline mean < 0.55 for a single-pass reviewer.

---

## Input File

`hard_cases_for_revision.json` — 10 full case objects in the current benchmark schema.
