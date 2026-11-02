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

This creates `.project-log/journal.jsonl` at the repo root. The repo holds data only; the journal scripts run from the installed skills.

If your organization blocks plugin installs but allows skills, copy the skill folders instead: see "Without the plugin system" in `plugins/ml-journal/README.md`.

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

You should see `/ml-lab` prompt for a hypothesis and `/log-status` show journal state (it runs the installed query script, so this also confirms the scripts work).

## Hooks

ml-journal auto-checkpoints before context compaction and auto-resumes at session start. The plugin registers both hooks on install (`plugins/ml-journal/hooks/hooks.json`), so there is nothing to configure. A skills-only install registers them by hand from `journal_setup.py hook-config`. They stay inactive in any repo until you run `/log-init` there, and SessionStart loads a checkpoint only from a journal `/log-init` has trusted on this machine (it trusts the journals it creates, and asks about existing ones). If your organization blocks hooks, they won't run, but every skill still works: use `/checkpoint` before `/compact` and `/resume` at session start.

!!! warning
    If you added ml-journal hooks to a settings file by hand (in an older setup, or from `hook-config` for a skills-only install), remove them when you install the plugin. Plugin hooks run in addition to settings hooks, so keeping both writes duplicate checkpoints. `/log-init` warns when it finds both.

## You have now...

- Installed ml-lab and ml-journal as Claude Code plugins
- Configured API keys for external LLM calls
- Initialized the journal audit trail
- Picked up the auto-checkpoint/resume hooks that ship with ml-journal

Next: [Worked Example: LLM Preambles](worked-example.md) — walk through a complete real-world investigation.
