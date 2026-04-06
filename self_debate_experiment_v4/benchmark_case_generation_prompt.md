# Benchmark Case Generation Prompt
## For use with a non-Anthropic LLM (GPT-4o, Gemini, etc.)

**Purpose:** Generate 50+ high-quality ML reasoning benchmark cases with known ground-truth verdicts. These cases will be used to evaluate an adversarial debate protocol against ensemble and single-pass baselines. Cases must be realistic, unambiguous in ground truth, and free of target leakage.

**Instructions for the operator:** Paste this entire prompt to your chosen LLM. It will generate cases in batches, evaluate them, and output a final curated JSON. Run in a long-context session. Expect 3-4 hours of generation and evaluation passes.

---

## SYSTEM INSTRUCTIONS

You are a benchmark designer for ML evaluation research. Your job is to generate a set of synthetic ML reasoning scenarios with known ground-truth verdicts. These scenarios will be used to test whether an AI debate protocol can correctly identify methodological flaws and exonerate valid work.

You will work in four phases:
1. Generate cases
2. Evaluate and filter cases
3. Score difficulty
4. Output the final curated benchmark

Follow each phase completely before moving to the next.

---

## PHASE 1: CASE GENERATION

Generate exactly 60 cases distributed across the following categories and constraints. You will curate down to 50 after evaluation.

### Category Quotas

| Category | Target n | Description |
|----------|----------|-------------|
| broken_baseline | 10 | Evaluation protocol flaws: unequal eval sets, missing CIs, test-set leakage, feature confounds, preprocessing mismatch, threshold tuning on test set |
| metric_mismatch | 9 | Wrong metric for the claim: accuracy on imbalanced data, offline-to-online correlation gap, ROUGE vs. human validity, Goodhart's Law violations |
| hidden_confounding | 10 | Confounders not acknowledged in the ML claim: seasonal effects, treatment-period interaction, self-selection, selection bias, data leakage |
| scope_intent_misunderstanding | 8 | Attribution or generalization claim exceeds what the experiment establishes: prediction vs. intervention, domain generalization without evidence |
| defense_wins | 13 | Methodologically sound work presented under adversarial framing — correct answer is "no issue" |
| real_world_framing | 10 | Deployment-context causal claims with confounds not stated in the prompt: retrospective evaluation ≠ prospective deployment, asymmetric error costs |

### Mandatory Constraints

**Correct-position distribution** (stored in `ground_truth.correct_position`):
- At least 12 cases must have `correct_position: "mixed"` — cases where both critique and defense positions are substantively defensible and the resolution requires an agreed empirical test
- All defense_wins cases must have `correct_position: "defense"`
- All other cases may be `correct_position: "critique"` or `correct_position: "mixed"`

**Must-find set sizes** (stored in `scoring_targets.must_find_issue_ids`):
- At least 20 cases must have 3 or more must-find items
- No case may have 0 must-find items except defense_wins cases
- Defense_wins cases must have `scoring_targets.must_find_issue_ids: []`

**Must-not-claim** (stored in `scoring_targets.must_not_claim`):
- **Every non-defense_wins case must have at least one `must_not_claim` item** — a plausible-sounding issue that is NOT actually a valid concern for this specific methodology. This is required for IDP scoring: a Critic that raises a `must_not_claim` issue has produced a false positive. Cases without this field produce unscoreable IDP results.
- Every defense_wins case must also have `must_not_claim` populated — use it to list the specific spurious claims a critic might raise about the work (e.g., `class_imbalance_present`, `comparison_invalid`). These should match or extend the false concern described in `planted_issues`.

**Acceptable resolutions** (stored in `scoring_targets.acceptable_resolutions`):
- Every case must have this field as a non-empty list
- At least 10 cases should have more than one acceptable resolution (e.g., both `critique_wins` and `empirical_test_agreed`)

**Difficulty distribution (rubric-anchored — see v3 POST_MORTEM Issue 9):**

Difficulty is defined by *expected rubric performance on a single-pass baseline*, not by how buried the flaw is in the text. The v3 benchmark defined difficulty by findability alone and produced no separation (rho=-0.069, p=0.68). Cases must be hard *to score well on*, not just hard *to find the issue in*.

- **15 easy cases:** The primary flaw is directly stated or implied by a single signal. A single-pass assessor finds all must-find issues, reaches the correct verdict, and would score ≥0.85 mean across applicable rubric dimensions. These cases test basic detection.
- **25 medium cases:** The flaw requires connecting two pieces of information or recognizing an implicit assumption. A single-pass assessor may miss one must-find issue or produce a partially correct resolution. Expected baseline mean: 0.55–0.85. These cases test synthesis.
- **20 hard cases:** The flaw requires multi-step reasoning, domain knowledge, or recognizing what is NOT stated. A single-pass assessor is expected to fail on **at least two** rubric dimensions: IDR (misses a must-find), DRQ (wrong resolution type), ETD (cannot specify a diagnostic test), DC (incorrect verdict direction), or IDP (raises a domain-plausible false positive). Expected baseline mean: <0.55. These cases test the limits of single-pass assessment.

**Structural requirements for hard cases (these create mechanical rubric difficulty, not just text difficulty):**

- At least 8 hard cases must have `correct_position: "mixed"` with `empirical_test_agreed` resolution — mechanically harder because the baseline must produce both a correct verdict AND a well-specified empirical test (ETD) to pass. Single-pass assessors that jump to `critique_wins` will fail DRQ and ETD.
- At least 5 hard cases must have 2+ high-severity planted issues that interact — issues where catching issue A changes the interpretation of issue B. A single-pass assessor that finds A but misses B will produce a qualitatively different (and incomplete) analysis, failing DC and DRQ.
- At least 4 hard cases must have `must_not_claim` items that are domain-plausible — red herrings that require domain expertise to correctly dismiss. A single-pass assessor without domain knowledge is likely to raise these, failing IDP.

**Hard cases must require genuine domain expertise beyond standard ML methodology:** At least 8 of the 20 hard cases must involve flaws that a competent ML generalist would not catch without specific domain knowledge — for example, knowledge of clinical trial EPV rules, recommendation system offline-online correlation standards, financial audit requirements, NLP inter-annotator agreement norms, or regulatory validation standards. The flaw must be genuinely non-obvious to someone who knows ML but does not know the specific domain. These domain-expertise cases are the most likely to produce IDR < 1.0 on the debate protocol.

**Critique cases must contain red herring features:** At least 15 non-defense_wins cases must include one or more scenario features that look methodologically suspicious but are actually valid or irrelevant — for example: a small sample size that is adequately powered by a pre-specified power analysis, a high performance metric that is appropriate for the narrow task, a non-standard split justified by an empirical pre-analysis, or a metric choice that is unusual but correct for the stated claim. These features provide fodder for spurious critiques and allow IDP to be tested on critique cases, not only on defense_wins cases. The prior benchmark had no such features — the Critic never raised a false positive on any critique case (IDP=1.000) because the scenarios contained only genuine flaws with no plausible decoys.

**Trivial baseline must be competitive on at least 5 cases:** At least 5 non-defense_wins cases must be easy enough that a single-pass assessor can find all must-find issues and reach the correct verdict direction without debate structure. This is required for honest lift measurement — a benchmark where the baseline always fails inflates the apparent advantage. Easy cases with directly stated, unambiguous flaws satisfy this requirement.

**No target leakage:** The correct answer must NEVER be visible in the case_id, the scenario introduction, or any reviewer framing.

**Realistic scenarios:** Each case must be plausible as something a real ML team would actually do and present.

### Case Format

Generate each case as a JSON object with this exact structure. Every field is required.

```json
{
  "case_id": "category_shortname_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "difficulty": "easy | medium | hard",
  "task_prompt": "The scenario text given verbatim to the Critic and Defender agents. Must be self-contained. 200-400 words. Written as a neutral description of what an ML team did and claims.",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct end-state conclusion in plain English.",
    "required_empirical_test": "For empirical_test_agreed cases: the exact experimental condition that would settle the disagreement. For critique_wins or defense_wins: null."
  },
  "planted_issues": [
    {
      "issue_id": "short_snake_case_id",
      "description": "One sentence: what the issue is and why it matters methodologically.",
      "severity": "low | medium | high"
    }
  ],
  "ideal_critique": [
    "What a well-calibrated critique should notice about this scenario."
  ],
  "ideal_defense": [
    "What a well-calibrated defense should concede or contest."
  ],
  "ideal_debate_resolution": {
    "type": "critique_wins | defense_wins | empirical_test_agreed",
    "supports_critique_if": "Exact result pattern that would confirm the critique.",
    "supports_defense_if": "Exact result pattern that would exonerate the work.",
    "ambiguous_if": "Exact result pattern that would leave the question open."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["issue_id_1", "issue_id_2"],
    "must_not_claim": ["unsupported_issue_x"],
    "acceptable_resolutions": ["critique_wins", "empirical_test_agreed"]
  },
  "suspicious_but_valid_features": "For defense_wins cases only: a plain-English list of the features that make the work *look* methodologically problematic to a pattern-matching critic but are actually justified (e.g., 'Small n=47 justified by pre-specified power analysis', 'Non-standard 0.22 threshold derived analytically from cost matrix'). This is a human-readable summary for the CASE_VERIFIER — it supplements `planted_issues` and `must_not_claim`. For non-defense_wins cases: null.",
  "ground_truth_rationale": "2-3 sentences explaining why ideal_resolution is correct. Answer key only — do not include in task_prompt.",
  "verifier_status": "pending",
  "notes": "Any design intent, edge cases, or disambiguation for the scorer. Not shown to agents."
}
```

**Field guidance:**

- `planted_issues` is the source of truth for IDR/IDP scoring. Every issue in `scoring_targets.must_find_issue_ids` must appear here with a matching `issue_id`. Severity values: `high` = fatal to the claim, `medium` = significantly weakens it, `low` = real but not disqualifying.

  **For defense_wins cases specifically:** `scoring_targets.must_find_issue_ids` is always `[]` — there are no issues to find. Instead, `planted_issues` must contain exactly ONE entry documenting the PRIMARY false concern a miscalibrated critic would raise. The `issue_id` should describe the false concern (e.g., `false_overfitting_concern`, `spurious_significance_challenge`), the `description` should explain why a critic might raise this concern and why it is actually invalid given the methodology, and the `severity` should be `low` (since it is not a real issue). This entry is what the scoring engine uses to characterize the false-positive trap — it is NOT something the agents should find.

- `scoring_targets.must_not_claim` lists issue IDs that are **plausible but wrong** — things the Critic might raise that are NOT valid concerns given this specific methodology. This is how IDP is properly scored: a Critic that raises a `must_not_claim` issue has produced a false positive.

- `scoring_targets.acceptable_resolutions` is a **list**, not a single value. Some cases genuinely accept multiple resolutions (e.g., both `critique_wins` and `empirical_test_agreed` are correct if the flaw is disqualifying but an empirical test would confirm it). Always include at least `ideal_resolution` in this list.

- `ideal_debate_resolution.supports_critique_if` and `supports_defense_if` must be specific and falsifiable. "If the model performs worse on the held-out set" is acceptable. "If further analysis shows problems" is not.

- `verifier_status` is always `"pending"` when you output the case. The CASE_VERIFIER step will update it to `"keep"`, `"revise"`, or `"reject"`.

### Category-Specific Requirements

**broken_baseline cases:**
- Must involve a specific evaluation design flaw, not just "the baseline is weak"
- The flaw must be fixable by a specific concrete remediation (e.g., matched preprocessing, validation-set threshold selection)
- Hard cases should involve flaws introduced through two simultaneous changes (e.g., model AND preprocessing changed together)

**metric_mismatch cases:**
- The metric must be inappropriate for the specific claim being made, not just "imperfect"
- Mixed-position cases should have a genuine two-sided argument: one position argues the metric is sufficient for the stated scope, the other argues it misses the key quantity
- Include at least 2 cases involving the offline-to-online gap (important for recommendation systems and DRIFT-adjacent fraud detection)

**hidden_confounding cases:**
- The confounder must be present in the task_prompt but not labeled as a confounder — the agent must infer it
- Hard cases should have a confounder that only becomes apparent when the reader notices what is NOT said (e.g., no control group, no prior-year comparison)
- At least 3 cases involving temporal confounds (seasonal, period, secular trend)

**scope_intent_misunderstanding cases:**
- The claim must exceed what the experiment establishes in a specific, articulable way
- Mixed-position cases: one position argues the claim is adequately scoped, the other argues it overgeneralizes
- Include at least 2 cases involving prediction-vs-intervention conflation (a model predicts X; the team claims the model can be used to intervene on X)

**defense_wins cases:**
- The work must be genuinely methodologically sound for the stated scope
- The critique-able features must be real methodological caveats (small n, non-standard split, high performance, unusual threshold) that are actually justified by design
- The justification must be in the task_prompt — agents cannot be expected to know things not stated
- Include at least 3 cases where the justification is a pre-specified analysis choice (power analysis, cost matrix, pre-registered threshold)
- Include at least 2 cases where a non-standard choice is justified by an empirical pre-analysis (e.g., i.i.d. test justifies random split)
- Hard defense_wins cases: the correct exoneration requires distinguishing "limitation that warrants disclosure" from "limitation that invalidates the claim"

**real_world_framing cases:**
- Must involve a deployment decision, not just a research claim
- Hard cases should involve asymmetric error costs that are not explicitly stated but inferable from the domain (e.g., medical triage, fraud detection, loan underwriting)
- At least 2 cases where retrospective evaluation is used to justify prospective deployment

### Domain Diversity

Distribute cases across these ML application domains. Do not cluster more than 15 cases in any single domain.

- Natural language processing / text classification
- Recommendation systems / ranking
- Fraud detection / anomaly detection
- Computer vision / image classification
- Clinical / medical ML
- Time series / forecasting
- Churn prediction / customer behavior
- Causal inference / A/B testing
- AutoML / hyperparameter search
- Tabular / structured data classification

---

## PHASE 2: EVALUATION AND FILTERING

After generating all 60 cases, evaluate each one against the following criteria. Disqualify any case that fails criteria 1-5. Flag but retain cases that fail criteria 6-7 (note the flag in `notes`).

**Criterion 1 — No target leakage (DISQUALIFY if fails)**
Read only the case_id and the first sentence of task_prompt. Can you determine the correct verdict? If yes, the case has target leakage. Rewrite or disqualify.

**Criterion 2 — Ground truth is unambiguous (DISQUALIFY if fails)**
Is `ideal_debate_resolution.type` clearly correct given the task_prompt? Would two independent ML experts agree? Cases where the correct answer requires information not in the prompt are disqualified.

**Criterion 3 — Must-find items are findable (DISQUALIFY if fails)**
Is each issue in `scoring_targets.must_find_issue_ids` identifiable from the task_prompt by a competent ML practitioner? Items that require domain knowledge not in the prompt are disqualified or moved to a "domain expertise required" category.

**Criterion 4 — Realistic scenario (DISQUALIFY if fails)**
Is this plausible as something a real ML team would do? Absurd setups are disqualified.

**Criterion 5 — Empirical test is diagnostic (DISQUALIFY if fails for empirical_test_agreed cases)**
For cases where `ideal_debate_resolution.type` is `empirical_test_agreed`: do `supports_critique_if` and `supports_defense_if` specify distinct, measurable, falsifiable outcomes? A test where both sides would claim the same result as confirmation is non-diagnostic and disqualifies the case.

**Criterion 6 — Defense_wins justification is in the prompt (FLAG if fails)**
For defense_wins cases: is the justification for the non-standard choice explicitly stated in task_prompt? If the defense requires knowledge the agent cannot have from the prompt alone, flag it.

**Criterion 7 — Mixed-position cases have genuine two-sided argument (FLAG if fails)**
For mixed-position cases: are both positions substantively defensible from the task_prompt? If one position clearly dominates, reclassify the case.

**Criterion 8 — Schema completeness check (DISQUALIFY if fails)**
Verify every required field is present and non-empty: `planted_issues` has at least one entry with severity, `scoring_targets.must_find_issue_ids` matches the issue_ids in `planted_issues`, `scoring_targets.acceptable_resolutions` is a non-empty list containing at least `ideal_debate_resolution.type`, `verifier_status` is `"pending"`.

After evaluation, rank all surviving cases by quality (1 = highest). Select the top 50, ensuring:
- All category quotas are approximately met (within ±2)
- At least 12 mixed-position cases survive
- At least 20 cases with 3+ must_find items survive
- Difficulty distribution is approximately maintained
- All defense_wins cases have non-empty `must_not_claim` lists (mandatory per constraint above)
- **All non-defense_wins cases have non-empty `must_not_claim`** — cases without this field are incomplete and must be revised before inclusion
- **At least 8 hard cases require non-ML domain expertise** — cases where a general ML practitioner could not find the flaw without specific domain knowledge. If fewer than 8 survive, flag and note in the summary.
- **At least 15 non-defense_wins cases contain red herring features** — scenario features that look suspicious but are actually valid. If fewer than 15 survive, flag and note in the summary.

---

## PHASE 3: DIFFICULTY CALIBRATION

For each surviving case, estimate the difficulty using rubric-anchored criteria — difficulty is defined by expected *scoring performance*, not just issue findability:

- **Easy:** A single-pass assessor finds all must-find issues, reaches the correct verdict direction, and scores ≥0.85 mean. Zero or one rubric dimensions fail. Cases where the flaw is directly stated or follows from a single signal.
- **Medium:** A single-pass assessor may miss one must-find issue or produce a partially correct resolution. Expected baseline mean 0.55–0.85. One rubric dimension likely fails (typically IDR or DRQ). Cases where the flaw requires connecting two pieces of information.
- **Hard:** A single-pass assessor is expected to fail on at least two rubric dimensions. Expected baseline mean <0.55. Cases where the flaw requires multi-step reasoning, domain knowledge, noticing what is NOT said, or where the correct resolution type is non-obvious.

Revise any difficulty labels that don't match these definitions. Note any cases where you are uncertain in `notes`.

### Difficulty self-test (required before proceeding to Phase 4)

For each case labeled **hard**, answer these two questions:
1. Which specific rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) would a single-pass assessor likely fail on?
2. Why — what structural property of the case causes that failure?

If the answer to question 1 is "none" or "only IDR would be slightly lower," the case is **medium**, not hard. Relabel it.

If after the self-test fewer than 15 cases remain classified as hard, revise cases upward in difficulty by adding interacting planted issues, domain-specific red herrings in `must_not_claim`, or resolution ambiguity (changing `critique_wins` to `empirical_test_agreed` where defensible). Do NOT increase difficulty by merely burying the flaw deeper in the text — that does not produce rubric separation.

---

## PHASE 4: OUTPUT

Output the final 50 curated cases as a single JSON array. The array should be sorted: easy cases first, then medium, then hard within each category. Include all fields from the case format above.

After the JSON, output a summary table:

```
BENCHMARK SUMMARY
=================
Total cases: 50
By category: [table]
By difficulty: [table]
By correct_position (from ground_truth.correct_position): [table]
Mixed-position cases: N
Cases with 3+ must_find_issue_ids: N
Cases with non-empty must_not_claim: N (expected: all 50)
Cases with red herring features in scenario text: N (target >= 15 non-defense_wins)
Hard cases requiring non-ML domain expertise: N (target >= 8)
Hard cases with mixed + empirical_test_agreed: N (target >= 8)
Hard cases with 2+ interacting high-severity issues: N (target >= 5)
Hard cases with domain-plausible must_not_claim: N (target >= 4)
Cases with multiple acceptable_resolutions: N
Cases disqualified (list reason): N
Cases flagged (list flags): N
High-severity planted issues total: N
```

Then output a **difficulty discrimination table** — for each difficulty tier, list the predicted mean number of rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) a single-pass assessor would fail on:

```
DIFFICULTY DISCRIMINATION
=========================
Easy:   predicted failed dims = X.X  (target: ≤0.5)
Medium: predicted failed dims = X.X  (target: 0.5–1.5)
Hard:   predicted failed dims = X.X  (target: ≥2.0)
```

If the predicted discrimination does not separate the tiers, flag this in the self-critique and identify which hard cases need structural revision.

Then output a self-critique: what are the 3 most likely weaknesses of this benchmark that an adversarial reviewer would identify?

---

## QUALITY STANDARDS

The benchmark will be used in a paper submission. Cases that would embarrass the authors if scrutinized are worse than having fewer cases. Prefer quality over quantity. It is better to generate 45 excellent cases than 50 mediocre ones.

The gold standard for a good case: a senior ML engineer reading the task_prompt would say "yes, this is a real problem I've seen teams make" (for critique cases) or "yes, this is a real methodology people challenge unfairly" (for defense cases).

Begin Phase 1 now. Generate all 60 cases before proceeding to Phase 2.

---

## OUTPUT FORMATTING REQUIREMENT

When outputting the final 50-case JSON array at the end of Phase 4, use no markdown formatting whatsoever. No code fences, no triple backticks, no language tags. The output must start directly with `[` and end directly with `]`. This is required so the output can be saved as `benchmark_cases.json` without any stripping or editing by the operator.
