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

## Issue 6 — Difficulty Gate Cannot Be Calibrated by Switching LLM Evaluators: Cases Remain Self-Annotating

**Scope:** Future fix — gate was waived by LEAD; experiment proceeds with documented caveat
**Severity:** Moderate

### What Happened

After the initial Phase 5.5 gate failure (Issue 5), the operator re-sourced 10 hard cases via an external LLM using the v1 generation prompt. The revised cases were re-verified (Phase 1 re-run) and the gate was re-run first with a Sonnet-class evaluator (9/9 cases scored 1.0), then with `claude-haiku-4-5` as a weaker proxy evaluator. Haiku also scored 1.0 on all 9 cases. The gate failed under both evaluators.

### Root Cause

The fundamental issue is not model capability — it is prompt design. The revised cases still describe flaws explicitly or strongly hint at them within the same paragraph that introduces the problematic design choice. A reviewer of any capability level who reads the document carefully will find the flaw because it is named. The v1 generation prompt produced "self-annotating" cases: memos that describe problems rather than documents that contain problems. Switching to a weaker evaluator cannot compensate for cases where the signal-to-noise ratio is 1.0 by construction.

### Impact

The difficulty gate as designed is not a reliable quality check for LLM-based benchmark evaluation. It correctly identified that the cases were too easy, but the available remediation paths (case revision, evaluator swap) both failed. The gate was waived by LEAD and the experiment proceeds with the caveat that the "hard" difficulty label is calibrated for human analysts, not Claude-family models. Difficulty-stratified lift results should be interpreted accordingly.

### What to Fix

The case generation prompt must be redesigned from scratch to produce cases where the flaw is not nameable from the text. `CASE_GENERATION_PROMPT_V2.md` (written during this phase) documents the required design principles:

- Flaw mechanism never named in the prompt text — described as a neutral design choice
- Multi-paragraph cross-referencing required to identify each must_find issue
- Active red herrings embedded as natural scenario features (not just listed in must_not_claim)
- Confident opening narrative that makes the evaluation appear sound

The gate evaluator model is secondary — if the cases are correctly designed, even a strong model will miss flaws. If the cases are self-annotating, no weaker model will reliably fail them.

### How to Use CASE_GENERATION_PROMPT_V2.md

This prompt is for **hard cases only** — easy and medium cases from v1 are not affected by the self-annotating issue.

**Steps:**
1. Open your external LLM (non-Anthropic, e.g. OpenAI GPT-4o or similar)
2. Paste the full contents of `synthetic-candidates/CASE_GENERATION_PROMPT_V2.md` as the system/instruction prompt
3. Provide `hard_cases_for_revision.json` as input — either ask for revisions to these 10 cases, or ask for N new hard cases from scratch using the same domains/categories
4. Request output as a JSON array matching the schema in the prompt
5. Run Phase 1 (CASE_VERIFIER) on the new cases to verify schema and check 12 (difficulty label)
6. Run Phase 5.5 with `claude-haiku-4-5` as evaluator — acceptance criterion is ≤ 4 of 10 hard cases score mean ≥ 0.55

**External LLM output — 10 v2 hard cases (generated with GPT-5.4, written from scratch following v2 design guide):**

**Key changes from v1:** v1 cases failed because flaws were directly named or strongly implied within individual paragraphs. v2 enforces a fundamentally different information architecture — every must_find issue requires connecting details from two separate paragraphs; neither paragraph alone reveals the flaw.

Cross-paragraph inference structure:

| Case | Flaw | Paragraph A | Paragraph B | What reader must infer |
|------|------|-------------|-------------|------------------------|
| 007 | Endpoint changed | P2: "24-hour deterioration prediction" | P3: "vasopressor initiation within 12-hour window" | Different clinical targets being compared |
| 007 | Timestamp mismatch | P2: "EHR-charted lab timestamps" | P4: "indexed to specimen collection time" | Different timestamping = different feature values |
| 007 | Patient overlap | P2: "recurring admissions" | P4: "random at encounter level" | Encounter-level split + recurring patients = leakage |
| 009 | Label exclusion | P2: "including pending and settled disputes" | P3: "restricted to settled dispute outcomes" | Removing hard cases flatters the challenger |
| 027 | Model-influenced labels | P4: "reviewed 100% of model-flagged entries" | P5: "sampling a smaller subset of non-flagged" | Circular validation — model selects its own eval set |

**Active red herrings embedded in text (appear naturally, are actually valid):**
- 007: Lactate/vasopressor features (temporal cutoff correctly implemented), Hospital B n=1,126 (adequately powered per pre-specified plan)
- 009: PR-AUC as metric (correct for extreme imbalance), merchant alias consolidation (validated by manual audit)
- 025: Weather forecasts as inputs (actual operational practice), outage-day exclusion (NERC standard)
- 027: Quarter-end volume spikes (normal accounting), year-end adjustments (routine close activity)
- 032: 15-day gap in time split (best practice for fraud), IP geolocation (standard CNP signal)

**Memo tone:** Every case reads as a confident recommendation. Opening paragraph leads with strong positive numbers — a reader skimming should think "this sounds solid."

**Expected difficulty profile:**
- **IDR < 1.0** — Flaws require cross-referencing details across paragraphs; a reader who processes each section independently will miss inter-section inconsistencies
- **IDP < 1.0** — Red herrings embedded as natural memo details make false-positive critiques more likely
- **DRQ failure on mixed cases** — Strong positive evidence in opening paragraphs makes critique_wins feel too aggressive, but buried flaws make defense_wins wrong

---

## Issue 7 — Phase 5.5 Gate Re-Run 3 (Haiku, v2 Cases): Gate Fails Again

**Scope:** Active — gate waived per LEAD decision in Issue 6; experiment proceeds with documented caveat
**Severity:** Moderate — expected outcome given Issue 6 root cause; confirms the gate is not calibrable by evaluator-switching on v2 cases
**Related:** Issue 5 (initial gate failure), Issue 6 (root cause: self-annotating cases + closed-loop limitation)

### What Happened

After replacing the 10 hard cases with v2 rewrites (GPT-5.4, cross-paragraph flaw structure per Issue 6 fix guidance), Phase 5.5 was re-run a third time using `claude-haiku-4-5` as a weaker proxy evaluator. Haiku scored 1.0 on all cases. Note: `eval_scenario_056` is a defense_wins case with 0 must_find items, making IDR trivially 1.0 — the meaningful gate test was on the 9 critique/mixed cases, all of which also scored 1.0.

### Root Cause

Same as Issue 6. The v2 redesign improved information architecture (cross-paragraph flaw distribution, embedded red herrings, confident memo tone) but the cases remain tractable for any Claude-family model. The closed-loop limitation is now confirmed across two independent case revisions and two evaluator tiers (Sonnet and Haiku).

### Impact

The difficulty gate cannot serve as a quality signal when the evaluator is any Claude-family model. Gate waived by LEAD; experiment proceeds with the caveat that "hard" difficulty labels are calibrated for human analysts, not Claude-family models. Difficulty-stratified lift results must be interpreted accordingly.

### What to Fix

For v5, the gate evaluator must be a non-Anthropic model, or the difficulty criterion must be validated against human annotators rather than a model pilot. Case generation must also be validated by the non-Claude evaluator before committing to a full benchmark run. The gate mechanism itself is sound — the failure is in using a same-family model as the evaluator.

---

## Issue 8 — Phase 6 Agents Attempt Direct Anthropic API Calls Despite Running Inside Claude Code Session

**Scope:** Active — occurred during Phase 6 execution
**Severity:** High — agents stall or waste resources attempting authentication that is not needed and cannot succeed from within a subagent context

### What Happened

During Phase 6 benchmark execution, one or more dispatched agents attempted to call the Anthropic API directly — searching for an `ANTHROPIC_API_KEY` environment variable, attempting to instantiate an API client, or running API connectivity tests. These agents are invoked via the Agent tool inside an already-authenticated Claude Code session and have no need to call the API directly; their inference is handled by the orchestrator's session.

### Root Cause

Agent prompts and phase files do not explicitly state the execution context. Agents lacking this context may assume they are running as standalone scripts that must self-authenticate, especially if they contain or observe code patterns (e.g., from `self_debate_poc.py`) that use `anthropic.Anthropic()` client initialization. The distinction between "I am a subagent invoked by Claude Code" and "I am a script that must call the API" is not communicated anywhere in the dispatch prompt or cross-cutting Reminders blocks.

### Impact

Agents stall mid-phase attempting to locate or test API credentials that do not exist in the subagent environment. This wastes tokens, adds latency, and may cause partial phase execution if the agent abandons its task after failing to authenticate.

### What to Fix

Add a clarifying line to the cross-cutting Reminders block at the top of every phase file that dispatches agents:

```
> - You are running as a subagent inside an authenticated Claude Code session.
>   Do not attempt to call the Anthropic API directly, locate API keys, or
>   instantiate an API client. Your inference is handled by the session.
```

Also add this to the CRITICAL EXECUTION DIRECTIVE in any agent `.md` files dispatched during Phase 6. The fix applies to all phases that use the Agent tool — not only Phase 6.

---

## Issue 9 — CLI-Based Agent Invocation Pattern (`claude --agent`) Is Not a Valid Execution Path

**Scope:** Active — pattern was attempted during Phase 6; must be prevented in all future phases
**Severity:** Moderate — failed invocations produce silent errors (stderr redirected to `/dev/null`) with no indication to the operator

### What Happened

During Phase 6, the following pattern was attempted to invoke the `ml-critic` agent from a bash script:

```bash
PROMPT=$(cat /tmp/p004.txt)
claude --agent ml-critic -p "$PROMPT" --dangerously-skip-permissions 2>/dev/null &
CRITIC_PID=$!
sleep 2
kill -0 $CRITIC_PID 2>/dev/null && echo "Critic process running" || echo "Critic process exited"
```

The `--agent` flag is not a documented Claude CLI option. The process exits immediately. Because stderr is suppressed and the invocation runs in the background, the failure is silent — no error is surfaced and the phase continues without the agent having run.

### Root Cause

Named agents in `~/.claude/agents/` are orchestration resources dispatched via the `Agent` tool inside a running Claude Code session. They are not standalone executables and cannot be invoked from bash. The CLI's `-p` flag runs a headless session but does not accept an `--agent` selector.

### Impact

If any phase script attempts this pattern, the agent silently does nothing. Downstream scoring or analysis that depends on the agent's output will fail or produce empty results without a clear error trail unless logs are inspected carefully.

### What to Fix

1. **Add to cross-cutting Reminders block** in all phase files that dispatch agents:

   ```
   > - Agents are invoked exclusively via the Agent tool inside this session.
   >   Do not attempt `claude --agent <name>` from bash — this flag does not exist
   >   and the process will exit silently. All agent dispatch must go through the
   >   orchestrator's Agent tool call.
   ```

2. **Add to `plan/PLAN.md` Execution Rules**, alongside the existing agent dispatch rule:

   > `Agents may only be invoked via the Agent tool. CLI-based agent invocation (claude --agent) is not supported and fails silently.`

3. **For v5 — if true shell parallelism is needed:** Use the Anthropic API directly with the agent's `.md` prompt as the system prompt, dispatched via subprocess. This is the only path to genuine bash-level parallelism outside a Claude Code session.

---

## Issue 10 — "Contains brace with quote character (expansion obfuscation)" Approval Prompt Fires on Every `--meta` Argument

**Scope:** Active — fires repeatedly during Phase 6 on every `log_entry.py` call that passes a `--meta` JSON argument
**Severity:** Moderate — cannot be suppressed via allow rules; requires restructuring the commands
**Related:** Issue 3 (newline+# heuristic — same pre-permission check class)

### What Happened

Every `log_entry.py` invocation that passes a `--meta` argument with inline JSON triggers the Claude Code security prompt "Contains brace with quote character (expansion obfuscation)." Phase 6 has many such calls — anomaly counts, hollow-round rates, DC/FVC diagnostic flags — making the approval prompts frequent throughout execution.

### Root Cause

Like Issue 3, this is a hard-coded pre-permission security heuristic that runs before `permissions.allow` is evaluated. The pattern `{` followed by `"` inside a quoted argument can be used to obfuscate shell expansion (e.g., `${IFS}`-style injection). No allow rule can suppress it.

### Impact

Operators must manually approve every `--meta` log entry during Phase 6, breaking the hands-off execution flow. Phase 6 generates the highest density of structured log entries in the experiment.

### What to Fix

Restructure `--meta` arguments to avoid inline JSON with brace+quote patterns. Two options:

**Option 1 — Fold meta into `--detail` string (immediate workaround, no script changes):**

```bash
uv run self_debate_experiment_v4/log_entry.py --step 9.5 --cat audit \
  --action post_run_audit_complete \
  --detail "Anomaly report complete — anomaly_count=3 critical_count=1"
```

Folds structured fields into the `--detail` string as `key=value` pairs. Less queryable downstream but avoids the heuristic entirely and requires no changes to `log_entry.py`.

**Option 2 — Add `--meta-file` support to `log_entry.py` (v5 permanent fix):**

```bash
echo '{"anomaly_count": 3, "critical_count": 1}' > /tmp/meta.json
uv run self_debate_experiment_v4/log_entry.py --step 9.5 --cat audit \
  --action post_run_audit_complete --meta-file /tmp/meta.json
```

Reads JSON from a file rather than inline. Preserves structured meta logging without triggering the heuristic. Requires adding `--meta-file` flag to `log_entry.py`.

Use Option 1 for the current experiment run. Implement Option 2 in v5.
