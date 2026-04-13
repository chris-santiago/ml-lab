# v7 Hypotheses (Pre-Registered)

> **FROZEN — Source of Truth.** This document defines all pre-registered hypotheses, test specifications, equivalence bounds, and the bootstrap protocol. Do not edit after the Phase 4 pre-registration commit. Any change after Phase 5 begins invalidates pre-registration and converts results to exploratory. Rationale for all decisions is embedded inline and traceable to journal entries (decision `8c032ebc` — equivalence CI bounds; decision `97872fd4` — H5 precision method; decision `db50a071` — no multiple comparison correction; memo `5b4e2e10` — full battery summary).

Pre-registration must be committed to git **before Phase 5 (benchmark run) begins**.
See `HYPOTHESIS.md` (v7 experiment root) for the full formal document.

**Critical:** Any change to hypotheses, thresholds, or test specifications after Phase 5
begins invalidates pre-registration and converts the result to exploratory. The commit hash
of `HYPOTHESIS.md` is the anchor — record it in the paper's §3 (Methods).

---

## Pre-Registered Framework Predictions (Primary)

These two predictions are the minimum sufficient test of the convergent/divergent framework.
**Both must hold** for the framework to be prospectively confirmed.

### P1 — Divergent detection (ensemble wins)

```
IDR: ensemble_3x > multiround_2r  [regular cases, n=160]
95% CI lower bound > 0  (one-sided bootstrap)
```

**What this tests:**
Whether independent redundancy with union pooling finds more planted flaws than adversarial
exchange at matched 3× compute. Regular cases have unambiguous planted flaws — this is a
purely divergent detection task. The ensemble's design (3 independent critics sampling
different subsets of the issue space without cross-contamination) is structurally suited
to this task type.

**Why we expect this to hold:**
The primary mechanism is **recall breadth via union pooling**, not debate suppression.
v6 per-condition IDR: ensemble_3x=0.7717, multiround=0.6523, baseline=0.6712. multiround
IDR was only 0.0189 below baseline — suppression is real but small (~2pp). The ensemble
advantage over multiround (+0.1194) is almost entirely explained by union pooling
recovering issues found by only 1-2 critics that majority-vote would discard (discovery
`a2ac43c0`: union IDR 0.8725 vs majority-vote 0.7679, +10.5pp). Debate does not
aggressively destroy IDR on regular cases; ensemble simply accumulates more of the issue
space through independent sampling.

Note on `conditional_fm` (v6): IDR=0.2153 at n=8 — not informative for P1. The gate
fired only on hard unresolved cases, so the low IDR reflects case difficulty selection,
not condition performance. No mixed-case data existed for that condition.

**Why the comparison is ensemble vs multiround_2r (not ensemble vs baseline):**
The central experimental question in v7 is whether compute allocation — to independent
parallelism vs structured adversarial exchange — determines performance. Comparing to
baseline conflates compute increase with structure. P1 isolates structure: same 3×
budget, different deployment of that budget.

**Peer review motivation:** *"The most interesting finding isn't compute-matched. The
debate advantage on convergent judgment comes from multiround at ~5× compute — not from
isolated debate at 3×."* (`v6_issues.md`) P1 creates the matched-compute counterpart for
the divergent task.

**If P1 fails:**
The divergent detection claim is not supported at matched compute. This would suggest
the ensemble advantage in v6 was partly attributable to the baseline comparison, not
to structural superiority over debate at equal budget. Report as null result with full CI.

---

### P2 — Convergent judgment (multiround_2r wins)

```
FVC_mixed: multiround_2r > ensemble_3x  [mixed cases, n=80]
95% CI lower bound > 0  (one-sided bootstrap)
```

**What this tests:**
Whether iterative adversarial exchange with full information-passing enables empirical
ambiguity recognition that independent redundancy cannot replicate — at matched 3× compute.
Mixed cases have genuine empirical uncertainty (correct verdict is `empirical_test_agreed`
or `defense_wins`). FVC_mixed measures whether the model correctly identifies this
ambiguity rather than defaulting to `critique_wins`.

**Why we expect this to hold:**
Discovery `5b6d7e89`: multiround produced 11.1% defense_wins vs 0.3% in isolated_debate —
a ~37× increase — because defenders can directly rebut specific claims rather than arguing
in the abstract. Discovery `35a8daed`: the conditional_fm 2-round hard cap produced 21.7%
`empirical_test_agreed` (the highest of any v6 condition), showing that a forced second
round highlights genuine ambiguity rather than forcing premature resolution. The
`multiround_2r` design inherits both properties: defender visibility (from `multiround`)
and a hard 2-round cap (from `conditional_fm`).

**Why ensemble cannot replicate this:**
Independent critics run without cross-visibility. Each assessor sees only the original
paper, not what the other critics found. Recognizing that a claim is genuinely ambiguous
(not just "found" or "not found") requires confronting the *opposing argument* — the
defender's case for why the claim is empirically unresolvable. Ensemble by design prevents
this confrontation. This is not a weakness; it is structurally appropriate for divergent
detection and structurally inappropriate for convergent judgment.

**Peer review motivation:** *"Scale mixed cases to ≥80. The debate-vs-ensemble mixed
comparison is inconclusive at n=40. Doubling it may push the CI off zero and make the
convergent/divergent framework formally testable rather than post-hoc."* (`v6_issues.md`)
P2 at n=80 is the direct response: same test, double the power.

**If P2 fails:**
The convergent judgment claim is not supported at matched compute — the v6 multiround
advantage was compute-budget confound, not mechanism. This would be the more important
null result: it would mean the convergent/divergent framework is not supported prospectively.
Report as null with full CI and note that v6 multiround advantage (at 5×) cannot be
extrapolated to matched-compute comparison.

**Framework verdict:**
- P1 AND P2 hold → framework prospectively confirmed
- P1 only → ensemble advantage general; convergent claim unsupported at matched compute
- P2 only → convergent advantage holds but divergent detection claim fails
- Neither → framework not supported at matched compute

---

## H1a — Debate vs Baseline (Equivalence)

```
FC: isolated_debate  vs  baseline  [regular cases, n=160]
Bootstrap 95% CI, two-sided
Equivalence bound: ±0.015 FC (pre-registered from v6 data; confirm in Phase 3 pilot)
```

**What this tests:**
Whether structured debate (at 3× compute) adds any practical value over single-pass
critique on the primary FC composite. H1a is not a directional prediction — it tests
equivalence: can we make a positive claim that the difference is smaller than a
pre-specified meaningful threshold?

**Why a pre-specified CI bound instead of a null result:**
**Peer review MUST DO:** *"Run TOST equivalence test for H1a. You correctly note that
non-significance ≠ equivalence. A TOST with a stated equivalence bound converts 'not sig'
into a formal claim about debate adding no meaningful value over baseline."* (`v6_issues.md`)

The working paper stated: *"The H1a non-significance result demonstrates failure to reject
the null, not formal equivalence."* Reporting a bootstrap CI that falls within a
pre-specified bound converts the claim from "we found no significant difference" to
"we have evidence the difference is smaller than ±0.015 FC" — a positive claim.
This achieves the same goal as TOST without introducing unfamiliar terminology for
ACL reviewers.

**Equivalence verdict:** H1a confirmed if the bootstrap 95% CI for
(isolated_debate − baseline) FC falls entirely within [−0.015, +0.015].

**Bound derivation (from v6 data):**
- **Lower bound (must exceed noise):** v6 H1a CI half-width was ~±0.010. The bound must
  sit above the measurement noise floor so the test is not conducted within scorer
  uncertainty.
- **Upper bound (must be non-trivial):** half the v6 ensemble FC advantage (+0.0287 ÷ 2
  = 0.014). The bound must be below half the smallest effect we consider meaningful, so
  equivalence is not a trivially weak claim.
- ±0.015 sits between these two anchors and is defensible from both directions.

**Phase 3 confirmation:** after the pilot, verify the v7 within-condition FC variance is
consistent with v6. If the noise floor shifts substantially, revisit the bound before
Phase 4 commit. **Bound must not change after Phase 5 begins.**

**v6 result:** H1a bootstrap CI was [−0.0108, +0.0059] — well within ±0.015. H1a at
n=160 should replicate with tighter CIs.

**If H1a fails:**
The CI extends beyond ±0.015 in either direction. This means isolated_debate differs
from baseline by a practically meaningful margin. Given v6's stable near-zero delta,
failure would likely reflect a genuine change in the case distribution. Report the CI
and directional delta; do not claim equivalence.

---

## H2 — Ensemble vs Debate (Two-Sided)

```
FC:       ensemble_3x  vs  isolated_debate  [regular cases, n=160]  (two-sided)
FVC_mixed: ensemble_3x  vs  isolated_debate  [mixed cases, n=80]  (two-sided)
```

**What this tests:**
The direct structural comparison: does ensemble or isolated debate perform better on the
primary task, and does this pattern hold on convergent tasks?

**Why two-sided:**
H2 is not a directional prediction — it probes the ensemble vs debate comparison without
constraining the sign. This is deliberately weaker than P1/P2. P1 already makes the
directional ensemble > multiround_2r prediction; H2 tests ensemble vs the *simplest*
debate format (no information-passing, 1-round). If ensemble wins H2_regular, it beats
isolated debate at matched compute — a stronger claim than beating multiround_2r.

**v6 result:** H2 passed. ensemble_3x FC CI lower bound = +0.0154 > 0, confirming
ensemble > isolated_debate at p < 0.05.

**Expected pattern consistent with P1/P2 framework:**
H2_regular PASS (ensemble wins regular) + H3 PASS (multiround_2r wins mixed). If both
hold alongside P1/P2, the convergent/divergent framework is supported at all comparison
levels.

**H2 is not primary:**
H2 is a replication of the v6 directional finding (now tested prospectively), not the
central framework test. P1 and P2 are the framework tests. H2 provides convergent evidence.

---

## H3 — Information-Passing Debate vs Isolated Debate (Mechanism Test)

```
FVC_mixed: multiround_2r  vs  isolated_debate  [mixed cases, n=80]  (one-sided)
CI lower bound > 0
```

**What this tests:**
The mechanistic claim: is *information-passing* (defender seeing critic output) the binding
variable for convergent judgment? By comparing `multiround_2r` (information-passing) vs
`isolated_debate` (no information-passing) at matched compute, H3 isolates the mechanism.
Both conditions use 3 API calls: critic + defender + adjudicator. The only difference is
whether the defender receives the critic's output.

**Why we expect this to hold:**
Discovery `5aab8ed6`: *"Isolation kills defense effectiveness: in isolated_debate, the
defender responds to the methodology in the abstract — not to the critic's specific claims.
This creates a fundamental asymmetry: the critic attacks specific gaps, while the defender
makes general methodological arguments. The adjudicator then has little basis to overturn
specific critiques, explaining the near-uniform critique_wins outcome."*

Discovery `5b6d7e89`: *"The defender-sees-critic effect is substantial: multiround produced
11.1% defense_wins vs 0.3% in isolated_debate — a ~37× increase. Sequential access to the
opposing argument is a critical variable — not just priming."*

**Why H3 cleanly isolates information-passing:**
`isolated_debate` and `multiround_2r` are structurally identical: critic → defender →
adjudicator, 3 API calls, 3× compute. The only difference is whether the defender
receives the critic's output. Round count is the same in both conditions — 2 agent turns
before adjudication. "2r" in the condition name refers to the 2 agent turns (critic +
defender), which is identical to isolated_debate's structure. There is no round-count
confound; H3 is a clean mechanism test.

**If H3 fails:**
Information-passing does not add measurable convergent judgment value over isolated debate
at matched compute. This would mean the FVC_mixed advantage in P2 (if P2 passes) comes
from some other property of the multiround_2r interaction not captured by the visibility
variable alone — an unexpected finding that would require further investigation into
adjudicator behavior when given a debate thread vs. independent submissions.

---

## H4 — Ensemble vs Baseline on IDR (Promoted from Post-Hoc)

### Primary

```
IDR: ensemble_3x  >  baseline  [regular cases, n=160]  (one-sided)
CI lower bound > 0
```

**What this tests:**
Whether the union-pooled ensemble recovers significantly more planted flaws than a single
baseline critic on regular cases.

**Why promoted from post-hoc:**
v6's most robust finding was never pre-registered. ensemble_3x > baseline IDR:
diff=+0.1005, CI=[+0.0426, +0.1648], p=0.0000. The effect size is large, the CI is
well off zero, and the mechanism (union pooling recovering minority-flagged issues) is
theoretically grounded in discovery `a2ac43c0`. Pre-registering this as H4 converts a
post-hoc result into a prospective replication. If H4 fails at n=160, the v6 finding
was either dataset-specific or sensitivity to case difficulty — a meaningful null result.

**v6 lesson:** The v6 ensemble > baseline finding was confirmed separately from the
main hypothesis battery. Promoting to H4 closes the gap: all major findings have
pre-registered counterparts.

### Secondary — RC subgroup (directional)

```
IDR delta (ensemble_3x − baseline): RC papers > synthetic cases  [directional]
```

**What this tests:**
Whether the ensemble IDR advantage is larger on harder, ecologically valid cases (real
ReScience C papers) than on synthetic planted flaws. Direction only — no ratio threshold
pre-registered.

**v6 post-hoc result:** RC delta=+0.172, synthetic delta=+0.059. The ensemble advantage
was ~3× larger on real papers.

**Why directional without a ratio threshold:**
Expected RC subgroup n≈40 (approximately 25% of 160 regular cases). At n≈40, bootstrap
CIs on per-subgroup deltas are wide enough that a ratio threshold (e.g. ≥2×) would
produce an inconclusive verdict even if the direction is clear. Pre-registering only
the direction gives a binary verdict — did RC delta exceed synthetic delta? — without
committing to a magnitude estimate the sample size cannot reliably support.

**Verdict rule:** H4 secondary confirmed if delta(RC) > delta(synthetic). Report both
deltas and the ratio descriptively. Flag if delta(RC) < delta(synthetic) — this would
contradict the ecological validity argument and require explanation.

**Why this matters:**
Synthetic cases have high baseline IDR (~0.90) — little room for improvement. RC cases
are harder (baseline IDR ~0.28) — ensemble recovers substantially more issues via union
pooling. Ceiling effects on synthetic cases structurally suppress the delta regardless
of ensemble quality. If the directional prediction holds, it strengthens the claim that
the ensemble advantage generalizes beyond easy synthetic cases to harder, real-world
methodology review.

---

## H5 — Union Pooling Precision Parity (Promoted from Post-Hoc)

```
Precision(1/3-flagged issues)  ≈  Precision(3/3-flagged issues)
Bootstrap 95% CI, two-sided
Equivalence bound: ±0.03 precision (pre-registered from v6 data)
```

**What this tests:**
Whether minority-flagged issues (raised by only 1 of 3 assessors) have precision
comparable to unanimous issues (raised by all 3 assessors). If the CI falls within the
pre-specified bound, union pooling is formally validated as precision-safe: minority
assessors are not producing meaningfully more false positives than unanimous assessors.

**Why promoted from post-hoc:**
v6 ENSEMBLE_ANALYSIS finding (post-hoc): 1/3 precision=0.946, 3/3 precision=0.929,
diff=+0.017, CI=[−0.028, +0.068]. The finding has a clear theoretical mechanism: LLM
assessors are calibrated; a minority flagging something does not make it a false positive
— it may be a genuinely subtle issue that only one of three reviewers caught.
Pre-registering H5 makes the union pooling recommendation formal: if H5 confirms, the
paper can recommend union-of-issues pooling without caveat about false positives from
minority assessors.

**Equivalence verdict:** H5 confirmed if the bootstrap 95% CI for
(1/3 precision − 3/3 precision) falls entirely within [−0.03, +0.03].

**Bound derivation (from v6 data):**
- v6 observed diff: +0.017, v6 CI half-width: ~±0.048. The measurement noise on
  precision is higher than on FC (fewer clusters than cases).
- ±0.03 is above the observed diff (+0.017), meaning the bound is not set to exclude
  the v6 result — it's set to confirm it prospectively.
- ±0.03 precision represents ~3pp on a scale where both tiers score above 0.92 — a
  practically negligible difference for a pooling recommendation.
- If the v7 CI half-width is substantially wider than v6 (fewer ensemble outputs), flag
  as underpowered rather than adjusting the bound post-hoc.

**Computation method (deterministic — no separate clustering pass):**
A single `gpt-5.4-mini` call per ensemble_3x case (Phase 6 scoring) receives all 3
assessors' `all_issues_raised` lists, ground truth `must_find_issue_ids`, and
`must_not_claim`. It deduplicates across assessors, classifies each unique issue as
`planted_match | valid_novel | false_claim | spurious`, and assigns support tiers from
the `raised_by` count. Output stored as `per_case_issue_map` in scoring output.

Precision per tier = (planted_match + valid_novel) / total issues at that tier.
This eliminates the v6 separate clustering pass and its 60% missing-label error rate.

**If H5 fails:**
Minority-flagged issues are precision liabilities relative to unanimous issues. Union
pooling should then be qualified: use union IDR but caveat that 1/3-tier issues require
additional validation. Paper recommendation shifts from "use union pooling directly" to
"use union pooling with tier weighting."

---

## Bootstrap Protocol

- **Type:** Paired bootstrap. Cases are matched observations across conditions (same case,
  different condition). Unpaired bootstrap would overestimate CI width by treating cases
  as independent across conditions — incorrect for this design.
- **Iterations:** n=10,000 (standard for bootstrap CI stability at this sample size)
- **Seed:** 42 (primary). Phase 8 reruns with seed=99 to verify CI stability; acceptable
  variation is ±0.001 on CI bounds. At n=10,000 bootstrap samples with n=160 cases,
  variation above ±0.001 is unexpected and should be reported as a sensitivity finding.
- **Alpha:** 0.05 (95% CIs throughout). No multiple comparison correction applied.
  Pre-registration controls family-wise error rate by eliminating post-hoc test
  selection — Bonferroni addresses data dredging, which pre-registration removes by
  design. Cite: Nosek et al. (2018) "The Preregistration Revolution." [→ decision `db50a071`]
- **Primary strata:** regular cases (n=160) for IDR/IDP/DRQ/FVC/FC; mixed cases (n=80)
  for FVC_mixed
- **RC subgroup (H4 secondary):** split by `is_real_paper_case` boolean; report n per
  stratum; use descriptive statistics only (not formal one-sided bootstrap) given expected
  n≈40 for RC subgroup
- **Minority precision (H5):** single gpt-5.4-mini call per ensemble_3x case deduplicates
  across assessors and classifies each unique issue; assign to support tier (1/3, 2/3, 3/3)
  based on `raised_by` count; compute precision per tier; pre-specified CI ±0.03 on
  (1/3 − 3/3) difference

---

## Hypothesis Summary Table

| ID | Test | Metric | Subset | Type | Origin |
|---|---|---|---|---|---|
| P1 | ensemble_3x > multiround_2r | IDR | Regular (n=160) | One-sided bootstrap | Framework prediction (pre-registered) |
| P2 | multiround_2r > ensemble_3x | FVC_mixed | Mixed (n=80) | One-sided bootstrap | Framework prediction (pre-registered) |
| H1a | isolated_debate ≈ baseline | FC | Regular (n=160) | Pre-specified CI ±0.015 | Replication + formal equivalence (v6 non-sig → v7 positive claim) |
| H2 | ensemble_3x vs isolated_debate | FC + FVC_mixed | Regular + Mixed | Two-sided bootstrap | Replication of v6 directional finding |
| H3 | multiround_2r > isolated_debate | FVC_mixed | Mixed (n=80) | One-sided bootstrap | Mechanism test (information-passing isolation) |
| H4 | ensemble_3x > baseline | IDR + RC subgroup | Regular (n=160) + RC | One-sided bootstrap + descriptive | Promoted from v6 post-hoc (p=0.0000) |
| H5 | 1/3 precision ≈ 3/3 precision | Precision by tier | Ensemble outputs | Pre-specified CI ±0.03 | Promoted from v6 post-hoc (ENSEMBLE_ANALYSIS) |
