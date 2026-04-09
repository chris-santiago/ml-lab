# V5 Calibration Issue Tracker

**Last updated:** 2026-04-08 (post-ARCH-1 scoring revision; OPEN-18 added)
**Purpose:** Canonical summary of all issues flagged during v5 pre-experiment calibration. Use this as the re-entry point when continuing work.

---

## Status at Last Update

- Smoke tests run: V1 (1xx) → V2 (2xx) → V3 (2xx + IDJ) → V4 (batch3, Lever A+B) → V5 (batch3, paragraphs removed) → **Pipeline batches 313–342 (pre-fix), 343–357 (post-fix), 358–372 (famous sources retired), 373–387 (first test of four prompt fixes)**
- Gate result: **FLAT** — IDR=0.0 trend: 0/8 → 3/9 → 4/9 → 3/8 across last four batches; four prompt fixes (OPEN-16) did not improve IDR=0.0 rate
- **PIPELINE REDESIGN DECISION (2026-04-08):** The entire case generation approach is being replaced. See ARCH-1 below. All previous batches (3xx) are superseded — wrong document type. No further batches will be run under the old pipeline.
- Infrastructure (scripts, phases, agents): **READY** — will be repurposed for new pipeline
- Active work: Design new two-node pipeline (ARCH-1)

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

**Empirical result (batch 343–357, 2026-04-08):** Fix partially effective. 3/9 critique/mixed cases achieved IDR=0.0 (mech_004/Ziegler, mech_007/Dacrema, mech_014/Caruana). 6/9 still IDR=1.0, all from the most famous papers (Obermeyer, DeGrave, Lazer, Zech, plus two pattern sources). Pattern is source-dependent, not stage-dependent — see OPEN-14.

---

## OPEN-12 — Stage 2 fact placement has no positional constraints; flaw facts can surface early

**Severity:** High — contributes to IDR=1.0 by allowing flaw facts in high-visibility paragraph positions  
**Source:** Batch 313–342 recycle patterns; memo structure analysis  

The Stage 2 prompt said "distribute facts across paragraphs" and "don't cluster all facts in one paragraph" — but imposed no hard positional constraint. The scenario architect frequently assigned methodologically significant facts (where flaws live) to paragraph 2 (the "addressing concerns" paragraph), which the memo writer then featured prominently. A fact described at the top of the memo is trivially findable; IDR=1.0 follows mechanically.

**Fix applied (2026-04-08):** Stage 2 prompt (`stage2_scenario_architect.md`) updated with hard placement constraints: at most 2 facts in paragraphs 1–2 combined; at least 2 facts assigned to paragraph 4; model architecture / validation design / data preprocessing facts restricted to paragraphs 3–4 only; no two methodologically significant facts may be consecutive in the same paragraph.

---

## OPEN-16 — Flaw facts still pattern-matchable in isolation; compound relationship encoded in phrasing

**Severity:** High — root cause of persistent IDR=1.0 wall after source retirement and transposition fixes  
**Source:** Cross-batch IDR analysis 2026-04-08; residual wall on Sources 6, 8, 9, 11, 13

After retiring famous papers and adding transposition depth requirements, 5/9 critique/mixed cases still hit IDR=1.0 in batch 358-372. Root cause: flaw facts are phrased in ways that are individually recognizable as ML pitfalls ("SMOTE applied before CV"), and compound facts encode their relationship in a single sentence — allowing pattern-matching without cross-paragraph synthesis.

Two sub-problems:
1. **Relationship encoding in compound phrasing:** "X was applied before Y" states the problematic ordering explicitly. A model pattern-matches to the known failure mode in one sentence. The compound mechanism (requiring synthesis across paragraphs) is bypassed.
2. **Uniform fact prominence:** Flaw facts, decoy facts, and neutral facts appear with equal prominence in the memo. A model scanning for the most notable or unusual methodology detail can identify the flaw by its relative distinctiveness rather than by domain reasoning.

**Fixes applied (2026-04-08, commit 820479b):**

*Stage 1 — Compound fact relationship stripping:*
- `neutralized_phrasing` must describe exactly one action with no temporal/causal/sequential connector to its compound pair
- Explicit prohibited patterns: "before", "after", "following", "which was then used for", "prior to"
- Bad/good example added; old example ("SMOTE applied before the k-fold loop") replaced — it was actively teaching the wrong output

*Stage 3 — Three new Difficulty Requirements:*
- **Rule 1 (compound isolation):** Compound facts must never appear in the same sentence, adjacent sentences, or be linked by any connector implying their relationship. Reader must assemble the compound picture by connecting facts across paragraphs.
- **Rule 2 (prominence inversion):** Decoy concern gets the most quantified, explicitly-rebutted treatment in paragraph 2. Flaw facts appear at exactly the same specificity level as surrounding non-flaw sentences — nothing distinguishes them.
- **Rule 3 (authoritative wrong justification):** The addressed-but-incorrectly fact gets a justification written with maximum authority — citing the domain standard by name, including specific numbers, written as the team's most carefully considered statement. Should be initially convincing; error only visible with domain-specific knowledge.

*Stage 2 — Two new output fields:*
- `decoy_prominence_note`: which fact(s) are decoys, with instruction to memo writer to give them dominant treatment
- `authoritative_justification_note`: which fact has the wrong justification, with instruction to write it with maximum authority

**First test result (batch 373–387, 2026-04-08):** Fixes did not improve IDR=0.0 rate. 3/8 accepted critique/mixed achieved IDR=0.0 (Source 1/Dacrema, Source 13, Source 11) vs. 4/9 in prior batch. IDR=0.0 trend: 0/8 → 3/9 → 4/9 → 3/8 — essentially flat.

New pattern: IDR=1.0, IDP=0.0 (proxy=0.5) cases now represent 4/8 accepted critique/mixed (Sources 14, 10, 6, 15). These pass the gate (proxy < 0.55) but Haiku correctly identified the flaw in a single pass. Additionally, Sources 7 and 9 exhausted (2 Stage 1 recycles each, still IDR=1.0, IDP=1.0) — both are retirement candidates.

Root cause assessment: the four prompt fixes address the *encoding* of compound relationships but not the *recognizability* of the underlying mechanism. Sources that have recognizable mechanisms at the pattern level will remain IDR=1.0 regardless of prompt engineering. See OPEN-17 for the gate-slip pattern this reveals.

---

## OPEN-17 — Gate permissive for IDR=1.0, IDP=0.0 cases (proxy=0.5 < 0.55 threshold)

**Severity:** High — cases where Haiku correctly identifies the flaw in a single pass are accepted into the benchmark  
**Source:** Batch 373–387 analysis (2026-04-08)

The gate threshold is `proxy < 0.55`. For critique/mixed cases where IDR=1.0 (Haiku found the planted flaw) but IDP=0.0 (Haiku didn't false-accuse any decoy), the proxy formula yields 0.5 — which passes the gate. These cases are trivially solved by a single Haiku pass; they will be even more trivially solved by a single Sonnet pass.

**Pattern:** In batch 373-387, 4/8 accepted critique/mixed cases fell into this bucket: Sources 14, 10, 6, 15 (IDR=1.0, IDP=0.0, proxy=0.5). They appear in `cases_373-387.json` as valid benchmark cases but provide no test of the debate protocol's value-add.

**Two options:**

1. **Add hard IDR gate for critique/mixed:** If `case_type in ["critique", "mixed"] and IDR == 1.0`, treat as difficulty_idr failure regardless of proxy score. Route to Stage 1 recycle. This would increase recycle rate and exhaustions for sources that produce persistent IDR=1.0.

2. **Two-tier acceptance:** Accept IDR=1.0, IDP=0.0 cases with a `difficulty_tier: "soft_pass"` label. Exclude them from the core benchmark; use them only in a separate "baseline calibration" analysis. Mark IDR=0.0 cases as `difficulty_tier: "hard_pass"`. Gate the main experiment to require a minimum fraction of hard_pass cases.

Option 2 is non-breaking (no change to gate logic) but requires downstream experiment stratification. Option 1 is cleaner but may exhaust remaining active sources faster.

**Next step:** User decision needed — tighten gate (Option 1) or stratify accepted cases (Option 2).

---

## OPEN-15 — Smoke test gate model (Haiku) is weaker than experiment baseline (Sonnet)

**Severity:** High — gate may be passing cases that are too easy for the actual experiment participants  
**Source:** Calibration analysis 2026-04-08

The smoke test uses Haiku to gate cases (reject if proxy ≥ 0.75). The main experiment debate agents run on Sonnet. Since Haiku ≪ Sonnet, cases that stumps Haiku (IDR=0.0, proxy=0.25) may still be trivially solved by a single Sonnet pass — meaning debate vs. single-pass Sonnet shows no lift, not because debate fails, but because the baseline already aces the case.

The gate currently filters "too easy for Haiku" but the experiment needs "hard enough for single Sonnet." Those are different bars. The second row of the risk matrix is unguarded:

| Haiku | Sonnet single-pass | Usable? |
|---|---|---|
| IDR=1.0 | — | No — filtered by gate |
| IDR=0.0 | IDR=1.0 | **No — but currently passes gate** |
| IDR=0.0 | partial | Yes — debate adds lift |
| IDR=0.0 | IDR=0.0 | No — too hard, noise |

**Next step:** Run a single-pass Sonnet evaluation on a sample of IDR=0.0 Haiku cases before committing to the full experiment. If Sonnet aces them, either swap the smoke test model to Sonnet or add a second gate pass. If Sonnet also struggles, current calibration is appropriate.

---

## OPEN-14 — Famous-paper ceiling: canonical ML papers remain IDR=1.0 regardless of transposition depth

**Severity:** High — limits effectiveness of transposition depth fix (OPEN-11) for the most well-known sources  
**Source:** Batch 343–357 comparative analysis (2026-04-08)

Batch 343–357 was the first run with all three IDR fixes applied (OPEN-10, OPEN-11, OPEN-12). Result: 3/9 critique/mixed at IDR=0.0, 6/9 still IDR=1.0. Analysis of which cases fell into which group reveals a clean source-level split:

**IDR=0.0 (fixes worked):**
- mech_004: Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)
- mech_007: Source 1 — Dacrema et al. (2019), RecSys
- mech_014: Source 9 — Caruana et al. (2015), KDD (required Stage 1 recycle)

**IDR=1.0 (fixes did not help):**
- mech_001: Source 2 — Obermeyer et al. (2019), Science
- mech_008: Source 3 — DeGrave et al. (2021), Nature Machine Intelligence
- mech_012: Source 4 — Lazer et al. (2014), Science (Google Flu Trends)
- mech_015: Source 5 — Zech et al. (2018), PLOS Medicine
- mech_002: Source 14 — Aggregated Performance Masking (pattern)
- mech_005: Source 16 — Instance-Filtering Bias (pattern)

The four persistently failing sources (Obermeyer, DeGrave, Lazer, Zech) are canonical ML failure case studies with thousands of citations, covered extensively in ML curricula, survey papers, and blog posts. Haiku almost certainly has these mechanisms encoded as named cautionary tales in its training data. No amount of domain transposition can obscure a mechanism that the model recognizes by its abstract form — the transposition fix changes the surface vocabulary but not the underlying inferential pattern that makes it recognizable.

The three sources that achieved IDR=0.0 (Ziegler, Dacrema, Caruana) are technically well-known but less culturally prominent as named failure modes. Their mechanisms require more domain-specific inference to connect to the source paper.

**Options:**
1. **Retire the four famous sources** — remove Obermeyer, DeGrave, Lazer, Zech from the source catalog. They've contributed their design patterns; continued use only wastes recycle budget. Replace with less-cited sources or new patterns.
2. **Require compound transposition for famous sources** — the mechanism must be split across two interacting causal steps, neither of which alone resembles the source paper's abstract mechanism.
3. **Accept the split and use selectively** — use famous-source cases for defense_wins scenarios (where IDR=1.0 doesn't fail the gate) and reserve critique/mixed slots for less-famous sources.

**Resolution (2026-04-08):** Option 1 applied — Obermeyer, DeGrave, Lazer, Zech removed from `CRITIQUE_SOURCES` in `source_catalog.py`. Moved to `RETIRED_SOURCES` list for reference. Active catalog reduced to 12 critique + 3 defense = 15 sources.

**Cross-batch analysis (2026-04-08):** Source 16 (Instance-Filtering Bias) confirmed consistent IDR=1.0 wall in both batches 343-357 and 358-372. Retired. Active catalog now 11 critique + 3 defense = 14 sources. All other sources with IDR=1.0 appearances had only single-batch data — insufficient to retire; monitoring continues.

**Empirical result (batch 358–372, 2026-04-08):** Retirement helped but wall persists. 4/9 IDR=0.0 (mech_001/Source 14 via S1 recycle, mech_004, mech_005/Source 8 via S1 recycle, mech_012). 5/9 still IDR=1.0 — Sources 14, 16, 6, 8, 11. Wall is not limited to canonical famous papers; pattern-level and moderately-known sources also ceiling. Trend: 0/8 → 3/9 → 4/9. Runtime dropped from ~20 min to ~10 min with concurrency=10. 15/15 accepted, 0 exhausted.

**Empirical result (batch 373–387, 2026-04-08):** 3/8 IDR=0.0 (Source 1, Source 13, Source 11). 4/8 IDR=1.0 proxy-passed (Sources 14, 10, 6, 15 — all IDP=0.0, proxy=0.5). 2 exhausted (Source 7/Hooker, Source 9/Caruana — both IDR=1.0, IDP=1.0 after 2 Stage 1 recycles each). Trend: 0/8 → 3/9 → 4/9 → 3/8 — flat. First test of OPEN-16 prompt fixes; fixes did not improve rate. Source 7 and Source 9 are confirmed wall — retirement pending user decision.

---

## OPEN-13 — `--resume` across different batches silently loads stale cases

**Severity:** Moderate — operator error risk; no current results corrupted  
**Source:** Cross-batch file lifecycle analysis (2026-04-08)  

`pipeline/run/cases/` is not cleared between runs. `mech_001.json` through `mech_015.json` from a prior batch persist. If `--resume` is passed when starting a new batch with a different `--start-case-id`, the orchestrator finds the prior batch's case files and skips those mechanisms entirely — producing a partial output file with mixed case IDs. No error is raised.

**Workaround:** Use `--resume` only when re-entering an interrupted run of the same batch (same `--start-case-id`). Never use it to start a new batch. Clear or archive `pipeline/run/` before starting a fresh batch if in doubt.

**Fix needed:** Guard `--resume` skip logic with a case_id check: if the existing `mech_NNN.json` has a `case_id` that doesn't match the expected range for this batch, do not skip — treat as a miss and re-run.

---

## ARCH-1 — Pipeline redesign: replace advocacy memo generation with experiment design generation

**Decision date:** 2026-04-08  
**Status:** ACTIVE — supersedes all prior case generation work (batches 313–387)

### Root cause of prior pipeline failure

The prior pipeline generated **advocacy memos** — retrospective documents written in team voice describing completed ML work, with flaws planted in the text and obscured through language. The benchmark task was: "read this memo, find the hidden flaw."

This was the wrong document type. When an LLM is asked to test a hypothesis, it does not produce an advocacy memo. It produces a **prospective experiment design** — a numbered plan describing what to do, what data to collect, how to validate, what metrics to use. The debate protocol operates on that plan, not on a retrospective report.

The entire infrastructure built to obscure flaws in language (compound fact isolation, prominence inversion, authoritative wrong justification, leakage auditor, IDR=0.0 pursuit) was solving a problem created by the wrong document type. Flaws in a plan don't need to be hidden — they just require methodology expertise to identify.

### New architecture: two-node design + corruption pipeline

**Node 1 — Design node (capable model):**  
Given a hypothesis, generates a sound, correct experiment design. This is the ground truth. No flaws are introduced here. The model is instructed only to produce a valid design.

**Orchestrator (Python, probabilistic):**  
Samples a corruption level for each case before passing to Node 2:
- P(0 flaws) ≈ 0.25 → sound design, correct verdict is "defend/approve"
- P(1 flaw) ≈ 0.35 → subtle single flaw
- P(2 flaws) ≈ 0.25 → compound or independent flaws
- P(many flaws) ≈ 0.15 → obvious/multiple errors, calibration anchor

**Node 2 — Corruption node (powerful model):**  
Takes the sound design and N as input. Replaces N design choices with plausible-but-wrong alternatives — flaws that look like natural LLM output from a model that didn't reason carefully about this choice. Returns: (a) corrupted design, (b) diff report (what changed, why it's wrong, what the correct version is).

**Ground truth:**  
The diff report from Node 2 is the ground truth. `must_find`, `correct_verdict`, and `corrected_design` are all byproducts of the corruption step — no separate engineering required.

**Debate agents see:**  
Hypothesis + corrupted design (or sound design if 0 corruptions). Never the diff report.

### Why this is correct

1. **Document type matches reality** — the cases look like what `ml-lab` actually produces when asked to design an experiment
2. **Ground truth is automatic** — the pre-corruption design is always correct; the diff is always known
3. **Difficulty is controlled by the orchestrator** — not by how well language obscures the flaw
4. **No hiding machinery needed** — a wrong split strategy is wrong whether or not the language is persuasive; difficulty comes from methodology subtlety, not text opacity
5. **Defense wins cases are trivial to generate** — 0 corruptions; correct verdict is "approve"
6. **Calibration anchors included** — "many flaws" cases catch protocol failures regardless of difficulty tuning

### Scope of hypothesis space

Cases should span the full range of what `ml-lab` handles: any ML hypothesis that can be run or simulated on a computer. This includes classification, regression, ranking, generative modeling, reinforcement learning, time series, causal inference, and any domain (healthcare, finance, NLP, vision, scientific ML, etc.).

### Pipeline stages (new)

| Stage | Model | Task |
|---|---|---|
| 1 | Any | Hypothesis + domain generator |
| 2 | Capable (Sonnet / GPT-4o) | Sound design writer — valid experiment plan |
| 3 | Powerful (Opus / GPT-5 / o3) | Corruption node — insert N flaws, return diff |
| 4 | Any | Ground truth assembler (structured from diff) |
| 5 | Sonnet | Smoke test — single-pass evaluation; gate on discriminating range |

### What is preserved from prior pipeline

- Python orchestrator skeleton (ThreadPoolExecutor, recycle logic, progress bars)
- Flaw taxonomy (broken baseline, metric mismatch, leakage, scope mismatch, hidden confounding, defense_wins)
- Scoring dimensions (IDR, IDP, FVC) — applied to new document type; **semantics revised post-ARCH-1** (see RESOLVED-8, RESOLVED-9)
- Gate concept — filter cases where single-pass is already perfect (no lift possible) or completely wrong (too hard, noise)

### What is replaced

- Stage 1: mechanism extractor + source catalog → hypothesis generator
- Stage 2: scenario architect → (eliminated; design node has no scenario context needed)
- Stage 3: memo writer → design writer (sound experiment plan)
- Stage 4 (new): corruption node
- Stage 5: leakage auditor → (eliminated; no language hiding needed)
- All cases in batches 313–387: wrong document type, not reusable

---

## OPEN-18 — IDP only covers must_not_claim list; invented false accusations outside the list score IDP=1.0

**Severity:** Moderate — IDP is misleading when Sonnet fabricates novel concerns not in `must_not_claim`  
**Source:** Scoring logic analysis, 2026-04-08

The scorer is asked to match Sonnet's `issues_found` against the pre-defined `must_not_claim` list and return `must_not_claim_raised`. IDP is then computed as `1 - n_raised / len(must_not_claim)`. This only penalizes false accusations that overlap with the finite set of "protected choices" Stage 4 defined.

If Sonnet invents concerns entirely outside that list — fabricating flaws that Stage 4 did not anticipate — they are invisible to IDP. For a 0-corruption case where Sonnet invents 4 novel false accusations:

- If none match `must_not_claim`: `raised_bad = []` → IDP = 1.0 (misleadingly clean)
- FVC = 0.0 still fires (wrong verdict), so proxy still flags the case as a debate candidate
- But the magnitude of false alarm behavior — 4 invented flaws vs. 1 — is not captured

**Consequence:** IDP understates false alarm rate when Sonnet fabricates concerns outside the expected universe. The gate doesn't fail silently (FVC catches the wrong verdict), but IDP is an incomplete precision metric.

**Potential fix:** Require the scorer to evaluate Sonnet's raw `issues_found` against the design soundness directly — not just match against a list. This is harder: the scorer would need to reason about whether each raised concern is legitimate, which requires it to understand the design. Alternatively, Stage 4 could generate a more exhaustive `must_not_claim` list covering the full space of plausible false accusations for each case.

**Current mitigation:** FVC=0.0 is the primary signal when Sonnet invents flaws on a sound design (wrong verdict). IDP provides supplementary precision signal only for anticipated false accusation types. Cases are still correctly flagged as debate candidates via FVC.

**Next step:** Monitor in live batches — if IDP=1.0, FVC=0.0 cases are common, the misleading IDP score may need to be addressed before reporting.

---

## RESOLVED-8 — FVC scoring bug: "approve" vs "defense_wins" string mismatch

**Resolved:** 2026-04-08  
**Affected code:** `compute_smoke_scores()` in `pipeline/orchestrator.py`

The smoke wrapper instructed Sonnet to return `verdict: "approve" | "critique"`. Stage 4 stored `correct_verdict` as `"defense_wins" | "critique"`. The FVC comparison used string equality — so `"approve" == "defense_wins"` was always `False`, meaning FVC=0.0 for every defense_wins case regardless of whether Sonnet correctly approved the design.

**Impact:** All 0-corruption cases showed FVC=0.0 even when Sonnet was correct. The old gate interpreted proxy=0.0 (IDR=None, IDP=??, FVC=0.0) as `defense_false_alarm` and recycled these cases unnecessarily, wasting recycle budget on valid cases.

**Fix:** Normalize verdict before comparison: `verdict_normalized = "defense_wins" if verdict == "approve" else verdict`. Verified by unit test: `approve + defense_wins correct_verdict → FVC=1.0`.

---

## RESOLVED-9 — IDR and IDP were binary; magnitude not captured

**Resolved:** 2026-04-08  
**Affected code:** `compute_smoke_scores()` in `pipeline/orchestrator.py`

**IDR (Issue Detection Recall)** was binary: `1.0` if ALL `must_find_ids` found, `0.0` otherwise. This collapsed "found 2 of 5 flaws" and "found 0 of 5 flaws" into the same score. A case where single-pass Sonnet finds 2 of 5 flaws is a strong debate candidate — the critic can surface the remaining 3, the defender can engage on the 2 already identified. Binary IDR mislabeled it as identical to a case where nothing was found.

Additionally, Stage 4 capped `must_find_issue_ids` at 2 for "many-corruption" cases, making IDR for 5-corruption and 2-corruption cases indistinguishable from the gate's perspective — and potentially easier (the top 2 are the most prominent).

**IDP (Issue Detection Precision)** was binary: `0.0` if any false accusation raised, `1.0` otherwise. Making 5 false accusations on a sound design was scored identically to making 1. The magnitude of false alarm behavior was lost.

**Fix:** Both metrics converted to partial credit fractions:
- `IDR = n_found / len(must_find_ids)` — fraction of required issues found; `None` if no must_find_ids
- `IDP = 1 - n_raised / len(must_not_claim)` — fraction of protected choices not falsely accused; `None` if no must_not_claim defined; clamped to `[0.0, 1.0]`

`proxy_mean` already excluded `None` metrics via the `applicable` filter — no change needed there.

The `must_find_issue_ids` cap for "many-corruption" cases is no longer hardcoded in scoring but remains a Stage 4 prompt concern — Stage 4 should include all significant issues, not cap at 2, so that IDR reflects actual recall across the full flaw set.

**Verified:** 36-test unit test suite in `pipeline/test_scoring.py` covers all partial-credit scenarios including magnitude differences, None exclusion, and proxy_mean recomputation.
