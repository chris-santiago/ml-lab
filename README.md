# ml-debate-lab

This project asks a simple question: **when an AI evaluates a piece of work, does it actually catch real problems?**

The context is ML research — model results, statistical claims, deployment decisions. These are exactly the situations where evaluation matters most and where confident-sounding-but-wrong answers are most dangerous.

We built a controlled experiment to find out whether adding structure to AI evaluation — specifically, a debate between two independent agents — produces measurably better results than a single-pass assessment. Not "sounds more thorough." Measurably more correct verdicts, on cases where we already knew the right answer.

---

## The Setup

The system under test is a **self-debate protocol**: one agent plays Critic, one plays Defender, a Judge adjudicates. The key architectural choice is that Critic and Defender receive the same scenario with no shared context — each produces an independent assessment before either sees the other's output.

This isolation is not a technicality. It's what makes the disagreement meaningful. When both agents independently find the same flaw, you have convergent evidence. When they disagree, you have a genuinely contested claim that requires an empirical test to resolve — not a confident guess.

The comparison is a **trivial baseline**: one AI agent, one pass, no debate structure.

To make the comparison meaningful, we needed cases with known correct answers. We built a **benchmark of 20 synthetic ML reasoning scenarios**, each with a planted flaw (or deliberate absence of one), a ground-truth verdict, and specific issues the evaluation had to find. Examples:

- A team claiming a 4-point model improvement, evaluated on 1/10th the data with no confidence intervals
- A loyalty program reporting a 22% sales lift that launched November 1st — right before Black Friday
- A fine-tuned model beating zero-shot, with the team concluding their architecture is superior (the real cause: training regime difference)
- Methodologically *sound* work, presented under adversarial framing — to test whether the protocol would wrongly condemn it

Pass criteria were set before running anything: benchmark mean ≥ 0.65, ≥ 75% of cases pass, lift ≥ +0.10 over baseline.

---

## What We Found

**Debate protocol: 0.97 out of 1.0. Single-pass baseline: 0.38. Reported lift: +0.59.**

The threshold we set in advance to call the experiment a success was +0.10. We exceeded it by nearly 6×. 19 of 20 cases passed.

> **Post-experiment adversarial review (2026-04-04):** After running `ml-critic` and `ml-defender` against the experiment's own findings, two rubric design choices were found to mechanically depress the baseline score: DC hardcoded to 0.0 and DRQ capped at 0.5 for all baseline cases. The DRQ cap was confirmed binding on all 9 affected cases — the baseline correctly identified the resolution type in every case, but received no credit. The honest lift range, accounting for these rubric effects, is **+0.335 to +0.441**. The protocol still clears the +0.10 threshold by 3–4×, and the defense_wins finding is unaffected. See [`SENSITIVITY_ANALYSIS.md`](self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md) for full analysis and corrective actions taken.

The most interesting result came from five cases that were *false-positive critique traps* — valid work, correctly designed, presented under adversarial framing. The baseline scored **0.000** on all five. It accepted the adversarial premise and condemned work that was actually fine. The debate protocol got all five correct.

> **Ensemble follow-on (2026-04-04):** A clean compute-matched ensemble (3 independent assessors + synthesizer, task-prompt-only — no role separation, no coaching) scored 0.754 overall vs. debate's 0.970. The ensemble correctly exonerated valid work in **4/5 false-positive trap cases** without structural isolation — meeting the pre-specified criterion that "compute budget partially explains the defense_wins advantage." The isolation architecture is not uniquely necessary for exoneration. The debate protocol's remaining structural advantage is concentrated in *empirical test design* (ETD): the Critic/Defender adversarial forcing function generates agreed test specifications that a parallel ensemble never produces. See [`ENSEMBLE_ANALYSIS.md`](self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md) for full analysis.

One case failed: a healthcare triage scenario where the Defender correctly identified all the flaws in its reasoning but then labeled the verdict "the work is valid." Correct reasoning, wrong label. A calibration failure in output structure, not a reasoning failure — and fixable.

Full results, per-case scores, and conclusions are in [`self_debate_experiment_v2/`](self_debate_experiment_v2/).

---

## The Agent Under Test

The deeper object being evaluated here is the **`ml-lab` agent** — a Claude Code subagent that runs a structured 9-step ML hypothesis investigation workflow.

The workflow is designed for rigor over speed. Given a hypothesis, `ml-lab` first sharpens it into a falsifiable claim with agreed metrics, then builds a minimal runnable PoC. From there it branches into two adversarial subagents with distinct mandates:

- **`ml-critic`** — a skeptical ML engineer with an applied mathematics background. It reads the hypothesis and PoC cold and identifies every implicit claim the code makes but hasn't tested, organized by root cause. It is explicitly forbidden from critiquing code style or features the PoC declared out of scope.
- **`ml-defender`** — the original designer, arguing that the implementation is sound. It reads the critique and responds point-by-point: concede, rebut, or mark as empirically open. Fast concession on a real problem is valued over protracted defense.

`ml-lab` then orchestrates a multi-round debate between them, alternating dispatches until each contested point resolves — either one side concedes, or both agree on an exact empirical test with pre-specified success and failure conditions. Only tests on that agreed list go into the experiment. If findings are surprising enough to falsify a debate assumption, the whole cycle reopens: `ml-critic` and `ml-defender` are dispatched again in evidence-informed mode, with experimental results in hand. The investigation closes with a self-contained report and a production re-evaluation that checks whether the experimental recommendation survives operational constraints.

The self-debate protocol was chosen as the domain for a specific reason: it's testable. Unlike most ML research questions, we can construct scenarios with known correct answers and measure whether the agent found the right one. This makes it possible to ask not just "did `ml-lab` follow the process?" but "did following the process actually produce correct verdicts?"

The self-debate experiment is, in that sense, `ml-lab` investigating itself — the protocol is both the tool and the subject.

---

## How the Experiment Was Built

The experiment ran in two phases.

**Phase 1** (`self_debate_experiment/`) established the protocol and tested a first version of the benchmark. This phase was orchestrated entirely by a multi-agent team — a Lead coordinating four specialized agents: CASE_AUTHOR (created benchmark cases), CASE_VERIFIER (validated them), META_EXPERIMENT_RUNNER (executed the workflow and wrote all artifacts), and EVALUATOR (scored outputs against a fixed rubric defined before execution). The orchestration prompt is in [`multi-agent-prompt.md`](multi-agent-prompt.md).

One important detail: in Phase 1, the debate transcripts were generated by Claude agents during the authoring session, then embedded as hardcoded data in the Python scripts. Re-running the script replays static text — it doesn't re-invoke the LLM. This was intentional: the point was to build and score the protocol, not to build a live inference pipeline.

Phase 1 identified two open problems. First, a rubric gap: `issue_discovery_precision` was undefined for cases where the Critique's premise was intentionally false — you can't measure "fraction of valid claims" when all claims are supposed to be invalid. Second, the contaminated protocol (Defense reads Critique before responding) made genuine `defense_wins` verdicts structurally impossible.

**Phase 2** (`self_debate_experiment_v2/`) fixed both. The rubric was extended with a redefined IDP dimension for `defense_wins` cases. The Defense was fully isolated — it receives only the original scenario, never the Critic's output. And critically, Phase 2's transcripts were generated through the full `ml-lab` workflow: each agent role (Critique, Defense, Judge, Scorer, Baseline) was dispatched as an isolated subagent via Claude Code, producing genuinely independent outputs before they were embedded in the script. This directly tested whether the structured investigation process produced correct verdicts when run end-to-end. It did, and then some.

For the full experimental design, scoring rubric, and benchmark case descriptions, see [`self_debate_experiment_v2/README.md`](self_debate_experiment_v2/README.md).

---

## Why This Matters

The standard approach to AI evaluation is single-pass: give a model some work, ask it what it thinks, get an answer. This works when the flaw is obvious. It breaks down when:

- The flaw requires independently questioning the framing
- The work is actually valid but sounds questionable  
- The correct answer is "we need to run an empirical test first" rather than a binary yes/no

Debate adds something single-pass cannot. The clearest illustration is the false-positive trap cases: the single-pass baseline scored 0.000 on all five exoneration cases, inheriting the adversarial framing entirely. The clean ensemble follow-on (4 independent assessors in parallel, no roles) correctly exonerated 4/5 cases — suggesting that multiple independent views can also counter framing bias, though with lower precision than the structurally isolated Defender. The debate protocol's clearest structural advantage is not exoneration per se, but *forcing specification of empirical tests* when positions diverge: the adversarial dynamic between Critic and Defender requires both to agree on what experiment would resolve the question, which parallel assessors never need to do.

---

## Running the Experiment

Both Phase 1 and Phase 2 scripts score pre-embedded transcripts — no API key or external calls required at runtime. The transcripts were generated during the investigation sessions (via Claude Code agent dispatches) and baked into the scripts. Running the scripts just scores them and writes results JSON.

**Phase 2:**

```bash
cd self_debate_experiment_v2/
python self_debate_poc.py
```

Produces `self_debate_results.json`.

**Phase 1:**

```bash
cd self_debate_experiment/
python self_debate_poc.py       # Experiment 1: contaminated protocol, 11 cases
python self_debate_experiment2.py  # Experiment 2: isolated protocol, 15 cases
```

Standard library only. No dependencies beyond Python 3.8+.

**Running the full multi-agent harness from scratch:**

The bootstrap prompt in [`multi-agent-prompt.md`](multi-agent-prompt.md) will recreate the entire Phase 1 experiment using a team of Claude Code agents. Requires agent teams enabled:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude --teammate-mode in-process
```

Then paste the contents of `multi-agent-prompt.md` as your first message.

---

## An Example Run

To validate that `ml-lab` correctly navigates the full iteration stack — not just the happy path — we ran it on a fraud detection hypothesis:

> *"An LSTM on ordered transaction category sequences outperforms a bag-of-categories baseline because fraud exhibits characteristic temporal patterns."*

The run exercised every major feature of the workflow.

Steps 1–2 produced a clean PoC with AP = 0.96 against 0.05 prevalence — a strong-looking result. The critic identified four issues; the defender conceded three and marked one as empirically open. One debate round resolved the contested point into a three-condition experiment design (ordered LSTM, count-vector LR, equalized-distribution LSTM). Pre-specified verdicts were written before any experiment ran.

The experiment returned mixed results: the randomized-phases test showed the critique was right (AP dropped from 0.96 to 0.68 — phase position was signal, not sequence structure). The ordered vs. bag-of-categories comparison went to the defense. Then Condition C returned AP = 1.00.

The near-perfect metrics suspicion trigger fired immediately. The agent investigated, found that `sort()` was making sequences trivially detectable, and redesigned Condition C with soft-sort (Gaussian noise on ranks). The redesigned condition returned AP = 0.996 — still suspicious.

This is where the spec's escalation logic was put to the test. Rather than accepting the second result or spinning into more micro-iterations, the agent correctly identified that the equalized-distribution test is *fundamentally broken for synthetic data*: any imposed ordering is trivially distinguishable from random sequences because LSTMs detect sequential structure. This isn't a fixable design flaw — it's a hypothesis-level problem.

The macro-iteration Outcome C trigger fired: the experiment wasn't measuring the wrong *thing*, it was testing the wrong *question*. The hypothesis was reformulated:

> *"Fraud accounts exhibit a specific temporal signature (low-value test transactions → rapid category switching → high-value extraction) that is distinguishable from both random ordering and generic monotonic trends."*

The most important result from this run isn't the fraud finding — it's that the spec handled the full escalation without any additional guidance: micro-iteration (fix Condition C), second micro-iteration (still broken), escalation to macro-iteration (hypothesis needs reformulation). The distinction between a fixable experimental flaw and a hypothesis-level problem was load-bearing, and the agent navigated it correctly.

Full trace and spec validation notes are in [`seq_fraud_experiment/TEST2_FINDINGS.md`](seq_fraud_experiment/TEST2_FINDINGS.md).

---

## Artifact Index

| Location | Contents |
|----------|----------|
| [`agents/`](agents/) | Reference copies of ml-lab, ml-critic, and ml-defender agent definitions |
| [`agents/README.md`](agents/README.md) | Installation instructions and agent interaction diagram |
| [`multi-agent-prompt.md`](multi-agent-prompt.md) | Bootstrap prompt for the full multi-agent harness |
| [`self_debate_experiment/`](self_debate_experiment/) | Phase 1: frozen transcripts, contaminated + isolated protocol, 11–15 cases |
| [`self_debate_experiment_v2/`](self_debate_experiment_v2/) | Phase 2: live API, isolated protocol, 20 cases, full results |
| [`self_debate_experiment_v2/README.md`](self_debate_experiment_v2/README.md) | Full experimental design, rubric, benchmark case breakdown |
| [`self_debate_experiment_v2/CONCLUSIONS.md`](self_debate_experiment_v2/CONCLUSIONS.md) | Per-case scores and findings |
| [`self_debate_experiment_v2/REPORT.md`](self_debate_experiment_v2/REPORT.md) | Full technical report |
| [`self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md`](self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md) | Post-experiment adversarial review: rubric design effects on reported lift |
| [`self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md`](self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md) | Compute-matched ensemble baseline results: flawed run, clean re-run, defense_wins isolation test resolution |
| [`self_debate_experiment_v2/ensemble_results.json`](self_debate_experiment_v2/ensemble_results.json) | Per-case ensemble scores — contaminated run (coaching artifacts; see contamination_flag fields) |
| [`self_debate_experiment_v2/clean_ensemble_results.json`](self_debate_experiment_v2/clean_ensemble_results.json) | Per-case ensemble scores — clean two-phase run (no coaching; Phase 1 task-prompt-only) |
| [`self_debate_experiment_v2/ELEVATOR_PITCH.md`](self_debate_experiment_v2/ELEVATOR_PITCH.md) | Non-technical summary of results |
| [`seq_fraud_experiment/HYPOTHESIS.md`](seq_fraud_experiment/HYPOTHESIS.md) | Hypothesis and metrics for the sequence fraud investigation |
| [`seq_fraud_experiment/TEST2_FINDINGS.md`](seq_fraud_experiment/TEST2_FINDINGS.md) | Full trace and spec validation notes for the example run |
