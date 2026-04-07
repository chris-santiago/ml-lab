## Phase 6.75 — Difficulty Validation Probe (Secondary In-Execution Check)

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

> **Secondary difficulty check during execution.** The primary difficulty gate ran in Phase 5.5 before any benchmark calls were made. This phase catches drift or edge cases that emerge during the full run, when all baseline outputs are available. Issue 9 remediation (in-execution stage).

After all Phase 6 conditions have completed, run a retrospective baseline probe:

```bash
uv run log_entry.py --step 6.75 --cat workflow --action step_start --detail "Phase 6.75: retrospective difficulty probe on first 10 hard cases from baseline outputs"
```

**Instruction:**

Examine the baseline raw outputs for the first 10 hard cases in
benchmark_cases_verified.json (in file order).

For each hard case, read v5_raw_outputs/{case_id}_baseline_run1.json and compute
a preliminary baseline score by checking:
- Did the baseline find all must_find_issue_ids? (IDR)
- Was the verdict in acceptable_resolutions? (FVC)
- Is the verdict the correct type? (DRQ)

Estimate the baseline rubric mean for each of the 10 cases.
Count how many of the 10 hard cases show baseline mean >= 0.55.

If more than 4 of the 10 hard cases score >= 0.55 on baseline:
  Flag: "Hard case difficulty labels may not predict rubric performance.
         {N}/10 hard cases show baseline mean >= 0.55. Review hard case design
         before accepting difficulty labels as valid."
  Log: uv run log_entry.py --step 6.75 --cat decision --action difficulty_probe_warning
       --detail "N/10 hard cases exceeded expected baseline ceiling"
       --meta '{"flagged_count": N, "threshold": 0.55}'
  Pause and present findings to LEAD before proceeding to Phase 7.

If 4 or fewer: log the result and proceed.

```bash
uv run log_entry.py --step 6.75 --cat workflow --action difficulty_probe_complete \
  --detail "Hard case difficulty validated: N/10 above threshold" \
  --meta '{"above_threshold": N}'
uv run log_entry.py --step 6.75 --cat workflow --action step_end --detail "Phase 6.75 complete"
```

> **Phase 6.75 note:** No new artifact files are produced in this phase (probe reads existing baseline outputs; findings go to INVESTIGATION_LOG.jsonl only). No commit required — log entry above is sufficient.

---
