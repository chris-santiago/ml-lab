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

## Step 3 — Establish Document Authority via Git Log

Authority is determined by **commit recency, not document category**. A post-hoc analysis doc committed after `CONCLUSIONS.md` is more authoritative on the claims it touches — it incorporates subsequent analysis, peer review, or corrections. Git log is the oracle.

For each document category, retrieve the last-modified commit date:

```bash
# Get commit dates for all .md files in the experiment dir
git log --format="%ci %s" -- <experiment_dir>/*.md | sort -r | head -30

# For a specific file
git log -1 --format="%ci" -- <experiment_dir>/<file>.md
```

**Document roles** (not a strict authority ranking — use commit dates to resolve conflicts):
- `CONCLUSIONS.md`, `REPORT.md`, `TECHNICAL_REPORT.md` — main experiment output documents
- `next_steps.md`, `FINAL_SYNTHESIS.md`, `RESEARCH_REPORT.md` — post-hoc docs; written after the main experiment to incorporate corrections, peer review, or updated analysis
- `ENSEMBLE_ANALYSIS.md`, `SENSITIVITY_ANALYSIS.md` — post-hoc supplementary analysis

**Post-hoc docs are authoritative over main experiment docs on the claims they address.** When a post-hoc doc contains a revised CI, flipped verdict, or updated metric, that correction must flow back into `CONCLUSIONS.md`, `REPORT.md`, and other main docs — not the other way around.

When multiple post-hoc docs are in conflict, the most recently committed one wins. If the git log shows many recent changes across several docs, list the commit dates explicitly and resolve each conflict by recency before proceeding.

## Step 4 — Update All Affected Artifacts

Read all post-hoc docs first. Extract any corrections or updates they contain. Then apply those corrections to the main experiment docs. Work through each artifact below. If nothing changed that affects it, say so explicitly — do not skip silently.

### Post-hoc docs → `CONCLUSIONS.md`
- For each correction or revised claim found in post-hoc docs: add a `> Post-experiment qualification (date):` block under the affected hypothesis
- Add numbered entries under any post-experiment review section for new findings
- Do not remove or overwrite existing verdict entries — append only

### Post-hoc docs → `REPORT.md` / `TECHNICAL_REPORT.md`
- Update the conclusion section if any headline claim or result was revised by a post-hoc doc
- Update the artifacts table with any new files
- Ensure revised CIs, verdicts, or metric values from post-hoc docs are reflected

### `ENSEMBLE_ANALYSIS.md` (if present)
- Add a new dated section for any ensemble or ablation result
- Update any summary tables if a claim or number changed

### `FINAL_SYNTHESIS.md` / `RESEARCH_REPORT.md`
- If updates were made to `CONCLUSIONS.md` or `REPORT.md` above, check these docs for consistency
- Update if they reference a now-superseded claim from main experiment docs

### `README.md`
- Add a dated finding block in "What We Found" if a headline number or structural advantage changed
- Update any recommendation sections if the current evidence changes the recommendation

### `next_steps.md`
- Mark resolved action items as complete using journal resolution entries as the source of truth
- Add new items surfaced by unresolved journal issues
- Update priorities if new findings changed what matters most

## Step 5 — Coherence Audit

Answer all three questions explicitly. Do not skip any.

**1. Conflicts** — Do any two documents contradict each other on the same claim?
- For each conflict: use `git log -1 --format="%ci" -- <file>` to determine which doc was committed more recently — that version is authoritative
- Fix all conflicts before continuing; note which doc was updated to match which

**2. Staleness** — Does any document reference a finding that has since been revised?
- Cross-reference claims in `REPORT.md` §conclusion and `README.md` against the most recent version of each result (post-hoc docs + journal entries)
- Check that unresolved journal issues are not described as resolved in any artifact
- Check that resolved journal issues are not still listed as open
- If yes: update the stale text

**3. Completeness** — Does each entry point contain the strongest current evidence?
- `README.md` — someone landing here cold should see the latest findings, not an older snapshot
- `REPORT.md` conclusion — should reflect the current honest summary including all post-experiment revisions
- `CONCLUSIONS.md` post-experiment section — should list all revisions with dates

If any entry point is missing a finding that others have, add it.

## Step 6 — Confirm and Commit

State which files were changed and why. Then use the **log-commit skill** (`/log-commit`) — do not use bare `git commit`. The commit message should list artifact updates separately from the experiment results that prompted them.

Do not mark any issue resolved until Steps 1–5 are complete.
