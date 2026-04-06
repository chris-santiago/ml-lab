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
