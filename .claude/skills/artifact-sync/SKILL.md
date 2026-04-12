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

This scan is intentionally shallow — subdirectories (`plan/`, `pipeline/`, `research-notes/`) are not in audit scope.

### 1c. Classify each file into a tier

Apply these rules **in order** (first match wins). For each file, state its tier explicitly.

**Frozen** — never edited by this skill:
1. First 10 lines contain a freeze/correction header (`> **Note` or `> **Correction`)
2. Filename matches a snapshot pattern: `PEER_REVIEW*`, `REPORT_ADDENDUM*`, `SENSITIVITY_ANALYSIS*`, `HYPOTHESIS*`, `V[0-9]_*`
3. Is `REPORT.md` AND any non-frozen doc in the same directory has a more recent commit:
   ```bash
   git log -1 --format="%ci" -- <experiment_dir>/REPORT.md
   git log -1 --format="%ci" -- <experiment_dir>/CONCLUSIONS.md  # or any other doc
   ```

**Derived** — out of sync scope:
4. `.md` file at the repo root AND not `README.md` AND not `CLAUDE.md`
   (e.g., `WORKING_PAPER.md`, `RELATED_WORK.md`)

**Canonical** — source of truth:
5. `CONCLUSIONS.md` — always canonical for hypothesis verdicts and formal test results

**Post-hoc** — staleness-only audit:
6. Filename matches a post-hoc pattern: `FINAL_SYNTHESIS*`, `ENSEMBLE_ANALYSIS*`, `*_SYNTHESIS*`
   These documents interpret or extend canonical findings. Conflicts and completeness gaps are
   intentional; only staleness is audited.

**Live** — sync targets (kept current):
7. `README.md` — always live
8. All remaining non-frozen, non-derived, non-post-hoc `.md` files in the experiment directory

### 1d. Show the classification

Present a table:

```
TIER CLASSIFICATION (experiment: self_debate_experiment_vN/)

Canonical:  CONCLUSIONS.md
Post-hoc:   FINAL_SYNTHESIS.md, ENSEMBLE_ANALYSIS.md
Live:       README.md, next_steps.md
Frozen:     REPORT.md (superseded), PEER_REVIEW_R1.md, SENSITIVITY_ANALYSIS.md, REPORT_ADDENDUM.md
Derived:    WORKING_PAPER.md, RELATED_WORK.md

Audit scope: 5 files (1 canonical + 2 post-hoc + 2 live)
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

Read the canonical doc (`CONCLUSIONS.md`), all post-hoc docs, and all live docs.

### Live docs — check all three:

1. **Conflicts** — Does any claim in this doc contradict the canonical source?
   - When two live docs conflict: `git log -1 --format="%ci" -- <file>` — more recent commit wins
2. **Staleness** — Does this doc reference a finding that has since been revised? Check against journal experiment/discovery entries.
3. **Completeness** — Is any finding present in the canonical source missing from this live doc, if the doc's scope covers it?

### Post-hoc docs — staleness only:

1. **Staleness** — Does this doc reference a finding revised since it was last committed? Check journal experiment/discovery entries.
2. **Timestamp staleness** — Run:
   ```bash
   git log -1 --format="%ci" -- <experiment_dir>/CONCLUSIONS.md
   git log -1 --format="%ci" -- <experiment_dir>/<post-hoc-doc>
   ```
   If CONCLUSIONS.md has a newer commit and the two docs disagree on a factual claim (a number, verdict string, or test name), flag as STALE. Do not flag interpretive extensions — they are intentional.

Do not check post-hoc docs for conflicts or completeness.

### Both tiers — also check:
- Unresolved journal issues are not described as resolved in any live or post-hoc doc
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
2. **Commit per file** using `/log-commit` — when log-commit asks for a message, suggest:
   ```
   fix(<file>): <what changed> (authority: <source>)
   ```
3. log-commit handles both the git commit and the journal entry in one step — do not call `git commit` or `journal_log.py` directly

Do not batch multiple files into one commit. The point is per-file traceability.

---

## Notes

- **Frozen docs are never wrong** — they're snapshots. If someone reads a frozen doc and gets a stale number, that's expected. The freeze header tells them where to find the current value.
- **Derived docs are the author's responsibility.** If WORKING_PAPER.md has a stale number, that's a separate editing task, not an artifact-sync issue.
- **Canonical wins ties.** When CONCLUSIONS.md and a live doc disagree, CONCLUSIONS.md is authoritative. When two live docs disagree, git recency breaks the tie.
- **The skill does not propagate numbers into new files.** It only checks existing claims in live docs against canonical sources. Adding a new finding to README.md is an authoring decision, not a sync operation.
