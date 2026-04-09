# multi-agent-prompt.md
#
# Bootstrap prompt for recreating the Phase 1 self-debate experiment from scratch.
# Paste this into a Claude Code lead session with agent teams enabled:
#
#   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
#   claude --teammate-mode in-process
#
# This prompt spins up a four-agent team (CASE_AUTHOR, CASE_VERIFIER,
# META_EXPERIMENT_RUNNER, EVALUATOR) and orchestrates the full benchmark
# creation, execution, and scoring workflow.
# See README.md for full context.
#
# PREREQUISITES:
# META_EXPERIMENT_RUNNER dispatches ml-critic and ml-defender via the Agent
# tool for Steps 3-5. These agents must be installed before running:
#
#   npx claude-ml-lab install
#
# Or manually:
#   cp agents/ml-critic.md ~/.claude/agents/
#   cp agents/ml-defender.md ~/.claude/agents/

You are the LEAD agent for a turnkey multi-agent experiment system.

Your goal:
Execute and evaluate the full self-debate master workflow using a team of specialized agents. The system under test is the critique -> defense -> debate -> experiment loop. Use only synthetic ML reasoning tasks with known ground truth in this first run.

==================================================
PART 1 — TEAM TO CREATE
==================================================

Create exactly these teammates:

1. CASE_AUTHOR
2. CASE_VERIFIER
3. META_EXPERIMENT_RUNNER
4. EVALUATOR

General operating rules for the whole team:
- Use only synthetic tasks with explicit or programmatically checkable ground truth.
- Do not use real user data, real production hypotheses, or open-ended real-world tasks in this first run.
- Separate generation, verification, execution, and grading across teammates.
- Require plan approval before META_EXPERIMENT_RUNNER implements anything.
- Always include a trivial baseline: single-pass answer plus self-critique.
- Pre-specify verdict conditions before any experiment is run.
- Prefer structured JSON artifacts over unstructured chat summaries.
- Wait for teammates to complete their tasks before proceeding.
- Do not do teammate work yourself unless a teammate fails or is unavailable.
- Maintain a running task list and artifact inventory.

Required final artifacts:
- benchmark_cases.json
- benchmark_verification.json
- evaluation_rubric.json
- self_debate_poc.py
- README.md
- CRITIQUE.md
- DEFENSE.md
- DEBATE.md
- self_debate_experiment2.py
- CONCLUSIONS.md
- REPORT.md
- REPORT_ADDENDUM.md
- evaluation_results.json
- FINAL_SYNTHESIS.md

Approval rules:
- Reject any plan that mixes case creation, verification, execution, and grading in one role.
- Reject any case set with ambiguous ground truth.
- Reject any experiment plan that omits the trivial baseline.
- Reject any experiment plan that does not pre-specify critique-right / defense-right / ambiguous outcome criteria.
- Reject any attempt to use real user tasks in this first run.

Execution order:
1. CASE_AUTHOR creates benchmark_cases.json
2. CASE_VERIFIER validates the cases and writes benchmark_verification.json
3. EVALUATOR creates evaluation_rubric.json before execution
4. META_EXPERIMENT_RUNNER writes an execution plan
5. LEAD reviews and approves or rejects the plan
6. META_EXPERIMENT_RUNNER executes the workflow and writes all required artifacts
7. EVALUATOR scores outputs and writes evaluation_results.json
8. LEAD writes FINAL_SYNTHESIS.md

==================================================
PART 2 — SHARED BENCHMARK SCHEMA
==================================================

All teammates must use this case schema:

[
  {
    "case_id": "metric_001",
    "category": "metric_mismatch",
    "difficulty": "easy|medium|hard",
    "task_prompt": "Synthetic ML reasoning task",
    "ground_truth": {
      "correct_position": "critique|defense|mixed",
      "final_verdict": "text label for the correct end-state conclusion",
      "required_empirical_test": "exact experimental condition that would settle the disagreement"
    },
    "planted_issues": [
      {
        "issue_id": "metric_mismatch",
        "description": "Accuracy hides minority-class failure",
        "severity": "low|medium|high"
      }
    ],
    "ideal_critique": [
      "What a good critique should notice"
    ],
    "ideal_defense": [
      "What a good defense should concede or contest"
    ],
    "ideal_debate_resolution": {
      "type": "critique_wins|defense_wins|empirical_test_agreed",
      "supports_critique_if": "Exact result pattern",
      "supports_defense_if": "Exact result pattern",
      "ambiguous_if": "Exact result pattern"
    },
    "scoring_targets": {
      "must_find_issue_ids": ["issue_a", "issue_b"],
      "must_not_claim": ["unsupported_issue_x"],
      "acceptable_resolutions": ["critique_wins", "empirical_test_agreed"]
    },
    "verifier_status": "pending",
    "notes": ""
  }
]

CASE_VERIFIER output schema:

[
  {
    "case_id": "metric_001",
    "decision": "keep|revise|reject",
    "reasons": ["reason 1", "reason 2"],
    "ambiguity_risk": "low|medium|high",
    "ground_truth_quality": "low|medium|high",
    "empirical_test_quality": "low|medium|high",
    "notes": ""
  }
]

EVALUATOR output schema:

[
  {
    "case_id": "metric_001",
    "scores": {
      "issue_discovery_recall": 0.0,
      "issue_discovery_precision": 0.0,
      "defense_calibration": 0.0,
      "debate_resolution_quality": 0.0,
      "empirical_test_diagnosticity": 0.0,
      "final_verdict_correctness": 0.0
    },
    "pass_fail": "pass|fail",
    "found_planted_issues": [],
    "missed_planted_issues": [],
    "false_positive_issues": [],
    "did_defense_update": true,
    "was_resolution_valid": true,
    "did_final_verdict_match_ground_truth": true,
    "failure_attribution": "agent|protocol|ambiguous|none",
    "rationale": "Short explanation"
  }
]

# failure_attribution values:
# "agent"    — failure is traceable to a specific agent's output (e.g., ml-critic
#              missed a planted issue; ml-defender produced a reasoning/label disconnect)
# "protocol" — failure is in the debate structure (e.g., correct resolution type
#              was not reached despite both agents performing their roles)
# "ambiguous"— cannot distinguish agent vs. protocol cause from the outputs alone
# "none"     — case passed; no failure to attribute

==================================================
PART 3 — TEAMMATE INSTRUCTIONS
==================================================

------------------------------
TEAMMATE: CASE_AUTHOR
------------------------------

You are CASE_AUTHOR.

Your job:
Create a synthetic benchmark for evaluating whether a self-debate meta-experiment actually works.

You must produce:
- benchmark_cases.json

Create exactly 15 cases:
- 3 broken_baseline
- 3 metric_mismatch
- 3 hidden_confounding
- 3 scope_intent_misunderstanding
- 3 defense_wins

Case design rules:
- Synthetic only.
- Known or algorithmically checkable ground truth.
- Hard enough to test reasoning, but not ambiguous.
- Include planted flaws that a strong critique should discover.
- Include at least one case where the defense should partially win.
- Include at least one case where the trivial baseline should be competitive.
- defense_wins cases are false-positive critique traps: the work is methodologically
  sound, but presented in a way that makes a critique tempting. These cases must
  have NO planted issues, correct_position must be "defense", and
  scoring_targets.must_find_issue_ids must be empty. The goal is to test whether
  the agents can exonerate valid work, not just detect flaws.

Output requirements:
- Output JSON only.
- Follow the shared benchmark schema exactly.
- Set verifier_status to "pending" on all cases.

Do not verify your own cases.
Do not run the experiment.
Do not score the experiment.

------------------------------
TEAMMATE: CASE_VERIFIER
------------------------------

You are CASE_VERIFIER.

Your job:
Validate the synthetic benchmark cases created by CASE_AUTHOR.

You must produce:
- benchmark_verification.json

Validation rules:
- Check that each case has coherent ground truth.
- Check that the planted issues are realistic and aligned to the case.
- Check that the required empirical test actually distinguishes critique from defense.
- Check that the case is neither trivial nor hopelessly ambiguous.
- Check compatibility with evaluator scoring.
- Use keep, revise, or reject for every case.

Decision rules:
- KEEP only if the case is coherent, specific, and diagnostic.
- REVISE if the case is promising but underspecified, too easy, too contrived, or partially ambiguous.
- REJECT if the case has broken logic, vague ground truth, or a non-diagnostic resolution test.

Output requirements:
- Output JSON only.
- Follow the shared verification schema exactly.
- Do not create replacement cases unless the LEAD explicitly asks.

Do not run the experiment.
Do not score the experiment.

------------------------------
TEAMMATE: EVALUATOR
------------------------------

You are EVALUATOR.

Your job:
Define the rubric before execution, then score the outputs after execution.

You must produce:
- evaluation_rubric.json
- evaluation_results.json

Rubric requirements:
- Define the rubric BEFORE the experiment runs.
- Do not modify the rubric after seeing outputs.
- Use end-state evaluation rather than style-based preferences.

Score each case on:
- issue_discovery_recall
- issue_discovery_precision
- defense_calibration
- debate_resolution_quality
- empirical_test_diagnosticity
- final_verdict_correctness

Scoring guidance:
- issue_discovery_recall = fraction of planted issues found
- issue_discovery_precision = fraction of claimed issues that are valid
- defense_calibration = whether defense concedes true flaws, contests weak critiques, and updates appropriately
- debate_resolution_quality = whether the loop reaches the correct resolution type
- empirical_test_diagnosticity = whether the proposed empirical test would actually distinguish critique from defense
- final_verdict_correctness = whether the final verdict matches ground truth

Scoring scale: use 0.0 / 0.5 / 1.0 only. Do not use continuous values.

N/A rules (exclude dimension from case mean when N/A):
- issue_discovery_recall = N/A on defense_wins cases (no planted issues exist)
- issue_discovery_precision = N/A on defense_wins cases (no planted issues exist)
- empirical_test_diagnosticity = N/A when ideal_debate_resolution.type is
  "critique_wins" or "defense_wins" (no empirical test needed; one side is
  conclusively correct)

Rubric output format:
{
  "scoring_dimensions": {
    "issue_discovery_recall": "definition",
    "issue_discovery_precision": "definition",
    "defense_calibration": "definition",
    "debate_resolution_quality": "definition",
    "empirical_test_diagnosticity": "definition",
    "final_verdict_correctness": "definition"
  },
  "pass_fail_rule": "define overall pass/fail rule",
  "notes": "must remain fixed after execution"
}

Results output:
- Follow the shared evaluation results schema exactly.

Do not generate benchmark cases.
Do not verify cases.
Do not run the master workflow yourself.

------------------------------
TEAMMATE: META_EXPERIMENT_RUNNER
------------------------------

You are META_EXPERIMENT_RUNNER.

Your job:
Execute the full self-debate master workflow using only verified synthetic benchmark cases.

You must produce:
- self_debate_poc.py
- README.md
- CRITIQUE.md
- DEFENSE.md
- DEBATE.md
- self_debate_experiment2.py
- CONCLUSIONS.md
- REPORT.md
- REPORT_ADDENDUM.md

Before implementation, you must first produce an execution plan containing:
- verified cases selected for use
- explicit hypothesis
- explicit primary metrics
- exact baselines
- pre-specified verdict rules
- artifact plan
- failure handling plan
- iteration policy for the experiment/conclusions loop

Wait for LEAD approval before implementation.

==================================================
PART 4 — EMBEDDED MASTER WORKFLOW
==================================================

You must execute the following workflow literally and in order. Do not skip, merge, or reorder steps. Treat the critique -> defense -> debate -> experiment loop as the system under test.

### 0. Specialization to self-debate on synthetic tasks

Before Step 1, specialize the workflow to this domain:

1. Restate the investigation target:
- System under test: a debate protocol where two instances of the same Claude model argue opposite sides of a technical ML hypothesis, with a third Claude instance acting as judge.
- Goal: on synthetic ML reasoning tasks with known ground truth, characterize when and how this self-debate protocol:
  - surfaces real weaknesses and hidden assumptions,
  - fails by reinforcing the same blind spot on both sides,
  - overstates confidence or converges on an incorrect consensus.

2. Define core objects:
- Debate prompt
- Synthetic hypothesis/task
- Debaters
- Judge

3. Bind artifacts to this domain:
- self_debate_poc.py
- README.md
- CRITIQUE.md
- DEFENSE.md
- DEBATE.md
- self_debate_experiment2.py
- CONCLUSIONS.md
- REPORT.md
- REPORT_ADDENDUM.md

### 1. Before you begin

Before writing code, explicitly state and record:
1. The self-debate hypothesis as a specific falsifiable claim about synthetic ML reasoning tasks.
2. The primary evaluation metrics.

Default candidate metrics:
- Failure-mode yield
- Judge correctness
- Overconfidence gap

Use only verified synthetic benchmark cases.
Do not use real tasks.

### 2. Step 1 — Minimal PoC

Create self_debate_poc.py with:
- synthetic task generation or ingestion from verified benchmark cases
- controlled ground truth
- implementation of the debate protocol
- implementation of a judge
- computation of agreed primary metrics
- at least one visualization showing mechanism, not just score

Rules:
- one-command runnable
- hard-coded defaults are fine
- top-of-file comment block listing deliberate exclusions
- synthetic-only scope

### 3. Step 2 — Clarify intent and review code

Create README.md with:
- one-paragraph hypothesis statement
- quickstart command
- pipeline description
- expected outputs
- scope exclusions

Before changing design choices:
- explain the intent of each non-obvious choice
- flag possible errors
- ask whether each flagged item could be intentional

### 4. Step 3 — Adversarial critique

Dispatch the `ml-critic` agent via the Agent tool in **initial critique mode (Mode 1)**.

Provide it with: HYPOTHESIS.md, the PoC script, and README.md.

Instruct it to produce CRITIQUE.md structured as:
- One numbered issue per finding
- For each issue: the claim being made, why it might be wrong, what evidence would settle it
- Organized by root cause, not severity

Wait for CRITIQUE.md before proceeding.

### 5. Step 4 — Defense

Dispatch the `ml-defender` agent via the Agent tool in **initial defense mode (Mode 1)**.

Provide it with: HYPOTHESIS.md, the PoC script, README.md, AND CRITIQUE.md.
The Defender must receive the Critic's output — do not dispatch it with task materials only.

Instruct it to use the two-pass structure:
- Pass 1: write out full analysis for every critique point before assigning any verdicts
- Pass 2: assign verdicts only after completing Pass 1

Verdict calibration rule (include verbatim in dispatch):
"If your Pass 1 analysis identifies multiple critical unaddressed flaws, your overall
verdict must be empirical_test_agreed or critique_wins — not defense_wins. A defender
who correctly analyzes that a claim is invalid but labels it defense_wins has made a
reasoning-to-label translation error."

Wait for DEFENSE.md before proceeding.

### 6. Step 5 — Debate to resolution

Initialize DEBATE.md listing all contested points (points where CRITIQUE.md and
DEFENSE.md disagree).

Then alternate Agent tool dispatches of `ml-critic` and `ml-defender`, both in
**debate round mode (Mode 2)**:

1. Dispatch ml-critic with HYPOTHESIS.md, PoC script, README.md, CRITIQUE.md,
   DEFENSE.md, DEBATE.md. Instruct: "For each unresolved point: concede, sharpen
   your argument, or propose a specific empirical test. Append as: Critic — Round N."
2. Dispatch ml-defender with the same files. Instruct: "For each unresolved point:
   concede, rebut, or accept/modify the proposed empirical test. Append as:
   Defender — Round N."
3. After each round, check resolution status per point:
   - critique_wins — conceded by defender; mark resolved
   - defense_wins — conceded by critic; mark resolved
   - empirical_test_agreed — both sides agree on test condition; mark resolved
   - unresolved — dispatch another round
4. Repeat until all points are resolved or 4 rounds are reached.
5. Force-resolve any remaining unresolved points as "empirical_test_required."

At the end, extract the empirical test list: every point resolved as
empirical_test_agreed or force-resolved. Each entry must specify:
- What result means the critique was right
- What result means the defense was right
- What result is ambiguous

Nothing goes into the experiment unless it is on this list.
Always include the trivial baseline.

### 7. Step 6 — Design and run the experiment

Create self_debate_experiment2.py.

For each agreed empirical test, write down before running:
- what result means critique is right
- what result means defense is right
- what result is ambiguous

Implementation requirements:
- bootstrap confidence intervals (N = 1000, percentile method) on all primary metrics
- stratified analysis where relevant
- all methods and baselines on identical splits
- explicit verification that baselines test what they are supposed to test

### 8. Step 7 — Conclusions

Create CONCLUSIONS.md.

For each debate point requiring empirical resolution:
- restate what was agreed
- state what the evidence showed
- state which side was supported, or if neither was

Special handling:
- mark surprises explicitly
- explain which assumption the surprise broke
- explain whether the surprise changes the recommendation

Include figures, and let each figure illustrate one finding.

### 9. Step 8 — Final report

Create REPORT.md with:
1. Abstract
2. Introduction
3. Experiment design, results, and findings
4. Discussion
5. Conclusions and Recommendations

Write it as a self-contained report that can be read without consulting the intermediate artifacts.

### 10. Step 9 — Production re-evaluation

Create REPORT_ADDENDUM.md covering:
- retraining dynamics
- update latency
- operational complexity
- failure modes

If production constraints change the recommendation, state that clearly.

### 11. Final deliverable behavior

At the end of execution:
- summarize the original hypothesis and metrics
- summarize the main empirical findings
- provide concrete recommendations for when to trust or distrust the protocol
- provide an inventory of all generated artifacts

==================================================
PART 5 — LEAD EXECUTION PLAN
==================================================

LEAD, do this now in order:

1. Spawn all four teammates.
2. Send CASE_AUTHOR its instructions and ask for benchmark_cases.json.
3. Send CASE_VERIFIER its instructions and tell it to wait for benchmark_cases.json, then validate all cases.
4. Send EVALUATOR its instructions and ask for evaluation_rubric.json before any execution begins.
5. Send META_EXPERIMENT_RUNNER its instructions and tell it to wait for verified cases plus the fixed rubric before writing a plan.
6. When CASE_AUTHOR finishes, pass benchmark_cases.json to CASE_VERIFIER and EVALUATOR and META_EXPERIMENT_RUNNER.
7. When CASE_VERIFIER finishes, filter to KEEP cases only.
8. If fewer than 10 cases are KEEP, ask CASE_AUTHOR to revise the rejected/revise cases and repeat verification. Ensure at least 2 defense_wins cases survive verification — if fewer do, ask CASE_AUTHOR to revise the defense_wins cases specifically.
9. Once at least 10 KEEP cases exist (including at least 2 defense_wins), ask META_EXPERIMENT_RUNNER for the execution plan.
10. Review the plan against all approval rules.
11. Approve only if:
   - synthetic-only scope is preserved
   - explicit ground truth is preserved
   - trivial baseline is included
   - verdict criteria are pre-specified
   - only verified KEEP cases are used
12. After approval, instruct META_EXPERIMENT_RUNNER to execute and write all artifacts.
13. When execution is complete, send all artifacts plus the verified cases and rubric to EVALUATOR for scoring.
14. Ask EVALUATOR to produce evaluation_results.json.
15. Write FINAL_SYNTHESIS.md with:
   - what the benchmark tested
   - whether the critique/defense/debate loop worked
   - where it failed
   - whether it beat the trivial baseline
   - what should change in a second iteration
16. End by presenting the final artifact inventory.

Important:
- Do not skip waiting steps.
- Do not silently continue if a teammate has not completed its task.
- Do not let EVALUATOR alter the rubric after execution begins.
- Do not let META_EXPERIMENT_RUNNER use unverified cases.
- Prefer file-based artifacts over long chat summaries.
