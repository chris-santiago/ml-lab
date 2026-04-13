# Divergent Detection, Convergent Judgment: A Prospective Test of Compute Allocation for LLM-Based Methodology Review

---

## Abstract

We test a framework for allocating compute in LLM-based methodology review: **divergent
detection** (finding issues benefits from independent redundancy) and **convergent judgment**
(recognizing ambiguity benefits from iterative adversarial exchange). Using a 280-case
benchmark with pre-registered hypotheses and a cross-vendor scorer (gpt-5.4-mini), we
confirm both predictions at matched 3x compute. Ensemble assessment (3 independent
critics with union pooling) achieves IDR 0.803 vs multiround IDR 0.634 (delta = +0.169,
CI [+0.139, +inf)). Multiround debate achieves FVC_mixed 0.731 vs ensemble 0.506
(delta = +0.225, CI [+0.192, +inf)). Six of eight pre-registered hypotheses hold.
Two fail: isolated debate degrades verdict quality vs baseline (-0.050 FC), and
minority-flagged issues carry a precision penalty (-0.080). All conditions fail to
exonerate valid methodologies (0% defense_wins verdicts).

---

## 1. Introduction

LLM-based methodology review — using language models to evaluate research designs,
statistical claims, and experimental protocols — faces a fundamental allocation question:
given a fixed compute budget, should the model generate multiple independent assessments
or engage in structured adversarial exchange?

Prior work (v6, 120 cases, 6 conditions) established that an ensemble of 3 independent
critics with union-of-issues pooling outperforms both single-pass baseline and isolated
adversarial debate on issue detection recall (IDR). However, the v6 ensemble comparison
was post-hoc, the multiround condition was not compute-matched, and the precision parity
finding (H5 equivalent) was underpowered.

This experiment (v7) pre-registers eight hypotheses testing the **divergent detection /
convergent judgment** framework: detection tasks benefit from independent redundancy,
while judgment tasks benefit from iterative exchange. All hypotheses are locked before
data collection (commit `6fadcc6`), tested against a 280-case benchmark at matched 3x
compute, and scored by a cross-vendor model (gpt-5.4-mini via OpenRouter).

---

## 2. Methods

### 2.1 Benchmark

280 cases in three strata:
- **Regular (n=160):** Planted methodology flaws where `critique_wins` is correct.
  5 extracted from ReScience C publications, 155 synthetic.
- **Mixed (n=80):** Empirically ambiguous designs where `empirical_test_agreed` is
  correct. 50 RC-sourced, 30 synthetic.
- **Defense (n=40):** Sound methodologies where `defense_wins` is correct. 18 RC, 22 synthetic.

### 2.2 Conditions

Four conditions at matched compute (3 API calls each, except baseline at 1):

| Condition | Structure |
|-----------|-----------|
| **baseline** | Single critic pass (1x compute) |
| **isolated_debate** | Critic + blind defender + adjudicator (3x) |
| **ensemble_3x** | 3 independent critics, union pooling (3x) |
| **multiround_2r** | Critic + informed defender + adjudicator (3x) |

All use Claude Sonnet 4.6. Each case evaluated 3 times per condition (3,360 outputs).

### 2.3 Metrics

- **IDR** (Issue Detection Recall): proportion of planted issues found. Cross-vendor
  scored by gpt-5.4-mini. Ensemble uses union IDR (found if ANY of 3 assessors found it).
- **IDP** (Issue Detection Precision): proportion of raised issues that are genuine.
  Cross-vendor scored.
- **DRQ/FVC** (Verdict quality): rule-based scoring against ground-truth verdicts.
  DRQ = FVC on regular cases.
- **FC** (Fair Comparison composite): mean(IDR, IDP, DRQ, FVC) on regular cases.
- **FVC_mixed**: FVC on mixed stratum only.

### 2.4 Statistical Protocol

Paired bootstrap (n=10,000, seed=42, alpha=0.05). Case-level differences resampled with
replacement. One-sided tests for directional predictions (P1, P2, H3, H4); two-sided for
non-directional (H1a, H2, H5). Stability verified at seed=99 (7/8 within +/-0.001 CI
drift). No multiple comparison correction; pre-registration controls family-wise error
rate.

---

## 3. Results

### 3.1 Primary Predictions

**P1 — Divergent Detection (Ensemble Wins).**
Ensemble IDR (0.803) exceeds multiround IDR (0.634): delta = +0.169, 95% CI lower
bound = +0.139. Three independent critics with union pooling find substantially more
planted issues than iterative adversarial exchange at matched compute.

**P2 — Convergent Judgment (Multiround Wins).**
Multiround FVC_mixed (0.731) exceeds ensemble FVC_mixed (0.506): delta = +0.225,
95% CI lower bound = +0.192. Iterative exchange with information-passing enables
correct ambiguity recognition that independent critics cannot replicate. Multiround
produces `empirical_test_agreed` on 46.3% of mixed runs; ensemble produces it on 1.3%.

**Framework verdict: CONFIRMED.** Both primary predictions pass with large, non-overlapping
effects. Detection and judgment are structurally different tasks that benefit from
different compute allocation.

### 3.2 Secondary Hypotheses

| ID | Prediction | Point Est. | 95% CI | n | Verdict |
|----|-----------|:---:|--------|---|---------|
| H1a | isolated_debate ~ baseline (FC) | -0.050 | [-0.065, -0.036] | 160 | **FAIL** |
| H2_reg | ensemble_3x > isolated_debate (FC) | +0.106 | [+0.092, +0.120] | 160 | **PASS** |
| H2_mix | ensemble_3x < isolated_debate (FVC) | -0.100 | [-0.131, -0.067] | 80 | **PASS** |
| H3 | multiround > isolated_debate (FVC_mixed) | +0.125 | [+0.088, +inf) | 80 | **PASS** |
| H4 | ensemble_3x > baseline (IDR) | +0.168 | [+0.140, +inf) | 160 | **PASS** |
| H5 | 1/3 precision ~ 3/3 precision | -0.080 | [-0.108, -0.052] | 432 | **FAIL** |

**H1a (Equivalence): FAIL.** Isolated debate is not equivalent to baseline — it is
significantly worse. Adding a blind defender introduces noise that causes the adjudicator
to reject valid critiques. DRQ/FVC drops from 0.993 (baseline) to 0.891 (isolated_debate).
This overturns v6's null finding and reveals an active cost of debate structure.

**H3 (Information-Passing): PASS.** The +0.125 delta between multiround and isolated_debate
isolates defender visibility as the binding mechanism. The two conditions are structurally
identical except whether the defender sees the critique.

**H4 (Replication): PASS.** Prospectively replicates v6's strongest post-hoc finding.
v7 effect (+0.168) exceeds v6 (+0.100) with a higher CI floor. RC subgroup delta (+0.200)
exceeds synthetic (+0.166), consistent with ecological validity (n=5, descriptive).

**H5 (Precision Parity): FAIL.** Minority-flagged issues (1/3 agreement) have 0.080pp
lower precision than consensus issues (3/3 agreement). CI [-0.108, -0.052] lies entirely
outside the +/-0.03 equivalence bound. This contradicts a prior finding at smaller scale
(+0.017, CI [-0.028, +0.068], n=180) and is driven by composition: 3/3 issues are 55%
planted_match (definitionally valid), while 1/3 issues carry 15% spurious noise.

### 3.3 Defense Case Exoneration

| Condition | Exoneration | Adjacent | Defense FVC |
|-----------|:---:|:---:|:---:|
| baseline | 0/120 (0%) | 1/120 (0.8%) | 0.004 |
| isolated_debate | 0/120 (0%) | 13/120 (10.8%) | 0.054 |
| ensemble_3x | 0/120 (0%) | 0/120 (0%) | 0.000 |
| multiround_2r | 0/120 (0%) | 60/120 (50.0%) | 0.250 |

Zero full exoneration across all conditions. The strongest concession is
`empirical_test_agreed` (adjacent, scored 0.5), achieved on 50% of multiround defense
runs. Claude Sonnet 4.6 is systematically critique-biased.

---

## 4. Robustness

**Within-case variance.** Multiround (60.7% verdict flip rate) and isolated_debate
(44.3%) exceed the 30% stability threshold. Ensemble (0.7%) and baseline (2.5%) are
stable. Variance is inherent to adversarial exchange; 3-run averaging produces stable
aggregate estimates.

**Bootstrap stability.** 7/8 tests within +/-0.001 CI drift between seeds. H2_mix
upper bound drifted 0.0021 (n=80); verdict unaffected.

**Scorer sensitivity.** 10% stratified spot-check: 89.6% exact IDR agreement, no
systematic bias (signed mean = +0.009). Scorer noise does not threaten verdicts.

**Subgroup stability.** P1 holds in both RC (delta = +0.261, n=5) and synthetic
(+0.166, n=155) subgroups. P2 holds in RC (+0.192, n=46) and synthetic (+0.270, n=34).

---

## 5. Discussion

### 5.1 The Framework

The divergent detection / convergent judgment framework provides a principled basis for
compute allocation in LLM-based methodology review:

- **For issue detection:** use ensemble (3 independent critics, union pooling). The
  ensemble IDR advantage (+0.169 over multiround, +0.168 over baseline) is the most
  robust finding across v6 and v7.

- **For ambiguity recognition:** use multiround with information-passing. The multiround
  FVC_mixed advantage (+0.225 over ensemble) is the largest single effect. The mechanism
  is the defender's ability to engage with specific claims (H3), not adversarial
  structure per se.

### 5.2 What Failed

**Isolated debate is dominated.** H1a's failure reveals that the original critic-defender
debate protocol — with a blind defender who argues methodology in the abstract — actively
harms verdict quality. The adjudicator, confronted with conflicting generic arguments,
rejects valid critiques ~10% of the time. This is worse than running a single critic pass.

**Union pooling carries a precision cost.** H5's failure means minority-flagged issues
are not unconditionally trustworthy. The recommendation is tier-weighted union pooling:
weight 1/3-flagged issues lower than 3/3-flagged issues. The recall advantage (P1, H4)
is real; the precision cost (H5) qualifies how that recall should be consumed.

**Defense exoneration is unsolved.** No condition produces `defense_wins` verdicts. This
is not a protocol failure — it is a model limitation. Claude Sonnet 4.6 is critique-biased:
even with a well-argued defense and multiround exchange, the adjudicator at most concedes
`empirical_test_agreed`. Future work should investigate whether this bias is addressable
through prompt calibration or requires model-level changes.

### 5.3 Cross-Version Stability

| Finding | v6 | v7 |
|---------|-----|-----|
| Ensemble > baseline IDR | +0.100 (post-hoc) | +0.168 (pre-registered) |
| Multiround FVC_mixed advantage | +0.367 (descriptive) | +0.225 (pre-registered) |
| Isolated debate vs baseline | -0.003 (null) | -0.050 (worse) |
| Minority precision parity | +0.017 (parity) | -0.080 (penalty) |
| Defense exoneration | 20% (multiround only) | 0% (all conditions) |

The ensemble IDR advantage is stable and strengthens with pre-registration. The multiround
FVC advantage is confirmed at matched compute (v6 was not compute-matched). The H5 reversal
is attributed to classifier model differences (GPT-4o vs gpt-5.4-mini) and a composition
effect at larger scale. The defense exoneration decline (20% → 0%) reflects the absence
of `defense_wins` from Claude Sonnet 4.6's output vocabulary.

### 5.4 Limitations

1. **Single generation model.** All conditions use Claude Sonnet 4.6. The framework
   predictions may not generalize to other models.
2. **Planted-flaw benchmark.** Regular cases have synthetic planted flaws. Real-world
   methodology review involves subtler, less cleanly categorized issues.
3. **Cross-vendor scorer dependency.** IDR and IDP depend on gpt-5.4-mini's extraction
   accuracy (~90% exact agreement on spot-check).
4. **RC regular sample.** Only 5 RC papers in the regular stratum (n=160). The ecological
   validity argument for regular cases rests primarily on synthetic data.
5. **Defense case exoneration.** Zero exoneration across all conditions limits conclusions
   about the framework's defense-case applicability.

---

## 6. Conclusion

At matched 3x compute, independent redundancy with union pooling outperforms adversarial
debate for issue detection (+0.169 IDR), while iterative exchange with information-passing
outperforms independence for ambiguity recognition (+0.225 FVC_mixed). Both predictions
are prospectively confirmed.

The practical recommendation: use ensemble for detection, multiround for judgment, and
neither for exoneration. Union pooling should be tier-weighted to account for the
minority precision penalty. Individual multiround runs should not be trusted without
replicate averaging.
