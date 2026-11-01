# ml-journal trust list (issue #1, option 3): defended choice

Approved 2026-11-01. Origin: https://github.com/chris-santiago/ml-lab/issues/1 (option 3: auto-resume only in repos this machine has vouched for).

## 1. Reframe

- A hostile repo can already write instructions into its `CLAUDE.md`. What the SessionStart hook adds is framing: it presents repo text, unprompted, as "the latest state" of the user's own work. The fix gates that automatic path.
- `/log-list`, `/log-summarize`, and `/research-note` are explicit reads of repo data, like `cat`. Only SessionStart and `/resume` frame the checkpoint as the user's state.
- `${CLAUDE_PLUGIN_DATA}` is exported to hook processes but only text-substituted into skill content (it is not in the Bash tool's environment), so skills pass `--data-dir "${CLAUDE_PLUGIN_DATA}"` explicitly. The data dir is `~/.claude/plugins/data/<plugin>-<marketplace>/`, kept across updates, deleted on uninstall.

## 2. Change

- `journal_common.py`: `trust_key(root)` (realpath of `git rev-parse --git-common-dir`), `is_trusted(root, data_dir)`, `trust_repo(root, data_dir)` over `<data_dir>/trusted-repos.json` (atomic replace), `UNTRUSTED_EXIT = 3`, fixed `UNTRUSTED_NOTICE`. Missing data dir or malformed store means untrusted.
- `journal_query.py --latest-checkpoint --trusted-only --data-dir D`: when a checkpoint exists and the repo is untrusted, print the notice (never checkpoint text) and exit 3.
- `journal-session-start.sh`: passes `$CLAUDE_PLUGIN_DATA`; exit 3 becomes a fixed notice (suggest `/resume` to view once, `/log-init` to trust). Legacy note unchanged.
- `journal_setup.py`: `--data-dir`; `inspect` reports `trusted`; `init` trusts only when it created the journal; new `trust` subcommand.
- `/log-init`: new step for an existing, untrusted journal asks before trusting. `/resume`: uses `--trusted-only`; on exit 3 relays the notice and asks before showing text, then frames it as repo-supplied.
- Docs describing SessionStart updated; version 0.5.0.
- Untouched: PreCompact, other read skills, journal writes.

## 3. Cases

| Case | Today | Under the fix | Result |
|---|---|---|---|
| Trusted repo, checkpoint | injected | injected, same text | unchanged |
| Untrusted repo, hostile checkpoint | injected | fixed notice, no repo text | fixed |
| Untrusted repo, no checkpoint | silent | silent | unchanged |
| No journal / symlinked journal | silent | silent | unchanged |
| Legacy repo | checkpoint + upgrade note | upgrade note + (checkpoint if trusted, else notice) | changed |
| Worktree of a trusted repo | injected | injected (shared trust key) | unchanged |
| `CLAUDE_PLUGIN_DATA` unset | injected | notice (fail closed) | changed |
| `/resume`, trusted | shows checkpoint | same | unchanged |
| `/resume`, untrusted (hooks on or blocked) | shows text silently | notice, asks first | fixed |
| `/log-init`, new journal | creates | creates and trusts | changed |
| `/log-init`, existing or legacy journal | upgrades | upgrades, then asks to trust | changed |
| Existing repos after update | auto-resume | notice until one `/log-init` | changed (accepted cost) |
| Plugin uninstalled | n/a | data dir deleted, trust resets | fail closed |
| `/research-note`, `/log-list`, PreCompact | as today | as today | unchanged |

Completeness: grepped `--latest-checkpoint` (hook, `/resume`, `/research-note`, docs) and `SessionStart`/`session-start` across plugin, docs, slides, README; `hooks.json` has no other context producers. A miss would be another skill that auto-loads checkpoint text; `--recent` and `--entry` can show checkpoints only on explicit request, which is the scope decision above.

## 4. Why this choice

Mirrors the legacy-note strategy (detection in plugin Python, thin bash hook, the `/resume` path covering blocked hooks, as `warn_if_legacy` does). One trust function, two callers through one flag. Fails closed. Trust is an explicit act on this machine. Fits the CLAUDE.md rule: scripts decide, skills ask.

## 5. Rejected alternatives

- Bash `jq` check on the trust file: duplicates key logic in a second language; `/resume` cannot reuse it.
- Gate all journal reads by default: over-reach; explicit reads break in colleagues' repos and every skill needs `--data-dir`.
- Reuse Claude Code's folder-trust flag in `~/.claude.json`: undocumented, and accepted for every folder including hostile clones; it means "let Claude run here", not "this journal is mine".
- Key by top-level path: every worktree nags until re-trusted.
- Key by journal content (first entry hash): public journals are copyable, so an attacker could reuse a trusted head.
- Fixed path (`~/.config/ml-journal`) instead of `${CLAUDE_PLUGIN_DATA}`: stable across install identities, but survives uninstall, is not platform-managed, and could sync trust to machines that never granted it. Accepted con of the chosen store: a second install identity (`-inline` vs `-ml-lab`) asks again (fail closed).
- Trust on every `/log-init` without asking: the notice tells users to run `/log-init`, so it would become a one-step bypass; a hostile repo could ship legacy copies to bait an upgrade.

Follow-up (separable): `journal_setup.py untrust` and `trust --list`; the store is plain JSON until then.

## 6. Plan

Inline build on `fix/ml-journal-trust`. `python-coder` writes Python and tests (TDD); skills and docs edited in-thread; `python-review-lite`; RED proof of the regression test before staging; `/log-commit`; `verification-before-completion`; merge and close #1 with confirmation.
