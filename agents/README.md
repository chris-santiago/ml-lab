# Agent Definitions

This directory contains reference copies of the Claude Code agents that power the ml-debate-lab investigation workflow.

## Agents

| File | Role | Spawned by |
|------|------|------------|
| `ml-lab.md` | Orchestrator — runs the full 12-step investigation | User / calling agent |
| `ml-critic.md` | Adversarial critic — finds flaws the PoC hasn't tested | `ml-lab` (Steps 3, 5) |
| `ml-defender.md` | Design defender — argues for the implementation, concedes valid points | `ml-lab` (Steps 4, 5) |
| `research-reviewer.md` | Deep peer reviewer — Opus-class structured review of REPORT.md | `ml-lab` (Step 10, Round 1) |
| `research-reviewer-lite.md` | Verification reviewer — Haiku-class follow-up review | `ml-lab` (Step 10, Rounds 2–3) |
| `readme-rewriter.md` | Outside-reader README rewriter — diagnoses and rewrites for external audiences | `ml-lab` (Step 13) |

All agents except `ml-lab` are subagents. They are never invoked directly — `ml-lab` dispatches them at the appropriate steps via the Claude Code Agent tool.

## Installing

**Via plugin (recommended):**

```shell
/plugin marketplace add chris-santiago/ml-debate-lab
/plugin install claude-ml-lab@ml-debate-lab
```

This installs all six agent files to `~/.claude/agents/` automatically.

**Manual install:**

```bash
cp agents/ml-lab.md ~/.claude/agents/
cp agents/ml-critic.md ~/.claude/agents/
cp agents/ml-defender.md ~/.claude/agents/
cp agents/research-reviewer.md ~/.claude/agents/
cp agents/research-reviewer-lite.md ~/.claude/agents/
cp agents/readme-rewriter.md ~/.claude/agents/
```

Once installed, Claude Code will make `ml-lab` available as a spawnable agent. Invoke it by describing an ML hypothesis — it will ask you to sharpen it into a falsifiable claim before starting the investigation.

## What these copies are

These are sanitized reference copies. Two changes were made from the originals before committing here:

1. **Memory path generalized** — the original references a hardcoded user home directory path for agent memory. The reference copy uses `~/.claude/agent-memory/ml-lab/` so it works for any installer.
2. **`memory: user` scope removed** — the original grants the agent access to the global user memory system. The reference copy removes this, scoping the agent to its own memory directory only. Add `memory: user` back to your local copy if you want cross-project memory access.

## How the agents interact

```
User hypothesis
      |
   [ml-lab]  ←——————————————— orchestrates all 12 core steps
      |
      +——— Steps 1-2:   builds PoC, reviews intent
      |
      +——— Step 3:      dispatches [ml-critic]          → CRITIQUE.md
      |
      +——— Step 4:      dispatches [ml-defender]        → DEFENSE.md
      |
      +——— Step 5:      alternates dispatches until contested points resolve → DEBATE.md
      |
      +——— Steps 6-7:   designs and runs experiment, synthesizes conclusions
      |
      +——— Macro-iteration: if results surprise, re-dispatches ml-critic and ml-defender
      |    in evidence-informed mode (Mode 3) with experimental results in hand
      |
      +——— Steps 8-9:   writes self-contained report, re-evaluates under production constraints
      |
      +——— Step 10:     dispatches [research-reviewer]      → PEER_REVIEW_R1.md  (Round 1, Opus)
      |                 dispatches [research-reviewer-lite] → PEER_REVIEW_R{N}.md (Rounds 2–3, Haiku)
      |
      +——— Step 11:     (optional) writes TECHNICAL_REPORT.md in results mode
      |
      +——— Step 12:     artifact coherence audit — cross-checks all documents for consistency
      |
      +——— Step 13:     (optional) dispatches [readme-rewriter] → rewrites README.md
```

The key architectural constraint is **context isolation**: `ml-critic` and `ml-defender` each receive only the task materials — never each other's output — before producing their independent assessments. The Defender's independence is what makes genuine `defense_wins` verdicts possible on false-positive critique cases.
