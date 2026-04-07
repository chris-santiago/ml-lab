# Hypothesis — v4 Self-Debate Benchmark

## Primary Hypothesis

The isolated self-debate protocol (ml-critic + ml-defender each receiving only the task prompt, orchestrator adjudicates) will achieve a benchmark aggregate score at least **+0.10 higher** than a single-pass baseline on the fair-comparison dimensions (IDR, IDP, DRQ, FVC) — dimensions where baseline has equal structural agency.

**Mechanism:** Adversarial role separation forces engagement with both sides, producing better-typed verdicts and catching false positives that correlated parallel assessors miss.

---

## Conditions

| Condition | Description |
|-----------|-------------|
| `isolated_debate` | Critic and Defender each receive only `task_prompt`; orchestrator adjudicates |
| `multiround` | Defender sees Critique; up to 4 rounds; ml-lab protocol |
| `forced_multiround` | Same as multiround but minimum 2 rounds enforced; hard cases only |
| `ensemble` | 3 independent assessors + ETD-constrained synthesizer; compute-matched |
| `baseline` | Single-pass, no structure |

---

## Metrics

**Primary (fair-comparison set):** IDR, IDP, DRQ, FVC
- These are the dimensions where baseline has equal structural agency.
- Lift calculation uses fair-comparison dimensions only.

**Secondary (debate-internal):** DC, ETD
- Not used in lift calculation against baseline.
- Diagnostic only.

### N/A Rules (pre-registered)

| Dimension | Condition | Rationale |
|-----------|-----------|-----------|
| DC | baseline | No Defender role; penalizing its absence is not a valid comparison |
| ETD | ensemble, baseline | No adversarial exchange; no contested-point structure |
| DC | defense_wins cases | IDR/IDP also N/A per v3 convention |

---

## Secondary Hypotheses

1. Debate outperforms compute-matched ensemble on IDR/IDP/DRQ/FVC (fair-comparison dimensions).
2. Ensemble DC >= 0.5 on >= 60% of defense_wins cases (compute budget partially explains defense_wins advantage).
3. Forced multiround outperforms natural multiround on hard cases (additional exchange surfaces real signal when cases have genuine complexity).

---

## Convergence Metric (v4)

**Point resolution rate** = (points resolved by concession or empirical agreement) / (total contested points in DEBATE.md)

Extraction: count DEBATE.md entries with status `"Resolved: critic wins"`, `"Resolved: defender wins"`, or `"Resolved: empirical_test_agreed"` vs total contested points listed.

**Diagnostic only** — not used in pass/fail determination.
