# v7 Pre-Registered Hypotheses

> **Pre-registration anchor.** This document must be committed to git before Phase 5
> (benchmark run) begins. The commit hash is the anchor — any change after Phase 5
> starts invalidates pre-registration and converts results to exploratory.

---

## Case Counts (Locked)

| Stratum | N | Source |
|---------|---|--------|
| Regular | 160 | Phase 2/3 selection |
| Mixed | 80 | Phase 2/3 selection |
| Defense | 40 | Phase 2/3 selection |
| **Total** | **280** | |

---

## Primary Framework Predictions

### P1 — Divergent Detection (Ensemble Wins)

```
IDR: ensemble_3x > multiround_2r  [regular cases, n=160]
95% CI lower bound > 0  (one-sided paired bootstrap)
```

**Mechanism:** Independent redundancy with union pooling finds more planted flaws than
adversarial exchange at matched 3x compute. The ensemble's 3 independent critics sample
different subsets of the issue space without cross-contamination; union pooling recovers
issues found by only 1-2 critics that majority-vote would discard (v6 discovery
`a2ac43c0`: union IDR 0.8725 vs majority-vote 0.7679, +10.5pp).

**Why ensemble vs multiround_2r (not baseline):** The central question is whether compute
allocation — independent parallelism vs structured adversarial exchange — determines
performance. Comparing to baseline conflates compute increase with structure.

**Verdict rule:** P1 confirmed if the one-sided 95% bootstrap CI lower bound for
(ensemble_3x IDR - multiround_2r IDR) > 0.

**If P1 fails:** The divergent detection claim is not supported at matched compute.
Report as null result with full CI.

### P2 — Convergent Judgment (Multiround Wins)

```
FVC_mixed: multiround_2r > ensemble_3x  [mixed cases, n=80]
95% CI lower bound > 0  (one-sided paired bootstrap)
```

**Mechanism:** Iterative adversarial exchange with full information-passing enables
empirical ambiguity recognition that independent redundancy cannot replicate. Mixed
cases have genuine empirical uncertainty (correct verdict is `empirical_test_agreed`
or `defense_wins`). FVC_mixed measures whether the model correctly identifies this
ambiguity rather than defaulting to `critique_wins`.

**Why ensemble cannot replicate this:** Independent critics run without cross-visibility.
Recognizing genuine ambiguity requires confronting the opposing argument — the
defender's case for why a claim is empirically unresolvable. Ensemble by design
prevents this confrontation.

**Verdict rule:** P2 confirmed if the one-sided 95% bootstrap CI lower bound for
(multiround_2r FVC_mixed - ensemble_3x FVC_mixed) > 0.

**If P2 fails:** The convergent judgment claim is not supported at matched compute —
the v6 multiround advantage was a compute-budget confound, not mechanism. Report as
null with full CI.

**Framework verdict:**
- P1 AND P2 hold: framework prospectively confirmed
- P1 only: ensemble advantage general; convergent claim unsupported at matched compute
- P2 only: convergent advantage holds but divergent detection claim fails
- Neither: framework not supported at matched compute

---

## Secondary Hypotheses

### H1a — Debate vs Baseline (Equivalence)

```
FC: isolated_debate vs baseline  [regular cases, n=160]
Bootstrap 95% CI, two-sided
Equivalence bound: +/-0.015 FC
```

**Verdict rule:** H1a confirmed if the bootstrap 95% CI for
(isolated_debate FC - baseline FC) falls entirely within [-0.015, +0.015].

**Rationale:** A non-significant difference in v6 is not formal equivalence. A
bootstrap CI that falls within a pre-specified bound converts "we found no significant
difference" into "we have evidence the difference is smaller than +/-0.015 FC" — a
positive claim. This achieves the same goal as TOST without introducing unfamiliar
terminology.

**Bound derivation:**
- Lower anchor (must exceed noise): v6 H1a CI half-width ~+/-0.010. The bound must
  sit above the measurement noise floor.
- Upper anchor (must be non-trivial): half the v6 ensemble FC advantage
  (0.0287 / 2 = 0.014). The bound must be below half the smallest meaningful effect.
- +/-0.015 sits between both anchors and is defensible from both directions.

**If H1a fails:** The CI extends beyond +/-0.015. Isolated debate differs from baseline
by a practically meaningful margin. Report the CI and directional delta; do not claim
equivalence.

### H2 — Ensemble vs Isolated Debate (Two-Sided)

```
FC:        ensemble_3x vs isolated_debate  [regular cases, n=160]  (two-sided)
FVC_mixed: ensemble_3x vs isolated_debate  [mixed cases, n=80]    (two-sided)
```

**Verdict rule:** H2 confirmed if the two-sided 95% bootstrap CI for the difference
excludes 0 on either metric.

### H3 — Information-Passing Mechanism Test

```
FVC_mixed: multiround_2r > isolated_debate  [mixed cases, n=80]
95% CI lower bound > 0  (one-sided paired bootstrap)
```

**Mechanism:** `isolated_debate` and `multiround_2r` are structurally identical: critic
-> defender -> adjudicator, 3 API calls, 3x compute. The only difference is whether
the defender receives the critic's output. In isolated_debate, the defender responds
to the methodology in the abstract; in multiround_2r, the defender rebuts specific
claims. This isolates information-passing as the binding variable.

v6 evidence: multiround produced 11.1% defense_wins vs 0.3% in isolated_debate — a
~37x increase (discovery `5b6d7e89`). Sequential access to the opposing argument is
a critical variable, not just priming.

**Verdict rule:** H3 confirmed if the one-sided 95% bootstrap CI lower bound for
(multiround_2r FVC_mixed - isolated_debate FVC_mixed) > 0.

**If H3 fails:** Information-passing does not add measurable convergent judgment
value. The P2 advantage (if P2 passes) comes from some other property of the
interaction not captured by the visibility variable alone.

### H4 — Ensemble vs Baseline on IDR (Promoted from Post-Hoc)

**Primary:**
```
IDR: ensemble_3x > baseline  [regular cases, n=160]
95% CI lower bound > 0  (one-sided paired bootstrap)
```

**Why promoted:** v6's most robust finding was never pre-registered. ensemble_3x >
baseline IDR: diff=+0.1005, CI=[+0.0426, +0.1648], p=0.0000. The mechanism (union
pooling recovering minority-flagged issues) is theoretically grounded (discovery
`a2ac43c0`). Pre-registering H4 converts a post-hoc result into a prospective
replication.

**Verdict rule:** H4 primary confirmed if the one-sided 95% bootstrap CI lower bound
for (ensemble_3x IDR - baseline IDR) > 0.

**Secondary (directional, descriptive):**
```
IDR delta (ensemble_3x - baseline): RC papers > synthetic cases  [directional]
```

**Why directional without a ratio threshold:** Expected RC subgroup n~40. At n~40,
bootstrap CIs on per-subgroup deltas are wide enough that a ratio threshold would
produce an inconclusive verdict even if the direction is clear.

**Verdict rule:** H4 secondary confirmed if delta(RC) > delta(synthetic). Report both
deltas and ratio descriptively. Flag if delta(RC) < delta(synthetic) — this would
contradict the ecological validity argument.

### H5 — Union Pooling Precision Parity (Promoted from Post-Hoc)

```
Precision(1/3-flagged issues) ~ Precision(3/3-flagged issues)
Bootstrap 95% CI, two-sided
Equivalence bound: +/-0.03 precision
```

**Why promoted:** v6 ENSEMBLE_ANALYSIS finding (post-hoc): 1/3 precision=0.946,
3/3 precision=0.929, diff=+0.017, CI=[-0.028, +0.068]. Mechanism: LLM assessors
are calibrated; a minority flagging something does not make it a false positive —
it may be a genuinely subtle issue that only one of three reviewers caught.

**Bound derivation:** +/-0.03 is above the v6 observed diff (+0.017), meaning
the bound is not set to exclude the v6 result. +/-0.03 precision represents ~3pp
on a scale where both tiers score above 0.92 — practically negligible for a
pooling recommendation.

**Verdict rule:** H5 confirmed if the bootstrap 95% CI for
(1/3 precision - 3/3 precision) falls entirely within [-0.03, +0.03].

**Computation (deterministic — no separate clustering pass):** Single gpt-5.4-mini
call per ensemble_3x case receives all 3 assessors' `all_issues_raised` lists,
ground truth `must_find_issue_ids`, and `must_not_claim`. It deduplicates across
assessors, classifies each unique issue as planted_match | valid_novel | false_claim |
spurious, and assigns support tiers from the `raised_by` count.
Precision per tier = (planted_match + valid_novel) / total issues at that tier.
This eliminates the v6 separate clustering pass and its 60% missing-label error rate.

**If H5 fails:** Minority-flagged issues are precision liabilities. Union pooling
should be qualified: "use union pooling with tier weighting."

---

## Scoring Definitions

| Dimension | Formula | Scorer | Applicable strata |
|-----------|---------|--------|--------------------|
| IDR (Issue Detection Recall) | found_planted / total_planted | gpt-5.4-mini cross-vendor | Regular only |
| IDP (Issue Detection Precision) | planted_match / total_raised | gpt-5.4-mini cross-vendor | Regular only |
| DRQ (Decision Resolution Quality) | verdict == correct_position -> 1.0; verdict in acceptable -> 0.5; adjacent -> 0.5; else 0.0 | Rule-based | All |
| FVC (Final Verdict Correctness) | verdict in acceptable -> 1.0; adjacent -> 0.5; else 0.0 | Rule-based | All |

**FC composite (regular):** mean(IDR, IDP, DRQ, FVC)
**FVC_mixed:** FVC on mixed cases only (co-primary for P2, H3)
**FC defense:** mean(DRQ, FVC) — IDR/IDP undefined for defense cases

**Defense cases excluded from:** P1, P2, H1a, H2, H4. Exoneration rate reported
separately as a secondary metric (not folded into main FC composite).

---

## Experimental Conditions

| Condition | API calls | Compute | Structure |
|-----------|-----------|---------|-----------|
| baseline | 1 (critic) | 1x | Single-pass critique |
| isolated_debate | 3 (critic + defender + adjudicator) | 3x | No information-passing |
| ensemble_3x | 3 (3 independent critics) | 3x | Union pooling |
| multiround_2r | 3 (critic + defender + adjudicator) | 3x | Defender sees critic output |

---

## Bootstrap Protocol

- **Type:** Paired bootstrap (cases matched across conditions)
- **Iterations:** n=10,000
- **Seed:** 42 (primary); seed=99 rerun for CI stability check (+/-0.001 acceptable)
- **Alpha:** 0.05 (95% CIs throughout)
- **Multiple comparison correction:** None. Pre-registration controls FWER by
  eliminating post-hoc test selection (Nosek et al. 2018).
- **Primary strata:** Regular (n=160) for IDR/IDP/DRQ/FVC/FC; Mixed (n=80) for FVC_mixed
- **RC subgroup (H4 secondary):** Split by is_real_paper_case; descriptive only
- **Minority precision (H5):** Per-tier precision from gpt-5.4-mini issue classifier;
  pre-specified CI +/-0.03 on (1/3 - 3/3) difference

---

## Hypothesis Summary Table

| ID | Test | Metric | Subset | Type | Bound |
|----|------|--------|--------|------|-------|
| P1 | ensemble_3x > multiround_2r | IDR | Regular (n=160) | One-sided | CI lower > 0 |
| P2 | multiround_2r > ensemble_3x | FVC_mixed | Mixed (n=80) | One-sided | CI lower > 0 |
| H1a | isolated_debate ~ baseline | FC | Regular (n=160) | Equivalence | +/-0.015 |
| H2 | ensemble_3x vs isolated_debate | FC + FVC_mixed | Regular + Mixed | Two-sided | CI excludes 0 |
| H3 | multiround_2r > isolated_debate | FVC_mixed | Mixed (n=80) | One-sided | CI lower > 0 |
| H4 | ensemble_3x > baseline | IDR + RC subgroup | Regular (n=160) | One-sided + descriptive | CI lower > 0 |
| H5 | 1/3 precision ~ 3/3 precision | Precision by tier | Ensemble outputs | Equivalence | +/-0.03 |
