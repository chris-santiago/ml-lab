# ml-lab Protocol: Recommended Changes Based on v6 Results

**Date:** 2026-04-11 (updated 2026-04-12)
**Source:** self_debate_experiment_v6 full results synthesis + post-session analysis

---

## The Core Finding

The central result is architectural: **adversarial structure ≠ better analysis for regular cases**. Three independent critics with union pooling beat one structured debate at matched compute on every metric that matters. The debate structure routes the same perspective through argument mechanics instead of adding new perspectives.

But for **empirically ambiguous cases**, debate does add something baseline can't: iterative exchange pushes agents to recognize when a verdict can't be made without more evidence. That's a structurally different mode of value.

This means ml-lab needs two paths, not one.

---

## Formal Test Results (all using paired bootstrap, n=10,000, seed=42)

The recommendation chain is fully closed — every comparison is now formally grounded, not descriptive.

| Comparison | n | Observed diff | 95% CI | Verdict |
|---|---|---|---|---|
| ensemble_3x > baseline (IDR) | 60 critique | +0.1005 | [+0.0426, +0.1648] | **PASS** |
| ensemble_3x > isolated_debate (FC) | 80 regular | +0.0287 | [+0.0154, +0.0434] | **PASS** (v6 H2) |
| baseline vs isolated_debate (FC) | 80 regular | −0.0026 | [−0.0108, +0.0059] | **INDISTINGUISHABLE** (v6 H1a) |

**Key implication of the three-way ordering:**
The ranking is `ensemble_3x > {baseline ≈ isolated_debate}`. Isolated debate and baseline are statistically equivalent (H1a CI spans zero), meaning the debate structure spends 3× compute to match a single-pass baseline. Ensemble spends the same 3× and formally outperforms baseline. There is no statistical regime where isolated_debate wins.

Scripts: `ensemble_vs_baseline_test.py` (new), `v6_analysis.py` (H1a, H2)

---

## Recommended Protocol Changes

### 1. Replace isolated_debate with ensemble_3x for all standard reviews

Formally supported at both ends: ensemble > baseline and ensemble > isolated_debate.

| | IDR | IDP | FC |
|---|---|---|---|
| isolated_debate (current) | 0.6603 | 0.9250 | 0.6759 |
| baseline | 0.6712 | 0.9472 | 0.6785 |
| **ensemble_3x (recommended)** | **0.7717** | **0.9861** | **0.7046** |

**What changes operationally:**
- Drop the critic→defender→adjudicator dispatch chain
- Run ml-critic three times independently on the same case
- Pool issues using union (any-assessor-found = credit); majority-vote for final verdict
- Same compute budget (3×), better output on both recall and precision

**Why no defender?** The defender suppresses true positives as often as false ones. IDP without a defender (ensemble: 0.9861) exceeds IDP with a defender (isolated_debate: 0.9250). Three independent critics, absent adversarial pressure, are naturally more precise because they pick their shots carefully. The defender creates inflation, not filtering.

**Open design question (issue `c9dfc257`):** Union IDR gives equal weight to minority-flagged issues (1/3 critics) and majority-flagged (2/3). A confidence-tiered output layer would let downstream consumers distinguish high-confidence from low-confidence findings without reintroducing adversarial suppression.

#### Practical Output Layer (production implementation)

The v6 scoring design — union IDR for measurement, majority-vote for output verdict — is a **measurement protocol, not a production protocol**. In practical use, majority-vote collapses the output to the two critics who agreed, silently discarding any minority-flagged finding. If only one critic found the critical flaw, the user sees "no major issues."

**The correct production implementation:**

1. Run 3 independent `ml-critic` calls on the same case (no cross-assessor visibility)
2. Collect all flagged issues across all 3 outputs — do not filter by assessor agreement
3. Tag each issue with its assessor support count: `1/3`, `2/3`, or `3/3`
4. **Output the full tagged issue list** — do not suppress minority-flagged issues
5. Do not collapse to a single verdict label as the primary response; instead output the verdict distribution (e.g., `{critique_wins: 2, defense_wins: 1}`)

**Output format:**

```json
{
  "issues": [
    {"description": "...", "assessor_support": "3/3", "confidence": "high"},
    {"description": "...", "assessor_support": "2/3", "confidence": "medium"},
    {"description": "...", "assessor_support": "1/3", "confidence": "low — review manually"}
  ],
  "verdict_distribution": {"critique_wins": 2, "defense_wins": 1},
  "recommended_action": "critique_wins (majority); 1 minority finding warrants manual review"
}
```

**Why not suppress `1/3` issues:** Majority-vote optimizes for precision. For recall-critical tasks (a flawed paper ships, a bad model deploys), missing one real flaw costs more than reviewing one false positive. The ensemble's IDR advantage (+0.1114 over isolated_debate) comes entirely from union recovery of minority-flagged issues — collapsing to majority-vote at the output layer discards this advantage entirely.

**When majority-vote verdict is acceptable:** Only when the downstream consumer is acting on the verdict label directly (e.g., approve/reject binary) and false positive review cost is high. In that regime, also report the minority-flagged issues separately so the human can exercise judgment before acting on the collapsed verdict.

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

Baseline and ensemble both score near 0 on mixed cases — they make a verdict and move on. Multiround iterative exchange pushes agents toward `empirical_test_agreed` outcomes in ~37% of cases. The adversarial back-and-forth is structurally necessary for recognizing empirical ambiguity; no amount of independent redundancy replicates it.

**Before deploying multiround:** variance must be stabilized. 20 of 23 high-variance case-condition pairs are multiround — the same case can flip between FC=0.0 and FC=1.0 across runs. Temperature reduction or a stricter adjudicator stopping checklist is required first.

---

### 3. Retire isolated_debate as a general-purpose path

No formal test goes in isolated_debate's favor:

| Protocol | Compute | IDR | Formal status |
|---|---|---|---|
| baseline | 1× | 0.6712 | minimum viable |
| **isolated_debate** | **3×** | **0.6603** | **statistically ≡ baseline at 3× cost** |
| ensemble_3x | 3× | 0.7717 | formally superior to both |

Isolated debate is strictly dominated: it matches baseline at 3× compute and loses to ensemble at the same compute. There is no use case it wins.

---

### 4. Fix or remove the CFM gate

The gate fires on 94.7% of cases — it is not functioning as a selective filter. Mean PRR after round 1 is 0.418; the gate requires PRR=1.0 to stop, which almost never occurs. Options:

- **Lower the threshold:** PRR ≥ 0.7 would stop on cases where most issues are resolved
- **Remove it entirely:** Run full multiround when multiround is warranted; avoid conditional complexity that saves no compute

---

### 5. Redesign ETD before it can be used as a metric

ETD=1.0 for 100% of debate outputs — the scorer measures presence/absence of structure, not quality. A sub-element rubric (specificity of condition, falsifiability of `supports_critique_if`, orthogonality of the two branches) is required before mixed-case quality is quantifiable.

---

### 6. Acknowledge the defense case failure

Every condition scores DRQ=FVC=0.0 on defense cases uniformly. This is a critic prompt calibration problem: ml-critic has no "no significant issues found" output path. Needs explicit prompt redesign before defense cases can be used as benchmark cases.

---

## Revised ml-lab Architecture

```
Input case
    │
    ├─► Regular methodology review
    │       └─► ensemble_3x: 3× ml-critic → union IDR pool → majority-vote verdict
    │               (optional: confidence tier — majority-flagged vs minority-flagged issues)
    │
    └─► Empirically ambiguous / mixed
            └─► multiround debate: ml-critic → ml-defender → adjudicator → round 2
                (post-stabilization: lower temperature, structured stopping criterion)
```

The critic/defender/adjudicator structure is right for exactly one scenario: when the question is whether a methodology is testable, not whether it's flawed. That's a smaller but real use case.

---

## v7 Priority Order

1. **Stabilize multiround** — FVC_mixed=0.3667 is the most actionable positive result; high variance (20/23 high-variance pairs are multiround) must be resolved before deployment
2. ~~**Formal ensemble vs. baseline test**~~ — **DONE** (`ensemble_vs_baseline_test.py`, journal `542251e1`): ensemble_3x > baseline IDR, CI=[+0.0426, +0.1648], p=0.0000
3. **Full difficulty labeling** — only 15/80 regular cases labeled; H3 chronically underpowered
4. **ETD sub-element rubric** — required before mixed-case quality is quantifiable
5. **Defense case exoneration path** — 0.0 across all conditions is a structural gap, not noise
6. **Confidence-tiered ensemble output** — distinguish majority-flagged (2/3) from minority-flagged (1/3) issues (journal issue `c9dfc257`)
