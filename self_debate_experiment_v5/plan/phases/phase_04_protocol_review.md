## Phase 4 — Protocol Self-Review: CRITIQUE + DEFENSE + DEBATE + EXECUTION_PLAN

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

Before running the benchmark, run the debate protocol against its own design.

> **Execution rules for Phase 4:** Use `uv run log_entry.py` for all log entries. Agents are dispatched by name. Do not read `agents/` source files.

```bash
uv run log_entry.py --step 4 --cat workflow --action step_start --detail "Phase 4: protocol self-review — CRITIQUE, DEFENSE, DEBATE, EXECUTION_PLAN, README"
```

**Instruction:**

Run the self-debate protocol against the v5 experimental design.

Step 1 — Dispatch ml-critic (Mode 1, initial critique):
Provide: HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json
Produce: CRITIQUE.md — numbered issues, each with: the claim being made /
why it might be wrong / what evidence would settle it. Organized by root cause.

Step 2 — Dispatch ml-defender (Mode 1, initial defense):
Provide: HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json, AND CRITIQUE.md
Use two-pass structure: Pass 1 full analysis, Pass 2 verdict selection.
Produce: DEFENSE.md

Step 3 — DYNAMIC GATE CONSTRUCTION (v5 required step, Issue 19 fix):
After receiving DEFENSE.md, before proceeding:

  a. Read the Defender's overall verdict from the Pass 2 section of DEFENSE.md.
  b. Parse the Pass 2 verdict table. Extract every row with verdict "Concede" or
     "Rebut (partial concede)".
  c. Extract every pre-execution requirement stated by the Defender — items flagged
     as "must be confirmed before execution", "must appear in the experiment plan",
     or equivalent phrasing.
  d. Compile all extracted items into a pre-flight checklist to be included in
     EXECUTION_PLAN.md. Format:

     | # | Source | Item | Verification Method | Status |
     |---|--------|------|---------------------|--------|
     | 1 | DEFENSE.md Issue N (Concede) | [exact item] | [how to verify] | PENDING |

  e. Log: uv run log_entry.py --step 4 --cat gate --action phase4_preflight_constructed
     --detail "Pre-flight checklist constructed from Defender verdict"
     --meta '{"checklist_item_count": N, "overall_verdict": "..."}'

  This checklist is dynamically constructed from the actual review output.
  Do not use a pre-written checklist.

Step 4 — Initialize DEBATE.md with all contested points from CRITIQUE.md vs DEFENSE.md.

Step 5 — Alternate ml-critic (Mode 2) and ml-defender (Mode 2) on DEBATE.md until all
points resolve. Maximum 4 rounds. Force-resolve remaining as empirical_test_required.

Step 6 — Write EXECUTION_PLAN.md:
  - Pre-flight checklist (from Step 3 above) as the FIRST section
  - Five conditions and their configurations
  - Pre-specified verdict criteria for all hypotheses
  - Complete artifact plan
  - Failure handling

Step 7 — Write README.md:
  - One-paragraph hypothesis statement (5 conditions)
  - Quickstart: uv run plan/scripts/self_debate_poc.py
  - Pipeline description
  - Expected outputs
  - Scope exclusions

Step 8 — GATE: Present EXECUTION_PLAN.md to LEAD for approval.
Do NOT proceed to Phase 5 until:
  1. Every pre-flight checklist item is marked CLOSED in EXECUTION_PLAN.md
  2. LEAD explicitly approves

The Defender's verdict is the experiment's own quality check. The checklist reflects
the actual review findings. A static pre-written checklist cannot substitute for
reading the Defender's actual output.

**After gate approval:**
```bash
uv run log_entry.py --step 4 --cat subagent --action dispatch_ml_critic --detail "ml-critic dispatched for Phase 4 self-critique" --artifact CRITIQUE.md
uv run log_entry.py --step 4 --cat write --action write_critique --detail "CRITIQUE.md written" --artifact CRITIQUE.md
uv run log_entry.py --step 4 --cat subagent --action dispatch_ml_defender --detail "ml-defender dispatched for Phase 4 self-defense" --artifact DEFENSE.md
uv run log_entry.py --step 4 --cat write --action write_defense --detail "DEFENSE.md written" --artifact DEFENSE.md
uv run log_entry.py --step 4 --cat write --action write_debate --detail "DEBATE.md initialized with contested points" --artifact DEBATE.md
uv run log_entry.py --step 4 --cat write --action write_execution_plan --detail "EXECUTION_PLAN.md written with dynamic preflight checklist" --artifact EXECUTION_PLAN.md
uv run log_entry.py --step 4 --cat write --action write_readme --detail "README.md written" --artifact README.md
uv run log_entry.py --step 4 --cat gate --action phase4_cleared --detail "EXECUTION_PLAN approved, all preflight items closed" --meta '{"items_closed": N}'
uv run log_entry.py --step 4 --cat workflow --action step_end --detail "Phase 4 complete"
git add self_debate_experiment_v5/CRITIQUE.md self_debate_experiment_v5/DEFENSE.md \
        self_debate_experiment_v5/DEBATE.md self_debate_experiment_v5/EXECUTION_PLAN.md \
        self_debate_experiment_v5/README.md
git commit -m "v5 Phase 4: protocol self-review complete, EXECUTION_PLAN approved"
```

---
