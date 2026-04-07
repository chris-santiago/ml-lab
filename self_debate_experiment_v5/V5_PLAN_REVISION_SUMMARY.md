# V5 Plan Revision Summary

**Date:** 2026-04-07
**Scope:** `self_debate_experiment_v5/plan/` — all 19 phase files, 14 scripts, PLAN.md

All changes in `plan/`. No files in `synthetic-candidates/` were modified.

---

## Step 1: Mechanical v4→v5 Renaming — all 34 files

| Pattern replaced | Notes |
|---|---|
| `self_debate_experiment_v4` → `v5` | All paths in phases/scripts |
| `v4_raw_outputs` → `v5_raw_outputs` | 6 phase files + 4 scripts |
| `v4_results.json` → `v5_results.json` | 5 scripts + 4 phase files |
| `v4_results_eval.json` → `v5_results_eval.json` | phases 7, 9.5, 11 |
| `external_cases_v4.json` → `v5` | phase_00, phase_06_5 |
| `cross_vendor_scores_v4.json` → `v5` | phase_09, phase_10, PLAN.md |
| Variable names `v4 = json.load(f)` | coherence_audit.py, post_report_coherence_audit.py, cross_model_scorer.py |
| Script docstrings, version labels, commit messages | All 34 files |

---

## Post-Mortem Issues → V5 Plan Changes

| Issue | Severity | V5 Status | Where Fixed |
|---|---|---|---|
| **Issue 1** — Relative paths break (CWD is repo root) | Moderate | Resolved | PLAN.md Rule 5; CWD reminder in all 19 phase files; phase_00 bash blocks rewritten |
| **Issue 2** — CASE_VERIFIER output schema unspecified | High | Resolved | `phase_01_case_verifier.md` — explicit JSON schema with field names and type constraints |
| **Issue 3** — Multiline commit messages trigger approval prompts | Moderate | Resolved | `phase_11_final.md` — commit rewritten as single-line `-m` |
| **Issue 4** — `log_entry.py` not found from repo root | High | Resolved | Same as Issue 1 fix |
| **Issue 5** — Phase 5.5 gate failed on hard cases scoring 1.0 | Critical | Resolved in synthetic-candidates | Cases redesigned; gate threshold now matched to generation acceptance criterion |
| **Issue 6** — Self-annotating cases ("task prompt transparency") | Moderate | Resolved in synthetic-candidates | Cases redesigned; no plan change needed |
| **Issue 7** — Phase 5.5 gate re-run still fails | Moderate | Resolved in synthetic-candidates | Cases use 4 flaw types undetectable by internal consistency check |
| **Issue 8** — Phase 6 agents attempt direct API calls | High | Resolved | PLAN.md Rule 4; subagent context reminder in all 19 phase files |
| **Issue 9** — `claude --agent` not a valid CLI option | Moderate | Resolved | Same as Issue 8 fix |
| **Issue 10** — `--meta` JSON triggers brace+quote approval | Moderate | Resolved | `log_entry.py` — `--meta-file` argument added |
| **Issue 11** — V5 must incorporate v4 debate insights | Moderate | Resolved | `phase_02_hypothesis.md` — compute-matched label removed, H2 reframed to FVC, information asymmetry confound documented; `write_preregistration.py` updated; `phase_05_5_difficulty_gate.md` expanded per DEBATE Issue 9 |
| **Issue 12** — Batch 1 total failure at scale | Critical | Resolved | `phase_06_benchmark_run.md` — mandatory smoke test before full batch |
| **Issue 13** — Malformed JSON in output files | High | Resolved | `phase_06_benchmark_run.md` — mandatory post-write validation (read-back + key check + re-dispatch on failure) |
| **Issue 14** — Ceiling scores on all hard cases | Critical | Resolved in synthetic-candidates | Hard cases redesigned with 4 new flaw types; Haiku acceptance criterion |
| **Issue 15** — Inverted Spearman rho=+0.691 | High | Resolved | `phase_05_5_difficulty_gate.md` — preliminary Spearman check added; v5 cases define difficulty via rubric performance |
| **Issue 16** — List comprehension scope bug + None comparison | Moderate | Already fixed | V5 scripts were copied post-fix; `stats_analysis.py:123` cosmetic cleanup applied |
| **Issue 17** — V5 case generation redesign | High | Resolved in synthetic-candidates | 8 design principles, real-paper supplement, Haiku acceptance criterion |
| **Issue 18** — Hardcoded task prompts dispatched to 7 cases | High | Resolved | `phase_06_benchmark_run.md` — CRITICAL DISPATCH RULE (read from JSON verbatim + pre-dispatch integrity check) |

---

## Additional Script Changes

| File | Change |
|---|---|
| `validate_cases.py` | Min count assertion: `>= 50` → `>= 60`; `--lenient` flag added for per-file checks; `source_paper` field check for real-paper cases |
| `filter_verified_cases.py` | Min keep: `< 40` → `< 50` |
| `write_preregistration.py` | Secondary H2 changed from DC to FVC (v4 DEBATE Issue 7); "compute-matched" label removed from ensemble rationale |
| `log_entry.py` | `--meta-file` argument added |
| `stats_analysis.py` | Line 123: `.get('DC', 0)` → `.get('DC')` (cosmetic; harmless but misleading default removed) |

---

## Phase-Specific Changes

| Phase | Change |
|---|---|
| `phase_00_setup.md` | Full rewrite: merge logic for two JSON sources; validate merged file; corrected bash paths |
| `phase_01_case_verifier.md` | Explicit `benchmark_verification.json` output schema added; filter threshold updated to ≥50 |
| `phase_02_hypothesis.md` | "compute-matched" removed; FVC criterion for H2; information asymmetry confound documented |
| `phase_05_5_difficulty_gate.md` | Full rewrite: 15-case stratified pilot (5/5/5); **10 hard cases** for ceiling check; **claude-haiku-4-5** evaluator specified; acceptance criterion **≥6/10 score mean < 0.55**; three-branch easy-stratum decision rule; preliminary Spearman check |
| `phase_06_benchmark_run.md` | Smoke test added; CRITICAL DISPATCH RULE (task prompts from JSON only); post-write validation; `source_paper` added to excluded fields |
| `phase_06_5_external_benchmark.md` | CRITICAL DISPATCH RULE and post-write validation added; `source_paper` excluded |
| `phase_11_final.md` | Multiline commit replaced with single-line `-m` |
| All 19 phase files | Subagent context reminder + CWD reminder added to Reminders block |
| `PLAN.md` | Title updated; Prerequisites updated for two source files + merge; Rules 4 and 5 added; call volume estimate updated for 64 cases |

---

## Synthetic-Candidates Alignment Checks

The following were confirmed already addressed by the v5 synthetic-candidates (no plan changes needed):

| Issue | How addressed in synthetic-candidates |
|---|---|
| Self-annotating cases | 8 design principles prohibiting internal-consistency flaws; trigger phrase prohibition list |
| Ceiling effect on hard cases | 4 flaw types (Assumption Violations, Quantitative Errors, Critical Omissions, Wrong Justifications) |
| Difficulty label validity | Difficulty defined by expected rubric performance on single-pass Haiku; `difficulty_justification` field in each hard case |
| Case generation redesign | Real-paper supplement grounded in 12 documented paper failures; Source Recognition Test gate |
| Rubric asymmetry (Issue 15) | Hard cases use specific `must_find_issue_ids`; easy cases have proportionate requirements |
