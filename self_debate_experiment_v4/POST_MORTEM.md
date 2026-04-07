# v4 Experiment Post-Mortem

Issues identified during and after execution of the v4 experiment plan. Each issue is scoped to whether it affected current results (active) or should be fixed in a future run (future fix).

---

## Issue 1 — Preflight Skill Bash Commands Use Relative Paths, Breaking When CWD Is Repo Root

**Scope:** Future fix
**Severity:** Moderate

### What Happened

The `/preflight` skill issued Bash tool calls using relative paths (e.g., `for f in plan/phases/*.md`) that assumed the working directory was `self_debate_experiment_v4/`. In practice the Bash tool's CWD is the repo root (`ml-debate-lab/`), so globs found no matches. When a bash glob expands to nothing, the loop variable receives the literal unexpanded pattern string rather than being skipped, causing downstream commands (`grep`, `awk`) to attempt to open that literal string as a filename and exit non-zero. Because parallel Bash tool calls share a failure-propagation model, the first failing call caused all remaining parallel calls in the same message to be cancelled, requiring multiple debug rounds before the root cause was identified.

### Root Cause

Bash glob patterns do not silently no-op when unmatched — by default the unexpanded pattern string is passed to the loop body as-is. Combined with the assumption that the Bash tool's CWD matches the experiment directory (it does not; it is always the repo root), every relative-path glob in the preflight checks silently misfired. The failure cascaded because parallel tool calls in a single message are cancelled when any one call exits non-zero.

### Impact

Preflight execution stalled repeatedly, producing misleading failures that appeared to be logic errors in the checks themselves. Multiple debug rounds were required to identify the CWD mismatch as the true cause. Experimental results were not affected.

### What to Fix

All path references in the `/preflight` skill should use absolute paths (constructed from a known repo-root anchor, e.g., `REPO="$(git rev-parse --show-toplevel)"`) or begin each Bash call with an explicit `cd` into the experiment root before any glob or file operation. Additionally, checks that are likely to fail independently should not be issued as parallel Bash tool calls; sequential calls should be used so that one failing check does not cascade-cancel unrelated checks.

---

## Issue 2 — CASE_VERIFIER Output Schema Unspecified, Causing TypeError and Silent Filter Failure

**Scope:** Active — Phase 1 has not yet run; without the fix the script will crash on first execution
**Severity:** High

### What Happened

`filter_verified_cases.py` was written with two concrete assumptions about the schema of `benchmark_verification.json`:

1. Line 10 reads `json.load(f)['cases']` — assumes the file is a dict with a `cases` key containing the list of entries.
2. Line 13 checks `.get('verdict') == 'keep'` — assumes each entry has a field named `verdict`.

The Phase 1 agent prompt (`plan/phases/phase_01_case_verifier.md`) tells the CASE_VERIFIER to "Write benchmark_verification.json" and to "Assign keep | revise | reject", but specifies no output schema. Without explicit field-name guidance, an LLM will plausibly write a flat JSON array (no wrapper dict) and use `decision` rather than `verdict` as the field name — neither of which the script expects.

### Root Cause

The CASE_VERIFIER prompt is underspecified. It describes what to decide but not what schema to write. The script was written with an explicit expected schema, but the prompt was never updated to mandate that schema, creating a silent contract between script and agent that the agent has no way to honour reliably.

### Impact

Two failure modes, each blocking all downstream phases:

- **Mismatch 1** (`cases` key absent): `json.load(f)['cases']` on a bare list raises `TypeError: list indices must be integers or slices, not str`. Phase 1 crashes immediately after CASE_VERIFIER writes its output.
- **Mismatch 2** (`verdict` vs `decision`): If mismatch 1 is patched manually, `.get('verdict')` on entries that use `decision` always returns `None`. No cases pass the filter, and `filter_verified_cases.py` raises `SystemExit('Insufficient cases')` even when CASE_VERIFIER marked 50 cases as `keep`.

Because Phase 1 is a mandatory gate, either failure prevents any experiment agent from seeing a single case.

### What to Fix

Update `plan/phases/phase_01_case_verifier.md` to append an explicit output schema block to the CASE_VERIFIER prompt. The block should specify:

- Top-level structure: `{ "cases": [...] }` — a dict with a single `cases` key whose value is the array of entries.
- Per-entry required fields: `case_id` (string), `verdict` (one of `"keep"`, `"revise"`, or `"reject"`), `notes` (string).

No change is needed in `filter_verified_cases.py` — its expected schema is correct. The fix is solely in the agent prompt.

---

## Issue 3 — Security Prompt for Newline-Containing Quoted Arguments Requires Manual Approval on Every Invocation

**Scope:** Future fix
**Severity:** Moderate

### What Happened

Any Bash tool call whose quoted argument contains a `#` character following a newline — or any heredoc-style block — triggers a Claude Code security prompt: "Newline followed by # inside a quoted argument can hide arguments from path validation." There is no per-pattern allow rule in the experiment's `.claude/settings.json`, so each occurrence requires the operator to stop and manually approve the prompt before execution continues. In the v4 workflow, `log_entry.py` is invoked at every phase boundary (step_start, exec, write, and step_end entries), and several of those invocations pass `--detail` or `--meta` arguments that can cross the newline-`#` threshold. Heredoc-style commit message blocks in the phase files trigger the same check. Across a complete multi-phase run this produces dozens of sequential approval prompts.

### Root Cause

Claude Code's path-validation security layer flags any quoted argument that contains a newline followed by a `#`, because that pattern can be used to smuggle hidden arguments past naive path checks. The check fires at the tool-call level and has no built-in exemption for known-safe command prefixes. Without a corresponding `allow` rule in `settings.json`, every matching invocation is paused for operator review regardless of how routine the command is. The v4 logging convention (frequent `log_entry.py` calls, multi-line `--detail` arguments, and heredoc commit messages) produces a high density of commands that match the pattern.

### Impact

Execution is not blocked — the operator can approve each prompt and the command runs correctly. However, the approval requirement breaks the hands-off phase flow that the v4 plan targets. A full run generates enough prompts that the workflow effectively requires the operator to sit at the terminal for its entire duration, defeating a primary design goal of reducing manual supervision. Operator fatigue also increases the chance of an accidental denial interrupting a phase mid-execution.

### What to Fix

**There is no allow rule that suppresses this warning.** The check is a hard-coded pre-permission security heuristic in Claude Code that runs before `permissions.allow` is evaluated — no `settings.json` pattern can bypass it.

The primary trigger in v4 is heredoc-style commit messages used in every phase commit block:

```bash
# Triggers the warning:
git commit -m "$(cat <<'EOF'
chore: snapshot artifacts [none]
EOF
)"
```

**Workaround:** Replace all heredoc commit blocks in the phase files with plain single-line `-m` arguments. Most v4 commit messages are already single-line; wrapping them in a heredoc adds no value and is the sole cause of the warning:

```bash
# No warning:
git commit -m "chore: snapshot artifacts [none]"
```

This applies to all `git commit` blocks in `plan/phases/phase_0*.md` through `plan/phases/phase_11_final.md`. The `log_entry.py` `--detail` arguments that cross the newline-`#` threshold are a secondary trigger and can be addressed by keeping detail strings on a single line.
