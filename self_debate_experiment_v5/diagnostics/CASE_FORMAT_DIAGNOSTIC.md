# Case Format Diagnostic — Generator Compliance Failure

**Date:** 2026-04-07
**Discovered via:** Smoke test V4 (batch3) scoring analysis
**Severity:** Critical — invalidates both proxy gate and actual experiment
**Status:** Unresolved — awaiting generation prompt revision

---

## The Problem

All critique/mixed cases generated in batches 1xx, 2xx, and 3xx contain **evaluative analysis paragraphs embedded in the task_prompt**. These paragraphs explicitly identify the real flaws and signal the correct verdict. This destroys difficulty at every level:

- **Proxy gate:** Any model that reads "the practical launch decision may still warrant a shadow trial, but the memo has not yet established a clean methodological superiority claim" scores FVC=1 by echoing the text. No reasoning required.
- **Actual experiment:** The Critic reads the flaw diagnosis in the task_prompt and repeats it. The Defender reads the hedged conclusion and concedes appropriately. DRQ, ETD, and DC scores will be inflated for the same reason — the case text is doing the work the debate is supposed to do.

The scoring targets (must_find_issue_ids, must_not_claim, acceptable_resolutions) are correct. The JSON metadata is sound. The task_prompt is the broken component.

---

## What the Generator Was Supposed to Do

The generation prompt (Step 3) specifies:

> "Write a 500–800 word internal memo, evaluation report, or launch proposal."
> "Opens with a positive result or deployment recommendation — no problem statements."
> "The flaw is present as an assumption violation, critical omission, or wrong justification — NOT as an explicit statement of a problem."

The Quality Standard (line 606) specifies:

> "A senior ML engineer reads the task_prompt and says 'this looks fine' on first pass, then on second pass with specific probing identifies 'wait — there's a problem with [the mechanism].'"

---

## What the Generator Actually Did

Every batch3 task_prompt follows this four-paragraph structure:

1. **Memo paragraph 1–2:** Team's positive results and acknowledged concerns (correct)
2. **Memo paragraph 3:** Methods section revealing the flaw mechanism (partially correct — the flaw is present, but…)
3. **Analysis paragraph 4:** Outside-reviewer commentary explicitly naming the flaw and hedging toward the correct verdict

Paragraph 4 is the failure. Examples from batch3:

> *"That business argument is not enough for the stronger claim the memo makes... Because synthetic events were created before folding, some training rows can encode geometric neighborhoods derived from events that later sit in validation folds... The practical launch decision may still warrant a shadow trial, but the memo has not yet established a clean methodological superiority claim."* (case 301)

> *"The problem is that overlapping windows from the same crane and week are not independent records... When that leakage is combined with a tuned challenger and a frozen incumbent queue, the document provides suggestive evidence for a shadow pilot but not clean evidence..."* (case 302)

These are not memo paragraphs. They are written from the perspective of an outside reviewer who has already identified the problem. A real approval memo would never say "the problem is that..." — it would advocate for deployment.

---

## Which Self-Evaluation Tests Were Violated

The generation prompt includes nine self-evaluation tests that each case must pass before output. Batch3 cases violate at least two:

### Skimming Test (line 576)
> "Read only the first and last paragraphs. Can you determine the correct verdict? If YES — verdict leakage is present. Restructure so the conclusion is not front-loaded or back-loaded."

**Violation:** Every batch3 case has the correct verdict in the last paragraph. Reading the first and last paragraphs of case 302 immediately yields: "the model may outperform → but leakage means no clean superiority claim → shadow pilot warranted." That is `empirical_test_agreed`, fully readable from the skimming test.

### Quality Standard (line 606)
> "A senior ML engineer reads the task_prompt and says 'this looks fine' on first pass."

**Violation:** Paragraph 3 of every case explicitly names the flaw ("The problem is that overlapping windows...", "Because synthetic events were created before folding...", "That distinction matters because..."). No engineer reads this and says "looks fine."

The generator either did not run the self-evaluation tests, or ran them but did not recognize the violations.

---

## Why the Trigger Phrase Prohibition Failed

Step 3 of the generation prompt states:

> "Apply all v5 trigger phrase prohibitions: no contrast signals, no compensation language, no parallel before/after structure."

This prohibition is **referenced but not defined**. The document does not contain the phrase "v5 trigger phrase prohibitions" anywhere except this single reference. The generator has no list of forbidden constructions to check against.

The batch3 cases contain the exact pattern this prohibition was meant to prevent:

> *"A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..."*

This is simultaneously a contrast signal ("yet"), compensation language ("but this concern is actually"), and a pre-emptive must_not_claim defuser. The generator produced it in every case because the prohibition gave no concrete examples and no mechanism for recognition.

---

## Why This Matters for the Actual Experiment (Not Just the Gate)

The smoke test uses a proxy rubric. But the actual experiment scoring engine has the same vulnerability:

- **IDR inflation:** The task_prompt tells the Critic which issues are real. Finding must_find issues is trivial.
- **IDJ inflation:** The task_prompt names the wrong justification and explains why it is wrong. Challenging it requires no reasoning.
- **DRQ inflation:** The task_prompt already frames the case as "needs empirical test." The debate's resolution quality score rewards reaching `empirical_test_agreed`, but the task_prompt is already pointing there. The debate is not driving the resolution — the case text is.
- **ETD inflation:** When the task_prompt specifies the exact shadow trial needed ("a post-redesign forward test"), the ETD score for proposing that test cannot be attributed to debate quality.

The experiment measures lift from debate vs. non-debate baseline. If both conditions benefit equally from task_prompt answer-leakage, the lift signal is attenuated — not because debate doesn't work, but because the baseline is already too well-informed.

---

## Root Cause Classification

| Cause | Verdict |
|-------|---------|
| Generator ignoring the Skimming Test | **Yes** — test exists, generator did not catch the violation |
| Generator ignoring the Quality Standard | **Yes** — standard exists, generator produced the opposite |
| Instructions insufficient (trigger phrases not defined) | **Yes** — prohibition referenced but undefined |
| Fundamental case design problem | **No** — the scoring target JSON (must_find, must_not_claim, abi) is correct; only task_prompt format is broken |

This is primarily a **generator compliance failure** against existing instructions, with a secondary **under-specification** of what forbidden constructions look like concretely.

---

## What a Correct task_prompt Looks Like

A correct task_prompt is written entirely from the perspective of the team seeking approval. It:
- Opens with results and a deployment recommendation
- Addresses concerns the team anticipates will be raised (the `must_not_claim` items) and explains why each is manageable — **without flagging the real flaws**
- Embeds the real flaws in methodology facts without labeling them as flaws
- Ends with the team's own conclusion (e.g., "we recommend approval for a phased rollout") — not an outside-reviewer assessment of whether the evidence is sufficient

A reviewer reading a correct task_prompt on first pass would say "this looks reasonable." On second pass, they would notice the SMOTE was applied before folding, or the windows overlap, or the verification depends on the same risk rules as the model features. They would not have been told where to look.

---

## Corrective Action Applied (2026-04-07)

Rather than re-generating batch3 cases from scratch, the evaluative analysis paragraphs were surgically removed from the 9 critique/mixed task_prompts (eval_scenario_301–309) in `synthetic-candidates/real_paper_cases_batch3.json`. Defense_wins cases (310–314) were unchanged.

### What Was Removed

For each critique/mixed case, the final paragraph(s) that:
- Switched from first-person team voice to third-person reviewer voice
- Explicitly named the flaw mechanism ("the problem is that...", "that argument is not enough...", "the decisive flaw is...")
- Hedged toward the correct verdict ("provides suggestive evidence but not clean evidence", "the memo has not yet established a clean methodological superiority claim")
- Contained "A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..." constructions (entire sentence removed)

### What Was Preserved

All content written from the team's advocacy perspective: results, methodology description, stated justifications (including wrong ones), addressed concerns, and the team's deployment recommendation. Each task_prompt now ends with the team's own conclusion — not an outside-reviewer assessment.

### Per-Case Summary

| Case | Removed | Now ends with |
|------|---------|---------------|
| 301 | "That business argument is not enough... memo has not yet established clean methodological superiority" | Team: analysts care about queue improvement, not model class |
| 302 | "The problem is that overlapping windows... suggestive evidence but not clean evidence" | Team: "practical question is whether learned forecaster beats queue mechanics" |
| 303 | "That distinction matters... current benchmark does not validate the stronger faithfulness claim" | Team: "best explanation is the one whose feature removal most harms retrained performance" |
| 304 | "stronger routine deployment claim needs a prevalence- and spectrum-aware prospective test" | Team: "model validity should be established on cases with reliable ground truth first" |
| 305 | "Without a post-redesign forward test... deployment claim remains under-supported" | Team: "behavior-feature drift is harmless so long as model is retrained on mixed-era data" |
| 306 | "The decisive flaw is verification bias... AUROC may be optimistic" | Team: "label quality is higher and AUROC is therefore conservative" |
| 307 | "launch case should be reframed around fresh-set performance... old headline benchmark" | Team: "relative ranking between models is preserved" |
| 308 | "The deeper flaw is a scope mismatch between evidence about best seed and claims about workflow reliability" | Team: "deployment decisions should compare the strongest available artifact" |
| 309 | "current headline performance can only be trusted after screening-plus-fitting pipeline is nested in proper CV" | Team: "screening was label-aware but performed solely to remove noise before model fitting" |

### Status

`real_paper_cases_batch3.json` has been updated in place. All scoring metadata (must_find_issue_ids, must_not_claim, planted_issues, acceptable_resolutions, ground_truth) is unchanged — only task_prompt content was modified.

**Next step:** Run smoke test V5 on the corrected batch3 cases to verify that the evaluative paragraph removal creates calibration headroom (critique/mixed mean < 1.000, gate pass target ≥9/14 cases scoring mean < 0.55).

---

## Evidence Across All Smoke Test Runs

Critique/mixed ceiling has been 1.00 in every single run:

| Run | Cases | Critique/mixed mean |
|-----|-------|:---:|
| V1 (1xx, invented) | 101–114 | 1.000 |
| V2 (2xx, real-paper) | 201–214 | 1.000 |
| V3 (2xx re-run, IDJ) | 201–214 | 1.000 |
| V4 (3xx batch3, Lever A+B) | 301–314 | 1.000 |

This is not a Lever A or Lever B problem. It is a task_prompt format problem that has been present since the first generation round and was never fixed because Lever A and B targeted the scoring metadata rather than the case text.
