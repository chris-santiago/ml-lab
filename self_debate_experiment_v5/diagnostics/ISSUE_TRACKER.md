# V5 Calibration Issue Tracker

**Last updated:** 2026-04-07
**Purpose:** Canonical summary of all issues flagged during v5 pre-experiment calibration. Use this as the re-entry point when continuing work.

---

## Status at Last Update

- Smoke tests run: V1 (1xx) → V2 (2xx) → V3 (2xx + IDJ) → V4 (batch3, Lever A+B) → V5 (batch3, paragraphs removed)
- Gate result across all runs: **FAIL** — critique/mixed ceiling at 1.000 in every run
- Infrastructure (scripts, phases, agents): **READY** — all preflight checks pass
- Only blocker: case difficulty calibration

---

## Open Issues (Blockers)

### OPEN-1 — Critique/mixed cases ceiling at 1.000 across all smoke test runs
**Severity:** Critical — blocks Phase 5.5 gate  
**Source:** V1–V5 smoke tests  
Haiku scores 1.000 on all critique/mixed cases in every run regardless of intervention. Five runs, five failures. The gate requires ≥9/14 cases below 0.55; best result was 1/14 (case 302, V5 at 0.75 from a compound-issue IDR miss).

### OPEN-2 — Flaw mechanisms are surface-readable: well-known ML pitfalls
**Severity:** Critical — root cause of OPEN-1  
**Source:** HAIKU_SMOKE_TEST_REAL_PAPER_V5.md  
The underlying issue types (data leakage, benchmark overfit, verification bias, calibration circularity, informative censoring, spectrum bias) are well-established ML failure modes. Haiku identifies them from a well-written description alone without domain expertise or multi-step inference. Removing the evaluative paragraph (V5) confirmed this: format was necessary but not sufficient. The cases need flaws that require genuine domain knowledge or non-obvious causal chains to detect.  
**Next step:** Requires user decision on case design direction. Options include: (a) domain-obscured flaws where the mechanism only looks wrong if you know the field-specific norm, (b) multi-step causal chains distributed across longer prompts, (c) accept the ceiling and proceed — treat the experiment as measuring lift above a high-performing baseline.

### OPEN-3 — Case text pre-empts correct verdict via hedge language
**Severity:** High  
**Source:** HAIKU_SMOKE_TEST_REAL_PAPER_V4.md, CASE_FORMAT_DIAGNOSTIC.md  
Even after evaluative paragraph removal (V5), the methodology descriptions are written clearly enough that Haiku reads the flaw mechanism directly and routes to `empirical_test_agreed`. The case text does not need to say "the problem is X" — describing the method accurately is enough. Related to OPEN-2.

### OPEN-4 — Trigger phrase prohibitions undefined in generation prompt
**Severity:** High — will cause future generation compliance failures  
**Source:** CASE_FORMAT_DIAGNOSTIC.md  
`REAL_PAPER_CASE_GENERATION_PROMPT.md` references "v5 trigger phrase prohibitions" in Step 3 but never defines them. The generator produced the exact forbidden pattern ("A pattern-matching reviewer could stop here and complain that X, yet in this domain Y...") in every batch3 case. Before any re-generation, the prohibited constructions need a concrete list with examples in the prompt itself.

### OPEN-5 — Generation prompt self-evaluation checks not enforced
**Severity:** High — will cause future generation compliance failures  
**Source:** CASE_FORMAT_DIAGNOSTIC.md  
The Skimming Test (line 576) and Quality Standard (line 606) exist in the generation prompt but the generator either skipped them or ran them without recognizing violations. The batch3 cases fail both tests, yet were output. Self-evaluation instructions need to be restructured so violations are mechanically checkable, not just described.

### OPEN-6 — Defense_wins stochasticity: calibration reference uncertain
**Severity:** Moderate  
**Source:** V3, V4 smoke tests; operative baseline is V2  
V2 showed defense_wins mean=0.467 (4/5 cases scoring 0.33 — Haiku invented flaws). V3 and V4 re-runs showed all 5 cases 1.00 (all correctly defended). V5 also 1.00. Multiple lucky rolls create uncertainty about whether the 2xx defense_wins cases are well-calibrated or just stochastically stable. Operative assumption: V2 calibration is correct; V3/V4/V5 are lucky rolls.

### OPEN-7 — batch3 cases (real_paper_cases_batch3.json) not yet the canonical file
**Severity:** Moderate — procedural  
**Source:** This session  
The edited batch3 cases are in `synthetic-candidates/real_paper_cases_batch3.json`. The original `real_paper_cases.json` (2xx cases) is also in `synthetic-candidates/`. `benchmark_cases.json` at the experiment root currently merges all three JSON files (78 cases total: real_paper + openai_benchmark + batch3). Clarify which cases are authoritative before Phase 0 — the 3xx cases are the most recent but haven't passed the gate.

---

## Resolved Issues

### RESOLVED-1 — IDP definition mismatch (proxy vs. actual engine)
**Fix:** Added IDJ dimension to capture justification quality separately. Implemented in `self_debate_poc.py`, phase files, and `write_preregistration.py`.

### RESOLVED-2 — IDJ not in scoring engine, phase files, or pre-registration
**Fix:** Full implementation per CALIBRATION_DIAGNOSTIC.md Section 12. All 5 files updated. See CALIBRATION_CHANGES_SUMMARY.md.

### RESOLVED-3 — Gate interpretation (bimodal distribution misread as batch failure)
**Fix:** Pre-registered stratum analysis added. Gate interpretation updated to account for critique-ceiling / defense-floor distribution. Stratum diagnostic table added to phase_05_5_difficulty_gate.md.

### RESOLVED-4 — Defense_wins baseline scoring error (0.33 vs 0.00 in actual engine)
**Fix:** Corrected in CALIBRATION_DIAGNOSTIC.md Section 10 projected scores. Actual engine scores 0.00, not 0.33, when Haiku incorrectly condemns a defense_wins case.

### RESOLVED-5 — Lever A did not create FVC=0 events
**Fix:** Root cause identified (case text pre-signals verdict). Lever A is correctly implemented in metadata but cannot fire if the task_prompt leads the evaluating model to the correct verdict regardless.

### RESOLVED-6 — Lever B did not create IDP=0 events
**Fix:** Root cause identified (case text pre-emptively defuses false alarms). Lever B is correctly implemented in metadata but cannot fire if the task_prompt explains why must_not_claim items are wrong.

### RESOLVED-7 — Evaluative analysis paragraphs in batch3 task_prompts
**Fix:** Surgically removed from eval_scenario_301–309. Cases now end in team-advocacy voice. V5 smoke test confirmed format is better but difficulty ceiling persists (OPEN-1/OPEN-2).

### RESOLVED-8 — Relative paths breaking from repo root
**Fix:** CWD rule in PLAN.md; all phase files updated with `cd` preamble and absolute-path invocations.

### RESOLVED-9 — CASE_VERIFIER output schema unspecified
**Fix:** Explicit JSON schema added to phase_01_case_verifier.md.

### RESOLVED-10 — log_entry.py `--meta` argument triggers approval prompts
**Fix:** `--meta-file` argument added; JSON passed via temp file.

### RESOLVED-11 — Phase 6 agents attempting direct API calls
**Fix:** PLAN.md Rule 4 added; subagent context reminder added to all 19 phase files.

### RESOLVED-12 — Hardcoded task prompts dispatched instead of JSON-sourced
**Fix:** CRITICAL DISPATCH RULE added to phase_06_benchmark_run.md. Pre-dispatch integrity check added.

### RESOLVED-13 — Malformed JSON in output files
**Fix:** Mandatory post-write validation added (read-back + key check + re-dispatch on failure).

### RESOLVED-14 — V4 inverted Spearman rho
**Fix:** Preliminary Spearman check added to phase_05_5_difficulty_gate.md. V5 cases define difficulty via rubric performance, not estimated labels.

### RESOLVED-15 — V4 script bugs (list comprehension scope, None comparison)
**Fix:** Copied post-fix scripts to v5. Cosmetic cleanup applied to stats_analysis.py line 123.

### RESOLVED-16 — V5 plan missing v4 debate insights
**Fix:** phase_02_hypothesis.md updated (compute-matched removed, H2 reframed, information asymmetry documented). write_preregistration.py updated.

---

## What the Next Session Needs to Decide

The infrastructure is ready. The only path to Phase 0 goes through the difficulty problem (OPEN-1 / OPEN-2). Three options:

**Option A — Redesign cases around domain-obscured flaws**
Cases where the flaw mechanism only looks wrong if you know a field-specific norm Haiku lacks (e.g., regulatory thresholds, domain-standard independence assumptions, operator conventions). Highest effort; highest likelihood of actually passing the gate.

**Option B — Accept ceiling, reframe the experiment**
Treat the high Haiku baseline as a feature, not a bug. The experiment measures lift above a strong unstructured-reader baseline — if debate adds signal on top of that, it still demonstrates value. Requires updating the gate criterion or removing the proxy gate entirely.

**Option C — Switch calibration model**
Use a weaker model (e.g., a smaller open-source model) as the gate criterion model instead of Haiku. Haiku may simply be too capable for this task domain. Requires understanding what model capability level is actually the target.

---

## Resolved by Pipeline Design

### RESOLVED-BY-DESIGN — Same-model circular bias in case generation
**Concern:** If Claude generates the benchmark cases and Claude debates them, the generating model implicitly calibrates cases to its own blind spots. Flaw mechanisms would be shaped by Claude's prior over "what looks like a flaw," making the benchmark a test of Claude's self-knowledge rather than debate quality.

**Resolution:** Already the practice since v2 — GPT has been used for case generation throughout the experiment. The generation prompt header has always specified non-Anthropic LLM use. The modular pipeline formalizes this workflow but did not introduce it. GPT generates the cases, Claude debates them — different architectures, different priors, clean cross-model design by design from the start.

**Residual:** The pipeline instructions (flaw taxonomy, decoy requirements, stage logic) were written by Claude, so Claude's fingerprint is on the scaffold even if not the output. This is a weaker bias and arguably unavoidable — someone has to design the benchmark methodology. The execution is cross-model; the meta-design is not.

**Empirical check:** Whether GPT transpositions are genuinely harder for Claude than Claude's own transpositions would be is an open empirical question — the smoke test will answer it.

---

## OPEN-8 — DEFAULT_MODELS diversity refactor solves assumed bias not supported by evidence

**Severity:** Moderate — the v5 pipeline design rests on an assumption (family-level circular bias) that empirical recycling data contradicts; no current results are invalidated but the refactor may be unnecessary complexity  
**Source:** orchestrator.py DEFAULT_MODELS; Stage-2/3 recycle observations

The DEFAULT_MODELS refactor switched from an all-GPT-5.4 lineup to a multi-family configuration (DeepSeek Stage 1, Qwen Stages 2/4, OpenAI Stage 3, Anthropic Stages 5/smoke) on the grounds that 14/15 smoke test failures implied family-level circular bias — same-family models unable to catch their own generation artifacts.

Empirical evidence now contradicts the circular-bias framing. Recycling Stage-3 failures back through Stage 3 with the same model fixed 10 of the 14 failing cases. The remaining 4 are being resolved by recycling through Stage 2. If circular bias were the operative mechanism, re-running the identical model at the same stage would not fix the cases — the bias would reproduce the same failure. The observed pattern is consistent with stage-level quality variance (stochastic generation failures at a specific pipeline stage), not a structural family-bias problem.

This means:

1. The multi-family lineup may be solving a non-existent problem. The diversity adds coordination risk (cross-family formatting inconsistencies, different refusal patterns per vendor) without demonstrated benefit.
2. The actual fix is a robust recycle/retry path at Stages 2 and 3. The orchestrator currently has no built-in recycle logic — failures at smoke test require manual re-entry at the correct stage. That manual path is what produced the 10/14 recovery.

The refactor is not harmful per se, but it should not be treated as the primary mitigation for smoke test failures. The absence of an automated recycle path is the higher-priority gap.

**Next step:** Add an automated recycle path at Stages 2 and 3 in `orchestrator.py` before the main v5 run. Separately, evaluate whether the multi-family DEFAULT_MODELS lineup is warranted once the recycle path is in place — if failures drop to near-zero under retry, revert to a homogeneous lineup and close the diversity question empirically. Reframe DEFAULT_MODELS comments in `orchestrator.py` — current comments imply circular bias is confirmed; change to reflect that diversity is a precaution, not a proven fix.

---

## OPEN-9 — Technical report on synthetic case generation methodology not yet written

**Severity:** Minor — documentation debt; no current results affected; only actionable if pipeline is validated  
**Source:** Multi-stage orchestrator design process; GPT-5.4 all-stages baseline failure (14/15 smoke test failures); smoke test threshold change

**Condition:** This issue should be actioned only if the v5 benchmark run confirms the multi-stage orchestrator produces a sufficient number of cases passing the smoke test gate.

The synthetic case generation pipeline evolved through a non-trivial architectural redesign. The initial implementation used GPT-5.4 and GPT-5.4-mini at every stage, producing 14/15 smoke test failures. The root causes — stage-level quality variance, absence of a recycle path, insufficient separation of concerns — were not obvious from the initial failure signal and required iterative diagnosis. The current multi-stage orchestrator (Stages 1–6) with recycle paths at Stages 2 and 3 represents a substantially different design whose principles are not documented anywhere in the project artifacts.

If the pipeline is validated, a technical report should be written covering:

1. **GPT-5.4 all-stages baseline** — what each stage produced, where failures occurred, and what the smoke test results showed
2. **Architectural evolution** — which stages were added or restructured and what specific problem each change addresses
3. **Current working design** — stage-by-stage breakdown of Stages 1–6
4. **Design principles** — separation of concerns, recycle path as the primary reliability mechanism, smoke test as quality gate, model diversity as a precaution (with OPEN-8 caveat that circular bias remains unconfirmed)
5. **Threshold comparability caveat** — the smoke test acceptance threshold was raised from 0.4 to 0.55 in the refactored orchestrator; pass rates are not directly comparable to prior methods or versions without adjusting for this change; any cross-version comparison must account for the threshold delta

**Next step:** If and only if the v5 benchmark run validates the pipeline, write the report to `self_debate_experiment_v5/diagnostics/CASE_GENERATION_METHODOLOGY.md`. All pass rate comparisons to previous pipeline versions must explicitly note the 0.4 → 0.55 threshold change.

---

## OPEN-10 — `difficulty_idr` recycle routed to Stage 2 when mechanism is the problem

**Severity:** High — wrong recycle target wastes recycle budget without addressing root cause  
**Source:** Batch 328–342 observations; mech_001 EXHAUSTED after 2 Stage 2 recycles at IDR=1.0  

When IDR=1.0 fires, the previous routing sent the case to Stage 2 (new scenario) with a note asking for "deeper domain embedding." This is the wrong abstraction level: if the abstract mechanism extracted at Stage 1 is too recognizable (e.g., Obermeyer proxy-variable bias, Dacrema RecSys comparison), a new scenario framing around the same mechanism will still be IDR=1.0. The mechanism itself needs to be re-generated with a different domain transposition, not just re-staged.

Evidence: mech_001 (Obermeyer et al.) exhausted 2 Stage 2 recycles and was dropped, all three attempts at IDR=1.0. mech_005, mech_007, mech_014 showed same pattern in the same batch.

**Fix applied (2026-04-08):** `difficulty_idr` recycle now routes to Stage 1. Added `run_stage1_recycle()` to orchestrator — re-generates blueprint using same source but forces completely different domain transposition, then re-runs fact_mixer before continuing to Stage 2. `recycle_action()` routing updated; `run_case()` now handles `stage == "stage1"` at top of retry loop.

---

## OPEN-11 — Stage 1 transposition depth insufficient for well-known paper mechanisms

**Severity:** High — root cause of persistent IDR=1.0 wall across batches 313–342  
**Source:** Batches 313–327 (5/7 critique IDR=1.0) and 328–342 (similar pattern despite model swap)  

The Stage 1 prompt instructed domain transposition but did not specify depth. Mechanisms from famous ML papers (Obermeyer et al. 2019, Dacrema et al. 2019, Ziegler et al. RLHF) are well-established failure modes that Haiku recognizes from a well-written description alone, even after domain relabeling. Transposing "proxy variable bias in healthcare" to "proxy variable bias in insurance" produces a memo that is equally obvious. The mechanism's surface form must change, not just its domain label.

Swapping Stage 3 from GPT-5.4 to DeepSeek v3.2 did not improve IDR — confirming the problem is at Stage 1, not Stage 3.

**Fix applied (2026-04-08):** Stage 1 prompt (`stage1_mechanism_extractor.md`) updated with explicit transposition depth requirement: ≥2 layers of domain-specific context, flaw detectable only via regulatory/field-specific knowledge, and explicit prohibition on shallow transpositions to adjacent ML application domains. Stage 1 recycle path (OPEN-10 fix) provides a retry mechanism when this requirement isn't met.

---

## OPEN-12 — Stage 2 fact placement has no positional constraints; flaw facts can surface early

**Severity:** High — contributes to IDR=1.0 by allowing flaw facts in high-visibility paragraph positions  
**Source:** Batch 313–342 recycle patterns; memo structure analysis  

The Stage 2 prompt said "distribute facts across paragraphs" and "don't cluster all facts in one paragraph" — but imposed no hard positional constraint. The scenario architect frequently assigned methodologically significant facts (where flaws live) to paragraph 2 (the "addressing concerns" paragraph), which the memo writer then featured prominently. A fact described at the top of the memo is trivially findable; IDR=1.0 follows mechanically.

**Fix applied (2026-04-08):** Stage 2 prompt (`stage2_scenario_architect.md`) updated with hard placement constraints: at most 2 facts in paragraphs 1–2 combined; at least 2 facts assigned to paragraph 4; model architecture / validation design / data preprocessing facts restricted to paragraphs 3–4 only; no two methodologically significant facts may be consecutive in the same paragraph.
