## Phase 6.5 — External Benchmark Evaluation

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

Runs all applicable conditions on `external_cases_v4.json`. External case IDs distinct from main benchmark — outputs go to same `v4_raw_outputs/` without collision.

```bash
uv run log_entry.py --step 6.5 --cat workflow --action step_start --detail "Phase 6.5: external benchmark evaluation — all applicable conditions, 3 runs each"
```

**Instruction:**

Load self_debate_experiment_v4/external_cases_v4.json.

For EACH case, run 3 complete passes, all applicable conditions, using the
identical protocol from Phase 6:
- isolated_debate, multiround, ensemble, baseline: all cases
- forced_multiround: hard external cases only (difficulty == "hard")

Write outputs to v4_raw_outputs/{case_id}_{condition}_run{N}.json.
After completing all cases, run isolation check on external isolated_debate outputs.

```bash
uv run plan/scripts/validate_raw_schema.py
# Must pass (exit 0) before check_isolation.py or self_debate_poc.py
uv run plan/scripts/check_isolation.py  # scans all isolated_debate outputs including ext_*

uv run plan/scripts/self_debate_poc.py \
  --cases external_cases_v4.json \
  --output v4_external_results.json
```

**Logging:**
```bash
uv run log_entry.py --step 6.5 --cat exec --action validate_raw_schema_external --detail "validate_raw_schema.py passed on all outputs including external — schema contract met"
uv run log_entry.py --step 6.5 --cat exec --action check_isolation_external --detail "check_isolation.py passed on external outputs — no isolation breaches"
uv run log_entry.py --step 6.5 --cat exec --action score_external --detail "self_debate_poc.py run on external_cases_v4.json" --artifact v4_external_results.json
uv run log_entry.py --step 6.5 --cat workflow --action step_end --detail "Phase 6.5 complete: external raw outputs collected, isolation check clean"
```

**Phase 6.5 commit:**
```bash
git add self_debate_experiment_v4/v4_raw_outputs/
git commit -m "chore: snapshot v4 external benchmark raw outputs — <N> external cases"
uv run log_entry.py --step 6.5 --cat exec --action commit_external_raw_outputs --detail "committed v4_raw_outputs/ external cases; <N> cases"
```

---
