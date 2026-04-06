# v3 Experiment Post-Mortem

Issues identified during and after execution of `claude_code_plan_v3_experiment.md`. Each issue is scoped to whether it affected current results (active) or should be fixed in a future run (future).

---

## Issue 1 — INVESTIGATION_LOG coverage is incomplete

**Scope:** Future fix  
**Severity:** Minor — audit quality, not result validity

The plan's logging directive (line 780) covers Phase 6 onward only. It defers to the ml-lab agent's `## Investigation Log` schema rather than embedding it, which means log quality depends on the executor consulting that section. Phases 0–5 (case validation, preregistration, scoring engine build, protocol self-review) and Phases 7–9 (stats, reports, peer review) have no explicit logging directives.

ml-lab's logging section specifies ~60 lines of rules covering all category codes (`gate`, `write`, `read`, `subagent`, `exec`, `decision`, `debate`, `review`, `audit`, `workflow`), entry timing, and per-step logging rhythm. The v3 plan has one paragraph.

**What to fix in v4:** Embed the full logging schema directly in the plan and add explicit logging directives to each phase, not just Phase 6.

---

## Issue 2 — Agents and subagents invoked `python` instead of `uv run`

**Scope:** Future fix  
**Severity:** Moderate — silent failures possible when scripts have PEP 723 inline dependencies

Several agents and subagents called scripts with `python` (or `python3`) directly rather than `uv run`. For scripts that rely only on the standard library this is harmless, but the v3 scripts use PEP 723 inline script metadata (`# /// script` blocks) to declare third-party dependencies. Invoking those scripts with bare `python` silently skips dependency resolution: the script either crashes on import or, worse, resolves against a stale environment that happens to have the package installed.

**Canonical rule:** every script invocation — whether from an agent, a subagent, or a one-liner — must use `uv run <script>`. This applies equally to inline `-c` one-liners: prefer `uv run python -c '...'` over `python3 -c '...'`.

**What to fix in v4:** Add an explicit enforcement note to the experiment plan and to any agent prompt that invokes scripts: "Always invoke Python scripts with `uv run`. Never use `python` or `python3` directly."

---

## Issue 3 — Isolation breaches not logged in INVESTIGATION_LOG

**Scope:** Active — confirmed gap in audit trail for this run  
**Severity:** Moderate — breach detection worked, but the event is absent from the log

`check_isolation.py` detected 2 isolation breaches at scoring time:

- `v3_raw_outputs/real_world_framing_002_isolated_debate_run1.json` — Defender output contained verbatim Critic issue text
- `v3_raw_outputs/real_world_framing_010_isolated_debate_run1.json` — same pattern

The orchestrator surface these in the console and re-ran the affected runs. However, inspection of all 7 batch INVESTIGATION_LOGs confirms neither the breach detection nor the re-run were logged. The batch7 entry for `real_world_framing_002` records normal completion and notes verdict variation as a "labeling" difference — no breach flag. The batch6 summary explicitly records `"isolation_violations": 0`.

This is a direct instance of the Issue 1 gap: because the plan has no explicit logging directive for breach detection or corrective re-runs, the orchestrator handled both silently. From the log alone, there is no record that two runs were contaminated and replaced.

**What to fix in v4:** Add explicit logging directives to the isolation check step: log a `decision` / `isolation_breach_detected` entry for each flagged file (with `meta` capturing the matched string and file path), and log a `workflow` / `rerun_triggered` entry before each corrective re-run and `workflow` / `rerun_complete` after.

---

## Issue 4 — Batch1 logging granularity and schema differ from all other batches

**Scope:** Active — inconsistent audit trail across batches in this run  
**Severity:** Moderate — batch1 data is present but informationally thin and structurally incompatible with other batches

Batch1 (`broken_baseline_*` cases, 7 cases) produced 84 log entries — one per individual run (12 per case). All other batches produced 7–9 entries total — one rich summary per case. Beyond the count difference, the schemas diverge: batch1 entries contain only `timestamp`, `type`, `case_id`, `condition`, `run`, and `note: "completed"`, with no verdict data, must-find coverage, or qualitative notes. Batches 2–7 entries include `verdicts`, `must_find_coverage`, `unanimous_verdict`, and substantive `notes` fields.

Comparison against the `ml-lab` logging spec reveals that **no batch is compliant**. The spec mandates six required fields; all batches deviate on multiple:

| Spec field | Batch1 | Batches 2–7 |
|---|---|---|
| `ts` | present as `timestamp` (wrong key) | present as `timestamp` (wrong key) |
| `step` | absent | absent |
| `seq` | absent | absent |
| `cat` | present as `type`; only `exec` used | absent entirely |
| `action` | absent | present, but no verb_noun convention |
| `detail` | absent | partially — folded into `notes` or `summary` |

The spec's 10-category `cat` taxonomy (`gate`, `write`, `read`, `subagent`, `exec`, `decision`, `debate`, `review`, `audit`, `workflow`) was never used. The monotonic `seq` counter was never maintained. The `step` field — which ties every entry to a phase of the experiment — is absent in all batches. Action-level granularity (one entry per meaningful action, with step boundaries, file I/O, and subagent dispatches each logged separately) was replaced by coarser run-level (batch1) or case-level (batches 2–7) summaries.

Batches 2–7 did add useful non-spec fields — `verdicts`, `must_find_coverage`, `unanimous_verdict` — which the spec would have placed in `meta`. The content is present but under non-standard keys, making uniform parsing unreliable.

The root cause is the same as Issue 1: the v3 plan referenced the ml-lab logging spec by pointer rather than embedding it, so orchestrators wrote something loosely inspired by the spec rather than actually following it.

**Investigation needed before v4:**
- Determine whether batch1's run-level format and batches 2–7's case-level format reflect different orchestrator agents or different prompting strategies within the same agent
- Decide whether the canonical granularity should be action-level (as spec requires), run-level, or case-level — and whether a two-tier format (fine-grained during execution, summary at case completion) is desirable
- Assess whether batch1's thin entries can be post-hoc enriched with verdict data from the raw output files, or whether that signal is simply missing from the log
- Determine whether to fix key names (`timestamp` → `ts`, `type` → `cat`) in the v4 schema or update the spec to match what orchestrators naturally produce

**Proposed fix for v4:** Replace prose-based logging with a dedicated `log_entry.py` script (PEP 723, invoked via `uv run`). The script accepts structured CLI arguments, enforces required fields, validates `cat` against the allowed taxonomy, auto-generates `ts`, and increments `seq` by reading the last line of the log. The orchestrator is explicitly instructed to call it for every loggable action:
```
uv run log_entry.py --step 6 --cat exec --action run_case --case_id foo --detail "ran isolated_debate run 1, verdict: critique_wins"
```
Schema compliance moves out of LLM text generation and into code — the same pattern as `check_isolation.py`. The v4 plan must include an explicit directive: "never write log entries manually; always use `uv run log_entry.py`."

---

## Issue 5 — Orchestrator reads agent source files from `agents/` despite agents being installed

**Scope:** Active — observed during this run  
**Severity:** Minor — functionally harmless, but wastes context and suggests the orchestrator doesn't trust its installed agents

The experiment orchestrator was observed reading agent source files directly from the repo's `agents/` directory (e.g. `agents/ml-critic.md`, `agents/ml-defender.md`) during execution. All agents are already installed in the Claude Code environment at `~/.claude/agents/` and are invoked by name via the Agent tool — the source files in `agents/` are reference copies, not the active definitions.

The cause is unclear. Possible explanations:
- The v3 plan explicitly references `agents/` paths, prompting the orchestrator to read them for context before dispatching
- The orchestrator is verifying agent behavior before dispatch, not trusting the installed version
- The orchestrator conflates "reading the spec to understand what the agent will do" with "dispatching the agent"

This is wasteful (consumes context window) and potentially risky: if the repo copy and the installed copy have diverged, the orchestrator is reading stale or incorrect behavior descriptions.

**Investigation needed before v4:** Audit the v3 plan for any explicit references to `agents/` file paths that might prompt reading behavior. Add a directive clarifying that agents are invoked by name only and their source files must not be read during execution. Determine whether this is plan-driven or spontaneous orchestrator behavior, as the fix differs in each case.

---

## Issue 6 — Several real_world_framing cases marked failed despite issues found and verdict matching ground truth

**Scope:** Active — both patterns are scorer bugs; all ETD scores are invalid and must be re-computed  
**Severity:** Critical — the ETD dimension is entirely unreliable in the current results; any analysis that uses ETD scores or pass/fail outcomes for `empirical_test_agreed` cases must be treated as provisional until re-scored

Several `real_world_framing` cases in `v3_results_eval.json` are marked `pass_fail: fail` despite having all planted issues found, valid resolution, and final verdict matching ground truth. Investigation identified two distinct scorer bugs.

### Pattern A — ETD=0.0 floor failures (rwf_005, rwf_006, rwf_007, rwf_008, rwf_009) — scorer schema mismatch

**This is a scorer bug, not agent failure.**

These five cases each score ETD=0.0 with all other dims at 1.0 (except DRQ=0.5 on rwf_005 and rwf_008). Initial hypothesis was that ETD should be `null` — but inspection of `benchmark_cases_verified.json` confirmed all five have `ideal_debate_resolution.type: empirical_test_agreed`, making ETD fully applicable. Further investigation of the raw output files confirmed that **empirical test designs were produced** across isolated_debate, multiround, and ensemble conditions in all five cases. For example, `real_world_framing_006_isolated_debate_run1.json` contains a fully-specified empirical test with condition, success criterion, and failure criterion.

The root cause is a **schema mismatch** between `compute_etd()` in `self_debate_poc.py` and the actual raw output format. The scorer checks for three keys:

```python
has_m = bool(empirical_test.get('measure'))
has_s = bool(empirical_test.get('success_criterion'))
has_f = bool(empirical_test.get('failure_criterion'))
```

But the raw outputs use a different schema:
```json
{
  "condition": "...",
  "supports_critique_if": "...",
  "supports_defense_if": "...",
  "ambiguous_if": "..."
}
```

None of the scorer's expected keys (`measure`, `success_criterion`, `failure_criterion`) are present in any raw output. Every `empirical_test` block evaluates to `has_m=False, has_s=False, has_f=False` → ETD=0.0, regardless of content quality. The only reason rwf_002 and rwf_010 score ETD=1.0 is a separate anomaly (Pattern B below) — the ETD=1.0 there is also suspect.

**This is a critical finding for experiment analysis.** All ETD scores in `v3_results_eval.json` are invalid. Cases scored ETD=0.0 may have produced high-quality empirical test designs; cases scored ETD=1.0 did not earn that score through `compute_etd()` as written. The entire ETD dimension must be re-scored after aligning the scorer schema with the actual output schema.

**Fix required before v4:** Reconcile the `compute_etd()` key expectations with the output format agents actually produce. Either update the scorer to read `condition`/`supports_critique_if`/`supports_defense_if`/`ambiguous_if`, or update the agent output format to emit `measure`/`success_criterion`/`failure_criterion` — and re-score all cases for ETD from the raw outputs.

### Pattern B — All dims 1.0 but still marked fail (rwf_002, rwf_010)

Both cases score 1.0 on every dimension including ETD, have all planted issues found, valid resolution, verdict matching ground truth, and `failure_attribution: "none"`. By every rubric criterion these should be passing cases. Given the Pattern A finding that `compute_etd()` cannot return 1.0 from the actual output schema, the ETD=1.0 scores on rwf_002 and rwf_010 are themselves anomalous — they may reflect a hardcoded or manually overridden score rather than a valid scorer output.

**This is a scorer bug.** Something in `case_passes()` or upstream result aggregation is marking these cases failed despite no failing dimension. The isolation breach on rwf_002 run1 and rwf_010 run1 (Issue 3) is a candidate cause — if the scorer aggregated pre-rerun results at the case level, it may have carried a stale failure flag that persisted even after the contaminated runs were replaced.

**Fix required before v4:** Audit `case_passes()` logic and result aggregation for rwf_002 and rwf_010. Verify that re-run outputs were correctly written and read by the scorer. Re-score both cases from corrected raw outputs after the ETD schema fix is applied.

### Remediation applied (v3)

**Root cause confirmed:** `compute_etd()` in `self_debate_poc.py` expected keys `measure` / `success_criterion` / `failure_criterion`, but agents naturally produced `condition` / `supports_critique_if` / `supports_defense_if` / `ambiguous_if`. Every output using the agent-native schema scored ETD=0.0 regardless of content quality.

**Fix:** `compute_etd()` updated to detect which schema is present (discriminating key: `measure` vs `condition`) and map both to the same three-component logic: `condition` → measure, `supports_critique_if` → success criterion, `supports_defense_if` → failure criterion. An `isinstance(empirical_test, dict)` guard was also added to handle two string-valued `empirical_test` fields in `defense_wins_009` raw outputs (no score impact — already short-circuited by the `defense_wins` early return).

**Re-scoring results:** All 49 main benchmark cases and 16 external cases re-scored. Only the 8 `real_world_framing` cases were affected — the only cases that produced condition-schema outputs. 5 changed from FAIL to PASS: rwf_002, rwf_006, rwf_007, rwf_009, rwf_010. The remaining 3 still fail for legitimate reasons: rwf_003's isolated debate returned `mixed` (not in acceptable resolutions); rwf_005 and rwf_008's isolated debate returned `critique_wins` without an empirical test, so ETD=0.0 is correct (ideal resolution is `empirical_test_agreed`, making ETD applicable regardless of actual verdict). External results unchanged — no condition-schema files in external outputs.

**Artifacts updated:** `v3_results.json`, `v3_results_eval.json`, `stats_results.json`, `external_stats_summary.json`, `sensitivity_analysis_results.json`, `within_case_variance_results.json`, `difficulty_validation_results.json`. No raw output files were modified — fix was entirely in the scorer.

**Pattern B fully explained:** The ETD=1.0 on run1 for rwf_002 and rwf_010 was not anomalous — it was coincidental. Run1 for both cases was the isolation breach re-run (original run1 contaminated and replaced, Issue 3). The replacement agent happened to emit the old `measure`/`success_criterion`/`failure_criterion` schema, which `compute_etd()` could correctly read → ETD=1.0. Runs 2 and 3 were original batch outputs using the condition-schema → ETD=0.0. Case-level aggregation required ≥2 passes; each case had only 1, so both were marked fail. The post-mortem description of "all dims 1.0" was describing run1 in isolation, not the case aggregate — there was no scorer bug in `case_passes()` itself. After the ETD schema fix, run2 and run3 now score correctly: rwf_002 reaches 2/3 passes (run3 still fails — verdict was `critique_wins` with no empirical test, ETD=0.0 correct); rwf_010 reaches 3/3 passes.

**Commit status — verify before closing:** As of the time this post-mortem was written, the scorer fix (`self_debate_poc.py`) and all re-scored artifacts (`v3_results.json`, `v3_results_eval.json`, `stats_results.json`, `external_stats_summary.json`, `sensitivity_analysis_results.json`, `within_case_variance_results.json`, `difficulty_validation_results.json`) are untracked in git. The remediation is functionally complete but not committed. The orchestrator may have its own commit plan for these files — verify that all remediation artifacts are committed before treating Issue 6 as closed.

**Open items carried forward to v4:**
- `ambiguous_if` is silently dropped in the mapping; a three-outcome test and a two-outcome test score identically — worth addressing in v4 schema design
- The dual-schema detection approach in `compute_etd()` is v3-only technical debt; v4 should standardize on a single canonical output schema so branching logic is not needed

---

## Issue 7 — Raw outputs not committed after Phase 6 completion

**Scope:** Future fix  
**Severity:** Moderate — raw outputs are ground truth for all downstream scoring; untracked files are vulnerable to inadvertent modification

The `v3_raw_outputs/` directory is never committed to git during the experiment run. All downstream scoring, ETD evaluation, bootstrap CIs, and sensitivity analysis read directly from these files. If any file is modified after scoring — whether by a re-run, a tool call, or an accidental overwrite — there is no way to detect the change or recover the original. The isolation breach re-runs in this experiment (Issue 3) are a concrete example: the re-run outputs replaced the contaminated files with no git record of what was overwritten or when.

**What to fix in v4:** Add explicit directives to the experiment plan for two commits:

1. **After Phase 6 (main benchmark):** Once all benchmark cases are complete and `check_isolation.py` passes clean, commit `v3_raw_outputs/` before any scoring begins. Commit message should record isolation check result and benchmark run count.
2. **After Phase 6b (external cases):** Once all external cases are complete and isolation check passes, commit `v3_raw_outputs/` again to snapshot the full dataset including external cases.

Each commit creates a tamper-evident checkpoint that scoring and analysis can be traced back to. The two-commit structure also makes it easy to identify which files belong to the main benchmark vs. the external benchmark by comparing the two snapshots.

---

## Issue 8 — Post-mortem process is entirely manual; consider automation


**Scope:** Future improvement — implement after v3 experiment is fully complete  
**Severity:** Low — process works, but does not scale and requires concurrent human attention during experiment execution

The v3 post-mortem was produced by manually cross-referencing logs, raw outputs, scorer source, benchmark case metadata, and git history in real time alongside the running experiment. Most items required synthesizing evidence across multiple artifacts (e.g. Issue 6 Pattern B required connecting the isolation breach, the re-run's coincidental output schema, run-level aggregation logic, and scorer source). This is high-effort and easy to miss things.

Three automation options to evaluate and implement in combination after the experiment is complete:

**Option 1 — Post-run audit agent**
After all phases complete, spawn a general-purpose agent with the raw outputs, scorer source, results eval JSON, and a checklist of known failure modes (schema mismatches, isolation flags, pass/fail anomalies). The agent produces a structured anomaly report — not a finished post-mortem, but a set of flagged items for human review and promotion. Lower bar than full automation, high signal.

**Option 2 — Inline orchestrator anomaly logging**
The orchestrator already notices unexpected events (isolation breaches, re-runs, non-zero scorer exits). A plan directive to log `decision` / `anomaly_detected` entries whenever something unexpected occurs would make the orchestrator self-documenting during the run. These entries could feed a post-run summarizer. Builds directly on the `log_entry.py` improvement from Issue 4 and is the highest-leverage near-term change.

**Option 3 — Dedicated post-mortem skill**
A skill that knows the experiment structure: reads a post-mortem template, runs structured checks (ETD validity, isolation status, schema consistency, pass/fail vs. ground-truth agreement), and drafts post-mortem items for each anomaly. Human reviews and edits rather than discovers and writes. Highest leverage long-term but requires the most upfront design and should wait until the experiment protocol is stable — a skill built on v3 assumptions would need rework for v4.

**Recommendation:** Options 1 and 2 are complementary and low-risk; implement both for v4. Option 3 is worth building after v4 when the protocol has stabilized. Priority for v4 is Option 2 — getting orchestrators to log anomalies inline is where the diagnostic signal already lives.

---

## Issue 9 — Near-ceiling scores limit interpretability of v3 results

**Scope:** Active — affects interpretation of all v3 findings  
**Severity:** High — the experiment cannot support several claims that the results superficially suggest

Post-fix results show all three debate conditions at 0.975–0.993 and a 93.9% pass rate (46/49). These numbers look strong but have limited interpretive value for four distinct reasons.

**1. The pass rate improvement is partially a scorer artifact.** Five of the six newly-passing cases (post-ETD fix) were failures caused by a scorer bug, not by agents underperforming. Treating 93.9% as evidence of benchmark difficulty would be incorrect — it reflects a correct fix, not a hard benchmark being cleared.

**2. The ETD fix may have introduced rubric leniency.** The corrected `compute_etd()` awards ETD=1.0 if `condition`, `supports_critique_if`, and `supports_defense_if` are present — it checks field presence, not content quality. Any three-field empirical test object clears the bar. The original intent was to assess whether the test was well-specified; the schema fix may have inadvertently lowered that bar, contributing to the ceiling effect.

**3. Conditions are indistinguishable at this score level.** 0.975 vs. 0.986 vs. 0.993 is within noise — the experiment cannot support any claim about whether multiround or ensemble adds value over isolated debate. Differential performance between protocol variants requires cases hard enough to separate the conditions. V3 does not have enough of those.

**4. The fair-comparison lift of +0.053 is the most defensible number.** After controlling for cases where baseline was also tested, debate adds approximately 5 points over baseline. At that margin, the experiment barely supports the claim that debate outperforms baseline at all, let alone that more elaborate debate structures add incremental value.

**Implication for v4 case design:** The benchmark needs cases that genuinely stress-test the conditions against each other — ambiguous scenarios where a single-pass critic misses something that a multiround exchange surfaces, or where ensemble synthesis resolves a contested point that isolated debate leaves open. High-difficulty cases with nuanced `empirical_test_agreed` resolutions are the most likely candidates. A 93.9% pass rate on a well-designed benchmark should be a warning sign, not a headline result.

