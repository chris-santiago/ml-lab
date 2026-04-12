# ml-lab Protocol: Recommended Changes Based on v6 Results

**Date:** 2026-04-11
**Source:** self_debate_experiment_v6 full results synthesis

---

## The Core Finding

The central result is architectural: **adversarial structure ≠ better analysis for regular cases**. Three independent critics with union pooling beat one structured debate at matched compute on every metric that matters. The debate structure routes the same perspective through argument mechanics instead of adding new perspectives.

But for **empirically ambiguous cases**, debate does add something baseline can't: iterative exchange pushes agents to recognize when a verdict can't be made without more evidence. That's a structurally different mode of value.

This means ml-lab needs two paths, not one.

---

## Recommended Protocol Changes

### 1. Replace isolated_debate with ensemble_3x for all standard reviews

This is the only formally supported change with CI excluding zero in the right direction.

| | IDR | IDP | FC |
|---|---|---|---|
| isolated_debate (current) | 0.6603 | 0.9250 | 0.6759 |
| **ensemble_3x (recommended)** | **0.7717** | **0.9861** | **0.7046** |
| Gain | +0.1114 | +0.0611 | +0.0287 |

**What changes operationally:**
- Drop the critic→defender→adjudicator dispatch chain
- Run ml-critic three times independently on the same case
- Pool issues using union (any-assessor-found = credit); majority-vote for final verdict
- Same compute budget (3×), better output

The intuition: the defender's job is to push back on the critic's claims. But if the critic already found all the real issues, pushback just suppresses them. Three independent critics find different issues from different angles — none of them suppress each other.

---

### 2. Route empirically ambiguous cases to multiround, not ensemble

This is where the adversarial structure earns its keep:

| Condition | FVC_mixed |
|---|---|
| baseline | 0.00 |
| isolated_debate | 0.0083 |
| ensemble_3x | 0.025 |
| biased_debate | 0.25 |
| **multiround** | **0.3667** |

Baseline and ensemble both score near 0 on mixed cases — they make a verdict and move on. Multiround iterative exchange pushes agents toward `empirical_test_agreed` outcomes in ~37% of cases.

**Before deploying multiround:** the variance problem must be solved. 20 of 23 high-variance case-condition pairs are multiround — the same case can flip between FC=0.0 and FC=1.0 across runs. This means temperature reduction or a stricter adjudicator stopping checklist is needed first.

---

### 3. Retire isolated_debate as a general-purpose path

The cost-benefit table is unambiguous:

| Protocol | Compute | IDR | Verdict |
|---|---|---|---|
| baseline | 1× | 0.6712 | minimum viable |
| **isolated_debate** | **3×** | **0.6603** | **worse than baseline at 3× cost** |
| ensemble_3x | 3× | 0.7717 | recommended |

Isolated debate is strictly dominated by ensemble_3x at the same compute and dominated by baseline at lower cost. There is no use case it wins.

---

### 4. Fix or remove the CFM gate

The gate fires on 94.7% of cases — it's not a gate, it's a formality. The PRR threshold (currently PRR=1.0 to stop) is never met because mean PRR after round 1 is only 0.418. Two options:

- **Lower the threshold:** PRR ≥ 0.7 would stop on cases where most issues are resolved
- **Remove it entirely:** Run full multiround when multiround is warranted; don't add conditional complexity that doesn't save compute

---

### 5. Redesign ETD before it can be used as a metric

ETD=1.0 for 100% of debate outputs — the scorer can't distinguish between a well-designed empirical test and a vague one. Until a sub-element rubric exists (specificity of condition, falsifiability of the `supports_critique_if` branch, orthogonality of the two branches), ETD is unmeasurable.

---

### 6. Acknowledge the defense case failure

Every condition scores DRQ=FVC=0.0 on defense cases uniformly. This isn't a debate structure problem — it's that the current critic prompt is not calibrated to ever exonerate. The ml-critic always finds issues. A "no significant methodological issues identified" output path doesn't exist in the current protocol. This needs an explicit prompt redesign before defense cases can be used as benchmark cases.

---

## Revised ml-lab Architecture

```
Input case
    │
    ├─► Regular methodology review
    │       └─► ensemble_3x: 3× ml-critic → union IDR pool → majority-vote verdict
    │
    └─► Empirically ambiguous / mixed
            └─► multiround debate: ml-critic → ml-defender → adjudicator → round 2
                (post-stabilization: lower temperature, structured stopping criterion)
```

The critic/defender/adjudicator structure isn't wrong — it's right for exactly one scenario: when the question is whether a methodology is testable, not whether it's flawed. That's a smaller but still real use case.

---

## v7 Priority Order

1. **Stabilize multiround** — the FVC_mixed=0.3667 signal is the most actionable positive result across all experiments
2. ~~**Formal ensemble vs. baseline test**~~ — **DONE** (`ensemble_vs_baseline_test.py`): ensemble_3x > baseline on IDR, observed diff=+0.1005, 95% CI=[+0.0426, +0.1648], p=0.0000 (n=60 critique cases). Both ends of the recommendation are now formally grounded.
3. **Full difficulty labeling** — only 15/80 regular cases are labeled; H3 is chronically underpowered and can't be evaluated properly
4. **ETD sub-element rubric** — required before mixed-case quality is quantifiable
5. **Defense case exoneration path** — 0.0 across all conditions is a structural gap, not noise
