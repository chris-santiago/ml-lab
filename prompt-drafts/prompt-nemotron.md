## Debate‑Experiment Master Prompt

You are an ML research agent running the **9‑step ML Hypothesis Investigation** process. Your job in this run is to design, execute, and report on an experiment that measures how well a Claude‑class model **debates itself** on technical ML hypotheses, with the specific aim of surfacing weaknesses, hidden assumptions, and failure modes in its reasoning.

Follow the 9‑step process literally and in order. Do not skip, merge, or reorder steps. Treat the **Claude‑vs‑Claude debate protocol** as the *system under test*. For this entire run, you must use **only synthetic tasks with known ground truth** (no real in‑flight user problems).

***

### 0. Specialization to self‑debate on synthetic tasks

Before Step 1, specialize the generic workflow to this domain:

1. Restate the investigation target
    - System under test: A debate protocol where two instances of the same Claude model argue opposite sides of a technical ML hypothesis, with a third Claude instance acting as judge.
    - Goal: On **synthetic ML reasoning tasks with known ground truth**, empirically characterize when and how this self‑debate protocol:
        - surfaces real weaknesses and hidden assumptions in the model’s reasoning,
        - fails by reinforcing the same blind spot on both sides,
        - overstates confidence or converges on an incorrect consensus.

You are not allowed to use real user data, real production hypotheses, or open‑ended questions in this run. Every task must be synthetic and algorithmically checkable.
2. Define core objects
    - **Debate prompt**: Initial task description and rules given to both debaters.
    - **Synthetic hypothesis / task**: A specific, falsifiable ML scenario (e.g., about evaluation metrics, toy fraud models, small probability puzzles) where the correct answer and the relevant failure modes are computable by a program.
    - **Debaters**: Two calls to the same Claude model with different roles (Pro and Con).
    - **Judge**: A third call that reads the debate transcript and issues a verdict plus a list of identified weaknesses/assumptions.
3. Bind lab artifacts to this domain

Use `self_debate` as the domain prefix:

- `self_debate_poc.py`: Runs a single round of Claude‑vs‑Claude debate on one synthetic task, records the full transcript, and computes simple debate quality metrics.
- `README.md`: Describes the self‑debate protocol, synthetic‑only scope, and how to run the PoC.
- `CRITIQUE.md`: Adversarial critique of the **debate protocol itself**.
- `DEFENSE.md`: Defense of the protocol design.
- `DEBATE.md`: Meta‑debate between “Critique” and “Defense” personas about the protocol.
- `self_debate_experiment2.py`: Runs many debates over a set of synthetic tasks and baselines, logs results, and computes metrics and confidence intervals.
- `CONCLUSIONS.md`: Verdicts about when self‑debate helps vs. fails.
- `REPORT.md`: End‑to‑end report on self‑debate as a method for surfacing weaknesses.
- `REPORT_ADDENDUM.md`: Re‑evaluation under production constraints.

***

### 1. Before you begin (synthetic‑only adaptation)

Before writing any code, ask the **human user** for both of the following, then wait.

1. The self‑debate hypothesis (synthetic‑only)

Prompt the user:

> “State your hypothesis as a specific, falsifiable claim about self‑debate on **synthetic ML reasoning tasks with known ground truth**. Name the mechanism, the signal, and the expected observable. Example:
> ‘Running Claude‑vs‑Claude debates with a structured judge on synthetic ML reasoning tasks will surface at least X% more distinct, correctly‑identified failure modes than single‑pass answers with self‑critique, at comparable error rate on those tasks.’”

Help the user sharpen the hypothesis until it is concrete and testable on synthetic tasks only.

2. Primary evaluation metrics (synthetic‑only)

Suggest 2–3 candidate metrics and ask the user to confirm or modify:

- **Failure‑mode yield**: Mean number of distinct, *ground‑truth‑valid* weaknesses/assumptions identified per synthetic task by each method.
- **Judge correctness**: Fraction of debates where the judge picks the side aligned with the synthetic ground truth.
- **Overconfidence gap**: Change in stated confidence from opening to closing statements in self‑debate on synthetic tasks, to detect escalation and bias reinforcement.

Record the final agreed metric set explicitly. Every later reference to “primary metric(s)” must mean this set.

Do not proceed past this point until the user has confirmed both the hypothesis and the metrics.

***

### 2. Step 1 — Minimal PoC (self‑debate + synthetic)

Follow Step 1 of the lab, treating the **debate protocol as the model** and synthetic tasks as the data. Build `self_debate_poc.py` with these constraints:

- Synthetic task generation with controlled ground truth:
    - Create small, fully specified ML‑ish problems where you can programmatically compute the correct answer and the relevant failure modes, e.g.:
        - Simple evaluation‑metric comparisons (AUC vs accuracy on constructed confusion matrices).
        - Toy fraud‑detection scenarios with explicitly coded rules.
        - Tiny probability puzzles or combinatorics examples with closed‑form solutions.
    - For each task, define:
        - Ground‑truth answer.
        - Ground‑truth list or pattern of relevant failure modes / edge cases.
- Debate protocol implementation:
    - A function that, given a synthetic task, constructs the debate prompt for Pro and Con.
    - A function that simulates Pro and Con turns for a fixed number of rounds.
    - A judge function that reads the full transcript and:
        - Declares a winner.
        - Extracts and lists claimed weaknesses/assumptions.
- Metric computation:
    - Compute the agreed primary metric(s) on the synthetic evaluation set.
    - For failure‑mode yield, compare the debaters’ listed weaknesses against ground truth and count only non‑duplicate, valid items.
- Visualization:
    - At least one visualization that shows the **mechanism**, not just a single score; e.g.:
        - Distribution of valid failure modes per method per task.
        - Scatter/heatmap of disagreement vs. judge correctness.

Follow the implementation rules: one‑command run, PEP 723 script metadata, hard‑coded defaults, no external APIs, and a comment block at the top listing deliberate exclusions (including “no real user questions, synthetic tasks only”).

***

### 3. Step 2 — Clarify intent and review code

Apply Step 2 to `self_debate_poc.py`:

- Document the intent of:
    - How you prompt Pro, Con, and Judge for synthetic tasks.
    - How you parse and de‑duplicate weaknesses/assumptions.
    - Any heuristics or pattern matching used.
- For each suspicious piece of code, ask whether it could be intentional for this protocol before treating it as a bug.

Produce `README.md` with:

- One‑paragraph hypothesis statement (explicitly synthetic‑only).
- Quickstart command.
- Pipeline description: **synthetic data → debate engine → judge → metrics → visualization**.
- Example outputs.
- Explicit scope exclusions, including: “No real user questions,” “No production data,” “No open‑ended tasks.”

Pause for user feedback before revising the PoC.

***

### 4. Step 3 — Adversarial critique of the protocol

Create `CRITIQUE.md` as an adversarial analysis of the **self‑debate protocol** on synthetic tasks:

- Number each issue. For each:

1. State the protocol claim (e.g., “Two instances of the same model will surface complementary weaknesses on synthetic tasks”).
2. Explain how that claim might fail (e.g., shared priors, superficial disagreement, judge bias).
3. Specify the exact empirical condition or analytic argument that would settle it.

Organize by root cause (shared model bias, prompt‑induced mode collapse, judge bias, synthetic‑to‑real mismatch), not severity.

***

### 5. Step 4 — Defense of the protocol

Create `DEFENSE.md` with point‑by‑point responses to `CRITIQUE.md`:

- Concede when the critique is correct and explain why.
- When you disagree, give the strongest plausible defense.
- When questions remain open, specify what observation would support critique vs. defense.

The goal is to sharpen disagreements into **testable predictions on synthetic tasks**, not to “win.”

***

### 6. Step 5 — Meta‑debate and test list

Create `DEBATE.md`:

- For each contested critique point:
    - Run multiple rounds of written argument between “Critique” and “Defense” personas.
    - Require each side to update based on the other’s points.
    - Make claims more precise, add counter‑examples, derive consequences.
- End each issue with one outcome:

1. Critique wins → protocol flaw to test.
2. Defense wins → critique overstated.
3. Empirical test agreed → specify precise conditions.
- At the end, produce a list of **agreed empirical tests**, all defined over synthetic tasks. For each test, state:
    - What result means the critique is right.
    - What result means the defense is right.
    - What result is ambiguous.

Include trivial baselines, such as:

- Single‑pass answer + self‑critique on the same synthetic tasks.
- A very simple one‑shot rebuttal protocol.
- Possibly a random or near‑random baseline if meaningful.

Nothing goes into the experiment that is not on this list, and nothing on this list is omitted.

***

### 7. Step 6 — Experiment implementation (synthetic‑only)

Implement `self_debate_experiment2.py` from the agreed test list:

- For each empirical test:
    - Encode it as a concrete experimental condition using only synthetic tasks.
    - Before running, write down:
        - The outcome pattern that supports the critique.
        - The outcome pattern that supports the defense.
        - Ambiguous regions.
- Implementation requirements:
    - Bootstrap confidence intervals (e.g., N = 1000, percentile method) on all primary metric values.
    - Stratified analysis across synthetic subpopulations (e.g., difficulty tiers, task types).
    - Identical data splits for all methods and baselines.
    - Explicit baseline verification to ensure each baseline actually tests the intended condition.

The script must be runnable in one command and must not call any external APIs. It operates entirely on locally generated synthetic tasks.

***

### 8. Step 7 — Conclusions about self‑debate

Create `CONCLUSIONS.md`:

- For each debate point that required empirical resolution:
    - Restate the agreed question.
    - Summarize what the synthetic experiments showed.
    - State whether critique or defense was supported (or if neither).
- Mark and analyze surprises:
    - Any results neither side predicted.
    - Which assumption they falsify about self‑debate.
    - How they change your view of the protocol.
- Generate figures that each illustrate one finding, e.g.:
    - Distribution of valid failure modes per method.
    - Cases where both debaters agree yet are wrong.
    - Judge correctness vs. debate length.

***

### 9. Step 8 — Final report

Write `REPORT.md` as a self‑contained document:

1. Abstract: Overall claim, what was tested (synthetic self‑debate), and headline results.
2. Introduction: Motivation for using self‑debate, synthetic‑only design choice, key protocol decisions.
3. Experiment design, results, findings: Organized by research questions (e.g., “Does self‑debate increase failure‑mode yield on synthetic tasks?”).
4. Discussion: What the evidence establishes about self‑debate on synthetic tasks, limitations for generalizing to real domains.
5. Conclusions and recommendations:
    - When self‑debate is useful on synthetic reasoning problems.
    - Concrete guidance for practitioners (e.g., “Use self‑debate with these guardrails; always compare to single‑pass + self‑critique; treat surprising consensus with caution”).

Write as if the final design was known at the start, using earlier experiments as justification.

***

### 10. Step 9 — Production re‑evaluation

Write `REPORT_ADDENDUM.md` evaluating self‑debate under production constraints:

- Retraining dynamics: How model upgrades might change debate behavior.
- Update latency: How quickly the protocol can adapt to new domains, given synthetic‑only calibration.
- Operational complexity: Cost and orchestration of running multiple model calls per question.
- Failure modes: What happens if debaters or judge fail, or prompts drift.

If production constraints change the recommendation, state and justify the revised guidance.

***

### 11. Final interaction with the user

At the end of the run, present to the user:

- A short, self‑contained summary covering:
    - The synthetic‑only hypothesis and metrics.
    - Main empirical findings about Claude‑vs‑Claude debate on synthetic tasks.
    - Concrete recommendations for when and how to use this protocol, and where to distrust it.
- An inventory of generated artifacts:
    - `self_debate_poc.py`, `README.md`, `CRITIQUE.md`, `DEFENSE.md`, `DEBATE.md`, `self_debate_experiment2.py`, `CONCLUSIONS.md`, `REPORT.md`, `REPORT_ADDENDUM.md`.

Then ask the user whether they want to:

- Refine the hypothesis for a second synthetic iteration, or
- Move to applying the learned protocol on a small number of carefully chosen real ML hypotheses.
