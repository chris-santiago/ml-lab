# Does Debate Between AI Agents Get Us Closer to the Truth?

## The Question

When an AI evaluates a piece of work — a model result, a statistical claim, a deployment decision — can it actually catch real problems? And does adding a second AI to argue the other side make it better, or is it just more words?

We built an experiment to find out.

---

## What We Did

We created 20 synthetic ML scenarios with *known correct answers* — cases like:

- A team claiming their model improved by 4 points, but evaluated on 1/10th the data with no confidence intervals
- A loyalty program showing a 22% sales lift that launched on November 1st (right before Black Friday)
- A fine-tuned model beating a zero-shot model, with the team concluding their architecture is superior
- Methodologically *sound* work, presented under adversarial conditions, to test whether the system would wrongly condemn it

Each case had a planted flaw (or deliberate absence of one), a ground-truth correct verdict, and specific issues the evaluation had to find.

We ran three conditions against every case:

**Debate condition:** Two AI agents receive the same scenario with no shared context. One plays Critic, one plays Defender. Each produces an independent assessment. A Judge adjudicates and assigns a typed verdict: *critique wins*, *defense wins*, or *run an empirical test*.

**Compute-matched ensemble:** Three independent assessors plus a synthesizer — same total compute as the debate, but no role differentiation. Everyone sees the same scenario; no one is assigned to argue a position.

**Baseline condition:** One AI agent, one pass, no debate structure.

---

## What We Found

The debate protocol scored **0.97 out of 1.0** on average. The single-pass baseline scored **0.38**.

The raw gap is **+0.59**, but two rubric choices mechanically penalize the baseline (defense calibration hardcoded to 0.0, reasoning quality capped at 0.5 for single-pass). The honest corrected lift — stripping those structural penalties — is **+0.335 to +0.441**. That's still 3–4× the threshold we set in advance (+0.10) to call the experiment a success.

19 of 20 cases passed.

To understand where the lift actually comes from, we ran a third condition: a compute-matched ensemble — three independent assessors and a synthesizer, no role differentiation. It scored **0.75**. That puts the full picture in view:

| Condition | Score | What it measures |
|-----------|-------|-----------------|
| Single-pass baseline | 0.38 | One agent, one call — the floor |
| Compute-matched ensemble | 0.75 | What more compute alone buys |
| Debate protocol | 0.97 | What adversarial role separation adds on top |

The gap from floor to ensemble (+0.37) is mostly more compute and more perspectives. The gap from ensemble to debate (+0.22, statistically significant at p=0.004) is what the Critic/Defender structure specifically adds.

---

## The Most Interesting Finding

Five of the 20 cases were *false-positive critique traps* — methodologically sound work deliberately presented under adversarial framing, to test whether the protocol would wrongly flag valid results.

The single-pass baseline scored **0.000** on all five. It accepted the adversarial framing, treated the planted critique as valid, and condemned work that was actually fine.

The debate protocol got all five correct. The compute-matched ensemble got **4 of 5** — an improvement over baseline, but it raised caveats alongside two of its correct exonerations ("this looks valid, *but*..."). The debate protocol's isolated Defender produced three clean, no-caveat exonerations.

So debate is not the *only* way to exonerate valid work — more compute and more perspectives gets most of the way there. What the Defender's structural isolation adds is a voice that is *required* to argue for the work, producing cleaner "no issues" verdicts rather than hedged ones. The 5/5 vs. 4/5 distinction is real in the data, but the sample is too small to confirm it statistically. Treat it as a directional finding, not a proven structural advantage.

---

## Where It Failed

One case failed: a healthcare triage scenario where the Defender *correctly identified all the flaws in its own analysis text* but then labeled its verdict "the work is valid." The reasoning was right; the label was wrong. This is a calibration failure in the Defender's output structure, not a reasoning failure — and it's fixable.

Two cases showed the Defender being overly cautious: it correctly identified why the work was sound but hedged toward "needs more testing" rather than committing to "this is fine." Both cases still passed, but the under-confidence is a real pattern.

---

## Why This Matters

The standard approach to AI evaluation is single-pass: give a model some work, ask it what it thinks, get an answer. This works when the flaw is obvious. It fails when:

- The flaw requires independently questioning the framing
- The work is actually valid but sounds questionable
- The correct answer is "we need to test X first" rather than a yes/no

Debate adds something single-pass cannot: an independent second opinion with no access to the first. The context isolation is not a technicality — it's what makes the disagreement meaningful. When both agents independently find the same flaw, you have convergent evidence. When they disagree, you have a genuinely contested claim that requires an experiment to resolve.

---

## The Setup in Brief

- **20 benchmark cases**, 6 categories (broken baselines, metric mismatches, hidden confounders, scope misunderstandings, false-positive traps, real-world deployment framing)
- **Three conditions**: debate protocol, compute-matched ensemble, single-pass baseline
- **Scoring rubric** defined before running the experiment: issue discovery, defense calibration, verdict quality, empirical test design, final verdict correctness
- **Full context isolation** between agents — no shared outputs before independent assessments
- **Known ground truth** for every case, so "better" has a definite answer
- **Benchmark pass criteria** set in advance: mean ≥ 0.65, ≥ 75% of cases pass, lift ≥ +0.10

All three criteria passed.

---

## What Debate Actually Does (and Doesn't)

Post-experiment ablations refined what the +0.22 advantage over the ensemble actually reflects.

**Not uniquely from debate:**
- *Empirical test design* — the debate protocol reliably specifies what experiment to run next. We originally thought this came from adversarial forcing. It doesn't. Adding one explicit instruction to the ensemble synthesizer ("specify the test with pre-specified success and failure criteria") achieved the same result. Test design is a prompt effect, portable to any configuration.

**From debate:**
- *Point-by-point argumentation.* The Critic/Defender structure forces every claim to be conceded, rebutted, or flagged as empirically open — with IDs. A synthesizing ensemble can't produce this by design.
- *Cleaner exonerations* *(directional, internal only).* When the Defender never sees the Critique, its defense of valid work is structurally independent — not a reaction to the Critic's framing. This produces more confident "no issues" verdicts. Three of five exonerations in the debate condition were clean; the ensemble hedged on two of its four correct ones. Note: the external benchmark confirms that debate *passes* exoneration cases (3/3), but does not confirm the clean/hedged distinction — critics raised plausible-but-wrong concerns (IDP=0.5) on all 3 external cases, the same pattern as internal IDP-stress cases.

---

## External Validation

The synthetic benchmark could have been too easy or too tailored. We checked.

**External fault detection (10 cases):** Cases drawn from published ML evaluation failures (Dacrema 2019, Obermeyer 2019, DeGrave 2021, and others) — ground truth from the published record, not the experiment designer. The debate protocol achieved IDR = 0.95 on these cases, meeting the pre-specified ≥ 0.85 threshold.

**External exoneration (3 cases):** Cases from peer-reviewed ML work (BERT/SQuAD 1.1, ResNet-152/ImageNet, clinical 5-fold CV) where a critique *could* be raised but the methodology is genuinely sound. Debate protocol passed all 3 (mean 0.875). Baseline reached correct verdict labels in all 3 but scored 0/3 on the rubric (the DC structural rule). The exoneration finding holds on externally grounded cases.

---

## Bottom Line

When AI agents debate with genuinely isolated context, the result is substantially better than a single-pass assessment — not because debate sounds more thorough, but because it produces measurably more correct verdicts on cases where we already know the right answer.

The honest version: most of the lift comes from more compute and more perspectives. The adversarial structure specifically adds point-by-point argumentation and — on the internal benchmark — a tendency toward cleaner exonerations (not confirmed in the external benchmark). The empirical test design output is a bonus that's portable to simpler configurations via a single prompt instruction.

The biggest gains are exactly where you'd want them: catching hidden confounders, refusing to condemn valid work, and forcing contested claims into the right kind of empirical resolution rather than a confident-sounding guess.
