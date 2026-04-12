---
name: artifact-sync
description: Audit artifacts for staleness and conflicts after any experiment step or issue resolution. Default mode is audit-only (produces a change manifest). Fix mode applies changes with per-file commits.
---

Run this after any experiment, analysis step, or issue resolution — before marking work complete.
[→ decision 88357f02]

**Default is audit-only.** If the manifest is clean (no conflicts, no staleness), you're done — the completion gate is satisfied. If issues are found, present the manifest and let the user decide whether to fix.

---

## Step 1 — Discover and Classify

### 1a. Identify the active experiment

```bash
ls -d self_debate_experiment_*/
```

The active experiment is whichever is flagged `active` in `CLAUDE.md`. If ambiguous, use the most recently committed `CONCLUSIONS.md`:

```bash
git log --oneline -1 -- self_debate_experiment_*/CONCLUSIONS.md
```

State the active experiment directory explicitly.

### 1b. Find all .md files in scope

```bash
# Experiment dir
ls <experiment_dir>/*.md

# Root level
ls *.md
```

### 1c. Classify each file into a tier

Apply these rules **in order** (first match wins). For each file, state its tier explicitly.

**Frozen** — never edited by this skill:
1. First 10 lines contain a freeze/correction header (`> **Note` or `> **Correction`)
2. Filename matches a snapshot pattern: `PEER_REVIEW*`, `REPORT_ADDENDUM*`, `SENSITIVITY_ANALYSIS*`
3. Is `REPORT.md` AND any other non-frozen doc in the same directory has a more recent commit:
   ```bash
   git log -1 --format="%ci" -- <experiment_dir>/REPORT.md
   git log -1 --format="%ci" -- <experiment_dir>/FINAL_SYNTHESIS.md  # or other post-hoc doc
   ```

**Derived** — out of sync scope:
4. `.md` file outside the active experiment directory AND not `README.md`
   (e.g., `WORKING_PAPER.md`, `RELATED_WORK.md`, `research-notes/*.md`)

**Canonical** — source of truth:
5. `CONCLUSIONS.md` — always canonical for hypothesis verdicts and formal test results

**Live** — sync targets (kept current):
6. `README.md` — always live
7. All remaining non-frozen, non-derived `.md` files in the experiment directory

### 1d. Show the classification

Present a table:

```
TIER CLASSIFICATION (experiment: self_debate_experiment_vN/)

Canonical:  CONCLUSIONS.md
Live:       README.md, FINAL_SYNTHESIS.md, next_steps.md, ENSEMBLE_ANALYSIS.md
Frozen:     REPORT.md (superseded), PEER_REVIEW_R1.md, SENSITIVITY_ANALYSIS.md, REPORT_ADDENDUM.md
Derived:    WORKING_PAPER.md, RELATED_WORK.md

Audit scope: 5 files (1 canonical + 4 live)
Skipping:   4 frozen, 2 derived
```

If a classification is uncertain, flag it and ask.

---

## Step 2 — Orient via Ground Truth

Run all four queries. Use the results to understand what changed — do not start editing.

```bash
python3 .project-log/journal_query.py --unresolved-issues
python3 .project-log/journal_query.py --list experiment --since 7d
python3 .project-log/journal_query.py --list discovery --since 7d
git log --oneline -10
```

State explicitly:
- **What changed** in this work session (new results, revised claims, resolved issues)
- **What issues are open** per the journal
- **What findings are logged** that may not yet appear in live docs

---

## Step 3 — Audit

Read the canonical doc (`CONCLUSIONS.md`) and all live docs. For each live doc, check:

1. **Conflicts** — Does any claim in this doc contradict the canonical source?
   - When two live docs conflict: `git log -1 --format="%ci" -- <file>` — more recent commit wins
2. **Staleness** — Does this doc reference a finding that has since been revised? Check against journal experiment/discovery entries.
3. **Completeness** — Is any finding present in the canonical source missing from this live doc, if the doc's scope covers it?

Also check:
- Unresolved journal issues are not described as resolved in any live doc
- Resolved journal issues are not still listed as open

### Produce the manifest

For each issue found, output one entry:

```
[CONFLICT|STALE|MISSING] <file>:<line>
  Current:   "<text in the file>"
  Should be: "<corrected text>"
  Authority: <canonical file or journal entry ID>
  Reason:    <one sentence>
```

If the manifest is empty, state:

```
AUDIT CLEAN — no conflicts, staleness, or completeness gaps across N files.
```

This satisfies the completion gate. Stop here unless the user requests fixes.

---

## Step 4 — Fix (only when requested)

If the user says to fix, apply changes from the manifest:

1. For each file in the manifest, make the edits
2. **Commit per file** — each commit message cites the authority:
   ```
   fix(<file>): <what changed> (authority: <source>)
   ```
3. Log each commit via the journal (`journal_log.py --type git`)

Do not batch multiple files into one commit. The point is per-file traceability.

---

## Notes

- **Frozen docs are never wrong** — they're snapshots. If someone reads a frozen doc and gets a stale number, that's expected. The freeze header tells them where to find the current value.
- **Derived docs are the author's responsibility.** If WORKING_PAPER.md has a stale number, that's a separate editing task, not an artifact-sync issue.
- **Canonical wins ties.** When CONCLUSIONS.md and a live doc disagree, CONCLUSIONS.md is authoritative. When two live docs disagree, git recency breaks the tie.
- **The skill does not propagate numbers into new files.** It only checks existing claims in live docs against canonical sources. Adding a new finding to README.md is an authoring decision, not a sync operation.
