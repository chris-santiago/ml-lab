# EXECUTION_PLAN.md — v5 Experiment

## Pre-Flight Checklist

**All items must be CLOSED before Phase 5 begins. Gate-8 requires LEAD approval.**

Dynamically constructed from DEFENSE.md and DEBATE.md Round 1-2 verdicts.

| # | Source | Item | Verification Method | Status |
|---|--------|------|---------------------|--------|
| PRE-1 | DEFENSE.md implementation check | `normalize_cases.py` confirmed as mandatory blocking step between `selected_cases_all.json` and Phase 5. `benchmark_cases.json` must exist before `self_debate_poc.py` executes. | Verify `phase_00_setup.md` or EXECUTION_PLAN.md requires `normalize_cases.py` and checks for `benchmark_cases.json` before Phase 5 gate. | CLOSED — Phase 0 complete; `benchmark_cases.json` exists and was validated by `validate_cases.py`. |
| PRE-2 | Issue 1 (partial concede) | Phase 9 cross-vendor disagreement rule: if cross-vendor fc_lift disagrees in direction or is more than 0.10 lower in magnitude vs. Claude-scored fc_lift, H1's generality claim must be explicitly qualified in CONCLUSIONS.md and REPORT.md. Rule must be pre-specified, not applied post-hoc. | Confirm rule appears in this EXECUTION_PLAN.md under Phase 9 interpretation directive. | CLOSED — see Phase 9 section below. |
| PRE-3 | Issue 2 (partial concede) | Pre-committed H1 × H2 outcome matrix: (a) H1 pass + H2 pass = debate outperforms baseline; adversarial structure demonstrated. (b) H1 pass + H2 fail = compute benefit confirmed; adversarial structure not demonstrated beyond compute volume. (c) H1 fail = protocol provides no benefit over baseline; H2 not interpretable. Must appear in EXECUTION_PLAN.md before execution. | Confirm matrix is present in this document. | CLOSED — see Outcome Matrix section below. |
| PRE-4 | Issue 3 (concede) | Phase 8 CONCLUSIONS.md must explicitly scope all protocol claims to binary-verdict cases (critique and defense_wins). The mechanism claim cannot be generalized to mixed-verdict scenarios from this benchmark. | Confirm scope statement appears in Phase 8 conclusions template or as a mandatory reporting norm. | CLOSED — see Phase 8 reporting norms below. |
| PRE-5 | Issue 4 (partial concede) | Sensitivity analysis must include: (a) per-dimension lift averaged across applicable cases, alongside the per-case-mean aggregate; (b) explicit note if they diverge by > 0.05. | Confirm `sensitivity_analysis.py` outputs both computations. | PENDING — verify before Phase 7. |
| PRE-6 | Issue 5 (partial concede) | Phase 5.5 pilot extended to 3 runs per case (not 1) on its 10 cases. After Phase 5.5, compute within-case variance. If mean within-case SD > 0.10, increase `n_runs_per_case` from 3 to 5 before Phase 6. Decision gate, not diagnostic. | Confirm Phase 5.5 instructions are updated to run 3 passes per pilot case and include the variance gate rule. | PENDING — gates Phase 6 start. |
| PRE-7 | Issue 6 (concede) | PREREGISTRATION.json H3 entry must be annotated as directional/descriptive: "H3 is not powered for binary pass/fail at N=30. The 60% threshold is a reference point for directional assessment. Results are reported descriptively with binomial CI; no pass/fail judgment is made." | Confirm annotation appears in PREREGISTRATION.json or EXECUTION_PLAN.md. | CLOSED — see H3 annotation below. |
| PRE-8 | DEBATE Point 1 (Round 1, supplementary) | Compute baseline and ensemble fc_lift on Phase 5.5 pilot cases (3-run basis per PRE-6). If ensemble lift over baseline on pilot >= 0.05, add explicit flag in EXECUTION_PLAN.md Phase 9 section: H1 result must be qualified against ensemble lift before claiming protocol benefit beyond compute. Interpretive flag only — not a Phase 6 execution gate. | Phase 5.5 outputs include pilot ensemble lift computation. | PENDING — gates Phase 6 start alongside PRE-6. |
| PRE-9 | DEBATE Point 2 (Round 1 concede) | Revise HYPOTHESIS.md H1 "Mechanism" field to "Motivation" with explicit note that mechanism claim is H2's conclusion, not established by H1. Add cross-reference to H1 × H2 outcome matrix. | Confirm HYPOTHESIS.md has been updated. | CLOSED — HYPOTHESIS.md updated this phase. |

---

## H1 × H2 Outcome Matrix

Pre-committed before any agent run. Prevents post-hoc interpretation of H1 as mechanism validation.

| H1 | H2 | Conclusion |
|----|----|------------|
| Pass (fc_lift ≥ 0.10) | Pass (debate > ensemble on IDR/IDP/DRQ/FVC) | Debate outperforms single-pass baseline. Adversarial structure demonstrated as the mechanism — not merely compute volume. |
| Pass (fc_lift ≥ 0.10) | Fail (debate ≤ ensemble) | Compute benefit confirmed: additional inference calls improve performance. Adversarial role structure does not add beyond compute volume alone. Protocol has practical value; mechanism claim unsupported. |
| Fail (fc_lift < 0.10) | — (not interpretable) | Protocol provides no reliable benefit over single-pass baseline. H2 result is not interpretable without H1 establishing a performance floor. |

---

## H3 Annotation (Directional Only)

**H3 is not powered for binary pass/fail at N=30 defense_wins cases.**

The 60% threshold (FVC ≥ 0.5 on ≥ 60% of defense_wins cases) is a reference point for directional assessment. The binomial standard error at N=30, p=0.60 is ≈ 0.089 — true rates within ±10 percentage points of the threshold cannot be reliably distinguished. Results for H3 are reported descriptively with binomial CI. No pass/fail judgment is made.

---

## Five Conditions

| Condition | Description | n_runs | Scope |
|-----------|-------------|--------|-------|
| `isolated_debate` | Critic and Defender each receive only task_prompt; orchestrator adjudicates | 3 | All 110 cases |
| `multiround` | Defender sees Critique; up to 4 rounds; ml-lab protocol | 3 | All 110 cases |
| `forced_multiround` | Same as multiround but minimum 2 rounds enforced | 3 | Hard cases only (42) |
| `ensemble` | 3 independent assessors + synthesizer | 3 | All 110 cases |
| `baseline` | Single-pass, no structure | 3 | All 110 cases |

---

## Phase Sequence

### Phase 5 — Build scoring engine
- Script: `plan/scripts/self_debate_poc.py`
- Implements v5 rubric: DC=N/A baseline/defense_wins, ETD=N/A all conditions (ARCH-1 has no empirical_test_agreed ground-truth cases), fair-comparison lift, forced_multiround hard-only
- Gate: `benchmark_cases.json` must exist (PRE-1 CLOSED)

### Phase 5.5 — Pre-benchmark difficulty gate (BLOCKER)
- 10-case stratified pilot: 5 medium + 5 hard, **3 runs per case** (extended per PRE-6)
- Hard-case ceiling check: ≥ 6/10 hard cases must score mean < 0.55 (claude-haiku-4-5)
- Medium calibration check: mean ≥ 0.40 to proceed
- Compute within-case SD across 3 runs; if mean SD > 0.10, increase n_runs_per_case to 5 (PRE-6 variance gate)
- Compute pilot ensemble lift over baseline; if ≥ 0.05, activate PRE-8 interpretive flag in Phase 9 section
- Spearman rho directional sanity check (medium vs hard)

**PRE-6 and PRE-8 gate:** Phase 6 does not begin until Phase 5.5 is complete and variance gate decision is recorded.

### Phase 6 — Full benchmark run
- All 5 conditions × all applicable cases × n_runs_per_case
- forced_multiround: hard cases only, minimum 2 rounds
- Output: `v5_raw_outputs/`, `v5_results.json`, `v5_results_eval.json`

### Phase 7 — Scoring
- Script: `plan/scripts/self_debate_poc.py` (scoring mode)
- Within-case variance analysis
- Sensitivity analysis: per-case-mean aggregate AND per-dimension lift (PRE-5 — verify `sensitivity_analysis.py` includes both)
- Flag if per-case-mean vs per-dimension lift diverge by > 0.05

### Phase 8 — Analysis
- Report fc_lift for: global, critique stratum, defense_wins stratum
- Apply H1 × H2 outcome matrix (PRE-3)
- **Scope constraint (PRE-4):** All protocol claims in CONCLUSIONS.md are scoped to binary-verdict cases only. The mechanism claim ("adversarial role separation") cannot be generalized to mixed-verdict scenarios from this benchmark.

### Phase 9 — Cross-vendor scoring
- Cross-vendor replication of key cases
- **Interpretation directive (PRE-2):** If cross-vendor fc_lift disagrees in direction with Claude-scored fc_lift, or is more than 0.10 lower in magnitude, H1's generality claim must be explicitly qualified in CONCLUSIONS.md and REPORT.md.
- **PRE-8 flag (conditional):** If Phase 5.5 pilot ensemble lift over baseline was ≥ 0.05, H1's result must additionally be qualified against full-run ensemble lift before claiming protocol benefit beyond compute volume.

### Phase 10 — Report

### Phase 11 — Final artifacts and coherence audit

---

## Failure Handling

- **Phase 5.5 hard-case ceiling fails:** Stop. Log. Present to LEAD. Cases must be revised or re-sourced before Phase 6.
- **Phase 5.5 medium calibration fails (mean < 0.40):** Stop. Relabeling plan to LEAD before Phase 6.
- **PRE-6 variance gate fires (SD > 0.10):** Increase n_runs_per_case from 3 to 5. Re-confirm with LEAD before Phase 6.
- **H1 fails:** Do not proceed to mechanism interpretation. Report: "Protocol provides no reliable benefit over single-pass baseline."
- **H1 passes, H2 fails:** Report: "Compute benefit confirmed; adversarial structure not demonstrated beyond compute volume." Do not cite mechanism claim.
- **Phase 9 cross-vendor disagrees by > 0.10:** Qualify H1's generality claim in all conclusions.

---

## Artifact Plan

| Artifact | Phase | Description |
|----------|-------|-------------|
| `benchmark_cases.json` | 0 | Normalized cases (110) |
| `benchmark_cases_verified.json` | 1 | Verified cases (110 keep) |
| `benchmark_verification.json` | 1 | Verifier verdicts |
| `HYPOTHESIS.md` | 2 | Pre-registered hypothesis |
| `BENCHMARK_PROMPTS.md` | 2 | Task prompts (no answer-key) |
| `PREREGISTRATION.json` | 3 | Locked rubric and hypotheses |
| `evaluation_rubric.json` | 3 | Scoring rubric |
| `CRITIQUE.md` | 4 | Protocol self-critique |
| `DEFENSE.md` | 4 | Protocol self-defense |
| `DEBATE.md` | 4 | Debate round log |
| `EXECUTION_PLAN.md` | 4 | This document |
| `README.md` | 4 | Experiment overview |
| `self_debate_poc.py` | 5 | Scoring engine |
| `v5_raw_outputs/` | 6 | Per-case agent outputs |
| `v5_results.json` | 7 | Scored results |
| `v5_results_eval.json` | 7 | Evaluation summary |
| `sensitivity_analysis.json` | 7 | Per-dimension lift + per-case-mean comparison |
| `within_case_variance_results.json` | 7 | Run-to-run variance analysis |
| `CONCLUSIONS.md` | 8 | Analysis conclusions (scoped to binary-verdict cases) |
| `REPORT.md` | 10 | Full experiment report |

---

## Gate 8 — LEAD Approval Required

Before Phase 5 begins:
1. Every PENDING pre-flight item must be confirmed CLOSED (PRE-5, PRE-6, PRE-8 close after Phase 5.5)
2. LEAD explicitly approves this EXECUTION_PLAN.md

Items already CLOSED at Phase 4 gate: PRE-1, PRE-2, PRE-3, PRE-4, PRE-7, PRE-9.
Items that close after Phase 5.5: PRE-5 (verify sensitivity_analysis.py), PRE-6 (variance gate decision), PRE-8 (pilot ensemble flag).

**Awaiting LEAD approval to proceed to Phase 5.**
