# v6 Pre-Registered Hypotheses

**Status:** DRAFT — must be committed to git before Phase 5 (benchmark run) begins.
Any post-Phase-5 changes to hypotheses, thresholds, or scoring rules invalidate pre-registration.

---

## Experiment Goal

Definitively answer three questions about the ml-lab debate protocol:

1. Does adversarial debate (critic + defender) add value over single-pass baseline?
2. Does it add value over a compute-matched ensemble (3 independent passes)?
3. Is forced multiround superior to natural stopping?

---

## Conditions

| Condition | Description | Compute |
|---|---|---|
| `baseline` | Single-pass critique | 1x |
| `isolated_debate` | Critic + Defender isolated; orchestrator adjudicates | ~3x |
| `biased_debate` | Same as isolated_debate; agents persona-primed (see H6) | ~3x |
| `multiround` | Defender sees Critic; natural stopping up to 4 rounds | ~3–6x |
| `conditional_fm` | Round 2 gated on unresolved disagreement | ~3–6x |
| `ensemble_3x` | 3 independent assessors; union-of-issues IDR | 3x |

---

## Scoring Dimensions

| Dimension | Regular cases | Mixed cases | Scorer |
|---|---|---|---|
| IDR (Issue Detection Rate) | Primary | N/A | GPT-4o |
| IDP (Issue Detection Precision) | Primary | N/A | GPT-4o |
| DRQ (Decision Resolution Quality) | Primary | Primary | Rule-based |
| FVC (Final Verdict Correctness) | Primary | **Co-primary** | Rule-based |
| ETD (Empirical Test Design) | N/A | Debate conditions only | GPT-4o |

DC is excluded — structurally redundant with FVC (v5 empirical: mean_abs_delta = 0.0 across
all conditions, all 330 runs).

**IDR scoring — bidirectional:** GPT-4o scores two separate IDR values per file:
- `idr_documented` — recall against flaws documented in the RC report (primary, used in fc_lift)
- `idr_novel` — novel valid concerns the debate raised that the reproducer missed (secondary,
  reported separately; cannot contribute to false negatives since ground truth is unknown)
Both scores saved in rescore JSON.

**IDP scoring — dual field:** Two IDP values per file:
- `idp_raw` — precision from `all_issues_raised` (Critic raw output; primary, v5-comparable)
- `idp_adj` — precision from `all_issues_adjudicated` (adjudicator synthesis after Defender
  exchange; new field measuring whether adversarial challenge filters false positives)
Primary analysis uses `idp_raw`; `idp_adj` reported as secondary.

**Fair-comparison set (regular cases):** IDR (`idr_documented`), IDP (`idp_raw`), DRQ, FVC.

---

## Per-Case Pass Criterion

**Regular cases:** `mean(non-null primary dims) >= 0.65 AND all >= 0.5`

**Mixed cases:** `ETD >= 0.5`
(Partial ETD credit — condition + one criterion — is sufficient for a mixed case pass.)

---

## H1a — Primary: Regular Case Lift (Debate vs Baseline)

```
fc_mean(isolated_debate, regular) - fc_mean(baseline, regular) >= threshold
```

**Threshold:** `threshold = max(0.03, min(0.10, (1.0 - pilot_baseline_fc_mean) * 0.5))`
- Set in Phase 3 (pilot), after observing baseline performance on candidate cases
- Must satisfy: threshold <= 50% of available headroom AND threshold >= 0.03
- Lower bound (0.03) prevents the threshold from collapsing to a trivially passable value on very hard benchmarks; upper bound (0.10) prevents a structurally impossible test on easy benchmarks
- Must be committed to this file before Phase 5

**Threshold (Phase 3 pilot, 2026-04-11):** `0.1000`
- pilot_baseline_fc_mean = 0.6500 (GPT-4o independent scorer, 30 cases, openai/gpt-4o via OpenRouter)
- formula: max(0.03, min(0.10, (1 − 0.6500) × 0.5)) = max(0.03, min(0.10, 0.1750)) = **0.1000**
- Ceiling gate: 5 cases discarded (FC > 0.80); 120 cases remain (60 critique + 20 defense + 40 mixed)

**Test:** one-sided bootstrap (N=10,000 resamples), 95% CI

**PASS if:** fc_lift >= threshold AND bootstrap CI lower bound > 0

**N/A condition:** if pilot baseline_fc_mean >= 0.80, halt and redesign difficulty filter
before proceeding

---

## H1b — Primary: Mixed Case FVC Lift (Debate vs Baseline)

```
mean FVC(isolated_debate, mixed) > mean FVC(baseline, mixed)
```

**Rationale:** On mixed cases, `acceptable_resolutions = ['empirical_test_agreed']`. Baseline
will commit to `critique_wins` or `defense_wins` and score FVC 0.0–0.5. Debate conditions
should produce `empirical_test_agreed` because the adversarial exchange forces engagement
with both the critic's concern and the defender's justification. This is the cleanest
structural test — comparable across all 5 conditions, unlike ETD.

**Test:** one-sided bootstrap (N=10,000 resamples), 95% CI

**PASS if:** bootstrap CI lower bound > 0

---

## H2 — Secondary: Debate vs Compute-Matched Ensemble (Structure Test)

```
[Regular cases]
fc_mean(isolated_debate) compared to fc_mean(ensemble_union_idr)

[Mixed cases]
mean FVC(isolated_debate, mixed) compared to mean FVC(ensemble, mixed)
```

**Rationale:** `isolated_debate` (~3x compute) vs `ensemble_3x` (3x compute) is a
matched-compute comparison. If ensemble >= debate, adversarial structure adds no value
over independent redundancy at the same token budget.

**Test:** two-sided bootstrap (N=10,000 resamples), 95% CI

**PASS if:**
- `isolated_debate fc_mean > ensemble fc_mean` (regular, CI excludes 0) — debate has structural value
- `isolated_debate FVC > ensemble FVC` (mixed, CI excludes 0) — debate has structural value on mixed cases
- FAIL if ensemble >= debate on either metric — structure adds no value over compute

---

## H3 — Secondary: Conditional FM vs Natural Multiround

```
[Hard cases only]
conditional_fm hard mean > multiround hard mean  (Wilcoxon signed-rank)
AND
hollow round rate (conditional_fm) < 0.10
```

**Hard case scope:** same definition as v5 — cases labeled `difficulty = hard` in
`benchmark_cases_verified.json`

**Hollow round definition:** round 2 with `round2_verdict == round1_verdict`
AND `round2_points_resolved == 0`

**PASS if:** Wilcoxon p < 0.05 AND hollow rate < 0.10

---

## H4 — Exploratory: ETD Quality by Debate Mode

```
Mean ETD across:
  - isolated_debate (mixed cases, 3 runs)
  - multiround (mixed cases, 3 runs)
  - conditional_fm (mixed cases, 3 runs)
```

**Expected:** More adversarial rounds should improve empirical test specification quality.
Exploratory only — no PASS/FAIL criterion, reported as distribution with 95% CIs.

---

## H6 — Secondary: Persona-Biasing Improves Debate Quality

```
[Regular cases]
fc_mean(biased_debate) vs fc_mean(isolated_debate)

[Mixed cases]
mean FVC(biased_debate, mixed) vs mean FVC(isolated_debate, mixed)
mean ETD(biased_debate, mixed) vs mean ETD(isolated_debate, mixed)
```

**Persona priming:**
- Critic: *"You are reviewing an experiment submitted by an inexperienced researcher. Be thorough
  and treat methodological gaps as real concerns until shown otherwise."*
- Defender: *"You are responding to a combative reviewer who frequently focuses on insignificant
  issues and overstates concerns. Be selective about what you concede."*

**Prediction:** biased_debate > isolated_debate on IDR (critic sensitivity raised) and IDP
(defender selectivity raised); directional improvement on mixed FVC and ETD.

**Test:** two-sided bootstrap (N=10,000 resamples), 95% CI per metric

**PASS if:** biased_debate shows improvement on >= 2 of {IDR, IDP, mixed FVC} with CI excluding 0

**If FAIL:** persona framing has no measurable effect — structural protocol dominates over
prompt-level framing

---

## H5 — Exploratory: Cross-Model Scorer Agreement

```
IDR delta = GPT4o_IDR - Claude_IDR
IDP delta = GPT4o_IDP - Claude_IDR
ETD delta = GPT4o_ETD - Claude_ETD
```

**Thresholds (flag, not fail):**
- IDR |delta| > 0.50 → flag severe closed-loop confound
- IDP |delta| > 0.20 → flag moderate concern
- ETD |delta| > 0.30 → flag moderate concern

**Purpose:** Quantify, not eliminate, the confound. The H1/H2 lift conclusions are valid
within-evaluator comparisons as long as scorer bias is condition-independent. This hypothesis
checks that assumption.

---

## Sample Size

**Target:**
- Regular cases: 80 (60 critique + 20 defense_wins)
- Mixed cases: 40
- Runs per condition per case: 3
- Total raw output files: 120 × 6 × 3 = 2,160

**Final N** determined in Phase 3 (pilot). If pilot within-case variance > 0.05, increase N.
Minimum acceptable: 80 regular + 30 mixed.

---

## Pre-Registration Audit Trail

| Field | Value |
|---|---|
| Hypotheses drafted | 2026-04-11 |
| Threshold filled (H1a) | 2026-04-11 — 0.1000 (pilot_fc_mean=0.6500) |
| Committed to git before Phase 5 | TBD |
| Phase 5 start date | TBD |
