# Installation & Prerequisites

This tutorial walks you through installing ml-lab and ml-journal, configuring environment variables, and verifying everything works. By the end, you'll have both plugins ready to use.

## Prerequisites

- **Claude Code** — installed and authenticated ([installation guide](https://docs.anthropic.com/en/docs/claude-code/overview))
- **uv** — Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** — required for ml-journal's audit trail

!!! note "No pyproject.toml needed"
    ml-lab scripts use PEP 723 inline metadata headers. `uv run` resolves dependencies per-script — no virtual environment or project-level dependency file required.

## Install ml-lab

```shell
/plugin marketplace add chris-santiago/ml-lab
/plugin install ml-lab@ml-lab
```

This installs the `/ml-lab` skill and all seven subagent files. Verify by typing `/ml-lab` — Claude Code should recognize it as a skill.

## Install ml-journal

```shell
/plugin install ml-journal@ml-lab
```

Then initialize the journal in your repo:

```shell
/log-init
```

This creates `.project-log/` at the repo root with `journal.jsonl`, `journal_log.py`, and `journal_query.py`.

## Set up environment variables

ml-lab's experiment scripts call external LLMs through OpenRouter. Create a `UV.env` file at the repo root (gitignored by default):

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

`uv run` loads `UV.env` automatically — no manual `export` needed.

For cross-vendor scoring (used in some experiment configurations), you'll also need:

```
CROSS_VENDOR_API_KEY=your-key
CROSS_VENDOR_BASE_URL=https://api.example.com/v1
CROSS_VENDOR_MODEL=model-name
```

## Verify the installation

Run each of these to confirm everything is wired up:

```shell
# ml-lab skill is available
/ml-lab

# ml-journal skills are available
/log-status

# uv can resolve PEP 723 scripts
uv run --help
```

You should see `/ml-lab` prompt for a hypothesis and `/log-status` show journal state (it runs the plugin's query script, so this also confirms the scripts work).

## Hooks

ml-journal auto-checkpoints before context compaction and auto-resumes at session start. The plugin registers both hooks on install (`plugins/ml-journal/hooks/hooks.json`), so there is nothing to configure. They stay inactive in any repo until you run `/log-init` there, and SessionStart loads a checkpoint only from a journal `/log-init` has trusted on this machine (it trusts the journals it creates, and asks about existing ones). If your organization blocks hooks, they won't run, but every skill still works: use `/checkpoint` before `/compact` and `/resume` at session start.

!!! warning
    If you previously added ml-journal hooks to `.claude/settings.local.json` by hand, remove them. Plugin hooks run in addition to settings hooks, so keeping both writes duplicate checkpoints.

## You have now...

- Installed ml-lab and ml-journal as Claude Code plugins
- Configured API keys for external LLM calls
- Initialized the journal audit trail
- Picked up the auto-checkpoint/resume hooks that ship with ml-journal

Next: [Worked Example: LLM Preambles](worked-example.md) — walk through a complete real-world investigation.
