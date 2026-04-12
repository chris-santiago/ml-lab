# Agent Definitions

This directory contains reference copies of the Claude Code agents and skills that power the ml-lab investigation workflow.

## Agents

| File | Role | Spawned by |
|------|------|------------|
| `ml-lab.md` | Orchestrator — runs the full 12-step investigation | User / calling agent |
| `ml-critic.md` | Adversarial critic — finds flaws the PoC hasn't tested | `ml-lab` (Step 3: 3× in ensemble mode, 1× in debate; Step 5: debate only) |
| `ml-defender.md` | Design defender — argues for the implementation, concedes valid points | `ml-lab` (Steps 4, 5 — **debate mode only**) |
| `research-reviewer.md` | Deep peer reviewer — Opus-class structured review of REPORT.md | `ml-lab` (Step 10, Round 1) |
| `research-reviewer-lite.md` | Verification reviewer — Haiku-class follow-up review | `ml-lab` (Step 10, Rounds 2–3) |
| `readme-rewriter.md` | Outside-reader README rewriter — diagnoses and rewrites for external audiences | `ml-lab` (Step 13) |
| `intent-monitor.md` | Pre-registration drift monitor — evaluates git changes in an experiment directory against binding constraints in a source-of-truth document; emits a clean-pass line or structured conflict report | `intent-watch` skill (user-invoked) |

All agents except `ml-lab` are subagents dispatched via the Agent tool. In **ensemble mode** (the default), `ml-defender` is not dispatched — the review phase runs 3 independent `ml-critic` dispatches with union pooling. In **debate mode**, the full critic → defender → rounds chain runs as before.

For installation instructions, invocation guide, workflow diagram, and agent interaction overview, see the [root README](../README.md#install).

## Skills

Skills are user-invocable slash commands that live in `skills/<name>/SKILL.md`.

| Skill | Invocation | Applicable to |
|-------|-----------|---------------|
| `intent-watch` | `/intent-watch <experiment_dir> <source_of_truth>` | Active experiment phases where a pre-registration document (e.g. `HYPOTHESIS.md`) is the binding reference. Run ad-hoc or via `/loop` for continuous monitoring during Phase 4–7 execution. Not useful before a source-of-truth document exists or after the experiment is complete. |

## What these copies are

These are sanitized reference copies. Two changes were made from the originals before committing here:

1. **Memory path generalized** — the original references a hardcoded user home directory path for agent memory. The reference copy uses `~/.claude/agent-memory/ml-lab/` so it works for any installer.
2. **`memory: user` scope removed** — the original grants the agent access to the global user memory system. The reference copy removes this, scoping the agent to its own memory directory only. Add `memory: user` back to your local copy if you want cross-project memory access.
