---
name: research-report
description: Synthesize a full research report from the project journal, git history, and supplementary markdown files. Produces RESEARCH_REPORT.md at the repo root. Use when the user says /research-report, "write a full research report", "end-of-project writeup", "document our full research history", "create a project report", or "document our research history".
---

## Step 1: Find repo root and check journal

```bash
git rev-parse --show-toplevel
```

If `.project-log/journal.jsonl` does not exist, say: "No journal found. Run `/journal-init` first." Stop.

## Step 2: Gather all inputs

### Journal entries
Read the full `.project-log/journal.jsonl`. Group by type for synthesis.

### Git history
```bash
git log --oneline --all
```

### Supplementary markdown files
Glob for files matching these patterns at repo root and up to 2 levels deep:
```bash
find <repo-root> -maxdepth 3 -name "*.md" | grep -iE "(ISSUE|lesson|POST_MORTEM|TODO|NOTES|CHANGELOG|DECISIONS)"
```
Do not hardcode paths. Read any matches and incorporate if relevant.

### Existing RESEARCH_REPORT.md
Check if one already exists — note it to the user but do not let it constrain the new synthesis.

## Step 3: Synthesize narrative

Write `RESEARCH_REPORT.md` with the following sections. Include only sections that have content — omit empty sections rather than writing placeholder text.

```markdown
# Research Report — <project name>

*Generated <date> from <N> journal entries and <N> commits.*

## Problem Statement
[What problem is this project trying to solve, derived from early decisions/discoveries]

## Timeline
[Chronological sequence of significant events — milestones, major decisions, key experiments — drawn from journal timestamps and git log]

## What Was Tried
[All approaches, experiments, and hypotheses — confirmed, refuted, and inconclusive]

## What Failed
[Issues and post-mortems — what broke, root causes, contributing factors]

## What Worked
[Confirmed experiments, successful resolutions, key discoveries with positive implications]

## Key Decisions
[All decision-type entries with rationale; note any decisions that were later revisited]

## Issues and Resolutions
[Linked pairs where available; unresolved issues clearly marked]

## Current State
[From latest checkpoint — in_progress, pending_decisions, open_threads]

## Open Questions
[Aggregated open_threads across all checkpoints, deduplicated, with oldest first]
```

Be specific — reference actual entry content, not vague summaries. Quote descriptions from the journal where they are clear and concise.

## Step 4: Show draft and confirm

Show the full draft to the user.

Ask: `► Write to RESEARCH_REPORT.md? This will overwrite any existing file. (y/n)`

(Git has history — overwriting is safe.)

## Step 5: Write file

Write to `<repo-root>/RESEARCH_REPORT.md`.

Confirm: "RESEARCH_REPORT.md written — <N> lines."
