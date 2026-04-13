# v7 Design Decisions

> **FROZEN — Source of Truth.** All phase files and pipeline code must conform to these decisions. Changes require explicit user approval and a new journal decision entry.

Every decision below is defended against the most likely reviewer challenge. Source
documents are cited inline so each rationale is traceable.

---

## 1. Conditions (4)

| Condition | Description | Compute | vs v6 |
|---|---|---|---|
| `baseline` | Single-pass critique | 1× | Retained |
| `isolated_debate` | Critic + Defender (no cross-visibility); Adjudicator synthesizes | 3× | Retained |
| `ensemble_3x` | 3 independent critics; union IDR / majority-vote verdicts | 3× | Retained |
| `multiround_2r` | Critic → Defender (sees critic) → Adjudicator; exactly 2 rounds | 3× | **New** |

### `baseline`

Single-pass critique at 1× compute. Serves as the anchor for all hypothesis tests — every
other condition is a 3× compute variant. The raw baseline IDR (~0.28 on RC papers, ~0.90
on synthetic) establishes the floor from which improvements are measured. Without this
anchor, comparisons between 3× conditions are untethered from the cost-benefit question.

### `isolated_debate`

Critic → Defender (no cross-visibility) → Adjudicator at 3× compute. Retained from v6
for two roles: (1) H1a tests whether debate adds value over baseline at all — if
isolated_debate ≈ baseline on FC, the basic debate claim fails; (2) H3 tests whether
*information-passing* (defender seeing critic output) is the binding mechanism — comparing
`multiround_2r` vs `isolated_debate` isolates this variable at matched compute.

Journal discovery `5aab8ed6` identified why isolated_debate systematically underperforms:
the defender responds to methodology in the abstract rather than to the critic's specific
claims, creating a structural asymmetry that the adjudicator cannot overcome. This is not
a calibration problem — it's a format property, and it's precisely what H3 tests.

### `ensemble_3x`

3 independent critics with no cross-visibility. IDR aggregated by union (any-assessor-found);
verdicts by majority-vote (2-of-3). Central to P1 (divergent detection) and H2 (ensemble vs
debate on regular cases).

**Why union IDR rather than majority-vote for IDR?**
v5 post-hoc analysis (discovery `a2ac43c0`) showed majority-vote dropped IDR from 0.8725
(union) to 0.7679 — a 10.5pp loss — by discarding issues found by only 1-2 critics. Union
pooling recovers this signal at no measured precision cost (H5 result: 1/3-flagged precision
0.946 ≈ 3/3 precision 0.929; diff=+0.017, CI=[−0.028, +0.068], p=0.258). The scoring engine
must implement union IDR specifically for `ensemble_3x`; all other conditions use standard
IDR from their single-assessor output.

**Why `ensemble_3x` as the divergent detection champion?**
v6 produced the most robust finding in the experiment: ensemble_3x > baseline IDR with
diff=+0.1005, CI=[+0.0426, +0.1648], p=0.0000. The mechanism is redundancy: three
independent critics sample different subsets of the issue space without cross-contamination.
Debate's defender can argue away valid critiques (consistent with the sycophancy mechanism
documented by Wynn et al.); ensemble avoids this by design.

### `multiround_2r` (New)

**The design:**
Exactly 3 API calls: Critic → Defender (receives full critic output) → Adjudicator.
No stop-detection. No conditional branching. No loop. Hard 2-round cap.

**Why this design and not v6's `multiround`?**
v6's `multiround` averaged ~5× compute (natural stop, up to 4 rounds). The FVC_mixed
advantage (0.3667 vs 0.0) was the most interesting finding in v6 but could not be
attributed to debate structure — it confounds "debate structure helps" with "more compute
helps." This is the central weakness flagged in peer review: *"the debate advantage on
convergent judgment comes from multiround at ~5× compute — not from isolated debate at 3×.
The debate-vs-ensemble mixed comparison is formally inconclusive."* (`v6_issues.md`)

`multiround_2r` is the direct response: exactly 3 API calls, matching `ensemble_3x` and
`isolated_debate` at 3× baseline. The hard cap also has empirical support: discovery
`35a8daed` shows the conditional_fm 2-round hard stop produced *more* `empirical_test_agreed`
(21.7%) than open-ended multiround (12.2%). The cap prevents attrition — agents in open-ended
multiround converge on `critique_wins` by exhaustion, masking genuine ambiguity.

**Why does defender-visibility matter?**
Discovery `5b6d7e89`: multiround produced 11.1% defense_wins vs 0.3% in isolated_debate —
a ~37× increase — because defenders can directly rebut specific claims rather than arguing
in the abstract. Discovery `5aab8ed6` confirmed the mechanism: isolation kills defense
effectiveness by preventing the defender from targeting what the critic actually said. The
defender-sees-critic design is the essential variable, not just round count.

**Peer review MUST DO:** *"Design and run compute-matched multiround variant. Cap multiround
at exactly 3× budget (e.g. 2 rounds max, fixed)."* (`v6_issues.md`)

**v6 lesson L1:** *"v6's `multiround` averaged ~5× compute. The FVC_mixed advantage was
real but confounded — we can't separate 'debate structure helps' from 'more compute helps.'
v7 fixes this with `multiround_2r` (exactly 3×)."*

### Dropped from v6

**`biased_debate`** — Persona-biased critic → biased defender → adjudicator. Bias sensitivity
was an interesting secondary result in v6 but is not a primary claim in the paper.
Discovery `c1101a56` showed counterintuitive behavior: biased priming actually *increased*
`empirical_test_agreed` (8.3% vs 0.3% in isolated_debate) because the adjudicator read
asymmetric arguing as genuine substantive dispute. This is an artifact of priming, not a
clean mechanism test. Dropping saves compute budget for the 160/80/20 case scale-up without
losing any primary hypothesis test. Report v6 result as a footnote if space permits.

**`conditional_fm`** — Discovery `35a8daed` showed it had the highest FVC_mixed of any
v6 condition (21.7% empirical_test_agreed), but the gate logic introduced a confound: the
gate fires *based on round-1 outcomes*, meaning the cases that receive a second round are
a selected subset. This selection bias makes `conditional_fm` results non-comparable to
the other conditions at matched N. `multiround_2r` solves the same problem (forced second
round) without the selection confound.

---

## 2. Case Composition: Target N = 280

| Stratum | v6 count | v7 target | Source | Rationale |
|---|---|---|---|---|
| Regular (planted flaws) | 80 | 160 | RC reports + synthetic | n=80 is desk-reject risk at ACL Findings (see below) |
| Mixed (ambiguous) | 40 | 80 | Synthetic + RC natural | Inconclusive at n=40; doubling may push CI off zero |
| Defense (valid work) | 0 | 40 | RC successful replications or synthetic no-flaw | Exoneration rate analysis; addresses 0/60 v6 failure |
| **Total** | **120** | **280** | | |

### Regular: 80 → 160

**Peer review MUST DO:** *"Scale benchmark to ≥160 regular cases. n=80 is the most likely
desk-reject risk for Findings. Target n≥160 for the primary comparison."* (`v6_issues.md`)

The primary comparison (P1: ensemble_3x > multiround_2r on IDR; H4: ensemble_3x > baseline
on IDR) requires sufficient power for paired bootstrap to produce a tight CI. At n=80, the
bootstrap CI for IDR is wide enough that modest differences may be inconclusive. The v6
ensemble > baseline result (CI=[+0.0426, +0.1648]) is robust at n=80, but the new P1
comparison (ensemble vs matched-compute multiround_2r) has unknown effect size — it may
be smaller than the ensemble vs baseline delta, requiring more cases to detect reliably.

n=160 provides 2× the bootstrap samples, halving CI width (approximately). This also
addresses the working paper limitation: *"n=120 total, n=80 regular cases is small for a
main-paper claim at ACL."*

### Mixed: 40 → 80

**Peer review MUST DO:** *"Scale mixed cases to ≥80 (from 40). The debate-vs-ensemble mixed
comparison is inconclusive at n=40. Doubling it may push the CI off zero and make the
convergent/divergent framework formally testable rather than post-hoc."* (`v6_issues.md`)

The convergent/divergent framework is the paper's main theoretical contribution. Its
empirical support depends on P2 (multiround_2r > ensemble_3x on FVC_mixed). In v6, the
debate-vs-ensemble mixed comparison had CI spanning zero at n=40 — formally inconclusive.
n=80 doubles the power for this exact test. The framework cannot be "prospectively confirmed"
(as the abstract will claim) if P2 is tested on 40 cases.

### Defense: 0 → 40

**Peer review primary concern:** *"0/60 correct verdicts across four conditions is striking
and underanalyzed. Add at least one diagnostic: does the critic prompt even include a 'no
issues found' output path?"* (`v6_issues.md`)

**v6 lesson L7:** The 0/20 exoneration rate in v6 was systematic: critics were prompted to
find flaws and did (or manufactured them). No valid "no issues found" output path existed in
the critic schema. v7 Phase 0 adds an explicit JSON path `{"verdict": "defense_wins",
"all_issues_raised": [], ...}` with the prompt instruction: *"A confident 'no significant
issues' conclusion is as important as identifying genuine flaws."*

**Why n=40:** n=40 is sufficient to show whether the prompt fix activated at all — even
12–15/40 exonerations would give a CI lower bound clearly above zero and answer the v6
0/60 concern. Cross-condition comparisons on exoneration rate at n=40 are underpowered for
small differences; report as directional only, not inferential.

Defense cases are excluded from primary hypothesis tests (P1, P2, H1a, H2, H4). They are
analyzed separately using a 2-dimension FC (DRQ + FVC only). This prevents the near-zero
exoneration score from diluting regular-case signal — a v6 design flaw that masked the
ensemble advantage in composite FC metrics.

### Fresh case generation

No reuse of v5 or v6 cases. The v5 candidate pool (728 cases) exists but all items have
`type: unknown` — they require manual categorization before use, and the categories used
by v5 (hard/medium/easy) do not map cleanly to v7's stratum labels (regular/mixed/defense).
Fresh generation with explicit strata from the outset is cleaner and avoids audit risk.

### Difficulty labeling (all 160 regular cases)

Working paper limitation: *"Only 15 of 80 regular cases have difficulty labels, leaving
difficulty-stratified analysis chronically underpowered."* (working paper Limitations §6)

v7 requires 100% difficulty labeling of all regular cases before Phase 4 pre-registration.
Proxy: pilot baseline FC mean per case — FC < 0.60 → hard, 0.60–0.80 → medium. This uses
observable performance, not ground-truth leakage (must_find issue count must not be used
as a difficulty proxy — it is answer-key data). Gate: all 160 regular cases labeled before
Phase 4 commit. Enables H4 secondary subgroup analysis (RC vs synthetic) and any
difficulty-stratified sensitivity check.

### Difficulty calibration gate (Phase 3)

Run baseline on ~40 cases per stratum as a pilot. Discard cases where
`baseline_fc_mean ≥ 0.80` — insufficient headroom for 3× compute conditions to
show improvement. This prevents ceiling effects that inflated v2/v3 results and
restores the signal dynamic that v6 correctly identified.

---

## 3. Scoring Battery

### Primary dimensions (4)

| Dimension | Regular | Mixed | Defense | Scorer |
|---|---|---|---|---|
| IDR (Issue Detection Recall) | Primary | N/A | N/A | gpt-5.4-mini cross-vendor |
| IDP (Issue Detection Precision) | Primary | N/A | N/A | gpt-5.4-mini cross-vendor |
| DRQ (Decision Resolution Quality) | Primary | Primary | Primary | Rule-based |
| FVC (Final Verdict Correctness) | Primary | **Co-primary** | Primary | Rule-based |

**FC composite (regular cases):** mean(IDR, IDP, DRQ, FVC) — same as v6 definition.
**FVC_mixed:** FVC on mixed cases only — co-primary for the convergent task test (P2, H3).
**FC defense:** mean(DRQ, FVC) — 2 dimensions only (IDR/IDP undefined for defense cases).

### IDR as co-primary metric

**Peer review MUST DO:** *"Add IDR as co-primary metric throughout. §5.2 makes the case
that IDR is the metric that matters for detection tasks and FC composites dilute it. Apply
this consistently: report IDR prominently in abstract, intro, and conclusion."*
(`v6_issues.md`)

IDR measures what the detection task actually requires: does the model find the planted
flaws? The FC composite averages IDR, IDP, DRQ, and FVC — but DRQ and FVC are near-ceiling
for Sonnet (both at 0.75+ even at baseline), contributing almost no variance. This dilutes
the IDR signal: the v6 ensemble IDR delta (+0.1005) becomes an FC delta (+0.0287) when
averaged with flat dimensions. The paper must report both, but IDR is the signal metric
for the divergent detection task. FVC_mixed is the signal metric for the convergent task.

### ETD removed

**v6 lesson L2:** ETD=1.0 for 100% of debate outputs in v6. This is not a calibration
problem — any LLM asked to propose an empirical test for an ambiguous claim will produce
a structurally valid test. The metric measures *presence*, not *quality*. There is no
signal to extract.

**Peer review MUST DO:** *"Replace or fix ETD metric. ETD=1.0 for 100% of debate outputs —
a metric with no variance is not a metric. Either add the sub-element rubric or drop ETD
and describe it as a known ceiling in limitations."* (`v6_issues.md`)

Discovery `3a9d5a35` provides additional context: in v3, ETD was the *only* dimension
where debate showed advantage (0.841 vs baseline 0.476, +0.365 delta). But v5 eliminated
mixed cases (the cases where ETD was evaluable), so ETD became structurally inapplicable.
v7 restores mixed cases but keeps ETD out of the primary battery. Include a one-paragraph
appendix note explaining the ceiling observation and why a quality-sensitive ETD rubric
is deferred to future work.

### Cross-vendor scoring (gpt-5.4-mini)

**v6 lesson L5:** Same-model scoring (Claude scoring Claude) produces IDR delta of −0.7737
relative to GPT-4o scoring Claude. This is the self-preference bias documented by
Panickssery et al. All IDR/IDP scoring in v7 uses `openai/gpt-5.4-mini` via OpenRouter
(`CROSS_VENDOR_API_KEY` / `CROSS_VENDOR_MODEL`).

gpt-5.4-mini is used consistently across all cross-vendor scoring tasks — IDR/IDP issue
matching and the H5 per-case issue classifier (both in `v7_scoring.py`). This avoids
introducing a second scorer model mid-pipeline and uses a stronger model than v6's GPT-4o
at lower cost ($0.00000075/tok prompt, $0.0000045/tok completion, 400k context).

DRQ and FVC are rule-based (verdict string matching against `correct_position` and
`acceptable_resolutions` ground truth) and do not require a neural scorer — these are
immune to self-preference bias by construction.

### FC for defense cases (2-dimension)

Defense cases have `category = "defense"` and `correct_position = "defense_wins"`.
They have no `must_find` issues — IDR and IDP are undefined (not scoreable).
FC_defense = mean(DRQ, FVC): 1.0 only if `verdict == "defense_wins"`.

**Defense cases are excluded from P1, P2, H1a, H2, H4.** All primary hypothesis tests
operate on regular cases (n=160) or mixed cases (n=80). The defense exoneration rate is
reported as a separate secondary metric (Phase 7 step 7.4) — not folded into the main
FC composite. This prevents defense failures from diluting regular-case signal.

### Union IDR for `ensemble_3x`

`ensemble_3x` uses union IDR: an issue is "found" if *any* of the 3 assessors found it.
This is justified by H5 (minority precision parity): if 1/3-flagged issues have
precision ≈ 3/3-flagged issues, then discarding minority-flagged issues via majority-vote
loses recall without recovering precision.

The `per_assessor_found` boolean array must be present in `ensemble_3x` output schema
(confirmed in Phase 4 coherence audit). Without this field, union IDR cannot be computed
from the output files. This is a Phase 4 output schema check.

### IDP dual field (retained from v6)
- `idp_raw` — precision from `all_issues_raised` (Critic raw output; primary)
- `idp_adj` — precision from `all_issues_adjudicated` (post-Adjudicator; secondary)

The adjudicator may filter or add issues relative to the raw critic output. Tracking both
fields lets us measure the adjudicator's precision contribution separately.

---

## 4. Statistical Tests

### Paired bootstrap CIs
- Paired bootstrap, n=10,000, seed=42 for all condition comparisons
- 95% CI on all primary metrics
- Paired because each case-condition pair is a matched observation (same case, different
  condition). Unpaired bootstrap would overestimate CI width by treating cases as
  independent across conditions.

Seed 42 is the v6 primary seed, retained for consistency. Phase 8 (sensitivity) reruns
with seed 99 to verify CI stability (acceptable variation: ±0.001 on CI bounds).

### Pre-specified CI bounds for H1a and H5

Rather than TOST as a named procedure, H1a and H5 use bootstrap 95% CIs with
pre-registered equivalence bounds. Equivalence is confirmed if the CI falls entirely
within the bound. This achieves the same positive claim as TOST — *"the difference is
smaller than X, not just 'we failed to reject null'"* — without introducing unfamiliar
terminology for ACL reviewers.

**Peer review MUST DO:** *"Run TOST equivalence test for H1a. You correctly note that
non-significance ≠ equivalence."* (`v6_issues.md`) The pre-specified CI approach
satisfies this requirement.

**H1a bound: ±0.015 FC**
Derived from v6 data at two anchors:
- Lower anchor (must exceed noise): v6 H1a CI half-width ~±0.010 — the bound must sit
  above the measurement noise floor.
- Upper anchor (must be non-trivial): half the v6 ensemble advantage (0.0287 ÷ 2 =
  0.014) — the bound must be below half the smallest meaningful effect.
- ±0.015 sits between both anchors. Confirmed via Phase 3 pilot check on v7 noise floor
  before Phase 4 commit. **Must not change after Phase 5 begins.**

**H5 bound: ±0.03 precision**
Derived from v6 ENSEMBLE_ANALYSIS: observed diff=+0.017, CI=[−0.028, +0.068].
±0.03 is above the observed diff (bound is not set to trivially exclude the finding) and
represents ~3pp on a scale where both precision tiers score above 0.92 — a practically
negligible difference for a union pooling recommendation.

### Pre-registration

**Peer review MUST DO:** *"Reframe convergent/divergent as prospective prediction, not just
post-hoc. State explicit falsifiable predictions — 'ensemble IDR should exceed debate IDR;
multiround should exceed ensemble on mixed judgment.' This upgrades the framework's status
for reviewers."* (`v6_issues.md`)

`HYPOTHESIS.md` must be committed to git with P1, P2, all hypothesis specifications, equivalence bounds (H1a: ±0.015 FC, H5: ±0.03 precision), and bootstrap protocol **before Phase 5 begins**. Any change after Phase 5 starts
invalidates pre-registration and converts all results to exploratory.

The pre-registration anchor commit hash must be recorded and cited in the paper's
§3 (Methods) subsection on pre-registration. This is the primary mechanism by which the
convergent/divergent framework transitions from "post-hoc interpretation" (v6) to
"prospectively confirmed/not confirmed" (v7). Discovery `4015fcd0` documented how Phase 4
self-review in v5 missed orchestrator context leakage — the explicit Phase 4 coherence
audit gate (v6 lesson L3) guards against this in v7.

---

## 5. Open Questions

| Question | Recommended resolution | Decide by |
|---|---|---|
| Defense case sourcing | RC successful replications preferred; fall back to synthetic | Phase 1 |
| Equivalence bounds (H1a, H5) | H1a: ±0.015 FC; H5: ±0.03 precision. Derived from v6 data. Confirm against pilot noise floor; must not change post-Phase-5. | Phase 3 pilot → Phase 4 commit |
| `idr_novel` secondary scoring | Compute per-condition; report as a paper footnote (not a table, not a primary or secondary hypothesis). Flag as future work: novel valid issue rate as a discovery-breadth metric beyond the planted-flaw ceiling. | Phase 7 step 7.7 |
| ~~multiround_2r hard-cap confound~~ | **Not a confound.** multiround_2r and isolated_debate are structurally identical (critic → defender → adjudicator, 3 calls, 3×). The only difference is defender visibility. H3 cleanly isolates information-passing with no round-count confound. [→ decision `33f58bc8`; see phase_08 step 8.3b] | Closed |
