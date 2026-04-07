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

---

## Issue 4 — `log_entry.py` Not Found During Phase 5.5 — CWD Is Repo Root, Not Experiment Root

**Scope:** Active — error fired during Phase 5.5 of the running experiment
**Severity:** High

### What Happened

Phase 5.5 invoked `uv run log_entry.py` and received `error: Failed to spawn: log_entry.py — No such file or directory (os error 2)`. Phase 0 copies `log_entry.py` to `self_debate_experiment_v4/`, but the Bash tool's CWD is `ml-debate-lab/` (the repo root), so `uv run log_entry.py` cannot find the script.

### Root Cause

Same underlying cause as Issue 1 — phase files assume the Bash tool's CWD is the experiment root; it is always the repo root. This is the runtime manifestation of that assumption applied to `log_entry.py` invocations, which appear at every phase boundary across all phases.

### Impact

Any phase that calls `uv run log_entry.py` without a path prefix fails with exit code 2. The phase step itself may continue, but the log entry is not written, leaving a gap in `INVESTIGATION_LOG.jsonl` for that action. Gaps accumulate across phases and undermine the audit trail the logging system is designed to provide.

### What to Fix

**Immediate workaround (running experiment):** Prefix each `log_entry.py` call with the experiment-root path:

```bash
uv run self_debate_experiment_v4/log_entry.py --step 5.5 --cat workflow --action step_start --detail "Phase 5.5: ..."
```

**Permanent fix:** All `log_entry.py` invocations in phase files should be updated to use a repo-root-relative path (`self_debate_experiment_v4/log_entry.py`) or be preceded by `cd self_debate_experiment_v4 &&`. This is the same fix direction as Issue 1 — a single pass updating all phase files to use absolute or repo-root-relative paths would resolve both issues simultaneously.

---

---

## Issue 5 — Phase 5.5 Difficulty Gate Failed: Hard Cases Score 1.0 Across All Dimensions

**Scope:** Active — Phase 6 cannot proceed; operator re-sourcing cases via external LLM
**Severity:** Critical

### What Happened

The Phase 5.5 pre-benchmark difficulty gate sampled up to 10 hard cases and ran a single-pass baseline evaluation on each. Every case scored 1.0/1.0/1.0 (IDR/IDP/FVC) — all must_find issues surfaced, no must_not_claim items triggered, and the correct verdict reached in every case. The gate threshold requires that at least 4 of 10 hard cases produce a mean score ≤ 0.55; the results were far above this bar, causing the gate to halt execution before Phase 6.

### Root Cause

Closed-loop evaluation. The pilot agent running the difficulty check is the same model family (Claude) that generated the scoring rubric and that will execute all benchmark conditions. Cases that are appropriately difficult for a human analyst or average model are straightforward for the model that has implicitly internalized the rubric structure and flaw-detection patterns used during case generation.

### Impact

Phase 6 is blocked. The current benchmark_cases.json cannot proceed to full experimental evaluation without revision or replacement. The gate functioned correctly — it caught a validity problem before any debate protocol resources were committed.

### What to Fix

Three options were available per the plan:

1. **Revise cases** — strengthen planted flaws so they require more domain expertise to surface; add more plausible-but-false red herrings
2. **Re-source cases** — have the external LLM (non-Anthropic) generate harder cases using a more adversarial generation prompt
3. **Revise gate threshold** — if cases are genuinely hard for the intended population and the gate is miscalibrated for the model doing the pilot

**Resolution chosen: Option 2** — re-source cases via external LLM with a revised generation prompt targeting stronger difficulty calibration. New cases must pass Phase 1 (CASE_VERIFIER) and Phase 5.5 (difficulty gate) before Phase 6 can proceed.

**External LLM output — 10 revised hard cases:**

| Case ID | Category | Revision Strategy |
|---------|----------|-------------------|
| eval_scenario_007 | broken_baseline | Recast as clinical informatics quarterly review. Endpoint change buried as "harmonization," patient overlap hidden in encounter-level split description, timestamp change in a pipeline spec section |
| eval_scenario_008 | broken_baseline | Recast as retention experiment readout. Objective shift buried in "evolving business case" narrative, DR fitting issue in methods section, cutoff tuning in deployment config |
| eval_scenario_009 | broken_baseline | Recast as fraud ops migration readiness assessment. Dispute exclusion presented as "label maturation," feed mismatch in infrastructure upgrade section, threshold tuning in deployment |
| eval_scenario_013 | metric_mismatch | Recast as ADAS perception milestone review. mAP-vs-safety gap requires connecting nighttime headline to per-frame evaluation protocol in different paragraphs |
| eval_scenario_016 | metric_mismatch | Recast as recommendation launch proposal. Offline-online correlation transferability hidden by citing historical precedent from a different launch type |
| eval_scenario_017 | metric_mismatch | Recast as hospital AI governance vendor review. F1-vs-report-quality gap split between executive summary and technical appendix sections |
| eval_scenario_025 | hidden_confounding | Recast as procurement vendor selection memo. Weather regime mismatch hidden in date ranges, outage improvement presented as good news |
| eval_scenario_026 | hidden_confounding | Recast as product analytics pilot retrospective. Self-selection hidden in "opted into" language, seasonal confound in timeline details |
| eval_scenario_027 | hidden_confounding | Recast as internal audit annual performance report. Year-end seasonality presented positively as "Q4 outperformance," dual-approval as separate governance improvement |
| eval_scenario_032 | scope_intent | Recast as product council deployment proposal. Training scope in one paragraph, deployment scope in another; second-issuer check adds genuine defense evidence |

**Key techniques applied across all revised cases:**
- Confident memo tone — every case opens with a recommendation or positive headline, not a problem statement
- Multi-paragraph flaw distribution — must-find issues require connecting details from separate sections
- Surface soundness signals — CIs, power analyses, temporal cutoffs, external validation sets make cases look rigorous
- Genuinely tempting red herrings — 3-4 must_not_claim items embedded naturally per case (e.g., Hospital B sample size, PR-AUC for fraud, IPW propensity clipping, κ=0.71 inter-rater agreement)
- Defense evidence for mixed cases — external validation, directional A/B results, stakeholder endorsements

**Expected difficulty profile:**
- **IDR < 1.0** — Flaws require connecting information across paragraphs; a first-pass reader scanning each section as internally sound will miss cross-paragraph dependencies
- **IDP < 1.0** — Red herrings embedded naturally as scenario features make false-positive critiques more likely
- **DRQ failure on mixed cases** — Genuine defense evidence makes critique_wins feel too strong, but the flaws make defense_wins wrong; correct empirical_test_agreed requires recognizing both sides

---

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
