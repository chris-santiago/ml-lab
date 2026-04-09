# Project Logging System — Implementation Plan

## Context

We need a persistent, structured audit trail that captures everything across a project: conversations, code changes, discovered issues, fixes, and decisions. The key constraint: **no Claude Code hooks** (org policy — invisible execution is a supply chain risk). Instead we use two complementary paths:

1. **Explicit logging** — Claude invokes a Python script when told to log something (via skills)
2. **Automatic git logging** — A macOS launchd daemon polls for new commits and logs them without instruction

Both paths write to a single **`.project-log/journal.jsonl`** file — machine-queryable, append-only, no concurrency risk.

---

## Files to Create

### 1. `.project-log/journal_log.py` — Core logging script

PEP 723 inline script (run via `uv run`). Accepts structured entries and appends to `journal.jsonl`.

**Interface:**
```bash
uv run .project-log/journal_log.py \
  --type issue \
  --description "14/15 smoke test failures with all-GPT lineup" \
  --severity high \
  --tags "pipeline,smoke-test" \
  --context "Stage 3 recycling fixed 10/14"
```

**Entry types and type-specific fields:**

| Type | Fields |
|---|---|
| `issue` | description, severity (low/moderate/high/critical), context, tags |
| `resolution` | description, linked_issue_id, approach |
| `summary` | description, key_decisions (list), open_threads (list) |
| `git` | commit_hash, message, branch, diff_summary, files_changed |
| `decision` | description, rationale, alternatives_considered |
| `discovery` | description, implications, source |

**Common envelope (all types):**
```json
{
  "id": "uuid4",
  "timestamp": "ISO8601",
  "type": "issue|resolution|summary|git|decision|discovery",
  "project": "<repo-name>",
  "session_id": null,
  ...type-specific fields
}
```

Auto-generates: `id`, `timestamp`, `project` (from repo directory name). Validates required fields per type. Appends single line to `.project-log/journal.jsonl`.

### 2. `.project-log/git_daemon.py` — Git commit watcher

PEP 723 inline script. Polls `git log` every 30 seconds, detects commits newer than the last logged `git`-type entry, and appends `git` entries via `journal_log.py`.

**Logic:**
- Read `.project-log/journal.jsonl`, find latest `git`-type entry's `commit_hash`
- Run `git log --format=json` for commits after that hash
- For each new commit: extract hash, message, branch, diff stat, files changed
- Call `journal_log.py` to append each as a `git`-type entry
- Sleep 30 seconds, repeat

**Designed for launchd:** runs as a long-lived process, handles SIGTERM cleanly.

### 3. `~/Library/LaunchAgents/com.user.project-journal-<repo>.plist` — launchd config

macOS launch agent that keeps `git_daemon.py` running.

```xml
<key>ProgramArguments</key>
<array>
  <string>/path/to/uv</string>
  <string>run</string>
  <string>/path/to/.project-log/git_daemon.py</string>
</array>
<key>WorkingDirectory</key>
<string>/path/to/repo</string>
<key>KeepAlive</key>
<true/>
<key>StandardOutPath</key>
<string>/path/to/.project-log/daemon.log</string>
<key>StandardErrorPath</key>
<string>/path/to/.project-log/daemon.log</string>
```

Will need a setup script or skill to generate this with the correct paths for the current repo.

### 4. `~/.claude/skills/journal-entry/SKILL.md` — Explicit logging skill

User-invocable. When user says "log this issue" / "log this fix" / "record this decision" / `/journal-entry`, Claude:

1. Finds repo root via `git rev-parse --show-toplevel`
2. Determines entry type from conversation context (issue, resolution, summary, decision, discovery)
3. Extracts relevant fields from the conversation
4. Runs `uv run .project-log/journal_log.py --type <type> --description "..." ...`
5. Confirms: "Logged [type] entry to journal.jsonl"

For `summary` type (session-level): also reads `git log` since last summary entry and any recent journal entries to synthesize a session overview.

**No confirmation step for routine entries** — logging should be low-friction. Show what was logged after the fact.

### 5. `~/.claude/skills/research-note/SKILL.md` — Narrative synthesis skill

User-invocable. When user says `/research-note` or "synthesize a research narrative":

1. Finds repo root
2. Reads `.project-log/journal.jsonl` in full
3. Reads `git log --oneline` for commit timeline
4. Discovers supplementary .md files (issue trackers, lessons, post-mortems) via glob patterns — no hardcoded paths
5. Synthesizes into `RESEARCH_NARRATIVE.md` at repo root with sections:
   - Problem Statement
   - Timeline (from journal entries, chronological)
   - What Was Tried / What Failed / What Worked
   - Key Decisions (from `decision`-type entries)
   - Issues and Resolutions (linked pairs)
   - Current State
   - Open Questions
6. Shows draft, confirms before writing

### 6. `.project-log/.gitignore`

```
daemon.log
```

Keep `journal.jsonl` and scripts tracked in git; ignore daemon logs.

---

## File to Modify

### 7. `.gitignore` (repo root)

Add `.project-log/daemon.log` pattern if not covered by existing `*.log` rule.
Check existing rules — ml-debate-lab already has `*.log` in gitignore so this may already be covered.

---

## Implementation Order

1. **Create `.project-log/` directory and `journal_log.py`** — the core writer. Test with manual invocations.
2. **Create `journal-entry` skill** — wires Claude to the logging script.
3. **Create `research-note` skill** — reads journal, produces narrative.
4. **Create `git_daemon.py`** — the commit watcher. Test by running manually.
5. **Create launchd plist + setup script** — makes the daemon persistent.
6. **Test end-to-end:** log a few entries via skill, make a commit, verify daemon captures it, run `/research-note`.

---

## Dependencies

- `uv` — all scripts use PEP 723 inline headers
- `jq` — not needed (Python handles all JSON)
- `git` — repo detection and commit monitoring
- `launchd` — macOS only; Linux equivalent would be systemd user service

---

## Portability Notes

- All scripts use `git rev-parse --show-toplevel` — no hardcoded paths
- Skills are user-level (`~/.claude/skills/`) — work in any repo
- `.project-log/` directory is per-repo — each project gets its own journal
- launchd plist is per-repo — one daemon per active project
- `journal_log.py` schema is project-agnostic; `project` field is auto-derived from repo name
- The `session_id` field is nullable — set by the skill when invoked from Claude, null for daemon entries

---

## Verification

1. `uv run .project-log/journal_log.py --type issue --description "test entry" --severity low` → verify line appended to `journal.jsonl`
2. `uv run .project-log/journal_log.py --type git --commit-hash abc123 --message "test" --branch main` → verify git entry
3. Run `git_daemon.py` manually, make a commit, verify auto-logged within 30s
4. Invoke `/journal-entry` in Claude, say "log this as an issue: test" → verify entry
5. Invoke `/research-note` after several entries → verify narrative output
6. `launchctl load ~/Library/LaunchAgents/com.user.project-journal-*.plist` → verify daemon starts and survives restart
