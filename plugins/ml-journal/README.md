# ml-journal

A persistent, structured audit trail for Claude Code sessions. Captures decisions, issues, discoveries, experiments, and session state in a machine-queryable, append-only JSONL log — survives compaction and session boundaries.

ml-journal is **standalone** and works in any git repo. It pairs naturally with the `ml-lab` plugin for hypothesis-driven experiments, but does not require it.

## Installation

```bash
# Install the plugin (once, user-scoped)
claude plugin install ml-journal@ml-debate-lab

# Initialize in any git repo (once per repo)
/log-init
```

`/log-init` creates `.project-log/` at the repo root, copies the query scripts, and writes a verification entry.

## Architecture

```
judgment layer     →  Claude skills (extract, classify, construct args)
mechanical layer   →  Python scripts (validate, serialize, write)
storage            →  .project-log/journal.jsonl (per-repo, append-only)
```

No background daemons. No external dependencies beyond `python3` and `git` (`jq` only needed for hooks).

## Typical Workflow

```
During a session:
  /log-entry          ← log decisions, issues, discoveries as they happen
  /log-commit         ← commit + log in one step

End of session:
  /checkpoint         ← snapshot current state for next session
  /research-note      ← generate a shareable note from today's work (optional)

Next session:
  /resume             ← reload checkpoint into context

Periodic:
  /log-summarize      ← prose synthesis of a specific entry type
  /log-status         ← quick overview of the journal state
  /research-report    ← full retrospective at end of phase or project
```

## Skills

| Skill | Description |
|---|---|
| `/log-init` | One-time repo setup — creates `.project-log/`, installs scripts, verifies with a test entry |
| `/log-entry` | Main logging path — infers entry type from conversation context, extracts fields, writes to journal |
| `/checkpoint` | Save session state for handoff to future sessions or post-compact recovery |
| `/resume` | Load and display the most recent checkpoint |
| `/log-status` | Quick overview — last checkpoint, entry counts, unresolved issues, recent commits |
| `/log-list` | List entries by type with optional time filter (`--since 7d`) |
| `/log-summarize` | Prose synthesis of all entries of a given type |
| `/log-commit` | Git commit + journal log in one step |
| `/research-note` | Generate a session or day-scoped formatted markdown note — shareable, PR-ready |
| `/research-report` | Synthesize `RESEARCH_REPORT.md` — dispatches `report-drafter` agent to read full journal + git history |

## Agents

| Agent | Dispatched by | Description |
|---|---|---|
| `report-drafter` | `/research-report` | Reads full journal, git history, and supplementary docs; synthesizes 9-section draft. Never writes files. |

## Entry Types

| Type | Required Fields | Confirm? | Weight |
|---|---|---|---|
| `issue` | description, severity¹ | No | Light |
| `resolution` | description | No | Light |
| `discovery` | description | No | Light |
| `hypothesis` | description | No | Light |
| `lesson` | description | No | Light |
| `decision` | description, rationale | Yes | Medium |
| `experiment` | description, verdict² | Yes | Medium |
| `summary` | description | Yes | Medium |
| `post_mortem` | description, what_failed, root_cause | Yes | Heavy |
| `checkpoint` | in_progress | Yes | Heavy |
| `git` | commit_hash, message, branch | Yes (via `/log-commit`) | — |

¹ `severity` must be one of: `low`, `moderate`, `high`, `critical`
² `verdict` must be one of: `confirmed`, `refuted`, `inconclusive`

Light entries are logged immediately. Medium and heavy entries show a draft and ask for confirmation before writing.

## Scripts

Both scripts are stdlib-only Python (no external dependencies). They are installed into `.project-log/` by `/log-init` and can be invoked directly.

- **`journal_log.py`** — Validates fields, constructs envelope (`id`, `timestamp`, `type`, `project`, `session_id`), appends entry to `journal.jsonl`
- **`journal_query.py`** — Read operations: `--status`, `--latest-checkpoint`, `--list TYPE [--since Nd]`, `--unresolved-issues`, `--entry ID_PREFIX`

The journal is a plain JSONL file — one JSON object per line. Query it directly without any skill:

```bash
# Show journal state
python3 .project-log/journal_query.py --status

# List decisions from the last week
python3 .project-log/journal_query.py --list decision --since 7d

# List all unresolved issues
python3 .project-log/journal_query.py --unresolved-issues

# Pipe to jq for custom queries
python3 .project-log/journal_query.py --list experiment | jq '.[] | {description, verdict}'
```

## Example Output

```
/log-status output:
  Last checkpoint: 2026-04-09 10:14 (3h ago) — in_progress: refining case scoring rubric
  Entries this session: 2 decisions, 1 experiment, 1 issue
  Unresolved issues: 1 [high]
  Recent commits: 3

/resume output:
  in_progress:         refining case scoring rubric
  pending_decisions:   whether to weight IDJ separately from must_find
  recently_completed:  Phase 7 cross-vendor scoring run
  open_threads:        baseline ceiling effect, rubric alignment with v4
```

## Hooks (Optional)

Two hook scripts enable automatic checkpoint/resume without manual invocation.

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

**Gotchas:**
- Hooks are per-machine — `.claude/settings.local.json` is gitignored and does not sync to teammates. Each developer must configure separately.
- `SessionStart` only injects a checkpoint if one exists. The first session in a new repo will see no injection.
- If your Claude Code environment does not permit hooks, use skills explicitly instead (`/checkpoint` before `/compact`, `/resume` at session start).

## Troubleshooting

**"No journal found. Run `/log-init` first."** — Run `/log-init` in the repo root. The `.project-log/` directory does not yet exist.

**Entries seem missing** — Check that `.project-log/journal.jsonl` is committed and not listed in `.gitignore`. The journal should be tracked, not ignored.

**`journal_query.py` skips a line with a warning** — A journal entry is malformed (e.g., manually edited). Malformed lines are skipped; all other entries remain accessible. Inspect with `grep -n "^{" .project-log/journal.jsonl | tail -20` to find the bad line.

**Hooks don't fire** — Confirm your Claude Code environment supports hooks and that `.claude/settings.local.json` exists on the current machine with the correct paths.

## Files

```
plugins/ml-journal/
  .claude-plugin/
    plugin.json                   # plugin manifest
  skills/
    log-init/
      SKILL.md
      scripts/
        journal_log.py            # bundled copy — installed into .project-log/ on /log-init
        journal_query.py
    log-entry/SKILL.md
    checkpoint/SKILL.md
    resume/SKILL.md
    log-status/SKILL.md
    log-list/SKILL.md
    log-summarize/SKILL.md
    log-commit/SKILL.md
    research-note/SKILL.md
    research-report/SKILL.md
  report-drafter.md               # agent — drafts RESEARCH_REPORT.md (dispatched by /research-report)
  journal_log.py                  # top-level copy (used at runtime from .project-log/)
  journal_query.py
  journal-precompact.sh           # optional PreCompact hook
  journal-session-start.sh        # optional SessionStart hook
  journal_system_spec.md          # internal system specification
```
