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
cp plugins/ml-lab/ml-critic.md ~/.claude/agents/
cp plugins/ml-lab/ml-defender.md ~/.claude/agents/
```

```bash
# Copy log_entry.py to experiment root for convenient invocation throughout all phases
cp self_debate_experiment_v5/plan/scripts/log_entry.py self_debate_experiment_v5/
```

---

## Plan-Specific Checks (always run)

> **Script:** `plan/scripts/log_entry.py` — structured INVESTIGATION_LOG.jsonl writer; enforces schema, auto-increments seq, validates cat taxonomy.

> **Script:** `plan/scripts/validate_cases.py` — validates case file schema, category distribution, must_find sizes, difficulty labels. Accepts `--lenient` to skip count assertions.

**Normalize pipeline output and write benchmark_cases.json** (ARCH-1 schema → experiment schema):

> `normalize_cases.py` maps the ARCH-1 flat schema to the nested schema expected by all
> downstream experiment scripts. It derives `difficulty` from `_pipeline.proxy_mean`,
> remaps `must_not_claim` to synthetic IDs, and maps `acceptable_resolutions` to verdict
> strings. Run this instead of a raw `cp` — the pipeline output schema is not directly
> compatible with `validate_cases.py` or `self_debate_poc.py`.

```bash
cd self_debate_experiment_v5 && uv run plan/scripts/normalize_cases.py \
  --input synthetic-candidates/selected_cases_all.json \
  --output benchmark_cases.json
```

**Validate normalized file (schema + composition assertions):**

```bash
cd self_debate_experiment_v5 && uv run plan/scripts/validate_cases.py benchmark_cases.json
# Must pass (>=60 cases, >=20 with 3+ must_find) before proceeding to Phase 1
# Note: mixed=0 is expected for ARCH-1 (binary verdicts only; assertion removed)
# Note: real-paper source_paper check uses is_real_paper_case flag set by normalize_cases.py
```

**Logging:**
```bash
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat workflow --action step_start --detail "Phase 0: setup complete, benchmark_cases copied from pipeline selected_cases_all.json, validate_cases passed"
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat exec --action validate_cases --detail "Pipeline-selected cases copied; composition validation passed" --artifact benchmark_cases.json
cd self_debate_experiment_v5 && uv run plan/scripts/log_entry.py --step 0 --cat workflow --action step_end --detail "Phase 0 complete"
```

**Phase 0 commit:**
```bash
git add self_debate_experiment_v5/log_entry.py \
        self_debate_experiment_v5/benchmark_cases.json
git commit -m "v5 Phase 0: log_entry.py, benchmark_cases from pipeline selected_cases_all.json"
```
