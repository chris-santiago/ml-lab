# Research Note — ml-debate-lab

*2026-04-11 | ~67 entries | scope: today*

## Summary
v6 experiment completed its full run: 120 cases × 6 conditions × 3 runs (2,160 outputs), GPT-4o
primary scorer. Co-primary hypotheses H1a and H2 both failed — adversarial debate produced no FC
lift over baseline, and ensemble_3x formally outperformed isolated_debate at matched compute.
The one strong positive result is FVC_mix=0.3667 for multiround on mixed/ambiguous cases vs.
baseline=0.0, establishing debate's value as an ambiguity detector rather than a flaw detector.
Post-experiment protocol synthesis finalized ensemble_3x as the ml-lab default with multiround
retained as an opt-in path for ambiguous-case routing.

## Key Decisions
- **ensemble_3x is the ml-lab default** [b9108902]: Formally superior to isolated_debate at matched
  compute (CI=[−0.0434,−0.0154]); union-IDR aggregation recovers +9.5pp recall without precision
  penalty.
- **multiround kept as opt-in** [1f55296d]: FVC_mix=0.3667 vs baseline=0.0 — iterative exchange
  is structurally necessary for empirical ambiguity detection; ensemble cannot replicate this.
- **Gate 1 output format finalized** [b9108902]: verdict_distribution omitted; confidence tiers
  renamed to detection redundancy tiers (high/medium/minority); Gate 1 ensemble summary added as
  structured handoff equivalent to the debate path's DEFENSE.md Pass 2 table.
- **Union-of-issues IDR confirmed as v6 aggregation rule** [0192f428]: Majority-vote synthesis
  was discarding +10.5pp IDR; union recovers recall without meaningful precision cost.
- **Phase 4 meta-debate artifacts (CRITIQUE/DEFENSE/DEBATE.md) are gate conditions** [9c8824be]:
  Silently dropped from v6 Phase 4 spec this round; re-added as Phase 5 gate — no data collection
  without the audit trail.

## Discoveries & Results

**Formal experiment verdicts:**
- H1a FAIL: lift=−0.0026, CI=[−0.0108,+0.0059]
- H1b FAIL
- H2 FAIL: ensemble>debate, CI=[−0.0434,−0.0154]
- H3 FAIL: p=0.3677
- H4 CEILING: ETD=1.0 all conditions (saturation — adversarial exchange reliably produces test specs)
- H6 PASS (mixed-direction): FVC_mix=+0.2417 positive, IDP_adj=−0.0389 negative

**Ensemble IDR formal test** [542251e1]: ensemble_3x IDR=0.7717 vs baseline=0.6712;
diff=+0.1005; 95% CI=[+0.0426,+0.1648], p=0.0000. Union IDR lift is statistically real.

**Minority precision analysis** [d3d79649]: No tier-level precision penalty for minority-flagged
issues. 1/3 tier: 0.946, 3/3 tier: 0.929, diff CI=[−0.028,+0.068]. Union output is justified on
both recall and precision grounds.

**Isolation kills defense** [5aab8ed6]: isolated_debate produces 99.4% critique_wins because
the defender responds to methodology in the abstract, not the critic's specific claims. critique_wins
in isolation is structurally overdetermined by format, not flaw severity.

**Biased priming backfires** [c1101a56]: biased_debate shows 8.3% empirical_test_agreed vs 0.3%
in isolated_debate — pro-critic priming did not inflate critique_wins; instead asymmetric framing
created apparent substantive disputes that fooled the adjudicator into deferring resolution.

**Conditional FM 2-round cap** [35a8daed]: conditional_fm produced the most empirical_test_agreed
(21.7%) of any condition; attrition in open-ended multiround may mask cases that deserve ambiguity
verdicts.

**Cross-experiment arc** [3a9d5a35]: v3's +0.341 raw lift was largely measurement artifact
(+0.25 from structural baseline penalties). Corrected v3 lift = +0.0913, driven by ETD — the one
dimension where debate adds genuine value. v5 removed mixed cases (ETD=N/A) and lift collapsed
to +0.0113. v6 confirms: debate's advantage is narrow, ETD/ambiguity-specific, and not replicable
by ensemble.

## Issues (Open)
- **[5273d436] moderate** — Coherence audit (spec vs plan vs code) not a named protocol step;
  caught two real gaps in v6 Phase 4 ad-hoc; should be a gate before Phase 5 in future experiments.
- **[621a8176] moderate** — artifact-sync skill lives only in ml-debate-lab; needs promotion to
  ml-lab plugin for reuse across projects.
- **[c9dfc257] low** — ensemble_3x output has no confidence-tiered signal; minority-flagged
  issues (1/3 critics) are indistinguishable from unanimous findings for downstream consumers.
- **[ce2704c1] low** — intent-watch agent not yet migrated into ml-lab plugin.

## Current State
Phase 3 complete; Phase 4 pre-experiment self-review not yet started. Immediate gate: commit
Phase 3 artifacts (HYPOTHESIS.md, benchmark_cases_verified.json, pilot artifacts) before Phase 4.
Phase 5 benchmark is 6 conditions × 120 cases × 3 runs = 2,160 agent dispatches — requires explicit
confirmation before start.
*(Note: checkpoint [7ce9a841] dates from mid-session; v6 experiment phases 5–10 are now complete.)*

## Next Steps
- Promote artifact-sync skill to ml-lab plugin [621a8176]
- Add coherence audit as a formal gate step in future experiment phase plans [5273d436]
- Design confidence-tiered output for ensemble_3x (detection redundancy tiers already named) [c9dfc257]
- Investigate multiround vs ensemble_3x on regular cases — v6 formal tests only compared ensemble
  vs isolated_debate (the weakened control), not ensemble vs multiround [1f55296d]
- Consider 2-round cap as calibration tool in future debate protocol designs [35a8daed]
