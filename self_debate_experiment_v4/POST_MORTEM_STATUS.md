# V4 POST_MORTEM Issue Tracker

Tracks resolution of all 19 issues found in `self_debate_experiment_v3/POST_MORTEM.md`.
Status reflects fixes applied to `plan/PLAN.md` and `plan/phases/` (the restructured plan). The original monolithic file is preserved at `claude_code_plan_v4_experiment_MONOLITHIC.md` for reference.

---

| # | Title | Severity | Status | Resolution |
|---|-------|----------|--------|------------|
| 1 | INVESTIGATION_LOG coverage is incomplete | Minor | ✅ Closed | Added explicit `log_entry.py` directives to every phase (0–11). Previously only Phase 6 had directives. |
| 2 | Agents invoked `python` instead of `uv run` | Moderate | ✅ Closed | Audit found zero bare `python`/`python3` invocations in v4 plan. All scripts already use `uv run`. Execution Rules section in `plan/PLAN.md` explicitly prohibits bare python usage; Reminders block in every phase file reinforces it. |
| 3 | Isolation breaches not logged in INVESTIGATION_LOG | Moderate | ✅ Closed | V4 plan includes explicit directives: log `decision/isolation_breach_detected`, `workflow/rerun_triggered`, `workflow/rerun_complete` for each breach and corrective re-run. |
| 4 | Batch1 logging granularity and schema differ from other batches | Moderate | ✅ Closed | `log_entry.py` (PEP 723, `uv run`) now enforces canonical schema: 6 required fields (`ts`, `step`, `seq`, `cat`, `action`, `detail`). Action-level granularity chosen. Schema validation moved from LLM prose to code. |
| 5 | Orchestrator reads agent source files from `agents/` despite agents being installed | Minor | ✅ Closed | Execution Rules section in `plan/PLAN.md` explicitly states agents are invoked by name only; `agents/` files are reference copies and must not be read during execution. Reminders block at the top of every phase file repeats this constraint. `agents/` and `~/.claude/agents/` are in sync. |
| 6 | Multiple cases marked failed due to ETD schema mismatch in `compute_etd()` | Critical | ✅ Closed | V4 standardizes on canonical ETD schema (`condition`/`supports_critique_if`/`supports_defense_if`/`ambiguous_if`). Dual-branch detection eliminated. All scoring logic updated. |
| 7 | Raw outputs not committed after Phase 6 completion | Moderate | ✅ Closed | Phase 6 and Phase 6.5 now have explicit `git commit` blocks with standardized messages (`chore: snapshot v4 ... raw outputs — <N> cases, isolation check <passed\|failed>`) and `log_entry.py` confirmation entries. |
| 8 | Post-mortem process is entirely manual | Low | ✅ Closed | Phase 10.5 (Post-Run Audit Agent) added to v4: automated agent scans raw outputs and results for schema mismatches, isolation breaches, pass/fail anomalies, ETD scoring errors, DC != null in baseline, forced_multiround debate_rounds < 2. Produces structured `POST_MORTEM.md`. |
| 9 | Near-ceiling scores limit interpretability; difficulty labels don't predict baseline performance | High | ✅ Closed | Phase 5.5 (Pre-Benchmark Difficulty Gate) added: samples up to 10 hard cases, runs 1 baseline call each, halts before Phase 6 if >4/10 exceed 0.55 mean. Probe fires before any Phase 6 agent runs — prevents full re-run recovery scenario. Phase 6.75 demoted to secondary in-execution check. |
| 10 | Orchestrator does not commit artifacts at phase boundaries | Moderate | ✅ Closed | Explicit `git commit` directives added at the conclusion of all phases: 0, 1, 2, 3, 4, 5, 5.5, 6, 6.5, 7, 8, 9, 9.75, 10, 10.5, 11. Phases 8.5 and 9.5 (audit-only) commit their audit scripts. Each commit uses specific `git add` paths (not `-A`) and includes a `log_entry.py` confirmation entry. |
| 11 | MiniMax cross-vendor validation yielded 82% parse failures | Low | ✅ Closed | V4 uses corrected OpenAI-compatible API. Cross-vendor scorer now runs on ALL cases (not just 7). Per-dimension deltas computed; bias > 0.1 flagged in REPORT.md limitations. |
| 12 | Report leads with raw lift; fair-comparison lift buried | Moderate | ✅ Closed | V4 redesigns primary metric: fair-comparison lift (IDR/IDP/DRQ/FVC only) is the primary benchmark hypothesis. Raw lift presented as supplementary with explicit note on structural penalties. Report must lead with fair-comparison lift in abstract and findings. |
| 13 | DC scored 0.0 for baseline instead of N/A; inflates raw lift | High | ✅ Closed | V4 scores DC as N/A for baseline (consistent with ETD=N/A treatment for structurally inapplicable dimensions). Pre-registered. Eliminates the single largest per-dimension gap driving spurious raw lift. |
| 14 | Multiround condition was never meaningfully exercised (avg 1.03 rounds) | Moderate | ✅ Closed | V4 adds `forced_multiround` as a 5th condition: hard cases only, 2-round minimum enforced. Enables direct comparison — if forced > natural, defenders concede too quickly; if equal, natural multiround is sufficient. |
| 15 | ETD scored for ensemble and baseline; creates illegitimate comparison | High | ✅ Closed | V4 scores ETD=N/A for ensemble and baseline (no adversarial exchange to produce meaningful empirical test). Comparisons restructured: (1) debate vs. ensemble on IDR/IDP/DRQ/FVC only; (2) debate conditions vs. each other on all dims including ETD. |
| 16 | Closed-loop evaluation: scoring-model confound unquantified | High | ⚠️ Partial | V4 Phase 10 runs cross-vendor scorer on ALL cases (improvement from 7 valid cases). Per-dimension deltas computed. However, POST_MORTEM also recommended human evaluation of 10–15 stratified cases to validate rubric interpretation — not included in v4. Confound is reduced but not fully bounded. |
| 17 | Report artifact contains prompt leakage; limitations framed as design properties | High | ✅ Closed | V4 adds Reporting Norms section with strict rules: no preamble or internal mode declarations, first line must be section header/abstract. Design property vs. limitation distinction enforced. `post_report_coherence_audit.py` checks compliance. |
| 18 | Pre-registered convergence metric misconceived; not computable from agent outputs | Moderate | ✅ Closed | V4 replaces convergence metric with `point_resolution_rate`: (points resolved by concession or empirical agreement) / (total contested points in DEBATE.md). Computable from actual outputs. Pre-registered with field extraction logic defined before execution. |
| 19 | Phase 4 protocol self-review gate was bypassed | High | ✅ Closed | V4 implements dynamic gate: after Defender dispatch, orchestrator reads DEFENSE.md Pass 2 verdict table, extracts all Concede/Rebut rows as pre-flight checklist items, writes to EXECUTION_PLAN.md, logs `gate/phase4_cleared` entry. LEAD approval required before Phase 5. Gate reflects actual review output, not a static pre-written list. |

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Closed | 18 |
| ⚠️ Partial | 1 (Issue #16) |
| ❌ Open | 0 |

## Notes

- Issues #5, #6, #8, #11, #12, #13, #14, #15, #17, #18, #19 were addressed in the initial v4 plan design (pre-session).
- Issues #1, #2, #3, #7, #9, #10 required edits during this session (applied to the monolithic file, then carried forward into the restructured plan).
- Issue #4 was resolved by the ml-lab agent update (embedded `log_entry.py` in spec) before this session.
- Issue #16 remains partial: cross-vendor coverage improved from 7 to all cases, but human evaluation stratum was not added.
- The monolithic plan (`claude_code_plan_v4_experiment_MONOLITHIC.md`) has been superseded by a three-layer structure: `plan/PLAN.md` (entry point), `plan/phases/` (19 phase files), `plan/scripts/` (13 Python scripts). All resolutions above apply to the current `plan/` structure.
