# V5 Trigger Phrase Prohibition List

These constructions are **banned** from all `task_prompt` text. They leak the answer by signaling that a flaw exists, naming it, or hedging toward the correct verdict from outside the team's perspective.

---

## Category 1 — Explicit Flaw Labeling

Do not name or describe a problem directly from a reviewer's perspective.

| Banned pattern | Why |
|---|---|
| `"The problem is that [mechanism]..."` | Names the flaw explicitly |
| `"The decisive flaw is [X]..."` | Names the flaw explicitly |
| `"A critical issue is [X]..."` | Names the flaw explicitly |
| `"This is problematic because [X]..."` | Names the flaw explicitly |
| `"[X] invalidates [Y]..."` | Names the flaw explicitly |
| `"...has not been addressed..."` | Signals omission |
| `"...fails to account for..."` | Signals omission |

**Correct alternative:** Embed the flaw as a methodology fact. Instead of "The problem is that SMOTE was applied before the train-test split," write: "The team applied synthetic minority oversampling to the full labeled dataset before dividing it into cross-validation folds." The fact is present; its significance is not labeled.

---

## Category 2 — Voice Switches (First-Person to Third-Person Reviewer)

The memo must be written entirely in team-advocacy voice. Any switch to an outside reviewer's perspective leaks the framing.

| Banned pattern | Why |
|---|---|
| `"The memo has not established..."` | Reviewer assessing the memo |
| `"The document provides..."` | Reviewer describing a document |
| `"The team's argument is..."` | Reviewer summarizing someone else |
| `"That business argument is not enough for..."` | Reviewer passing judgment |
| `"This provides suggestive evidence but not clean evidence..."` | Reviewer grading quality |
| `"The methodology description suggests..."` | Reviewer analyzing text |
| Any switch from "we" → "the team" | Voice shift |
| Any switch from "our model" → "the model" | Voice shift |

**Correct alternative:** Stay in "we" throughout. "We recommend approval for phased rollout." Not "The team recommends."

---

## Category 3 — Contrast Signals That Acknowledge a Flaw

Mid-sentence contrasts that implicitly concede the critique point before pivoting away.

| Banned pattern | Why |
|---|---|
| `"...yet in this domain..."` | Concedes the concern, then deflects |
| `"...however, the team argues..."` | Contrast = implied concession |
| `"...but this is addressed by..."` | Contrast = implied concession |
| `"While [concern] could be raised, [deflection]..."` | Concession + deflection pattern |
| `"Although [limitation], [justification]..."` | Signals limitation exists |
| `"A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..."` | **Most flagrant violation — banned entirely** |

**Correct alternative:** Address the concern from the team's perspective without acknowledging it as a concern. "We use AUROC because threshold-independent metrics are standard in domains where alert budgets vary with conditions." No "yet," no "although," no "a reviewer might."

---

## Category 4 — Hedged Verdict Language

Text that nudges the reader toward the correct verdict without stating it directly.

| Banned pattern | Why |
|---|---|
| `"...provides suggestive evidence but not clean evidence..."` | Maps directly to `empirical_test_agreed` |
| `"...may still warrant a shadow trial..."` | Maps directly to `empirical_test_agreed` |
| `"...a prospective test would confirm..."` | Maps directly to `empirical_test_agreed` |
| `"...the evidence is promising but not conclusive..."` | Maps directly to `empirical_test_agreed` |
| `"...warrants further validation before broader deployment..."` | Maps directly to `empirical_test_agreed` |
| `"...has not yet established [specific claim]..."` | Outside-reviewer assessment of sufficiency |

**Correct alternative:** End with the team's recommendation. "We recommend approval for initial deployment at three pilot sites with structured outcome tracking." This is what a team memo says — not a reviewer's assessment of whether the evidence is sufficient.

---

## Category 5 — Compensation Language (Must-Not-Claim Defusing)

Pre-emptively explaining why a must_not_claim concern doesn't apply. This prevents the evaluating model from making the false alarm but is visible as a tell.

| Banned pattern | Why |
|---|---|
| `"A pattern-matching reviewer could stop here..."` | Names the meta-concern |
| `"Critics might object that..., but this misses the point..."` | Compensation structure |
| `"While this may look like [naive concern], in fact..."` | Compensation structure |
| `"This is not [naive failure]; rather it is [correct practice]..."` | Compensation structure |

**Correct alternative:** The team defuses the must_not_claim concern in their voice, as if explaining their domain-appropriate choice. "We report AUROC because our alert budget varies seasonally with solar activity and staffing — a threshold-independent metric is the appropriate choice under variable deployment conditions." They are not addressing a critic. They are explaining their methodology.

---

## Category 6 — Parallel Before/After Structure

Side-by-side comparisons that frame old method vs. new method as implicitly bad vs. good.

| Banned pattern | Why |
|---|---|
| `"Previously, [X]. Now, [Y]."` | Implies old was worse |
| `"The old approach did [X]; the new approach does [Y]."` | Implies linear improvement |
| `"Unlike [baseline], our method [advantage]."` | Signals superiority framing |

**Correct alternative:** Describe the current approach on its merits. Mention the comparison target only in a results table or metric comparison, not as a narrative of improvement.

---

## Quick Reference — Banned Constructions

```
"The problem is that..."
"The decisive flaw is..."
"A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..."
"This provides suggestive evidence but not clean evidence..."
"The memo has not established..."
"That business argument is not enough for..."
"While [X], [Y]..."          ← when used to concede a concern
"Although [X], [Y]..."       ← when used to concede a concern
"...may still warrant a shadow trial..."
"...has not yet established..."
"Previously, [X]. Now, [Y]."
Any switch from "we" to "the team"
Any switch from "our model" to "the model"
```
