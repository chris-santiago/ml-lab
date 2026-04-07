# Case Generation Prompt v5 — Hard Cases Only

**Scope:** Hard cases only (difficulty=hard). Easy and medium cases from v1 are retained without modification.

**For use with a non-Anthropic LLM (e.g., GPT-4o, GPT-5, Gemini, etc.)**

**Purpose:** Generate 15–20 hard benchmark cases that are genuinely difficult for a frontier LLM single-pass reviewer — not just for human domain experts. These cases will replace the current hard cases in a benchmark that evaluates whether an adversarial debate protocol outperforms single-pass assessment.

**How to use:**
1. Paste this entire document as the system/instruction prompt
2. Request 15–20 new hard cases from scratch (not revisions of existing cases)
3. Request output as a JSON array matching the schema in the Output Format section
4. Run Phase 1 (CASE_VERIFIER) on the new cases
5. Run Phase 5.5 difficulty gate — acceptance criterion: ≥ 6 of 10 sampled hard cases score mean < 0.55 with `claude-haiku-4-5` as evaluator

---

## Why Previous Prompts Failed

### v1 (self-annotating cases)
Flaws were directly named in the text. "The endpoint definition changed from X to Y" is trivially findable by any reader. Every hard case scored 1.0.

### v1 revision (buried in memos)
Rewrote cases as confident memos with flaws distributed across paragraphs. Still scored 1.0. Models process entire documents holistically — distributing information across paragraphs does not create difficulty for a model that sees all paragraphs simultaneously.

### v2 (cross-paragraph inference + red herrings)
Required connecting details from different sections, added active red herrings, used opaque identifiers. Still scored 1.0 with both Sonnet and Haiku. The flaws were still **inconsistencies between stated facts** — and finding factual inconsistencies within a document is something LLMs excel at. Asking "do these two paragraphs contradict each other?" is trivial for a model trained on massive text corpora.

### Core diagnosis
All three versions failed for the same reason: **the flaws were detectable by pattern-matching within the document**. Inconsistencies, contradictions, and cross-paragraph mismatches are exactly what LLMs are trained to find. No amount of hiding or distributing this type of flaw across paragraphs will work.

---

## v5 Design Principles — What Actually Makes Cases Hard for LLMs

A case is hard for an LLM when the flaw **cannot be found by analyzing the document's internal consistency**. The document must be internally consistent — every stated fact must agree with every other stated fact. The flaw must be in the relationship between what the document states and **what is actually true about the world**, or in a **quantitative claim that requires computation to verify**.

### Principle 1: Flaws Are Wrong Assumptions, Not Inconsistent Facts

**Never:** Two paragraphs that contradict each other (model finds this instantly).
**Never:** Parallel before/after paragraph structure ("The old system... The new system...") — this is the first thing agents scan. Even if the content is sound, parallel structure triggers a mechanical diff that will surface any asymmetry.
**Instead:** A single coherent methodology that is based on an unstated assumption that happens to be wrong.

Example: A document describes using propensity score matching with a logistic regression propensity model to adjust for confounders in a treatment-control comparison. The methodology sounds standard. But the treatment was assigned based on a decision tree with interaction effects — logistic propensity scores cannot capture the true assignment mechanism, making the matched comparison biased. The document never states the assignment mechanism incorrectly — it simply doesn't state it, and the reader must know that propensity matching requires the propensity model to be correctly specified.

The reviewer must bring **external knowledge** about when propensity matching fails, not just check whether the document contradicts itself.

### Principle 2: Flaws Require Quantitative Verification

Include specific numbers that sound reasonable but are wrong when checked:

- A stated sample size that is insufficient for the claimed effect size (requires power calculation)
- A confidence interval width that is inconsistent with the stated N and variance (requires back-of-envelope math)
- A reported precision/recall that is mathematically impossible given the stated confusion matrix
- A claimed lift that is within the noise floor of the evaluation design (requires significance estimation)
- A temporal split that sounds reasonable but creates a train-test overlap given the stated feature window

The numbers must be specific enough that a reviewer COULD verify them, but plausible enough that a reviewer who doesn't verify them would accept them.

### Principle 3: Flaws Are Strategic Omissions

The document doesn't mention something that, if present, would be fine — but its absence is a problem. These are invisible to consistency checkers because there's nothing to contradict.

- No mention of how missing values were handled (in a domain where missing-not-at-random is common)
- No mention of temporal ordering between feature computation and label observation (in a prediction task)
- No mention of whether the comparison model was retrained on the same data (in a model upgrade evaluation)
- No mention of how ties were broken in a ranking metric (when the reported metric is at a threshold where ties matter)
- No mention of survivorship in a cohort study (when the outcome is time-dependent)

The reviewer must know what SHOULD be mentioned for this type of study and notice its absence.

### Principle 4: Justifications That Are Subtly Wrong

The document acknowledges a potential concern and provides a justification — but the justification contains a subtle error. This is harder than either hiding the concern or not justifying it, because the reviewer must:
1. Notice the concern
2. Read the justification
3. Evaluate whether the justification is valid
4. Determine that it isn't (requires domain knowledge)

Example: "To address class imbalance, we applied SMOTE to the training set before cross-validation." This sounds like the right answer (address imbalance, do it on training set). But SMOTE before CV means the synthetic samples from the same minority instance can appear in both the training and validation folds of the CV — inflating the CV estimate. The justification ("applied to the training set") is partially correct but the key error is the ordering relative to the CV split, which is a known but non-obvious pitfall.

### Principle 5: Red Herrings With Defensible But Incomplete Justifications

Previous red herrings failed because their justifications were clearly correct — the model could easily verify "this concern is addressed." V5 red herrings should have justifications that are **mostly correct but leave a plausible gap**, so the reviewer must spend effort evaluating whether the justification is sufficient. The reviewer should ultimately conclude it IS sufficient (it's a red herring, not a real flaw), but the conclusion should require domain knowledge, not just reading the justification.

Example red herring: "The evaluation used only 14 days of production data." This sounds short. The document justifies it by noting the product has a 7-day usage cycle. A reviewer might still flag it — but in this specific domain, 14 days (2 full cycles) is standard practice for this type of evaluation, and the seasonal/trend effects that would require longer windows don't apply to this product category.

### Principle 6: Flaw Category Must Not Be Predictable From Scenario Type

In v1/v2, model comparison scenarios had comparison flaws, confounding scenarios had confounders, etc. An LLM can learn "when I see a model comparison, check for unfair comparison" and find the flaw mechanically.

V5 cases must **decouple the scenario type from the flaw type**:
- A model comparison scenario where the flaw is actually a confounding issue (not a comparison issue)
- A deployment proposal where the flaw is actually a metric mismatch (not a deployment-readiness issue)
- A causal inference study where the flaw is actually a scope/intent issue (not a confounding issue)

The reviewer who applies the category-appropriate checklist should NOT find the flaw.

### Principle 7: Length Creates Difficulty

V5 hard case prompts must be **500–800 words** (v1 was 200–400). Longer prompts with more operational detail create more surface area for the reviewer to track. The flaw should be a small detail within a large, mostly-sound methodology. The signal-to-noise ratio should be low.

Include realistic operational details: team names, deployment timelines, infrastructure constraints, stakeholder quotes, budget figures, rollout plans. These are not flaws — they are noise that makes the flaw harder to isolate.

### Principle 8: The Obvious Finding Must Be a Red Herring

Raw output analysis of v1–v2 cases showed that agents immediately lock onto the most salient surface feature — an unusual class ratio, a short evaluation window, a non-standard metric name — and announce it as the flaw. In v5, this surface feature must exist but must be the **must_not_claim** item: a genuine concern that has an adequate (if subtle) justification. The real flaw must be found elsewhere, in the less salient methodology.

This forces the agent to do two things correctly: (1) evaluate the justification for the obvious concern rather than stopping when it finds it, and (2) continue searching after that concern is resolved. A case where the only unusual-looking feature is the real flaw is too easy — a calibrated agent locks onto unusual features first.

---

## Detection Patterns to Design Against

Empirical analysis of raw agent outputs across v1–v2 hard cases revealed four systematic detection strategies that agents apply. Every v5 case must be designed to resist all four.

### Pattern 1: Diff-the-Paragraphs

Agents maintain an internal checklist of comparison dimensions (data source, preprocessing, evaluation metric, time period, population) and mechanically diff every stated attribute across compared systems. Any asymmetry — even a word choice difference — is flagged as a potential flaw.

**Defense:** The compared systems must be described in non-parallel prose. Interleave operational details about both systems. Never use a "System A: ... System B: ..." structure. Avoid symmetric sentence patterns even when describing different things.

### Pattern 2: Claim-vs-Evidence Gap Analysis

Agents read each claim and ask whether the cited evidence supports it. If a metric is reported and the measurement methodology is implicit, agents probe the methodology. If a significance claim is made, agents check whether statistical details are consistent.

**Defense:** All evidence must appear to support its claim. The flaw must be in the *framework* the evidence is embedded in (wrong assumption, omitted confounder) — not in a gap between a claim and its stated evidence. The numbers must be internally consistent; the error must require computation to surface.

### Pattern 3: Label Provenance Tracing

For prediction or classification tasks, agents trace the path from raw data → features → labels and look for temporal contamination, label drift, or definition changes. This pattern finds leakage and endpoint changes instantly.

**Defense:** Label definitions must be stable and unambiguous throughout the document. If the task involves a label, describe its definition once, clearly, and do not reference it again in a way that implies change. The flaw must be in something other than the label pipeline.

### Pattern 4: Observational Study Confound Enumeration

For any before/after, treatment/control, or cohort comparison, agents apply a textbook causal checklist: selection bias, survivorship, concurrent interventions, regression to the mean, informative censoring. They enumerate candidate confounders and check whether each is addressed.

**Defense:** Confounders that agents would enumerate must be explicitly addressed in the document — with justifications that are mostly-correct but subtly wrong (Type D flaw), or addressed correctly (must_not_claim). The real flaw must be outside the standard confound checklist — e.g., a violated statistical assumption, a quantitative error, or an omitted step the standard checklist doesn't ask about.

---

## Trigger Phrases to Eliminate

The following phrases and structural patterns caused immediate flaw detection in v1–v2 raw outputs. Do not use them in v5 prompts.

**Numerical patterns that invite direct comparison:**
- Side-by-side statistics for compared groups: "Group A: 23%; Group B: 7%"
- Named temporal partitions: "Q1–Q2 vs. Q3–Q4", "pre-launch vs. post-launch", "before vs. after"
- Explicit percentage-point lifts: "+12.3pp improvement"

**Population selection signals:**
- "opt-in", "self-selected", "voluntary enrollment"
- "normal intake", "standard referral pathway", "usual care"
- Any phrase that signals the treatment group chose their own treatment

**Threshold/calibration signals:**
- "threshold was calibrated on [the evaluation period]"
- "cutoff selected based on [the held-out set]"
- "optimized against [the test data]"

**Structural signals:**
- Parallel paragraph structure for compared systems
- Sentences containing both a confound and the mechanism in one clause: "because patients in the intervention arm were healthier to begin with, we..."
- Explicit transition sentences: "To address this concern, we..." — agents read these as a roadmap to the concerns and their justifications, and evaluate each one

**Replacement strategy:** Integrate comparison details into a single unified narrative about the evaluation design. Report results as properties of the evaluation, not as contrasts between systems. If a concern is addressed, the justification must be embedded in operational detail, not flagged with a transition sentence.

---

## Flaw Taxonomy for v5 Hard Cases

Generate cases using these flaw types. Each type is designed to resist pattern-matching.

### Type A: Assumption Violations (target: 5–6 cases)
The methodology makes an unstated assumption that is violated by the data or deployment context. The document is internally consistent. The assumption is standard practice — but not for this specific situation.

Examples:
- i.i.d. assumption violated by spatial or network autocorrelation
- Stationarity assumption violated by a regime change that occurred during data collection
- Overlap assumption violated in causal inference (positivity violation)
- Conditional independence assumption violated by an unmeasured common cause
- Exchangeability assumption violated by informative censoring

### Type B: Quantitative Errors (target: 3–4 cases)
The document reports specific numbers that are internally consistent but quantitatively wrong when verified. The error is not detectable by reading — it requires computation.

Examples:
- Reported CI width incompatible with stated N and effect size
- Claimed statistical significance with a p-value that doesn't survive multiple testing correction (correction is mentioned but applied incorrectly)
- Power analysis that uses the wrong formula for the test actually performed
- Precision@k that is mathematically impossible given the stated prevalence and N

### Type C: Critical Omissions (target: 3–4 cases)
The methodology omits a step or disclosure that is mandatory for this type of study. The omission is not flagged — it simply isn't there. The reviewer must know the standard for this study type.

Examples:
- No disclosure of feature engineering performed after the train/test split
- No mention of calibration in a probability-based decision system
- No mention of how the threshold was selected in a classification deployment
- No disclosure of whether hyperparameter tuning used the test set
- No survivorship bias analysis in a longitudinal cohort study

### Type D: Subtly Wrong Justifications (target: 4–5 cases)
The document anticipates a concern and provides a justification that is almost but not quite correct. The justification has a specific technical error.

Examples:
- Claims "we used stratified sampling" to address class imbalance — but stratified sampling preserves class proportions, it doesn't address the imbalance's effect on the loss function
- Claims "we ensured temporal ordering" by using a date cutoff — but the feature window extends past the cutoff for some records
- Claims "we corrected for multiple comparisons using Bonferroni" — but applied it to correlated tests where Bonferroni is overly conservative and the real issue is that they should have used a permutation test
- Claims "we validated on an external dataset" — but the external dataset was used for early stopping, not held out entirely

---

## Constraints

### Category distribution (across all 15–20 generated hard cases)
| Category | Target n |
|----------|----------|
| broken_baseline | 4 |
| metric_mismatch | 3 |
| hidden_confounding | 4 |
| scope_intent | 3 |
| defense_wins | 3–4 |
| real_world_framing | 2 |

### Position distribution
- At least 6 cases must have `correct_position: "mixed"` with `empirical_test_agreed` resolution
- All defense_wins cases must have `correct_position: "defense"`
- Remaining cases: `correct_position: "critique"`

### Must-find requirements
- Non-defense_wins cases: 3–5 must_find_issue_ids each
- Defense_wins cases: 0 must_find (IDR trivially 1.0); planted_issues describes the false concern trap

### Must-not-claim requirements
- Every case (including defense_wins): 2–4 must_not_claim items
- Each must_not_claim must appear as a plausible concern IN the prompt text, with a defensible but incomplete justification
- A reviewer who does not carefully evaluate the justification should be tempted to flag it

### Prompt length
- 500–800 words per task_prompt for hard cases
- Written as a confident internal memo, quarterly review, launch proposal, or evaluation report
- No problem statements — every prompt opens with a positive recommendation or result

### No target leakage
- case_id must be opaque (e.g., `eval_scenario_NNN`)
- The correct answer must not be inferrable from the scenario introduction
- The category must not be guessable from the scenario type (per Principle 6)

---

## Output Format

Return a JSON array. No markdown formatting. Output starts with `[` and ends with `]`.

Each case object:

```json
{
  "case_id": "eval_scenario_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent | defense_wins | real_world_framing",
  "difficulty": "hard",
  "task_prompt": "500-800 word memo/report. Internally consistent. Flaw is an assumption violation, quantitative error, critical omission, or subtly wrong justification — NOT a factual inconsistency.",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct conclusion.",
    "required_empirical_test": "For empirical_test_agreed cases: the exact experiment. For others: null."
  },
  "planted_issues": [
    {
      "issue_id": "opaque_snake_case_id",
      "description": "What the issue is and why it matters. For defense_wins: the false concern trap.",
      "severity": "low | medium | high",
      "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification",
      "requires_external_knowledge": "One sentence: what domain knowledge is needed to find this flaw."
    }
  ],
  "ideal_critique": ["What a well-calibrated critique should find."],
  "ideal_defense": ["What a well-calibrated defense should concede or contest."],
  "ideal_debate_resolution": {
    "type": "critique_wins | defense_wins | empirical_test_agreed",
    "supports_critique_if": "Specific, falsifiable result pattern.",
    "supports_defense_if": "Specific, falsifiable result pattern.",
    "ambiguous_if": "Specific, falsifiable result pattern."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["issue_id_1", "issue_id_2"],
    "must_not_claim": ["plausible_but_wrong_concern_1"],
    "acceptable_resolutions": ["critique_wins"]
  },
  "suspicious_but_valid_features": "For defense_wins: plain-English list. For others: null.",
  "ground_truth_rationale": "2-3 sentences. Answer key only.",
  "difficulty_justification": "Which v5 principles make this case hard. Which specific rubric dimensions (IDR, IDP, DRQ, ETD, FVC) a single-pass assessor should fail on and why.",
  "verifier_status": "pending",
  "notes": ""
}
```

### New fields in v5 schema
- `planted_issues[].flaw_type`: Which of the 4 v5 flaw types this issue uses
- `planted_issues[].requires_external_knowledge`: What domain knowledge the reviewer needs
- `difficulty_justification`: Why the case is hard, anchored to specific rubric dimensions

---

## Self-Evaluation (Required Before Output)

After generating all cases, evaluate each one against the following test:

**The Internal Consistency Test:** Read only the task_prompt. Can you find ALL must_find issues by checking whether any stated facts contradict each other? If YES → the case is too easy. The flaw is a factual inconsistency, not an assumption violation. Redesign it.

**The Checklist Test:** For the case's category, apply the standard review checklist (e.g., for broken_baseline: same data? same preprocessing? same metrics? same splits?). Does the checklist find the flaw? If YES → the flaw type is predictable from the category. Change the flaw type or the category framing.

**The Skimming Test:** Read only the first and last paragraphs. Can you determine the correct verdict? If YES → the case has verdict leakage. Restructure it.

**The Justification Test:** Does the document acknowledge potential concerns and provide justifications? For each justification: is the justification clearly correct (reviewer stops investigating), clearly wrong (reviewer flags immediately), or subtly wrong (reviewer must evaluate carefully)? The answer must be "subtly wrong" for at least one justification per case.

**The Run-to-Run Variation Test (proxy difficulty check):** Mentally simulate submitting this task_prompt to a single-pass evaluator twice with temperature > 0. Would both runs produce the same findings, in the same order, at the same confidence level? If YES → the case has a deterministic single correct reading. A hard case should generate **meaningfully different runs**: different issues found, different ordering, different uncertainty level, or different verdict. Verbatim-identical outputs across runs are a direct measure of a case being too easy — they indicate the document has a single obvious reading that every reviewer converges to without deliberation.

Discard or redesign any case that fails two or more tests. Note which tests each case passes in the `notes` field.

---

## Difficulty Acceptance Criteria

A v5 hard case passes the gate if a `claude-haiku-4-5` single-pass assessor scores **mean < 0.55** — meaning Haiku misses ≥ 1 must_find issue, OR asserts a must_not_claim item, OR reaches the wrong verdict.

Additionally, a well-designed hard case should produce **run-to-run variation** when evaluated at nonzero temperature: different runs should differ in which issues they identify, the ordering, or the verdict. If you can predict exactly what a reviewer will find on every run, the case is too easy regardless of whether the reviewer is technically correct.

Cases that score 1.0 with Haiku, or that produce verbatim-identical reviewer outputs across runs, must be redesigned.

---

## Quality Standard

The gold standard: a senior ML engineer reading the task_prompt says "I read this carefully and it seems fine" on first pass, then on second pass with specific probing says "wait — actually, there's a problem with [specific assumption/number/omission]." The case must survive the first pass to be hard.

Cases where the flaw is obvious to a careful first-time reader — regardless of how the flaw is structured — are medium difficulty, not hard.

Begin generation now. Generate all 15–20 cases, run the self-evaluation, then output the final set.
