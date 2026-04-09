## Phase 6.5 — External Benchmark Evaluation

> **⚠ SKIP FOR V5 RUN — `external_cases_v5.json` was never created. Decision logged: journal issue bfe958a1 / decision 9723bed9. External benchmark deferred to a future experiment. Proceed directly to Phase 6.75.**

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

Runs all applicable conditions on `external_cases_v5.json`. External case IDs distinct from main benchmark — outputs go to same `v5_raw_outputs/` without collision.

```bash
uv run log_entry.py --step 6.5 --cat workflow --action step_start --detail "Phase 6.5: external benchmark evaluation — all applicable conditions, 3 runs each"
```

**Instruction:**

Load `self_debate_experiment_v5/external_cases_v5.json`.

**CRITICAL DISPATCH RULE:** For every agent dispatch, read `case['task_prompt']` directly from the loaded JSON object. Do NOT reconstruct, paraphrase, or hardcode task prompts from memory or prior context.

For EACH case, run 3 complete passes, all applicable conditions, using the
identical protocol from Phase 6 (including POST-WRITE VALIDATION on every output file):
- isolated_debate, multiround, ensemble, baseline: all cases
- forced_multiround: hard external cases only (difficulty == "hard")

Write outputs to v5_raw_outputs/{case_id}_{condition}_run{N}.json.
After completing all cases, run isolation check on external isolated_debate outputs.

```bash
uv run plan/scripts/validate_raw_schema.py
# Must pass (exit 0) before check_isolation.py or self_debate_poc.py
uv run plan/scripts/check_isolation.py  # scans all isolated_debate outputs including ext_*

uv run plan/scripts/self_debate_poc.py \
  --cases external_cases_v5.json \
  --output v5_external_results.json
```

**Logging:**
```bash
uv run log_entry.py --step 6.5 --cat exec --action validate_raw_schema_external --detail "validate_raw_schema.py passed on all outputs including external — schema contract met"
uv run log_entry.py --step 6.5 --cat exec --action check_isolation_external --detail "check_isolation.py passed on external outputs — no isolation breaches"
uv run log_entry.py --step 6.5 --cat exec --action score_external --detail "self_debate_poc.py run on external_cases_v5.json" --artifact v5_external_results.json
uv run log_entry.py --step 6.5 --cat workflow --action step_end --detail "Phase 6.5 complete: external raw outputs collected, isolation check clean"
```

**Phase 6.5 commit:**
```bash
git add self_debate_experiment_v5/v5_raw_outputs/
git commit -m "chore: snapshot v5 external benchmark raw outputs — <N> external cases"
uv run log_entry.py --step 6.5 --cat exec --action commit_external_raw_outputs --detail "committed v5_raw_outputs/ external cases; <N> cases"
```

---
