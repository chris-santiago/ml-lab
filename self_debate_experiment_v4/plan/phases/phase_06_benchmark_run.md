## Phase 6 — Run the Benchmark

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

**Uses existing ml-critic and ml-defender agents directly — not inline prompts.**

> **Execution rules for Phase 6:**
> - All script invocations use `uv run`. Never `python` or `python3`.
> - Log entries use `uv run log_entry.py`. Never write JSONL manually.
> - Do not read `agents/` source files. Agents are dispatched by name only.
> - Do not pass must_find_issue_ids, scoring_targets, ground_truth, planted_issues, or any answer-key fields to agents in any condition.

```bash
mkdir -p v4_raw_outputs
uv run log_entry.py --step 6 --cat workflow --action step_start --detail "Phase 6: running benchmark — all cases, all applicable conditions, 3 runs each"
```

**Instruction:**

Load self_debate_experiment_v4/benchmark_cases_verified.json.

For EACH case, run 3 complete passes (run 1, run 2, run 3).
Within each pass, run all applicable conditions:

--- ISOLATED DEBATE CONDITION ---
Dispatch ml-critic with ONLY the case task_prompt. No other context.
Dispatch ml-defender with ONLY the case task_prompt.
Do NOT pass Critic output to Defender — isolation is deliberate and essential.
This is NOT the standard ml-lab debate protocol. Isolation enables genuine defense_wins
verdicts and tests whether role separation alone improves ML review quality.

As orchestrator, adjudicate:
- Assign typed verdict: critique_wins | defense_wins | empirical_test_agreed
- If empirical_test_agreed, specify canonical schema:
    condition: [what to test]
    supports_critique_if: [result confirming critique]
    supports_defense_if: [result exonerating work]
    ambiguous_if: [result that does not resolve the dispute]
- Extract issues_found: which scoring_targets.must_find_issue_ids appear in Critic output
- Extract all_issues_raised: all numbered issues in Critic output

Write v4_raw_outputs/{case_id}_isolated_debate_run{N}.json:
{
  "case_id": "...", "run": N, "condition": "isolated_debate",
  "critic_raw": "...", "defender_raw": "...", "adjudication_raw": "...",
  "verdict": "critique_wins | defense_wins | empirical_test_agreed",
  "issues_found": [...],
  "all_issues_raised": [...],
  "empirical_test": {"condition": "...", "supports_critique_if": "...",
                     "supports_defense_if": "...", "ambiguous_if": "..."} or null
}

--- MULTIROUND DEBATE CONDITION (ml-lab protocol) ---
Dispatch ml-critic with ONLY the case task_prompt.
Dispatch ml-defender with task_prompt AND Critic's output.
Alternate up to 4 rounds. Force-resolve remaining as empirical_test_required.
Track resolved/open points across rounds — pass only unresolved points to next round.
CRITICAL: Adjudicate from the debate transcript only. Do NOT reference ground_truth,
correct_position, must_find_issue_ids, planted_issues, or any answer-key field.
Write v4_raw_outputs/{case_id}_multiround_run{N}.json (same format + debate_rounds,
points_resolved, points_force_resolved, point_resolution_rate fields).

--- FORCED MULTIROUND CONDITION (hard cases only, 2-round minimum) ---
Only run on cases where difficulty == "hard".
Same as multiround but enforce at least 2 full exchange rounds even if all points
appeared resolved after round 1. After the mandatory second round, check convergence
and continue naturally up to 4 total rounds.
Write v4_raw_outputs/{case_id}_forced_multiround_run{N}.json (same format;
debate_rounds field must be >= 2).

For each forced_multiround case, the raw output JSON must include a `rounds` array:
[
  {"round": 1, "verdict": "<typed verdict after round 1>", "points_resolved": <int>, "points_open": <int>},
  {"round": 2, "verdict": "<typed verdict after round 2>", "points_resolved": <int>, "points_open": <int>}
]
A case is flagged as a "hollow forced round" if round 2 verdict == round 1 verdict AND round 2 points_resolved == 0 (no new resolutions in round 2).

--- ENSEMBLE CONDITION ---
Dispatch three independent assessors with ONLY the task_prompt. No role identity.
CRITICAL: Do NOT pass must_find_issue_ids, scoring_targets, ground_truth, planted_issues,
or any answer-key fields to ensemble assessors.
Synthesize with ETD output constraint (applied uniformly to produce comparable outputs,
but ETD will be scored N/A for ensemble per pre-registration):
"If issues are genuine but empirically resolvable, specify:
condition / supports_critique_if / supports_defense_if / ambiguous_if — all four required."
Write v4_raw_outputs/{case_id}_ensemble_run{N}.json.

--- BASELINE CONDITION ---
Single call with task_prompt only. No structure, no role.
Write v4_raw_outputs/{case_id}_baseline_run{N}.json.

After completing all runs for a case, log:
uv run log_entry.py --step 6 --cat exec --action case_complete --case_id {case_id}
  --detail "all applicable conditions, 3 runs each" --meta '{"difficulty": "..."}'

> **Script:** `plan/scripts/validate_raw_schema.py` — enforces the v4 raw output schema contract before scoring. For forced_multiround, validates both `debate_rounds` (int ≥ 2) and `rounds` (array ≥ 2 entries with `round`/`verdict`/`points_resolved`/`points_open`). The scoring engine (`self_debate_poc.py`) does not read these fields, so a mismatch is invisible to scoring but breaks Phase 10.5 audit checks. Run before isolation check and scoring.

```bash
uv run plan/scripts/validate_raw_schema.py
# Must pass (exit 0) before check_isolation.py or self_debate_poc.py
```

> **Script:** `plan/scripts/check_isolation.py` — scans isolated_debate and forced_multiround defender raw outputs for isolation breaches; checks if verbatim Critic language appears in Defender output. Raises SystemExit if breaches detected (results contaminated).

```bash
uv run plan/scripts/check_isolation.py
# Must pass before running self_debate_poc.py
```

**Isolation breach logging (if any breaches detected):**
```bash
# For each breach detected:
uv run log_entry.py --step 6 --cat decision --action isolation_breach_detected \
  --detail "Breach detected in {file}" --meta '{"matched_snippet": "...", "file_path": "..."}'
# Before each re-run:
uv run log_entry.py --step 6 --cat workflow --action rerun_triggered \
  --detail "Re-running {case_id} isolated_debate run{N} — breach replacement"
# After re-run completes:
uv run log_entry.py --step 6 --cat workflow --action rerun_complete \
  --detail "Re-run complete for {case_id} run{N}"
```

```bash
uv run log_entry.py --step 6 --cat exec --action validate_raw_schema --detail "validate_raw_schema.py passed — all raw output files conform to v4 schema contract" --artifact validate_raw_schema.py
uv run log_entry.py --step 6 --cat exec --action check_isolation --detail "check_isolation.py passed — no isolation breaches in isolated_debate runs" --artifact check_isolation.py
uv run log_entry.py --step 6 --cat workflow --action step_end --detail "Phase 6 complete: raw outputs collected, isolation check clean"
```

**Phase 6 commit (BEFORE scoring):**
```bash
git add self_debate_experiment_v4/v4_raw_outputs/
git commit -m "chore: snapshot v4 main benchmark raw outputs — <N> cases, isolation check <passed|failed>"
uv run log_entry.py --step 6 --cat exec --action commit_raw_outputs --detail "committed v4_raw_outputs/ after main benchmark; <N> cases; isolation check passed"
```

---
