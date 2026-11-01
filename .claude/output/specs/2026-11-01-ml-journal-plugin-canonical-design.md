# ml-journal Plugin-Canonical Execution Design Spec

Intent ledger: `.claude/output/intent/2026-11-01-ml-journal-plugin-canonical-intent.md`

## 1. Scope

`plugins/ml-journal` is the single source of journal code. Every skill and hook runs the plugin's bundled `journal_log.py` / `journal_query.py`; a repo holds only data (`.project-log/journal.jsonl`). `/log-init` initializes new repos with data only and upgrades repos set up under the old copy-scripts layout. The ml-lab repo is upgraded like any other consumer. Ships with the hook fixes already on `fix/ml-journal-hooks` as plugin version 0.4.0.

## 2. Goals

- No ml-journal skill, hook, or managed `CLAUDE.md` text invokes a script under a repo's `.project-log/`.
- One copy of each journal script exists, in the plugin; it includes the field validation that currently exists only in ml-lab's copy (commit 782506d).
- The scripts refuse to read or write through a symlinked `.project-log/` or `journal.jsonl`, for every caller.
- Already-initialized repos are told they need upgrading and are upgraded by `/log-init` without touching journal data.
- A test prevents reintroducing repo-local script invocation.

## 3. Non-goals

- Changing the journal entry schema or `git_state` format (comma-joined paths stay).
- Framing/sanitizing injected checkpoint text against prompt injection.
- Supporting installs without the plugin (skills copied into `~/.claude/skills/`). That mode is dropped from the docs.
- Shell-level human use of the scripts. Humans may run the plugin's scripts by path; no repo-local convenience copy is kept.

## 4. System behavior

**Skills.** Every journal read/write runs the plugin script via `${CLAUDE_PLUGIN_ROOT}`. Behavior and output of each skill are otherwise unchanged.

**Hooks.** Locate the plugin scripts relative to their own file (as today). SessionStart additionally detects the legacy layout and adds one line to the injected context telling the user to run `/log-init` to upgrade. This line is emitted even when no checkpoint exists. Detection only checks for file existence; it never executes or reads the legacy files.

**`/log-init`, fresh repo** (no `.project-log/journal.jsonl`): creates `.project-log/` and an empty `journal.jsonl`, writes a verification entry via the plugin script, offers the managed `CLAUDE.md` sections. No scripts are copied.

**`/log-init`, initialized repo:**
- Legacy layout present → shows what it will change (including a diff of any `CLAUDE.md` rewrite), then on confirmation: deletes the legacy script copies; replaces each managed `CLAUDE.md` section that invokes `.project-log/` scripts with the current template; reports (does not edit) any other `CLAUDE.md` line that invokes them. Managed sections that differ from the template but do not invoke legacy scripts are user customizations and are left alone. `journal.jsonl` is never modified, moved, or rewritten. A symlinked `CLAUDE.md` is never read or written, wherever it points (it is reported and skipped); the copies are still removed. (Amended 2026-11-01 after review: a resolve-inside check missed case-variant `.GIT/` links and links into the journal.)
- Already current → reports "journal already initialized and current" and changes nothing.
- Running it again after an upgrade is a no-op.

**Symlink refusal.** If `.project-log/` or `.project-log/journal.jsonl` is a symlink, both scripts exit non-zero with an error naming the path and write nothing. Hooks stay silent (exit 0) in that case, as they already do for any script failure.

## 5. Architecture

| Unit | Responsibility |
|---|---|
| `journal_log.py`, `journal_query.py` (plugin) | Only journal code. Resolve the journal from the cwd's git root; enforce symlink refusal; validate and append / query. |
| Skills | Judgment: decide what to log/query, build arguments, call the plugin scripts. |
| Hooks + `journal-hook-lib.sh` | Repo detection, cheap "journal exists" gate, legacy-layout detection, call plugin scripts. No safety logic of their own beyond refusing to run repo code. |
| `/log-init` | Initialize (data only) or upgrade legacy layout. The `CLAUDE.md` section replacement is deterministic and lives in a script, not in prompt prose. |
| Relapse test | Scans plugin skills, agents, hooks, scripts, README, and spec for repo-local script invocation. |

## 6. Canonical interfaces / data contracts

**Script invocation (skills).**
```
python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/log-init/scripts/journal_log.py"   <existing flags>
python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/log-init/scripts/journal_query.py" <existing flags>
```
CLI flags and output formats of both scripts are unchanged, except that `journal_log.py` rejects fields not valid for the entry type (782506d behavior: non-zero exit, message listing valid fields).

**Legacy layout.** A repo is legacy iff `.project-log/journal_log.py` or `.project-log/journal_query.py` exists (regular file or symlink).

**Managed `CLAUDE.md` sections.** Identified by exact headings: `## Journal — Consultation Before Planning`, `## Journal — Committing`, `## Journal — Proactive Logging`. A section runs from its heading to the next `## ` heading or EOF. Upgrade replaces each present managed section with the current template text; absent sections are not added during upgrade (they remain an opt-in offer). The template references skills (`/log-status`, `/log-list`, `/log-entry`, `/log-commit`), never scripts.

**Forbidden pattern (relapse test).** Any invocation of a repo-local journal script: a `.project-log/journal_<name>.py` path appearing as a command to run (e.g. after `python3`, or as `<repo-root>/.project-log/journal_*.py` in a command). Mentions as data (legacy detection, deletion targets) are allowed.

## 7. Invariants and constraints

- Journal data is never modified by upgrade; entries are append-only as before.
- No code under a repo's working tree is executed by any ml-journal skill or hook.
- Scripts stay stdlib-only, Python ≥ 3.10, and work under `python3 -I`. They may import plugin-local sibling modules (one shared path/symlink helper) by adding their own directory to `sys.path`; nothing is ever imported from the repo. (Amended 2026-11-01 with user approval: avoids three drifting copies of the safety logic.)
- Hooks never exit non-zero (PreCompact exit 2 would block compaction).
- Upgrade is idempotent and previewed before any write or delete.

## 8. Key decisions and tradeoffs

- **`${CLAUDE_PLUGIN_ROOT}` over a plugin `bin/`.** Proven in this plugin already; works on every surface. `bin/` would block claude.ai/Cowork installs and adds names to PATH.
- **No repo-local copies at all (not hash-checked copies).** Checking a copy still executes repo code and keeps two copies to drift; removing them removes the cause.
- **Symlink refusal lives in the scripts.** Single point every caller passes through; skills previously had no guard. Hook-level duplicate check is removed.
- **`/log-init` is also the upgrade command.** One command brings any repo to current; no separate `/log-upgrade`.
- **SessionStart nudges legacy repos.** The user runs ml-journal across several work repos; a passive nudge ensures each gets upgraded without tracking which ones are done.
- **Managed `CLAUDE.md` text points at skills.** `CLAUDE.md` is not plugin content, so `${CLAUDE_PLUGIN_ROOT}` is unavailable there; skills are also the intended judgment layer.
- **ml-lab gets no special treatment.** It is upgraded through `/log-init` like any consumer; its unique validation is ported into the plugin first so nothing is lost.

## 9. Acceptance criteria

1. No skill, agent, hook, script docstring, README, or plugin spec invokes `.project-log/journal_*.py`; the relapse test enforces it and fails on a planted violation.
2. `journal_log.py` (plugin) rejects a field not valid for the entry type, as 782506d did.
3. Both scripts refuse a symlinked `.project-log/` and a symlinked `journal.jsonl` (read and write), leaving the symlink target unchanged; hooks stay silent in that case.
4. Fresh `/log-init` leaves exactly `.project-log/journal.jsonl` (plus the verification entry) and no scripts.
5. On a legacy repo: SessionStart context contains the upgrade line (with and without a checkpoint); after `/log-init` upgrade, copies are gone, managed sections match the template, unmanaged script references are reported, and `journal.jsonl` is byte-identical before and after (upgrade writes no entries).
6. Upgrade run twice: second run changes nothing.
7. ml-lab repo after upgrade: no `.project-log/*.py`, its `CLAUDE.md` journal sections reference skills, and skills/hooks work end-to-end through the installed plugin.
8. Existing hook tests (19) still pass; `claude plugin validate` passes.

## 10. Validation strategy

- Script-level tests for field validation and symlink refusal (read and write paths), run against the plugin copies.
- Section-replacement logic tested deterministically: section present/absent, at EOF, followed by another heading, already-current (no-op), unmanaged script references reported.
- Hook tests extended for legacy-layout notice and to confirm no repo file is executed.
- Relapse test with a positive control (planted violation fails) and the real tree passing.
- End-to-end: a headless Claude session with `--plugin-dir` in a scratch legacy repo receives the upgrade notice; the ml-lab repo is upgraded via `/log-init` and a `/checkpoint` → `/resume` round trip works.
