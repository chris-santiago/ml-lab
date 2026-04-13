# v7 Experiment Report

> **Pre-registration anchor:** commit `6fadcc6` (HYPOTHESIS.md frozen before Phase 5).
> **Cross-vendor scorer:** gpt-5.4-mini via OpenRouter (pre-registered in HYPOTHESIS.md).
> **Bootstrap:** paired, n=10,000, seed=42, alpha=0.05.

---

## 1. Executive Summary

The divergent detection / convergent judgment framework is **prospectively confirmed**.
Both primary predictions pass with large margins:

- **P1 (Divergent Detection):** Ensemble IDR exceeds multiround IDR by +0.169,
  CI lower bound +0.139. Independent redundancy with union pooling is superior for
  issue detection at matched 3x compute.
- **P2 (Convergent Judgment):** Multiround FVC_mixed exceeds ensemble FVC_mixed by
  +0.225, CI lower bound +0.192. Iterative adversarial exchange is superior for
  ambiguity recognition.

Six of eight hypotheses hold as predicted. Two fail:
- **H1a:** Isolated debate is *worse* than baseline, not equivalent (delta = -0.050).
- **H5:** Minority-flagged issues carry a precision penalty (delta = -0.080), contradicting
  v6's parity finding.

Zero defense cases are fully exonerated across all conditions. Claude Sonnet 4.6 never
produces a `defense_wins` verdict. The strongest concession is `empirical_test_agreed`
(50% of multiround defense runs).

---

## 2. Experimental Design

### 2.1 Case Library

| Stratum | n | Correct Position | Source |
|---------|---|-----------------|--------|
| Regular | 160 | critique_wins | 5 RC + 155 synthetic |
| Mixed | 80 | empirical_test_agreed | 50 RC + 30 synthetic |
| Defense | 40 | defense_wins | 18 RC + 22 synthetic |
| **Total** | **280** | | 73 RC + 207 synthetic |

Cases generated via a multi-stage pipeline (Phase 1–2) with RC papers extracted from
ReScience C 2020–2021 publications and synthetic cases using a 9-type flaw taxonomy
(regular) or 6-type ambiguity taxonomy (mixed). Defense cases have sound methodology
where the correct verdict is exoneration.

### 2.2 Conditions

| Condition | API Calls | Compute | Structure |
|-----------|-----------|---------|-----------|
| baseline | 1 (critic) | 1x | Single-pass critique |
| isolated_debate | 3 (critic + defender + adjudicator) | 3x | No information-passing |
| ensemble_3x | 3 (3 independent critics) | 3x | Union pooling |
| multiround_2r | 3 (critic + defender + adjudicator) | 3x | Defender sees critique |

All conditions use Claude Sonnet 4.6 as the generation model. Each case is evaluated
3 times per condition (3,360 total outputs).

### 2.3 Scoring Dimensions

| Dimension | Scorer | Applicable Strata |
|-----------|--------|--------------------|
| IDR (Issue Detection Recall) | gpt-5.4-mini (cross-vendor) | Regular only |
| IDP (Issue Detection Precision) | gpt-5.4-mini (cross-vendor) | Regular only |
| DRQ (Decision Resolution Quality) | Rule-based | All |
| FVC (Final Verdict Correctness) | Rule-based | All |

FC composite = mean(IDR, IDP, DRQ, FVC). FVC_mixed = FVC on mixed cases only.

Note: DRQ = FVC exactly on regular cases (where `acceptable_resolutions = [correct_position]`).
FC therefore double-weights the verdict dimension relative to IDR and IDP on regular cases.

---

## 3. Primary Results

### 3.1 P1 — Divergent Detection: PASS

```
IDR: ensemble_3x > multiround_2r  [regular, n=160]
Point estimate: +0.169
95% CI lower bound: +0.139  (> 0)
Verdict: PASS
```

Ensemble IDR (0.803) vastly exceeds multiround IDR (0.634). The delta (+0.169) is larger
than v6's post-hoc ensemble vs baseline finding (+0.100), with a CI floor well above zero.

Independent redundancy with union pooling outperforms adversarial exchange for issue
detection. The three independent critics sample non-overlapping regions of the issue
space; union pooling recovers minority-flagged issues that any single assessor misses.

### 3.2 P2 — Convergent Judgment: PASS

```
FVC_mixed: multiround_2r > ensemble_3x  [mixed, n=80]
Point estimate: +0.225
95% CI lower bound: +0.192  (> 0)
Verdict: PASS
```

Multiround FVC_mixed (0.731) greatly exceeds ensemble FVC_mixed (0.506). The +0.225
delta is the largest effect in the experiment.

Recognizing genuine empirical ambiguity requires confronting the opposing argument.
In multiround, the defender sees the critique and can rebut specific claims; the
adjudicator then has substantive disagreement to evaluate. Ensemble critics, running
independently, almost always converge on `critique_wins` even when the methodology
is empirically sound.

**Verdict distribution on mixed cases (all runs):**

| Condition | critique_wins | empirical_test_agreed |
|-----------|:---:|:---:|
| baseline | 234 (97.5%) | 6 (2.5%) |
| ensemble_3x | 237 (98.8%) | 3 (1.3%) |
| isolated_debate | 188 (78.3%) | 51 (21.3%) |
| multiround_2r | 129 (53.8%) | 111 (46.3%) |

### 3.3 Framework Verdict: CONFIRMED

P1 PASS + P2 PASS = framework prospectively confirmed. The divergent detection /
convergent judgment model correctly predicts that:

1. **Detection** is a breadth problem — more independent perspectives find more issues.
2. **Judgment** is a depth problem — recognizing ambiguity requires iterative exchange.

These are structurally different tasks that benefit from different compute allocation
strategies.

---

## 4. Secondary Hypotheses

### 4.1 H1a — Isolated Debate vs Baseline: FAIL

```
FC: isolated_debate vs baseline  [regular, n=160]
Point estimate: -0.050
95% CI: [-0.065, -0.036]
Equivalence bound: +/-0.015
Verdict: FAIL (CI entirely below -0.015)
```

Isolated debate is significantly *worse* than baseline, not equivalent. The CI lies
entirely below -0.015, far from the equivalence zone.

The driver is DRQ/FVC: baseline 0.993 vs isolated_debate 0.891. Adding a generic
defender (who argues without seeing the critique) introduces noise that causes the
adjudicator to reject valid critiques ~10% of the time. IDR is unaffected (0.636 vs
0.626), so the damage is purely to verdict quality.

This overturns v6's null finding (v6 delta = -0.003, CI [-0.011, +0.006]) and reveals
an active cost of the debate structure on regular cases — a cost that was below v6's
detection threshold.

### 4.2 H2 — Ensemble vs Isolated Debate: PASS (both subsets)

**Regular (FC):**
```
Point estimate: +0.106
95% CI: [+0.092, +0.120]
Verdict: PASS (CI excludes 0)
```

**Mixed (FVC_mixed):**
```
Point estimate: -0.100
95% CI: [-0.131, -0.067]
Verdict: PASS (CI excludes 0)
```

Ensemble outperforms isolated debate on regular FC (+0.106) but underperforms on mixed
FVC (-0.100). This is the framework prediction in action: ensemble excels at detection,
isolated debate (even with its costs) provides more ambiguity recognition than ensemble.

### 4.3 H3 — Information-Passing Mechanism: PASS

```
FVC_mixed: multiround_2r > isolated_debate  [mixed, n=80]
Point estimate: +0.125
95% CI lower bound: +0.088  (> 0)
Verdict: PASS
```

The only structural difference between isolated_debate and multiround_2r is whether the
defender sees the critique. This +0.125 delta isolates information-passing as a binding
variable for convergent judgment. The mechanism is not the adversarial structure per se
— it is the defender's ability to engage with specific claims.

### 4.4 H4 — Ensemble vs Baseline IDR: PASS

**Primary:**
```
IDR: ensemble_3x > baseline  [regular, n=160]
Point estimate: +0.168
95% CI lower bound: +0.140  (> 0)
Verdict: PASS
```

Prospectively replicates v6's most robust post-hoc finding (v6: +0.100, CI [+0.043,
+0.165]). The v7 effect is larger (+0.168 vs +0.100) with a higher CI floor (+0.140
vs +0.043).

**Secondary (RC subgroup, descriptive):**

| Subgroup | n | IDR delta (ensemble − baseline) |
|----------|---|--------------------------------|
| RC papers | 5 | +0.200 |
| Synthetic | 155 | +0.166 |

RC delta > synthetic delta, consistent with the ecological validity argument. RC n=5 is
descriptive only.

### 4.5 H5 — Union Pooling Precision Parity: FAIL

```
Precision: 1/3-flagged ~ 3/3-flagged  [ensemble outputs, n=432]
Point estimate: -0.080
95% CI: [-0.108, -0.052]
Equivalence bound: +/-0.03
Verdict: FAIL (CI entirely outside +/-0.03)
```

Minority-flagged issues (1/3 agreement) have meaningfully lower precision than consensus
issues (3/3 agreement). The CI lies entirely below -0.03.

**Audit correction:** The initial v7 delta (-0.103) was inflated by a v7 pipeline bug
where tier precisions were taken from the scorer's JSON response without recomputation.
Recomputing in Python from `unique_issues` arrays (filtering phantom issues, deriving
tier from assessor count) reduced the delta to -0.080. This bug was v7-only; v6 always
computed precisions in Python. See `H5_AUDIT.md`.

**Composition effect:** The precision gap is driven by content differences across tiers:
3/3 issues are 55% planted_match (high precision by definition), while 1/3 issues are
66% valid_novel with 15% spurious noise. This is structurally expected — minority-flagged
issues include more edge cases and subjective concerns.

**Recommendation:** Union pooling with tier weighting (as pre-specified in HYPOTHESIS.md
failure mode). Weight 1/3-flagged issues lower than 3/3-flagged issues.

---

## 5. Defense Case Performance

| Condition | n | Exoneration (defense_wins) | Adjacent (empirical_test_agreed) | Defense FVC |
|-----------|---|:---:|:---:|:---:|
| baseline | 120 | 0 (0%) | 1 (0.8%) | 0.004 |
| isolated_debate | 120 | 0 (0%) | 13 (10.8%) | 0.054 |
| ensemble_3x | 120 | 0 (0%) | 0 (0%) | 0.000 |
| multiround_2r | 120 | 0 (0%) | 60 (50.0%) | 0.250 |

Zero exoneration across all conditions. Claude Sonnet 4.6 is systematically
critique-biased — it never produces a `defense_wins` verdict even when the methodology
is explicitly sound.

Multiround achieves adjacent verdicts (`empirical_test_agreed`, scored 0.5) on 50% of
defense runs, confirming that information-passing enables partial ambiguity recognition.
But the model cannot fully exonerate. Ensemble (0% adjacent) is the worst — independent
critics without a defender always converge on `critique_wins`.

---

## 6. Condition Summary

### Regular Cases (n=160 per condition)

| Condition | IDR | IDP | DRQ | FVC | FC | FVC_mixed (n=80) |
|-----------|-----|-----|-----|-----|-----|-----------------|
| baseline | 0.636 | 0.910 | 0.993 | 0.993 | 0.883 | 0.513 |
| isolated_debate | 0.626 | 0.923 | 0.891 | 0.891 | 0.833 | 0.606 |
| ensemble_3x | 0.803 | 0.963 | 0.994 | 0.994 | 0.938 | 0.506 |
| multiround_2r | 0.634 | 0.919 | 0.773 | 0.773 | 0.775 | 0.731 |

### idr_novel (paper footnote)

| Condition | n | Mean |
|-----------|---|------|
| baseline | 480 | 0.814 |
| isolated_debate | 480 | 0.813 |
| ensemble_3x | 480 | 0.831 |
| multiround_2r | 480 | 0.805 |

Novel valid issues (beyond planted flaws) are comparable across conditions. Ensemble shows
a slight edge (+0.017 vs baseline), consistent with broader issue coverage.

---

## 7. Sensitivity Analysis

### 7.1 Within-Case Variance

| Condition | Verdict Flip Rate | FVC Variance |
|-----------|------------------|-------------|
| baseline | 2.5% | 0.002 |
| isolated_debate | 44.3% | 0.037 |
| ensemble_3x | 0.7% | 0.001 |
| multiround_2r | 60.7% | 0.051 |

Multiround and isolated_debate exceed the 30% flag threshold. This is inherent to
adversarial exchange — the defender/adjudicator interaction is stochastic. The 3-run
means used in hypothesis tests are stable (bootstrap CIs are tight); individual runs
are not.

**Cross-version:** v6 multiround had 40.0% flip rate (v7: 60.7%). v6 isolated_debate
had 1.7% (v7: 44.3%). The v7 isolated_debate increase reflects the structural change
to defender+adjudicator architecture.

### 7.2 Bootstrap Stability

7/8 tests within +/-0.001 CI drift between seed=42 and seed=99. H2_mix upper bound
drifted 0.0021 (smallest sample, n=80). No verdict affected.

### 7.3 Scorer Sensitivity

10% stratified spot-check (192 files re-scored with a second gpt-5.4-mini run):
- IDR exact agreement: 89.6%
- IDP exact agreement: 88.0%
- Mean absolute IDR diff: 0.058
- Signed mean: +0.009 (no systematic bias)

Scorer noise is within expected bounds for LLM-based extraction and does not threaten
any hypothesis verdict.

### 7.4 RC vs Synthetic Subgroup

| Test | RC delta | RC n | Synthetic delta | Synthetic n |
|------|---------|------|----------------|-------------|
| P1 (IDR) | +0.261 | 5 | +0.166 | 155 |
| P2 (FVC_mixed) | +0.192 | 46 | +0.270 | 34 |

Both P1 and P2 hold in both subgroups. The RC regular sample (n=5) is too small for
inference but directionally consistent.

---

## 8. Hypothesis Verdict Summary

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
**Score:** 6/8 hypotheses as predicted
**Failures:** H1a (isolated debate is worse, not equivalent), H5 (precision penalty)

---

## 9. Key Findings for the ml-lab Framework

1. **Ensemble is the correct default for issue detection.** Ensemble IDR (0.803) exceeds
   all other conditions by at least +0.169. This is now prospectively confirmed (P1, H4).

2. **Multiround is the correct choice for ambiguity recognition.** Multiround FVC_mixed
   (0.731) exceeds all other conditions. The mechanism is information-passing (H3), not
   adversarial structure per se.

3. **Isolated debate is actively harmful on regular cases.** H1a FAIL reveals a ~10%
   verdict degradation when a blind defender is added. The debate architecture should not
   be used for straightforward flaw detection.

4. **Union pooling needs tier weighting.** H5 FAIL means minority-flagged issues carry
   a precision cost. The recommendation is tier-weighted union pooling, not unqualified
   union.

5. **Defense case exoneration remains unsolved.** Zero `defense_wins` verdicts across
   all conditions. Claude Sonnet 4.6 is systematically critique-biased. This is the
   sharpest open problem for future work.

6. **Individual multiround runs are unreliable.** 60.7% verdict flip rate means single
   runs should not be treated as authoritative. Replicate averaging is mandatory.
