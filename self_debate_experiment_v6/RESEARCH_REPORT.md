# Research Report — ml-debate-lab

*Generated 2026-04-12 from 270 journal entries and 381 commits.*

---

## Problem Statement

This project investigates whether structured adversarial debate between LLM agents produces better ML methodology reviews than simpler alternatives. The animating question traces back to a single applied experiment: can FastText-encoded device IDs and attributes serve as features for ML model consumption? Once that experiment proved worth formalizing, it was captured as a monolithic Claude Code prompt, then refactored into modular agent dispatches, then consolidated back into a two-agent debate structure (critic + defender), and finally packaged as a reusable Claude Code plugin (`ml-lab`).

The meta-evaluation problem emerged naturally: how do you assess whether the debate protocol actually works? This produced a six-version empirical series (v1 through v6, with v4 halted early), each iteration stress-testing the debate protocol's ability to surface real ML methodology flaws compared to baseline single-pass critique and compute-matched ensemble alternatives. The series draws on Irving et al. (2018)'s debate-as-alignment-mechanism framing and operationalizes it for ML methodology review via a critic-defender-adjudicator structure.

By v6, the original FastText question had recursed several levels deep into evaluation infrastructure: real-paper benchmark sourcing (ML Reproducibility Challenge), multi-LLM scoring pipelines via OpenRouter, concurrent Python-orchestrated agent dispatch, paired bootstrap statistical testing, and a second plugin (`ml-journal`) for structured session logging and research reporting.

---

## Timeline

| Date | Event |
|------|-------|
| Pre-journal | Initial FastText experiment (v1) — single monolithic Claude prompt, adversarial critique architecture proven worthwhile |
| Pre-journal | v2 — refactored to modular agent dispatches; agents lost overall context; consolidated back |
| Pre-journal | v3 — 49-case synthetic benchmark; raw lift = +0.341 over baseline; cases too easy; ETD drove most of the apparent advantage |
| Pre-journal | v4 — halted after Phase 7; baseline ceiling effect; cases filtered on Claude proxy scores (same-model bias) |
| 2026-04-09 | Journal initialized; v5 experiment active; ARCH-1 compatibility audit begins (7 schema/scoring fixes committed) |
| 2026-04-09 | Decision: remove IDJ (Issue Detection Justification) dimension from v5 scoring engine; normalize_cases.py written to bridge ARCH-1 schema to experiment schema |
| 2026-04-09 | v5 Phase 5.5 difficulty gate kept; Phase 6.5 external benchmark excluded from run scope |
| 2026-04-10 | Plugin infrastructure session: sync hook version hardcoding fixed, ml-journal plugin stabilized; session_id fallback (os.getppid()) added |
| 2026-04-10 | v5 preflight complete; Phase 0 → Phase 1 CASE_VERIFIER dispatched |
| 2026-04-11 | v5 Phase 7 post-mortem: answer-key leakage detected — orchestrator-mediated `issues_found` contaminated IDR/IDP scoring; isolated rescore via Claude Haiku corrected |
| 2026-04-11 | Honest v5 result confirmed: fc_lift = +0.0097, CI [−0.0013, +0.0217] — H1 FAILS; baseline ceiling (FC = 0.9452) is the primary cause |
| 2026-04-11 | v5 ensemble IDR suppression diagnosed: majority-vote IDR = 0.7679; union-of-issues IDR = 0.8725; a +0.5837 per-case recovery on 43/240 affected runs |
| 2026-04-11 | Post-mortems filed for four v5 structural weaknesses: closed-loop evaluator confound, same-model benchmark selection bias, insufficient statistical headroom, ensemble IDR suppression artifact |
| 2026-04-11 | v6 design decisions locked: ML Reproducibility Challenge as ground-truth source, GPT-4o primary scorer (cross-model), union-of-issues ensemble IDR, conditional FM gate, mixed-case pipeline, persona-biased condition |
| 2026-04-11 | v6 RC pipeline: 80 real MLRC papers fetched; 120 synthetic cases (IDs 702–821) generated at 100% yield; benchmark_cases_verified.json built (60 critique + 20 defense + 40 mixed) |
| 2026-04-11 | Phase 3 pilot (30 cases, GPT-4o scorer): pilot_fc_mean = 0.6500; H1a threshold set at 0.1000; hard stop gate passed |
| 2026-04-11 | v6 PLAN.md refactored from 602-line monolith into hub-and-spoke (1 index + 11 phase files + 5 reference docs) |
| 2026-04-11 | Phase 4 meta-debate self-review complete: ml-critic raised 8 PRE-N requirements; ml-defender responded; all closed in one round |
| 2026-04-11 | Phase 5: 2,160 files produced (6 conditions × 120 cases × 3 runs) via chunked concurrent agent dispatch (20 cases/chunk, 18 parallel agents/wave) |
| 2026-04-11 | Phase 6: GPT-4o semantic rescoring (IDR/IDP/ETD) complete; Phase 7+8 bootstrap analysis and sensitivity checks complete |
| 2026-04-11 | Phase 10 reporting complete: REPORT.md, REPORT_ADDENDUM.md, PEER_REVIEW_R1.md, FINAL_SYNTHESIS.md |
| 2026-04-12 | Peer review correction: unpaired → paired bootstrap; H2 regular converted from INCONCLUSIVE to FAIL (ensemble superior); H6 verdict corrected from FAIL to PASS (mixed direction) |
| 2026-04-12 | Post-session: formal ensemble_3x vs. baseline IDR test completed (`ensemble_vs_baseline_test.py`): CI = [+0.0426, +0.1648], PASS; three-way ordering fully grounded |

---

## What Was Tried

### v3 — Synthetic Benchmark, Mixed-Case Protocol (Pre-Journal)

Forty-nine synthetic cases across five flaw categories (broken_baseline, metric_mismatch, hidden_confounding, scope_intent, defense_wins) plus real_world_framing cases. Three conditions tested: isolated_debate, multiround, ensemble, baseline. Raw lift over baseline = +0.341, CI [+0.309, +0.371]. Cases included hard mixed-position cases where the ideal resolution was `empirical_test_agreed`. All debate conditions scored near ceiling (isolated mean = 0.975). External benchmark (16 published-paper and synthetic-grounded cases): 16/16 pass across all debate conditions.

### v4 — Halted After Phase 7

v4 was designed to address v3's calibration concerns. Halted before Phase 8 due to a baseline ceiling effect identical to the pattern that would recur in v5. Cases were still selected on Claude proxy scores, producing the same same-model bias documented later as a formal post-mortem. No publishable results.

### v5 — ARCH-1 Benchmark, Five Conditions

One hundred and ten synthetic binary-verdict cases (80 critique with planted flaws, 30 defense_wins with sound designs) across five conditions: baseline, isolated_debate, multiround, forced_multiround, ensemble. Three runs per case. Primary scorer: Claude Haiku (subsequently identified as same-family closed-loop confound).

**Answer-key leakage:** Original Phase 6 scoring collapsed IDR/IDP to ~1.0 across all conditions by passing orchestrator-generated `issues_found` alongside raw output to the scorer. Detected via isolation check; corrected via re-score of 996 files with an isolated scorer that received only raw agent output.

**Batch 2 contamination:** 165 files showed zero within-case variance (identical across all 3 runs) — evidence of a caching or replay artifact. Re-run clean.

**Honest result after correction:** fc_lift = +0.0097, CI [−0.0013, +0.0217]. H1 FAILS. Baseline FC = 0.9452 left only ~0.05 of headroom; the pre-registered threshold of +0.10 exceeded the available dynamic range.

**Forced multiround on hard cases:** FM hard mean = 0.9921 vs. MR hard mean = 0.9826; difference directional but not significant (W=12.5, p=0.376). Hollow-round rate = 20.5% on defense_wins cases — structurally vacuous because all points resolved in round 1.

**Ensemble IDR suppression:** Majority-vote IDR = 0.7679. Union-of-issues reanalysis recovered IDR to 0.8725, flipping ensemble FC from below baseline to above baseline. This was an aggregation artifact, not a genuine recall deficit.

**Cross-vendor validation (Phase 9):** GPT-4o-mini scorer vs. Claude on same outputs: IDR delta = −0.7737, meaning absolute IDR values are evaluator-relative. The closed-loop confound was real and large.

### v6 — RC Benchmark, Six Conditions, GPT-4o Scorer

Six conditions tested on 120 cases (80 regular: 60 critique + 20 defense; 40 mixed) × 3 runs = 2,160 outputs:

- **baseline**: single-pass critique; 1× compute
- **isolated_debate**: critic + defender independently; orchestrator adjudicates; ~3× compute
- **biased_debate**: same as isolated_debate but agents persona-primed (combative critic, selective defender); ~3× compute
- **multiround**: defender sees critic output; up to 4 rounds, natural stopping; ~3–6× compute
- **conditional_fm**: round 2 gated on unresolved disagreement (PRR < 1.0) after round 1; n=8 hard cases only
- **ensemble_3x**: 3 independent critics; union-of-issues IDR pooling; majority-vote verdict; 3× compute

Benchmark construction used three pipelines converging at `normalize_cases.py`: real RC/ReScience flaws (MLRC GitHub), synthetic regular cases (9-type flaw taxonomy, Gemini 2.5 Flash smoke validation), synthetic mixed cases (6-type ambiguity taxonomy with concrete empirical test specifications). H1a threshold set dynamically after Phase 3 pilot (max(0.03, min(0.10, (1.0 − 0.6500) × 0.5)) = 0.1000).

**Hypothesis H1: Debate persona-biasing (H6):** Pre-registered that persona-biased critique/defender agents would improve debate quality on ≥2/3 dimensions. Tested biased vs. isolated on IDR, IDP_adj, FVC_mixed.

**Hypothesis H3: Conditional FM gate:** Gate designed to fire round 2 only when PRR < 1.0 after round 1; tested on n=8 hard cases via Wilcoxon signed-rank.

**Hypothesis H4 (exploratory): ETD discrimination:** All debate conditions expected to produce structurally different empirical test specifications on mixed cases; GPT-4o ETD scorer used to discriminate quality.

**Formal ensemble vs. baseline test (post-session):** `ensemble_vs_baseline_test.py` ran paired bootstrap on IDR for ensemble_3x vs. baseline (n=60 critique cases), seeded, n=10,000 resamples.

---

## What Failed

### v3 Calibration Problems

v3's +0.341 raw lift was largely a measurement artifact. Three sources: (1) structural penalty in baseline scoring (DC=0.0 hardcoded for baseline by design); (2) ETD dimension drove the lift on mixed cases, but ETD is structurally inapplicable to non-debate conditions; (3) cases were easy enough that all debate conditions scored near-ceiling, eliminating discriminative power. Discovery `3a9d5a35`: "v3's +0.341 raw lift was almost entirely measurement artifact."

### v5 Answer-Key Leakage (Post-Mortem 45eee14b)

The Phase 6 scoring pipeline passed orchestrator-synthesized `issues_found` alongside raw agent output to the Claude scorer, giving the scorer pre-digested answers. This collapsed IDR/IDP to near-1.0 across all conditions and made the original null result appear to be a leakage artifact. Detection came from an audit of the scorer's input format. Remediation: 996 files re-scored using an isolated scorer receiving raw output only.

### v5 Closed-Loop Evaluator Confound (Post-Mortem bc3a08d0)

Claude generated debate outputs; Claude (Haiku) scored them. GPT-4o-mini cross-vendor validation revealed an IDR delta of −0.7737 between scorers on the same outputs — meaning absolute IDR values were evaluator-relative, not ground-truth quality measurements. v6 addressed this by using GPT-4o as the primary scorer for all semantic dimensions.

### v5 Same-Model Benchmark Selection Bias (Post-Mortem 358b7a5a)

Cases were filtered using Claude proxy scores (proxy_mean < 0.83), selecting for cases that Claude found moderately difficult. This created a sample that Claude-family scorers would be calibrated to, introducing bias toward the generation model family. v6 used Gemini 2.5 Flash for smoke validation and GPT-4o for difficulty calibration.

### v5 Baseline Ceiling Effect (Post-Mortem fee829a4)

Baseline FC = 0.9452 left only ~0.05 of headroom. The pre-registered threshold of +0.10 exceeded the available dynamic range, making H1 an uninformative test regardless of the protocol's true quality. v6 addressed this via a pilot-calibrated adaptive threshold, achieving pilot_fc_mean = 0.6500.

### v5 Ensemble IDR Suppression (Post-Mortem 3363672c)

Majority-vote IDR aggregation required 2/3 critics to flag an issue independently for it to count. This systematically suppressed recall: union IDR = 0.8725 vs. majority IDR = 0.7679. The suppression mischaracterized ensemble recall as a genuine deficit when it was an aggregation artifact. v6 adopted union-of-issues IDR from the outset.

### v5 Forced Multiround Hollow Rounds

20.5% of forced_multiround files on defense_wins cases produced `round2_verdict == round1_verdict` with `round2_points_resolved == 0` — structurally hollow because all points resolved in round 1. Three hard cases (eval_scenario_381, 411, 616) were additionally misclassified as `not_applicable_difficulty` and dispatched with null protocol, depressing `forced_multiround_hard_mean` from a true ~0.9957 to a reported 0.9425.

### v6 H1a: Debate Does Not Beat Baseline

FC lift = −0.0026, CI [−0.0108, +0.0059] (paired bootstrap, corrected). Not only does the debate protocol fail to surpass the pre-registered +0.10 threshold — it produces a negative point estimate. IDR is the primary driver: debate misses slightly more planted issues than baseline (0.6603 vs. 0.6712). DRQ and FVC are flat at 0.75 across four conditions, compressing the effective comparison to two of four FC dimensions.

### v6 H2: Debate Does Not Beat Compute-Matched Ensemble

FC delta (isolated_debate − ensemble_3x) = −0.0287, CI [−0.0434, −0.0154]. Excluding zero entirely in the ensemble-favored direction. At matched compute (3×), three independent assessors formally outperform one structured debate on the primary composite metric.

### v6 H3: Conditional FM Gate Does Not Improve Hard Cases

W=16.0, p=0.3677. The gate fires on 94.7% of cases (341/360 files) — mean PRR after round 1 is 0.418, far below the gate's implicit requirement of PRR = 1.0 for stop. The conditional gate provides no efficiency or quality advantage over full multiround. It is functionally equivalent to unconditional multiround.

### v6 H4: ETD Scorer Saturates

ETD = 1.0 for 100% of mixed cases across all three debate conditions. Every transcript contains the three structural elements (condition, supports_critique_if, supports_defense_if) that the GPT-4o ETD scorer checks. The metric measures presence/absence of structure, not quality, and provides zero discrimination.

### v6 Defense Case Failure

DRQ = FVC = 0.0 for all 20 defense cases uniformly across all conditions. The ml-critic agent has no "no significant issues found" output path; it always produces critique-framing output. This is a prompt calibration problem, not a statistical finding, but it means two dimensions of FC contribute zero signal on defense cases and the 20 defense cases become dead weight in the benchmark.

### v6 Multiround Instability

20 of 23 high-variance case-condition pairs belong to multiround. Several cases swing between FC = 0.0 and FC = 1.0 across three runs (e.g., rc_rescience_2020_schneider2021re: run means [1.0, 0.0, 0.0], variance = 0.2222). The adversarial iterative exchange is uniquely path-dependent.

### v6 Peer Review: Unpaired Bootstrap Error (Issue 3.1)

The initial Phase 7 analysis used an unpaired bootstrap across all hypothesis tests despite the design being fully paired (every case appears in every condition). The paired bootstrap narrowed CI width by approximately 18× for regular-case comparisons. This changed H2 regular from INCONCLUSIVE to FAIL (ensemble superior) and H6 IDP_adj from borderline to formally significant.

### Recurring Infrastructure Issues

**v3:** Agents invoked `python` instead of `uv run`, causing silent dependency failures; logging schema non-compliant with spec; two isolation breaches not logged.

**v4:** Preflight skill used relative paths (not absolute), causing glob misfire and parallel Bash cancellation cascades; CASE_VERIFIER output schema unspecified, causing script type errors; heredoc commit blocks triggered Claude Code security prompts on every invocation.

**v6 Phase 5:** Agent Write calls used relative paths for `v6_raw_outputs/`, causing double-nested directory errors (resolved: absolute path requirement added to cross-cutting rules).

---

## What Worked

### v3 — Protocol Produces Valid Debate Dynamics

Despite the calibration flaws, the v3 experiment demonstrated that the critic-defender-adjudicator mechanism works mechanically: isolation checks passed (after re-runs), agent concession arcs were observed in qualitative review, and all 16 external benchmark cases (published-paper and synthetic-grounded) scored perfectly across all debate conditions. The mechanism produces debate; the question was always whether it produces better analysis.

### v5 — Leakage Detection and Correction

The answer-key leakage in Phase 6 was detected through an auditing pipeline (`check_isolation.py`) and corrected by an isolated re-scorer, demonstrating that within-experiment error detection is feasible. The corrected result (fc_lift = +0.0097) is an honest null result, not an artifact.

### v5 — Union IDR Recovery

Post-hoc reanalysis via `union_idr_analysis.py` recovered ensemble IDR from 0.7679 (majority-vote) to 0.8725 (union-of-issues), a +0.1046 recovery. This finding directly informed v6's ensemble design (union-of-issues IDR from the outset) and is the most consequential single discovery in the series.

### v6 — Ensemble Formally Outperforms Isolated Debate

H2 regular: FC delta = −0.0287, CI [−0.0434, −0.0154], excluding zero. At matched compute, three independent assessors with union-of-issues pooling outperform one structured debate on both recall (IDR = 0.7717 vs. 0.6603) and precision (IDP = 0.9861 vs. 0.9444). This is the strongest positive finding in the series and is formally supported.

### v6 — Ensemble Formally Outperforms Baseline (Post-Session)

`ensemble_vs_baseline_test.py` (paired bootstrap, n=60 critique cases): IDR diff = +0.1005, CI [+0.0426, +0.1648]. The three-way ordering is now fully grounded: ensemble_3x > {baseline ≈ isolated_debate}. Isolated debate is strictly dominated at 3× compute.

### v6 — Multiround Helps Mixed Cases

Multiround achieves FVC_mixed = 0.3667, versus baseline = 0.0 and isolated_debate = 0.0083. The iterative exchange structurally enables agents to recognize empirical ambiguity and produce `empirical_test_agreed` outcomes. This is a real architectural advantage unavailable to ensemble or single-pass approaches.

### v6 — Biased Debate Improves Mixed FVC

H6 FVC_mixed: delta = +0.2417, CI [+0.1583, +0.3417], p = 0.0000, survives Bonferroni correction (threshold at 8-test level = 0.00625). Combative-critic and selective-defender personas reliably push agents toward empirical test specification on mixed cases. Isolated debate without persona priming produces FVC_mixed ≈ 0.0083.

### v6 — Pre-Registration Held

All hypotheses, thresholds, and scoring rules were committed to `HYPOTHESIS.md` before Phase 5 (benchmark run). The H1a threshold was set adaptively from Phase 3 pilot data and documented in git before the main run. The pre-registration was intact through peer review.

### Infrastructure — ml-journal Plugin

The ml-journal plugin (journal.jsonl, log_entry.py, journal_query.py, checkpoint/resume/log-list/log-summarize/research-report skills) operationalized structured session logging, enabling reproducible experiment audit trails, unresolved-issue surfacing, and cross-session state recovery. PostToolUse hooks automate sync between plugin source and installed cache.

---

## Key Decisions

| ID | Date | Decision | Rationale |
|----|------|----------|-----------|
| fe9e84a3 | 2026-04-09 | Remove IDJ (Issue Detection Justification) dimension from v5 scoring engine | Dimension added no signal independent of IDR; removed to simplify scoring |
| 523adf7f | 2026-04-09 | Write normalize_cases.py to transform ARCH-1 pipeline output schema → experiment schema | ARCH-1 pipeline used flat schema; experiment scripts expected nested schema |
| 9723bed9 | 2026-04-09 | Exclude Phase 6.5 external benchmark from v5 run | No case file, no analysis path, no schema defined — stub only |
| 2e525f35 | 2026-04-09 | Keep Phase 5.5 difficulty gate for v5 run despite ARCH-1 empirical difficulty labels | Gate calibration retained even though ARCH-1 labels were empirically validated |
| 3fc05885 | 2026-04-11 | Re-scorer architecture: async OpenRouter calls with asyncio.Semaphore(100), not parallel subagents | Subagent parallelism too slow for 996-file rescore; async I/O with rate limiting faster |
| b57177be | 2026-04-11 | Use ML Reproducibility Challenge reports as ground-truth source for v6 benchmark cases | Replaces synthetic planted corruptions with real documented flaws requiring genuine analytical judgment |
| 0192f428 | 2026-04-11 | Change ensemble IDR aggregation to union-of-issues for v6 | Corrects v5 suppression artifact; majority-vote IDR drops recall without any quality benefit |
| b117d517 | 2026-04-11 | v6 orchestrator DEFAULT_MODELS assigned to eliminate same-model/family bias across all pipeline stages | PM3 mitigation: Gemini 2.5 Flash for smoke validation, GPT-4o for scoring, to break Claude-evaluating-Claude confound |
| b4bf959e | 2026-04-11 | Use ReScience/MLRC GitHub repo as sole RC source | OpenReview API (v1 and v2) returns 403 for all unauthenticated requests |
| 87d086b1 | 2026-04-11 | H2 FAIL criterion tightened: requires CI excluding zero, not just directional majority | Strengthens pre-registration; prevents INCONCLUSIVE from being treated as passing |
| 09206a5b | 2026-04-11 | Phase 5 dispatch via Claude Code Agent tool; no Python API script; no adjudicator Python wrapping | Adjudicator role must be inside the debate agent, not a separate Python layer |
| d5f936ea | 2026-04-11 | Phase 5 benchmark uses chunked concurrent agent dispatch: 20 cases/chunk, 18 parallel agents/wave | Sequential dispatch would have taken too long for 2,160 runs; chunking prevents context overflow |
| 1c0a75a6 | 2026-04-10 | Peer review depth for v5: single Opus round, conditional Round 2 not required | Research-reviewer Opus provides sufficient coverage; second round reserved for major unresolved issues |
| 654819e4 | 2026-04-10 | Use os.getppid() as session_id fallback in journal_log.py | Terminal PPID is stable within a session and does not require environment variable setup |

---

## Issues and Resolutions

### Resolved

**v5 Answer-Key Leakage (issue 45eee14b → resolution 310659cd)**
Orchestrator-mediated `issues_found` contaminated IDR/IDP scoring. Resolved via isolated re-scorer (Claude Haiku receiving raw output only, no pre-processed issue list). 996 files rescored. Corrected fc_lift = +0.0097.

**v5 Ensemble IDR Suppression (issue bb27d940 → resolution db747010)**
`score_run` ensemble IDR used synthesized output only; union-of-issues aggregation requires per-critic found booleans. Resolved in v6 design: `compute_ensemble_union_idr()` in poc.py uses per-assessor found booleans from the outset.

**v6 Ensemble Naming Inconsistency (issue 0597f24a → resolution b1be4933)**
poc.py CONDITIONS used `'ensemble'` while HYPOTHESIS.md pre-registered `'ensemble_3x'`. Resolved: renamed throughout poc.py.

**v6 normalize_cases.py superset check (issue fb119998 → resolution bfbb9c1f)**
`_normalize_synthetic_mixed()` used superset check `set(ar) > {"empirical_test_agreed"}` for acceptable_resolutions, incorrectly rejecting cases with additional valid resolutions. Resolved: changed to inequality check (set must include empirical_test_agreed, not equal it).

**v6 Absolute path enforcement (issue 3728e4b1 → resolution 4365ec7c)**
Phase 5 agent Write calls used relative paths for `v6_raw_outputs/`, causing double-nested directory creation. Resolved: absolute path requirement added to Phase 5 cross-cutting rules.

**v6 Adaptive H1a threshold (issue 6e1d23ae → resolution 4e80115a)**
poc.py hardcoded `fc_lift >= 0.10` instead of HYPOTHESIS.md adaptive threshold. Resolved: adaptive threshold formula added to poc.py; `benchmark_passes` function updated.

**v6 H1b FVC analysis missing (issue 8ef9ed66 → resolution 697d1481)**
poc.py missing H1b FVC mixed-case analysis block despite H1b being a co-primary hypothesis. Resolved: H1b FVC analysis block added to summary output.

**v6 Paired bootstrap correction (PEER_REVIEW_R1 Issue 3.1)**
Initial Phase 7 analysis used unpaired bootstrap across all tests. Resolved: `bootstrap_paired_mean_diff` implemented in `v6_analysis.py`; all hypothesis tests re-run. Verdicts corrected: H2 regular INCONCLUSIVE → FAIL (ensemble superior); H6 IDP_adj borderline → significantly negative.

### Unresolved

**ensemble_3x confidence-tiered output (issue c9dfc257, 2026-04-12)**
Union IDR gives equal weight to minority-flagged issues (1/3 critics) and majority-flagged (2/3). A confidence-tiered output layer would let downstream consumers distinguish high-confidence from low-confidence findings. No implementation path yet defined.

**Multiround variance — stabilization path (noted in REPORT_ADDENDUM.md)**
20/23 high-variance case-condition pairs are multiround; several cases oscillate between FC = 0.0 and FC = 1.0. Temperature reduction and adjudicator prompt hardening are recommended; no formal stabilization work done.

**ETD sub-element rubric (identified in FINAL_SYNTHESIS.md)**
ETD = 1.0 for 100% of debate outputs. A finer-grained rubric is required before mixed-case quality is quantifiable. No redesign yet.

**Defense case exoneration path (identified in next_steps.md)**
All conditions score DRQ = FVC = 0.0 on defense cases. ml-critic has no "no significant issues found" output path. Requires prompt redesign before defense cases can be used as benchmark cases.

**ml-lab.md dispatch syntax (issue b16abd51)**
ml-lab.md uses subagent_type dispatch syntax not applicable to the Agent tool. Low priority; functional workaround in place.

---

## Current State

**v6 is complete.** Phase 10 (reporting) is done. REPORT.md, REPORT_ADDENDUM.md, PEER_REVIEW_R1.md, FINAL_SYNTHESIS.md, CONCLUSIONS.md, and next_steps.md are all written and committed. The paired bootstrap correction has been applied. The formal ensemble-vs-baseline test is complete. The three-way ordering (ensemble_3x > baseline ≈ isolated_debate) is fully grounded.

**v6 artifact status:**
- `FINAL_SYNTHESIS.md` — authoritative post-review summary with corrected verdicts
- `CONCLUSIONS.md` — updated with paired bootstrap verdicts for H2 and H6
- `REPORT.md` — reflects pre-correction analysis; FINAL_SYNTHESIS.md supersedes on corrected verdicts
- `REPORT_ADDENDUM.md` — production deployment recommendation (ensemble for regular, multiround for mixed)
- `next_steps.md` — v7 priority order with formal test results

**ml-journal plugin:** Active, version-synced via PostToolUse hook. Skills: log-entry, log-list, log-summarize, checkpoint, resume, log-status, research-report, research-note, log-commit.

---

## Open Questions

The following open threads are aggregated across checkpoints and current unresolved issues, deduplicated, oldest first:

1. **Journal cross-category query mode** (issue c1401026, 2026-04-09): journal_query.py has no cross-category mode; cannot summarize the most recent entries of any type in one call. Tooling limitation for future sessions.

2. **ml-lab.md peer review round cap alignment** (issue f357f5b2, 2026-04-10): PLAN.md says 2 peer-review rounds; ml-lab.md says 3. Minor inconsistency in the plugin documentation.

3. **readme-rewriter never dispatched** (issue f7293738, 2026-04-10): Listed in PLAN.md agent rule but not dispatched in any v5 or v6 phase. If README readability is a goal, this step was skipped.

4. **multiround stabilization before mixed-case deployment**: Temperature reduction, fixed-seed inference, and adjudicator stopping checklist are required before multiround can be reliably deployed for mixed/ambiguous cases (REPORT_ADDENDUM.md). Specific implementation not yet designed.

5. **ETD sub-element rubric design**: A finer-grained ETD rubric (specificity, falsifiability, orthogonality dimensions) is required before ETD provides useful signal. The current scorer saturates at 1.0 for all debate outputs (next_steps.md item 4).

6. **Defense case exoneration path**: ml-critic produces critique-framing output in all cases; no output path for "no significant issues found." Required before defense cases can contribute meaningful signal to the benchmark (next_steps.md item 5).

7. **Confidence-tiered ensemble output** (issue c9dfc257, 2026-04-12): Distinguish majority-flagged (2/3 critics) from minority-flagged (1/3) issues in ensemble output without reintroducing adversarial suppression. Design question open.

8. **Full difficulty labeling** (next_steps.md item 3): Only 15/80 regular v6 cases carry difficulty labels; H3 was chronically underpowered (n=8 hard cases). Full labeling is required for stratified analysis in v7.

9. **v7 entry point undefined**: The next_steps.md v7 priority order is written (stabilize multiround, full labeling, ETD rubric, defense exoneration, confidence-tiered ensemble). No v7 PLAN.md or experiment directory exists yet.

10. **Formal ensemble vs. multiround test for mixed cases**: H2 mixed FVC remains INCONCLUSIVE (CI spans zero). The question of whether ensemble or multiround is better on mixed cases has no formal answer yet.
