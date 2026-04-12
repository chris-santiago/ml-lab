---
name: sync-ml-lab-docs
description: Propagate ml-lab.md changes to the two downstream artifacts that must stay in sync with it — plugins/ml-lab/ML_LAB_FLOW.md (mermaid flowchart) and README.md (mermaid copy + investigation logging section + Gate prose).
user-invocable: true
---

You are executing the `sync-ml-lab-docs` skill. Your job is to propagate any changes in `plugins/ml-lab/ml-lab.md` to two downstream artifacts and report exactly what changed.

## Files involved

| File | What must stay in sync |
|------|----------------------|
| `plugins/ml-lab/ML_LAB_FLOW.md` | The mermaid flowchart — must match the workflow structure, node labels, gate labels, and LOG node caption in ml-lab.md |
| `README.md` | Mermaid block under `### The Full Workflow` + any prose sections that describe or summarize workflow content from ml-lab.md (gates, logging, example runs, etc.) |

## Steps

### 1. Read source and all downstream files

Read these files in full:
- `plugins/ml-lab/ml-lab.md` (source of truth)
- `plugins/ml-lab/ML_LAB_FLOW.md`
- `README.md`

### 2. Update `plugins/ml-lab/ML_LAB_FLOW.md`

Extract the canonical mermaid flowchart from `plugins/ml-lab/ml-lab.md`. The flowchart is the primary visual specification — it must reflect:
- All nodes and their labels (especially PREFLIGHT, Gate 1, Gate 2, Gate 3, LOG)
- The LOG node caption (must match the log_entry.py invocation pattern in ml-lab.md)
- Gate labels (must match gate descriptions in ml-lab.md)
- Any new or removed nodes since the last sync

Rewrite the mermaid block in `ML_LAB_FLOW.md` to match.

### 3. Update `README.md` — mermaid block

Locate the mermaid flowchart block under the `### The Full Workflow` section in README.md. Replace it with the same flowchart you just put in ML_LAB_FLOW.md. The block starts with ` ```mermaid ` and ends with ` ``` `.

### 4. Update `README.md` — prose sections derived from ml-lab.md

README.md contains several narrative sections that summarize or describe content from `plugins/ml-lab/ml-lab.md`. For each such section, compare against the corresponding source section in ml-lab.md and update the README to reflect the current authoritative content. Do not look for specific expected text — read both files and use judgment to identify any drift.

Sections to check include (but are not limited to):
- Any section describing the investigation logging workflow (schema, invocation, constraints)
- Any section describing gate behavior (Gate 1, Gate 2, Gate 3 — what triggers them, what blocks them, how they resolve)
- Any example run narrative or walkthrough prose that references workflow steps

For each section that has drifted from ml-lab.md: update the README to match the current behavior. Preserve README-appropriate voice (user-facing, explanatory) rather than copying agent-prompt text verbatim.

### 5. Report

List every change made, organized by file. For each change, give one line describing what was updated and why (e.g., "Updated LOG node caption to reference `uv run log_entry.py`"). If a file was already in sync, say so explicitly.

If no changes were needed anywhere, report "All downstream artifacts already in sync with plugins/ml-lab/ml-lab.md."

Do NOT remind the user to run `claude plugin reinstall ml-lab`. The `PostToolUse` hook (`sync-plugin-cache.sh`) fires automatically on every Edit or Write to any file under `plugins/ml-lab/` and rsyncs the directory to the plugin cache immediately — manual reinstall is not needed.
