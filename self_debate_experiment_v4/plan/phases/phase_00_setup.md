# Phase 0 — Setup and Case Validation

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

```bash
mkdir -p self_debate_experiment_v4
cd self_debate_experiment_v4

# Install agents (invoked by name — source files not read during execution)
cp ../agents/ml-critic.md ~/.claude/agents/
cp ../agents/ml-defender.md ~/.claude/agents/
```

```bash
# Copy log_entry.py to experiment root for convenient invocation throughout all phases
cp plan/scripts/log_entry.py .
```

Initialize the investigation log and create `log_entry.py`:

> **Script:** `plan/scripts/log_entry.py` — structured INVESTIGATION_LOG.jsonl writer; enforces schema, auto-increments seq, validates cat taxonomy.

> **Script:** `plan/scripts/validate_cases.py` — validates benchmark_cases.json schema, category distribution, must_find sizes, difficulty labels.

```bash
uv run plan/scripts/validate_cases.py
uv run plan/scripts/validate_cases.py external_cases_v4.json
# Both must pass before proceeding to Phase 1
```

**Logging:**
```bash
uv run log_entry.py --step 0 --cat workflow --action step_start --detail "Phase 0: setup, log_entry.py created, validate_cases.py ready"
# After validate_cases.py passes:
uv run log_entry.py --step 0 --cat exec --action validate_cases --detail "Validation passed" --artifact benchmark_cases.json
uv run log_entry.py --step 0 --cat workflow --action step_end --detail "Phase 0 complete"
```

**Phase 0 commit:**
```bash
git add self_debate_experiment_v4/log_entry.py self_debate_experiment_v4/validate_cases.py \
        self_debate_experiment_v4/benchmark_cases.json
git commit -m "v4 Phase 0: log_entry.py, validate_cases, benchmark_cases"
```
