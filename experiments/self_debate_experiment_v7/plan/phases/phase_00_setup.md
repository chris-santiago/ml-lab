# Phase 0 — Setup

> **Reminders**
> - `uv run` only. Never `python` or `python3`.
> - CWD: repo root. Use `cd experiments/self_debate_experiment_v7 &&` prefix.
> - No agent dispatch in Phase 5 — Claude calls go through `pipeline/phase5_benchmark.py`.

## Required Reading
- [design_decisions.md §1](../references/design_decisions.md#1-conditions-4) — `multiround_2r` design
- [API_DISPATCH_PLAN.md](../references/API_DISPATCH_PLAN.md) — phase5_benchmark.py architecture
- [v6_lessons.md L4, L6](../references/v6_lessons.md) — adjudicator prompt + atomic writes

---

## Steps

### 0.1 Environment verification
```bash
uv --version
echo $OPENROUTER_API_KEY | cut -c1-8   # confirm set (show prefix only)
echo $CROSS_VENDOR_API_KEY | cut -c1-8
echo $CROSS_VENDOR_MODEL
```
Required env vars: `OPENROUTER_API_KEY`, `CROSS_VENDOR_API_KEY`, `CROSS_VENDOR_BASE_URL`,
`CROSS_VENDOR_MODEL`. Set in `.claude/settings.local.json` or `UV.env` (both gitignored).

### 0.2 Create v7 directory structure
```bash
cd experiments/self_debate_experiment_v7 && mkdir -p v7_raw_outputs pipeline/prompts
```

### 0.3 Scaffold `pipeline/phase5_benchmark.py`
Following the architecture in `API_DISPATCH_PLAN.md`:
- PEP 723 header (openai>=1.0, rich>=13.0)
- CLI args: `--cases`, `--output-dir`, `--conditions`, `--max-concurrent`, `--model`,
  `--timeout`, `--retries`, `--dry-run`, `--temperature`
- AsyncOpenAI client via OpenRouter
- `call_api` + `parse_response` (think-tag strip + JSON extract + repair)
- Atomic file writes: `.tmp` → `os.rename()`
- Resume logic: scan output dir, skip completed `(case_id, condition, run_idx)` tuples

Verify current OpenRouter model string before coding:
```bash
# Check available claude models on OpenRouter
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | \
  python3 -c "import json,sys; models=[m['id'] for m in json.load(sys.stdin)['data'] if 'claude' in m['id'].lower()]; print('\n'.join(sorted(models)))"
```

### 0.4 Write system prompts

**Critic** (`pipeline/prompts/critic.md`): adapted from `plugins/ml-lab/ml-critic.md`.
Strip Mode 1/2/3 file-reading instructions. Add explicit `defense_wins` verdict path
with empty `all_issues_raised` and the instruction: *"A confident 'no significant issues'
conclusion is as important as identifying genuine flaws."* (per `design_decisions.md §2`,
v6 lesson L7). JSON output format:
```json
{"critic_raw": "...", "all_issues_raised": ["..."], "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

**Isolated defender** (`pipeline/prompts/defender_isolated.md`): adapted from
`plugins/ml-lab/ml-defender.md`. Does NOT see critic output.

**Debate defender** (`pipeline/prompts/multiround_2r_defender.md`): receives critic output
in user message. Prompt: "Respond to the critic's analysis point by point."
```json
{"defender_raw": "...", "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

**Adjudicator** (`pipeline/prompts/adjudicator.md`): new — no v6 equivalent (was inline).
- Per-issue triage: SURVIVES (unaddressed, conceded, or empirically open) vs DROP (convincingly rebutted)
- Mixed-case injection (per v6 lesson L4): append to prompt when `case["category"] == "mixed"`:
  "This is a mixed case. Valid verdicts: critique_wins, defense_wins, empirical_test_agreed.
  Use empirical_test_agreed when both sides made substantive points only resolvable empirically."
```json
{"all_issues_adjudicated": ["..."], "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

### 0.5 Implement condition handlers in `phase5_benchmark.py`

**`multiround_2r`** (3 sequential calls):
```
critic(task_prompt) → defender(task_prompt + critic_output) → adjudicator(critic + defender)
```
No stop detection. No loop. Exactly 3 calls.

**`isolated_debate`** (3 calls: critic ‖ defender concurrently, then adjudicator):
```
asyncio.gather(critic(task_prompt), defender(task_prompt)) → adjudicator(critic + defender)
```
Defender does NOT receive critic output (use `defender_isolated.md`).

**`ensemble_3x`** (3 parallel critic calls):
```
asyncio.gather(critic_0, critic_1, critic_2)
  → majority vote for verdict; union for all_issues
  → store per-assessor {found} booleans
```

**`baseline`** (1 call): `critic(task_prompt)` only. `all_issues_adjudicated = all_issues_raised`.

### 0.6 Dry-run validation
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/phase5_benchmark.py \
  --cases v7_cases_sanitized.json \
  --output-dir v7_raw_outputs \
  --conditions baseline \
  --dry-run
```
Confirm: prompts printed, no API calls, output paths correctly formed.

### 0.7 Update scoring engine

Copy `experiments/self_debate_experiment_v6/v6_scoring.py` → `pipeline/v7_scoring.py`.
Changes:
- Remove ETD from `DIMENSIONS` and all scoring/reporting code
- Add equivalence CI check function: `check_equivalence(ci_lower, ci_upper, bound) -> bool`
  returning True if CI falls entirely within [−bound, +bound]. Accepts per-hypothesis
  bounds: H1a ±0.015 FC, H5 ±0.03 precision (see `design_decisions.md §4`)
- Add H4 test: one-sided bootstrap for ensemble_3x > baseline IDR (regular cases)
- Add H5 test: per-case issue classification (1/3 vs 3/3 precision parity)
- Update file paths from `v6_*` to `v7_*`

### 0.8 Commit all setup artifacts
Commit `pipeline/phase5_benchmark.py`, all system prompts, `pipeline/v7_scoring.py`
before Phase 1 begins.

---

## Verification
- [ ] All env vars confirmed set
- [ ] `phase5_benchmark.py` dry-run prints prompts without API calls
- [ ] `multiround_2r` handler: exactly 3 sequential calls (verify with `--dry-run` trace)
- [ ] Adjudicator prompt includes mixed-case injection logic
- [ ] Atomic write pattern implemented (`os.rename()` after `.tmp`)
- [ ] ETD removed from `v7_scoring.py`

## Outputs
- `pipeline/phase5_benchmark.py`
- `pipeline/prompts/critic.md`, `defender_isolated.md`, `multiround_2r_defender.md`, `adjudicator.md`
- `pipeline/v7_scoring.py`

## Gate
All artifacts committed. Dry-run passes. Scoring engine updated.
