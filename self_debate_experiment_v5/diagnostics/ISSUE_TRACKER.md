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

**Resolution:** The modular pipeline in `synthetic-candidates/pipeline/` is explicitly designed to be run by a non-Anthropic LLM (GPT-4o, Gemini, Perplexity, etc.). The generation prompt header has always specified this; the pipeline formalizes it. GPT generates the cases, Claude debates them — different architectures, different priors, clean cross-model design.

**Residual:** The pipeline instructions (flaw taxonomy, decoy requirements, stage logic) were written by Claude, so Claude's fingerprint is on the scaffold even if not the output. This is a weaker bias and arguably unavoidable — someone has to design the benchmark methodology. The execution is cross-model; the meta-design is not.

**Empirical check:** Whether GPT transpositions are genuinely harder for Claude than Claude's own transpositions would be is an open empirical question — the smoke test will answer it.
