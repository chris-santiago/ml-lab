## Phase 5.5 — Pre-Benchmark Difficulty Gate

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **Primary difficulty validation gate.** Runs BEFORE Phase 6 begins. Prevents a full-scale benchmark run on cases whose difficulty labels are too easy to be discriminating. Issue 9 remediation (pre-execution stage).

Pre-registration (Phase 3) must be locked before this gate runs.

```bash
uv run log_entry.py --step 5.5 --cat workflow --action step_start --detail "Phase 5.5: pre-benchmark difficulty gate — sampling up to 10 hard cases"
```

**Instruction:**

Load self_debate_experiment_v4/benchmark_cases_verified.json.
Select up to 10 cases where difficulty == "hard" (in file order).

For each selected case, run a single baseline call — task_prompt only, no role, no
structure, no additional context. Do NOT run the full 3-pass protocol.

For each baseline response, score the following inline (do not invoke self_debate_poc.py):
- IDR: Did the response identify all must_find_issue_ids?
- IDP: Was at least one issue description substantively correct?
- FVC: Is the verdict (or implied resolution) in acceptable_resolutions?

Compute a preliminary baseline mean for each case from those three binary scores.
Count how many of the sampled hard cases have a baseline mean >= 0.55.

If more than 4 of the sampled hard cases exceed 0.55:
  STOP. Do not proceed to Phase 6.
  Log: uv run log_entry.py --step 5.5 --cat gate --action difficulty_preflight_failed \
       --detail "Pre-benchmark gate FAILED: N/10 hard cases exceeded baseline ceiling" \
       --meta '{"flagged_count": N, "threshold": 0.55, "sampled_cases": [...]}'
  Present findings to LEAD. Cases must be revised or re-sourced before the benchmark runs.

If 4 or fewer hard cases exceed 0.55:
  Log: uv run log_entry.py --step 5.5 --cat gate --action difficulty_preflight_passed \
       --detail "Pre-benchmark gate passed: N/10 hard cases at or below baseline ceiling" \
       --meta '{"flagged_count": N, "threshold": 0.55, "sampled_cases": [...]}'
  Proceed to Phase 6.

```bash
uv run log_entry.py --step 5.5 --cat workflow --action step_end \
  --detail "Phase 5.5 difficulty gate complete; outcome logged above"
```

**Phase 5.5 commit:**
```bash
git add self_debate_experiment_v4/INVESTIGATION_LOG.jsonl
git commit -m "chore: snapshot v4 phase 5.5 artifacts — difficulty preflight gate result logged [none]"
uv run log_entry.py --step 5.5 --cat exec --action commit_phase_artifacts --detail "committed phase 5.5 artifacts: difficulty preflight gate outcome in INVESTIGATION_LOG.jsonl"
```

---
