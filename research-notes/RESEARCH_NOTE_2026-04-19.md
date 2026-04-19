# Research Note — ml-lab (v8 Multi-Round Prototype)

*2026-04-19 | 15 entries | scope: this session*

## Summary
This session completed the core v8 multi-round protocol build: Phase 0 existence proof,
Gate 1 case audit (3 new hard defense cases added), canary labeling re-passes, two full
canary runs (45 cases × 3 runs), and a diagnostic DEFER fix. The session resolved the
IDR=0.000 collapse from canary_run1 but surfaced a tradeoff: the substantive DEFER
requirement (3-question test) recovered IDR to 0.600 but overcorrected on AER (0.739 →
0.217), collapsing ambiguity recognition. The IDR/AER tradeoff is now the primary open
design tension.

## Key Decisions
- **Skip Phase 0.5** [da8f8113]: v7 prompts baseline run superseded — v7 failure mode
  already documented (sycophantic concessions), v8 scorer validated on Phase 0 live runs.
- **Collapse adjudicator to derive_verdict()** [c93e0fb6]: adjudicator LLM replaced by
  a deterministic Python lookup table. Eliminates one API call per run, removes sampling
  variance, aligns benchmark with production ml-lab behavior. AOR now measures defender
  self-consistency, not LLM override rate.
- **Refined correct_position labeling criterion** [bdd068dd]: `defense_wins` reserved for
  airtight designs OR trivially-wrong critic concerns (real but genuinely insignificant).
  `empirical_test_agreed` for sound designs with real uncertainties. Second re-labeling
  pass applied to all 23 defense_wins cases → 6 re-labeled ETA → final distribution:
  17 defense_wins / 23 empirical_test_agreed / 5 critique_wins.
- **DEFER requires substantive justification** [ed352ea]: DEFER must answer: (1) what
  experiment settles this, (2) what result vindicates the design, (3) what result validates
  the critique. Applied to both DEFENDER.md and DEFENDER_R2.md.

## Discoveries & Results
- **Phase 0 existence proof** [7a83d0a4] `confirmed`: 4/4 runs → defense_wins on clean
  eval_scenario_858 defense case. Pipeline bugs fixed (EXONERATE threshold, flaw_category
  taxonomy).
- **canary_multiround_run1** [923199c9] `confirmed` (multi-round, 45 cases × 3 runs):
  DER=0.471, FDR=0.786, AER=0.739, IDR=0.000, FHR=0.773, MCC=−0.107. ETA identified
  as path of least resistance — DEFER costs zero, FATAL rule fires on partial rebuttals,
  producing systematic over-hedging.
- **Substantive DEFER probe** [ab4ee47f] `confirmed`: Both probe cases (858, 777) correct
  after 3-question DEFER requirement added.
- **canary_multiround_run2** [25c519a4] `inconclusive`: IDR: 0.000 → 0.600 ✓. AER:
  0.739 → 0.217 ✗ (overcorrection). FDR: 0.786 → 0.536 ✗. DER: 0.471 → 0.588 ✓.
  FHR: 0.773 → 0.227 ✓. MCC: −0.107 → −0.064. FCE: 0.260 (remains high).

## Issues
- **ETA/IDR tradeoff** (open, high): DEFER quality requirement improves IDR but collapses
  AER. Root cause: when DEFER is hard, defenders either fight (REBUT) or fold (CONCEDE);
  both paths lose ambiguity recognition. No clear fix yet — may require separate prompting
  for genuinely ambiguous vs. undeniable-flaw cases.
- **5 partial-run cases** (open, low): 5/45 cases completed only 1 run due to API rate
  limits during canary_multiround_run2. Majority vote over 1 run is the full result for
  those cases.
- **canary_full.json sync gap** [ff3a889d] `resolved`: canary_full.json was silently out
  of sync with canary_cases.json after Gate 1 additions. Fixed; both files now at 45 cases.

## Current State
canary_multiround_run2 scored. Primary metric (MCC=−0.064) remains below threshold
(target: baseline + 0.06 MMD). AER floor (≥0.50) not met at 0.217. FDR floor (≥0.60)
not met at 0.536. IDR floor (≥0.60) now met at 0.600. All three prompt intervention
slots still available: DEFER calibration, CONCEDE trigger, severity adjustment caps.

## Next Steps
- Diagnose AER collapse: examine canary_multiround_run2 ETA case transcripts where
  prediction was defense_wins — are defenders using REBUT-DESIGN or CONCEDE on cases
  that should DEFER?
- Design targeted fix that raises DEFER friction on undeniable flaws without penalizing
  genuine uncertainty recognition
- Consider whether FCE (0.260) and FAR (0.176) require separate interventions
- Run next canary iteration once intervention direction is identified
