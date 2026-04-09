# ml-journal

A persistent, structured audit trail for Claude Code sessions. Captures decisions, issues, discoveries, experiments, and session state in a machine-queryable, append-only JSONL log.

## Architecture

```
judgment layer     →  Claude skills (extract, classify, construct args)
mechanical layer   →  Python scripts (validate, serialize, write)
storage            →  .project-log/journal.jsonl (per-repo, append-only)
```

No background daemons. No external dependencies beyond `python3`, `git`, and `jq` (hooks only).

## Skills

| Skill | Description |
|---|---|
| `/log-init` | One-time repo setup — creates `.project-log/`, installs scripts, verifies with a test entry |
| `/log-entry` | Main logging path — infers entry type from conversation context, extracts fields, writes to journal |
| `/checkpoint` | Save session state for handoff to future sessions or post-compact recovery |
| `/resume` | Load and display the most recent checkpoint |
| `/log-status` | Quick overview — last checkpoint, entry counts, unresolved issues, recent commits |
| `/log-list` | List entries by type with optional time filter (`--since 7d`) |
| `/log-summarize` | Prose synthesis of entries by type |
| `/log-commit` | Git commit + journal log in one step |
| `/research-note` | Generate a session or day-scoped formatted markdown note — shareable, PR-ready |
| `/research-report` | Synthesize `RESEARCH_REPORT.md` — full research report from journal, git history, and supplementary docs |

## Entry Types

| Type | Required Fields | Confirm? |
|---|---|---|
| `issue` | description, severity | No |
| `resolution` | description | No |
| `decision` | description, rationale | Yes |
| `discovery` | description | No |
| `hypothesis` | description | No |
| `experiment` | description, verdict | Yes |
| `lesson` | description | No |
| `post_mortem` | description, what_failed, root_cause | Yes |
| `summary` | description | Yes |
| `checkpoint` | in_progress | Yes |
| `git` | commit_hash, message, branch | Yes (via `/journal-commit`) |

## Scripts

Both scripts are stdlib-only Python (no external dependencies).

- **`journal_log.py`** — Validates fields, constructs envelope (id, timestamp, type, project, session_id), appends entry to `journal.jsonl`
- **`journal_query.py`** — Read operations: `--status`, `--latest-checkpoint`, `--list TYPE [--since]`, `--unresolved-issues`, `--entry ID_PREFIX`

## Setup

```bash
# In any git repo with the plugin installed:
/journal-init
```

This creates `.project-log/` in the repo root, copies the scripts, and writes a verification entry.

## Hooks (Optional)

Two hook scripts are included for automatic checkpoint/resume behavior. These are **not registered by default** — install only if your environment permits hooks.

| Hook | Script | Behavior |
|---|---|---|
| PreCompact | `journal-precompact.sh` | Auto-writes a checkpoint before `/compact` |
| SessionStart | `journal-session-start.sh` | Injects latest checkpoint as session context |

To enable, add to `.claude/settings.local.json` (per-machine, gitignored):

```json
{
  "hooks": {
    "PreCompact": [{ "type": "command", "command": "bash plugins/ml-journal/journal-precompact.sh" }],
    "SessionStart": [{ "type": "command", "command": "bash plugins/ml-journal/journal-session-start.sh" }]
  }
}
```

## Files

```
plugins/ml-journal/
  journal_system_spec.md      # full system specification
  all_skills.md               # all 10 skill definitions (source for SKILL.md split)
  journal_log.py              # entry writer
  journal_query.py            # entry reader / querier
  journal-precompact.sh       # optional PreCompact hook
  journal-session-start.sh    # optional SessionStart hook
```
