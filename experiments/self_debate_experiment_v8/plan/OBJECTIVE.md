# Objective

## The Problem

ml-lab cannot exonerate sound methodology. Across all v7 conditions — 480 defense-case evaluations (4 conditions × 40 cases × 3 runs) — the system produces **zero** `defense_wins` verdicts. The best outcome is `empirical_test_agreed`, a hedge scored 0.5, achieved on 50% of multiround defense runs.

A review system that can never say "this is fine, proceed" trains its users to ignore it. Every methodology gets flagged. Every design gets questioned. Experiments get recommended that aren't needed.

## Root Causes (Three Compounding Mechanisms)

**1. The critic has no "nothing found" exit path.** The prompt instructs "identify every claim the PoC makes implicitly but has not tested." Given any methodology, an instruction-tuned LLM will generate something. No threshold exists below which the critic says "not worth raising."

**2. The defender is prompted to concede, not to win.** Five explicit concession instructions vs. zero exoneration instructions. The only mention of `defense_wins` in the defender prompt is a prohibition. The system has no exit path for "I reviewed the critique and none of it holds up."

**3. Adjudication has no cost model.** The orchestrator weighs critique quality vs. defense quality but never asks whether the recommended experiment is worth running. Without a cost threshold, any non-zero critique wins.

## The Implicit Cost Asymmetry

| Action | Current cost |
|---|---|
| Recommend unnecessary experiment | 0 |
| Miss a real flaw | ∞ |

The system behaves as if false alarms are free. They are not. Unnecessary experiments waste time and erode trust. The cost model is wrong.

## Goal

Iterate on ml-lab's agent prompts — critic, defender, and orchestrator adjudication logic — until the system can:

1. **Correctly exonerate sound methodology** (DER > 0.30 on defense cases)
2. **Without breaking detection** (IDR >= 0.75 on regular cases)
3. **Without increasing false hedging** (FHR does not regress on clear cases)

## Success Criteria

| Metric | v7 Baseline | v8 Target | Rationale |
|---|---|---|---|
| DER (defense exoneration rate) | 0.00 | > 0.30 | System can exonerate at least 30% of sound cases |
| IDR (issue detection rate) | 0.803 (ensemble) / 0.634 (multiround) | >= 0.75 (multiround) | Detection must not degrade |
| FAR (false alarm rate) | 1.00 | < 0.50 | Fewer than half of sound cases get false critique_wins |
| FHR (false hedge rate) | — | ≤ canary-run-1 + 0.05 | Non-regression: first canary run sets baseline; subsequent iterations must not exceed it by more than 0.05 |

DER is the primary metric. FVC_mixed (retired) gave 0.5 credit for hedges — the system already hedges. The actual problem is confident exoneration: `defense_wins` verdicts on sound methodology.

## Phase 0 — Existence Proof (Kill Switch)

Before building the iteration framework, verify the capability exists.

**Test:** Take one obviously-sound defense case from the v7 benchmark. Hand-craft an ideal defender prompt — explicit exoneration instruction, explicit permission to dismiss critiques, full context of why the methodology is sound.

- If the model produces `defense_wins` → the model CAN do this. The production prompt is the bottleneck. Proceed.
- If the model CANNOT produce `defense_wins` → prompt iteration won't help. Pivot.

**Phase 0 fallback (must be defined before starting):**
If Phase 0 fails, the immediate next step is: dispatch the same defense case to a different model family as defender (e.g., use a pool model instead of Claude) with the same ideal prompt. If any model in the pool produces `defense_wins`, the problem is Anthropic-model-specific RLHF and cross-model dispatch is the solution. If no model produces `defense_wins`, the problem is architectural — stop and report.

## Success Deliverable

**Open question — define before starting.** Candidates:
- Revised ml-lab plugin files (updated ml-critic.md, ml-defender.md, ml-lab.md adjudication section) with versioned changelog
- REPORT.md documenting the v8 investigation arc, intervention results, and final metric comparison
- Updated benchmark documentation (audit results, taxonomy coverage, canary composition)
- All three — the plugin update is the product; the report is the record
