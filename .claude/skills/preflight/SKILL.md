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

Run this exact command from the experiment root to extract bare phase filenames:
```bash
grep -roh 'phase_[0-9][0-9_a-z]*\.md' plan/ | sort -u
```
The pattern `phase_[0-9][0-9_a-z]*\.md` stops at `.md` and only matches digits, underscores, and lowercase letters — it will not capture trailing markdown link syntax like `](phases/...`. For each unique filename returned, check whether `plan/phases/<filename>` exists on disk.

- PASS if all referenced filenames resolve to existing files.
- WARN for each unresolvable reference. To find which file contains it, run: `grep -rn '<filename>' plan/`

This catches renames where cross-references were not updated.

---

### Check 5 — Step number consistency (WARN)

Phase files use either `# Phase N` or `## Phase N` as the header (both forms are used; the number of `#` characters varies). Run this for each file in `plan/phases/`:

```bash
for f in plan/phases/*.md; do
  fname=$(basename "$f")
  # Match both # and ## headers
  header=$(grep -m1 '^#\+ Phase' "$f" | grep -o 'Phase [0-9.]*' | awk '{print $2}')
  steps=$(grep -o '\-\-step [0-9.]*' "$f" | awk '{print $2}' | sort -u)
  for s in $steps; do
    [ "$s" != "$header" ] && echo "MISMATCH [$fname] header=$header --step=$s"
  done
done
```

- PASS if no output.
- WARN for each line of output. Include filename, header phase, and mismatched `--step` value.

---

### Check 6 — Stale detail strings (WARN)

Run this for each file in `plan/phases/`:

```bash
for f in plan/phases/*.md; do
  fname=$(basename "$f")
  header=$(grep -m1 '^#\+ Phase' "$f" | grep -o 'Phase [0-9.]*' | awk '{print $2}')
  grep -n '"Phase [0-9]' "$f" | while IFS=: read lineno content; do
    detail_phase=$(echo "$content" | grep -o '"Phase [0-9.]*' | sed 's/"Phase //')
    [ -n "$detail_phase" ] && [ "$detail_phase" != "$header" ] && \
      echo "STALE [$fname:$lineno] header=Phase $header detail=Phase $detail_phase"
  done
done
```

- PASS if no output.
- WARN for each line of output. Note: these produce misleading log entries but don't break execution.

---

### Check 7 — Agents installed (BLOCKER)

The Execution Rules section of `plan/PLAN.md` contains exactly one sentence of the form:
> `Agents (`ml-critic`, `ml-defender`, ...) are invoked by name via the Agent tool.`

Extract agent names from that sentence only — not from the full file. Run:
```bash
grep 'invoked by name' plan/PLAN.md | grep -o '`[a-z][a-z-]*`' | tr -d '`' | while read agent; do
  if [ -f "$HOME/.claude/agents/${agent}.md" ]; then
    echo "INSTALLED: $agent"
  else
    echo "MISSING: $agent"
  fi
done
```

The pattern `` `[a-z][a-z-]*` `` matches only lowercase-letter agent names in backticks — it will not match schema field names, step numbers, or other backtick-quoted terms in the file.

- PASS if all agents print INSTALLED.
- FAIL for each MISSING agent. Remediation: `cp agents/<agent-name>.md ~/.claude/agents/` from the repo root.

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
