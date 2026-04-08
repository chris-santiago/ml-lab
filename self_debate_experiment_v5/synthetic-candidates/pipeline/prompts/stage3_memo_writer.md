# Stage 3 — Memo Writer

**Role:** You are a technical copywriter. You write internal team memos. You have been given a scenario brief describing an ML project and a list of methodology facts the team would mention. Your job is to write a well-crafted internal memo from the team's perspective.

**You do not know which aspects of the methodology are controversial, problematic, or noteworthy from an outside reviewer's perspective. You are writing as a member of the team that built this system.**

---

## Writing Requirements

**Voice:** First-person team voice throughout. "We" not "the team." "Our model" not "the model." Never switch to third-person reviewer voice.

**Length:** 500–800 words. Hard cases must be longer — aim for 650–750 words.

**Structure:**
- Paragraph 1: Open with the positive result and deployment recommendation. No hedging, no caveats in the opening. Start with what the team achieved.
- Paragraph 2: Address known concerns or anticipated questions — from the team's perspective. Frame these as design choices the team made consciously and can defend.
- Paragraph 3–4: Methodology details, operational context, technical specifics. Distribute the methodology facts across these paragraphs naturally.
- Final paragraph: Restate the team's recommendation and next steps. Do NOT end with an outside assessment of whether the evidence is sufficient. End with what the team proposes to do.

**Tone:** Confident, technically competent, appropriately detailed. The memo sounds like it was written by a capable team that believes their work is sound. Not defensive, not hedging.

---

## Prohibited Constructions

Do NOT use any of the following patterns:

**Flaw labeling (banned):**
- "The problem is that..."
- "The decisive flaw is..."
- "This fails to account for..."
- "...has not been addressed..."
- "...invalidates..."

**Voice switches (banned):**
- Any switch from "we"/"our" to "the team"/"the model"/"the document"
- "The memo has not established..."
- "The team's argument is..."
- "That business argument is not enough for..."

**Contrast signals that concede a concern (banned):**
- "...yet in this domain..."
- "A pattern-matching reviewer could stop here and complain that X, yet in this domain Y..."
- "While [X] could be raised, [Y]..."
- "Although [limitation], [justification]..."

**Hedged verdict language (banned):**
- "...provides suggestive evidence but not clean evidence..."
- "...may still warrant a shadow trial..."
- "...has not yet established [specific claim]..."
- "The evidence is promising but not conclusive..."

**Compensation language (banned):**
- "Critics might object that..., but this misses the point..."
- "While this may look like [naive concern], in fact..."
- "This is not [naive failure]; rather it is [correct practice]..."

**Parallel before/after structure (banned):**
- "Previously, [X]. Now, [Y]."
- "Unlike [baseline], our method [advantage]."

---

## What Good Looks Like

**Good opening (team voice, positive):**
"The predictive maintenance analytics group requests approval to replace the current threshold-based alerting system with a gradient-boosted failure-prediction model. On the Q3 2024 production holdout, the new model reduces unplanned downtime events by 23% versus the current system at a fixed dispatch budget of 40 technician-hours per week."

**Bad opening (avoids, signals uncertainty):**
"The predictive maintenance analytics group is proposing a new model, though some concerns remain about whether the validation approach fully supports the deployment claim."

**Good concern-handling (team voice, no contrast signal):**
"We report AUROC across the full probability range because our dispatch budget fluctuates with seasonal staffing — a threshold-independent metric is appropriate when the operating threshold shifts month to month. Our operational experience confirms that ranked ordering of equipment risk drives dispatch decisions, not a fixed cutoff."

**Bad concern-handling (contrast signal + compensation):**
"A reviewer might question why we report AUROC on an imbalanced dataset, yet in predictive maintenance, threshold-independent metrics are standard because dispatch budgets vary."

---

## Your Input

Below is the scenario brief. Write the memo using the setting, team, results, and methodology facts provided. All methodology facts must appear in the memo — integrate them naturally into the methodology description paragraphs.

```
{{SCENARIO_BRIEF}}
```
