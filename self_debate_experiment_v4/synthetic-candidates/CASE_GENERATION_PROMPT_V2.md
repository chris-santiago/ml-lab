# Case Generation Prompt v2 — Hard Case Design Guide

**Purpose:** Generate benchmark cases that are genuinely hard for a capable LLM single-pass reviewer — not just for human domain experts. Cases generated with v1 prompts failed a Claude-family difficulty gate because flaws were directly named or strongly implied in the prompt text.

---

## What v1 Cases Got Wrong

v1 hard cases were "self-annotating": the flaw mechanism was stated in the same paragraph that introduced it (e.g., "the endpoint definition changed from X to Y"). A reviewer reading for evaluation problems found every flaw without needing to infer anything. The cases read as *descriptions of problems* rather than *plausible reports that happen to contain problems*.

**The test:** A hard case should read like a confident internal recommendation memo or evaluation report. Someone skimming it should think "this sounds solid." Only a careful, expert reviewer who actively probes each claim should find the flaw.

---

## Hard Case Design Principles

### 1. Never name the flaw mechanism

Do not write: "the endpoint definition changed."
Write instead: a memo section that describes the new model's target with natural-sounding clinical or business language, and separately describes the baseline's performance on a different metric in a different section — without flagging the discrepancy.

The reader must notice that Metric A (used for the new model) and Metric B (cited for the baseline) are different, and that this makes the comparison invalid. Neither A nor B is labeled as a problem.

### 2. Lead with strong positive evidence

Open with numbers that sound good. The comparison should be *apparently favorable*. Hard cases need a credible defense — a reviewer should spend at least a few sentences considering whether the positive evidence is sufficient before finding the flaw.

For mixed-position cases: the evidence should genuinely support both sides. The must_find flaw should make the reader uncertain, not certain.

### 3. Require cross-paragraph inference for every must_find issue

Each must_find flaw should only be discoverable by connecting two pieces of information in different parts of the prompt:
- Paragraph 2 states a data collection detail
- Paragraph 5 states a modeling assumption
- The flaw is that these are inconsistent

A reviewer who reads each paragraph in isolation misses it. Only a reviewer who tracks constraints across the full document finds it.

### 4. Plant active red herrings

Each case needs 1-2 features that look like problems but are actually fine. These must appear as natural-sounding details — not labeled as suspicious. Good red herrings:
- A small validation set that sounds underpowered but is fine for the specific test
- A feature that sounds like target leakage but has a clear temporal firewall
- A preprocessing step that sounds nonstandard but is documented best practice for the domain
- A metric that sounds wrong for the task but is actually the right choice

The red herring must appear *in the text* (not just in must_not_claim) so the reviewer is actively tempted.

### 5. Make domain knowledge load-bearing

For hard cases, at least one must_find issue should require knowing something specific about the domain that a general ML reviewer wouldn't know:
- What the standard data split practice is in that specific field
- What a particular metric actually measures vs. what it sounds like it measures
- What operational constraints apply in that deployment context
- What the typical failure mode of the evaluation methodology is for that problem type

The flaw should not be findable by applying "general ML hygiene" thinking — it should require knowing the domain.

### 6. Separate the "smoking gun" from the verdict

In v1 cases, finding the flaw immediately determined the verdict. In v2 hard cases:
- For critique cases: finding one flaw should make the reviewer uncertain whether it's fatal or not. The verdict (critique) requires also understanding *why the flaw is disqualifying* given the deployment context.
- For mixed cases: the reviewer should be able to find all must_find issues and still be uncertain whether the defense holds.

---

## Structural Template for Hard Prompts

```
[Opening paragraph: positive result headline with specific numbers]

[Context paragraph: background on the problem, previous approach, why a change was needed]

[Method paragraph: what was built or changed — described in neutral, matter-of-fact language.
 Flaw #1 is buried here as a design detail that sounds like a reasonable choice.]

[Evaluation setup paragraph: how the comparison was run.
 Flaw #2 is embedded here as a data handling step described as standard practice.]

[Results paragraph: the positive numbers, with confidence or significance language.
 Red herring appears here — something that looks suspicious but is actually fine.]

[Recommendation paragraph: what the team proposes to do next.
 If mixed-position: a genuine uncertainty or caveat that makes the defense plausible.]
```

---

## Scoring Targets Design

### must_find_issue_ids
- Use opaque identifiers that don't hint at the flaw (e.g., `q4_label_regime_change` not `label_contamination_by_policy`)
- Each issue should require cross-paragraph inference to identify
- For hard cases: 3-4 must_find issues minimum

### must_not_claim
- Every hard case must have 2-3 must_not_claim items
- Each must_not_claim item must appear as a plausible concern in the prompt text
- The item should be something a careful reviewer might flag but that is actually fine
- Example: "The 90-day label maturation window is too short for accurate fraud attribution" — acceptable if the domain standard is 90 days and the prompt includes a footnote supporting this

### acceptable_resolutions
- For hard critique cases: ["critique"] only — don't offer escape hatches
- For hard mixed cases: ["mixed", "empirical_test_agreed"] — the case should be genuinely two-sided
- For hard defense_wins cases: ["defense_wins"] — but the defense must be non-obvious

---

## Difficulty Acceptance Criteria

A case is hard enough if a `claude-haiku-4-5` single-pass assessment scores **mean < 0.55** — meaning Haiku misses ≥ 1 must_find issue, OR asserts a must_not_claim item, OR reaches the wrong verdict.

Cases that score 1.0 with Haiku are too easy and must be redesigned.

---

## What to Preserve from v1

- Domain variety: keep cases spread across medical AI, fintech, NLP, CV, RL, recommendation systems
- Schema structure: same JSON schema as v1 cases
- Realistic scenarios: the situations must be plausible for a real ML team
- Correct_position diversity: roughly 50% critique, 30% mixed, 20% defense_wins across the full set
