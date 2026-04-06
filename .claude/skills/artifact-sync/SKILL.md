---
name: artifact-sync
description: Sync all artifacts after any experiment, analysis step, or issue resolution in ml-debate-lab — updates open issues, ensemble analysis, conclusions, report, and README, then runs a coherence audit
---

After any experiment, analysis step, or issue resolution in ml-debate-lab, run this full sync before marking work complete.

## Step 1 — Identify What Changed

State explicitly what was added or revised in this step:
- New result files (JSON, markdown sections)
- New findings (scores, verdicts, statistics)
- Revised claims (anything that contradicts or narrows a prior claim)

## Step 2 — Update All Affected Artifacts

Work through each artifact. If nothing changed that affects it, say so explicitly — do not skip silently.

### `tasks/open_issues.md`
- Mark resolved issues as `**Resolved** <date>` in the status table
- Add a resolution note at the bottom with: what was done, key numbers, where results live

### `self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md`
- Add a new dated section for any ensemble or ablation result
- Update the "Revised Summary of Protocol Advantages" table if any claim changed

### `self_debate_experiment_v2/CONCLUSIONS.md`
- Add a `> Post-experiment qualification (date):` block under any hypothesis whose verdict changed
- Add a numbered entry under §7 post-experiment review

### `self_debate_experiment_v2/REPORT.md`
- Update the artifacts table (§8) with any new files
- Update the conclusion section (§9) if the headline claim or structural advantage list changed
- Update Related Work if a new finding contradicts a cited mechanism

### `README.md`
- Add a dated `> **<Finding name> (date):**` block in "What We Found" if a headline number or structural advantage changed
- Update the "Should I Use ml-lab or Just Run an Ensemble?" section if the advantage list changed

## Step 3 — Coherence Audit

Answer all three questions explicitly. Do not skip any.

**1. Conflicts** — Do any two documents now contradict each other on the same claim?
- Check: ETD claim, exoneration advantage, headline lift, pass counts, ensemble mean
- If yes: fix the contradiction before continuing

**2. Staleness** — Does any document reference a finding that has since been revised?
- Check for: old advantage claims, old open-issue status, old interpretation language
- Search for key claim keywords: "adversarial forcing", "ETD advantage", "isolation necessary", "cleaner exonerations", "self-scoring bias"
- If yes: update the stale text

**3. Completeness** — Does each of these entry points contain the strongest current evidence on each active claim?
  - `README.md` — someone landing here cold should see the latest findings
  - `REPORT.md` §9 conclusion — should reflect the current honest summary
  - `CONCLUSIONS.md` §7 — should list all post-experiment revisions

If any entry point is missing a finding that others have, add it.

## Step 4 — Confirm and Commit

State which files were changed and why. Then commit with a message that lists the artifact updates separately from the experiment results.

Do not mark any issue resolved until Steps 1–3 are complete.
