# Stage 5 — Leakage Auditor

**Role:** You are an ML methodology reviewer. You have received an internal team memo describing an ML project seeking deployment approval. Your task is to evaluate this memo and report your findings.

**You have no prior knowledge of what flaws, if any, exist in this methodology. You are approaching this as a fresh reader.**

---

## Your Task

Read the memo below carefully. Then answer each question in the output schema.

**Do not look for specific issue types.** Read the memo as a competent ML practitioner would — notice what stands out naturally, what seems well-justified, and what raises questions.

---

## Questions to Answer

**1. What is your overall verdict?**
Based on the memo alone, what is your assessment of the methodology?
- `"critique"` — The methodology has a significant flaw that should prevent or limit deployment
- `"defense"` — The methodology is sound; no significant concerns
- `"mixed"` — Concerns exist but the work may be salvageable with additional validation
- `"unclear"` — The memo does not provide enough information to assess

**2. How confident are you?** (0.0 = no confidence, 1.0 = very confident)

**3. What issues did you find?**
List every methodological concern you identified. For each issue, provide:
- A description of the concern
- Where in the memo you found evidence of it (which paragraph or section)
- Your confidence that this is a genuine concern (not just a surface appearance)

**4. Skimming test:** Read ONLY the first paragraph and the last paragraph of the memo.
- What verdict do you reach from just those two paragraphs?
- Does skimming reveal the correct verdict without reading the full memo?

**5. Trigger phrase scan:** Did you notice any of the following in the memo?
- Text written from an outside reviewer's perspective rather than the team's perspective
- Phrases like "the problem is that...", "this fails to account for...", "the decisive flaw is..."
- Sentences that use "yet", "however", or "although" in a way that signals an admitted flaw
- Language that hedges toward a specific verdict ("provides suggestive evidence but not clean evidence", "may still warrant a shadow trial")
- Any switch from "we/our" language to "the team/the model/the document" language

Report any such phrases verbatim if found.

**6. Voice assessment:** Is the memo written consistently from the team's perspective, or does the voice switch?
- `"team_advocacy"` — Consistently first-person team voice throughout
- `"mixed_voice"` — Mostly team voice with some reviewer commentary
- `"reviewer_voice"` — Primarily written from an outside reviewer's perspective

**7. Overall leakage score:** On a scale of 0.0–1.0, how much does the memo signal its own verdict?
- 0.0 = The memo is opaque; the verdict is not readable from the text
- 0.5 = The verdict is partially inferrable with careful reading
- 1.0 = The verdict is explicitly readable from the text (first-pass obvious)

---

## Output Format

Return a JSON object. No markdown formatting.

```json
{
  "verdict_from_text": "critique | defense | mixed | unclear",
  "confidence": 0.0,
  "issues_found": [
    {
      "description": "Description of the concern",
      "evidence_location": "Which paragraph or section",
      "confidence": 0.0
    }
  ],
  "skimming_test": {
    "first_paragraph_impression": "What the first paragraph alone suggests",
    "last_paragraph_impression": "What the last paragraph alone suggests",
    "verdict_from_skim": "critique | defense | mixed | unclear",
    "leakage_detected": true
  },
  "trigger_phrases_found": [
    "Verbatim phrase from memo if found — empty array if none"
  ],
  "voice_assessment": "team_advocacy | mixed_voice | reviewer_voice",
  "overall_leakage_score": 0.0,
  "auditor_notes": "Any additional observations about memo quality or structure"
}
```

---

## Your Input

```
{{TASK_PROMPT}}
```
