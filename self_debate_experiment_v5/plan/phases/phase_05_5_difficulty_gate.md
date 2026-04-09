## Phase 5.5 — Pre-Benchmark Difficulty Gate

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

> **Primary difficulty validation gate.** Runs BEFORE Phase 6 begins. Prevents a full-scale benchmark run on cases whose difficulty labels are miscalibrated. Incorporates v4 DEBATE Issue 9 resolution: expanded to 15-case stratified pilot with three-branch decision rule and relabeling branch. Hard-case sub-sample increased to 10 per v5 acceptance criterion (≥6/10 < 0.55).

Pre-registration (Phase 3) must be locked before this gate runs.

```bash
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat workflow --action step_start --detail "Phase 5.5: pre-benchmark difficulty gate — 15-case stratified pilot + 10-case hard ceiling check"
```

**Instruction:**

Load `self_debate_experiment_v5/benchmark_cases_verified.json`.

Select a **stratified pilot of 15 cases**: exactly 5 easy, 5 medium, 5 hard (in file order within each stratum). Additionally, from the hard stratum, select 5 more hard cases (cases 6–10 by file order) for the hard-case ceiling check, giving **10 hard cases total evaluated** (the first 5 contribute to both the Spearman check and the ceiling check; all 10 contribute to the ceiling check only).

For each selected case, run a single baseline call using **`claude-haiku-4-5`** — task_prompt only, no role, no structure, no additional context. Do NOT run the full 3-pass protocol.

> **Why claude-haiku-4-5:** Haiku is the acceptance criterion model for v5 hard case generation. Using the same model here ensures the gate reflects the same calibration standard used during case authoring. If Haiku scores hard cases above 0.55, the cases are easier than designed.

For each baseline response, score the following inline (do not invoke self_debate_poc.py):
- IDR: Did the response identify all must_find_issue_ids?
- IDP: Was at least one issue description substantively correct?
- FVC: Is the verdict (or implied resolution) in acceptable_resolutions?
Compute a preliminary baseline mean for each case from the applicable scores (IDR, IDP, FVC). Exclude N/A dimensions (defense_wins cases: IDR/IDP = N/A) from the denominator.

**Preliminary Spearman check (on the 15-case stratified pilot):**
Rank the 15 cases by difficulty (easy=1, medium=2, hard=3) and by their baseline means. Compute Spearman rho between rank-difficulty and baseline scores. If rho > 0 (hard cases scoring HIGHER than easy ones — inverted correlation), flag as a warning and present to LEAD before proceeding. This is an early warning for the Issue 15 pattern observed in v4.

**Hard-case ceiling check — v5 acceptance criterion (BLOCKER):**
Count how many of the 10 sampled hard cases have a baseline mean >= 0.55.
- If **fewer than 6** of the 10 hard cases score mean < 0.55 (i.e., ≥5 of 10 exceed 0.55): **STOP.**
  Gate fails. Log and present to LEAD. Hard cases must be revised or re-sourced.
  ```bash
  cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat gate --action difficulty_preflight_failed \
       --detail "Pre-benchmark gate FAILED: only N/10 hard cases scored mean < 0.55 (need >= 6/10)" \
       --artifact INVESTIGATION_LOG.jsonl
  ```

- If **6 or more** of the 10 hard cases score mean < 0.55: hard-case ceiling check passes.

**Easy-stratum branch (determines calibration action, using the 5 easy pilot cases):**

| Easy baseline mean | Action |
|--------------------|--------|
| < 0.70 | **STOP — relabeling required.** Easy cases are failing too often. Audit and relabel: cases scoring < 0.55 may be mislabeled medium; cases scoring < 0.40 should be reviewed for schema errors. Present relabeling plan to LEAD before Phase 6. |
| 0.70 – 0.84 | **Proceed with calibration uncertainty noted.** Log the calibration gap and note it in Phase 8 CONCLUSIONS.md. |
| ≥ 0.85 | **Proceed as planned.** Gate passed. |

If all checks pass, log:
```bash
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat gate --action difficulty_preflight_passed \
     --detail "Pre-benchmark gate passed: 10 hard cases sampled by haiku-4-5 — N/10 scored mean < 0.55; easy stratum mean = X.XX" \
     --artifact INVESTIGATION_LOG.jsonl
```

```bash
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat workflow --action step_end \
  --detail "Phase 5.5 difficulty gate complete; outcome logged above"
```

**Stratum diagnostic (non-blocking — informational only):**
Report mean scores broken down by stratum:

| Stratum | N cases | N below 0.55 | Mean score |
|---|---|---|---|
| Pure critique | N | N | X.XX |
| Mixed | N | N | X.XX |
| Defense_wins | N | N | X.XX |

This table does not affect the gate decision. It identifies which stratum drives any gate failure and informs Phase 8 analysis planning.

```bash
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat gate \
  --action stratum_diagnostic \
  --detail "Stratum breakdown: critique mean=X.XX (N/N below 0.55); mixed mean=X.XX (N/N); defense_wins mean=X.XX (N/N)"
```

**Phase 5.5 commit:**
```bash
git add self_debate_experiment_v5/INVESTIGATION_LOG.jsonl
git commit -m "chore: snapshot v5 phase 5.5 artifacts — difficulty preflight gate result logged"
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat exec --action commit_phase_artifacts --detail "committed phase 5.5 artifacts: difficulty preflight gate outcome in INVESTIGATION_LOG.jsonl"
```

---
