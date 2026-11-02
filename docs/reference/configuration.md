# Configuration

## Environment variables

Set in `UV.env` at the repo root (gitignored, loaded automatically by `uv run`):

| Variable | Required for | Description |
|----------|-------------|-------------|
| `OPENROUTER_API_KEY` | External LLM calls | OpenRouter API key for synthetic case generation and experiment scripts |
| `CROSS_VENDOR_API_KEY` | Phase 9 cross-vendor scoring | API key for cross-vendor evaluation |
| `CROSS_VENDOR_BASE_URL` | Phase 9 cross-vendor scoring | Base URL for cross-vendor API |
| `CROSS_VENDOR_MODEL` | Phase 9 cross-vendor scoring | Model identifier for cross-vendor evaluation |

## Settings files

### .claude/settings.json

Project-level settings, committed to git. Shared across all contributors.

### .claude/settings.local.json

Per-machine settings, gitignored. Use for:

- API keys and secrets
- Hook configurations (paths vary per machine)
- Personal permission allow-rules

!!! warning
    Always prefer `settings.local.json` for hooks and secrets. Never write secrets to the git-tracked `settings.json`.

## Hooks

The ml-journal plugin registers its hooks itself in `plugins/ml-journal/hooks/hooks.json`, using `${CLAUDE_PLUGIN_ROOT}` so the paths resolve wherever the plugin is installed. The scripts live in `skills/log-init/hooks/`; a skills-only install (no plugin system) registers them in `~/.claude/settings.json` from `journal_setup.py hook-config` instead. This repo's development hooks (`sync-plugin-cache.sh` and `sync-to-chris-code.sh`) are machine-local: they are registered in the gitignored `.claude/settings.local.json`, and the scripts themselves are not tracked in git.

| Hook | Script | Registered by | Behavior |
|------|--------|---------------|----------|
| `PreCompact` | `journal-precompact.sh` | ml-journal plugin (skills-only: `~/.claude/settings.json`) | Auto-writes a checkpoint before `/compact` |
| `SessionStart` | `journal-session-start.sh` | ml-journal plugin (skills-only: `~/.claude/settings.json`) | Injects the latest checkpoint as session context, in repos this machine trusts |
| `PostToolUse` | `sync-plugin-cache.sh` | repo settings | Mirrors plugin edits to the installed plugin cache (`rsync --delete`) |
| `PostToolUse` | `sync-to-chris-code.sh` | repo settings | Mirrors plugin edits to the chris-code marketplace repo (`rsync --delete`) |

!!! warning
    With the plugin installed, do not also add the ml-journal hooks to a settings file. Plugin hooks run in addition to settings hooks, so a manual copy writes duplicate checkpoints. `/log-init` warns when it finds both.

## Plugin registration

The plugin manifest lives at `plugins/ml-lab/.claude-plugin/plugin.json`. Agents and skills are auto-discovered from their respective directories within the plugin.

## File layout

```
.claude/
├── settings.json           # project-level (committed)
├── settings.local.json     # per-machine (gitignored)
├── hooks/
│   └── sync-plugin-cache.sh
└── scheduled_tasks.lock

plugins/
├── ml-lab/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/             # auto-discovered
│   └── skills/             # auto-discovered
└── ml-journal/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── agents/
    ├── hooks/
    │   └── hooks.json      # auto-registered on install
    └── skills/
        └── log-init/
            ├── hooks/      # journal-hook-lib.sh, journal-precompact.sh, journal-session-start.sh
            └── scripts/    # journal_*.py, run by every skill and hook

UV.env                      # uv runtime env vars (gitignored)
```
