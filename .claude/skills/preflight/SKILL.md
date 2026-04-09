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
- FAIL for each MISSING agent. Remediation: `cp plugins/ml-lab/<agent-name>.md ~/.claude/agents/` from the repo root.

---

### Check 8 — Script syntax + log_entry.py smoke test (WARN / BLOCKER)

**8a — Syntax check (WARN):** For each `.py` file in `plan/scripts/`: run:
```bash
uv run python -c "import ast; ast.parse(open('<path>').read()); print('OK')"
```
- PASS if all scripts parse without errors.
- WARN for each file with a syntax error. Give the filename and error message.

Note: syntax errors in scripts not used until later phases won't block Phase 0, but will cause failures when those phases run.

**8b — log_entry.py smoke test (BLOCKER):** `log_entry.py` is used in every phase — a runtime failure blocks the entire experiment. Verify it actually executes (not just parses) and then clean up the test entry.

Run this sequence:
```bash
# 1. Record pre-test log state
LOG="<experiment-root>/INVESTIGATION_LOG.jsonl"
existed_before=false
lines_before=0
[ -f "$LOG" ] && existed_before=true && lines_before=$(wc -l < "$LOG")

# 2. Run the smoke test
# log_entry.py is only copied to the experiment root by Phase 0.
# Before Phase 0, use plan/scripts/log_entry.py directly.
LOGENTRY="plan/scripts/log_entry.py"
[ -f "<experiment-root>/log_entry.py" ] && LOGENTRY="log_entry.py"
cd <experiment-root>
uv run $LOGENTRY --step 0 --cat workflow --action preflight_smoke_test \
  --detail "preflight skill smoke test — will be removed"

# 3. Verify entry was written
lines_after=$(wc -l < "$LOG")
if [ "$lines_after" -gt "$lines_before" ]; then
  echo "SMOKE_OK: log_entry.py wrote an entry"
else
  echo "SMOKE_FAIL: no entry written"
fi

# 4. Clean up: remove the test entry
if [ "$existed_before" = false ]; then
  rm "$LOG"
  echo "CLEANUP: removed INVESTIGATION_LOG.jsonl (did not exist before)"
else
  # Remove only the last line (the smoke test entry)
  if [ "$(uname)" = "Darwin" ]; then
    sed -i '' -e '$ d' "$LOG"
  else
    sed -i '$ d' "$LOG"
  fi
  echo "CLEANUP: removed smoke test entry; log restored to $lines_before entries"
fi
```

- PASS if `SMOKE_OK` and cleanup succeeds.
- FAIL if `SMOKE_FAIL`. The log_entry.py script has a runtime error — inspect the output above and fix before Phase 0.

---

### Check 9 — Operator prerequisite: benchmark_cases.json (BLOCKER)

Check whether `benchmark_cases.json` exists in the experiment root.

- PASS if it exists. Skip the rest of this check.
- If it does not exist:
  - **If `plan/scripts/normalize_cases.py` exists:** the pipeline output requires schema normalization before it can be used as a benchmark input. Run:
    ```bash
    cd <experiment-root> && uv run plan/scripts/normalize_cases.py \
      --input synthetic-candidates/selected_cases_all.json \
      --output benchmark_cases.json
    ```
    Report PASS with note "benchmark_cases.json generated via normalize_cases.py from synthetic-candidates/selected_cases_all.json".
    > Note: do NOT do a raw copy or merge when `normalize_cases.py` is present — the pipeline output uses a flat schema that is incompatible with the experiment scripts. normalize_cases.py handles all field remapping, ID generation, difficulty derivation, and schema nesting.
  - **If `normalize_cases.py` does not exist:** count `.json` files in `synthetic-candidates/`.
    - **Exactly one file found:** execute the copy automatically:
      ```bash
      cp <experiment-root>/synthetic-candidates/<candidate>.json <experiment-root>/benchmark_cases.json
      ```
      Report PASS with note "benchmark_cases.json copied from synthetic-candidates/<candidate>.json".
    - **Multiple files found:** this experiment uses a multi-file merge. Execute the merge automatically:
      ```bash
      cd <experiment-root> && uv run python -c "
      import json, glob
      files = sorted(glob.glob('synthetic-candidates/*.json'))
      merged, seen_ids = [], set()
      for path in files:
          with open(path) as f:
              cases = json.load(f)
          for c in cases:
              if c['case_id'] in seen_ids:
                  raise ValueError(f'Case ID collision: {c[\"case_id\"]} in {path}')
              seen_ids.add(c['case_id'])
              merged.append(c)
      with open('benchmark_cases.json', 'w') as f:
          json.dump(merged, f, indent=2)
      print(f'Merged {len(files)} files = {len(merged)} cases')
      "
      ```
      Report PASS with note "benchmark_cases.json merged from N source files in synthetic-candidates/".
    - **No `.json` files in `synthetic-candidates/`:** FAIL. Benchmark cases must be generated by a non-Anthropic LLM using the companion case generation prompt before the experiment can run.

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

---

## Post-Check: Record Completion (READY only)

If the verdict is **READY**, write a persistent log entry so Phase 0 can detect that preflight has run and skip its redundant infrastructure steps:

```bash
cd <experiment-root>
LOGENTRY="plan/scripts/log_entry.py"
[ -f "log_entry.py" ] && LOGENTRY="log_entry.py"
uv run $LOGENTRY --step 0 --cat workflow --action preflight_complete \
  --detail "preflight skill completed — all blockers passed; Phase 0 infrastructure checks are satisfied"
```

This entry persists in `INVESTIGATION_LOG.jsonl` and is NOT cleaned up (unlike the Check 8b smoke test). Do **not** write this entry if the verdict is BLOCKED.
