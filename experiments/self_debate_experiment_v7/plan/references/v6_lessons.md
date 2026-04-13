# Lessons from v6 Constraining v7 Design

> **FROZEN — Source of Truth.** This document records lessons extracted from v6 experiment failures and post-mortems. Do not edit or add entries. New lessons from v7 go into the journal as `lesson` entries, not here.

Key findings and failure modes from v6 that directly constrain v7 decisions.

---

## L1 — Compute matching is the experimental control

v6's `multiround` averaged ~5× compute (natural stop, up to 4 rounds). The FVC_mixed
advantage (0.3667 vs 0.0) was real but confounded — we can't separate "debate structure
helps" from "more compute helps." v7 fixes this with `multiround_2r` (exactly 3×).

**Applies to:** Phase 0 (multiround_2r design), Phase 5 (dispatch logic)

---

## L2 — ETD is a structural ceiling, not a calibration problem

ETD=1.0 for 100% of debate outputs in v6. This isn't a calibration issue — any LLM asked
to propose an empirical test for an ambiguous claim will produce a structurally valid test.
The metric measures presence, not quality. Removing ETD from primary battery is the right
call; no attempt to create a quality-sensitive ETD variant in v7.

**Applies to:** Phase 0 (scoring engine update), Phase 7 (analysis)

---

## L3 — Coherence audit must be a named Phase 4 gate

v6 performed coherence audit ad-hoc at the end of Phase 4 and caught two real gaps (H6
test plan incompatible with HYPOTHESIS.md criterion; H2 missing INCONCLUSIVE verdict).
Both were fixed before Phase 5 — but only because the audit happened at all. In v7,
coherence audit is an explicit mandatory step in Phase 4, not optional cleanup.

**Applies to:** Phase 4 (gate definition) | Resolves journal issue `5273d436`

---

## L4 — Adjudicator mixed-case instruction is critical

v6 discovered (via PRE-1) that the adjudicator must receive an explicit instruction for
mixed cases: "Valid verdicts are critique_wins, defense_wins, empirical_test_agreed. Use
empirical_test_agreed when both sides made substantive points only resolvable empirically."
Without this, adjudicator defaults to a binary verdict on mixed cases, suppressing
`empirical_test_agreed` and collapsing FVC_mixed to near-zero.

**Applies to:** Phase 0 (adjudicator prompt design), Phase 5 (API dispatch logic)

---

## L5 — Cross-vendor scoring is non-negotiable

Same-model scoring (Claude scoring Claude) produces IDR delta of −0.7737 relative to
GPT-4o scoring Claude. This is the self-preference bias documented by Panickssery et al.
All scoring in v7 uses GPT-4o via OpenRouter (CROSS_VENDOR_API_KEY / CROSS_VENDOR_MODEL).

**Applies to:** Phase 0 (env verification), Phase 6 (scoring)

---

## L6 — Atomic file writes prevent partial output corruption

v6 benchmark run produced cases where `json.load()` failed on partially-written files
during concurrent execution. v7's `pipeline/phase5_benchmark.py` must use atomic writes:
write to `{path}.tmp`, then `os.rename()` to final path. `os.rename()` is atomic on POSIX.

**Applies to:** Phase 0 (phase5_benchmark.py implementation), Phase 5 (dispatch)

---

## L7 — Defense cases require targeted prompt for exoneration

v6 had 0/20 correct exonerations. Baseline and debate conditions both defaulted to
`critique_wins` even for valid methodology. The issue is systematic: the critic is
prompted to find flaws and will find (or manufacture) them. v7 defense cases need
a ground truth `correct_position = "defense_wins"` and the scoring must count only
full exonerations (`verdict == "defense_wins"`) as correct for these cases.

**Applies to:** Phase 2 (case assembly), Phase 7 (analysis — report exoneration rate separately)
