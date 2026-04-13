# Phase 4 — Pre-Experiment Self-Review

> **Reminders:** `uv run` only. CWD: repo root.
> **This is the pre-registration lock. Nothing committed here can change after Phase 5 begins.**

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — P1, P2, H1a–H5, equivalence bounds
- [design_decisions.md](../references/design_decisions.md) — conditions, scoring, equivalence bounds
- [v6_lessons.md L3](../references/v6_lessons.md) — coherence audit as named gate

---

## Key Constraint
`HYPOTHESIS.md` must be committed to git before Phase 5 begins. P1, P2, equivalence bounds
(H1a ±0.015 FC, H5 ±0.03 precision), and all hypothesis test specifications must be in
that commit. Any change after Phase 5 starts
invalidates pre-registration.

---

## Steps

### 4.1 Write and commit `HYPOTHESIS.md`

`HYPOTHESIS.md` must contain:
- **P1** — IDR: ensemble_3x > multiround_2r (regular, n=160). One-sided bootstrap CI lower bound > 0.
- **P2** — FVC_mixed: multiround_2r > ensemble_3x (mixed cases, n=80). One-sided bootstrap CI lower bound > 0.
- **H1a** — Pre-specified CI ±0.015 FC: isolated_debate vs baseline (regular, n=160). CI must fall entirely within [−0.015, +0.015].
- **H2** — Two-sided: ensemble_3x vs isolated_debate on FC (regular) and FVC_mixed (mixed).
- **H3** — One-sided: multiround_2r vs isolated_debate on FVC_mixed (mixed, n=80). CI lower bound > 0.
- **H4** — IDR: ensemble_3x > baseline (regular, n=160). One-sided bootstrap CI lower bound > 0. Secondary: RC subgroup directional (delta(RC) > delta(synthetic)).
- **H5** — Precision parity: 1/3-flagged ≈ 3/3-flagged (ensemble outputs). Pre-specified CI ±0.03 precision. CI must fall entirely within [−0.03, +0.03].
- Bootstrap protocol: paired, n=10,000, seed=42. No multiple comparison correction (pre-registration controls FWER; cite Nosek et al. 2018).
- Case counts locked in: `n_regular`, `n_mixed`, `n_defense` (from Phase 2/3 outputs).

Commit `HYPOTHESIS.md` **before dispatching review agents.**

### 4.2 Coherence Audit (mandatory named gate — resolves issue 5273d436)

Verify alignment across: `HYPOTHESIS.md`, `pipeline/v7_scoring.py`, and this phase file.

Check each item:

**a) Hypothesis ↔ scoring code:**
- Each hypothesis has a corresponding test function in `v7_scoring.py`
- Test functions use the correct N (regular vs mixed case subset)
- Equivalence CI check function uses the bounds committed in `HYPOTHESIS.md` (H1a ±0.015, H5 ±0.03)
- Bootstrap uses seed=42 and n=10,000

**b) Scoring dimensions ↔ conditions:**
- ETD is absent from `DIMENSIONS` in `v7_scoring.py`
- FC composite = mean(IDR, IDP, DRQ, FVC) — 4 dimensions
- FVC_mixed subset correctly filters to `category == "mixed"` cases only

**c) Dispatch logic ↔ conditions list:**
- `phase5_benchmark.py` `--conditions` handles exactly: `baseline`, `isolated_debate`,
  `ensemble_3x`, `multiround_2r`
- `multiround_2r` handler makes exactly 3 API calls (verify in code)
- Adjudicator receives mixed-case injection when `case["category"] == "mixed"`

**d) Output schema ↔ scoring input:**
- All fields consumed by `v7_scoring.py` are produced by `phase5_benchmark.py` output schema
- `per_assessor_found` booleans present in `ensemble_3x` outputs (needed for union IDR)

Document any gaps found. Fix before continuing. Record in `COHESION_AUDIT.md`.

### 4.3 Dispatch `ml-critic` for design review

Agent prompt:
```
Review HYPOTHESIS.md and the v7 evaluation design.

Context: This is a pre-registered benchmark experiment testing whether multiround_2r
(critic → defender-with-visibility → adjudicator, exactly 3x compute) outperforms
ensemble_3x on convergent tasks (mixed cases, FVC_mixed) and vice versa on divergent
detection (regular cases, IDR). Two directional predictions P1 and P2 must both hold.

Your tasks:
1. Evaluate P1 and P2 — are they falsifiable and the test specifications correct?
2. Evaluate H1a equivalence CI — is ±0.015 FC appropriate given the pilot baseline mean?
3. Identify any confounds, power issues, or design gaps not addressed by v6_lessons.md.
4. Check for answer-key leakage vectors in the benchmark runner design.
5. Generate PRE-1 through PRE-N pre-execution requirements.

Read: experiments/self_debate_experiment_v7/HYPOTHESIS.md
Reference: experiments/self_debate_experiment_v7/plan/references/hypotheses.md
Reference: experiments/self_debate_experiment_v7/plan/references/v6_lessons.md
```

### 4.4 Dispatch `ml-defender`
After critic output, dispatch `ml-defender` with critic output + `HYPOTHESIS.md`.
Run up to 2 debate rounds. Stop when requirements are stable.

### 4.5 Resolve PRE-N requirements
Address each pre-execution requirement. Update `pipeline/phase5_benchmark.py` or
`pipeline/v7_scoring.py` if needed. Commit resolutions.

### 4.6 Final commit
Commit resolved `HYPOTHESIS.md`, `COHESION_AUDIT.md`, and any scoring/dispatch fixes.
This is the pre-registration anchor commit. Record commit hash.

---

## Verification
- [ ] `HYPOTHESIS.md` committed with P1, P2, H1a–H5, equivalence bounds (H1a ±0.015 FC, H5 ±0.03), bootstrap protocol
- [ ] Coherence audit complete: all 4 checks pass, documented in `COHESION_AUDIT.md`
- [ ] All PRE-N requirements resolved and committed
- [ ] No answer-key leakage vectors identified (or mitigated)
- [ ] `CRITIQUE.md`, `DEFENSE.md` written

## Outputs
- Committed `HYPOTHESIS.md`
- `COHESION_AUDIT.md`
- `CRITIQUE.md`
- `DEFENSE.md`

## Gate
`HYPOTHESIS.md` committed to git. All PRE-N resolved. Coherence audit passed and documented.
