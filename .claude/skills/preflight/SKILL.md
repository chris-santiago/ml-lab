---
name: preflight
description: Pre-execution readiness check for any ml-debate-lab experiment version. Verifies uv installation, PEP 723 headers, phase file completeness, step-number consistency, agent installation, script syntax, and operator prerequisites. Reports a structured PASS/WARN/FAIL table and a final READY or BLOCKED verdict.
user-invocable: true
---

You are executing the `preflight` skill. Run all checks below in order and produce a structured report. The skill accepts an optional experiment directory argument (e.g., `/preflight self_debate_experiment_v4`). If no argument is given, use the current working directory.

## Setup

Determine the experiment root:
- If an argument was provided (e.g., `self_debate_experiment_v4`), resolve it as a path relative to the repo root.
- Otherwise, use the current working directory.

The experiment root must contain `plan/PLAN.md`. If it does not, halt immediately and tell the user: "Could not find plan/PLAN.md. Run this skill from an experiment directory or pass the experiment directory name as an argument."

All relative paths below are relative to the experiment root.

---

## Checks

Run each check in order. Record each result as PASS, WARN, or FAIL with a one-line note. Severity legend:
- **FAIL (BLOCKER)** — experiment cannot run correctly; must be fixed before Phase 0
- **WARN** — won't prevent execution but will create confusing log entries or audit failures downstream
- **PASS** — no action needed

---

### Check 1 — uv installed (BLOCKER)

Run: `which uv && uv --version`

- PASS if uv is found and prints a version.
- FAIL if not found. Remediation: `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

### Check 2 — PEP 723 headers (BLOCKER)

For every `.py` file in `plan/scripts/`: check that the file contains the line `# /// script`.

Use Grep with `pattern="# /// script"` across `plan/scripts/*.py`. Cross-reference against a Glob of all `.py` files in `plan/scripts/`. Any file present in the Glob but absent from the Grep results is missing its PEP 723 header.

- PASS if all scripts have the header.
- FAIL for each script missing it. Remediation: add `# /// script\n# requires-python = ">=3.10"\n# ///` at the top of the file.

---

### Check 3 — Phase files present (BLOCKER)

Read `plan/PLAN.md`. Find the Phase Index table — it contains rows like `| 0 | Description | [phase_00_setup.md](phases/phase_00_setup.md) |`. Extract every filename referenced in a `[...](phases/filename.md)` link.

For each extracted filename: check that `plan/phases/<filename>` exists on disk.

- PASS if all linked files exist.
- FAIL for each missing file. Note the phase number and filename.

---

### Check 4 — No orphaned phase references (WARN)

Using Grep, search `plan/` recursively for any string matching `phase_\d+.*\.md` (phase filename patterns). Collect all unique filenames mentioned. For each, check whether the file exists in `plan/phases/`. Flag any filename that appears in prose but does not exist on disk.

- PASS if all referenced filenames resolve to existing files.
- WARN for each unresolvable reference with the file it appears in and the line number.

This catches renames where cross-references were not updated.

---

### Check 5 — Step number consistency (WARN)

For each file in `plan/phases/`: 
1. Extract the phase number from the `## Phase N` or `## Phase N.N` header on line 1.
2. Find all `--step` flag values in the file (pattern: `--step\s+[\d.]+`).
3. Flag any `--step` value that does not match the phase number from the header.

- PASS if all `--step` values match the phase header in every file.
- WARN for each mismatch. Give the filename, line number, header number, and mismatched `--step` value.

---

### Check 6 — Stale detail strings (WARN)

For each file in `plan/phases/`:
1. Extract the phase number from the `## Phase N` header (same as Check 5).
2. Find all `--detail` strings that contain a phrase matching `"Phase \d+` or `"Phase \d+\.\d+` (e.g., `--detail "Phase 10.5: ..."`)
3. Extract the phase number embedded in the detail string. If it differs from the file's header phase number, flag it.

- PASS if no mismatches found.
- WARN for each stale detail string. Give filename, line number, header phase, and detail-string phase. Note: these produce misleading log entries but don't break execution.

---

### Check 7 — Agents installed (BLOCKER)

Read `plan/PLAN.md`. Find the Execution Rules section — it contains a sentence listing agent names in backticks (e.g., `` `ml-critic`, `ml-defender`, `research-reviewer` ``). Extract all agent names from that sentence.

For each agent name: check that `~/.claude/agents/<agent-name>.md` exists.

- PASS if all agents are installed.
- FAIL for each missing agent. Remediation: `cp agents/<agent-name>.md ~/.claude/agents/` from the repo root.

---

### Check 8 — Script syntax (WARN)

For each `.py` file in `plan/scripts/`: run:
```bash
uv run python -c "import ast; ast.parse(open('<path>').read()); print('OK')"
```

- PASS if all scripts parse without errors.
- WARN for each file with a syntax error. Give the filename and error message.

Note: syntax errors in scripts not used until later phases won't block Phase 0, but will cause failures when those phases run.

---

### Check 9 — Operator prerequisite: benchmark_cases.json (BLOCKER)

Check whether `benchmark_cases.json` exists in the experiment root.

- PASS if it exists. Skip the rest of this check.
- If it does not exist: check whether a `.json` file exists in `synthetic-candidates/`. 
  - If a candidate file is found: **execute the copy automatically**:
    ```bash
    cp <experiment-root>/synthetic-candidates/<candidate>.json <experiment-root>/benchmark_cases.json
    ```
    After running the copy, verify `benchmark_cases.json` now exists. If the copy succeeded: report PASS with note "benchmark_cases.json copied from synthetic-candidates/<candidate>.json".
  - If no candidate file exists in `synthetic-candidates/` either: FAIL. Note that benchmark cases must be generated by a non-Anthropic LLM using the companion case generation prompt before the experiment can run.

---

### Check 10 — INVESTIGATION_LOG.jsonl state (INFO)

Check whether `INVESTIGATION_LOG.jsonl` exists in the experiment root.

- If it does not exist: PASS — clean start.
- If it exists: count the number of lines (entries). Report the count.
  - If count == 0: PASS.
  - If count > 0: WARN — report how many entries exist. Note: Phase 0 will append from `seq = N+1`. If a clean log is desired before Phase 0, the user can delete it: `rm <experiment-root>/INVESTIGATION_LOG.jsonl`. Preflight entries (labeled `preflight_check`) are safe to leave if the user does not want a clean log.

---

## Report

After all checks, produce:

1. **Results table** — one row per check:

| # | Check | Status | Note |
|---|-------|--------|------|
| 1 | uv installed | PASS/FAIL | ... |
| 2 | PEP 723 headers | PASS/FAIL | ... |
| ... | | | |

2. **Details** — for each FAIL or WARN, a short block with:
   - What was found
   - Exact remediation command or file/line reference

3. **Verdict**:
   - **READY** — all BLOCKERs pass (WARNs and INFOs do not block)
   - **BLOCKED** — one or more BLOCKERs failed; list them

If BLOCKED, end with: "Resolve the items above and re-run `/preflight` before starting Phase 0."
If READY with warnings, end with: "Experiment is ready to run. Review the warnings above before Phase 0 if desired — they will not block execution but may produce confusing log entries."
If fully READY with no warnings: "All checks passed. Experiment is ready to run."
