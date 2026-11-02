# Scripts & CLI

Scripts used by ml-lab and ml-journal. All are stdlib-only Python (no external dependencies beyond the standard library).

## journal_log.py

**Location:** `plugins/ml-journal/skills/log-init/scripts/journal_log.py`. The ml-journal scripts live only in the installed skills and are never copied into a repo; a repo holds data only (`.project-log/journal.jsonl`). Skills run them as `python3 -I "${CLAUDE_SKILL_DIR}/../log-init/scripts/<script>"` (`${CLAUDE_SKILL_DIR}/scripts/` from `/log-init`), which works for plugin and skills-only installs.

Entry writer. Validates fields against the type schema (rejecting fields not valid for the type), constructs the envelope (`id`, `timestamp`, `type`, `project`, `session_id`), and appends a single JSON line to `journal.jsonl`. Refuses a symlinked `.project-log/` or `journal.jsonl`.

**Usage:** Called by ml-journal skills internally.

!!! warning
    Use `/log-entry` (or another journal skill) for journal writes. Manual JSONL appends bypass schema validation. ml-lab's investigation log is separate: it uses `uv run log_entry.py`.

---

## journal_query.py

**Location:** `plugins/ml-journal/skills/log-init/scripts/journal_query.py`

Read-only query interface for the journal. From a shell, set `Q` to the installed copy (for a plugin, under the `installPath` for `ml-journal` in `~/.claude/plugins/installed_plugins.json`; for a skills-only install, `~/.claude/skills/log-init/scripts/journal_query.py`) and run it from anywhere inside the repo.

**Operations:**

```bash
Q="<installPath>/skills/log-init/scripts/journal_query.py"

# Journal health overview
python3 "$Q" --status

# List entries by type (with optional time filter)
python3 "$Q" --list <type> [--since <duration>]

# Unresolved issues
python3 "$Q" --unresolved-issues

# Resolved issues with linked resolutions
python3 "$Q" --resolved-issues

# Recent entries (with optional time filter)
python3 "$Q" --recent <N> [--since <duration>]

# Lookup by ID prefix
python3 "$Q" --entry <id_prefix>

# Latest checkpoint
python3 "$Q" --latest-checkpoint

# Latest checkpoint, only if this machine trusts the journal (exit 3 and a notice otherwise)
python3 "$Q" --latest-checkpoint --trusted-only
```

**Time durations:** `7d` (days), `4h` (hours), `30m` (minutes).

---

## journal_setup.py

**Location:** `plugins/ml-journal/skills/log-init/scripts/journal_setup.py`

Used by `/log-init`. The trust list is `~/.local/share/ml-journal/trusted-repos.json` (`$XDG_DATA_HOME/ml-journal/` instead when `XDG_DATA_HOME` is an absolute path), shared by plugin and skills-only installs; `--data-dir` overrides it. Subcommands: `inspect [--plugin-root R]` (JSON report of journal state, whether it is trusted, legacy script copies, managed `CLAUDE.md` sections, and how the hooks are registered: `hooks.plugin` from a non-empty plugin root, `hooks.settings` listing settings files that name the hook), `init` (creates `.project-log/journal.jsonl` if absent, never truncates, and trusts a journal it created), `trust` (trusts an existing journal on this machine), `upgrade [--dry-run]` (removes script copies left by older versions and rewrites stale managed `CLAUDE.md` sections; never touches the journal), `add-sections [--dry-run]` (appends absent managed sections from `skills/log-init/assets/claude-md-sections.md`), `hook-config` (prints the `settings.json` hooks block for a skills-only install, with absolute paths to this copy's hook scripts; needs no repo).

---

## log_entry.py

**Location:** Experiment directory root (e.g., `experiments/self_debate_experiment_v8/`)

Investigation log writer for ml-lab experiments. Appends sequenced entries to `INVESTIGATION_LOG.jsonl` with step numbers and timestamps.

**Usage:**

```bash
uv run log_entry.py --step <N> --type <type> --description "..."
```

---

## generate_figures.py

**Location:** Repository root

Generates publication-ready figures from experiment results using matplotlib. Uses PEP 723 inline metadata for dependency resolution.

**Usage:**

```bash
uv run generate_figures.py
```

---

## flow-lint.py

**Location:** `plugins/ml-lab/skills/pipeline-init/scripts/flow-lint.py` (shipped by `/pipeline-init`)

Deterministic static linter for promoted Metaflow flows. Uses PEP 723 inline metadata; stdlib `ast` only — no project dependencies, never imports the flow under test.

Detects five mechanical anti-patterns:

| Rule ID | What it detects |
|---|---|
| `merge-artifacts-module` | `merge_artifacts()` with no `include=`/`exclude=`; an unconstrained merge raises on `nn.Module`/tensor artifacts |
| `cwd-relative-config` | `Config(default=...)` not anchored to `__file__`; CWD-relative paths break under `uv run` script mode |
| `per-config-foreach` | `foreach=` attribute names a per-method/config list instead of the dataset/data-axis grain |
| `bare-project-import` | First-party import with no preceding module-scope `sys.path.insert(...)` shim |
| `module-global-experiment-const` | Module-level numeric constant read inside a `@step`/`@card` body; belongs in Hydra config |

Reports findings as `file:line  [rule-id]  message`. Exits nonzero on any finding.

**Usage:**

```bash
uv run flow-lint.py <flow.py> [<flow.py> ...]
```

!!! note
    The script path is resolved portably from the plugin registry (`installed_plugins.json` → `installPath`), matching the same pattern used by `derive_verdict.py`.

---

## determinism-check.py

**Location:** `plugins/ml-lab/skills/pipeline-init/scripts/determinism-check.py` (shipped by `/pipeline-init`)

Prove layer for promoted Metaflow flows. Verifies that a flow holds its declared `experiment.determinism` contract by diffing two runs' aggregate outputs (`lift_results`, `aggregate_results`) for exact equality, order-insensitive over cells. Uses PEP 723 inline metadata; requires `metaflow>=2.19`.

Reads the contract from `run.data.determinism`:

| Contract | Verification behavior |
|---|---|
| `order_independent` | Two runs (any `--max-workers`) must produce identical aggregate outputs |
| `single_worker` | Two runs both at `--max-workers 1` must produce identical outputs |
| `nondeterministic` | Verification skipped (escape hatch, exits 0) |

!!! warning
    This is not a reproduce-the-PoC check. It validates the promoted flow against itself across two runs — confirming that the pipeline's own declared contract holds.

**Usage:**

```bash
# Compare two specific runs
uv run determinism-check.py <run_a_pathspec> <run_b_pathspec>

# Compare the latest two runs of a named flow
uv run determinism-check.py --flow <FlowName>

# Override the contract (fallback when run artifact is absent)
uv run determinism-check.py <run_a> <run_b> --contract order_independent
```

---

## Hook scripts

### journal-precompact.sh

**Location:** `plugins/ml-journal/skills/log-init/hooks/journal-precompact.sh`

Auto-writes a checkpoint before `/compact` runs. Registered as a `PreCompact` hook by the plugin's `hooks/hooks.json`, or by hand from `journal_setup.py hook-config` in a skills-only install. Changed paths come from `git status --porcelain -z`, so renames record the new name and paths with spaces are kept whole.

### journal-session-start.sh

**Location:** `plugins/ml-journal/skills/log-init/hooks/journal-session-start.sh`

Injects the latest checkpoint as session context at session start, only for a journal this machine trusts; otherwise it emits a fixed notice with no checkpoint text. Registered as a `SessionStart` hook the same way. Emits `hookSpecificOutput.additionalContext`.

### sync-plugin-cache.sh

**Location:** `.claude/hooks/sync-plugin-cache.sh`

PostToolUse hook that auto-rsyncs edits in `plugins/ml-lab/` or `plugins/ml-journal/` to the versioned plugin cache. Fires on any file edit within the plugin directories.
