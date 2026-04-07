# Phase 0 — Setup and Case Validation

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

---

## Quick-start: Was preflight recently run?

Before running any Phase 0 steps, check whether `/preflight self_debate_experiment_v5` has already been run this session:

```bash
cd self_debate_experiment_v5 && grep -q '"action": "preflight_complete"' INVESTIGATION_LOG.jsonl 2>/dev/null \
  && echo "PREFLIGHT_FOUND: skip Infrastructure section" \
  || echo "PREFLIGHT_NOT_FOUND: run all steps"
```

- **PREFLIGHT_FOUND** → skip the **Infrastructure** section below and go directly to **Plan-Specific Checks**.
- **PREFLIGHT_NOT_FOUND** → run both sections in order.

---

## Infrastructure (skip if preflight passed)

> These steps are redundant if `/preflight` returned READY — preflight already verified agents are installed and that `benchmark_cases.json` exists.

```bash
# Install agents (invoked by name — source files not read during execution)
cp agents/ml-critic.md ~/.claude/agents/
cp agents/ml-defender.md ~/.claude/agents/
```

```bash
# Copy log_entry.py to experiment root for convenient invocation throughout all phases
cp self_debate_experiment_v5/plan/scripts/log_entry.py self_debate_experiment_v5/
```

---

## Plan-Specific Checks (always run)

> **Script:** `plan/scripts/log_entry.py` — structured INVESTIGATION_LOG.jsonl writer; enforces schema, auto-increments seq, validates cat taxonomy.

> **Script:** `plan/scripts/validate_cases.py` — validates case file schema, category distribution, must_find sizes, difficulty labels. Accepts `--lenient` to skip count assertions.

**Merge both source files into benchmark_cases.json** (idempotent — safe to re-run if preflight already created it):

```bash
cd self_debate_experiment_v5 && uv run python -c "
import json
with open('synthetic-candidates/openai_benchmark_cases.json') as f:
    main = json.load(f)
with open('synthetic-candidates/real_paper_cases.json') as f:
    supplement = json.load(f)
main_ids = {c['case_id'] for c in main}
supp_ids = {c['case_id'] for c in supplement}
overlap = main_ids & supp_ids
assert not overlap, f'Case ID collision: {overlap}'
merged = main + supplement
with open('benchmark_cases.json', 'w') as f:
    json.dump(merged, f, indent=2)
print(f'Merged {len(main)} + {len(supplement)} = {len(merged)} cases')
"
```

**Validate merged file (schema + composition assertions):**

```bash
cd self_debate_experiment_v5 && uv run plan/scripts/validate_cases.py benchmark_cases.json
# Must pass (>=60 cases, >=12 mixed, >=20 with 3+ must_find) before proceeding to Phase 1
# Also warns if any real-paper cases (eval_scenario_1xx) are missing source_paper field
```

**Logging:**
```bash
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat workflow --action step_start --detail "Phase 0: setup complete, benchmark_cases merged from 2 source files, validate_cases passed"
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat exec --action validate_cases --detail "Merged 50+14=64 cases; composition validation passed" --artifact benchmark_cases.json
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat workflow --action step_end --detail "Phase 0 complete"
```

**Phase 0 commit:**
```bash
git add self_debate_experiment_v5/log_entry.py \
        self_debate_experiment_v5/benchmark_cases.json
git commit -m "v5 Phase 0: log_entry.py, benchmark_cases merged (50 main + 14 real-paper = 64)"
```
