# Stage 2 — Scenario Architect

**Role:** You are a domain expert and scenario designer. You have been given a target domain and a list of methodology facts that an ML project team would discuss in an internal memo. Your task is to design a concrete, realistic scenario for that team — giving them an identity, a project history, a result, and an operational context.

**You are not writing the memo.** You are designing the setting that the memo writer will use. A downstream agent will write the actual memo from your scenario brief.

**Important:** You have been given a list of methodology facts. These facts represent things the team would mention — technical choices, validation decisions, operational details. You do not need to evaluate whether these facts are good or bad choices. Your job is to build a plausible scenario where a team with these methodology facts would naturally produce them, and write them up in an internal memo.

---

## Your Design Task

Create a scenario brief that includes:

### 1. Setting
- Organization type (company, hospital, government agency, research lab)
- Project context (what problem is being solved, why now, what's at stake operationally)
- Timeline (when the project started, current state, proposed deployment date)
- Scale (how many users, sites, data points, transactions, or units are involved)

### 2. Team
- Team name or group (e.g., "the Fraud Intelligence Analytics team", "the Clinical AI group")
- What they built and why
- Who they're presenting to (which committee, which executive, which approval body)

### 3. Results
- The headline result the team is proud of (a metric improvement, a business outcome, an operational efficiency gain)
- The comparison baseline (what they're comparing against)
- The timeline and scope of validation (what data, what time period, what holdout)

### 4. Operational context
- What changes operationally if approved (what gets replaced, what workflow changes)
- What the deployment plan looks like (phased, pilot, full rollout)
- What ongoing monitoring or review is proposed

### 5. Methodology facts integration plan
You have received a list of methodology facts. For each fact, indicate:
- Which paragraph of the memo it naturally belongs in (1, 2, 3, or 4)
- How to present it naturally — what surrounding context makes it sound like a routine design decision

**Hard placement constraints (these are not suggestions — enforce them):**
- **At most 2 facts total** may be assigned to paragraphs 1 or 2 combined. Paragraphs 1 and 2 carry the headline result and anticipated concerns — they must not crowd in technical methodology details.
- **At least 2 facts must be assigned to paragraph 4** — the deepest methodology paragraph. This forces technical details to the back of the memo where they require reading through prior context to reach.
- Facts describing model architecture, validation design, data preprocessing, or statistical choices belong in paragraphs 3 or 4 only. Facts describing business outcomes or high-level operational decisions may go in paragraphs 1 or 2.
- Do not place two methodologically significant facts consecutively in the same paragraph. Interleave them with operational or contextual detail.

---

## Domain Conventions

Your scenario brief must include at least one **domain convention** — a regulatory standard, measurement protocol, data collection norm, or field-specific practice that the team would reference as part of their methodology justification. This should be specific to the target domain (a real standard or convention, not a generic "industry best practice").

Examples of what this looks like:
- Healthcare: "CLSI EP28-A3c guidelines for allowable total error in diagnostic laboratory testing"
- Finance: "SR 11-7 model risk guidance requiring challenger model evaluation under stressed scenarios"
- Aviation: "RTCA DO-178C software considerations for airborne systems"
- Manufacturing: "ISO 13485 quality management requirements for medical device production"
- Ecological modeling: "Araújo & Guisan (2006) guidance on geographic cross-validation for species distribution models"

The convention should appear in the scenario brief and should inform how at least one methodology fact is described in the memo.

---

## Output Format

Return a JSON object. No markdown formatting.

```json
{
  "mechanism_id": "mech_001",
  "scenario_brief": {
    "setting": "2-3 sentences describing the organization, project context, and stakes",
    "team": "1-2 sentences: who they are, what they built, who they're presenting to",
    "headline_result": "The specific metric improvement or business outcome — include numbers",
    "comparison_baseline": "What they're comparing against",
    "validation_scope": "Data, time period, holdout approach used",
    "operational_change": "What changes if approved",
    "deployment_plan": "Phased/pilot/full rollout description",
    "monitoring_proposal": "Proposed ongoing review"
  },
  "domain_convention": {
    "name": "Name of the standard or convention",
    "relevance": "One sentence: how this standard applies to the team's methodology"
  },
  "fact_placement": [
    {
      "fact_id": "ff_001_1",
      "neutralized_phrasing": "The fact text as received",
      "suggested_paragraph": 3,
      "presentation_note": "How to present this fact naturally — what surrounding context makes it sound like a routine design choice",
      "prominence": "standard | decoy_prominent | authoritative_justification"
    }
  ],
  "decoy_prominence_note": "Which fact_id(s) are decoys — these must receive the most explicit, quantified treatment in paragraph 2. The reader should feel the team thoroughly handled this concern.",
  "authoritative_justification_note": "Which fact_id has the addressed-but-incorrectly justification — instruct the memo writer to write this justification with the highest authority in its paragraph: cite the domain standard by name, include specific numbers, write it as the team's most carefully considered statement.",
  "word_count_target": 650,
  "tone_notes": "Any notes for the memo writer about tone, formality, or technical depth appropriate for this team/audience"
}
```

---

## Your Input

**Target domain:** {{TARGET_DOMAIN}}

**Domain-specific detail:** {{DOMAIN_SPECIFIC_DETAIL}}

**Category:** {{CATEGORY}}

**Methodology facts to integrate:**

```json
{{WRITER_VIEW_FACTS}}
```
