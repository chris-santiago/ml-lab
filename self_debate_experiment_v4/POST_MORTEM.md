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

**Option 3 — Skip all permissions for the session, scoped to repo directory:**

```json
{
  "dangerouslySkipPermissions": true,
  "allowedPaths": ["/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab"]
}
```

Add to `.claude/settings.json` before starting the Phase 6 session (remove after). Bypasses all approval prompts — including hard-coded security heuristics that allow rules cannot suppress — while restricting file operations to the repo. Bash commands are not path-restricted, but all experiment outputs land inside the repo anyway. Most aggressive option; appropriate for a known, bounded phase running locally.

---

## Issue 11 — v5 Plan Must Incorporate v4 Debate Insights and Settled Hypothesis Findings

**Scope:** Future fix — v4 experiment still running; applies to v5 plan construction
**Severity:** Moderate — a v5 plan built without v4 outcome artifacts risks repeating resolved questions and ignoring validated design constraints

### What Happened

This post-mortem captures execution issues but not the intellectual resolution of the v4 hypothesis. The debate artifacts — DEBATE.md in particular — contain the settled arguments: what the critic raised, what the defender conceded, what remained contested, and what was upheld. These represent knowledge that does not exist anywhere else in the artifact set and is the most likely to be overlooked when constructing a v5 plan.

A v5 plan built from the v4 plan files alone will inherit the v4 framing without knowing which parts of that framing were validated, which were falsified, and which open questions the debate identified as requiring a follow-on experiment.

### Impact

v5 may re-test already-settled questions, preserve design choices that were conceded as flaws, or miss the most productive next research direction — all because the planning session started from plan files rather than outcome files.

### What to Fix

Before drafting any v5 plan, the orchestrator must read and synthesize these artifacts in priority order:

1. **`DEBATE.md`** *(highest priority — most likely to be missed)* — what the critic raised, what was conceded, what was defended and upheld, what was left open
2. **`CONCLUSIONS.md`** — settled quantitative findings and their interpretations
3. **`REPORT.md` / `TECHNICAL_REPORT.md`** — final framing of what was established
4. **`POST_MORTEM.md`** — execution issues and their v5 fix recommendations (this file)

The v5 hypothesis should be derived from the open questions v4 left unresolved. The v5 protocol should preserve confirmed v4 design properties and replace all conceded v4 design flaws. Neither of these decisions can be made correctly without reading DEBATE.md first.

---

## Issue 12 — Phase 6 Batch 1 Produced Zero Valid Outputs: All 108 Runs Failed with Authentication Error

**Scope:** Active — all batch 1 data is invalid; batch must be fully re-run
**Severity:** Critical — entire batch 1 is lost; `phase6_batch1_summary.json` shows 108 authentication failures across 9 cases × 3 replicates × 4 conditions
**Related:** Issue 8 (agents attempting direct Anthropic API calls)

### What Happened

`phase6_batch1_summary.json` shows 9 cases (eval_scenario_004, 005, 015, 022, 024, 029, 030, 033, 048), each with 3 runs of 4 conditions (isolated, multiround, ensemble, baseline). All 108 runs failed identically:

```
ERROR "Could not resolve authentication method. Expected either api_key or
auth_token to be set. Or for one of the `X-Api-Key` or `Authorization` headers
to be explicitly omitted"
```

All `runs` entries are empty `{}`. No debate outputs were produced.

### Root Cause

Issue 8 manifesting at batch scale. The debate agents dispatched during Phase 6 attempted to call the Anthropic API directly to run the critic/defender protocol, rather than operating as subagents within the authenticated Claude Code session. The Issue 8 Reminders block fix was not yet applied to the running experiment's phase files when batch 1 executed.

### Impact

All of Phase 6 batch 1 must be discarded and re-run. No raw outputs exist for any of the 9 cases. The `v4_raw_outputs/` directory must be checked for corrupted partial outputs before re-running.

### What to Fix

Before re-running batch 1:

1. Verify `v4_raw_outputs/` contains no partial or corrupted outputs from the 9 batch 1 cases — delete any that exist
2. Add the subagent context reminder (Issue 8 fix) to the Phase 6 agent dispatch prompt before re-launching:
   ```
   You are running as a subagent inside an authenticated Claude Code session.
   Do not attempt to call the Anthropic API directly or locate API keys.
   Your inference is handled by the session.
   ```
3. Confirm agents are running correctly via Agent tool (not CLI) on a single test case before re-launching the full batch

---

## Issue 13 — Phase 6 Validation Step Found Malformed JSON in Benchmark Output Files

**Scope:** Active — affects current Phase 6 results; any output file from Phase 6 benchmark runs is suspect until re-validated
**Severity:** High — malformed output files cannot be parsed by downstream scoring and analysis scripts; affected runs must be identified, triaged, and re-run before Phase 7 can proceed

### What Happened

During Phase 6, the validation step that parses benchmark output files raised JSON decode errors on one or more files produced by benchmark runs. The files were written by agents executing the debate protocol conditions (isolated, multiround, ensemble, baseline) and are the primary raw artifact for all downstream scoring. The validation step could not parse the affected files, meaning their run data is inaccessible in its current form.

### Root Cause

Output files produced by Phase 6 agents are written as free-text or structured agent responses and then saved to disk without a parse-then-reserialize step. If an agent outputs malformed JSON — truncated content due to a context-length limit, escaped characters that break JSON syntax, prose mixed into a JSON block, or a missing closing delimiter — the file is written as-is. No write-time validation guards against this. The validation step is the first point in the pipeline that attempts `json.loads()` on the output, so malformed files are only discovered after the fact.

### Impact

Any output file that fails JSON parsing cannot contribute data to Phase 7 scoring or analysis. The number of affected runs, and which cases and conditions they cover, must be determined by inspecting the validation step's error output before any further work proceeds. If the affected runs are concentrated in a single condition or case subset, the experimental results for that slice are incomplete. If they are distributed across conditions, lift estimates derived from the Phase 6 data will be biased by unequal sample sizes.

**What to fix in v5:**
1. **Immediate triage (running experiment):** Run the validation step with verbose error output to collect the exact file paths and case/condition/replicate coordinates of every malformed file. Log these to `INVESTIGATION_LOG.jsonl` before taking any remediation action.
2. **Re-run affected cases:** For each affected run coordinate, delete the malformed output file and re-dispatch the corresponding agent with the same inputs. Confirm the replacement file parses cleanly before moving to Phase 7.
3. **Add write-time JSON validation to the Phase 6 output writer:** After each agent completes and its output is written to `v4_raw_outputs/`, immediately attempt `json.loads()` on the file. If it fails, log the error to `INVESTIGATION_LOG.jsonl` with action `write_validation_fail` and flag the run for immediate re-execution — do not proceed to the next case in the batch.
4. **Add a schema check to write-time validation:** Confirm the parsed object has the required top-level keys before accepting the file as valid. A file that parses as `{}` or as a bare string should be treated the same as one that raises a `JSONDecodeError`.
5. **Add `--validate-output` flag to the batch runner script:** Parse and schema-check each output immediately after write; abort the run and surface a clear error rather than silently writing a corrupt file and continuing.

---

## Issue 14 — Phase 6.75 Confirms Ceiling Scores on All 16 Hard Cases; DRQ Non-Informative for Majority of Hard Cases

**Scope:** Active — blocks Phase 7; all hard case scores for the baseline condition are meaningless under current evaluation setup
**Severity:** Critical — 10/10 hard cases in Phase 6.75 sample score baseline mean = 1.0; combined with prior hard case runs this is 16/16 hard cases at ceiling; the difficulty gate has failed for the third time; Phase 7 cannot produce valid difficulty-stratified results until this is resolved
**Related:** Issue 5 (Phase 5.5 gate failure v1), Issue 6 (closed-loop evaluation root cause), Issue 7 (Phase 5.5 gate re-run 3 — gate fails again)

### What Happened

Phase 6.75 ran a single-pass baseline evaluation on a sample of 10 hard cases as a pre-Phase-7 checkpoint. Every case scored baseline mean = 1.0 — all must_find issues surfaced, no must_not_claim items triggered, and the correct verdict reached on every case. This is the same result observed in Issues 5 and 7: a Claude-family model acting as evaluator scores hard cases perfectly regardless of difficulty label or case redesign effort.

A second structural problem was also identified: DRQ (Debate Resolution Quality) is `None` for 8 of 10 hard cases. These 8 cases resolve to `empirical_test_agreed`, which occurs when the correct position is `"mixed"` — i.e., cases where both the critique and the defense are partially valid. The DRQ scoring logic excludes `empirical_test_agreed` resolutions, so the metric produces no signal for the majority of hard cases in the current benchmark. DRQ is effectively non-informative as a comparative metric across conditions for the hard-case stratum.

This phase checkpoint is plan-mandated. The plan requires pausing and presenting findings to the LEAD before proceeding to Phase 7.

### Root Cause

**Ceiling scores (IDR/IDP/FVC):** Same result confirmed across three independent gate runs spanning two case generations (v1 revision and v2 revision) and two evaluator tiers (Sonnet and Haiku). Critically: the hard cases were generated by ChatGPT — a non-Anthropic model — not by a Claude-family model. Cross-family case generation does not break the ceiling. This rules out generator–evaluator family overlap as the root cause. The problem is structural: the cases contain flaws that are detectable by pattern-matching within the document — factual inconsistencies, explicit cross-paragraph contrasts, or trigger phrases that activate known LLM detection heuristics. Claude-family models execute these heuristics reliably regardless of who wrote the case. Switching case generators alone does not help; changing the flaw type to something that requires external knowledge, computation, or detection of absence (per CASE_GENERATION_PROMPT_V5.md) is required.

**DRQ null problem:** The DRQ metric is defined only for resolutions that produce a clear winner (`critique_wins` or `defense_wins`). Cases where the correct position is `"mixed"` resolve to `empirical_test_agreed` when the debate reaches the correct verdict, and this resolution is excluded from DRQ scoring by design. The current hard-case benchmark disproportionately contains `"mixed"` cases — 8 of 10 sampled. This is not a scoring bug; it is a benchmark composition problem that makes DRQ near-useless for the hard stratum specifically.

### Impact

Phase 7 cannot produce valid difficulty-stratified results for hard cases under the current setup. Difficulty-stratified lift estimates that include the hard stratum will show ceiling performance on the baseline condition, compressing any apparent debate protocol lift toward zero for that stratum. The two-metric failure compounds: IDR/IDP/FVC are at ceiling (no room for lift), and DRQ is null for 80% of cases (no comparative signal). Any Phase 7 results for hard cases would be uninterpretable and should not be reported.

The Phase 6.75 checkpoint functioned correctly — it caught this validity problem before Phase 7 resources were committed. The gate mechanism is sound; the case structure is not.

### What to Fix

**1. Immediate — plan-mandated LEAD decision required before Phase 7:**

Options: (a) proceed to Phase 7 with hard cases excluded from difficulty-stratified analysis and document the caveat explicitly, (b) replace hard cases with v5-designed cases and re-run the difficulty gate before Phase 7, or (c) defer Phase 7 entirely until v5. Log the LEAD decision to `INVESTIGATION_LOG.jsonl` before any Phase 7 execution begins.

**2. DRQ null problem — revise scoring or benchmark composition for v5:**

Either (a) define a DRQ score for `empirical_test_agreed` resolutions based on argument quality relative to the shared correct resolution, or (b) report DRQ coverage (percent of cases where DRQ is non-null) as a first-class metric. Additionally, cap `"mixed"` cases at ≤ 30% of the hard-case stratum in v5 to ensure DRQ is informative across a meaningful subset.

**3. Structural fix — v5 hard cases require flaw types outside LLM detection heuristics:**

Switching the case generator (ChatGPT instead of Claude) did not change scores. The fix is in the flaw type: v5 cases (per `CASE_GENERATION_PROMPT_V5.md`) target assumption violations, critical omissions, and quantitative errors that require external knowledge or computation to find — not factual inconsistencies that any capable LLM detects by pattern-matching. Validate v5 cases against a Claude-family evaluator *before* committing to Phase 6 to confirm the ceiling is broken.

**4. v5 difficulty gate must confirm < 1.0 before Phase 6:**

Do not proceed to Phase 6 in v5 with any hard case that scores 1.0 under single-pass Claude evaluation. The Phase 5.5 gate is the correct control point; the acceptance criterion (mean < 0.55 on ≥ 6 of 10 cases) must be enforced, not bypassed.

---

## Issue 15 — Inverted Difficulty–Score Correlation: Spearman rho=+0.691 Between Difficulty Labels and Baseline Rubric Scores

**Scope:** Active — affects current Phase 7 scoring results
**Severity:** High — invalidates difficulty labels as a validity check; difficulty-stratified lift estimates are uninterpretable
**Related:** Issue 5 (Phase 5.5 gate failure), Issue 6 (closed-loop evaluation root cause), Issue 14 (Phase 6.75 ceiling scores on hard cases)

### What Happened

`difficulty_validation.py` computed Spearman rho between difficulty labels (easy=1, medium=2, hard=3) and baseline rubric scores (mean of IDR, IDP, FVC) across all benchmark cases. The result was rho=+0.691 (p<0.001) — a strong positive correlation. The script printed:

```
WARNING: Difficulty labels may not predict rubric performance. Review case design.
```

The expected relationship is a negative correlation: harder cases should produce lower baseline scores. The observed correlation is in the opposite direction. Hard cases scored higher than easy cases on every scoring dimension across all conditions.

### Root Cause

The inversion arises from a structural asymmetry in how easy and hard cases were constructed:

- **Hard cases** predominantly have `empirical_test_agreed` as their `ideal_resolution`, with broadly stated `acceptable_resolutions` that match multiple argument framings. Any agent that reaches the correct general verdict satisfies the rubric regardless of how it gets there.
- **Easy cases** tend to have specific `must_find_issue_ids` that require agents to identify named flaws using the exact terminology encoded in the rubric. Agents that identify the correct underlying problem but describe it differently fail to trigger a `must_find` match, depressing IDR.

The result is a rubric that is mechanically easier to satisfy on hard cases than easy ones, independent of analytical difficulty.

### Impact

Difficulty-stratified analysis in Phase 7 is invalid. Apparent lift compression in the easy stratum reflects rubric strictness, not protocol weakness. This compounds Issues 5/6/14 — not only do all cases score near ceiling, but the stratum ordering is inverted relative to its intended interpretation.

### What to Fix

**Immediate:** Do not report difficulty-stratified lift estimates without a prominent caveat. Note rho=+0.691 (p<0.001) in conclusions.

**v5 structural fixes:**
1. Revise easy-case `must_find_issue_ids` to use broader semantic matching — easy cases should be easy to satisfy
2. Revise hard-case `acceptable_resolutions` to require more specific framing
3. Add Spearman anti-correlation check (rho must be < 0) to Phase 5.5 before gate acceptance
4. Cap `empirical_test_agreed` as `ideal_resolution` for hard cases at ≤30% of the hard stratum

---

## Issue 16 — List Comprehension Scope Bug and None Comparison Error in Phase 7 Analysis Scripts

**Scope:** Future fix — scripts have been patched in-place; Phase 7 results are correct
**Severity:** Moderate — blocked Phase 7 execution but was straightforward to fix once identified

### What Happened

Two bugs in the Phase 7 analysis scripts (`stats_analysis.py`, `sensitivity_analysis.py`) prevented Phase 7 from executing without manual intervention.

**Bug 1 — List comprehension variable scope:** Both scripts contained nested list comprehensions of the form:

```python
[expr for run in runs if run['scores'].get(d) for d in dims]
```

This raises `UnboundLocalError: free variable 'd' referenced before assignment in enclosing scope` at runtime. Python evaluates comprehension clauses strictly left-to-right, so the `if` clause referencing `d` is reached before the `for d in dims` clause that defines it.

**Bug 2 — None comparison in `stats_analysis.py`:** A scoring threshold check used `.get('DC', 0) >= 0.5` to test whether the DC dimension score met the acceptance threshold. When the key is present in the dict but its value is explicitly `None`, `.get('DC', 0)` returns `None` — the default `0` only applies when the key is absent. Comparing `None >= 0.5` raises `TypeError: '>=' not supported between instances of 'NoneType' and 'float'`.

### Root Cause

**Bug 1:** The comprehension clause order inverted the required left-to-right evaluation sequence. The correct form is:

```python
[expr for run in runs for d in dims if run['scores'].get(d)]
```

The `for d in dims` binding must precede any `if` clause that references `d`.

**Bug 2:** `dict.get(key, default)` only returns the default when the key is absent. If the key is present with value `None`, the stored `None` is returned directly. Fix:

```python
(r['ensemble']['runs'][0]['scores'].get('DC') or 0) >= 0.5
```

### Impact

Both bugs raised exceptions before any output was written. Manual in-place fixes were required before Phase 7 could complete. No output artifacts were affected — all Phase 7 results are valid.

### What to Fix

1. Enforce `for d in dims` before `if cond(d)` in all comprehensions — binding clauses always precede filter clauses
2. Audit all `.get(key, default)` arithmetic/comparison calls in scoring paths; replace with `(d.get(key) or default)` pattern
3. Add a Phase 6 output normalization step that replaces `None`-valued score fields with `0` before Phase 7 scripts read them

---

## Issue 17 — v5 Benchmark Case Generation Redesigned to Break Hard-Case Ceiling

**Scope:** Future fix — applies to v5 benchmark case generation; v4 results are not affected
**Severity:** High — addresses the root cause of the inverted difficulty–score correlation and ceiling failure documented in Issues 14 and 15
**Status:** Resolved
**Related:** Issue 14 (Phase 6.75 ceiling scores on all hard cases), Issue 15 (inverted difficulty–score correlation, rho=+0.691)

### What Happened

All v4 hard cases scored at ceiling (baseline mean = 1.0) across three independent gate runs. Issue 14 confirmed that switching the case generator from Claude-family to ChatGPT did not break the ceiling. Issue 15 identified the structural cause: hard cases relied on planted flaws detectable by internal consistency checking — factual contradictions between stated facts within a single document. Finding within-document inconsistencies is a capability LLMs exercise through pattern-matching, regardless of how those inconsistencies are distributed across paragraphs or surrounded by red herrings. The flaw type was wrong; redesigning surface structure without changing the flaw type cannot break the ceiling.

Two generation prompts were redesigned to address this root cause before v5 case generation begins.

### Changes Made — `benchmark_case_generation_prompt.md`

The main prompt was redesigned around 8 structural principles that collectively prohibit the flaw types that produced ceiling scores in v4:

- **Principle 1** prohibits parallel before/after paragraph structure. The pattern — "in the training period ... in the deployment period" — triggers a mechanical diff scan that finds the inconsistency without domain reasoning.
- **Principle 8** requires the most salient surface feature to be a `must_not_claim` red herring. The agent must evaluate the justification and continue searching rather than surface the first anomaly it finds.

The remaining 6 principles address related structural tells: contrast-signaling vocabulary, compensation language, named temporal partitions, and other trigger phrases observed causing immediate detection in v4 raw output analysis.

A 4-type flaw taxonomy was added:

| Type | Description |
|------|-------------|
| A | Assumption violations — conclusions that follow from stated facts but rest on an unstated assumption that does not hold |
| B | Quantitative errors — computations that appear reasonable but produce wrong results; verification requires arithmetic |
| C | Critical omissions — absence of a mandatory disclosure; detection requires knowing what should be present |
| D | Subtly wrong justifications — correct intent, but the stated reasoning is invalid in a non-obvious way |

All four types require the evaluating model to bring external knowledge, perform computation, or reason about absence — none detectable by comparing statements within the document.

Empirically-grounded detection patterns from v4 raw output analysis were added with structural defenses: Diff-the-Paragraphs, Claim-vs-Evidence Gap Analysis, Label Provenance Tracing, Observational Study Confound Enumeration. A trigger phrase prohibition list was added enumerating specific vocabulary observed immediately preceding correct flaw identification in v4 outputs.

New schema fields: `planted_issues[].flaw_type`, `planted_issues[].requires_external_knowledge`, `difficulty_justification`.

A 5th self-evaluation gate — the **Run-to-Run Variation Test** — was added: verbatim-identical outputs across independent runs are a falsifiable signal the case is too easy.

Hard case acceptance criteria formalized: `claude-haiku-4-5` single-pass mean < 0.55 AND demonstrated run-to-run variation. Phase 5.5 difficulty gate formalized as a mandatory operator step with a documented pass/fail decision point.

### Changes Made — `REAL_PAPER_CASE_GENERATION_PROMPT.md` (new)

A secondary generation strategy grounds cases in documented real-world methodological failures from published ML papers, then transposes the underlying flaw mechanism to a structurally analogous domain to prevent source recognition.

Source paper library (12 papers):

| Paper | Core flaw mechanism |
|-------|---------------------|
| Dacrema et al. 2019 | Untuned baselines inflate apparent lift |
| Obermeyer et al. 2019 | Cost-as-proxy assumption violation in label construction |
| DeGrave et al. 2021 | Shortcut learning; no out-of-site validation |
| Lazer et al. 2014 | Stationarity assumption violated by search algorithm changes |
| Zech et al. 2018 | Hospital-system confounding invisible under internal splits |
| Recht et al. 2019 | Benchmark overfitting via iterative test-set reuse |
| Hooker et al. 2019 (ROAR) | Retraining changes the model being evaluated |
| SMOTE-before-CV pitfall | Correct intent, wrong execution order |
| Caruana et al. 2015 | Treatment selection bias masking true population risk |
| Time series sequence leakage | Sequence generation before split leaks future information |
| Offline-online recommendation gap | Offline metrics do not predict online behavior |
| RLHF reward overoptimization | Goodhart's Law: reward model becomes the optimization target |

Transformation instructions require extracting the flaw at the abstract mechanism level before transposing to a new domain. A 6th self-evaluation test — the **Source Recognition Test** — was added: a reviewer who has read the source paper must not identify it from the task prompt. A `source_paper` field tracks provenance for operators only.

### Expected Outcome

Hard cases should score mean < 0.55 on `claude-haiku-4-5` single-pass assessment and produce run-to-run variation. Both must be confirmed empirically via Phase 5.5 before any batch proceeds to Phase 6.

### What to Fix in v5

1. Use revised `benchmark_case_generation_prompt.md` as the primary generation prompt. Enforce all 8 design principles at generation time, not at gate time.
2. Use `REAL_PAPER_CASE_GENERATION_PROMPT.md` as a secondary strategy, targeting at least 4 of 10 hard cases per batch from real-paper transpositions.
3. Enforce Phase 5.5 as a mandatory gate: no hard case with `claude-haiku-4-5` single-pass mean ≥ 0.55 or with identical outputs across two independent runs proceeds to Phase 6.
4. Add the Spearman anti-correlation check to Phase 5.5 (per Issue 15): rho between difficulty labels and baseline scores must be negative before the hard-case batch is accepted.
5. Cap `"mixed"` correct-position cases at ≤ 30% of the hard stratum (per Issue 14) to ensure DRQ is informative.
