---
name: artifact-sync
description: Sync all artifacts after any experiment, analysis step, or issue resolution in ml-lab — orients from journal and git ground truth, updates conclusions, analysis, report, and README, then runs a coherence audit
---

After any experiment, analysis step, or issue resolution in ml-lab, run this full sync before marking work complete.

## Step 1 — Orient via Ground-Truth Sources

Run all four commands. Do not skip any. Use the results to build situational awareness before touching any file.

```bash
# Unresolved issues — the open problem list
python3 .project-log/journal_query.py --unresolved-issues

# Recent experiment entries — logged verdicts and results
python3 .project-log/journal_query.py --list experiment --since 7d

# Recent discoveries — new findings that may change interpretation
python3 .project-log/journal_query.py --list discovery --since 7d

# Recent git activity — what files actually changed and when
git log --oneline -10
```

From these four sources, explicitly state:
- **What changed** in this work session (new results, revised claims, resolved issues)
- **What issues are currently open** per the journal (not per any local file)
- **What findings are logged** that may not yet be reflected in written artifacts

## Step 2 — Identify the Active Experiment

Find all `self_debate_experiment_*` directories that contain a `CONCLUSIONS.md`:

```bash
ls -d self_debate_experiment_*/  # list candidates
```

The active experiment is whichever one is flagged `active` in `CLAUDE.md`. If CLAUDE.md is ambiguous, use the one whose `CONCLUSIONS.md` was most recently committed:

```bash
git log --oneline -- self_debate_experiment_*/CONCLUSIONS.md
```

State the active experiment directory explicitly before proceeding.

## Step 3 — Establish Document Authority Order

Within the active experiment directory, apply this authority hierarchy:

1. **Primary results** (ground truth): `CONCLUSIONS.md`, `next_steps.md`
2. **Summaries**: `REPORT.md`, `TECHNICAL_REPORT.md`
3. **Post-experiment analysis**: `FINAL_SYNTHESIS.md`, `RESEARCH_REPORT.md`, `ENSEMBLE_ANALYSIS.md`, `SENSITIVITY_ANALYSIS.md`
4. **Post-conclusions updates** (potential corrections): any `.md` file committed *after* CONCLUSIONS.md

To find post-conclusions updates, get the commit date of CONCLUSIONS.md and list files modified after it:

```bash
# Date of CONCLUSIONS.md's last commit
git log -1 --format="%ci" -- <experiment_dir>/CONCLUSIONS.md

# Files committed after that date within the experiment dir
git log --since="<date>" --name-only --diff-filter=A -- <experiment_dir>/
```

Post-conclusions docs may contain corrections to CIs, verdicts, or metric values. Read them and note any claims that supersede the primary results.

## Step 4 — Update All Affected Artifacts

Work through each artifact in authority order. If nothing changed that affects it, say so explicitly — do not skip silently.

### `CONCLUSIONS.md` (primary results — update first)
- Add a `> Post-experiment qualification (date):` block under any hypothesis whose verdict changed
- Add numbered entries under any post-experiment review section for new findings
- Do not remove or overwrite existing verdict entries — append only

### `next_steps.md` (primary results)
- Mark resolved action items as complete
- Add new items surfaced by unresolved journal issues
- Update priorities if new findings changed what matters most

### `ENSEMBLE_ANALYSIS.md` (if present)
- Add a new dated section for any ensemble or ablation result
- Update any summary tables if a claim or number changed

### `REPORT.md` / `TECHNICAL_REPORT.md`
- Update the artifacts table with any new files
- Update the conclusion section if any headline claim or result changed
- Ensure any post-conclusions corrections from Step 3 are reflected

### `README.md`
- Add a dated finding block in "What We Found" if a headline number or structural advantage changed
- Update any recommendation sections if the current evidence changes the recommendation

## Step 5 — Coherence Audit

Answer all three questions explicitly. Do not skip any.

**1. Conflicts** — Do any two documents contradict each other on the same claim?
- Start from `CONCLUSIONS.md`: extract the current verdict and key numbers for each hypothesis
- Check that `REPORT.md`, `ENSEMBLE_ANALYSIS.md`, and `README.md` report the same numbers and verdicts
- If a post-conclusions doc from Step 3 contains a correction, verify it has propagated to all downstream documents
- If yes: fix the contradiction before continuing

**2. Staleness** — Does any document reference a finding that has since been revised?
- Cross-reference each claim in `REPORT.md` §conclusion and `README.md` against what `CONCLUSIONS.md` currently says
- Check that unresolved journal issues are not described as resolved in any artifact
- Check that resolved journal issues are not still listed as open
- If yes: update the stale text

**3. Completeness** — Does each entry point contain the strongest current evidence?
- `README.md` — someone landing here cold should see the latest findings, not an older snapshot
- `REPORT.md` conclusion — should reflect the current honest summary including any post-experiment revisions
- `CONCLUSIONS.md` post-experiment section — should list all revisions with dates

If any entry point is missing a finding that others have, add it.

## Step 6 — Confirm and Commit

State which files were changed and why. Then use the **log-commit skill** (`/log-commit`) — do not use bare `git commit`. The commit message should list artifact updates separately from the experiment results that prompted them.

Do not mark any issue resolved until Steps 1–5 are complete.
