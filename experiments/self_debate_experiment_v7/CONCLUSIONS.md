# v7 Conclusions

> Pre-registration anchor: commit `6fadcc6` (HYPOTHESIS.md frozen before Phase 5).
> Cross-vendor scorer: gpt-5.4-mini via OpenRouter (pre-registered).
> Bootstrap: paired, n=10,000, seed=42. Stability check: seed=99 (7/8 within +/-0.001; H2_mix upper bound drift 0.0021 — verdict unaffected).

---

## Framework Verdict: CONFIRMED

Both primary predictions pass. The divergent detection / convergent judgment framework
is prospectively confirmed at matched 3x compute.

---

## Primary Predictions

### P1 — Divergent Detection (Ensemble Wins): PASS

```
IDR: ensemble_3x > multiround_2r  [regular, n=160]
Point estimate: +0.169
95% CI lower bound: +0.139  (> 0)
```

Ensemble IDR (0.803) vastly exceeds multiround IDR (0.634). The +0.169 delta is larger
than v6's +0.100, with a CI floor well above zero. Independent redundancy with union
pooling reliably outperforms adversarial exchange for issue detection.

### P2 — Convergent Judgment (Multiround Wins): PASS

```
FVC_mixed: multiround_2r > ensemble_3x  [mixed, n=80]
Point estimate: +0.225
95% CI lower bound: +0.192  (> 0)
```

Multiround FVC_mixed (0.731) greatly exceeds ensemble FVC_mixed (0.506). The +0.225
delta is the largest effect in the experiment. Adversarial exchange with information-passing
enables correct ambiguity recognition that independent critics cannot replicate.

---

## Secondary Hypotheses

### H1a — Isolated Debate ~ Baseline (Equivalence): FAIL

```
FC: isolated_debate vs baseline  [regular, n=160]
Point estimate: -0.050
95% CI: [-0.065, -0.036]
Equivalence bound: +/-0.015
```

Not merely non-equivalent — isolated debate is significantly *worse* than baseline.
The CI lies entirely below -0.015. The driver is DRQ/FVC: baseline 0.993 vs isolated_debate
0.891. Adding a generic defender (who argues without seeing the critique) introduces noise
that causes the adjudicator to reject valid critiques ~10% of the time.

This overturns v6's null finding and reveals a cost of debate structure on regular cases.
IDR is unaffected (0.636 vs 0.626), so the damage is purely to verdict quality.

### H2 — Ensemble vs Isolated Debate (Two-Sided): PASS (both subsets)

**Regular (FC):**
```
Point estimate: +0.106
95% CI: [+0.092, +0.120]  (excludes 0)
```

**Mixed (FVC_mixed):**
```
Point estimate: -0.100
95% CI: [-0.131, -0.067]  (excludes 0)
```

Ensemble significantly outperforms isolated debate on regular FC (+0.106) but significantly
underperforms on mixed FVC (-0.100). Consistent with framework: ensemble excels at
detection but cannot recognize ambiguity.

**Bootstrap stability note:** H2_mix upper bound drifts 0.0021 between seeds (spec: +/-0.001).
Verdict unaffected — CI is entirely below zero on both seeds.

### H3 — Information-Passing Mechanism: PASS

```
FVC_mixed: multiround_2r > isolated_debate  [mixed, n=80]
Point estimate: +0.125
95% CI lower bound: +0.088  (> 0)
```

The only structural difference between isolated_debate and multiround_2r is whether the
defender sees the critique. This +0.125 delta isolates information-passing as a binding
variable for convergent judgment. Without visibility into opposing arguments, the
defender cannot mount effective rebuttals on genuinely ambiguous cases.

### H4 — Ensemble vs Baseline IDR (Promoted Replication): PASS

**Primary:**
```
IDR: ensemble_3x > baseline  [regular, n=160]
Point estimate: +0.168
95% CI lower bound: +0.140  (> 0)
```

Replicates v6's most robust finding (v6: diff=+0.100, CI=[+0.043, +0.165]).
v7 effect is larger (+0.168 vs +0.100), with a higher CI floor.

**Secondary (RC subgroup, descriptive):**

| Subgroup | n | IDR delta (ensemble - baseline) |
|----------|---|--------------------------------|
| RC papers | 5 | +0.200 |
| Synthetic | 155 | +0.166 |

RC delta > synthetic delta, consistent with the ecological validity argument (harder
real-world papers benefit more from redundant assessment). However, RC n=5 is far too
small for inference — this is descriptive only.

### H5 — Union Pooling Precision Parity: FAIL

```
Precision: 1/3-flagged ~ 3/3-flagged  [ensemble outputs, n=432]
Point estimate: -0.080
95% CI: [-0.108, -0.052]
Equivalence bound: +/-0.03
```

Minority-flagged issues (1/3 agreement) have meaningfully lower precision than consensus
issues (3/3 agreement). The CI lies entirely below -0.03.

This contradicts v6's finding (v6: +0.017, CI [-0.028, +0.068]) and means union pooling
carries a precision cost. Recommendation: use union pooling with tier weighting (as
pre-specified in HYPOTHESIS.md failure mode).

**Audit correction:** The initial v7 H5 delta (-0.103) was inflated by a v7 pipeline bug
where tier precisions were taken from the scorer's JSON response without recomputation.
Recomputing in Python from the `unique_issues` arrays (filtering phantom issues, deriving
tier from assessor count) reduced the delta to -0.080. This bug was v7-only; v6's
`v6_minority_precision.py` always computed precisions in Python. See `H5_AUDIT.md`.

**Methodological note:** H5 is computed at the per-file level (n=432 observations from
160 cases x 3 runs), while all other tests average across runs first (n=160 or n=80
per-case observations). This asymmetry does not affect the verdict given the point
estimate is 2.7x the equivalence bound, but is noted for transparency.

---

## Condition Summary

### Regular Cases (n=160 per condition)

| Condition | IDR | IDP | DRQ | FVC | FC | FVC_mixed (n=80) |
|-----------|-----|-----|-----|-----|-----|-----------------|
| baseline | 0.636 | 0.910 | 0.993 | 0.993 | 0.883 | 0.513 |
| isolated_debate | 0.626 | 0.923 | 0.891 | 0.891 | 0.833 | 0.606 |
| ensemble_3x | 0.803 | 0.963 | 0.994 | 0.994 | 0.938 | 0.506 |
| multiround_2r | 0.634 | 0.919 | 0.773 | 0.773 | 0.775 | 0.731 |

**Note:** DRQ = FVC exactly for regular cases. When `acceptable_resolutions = [correct_position]`,
the two scoring functions are algebraically identical. FC therefore double-weights the
verdict dimension relative to IDR and IDP.

### idr_novel (paper footnote)

| Condition | n | Mean |
|-----------|---|------|
| baseline | 480 | 0.814 |
| isolated_debate | 480 | 0.813 |
| ensemble_3x | 480 | 0.831 |
| multiround_2r | 480 | 0.805 |

Novel valid issues (beyond planted flaws) are comparable across conditions. Ensemble
shows a slight edge (+0.017 vs baseline), consistent with broader issue coverage from
independent assessment. Flagged as future work: novel issue rate as a discovery-breadth
metric beyond the planted-flaw ceiling.

---

## Defense Case Exoneration

| Condition | n | Exoneration | Adjacent | Defense FVC |
|-----------|---|------------|----------|-------------|
| baseline | 120 | 0/120 (0%) | 1/120 (0.8%) | 0.004 |
| isolated_debate | 120 | 0/120 (0%) | 13/120 (10.8%) | 0.054 |
| ensemble_3x | 120 | 0/120 (0%) | 0/120 (0%) | 0.000 |
| multiround_2r | 120 | 0/120 (0%) | 60/120 (50.0%) | 0.250 |

**Zero exoneration across all conditions.** Claude Sonnet 4.6 never produces a
`defense_wins` verdict. The strongest concession is `empirical_test_agreed` (adjacent,
scored 0.5). Multiround achieves this on 50% of defense cases, confirming that
information-passing enables partial ambiguity recognition — but the model is
systematically critique-biased and cannot fully exonerate.

Ensemble (0 adjacent) is the worst: independent critics without a defender always
converge on `critique_wins`, even for well-designed methodologies.

---

## Hypothesis Verdict Summary

| ID | Verdict | Point Estimate | CI | n |
|----|---------|---------------|-----|---|
| P1 | **PASS** | +0.169 | [+0.139, +inf) | 160 |
| P2 | **PASS** | +0.225 | [+0.192, +inf) | 80 |
| H1a | **FAIL** | -0.050 | [-0.065, -0.036] | 160 |
| H2_reg | **PASS** | +0.106 | [+0.092, +0.120] | 160 |
| H2_mix | **PASS** | -0.100 | [-0.131, -0.067] | 80 |
| H3 | **PASS** | +0.125 | [+0.088, +inf) | 80 |
| H4 | **PASS** | +0.168 | [+0.140, +inf) | 160 |
| H5 | **FAIL** | -0.080 | [-0.108, -0.052] | 432 |

**Framework:** CONFIRMED (P1 PASS + P2 PASS)
**Score:** 6/8 hypotheses as predicted (P1, P2, H2_reg, H2_mix, H3, H4)
**Failures:** H1a (isolated debate is worse, not equivalent), H5 (minority precision penalty)
