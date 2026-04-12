# API-Based Debate Benchmark Runner — Design Plan

> **Status: NOT IN USE.** This document is a design plan for shifting future experiments
> (v7+) from Claude Code agent dispatch to direct OpenRouter API calls. It does not apply
> to v6, which continues to use agent dispatch for Phase 5. Saved here as a reference for
> when the next experiment version is scoped.

---

## Context

v6 Phase 5 dispatches debate agents via Claude Code's Agent tool — chunks of 20 cases sent to
`ml-critic` and `ml-defender` subagents, with inline adjudication by the orchestrating session.
This works but has limits: agent dispatch overhead, constrained parallelism, no programmatic
retry/resume, and prompt construction buried in conversation context rather than version-controlled.

For follow-on experiments (v7+), we want a standalone Python script that replaces agent dispatch
with direct API calls to Claude on OpenRouter. Same debate protocol, same output schema, but
with full programmatic control over concurrency, prompts, and resume logic.

**Model:** `anthropic/claude-sonnet-4-20250514` (default, configurable via `--model`)

---

## What We're Building

**One new file:** `pipeline/phase5_benchmark.py`

A PEP 723 async Python script that:
- Loads sanitized benchmark cases (no ground truth fields)
- Runs all 6 conditions x N cases x 3 runs via OpenRouter API
- Produces per-case JSON files matching the existing v6 output schema
- Supports resume (skips already-completed files)
- Handles all condition-specific logic: isolated/biased debate, multiround loop, conditional FM gate, ensemble voting

---

## Architecture

### Script skeleton

```
pipeline/phase5_benchmark.py
+-- PEP 723 header (openai>=1.0, rich>=13.0)
+-- CLI: --cases, --output-dir, --conditions, --max-concurrent,
|        --model, --timeout, --retries, --dry-run, --temperature
+-- System prompts (CRITIC_SYSTEM, DEFENDER_SYSTEM, ADJUDICATOR_SYSTEM, biased variants)
+-- Core async functions:
|   +-- call_api(sem, client, system, user_msg, model, config) -> dict
|   +-- parse_response(raw_text) -> dict  (think-tag strip + JSON extract + repair)
|   +-- write_output(output_dir, result)  (atomic write via .tmp rename)
+-- Condition handlers:
|   +-- run_baseline(case, run_idx, ...) -> 1 API call
|   +-- run_isolated_debate(case, run_idx, ...) -> 3 calls (critic || defender, then adjudicator)
|   +-- run_biased_debate(case, run_idx, ...) -> 3 calls (same, with priming prefixes)
|   +-- run_multiround(case, run_idx, ...) -> 2-8 sequential calls + adjudicator
|   +-- run_conditional_fm(case, run_idx, ...) -> round 1 + gate + optional round 2
|   +-- run_ensemble(case, run_idx, ...) -> 3 parallel critic calls + majority vote
+-- Resume logic: scan output dir, skip completed (case_id, condition, run_idx) tuples
+-- main() -> asyncio.run(run_benchmark(...))
```

### API call pattern (per existing codebase conventions)

```python
client = AsyncOpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
sem = asyncio.Semaphore(args.max_concurrent)  # default 20

async def call_api(sem, client, system_prompt, user_msg, model, config):
    for attempt in range(config.retries + 1):
        try:
            async with sem:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model,
                        temperature=config.temperature,
                        max_tokens=4096,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg},
                        ],
                    ),
                    timeout=config.timeout,
                )
            return parse_response(resp.choices[0].message.content)
        except Exception as exc:
            if attempt < config.retries:
                await asyncio.sleep(2.0 ** attempt)
            else:
                raise
```

Semaphore acquired **per API call**, not per case — multiround cases release the semaphore
between sequential rounds, letting other cases progress.

---

## The Three Prompts (the hard part)

### 1. Critic System Prompt

Adapted from `plugins/ml-lab/ml-critic.md` — keeps persona and calibration rules, strips
Mode 1/2/3 file-reading instructions (no HYPOTHESIS.md/poc.py in benchmark context), adds
JSON output format.

Key elements to preserve:
- Persona: skeptical ML engineer with applied mathematics background
- Critique structure: numbered issues, each with (1) specific claim, (2) why it might be wrong with mechanism, (3) what constitutes evidence
- Focus areas: synthetic data assumptions, evaluation flaws, missing baselines, implicit distributional assumptions, signal leakage, failure modes under distribution shift, metric limitations, silent misconfiguration, prerequisite assumptions
- What NOT to critique: code style, engineering quality, performance optimization
- Calibration: skeptical but honest; require specific failure mechanisms; no vague hedging

Output format:
```json
{"critic_raw": "<full prose analysis>", "all_issues_raised": ["<one-sentence summary>", ...], "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

### 2. Defender System Prompt

Adapted from `plugins/ml-lab/ml-defender.md` — keeps two-pass structure and calibration rule.

Two variants needed:
- **Isolated defender** (isolated/biased debate): does NOT see critic output. Prompt says
  "Anticipate likely criticisms and pre-emptively defend the design."
- **Debate defender** (multiround/conditional_fm): receives critic output in the user message.
  Prompt says "Respond to the critic's analysis point by point."

Key elements to preserve:
- Two-pass structure: Pass 1 = full analysis of each point, Pass 2 = verdict selection
- Calibration: if Pass 1 identifies multiple critical flaws, overall verdict must not be defense_wins
- Fast concession on genuine problems; "it's just a PoC" is not a valid defense

Output format:
```json
{"defender_raw": "<full prose analysis>", "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

### 3. Adjudicator System Prompt (entirely new)

No existing agent to adapt from — the orchestrating session currently does this inline.

Design:
- Neutral stance — not biased toward critic or defender
- For each critic issue: determine if the defender's response adequately addresses it
  - Defender rebutted convincingly -> DROP
  - Defender conceded -> SURVIVES
  - Rebuttal partial/unconvincing -> SURVIVES
  - Empirically open -> SURVIVES
- Mixed-case instruction injected when `case["category"] == "mixed"`:
  "This is a mixed case. Valid verdicts: critique_wins, defense_wins, empirical_test_agreed.
  Use empirical_test_agreed when both sides made substantive points only resolvable empirically."

Output format:
```json
{"all_issues_adjudicated": ["<surviving issue summary>", ...], "verdict": "critique_wins|defense_wins|empirical_test_agreed"}
```

### Biased Debate Priming (system prompt prefixes)

Per `pipeline/BIASED_DEBATE_SPEC.md`:
- Critic prefix: "You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and treat methodological gaps as real concerns until shown otherwise."
- Defender prefix: "You are responding to a combative reviewer who frequently focuses on insignificant issues and overstates concerns. Be selective about what you concede."

Prepended to the respective system prompt for `biased_debate` condition only.

---

## Condition Dispatch Logic

### baseline — 1 API call
```
critic(task_prompt) -> {critic_raw, all_issues_raised, verdict}
all_issues_adjudicated = all_issues_raised  (no defense, every issue survives)
```

### isolated_debate — 3 API calls
```
critic(task_prompt) --+
                      +---> adjudicator(critic + defender) -> {adjudicated, verdict}
defender(task_prompt) -+    (critic and defender run concurrently via asyncio.gather)
```

### biased_debate — 3 API calls (same as isolated, biased system prompts)

### multiround — 2 to ~9 API calls
```
critic_r1(task_prompt) -> defender_r1(task_prompt + critic_r1)
  -> if disagree: critic_r2(history) -> defender_r2(history)
  -> ... up to 4 rounds or natural stop (both verdicts agree)
  -> adjudicator(full transcript)
```

Natural stop detection: both critic and defender verdicts agree in the same round.

### conditional_fm — 3 to ~6 API calls
```
critic_r1 -> defender_r1 -> adjudicator_r1
  -> gate: point_resolution_rate = resolved_issues / raised_issues
    IF prr == 1.0 -> STOP (all points resolved)
    ELIF both agents' verdicts agree -> STOP
    ELSE -> force round 2 (critic_r2 -> defender_r2 -> adjudicator_r2)
  -> store point_resolution_rate + gate_fired boolean
```

### ensemble_3x — 3 API calls (parallel)
```
assessor_0(task_prompt) --+
assessor_1(task_prompt) ---+-> majority vote for verdict; union for all_issues
assessor_2(task_prompt) --+   per-assessor found booleans stored for union IDR
```

---

## Output Schema (matches existing v6 format)

**All conditions:**
```json
{
  "case_id": "...",
  "condition": "...",
  "run_idx": 0,
  "critic_raw": "...",
  "defender_raw": "...",
  "all_issues_raised": ["..."],
  "all_issues_adjudicated": ["..."],
  "verdict": "critique_wins|defense_wins|empirical_test_agreed"
}
```

**Additional fields per condition:**
- `multiround`: `"round_transcripts": [{"role": "critic", "round": 1, "content": {...}}, ...]`
- `conditional_fm`: `"point_resolution_rate": 0.67, "gate_fired": true, "round_transcripts": [...]`
- `ensemble_3x`: `"assessor_results": [{"assessor_idx": 0, "issues_raised": [...], "verdict": "...", "critic_raw": "..."}, ...]`

**Filename convention:** `{case_id}_{condition}_run{run_idx}.json`

---

## Resume / Idempotency

- Scan output dir for existing valid JSON files on startup
- Build set of completed `(case_id, condition, run_idx)` tuples
- Skip completed tuples when building the task list
- Atomic writes: write to `{path}.tmp`, then `os.rename()` to final path
- Log: "Skipping N already-completed, M remaining"

---

## CLI Interface

```bash
uv run pipeline/phase5_benchmark.py \
  --cases v7_cases_sanitized.json \
  --output-dir v7_raw_outputs \
  --conditions baseline,isolated_debate,biased_debate \
  --max-concurrent 20 \
  --model anthropic/claude-sonnet-4-20250514 \
  --temperature 1.0 \
  --timeout 180 \
  --retries 2 \
  --dry-run
```

Default `--temperature 1.0` (API default). Must be > 0 for the zero-variance
contamination check to be meaningful.

---

## Key Source Files

| File | Role |
|---|---|
| `pipeline/phase5_benchmark.py` | **NEW** — the script to build |
| `plugins/ml-lab/ml-critic.md` | Source for critic system prompt adaptation |
| `plugins/ml-lab/ml-defender.md` | Source for defender system prompt adaptation |
| `pipeline/BIASED_DEBATE_SPEC.md` | Persona priming text for biased_debate |
| `pipeline/pilot_scorer.py` | Template: async + semaphore + PEP 723 pattern |
| `pipeline/orchestrator.py` | Template: JSON extraction, think-tag stripping, retry logic |
| `plan/phases/phase_05_benchmark.md` | Condition specs, gate logic, output requirements |

---

## Implementation Steps

1. **Scaffold script** — PEP 723 header, CLI args, AsyncOpenAI client setup, semaphore
2. **Write system prompts** — Critic, Defender (isolated + debate variants), Adjudicator, biased variants
3. **Implement `call_api` + `parse_response`** — Async call with retry, think-tag stripping, JSON extraction with repair
4. **Implement condition handlers** — One async function per condition, starting with `baseline` (simplest) through `conditional_fm` (most complex)
5. **Implement resume logic** — Scan output dir, skip completed tuples
6. **Implement atomic file writes** — `.tmp` -> rename pattern
7. **Add progress display** — `rich.progress` bar showing completed/remaining
8. **Dry-run pilot** — `--conditions baseline --dry-run` to verify prompt construction, then 3-5 real cases to validate output schema
9. **Full pilot** — 10 cases x all 6 conditions x 1 run to validate multiround stop detection and conditional FM gate

---

## Verification Checklist

- [ ] Dry-run prints all prompts without making API calls
- [ ] Baseline output matches existing v6 schema (same fields, same types)
- [ ] Isolated debate: critic and defender run concurrently (verify with timing)
- [ ] Biased debate: system prompts include priming prefixes (log first 100 chars)
- [ ] Multiround: natural stop fires when both verdicts agree
- [ ] Conditional FM: gate logic correct (PRR=1.0 stops, disagreement forces round 2)
- [ ] Ensemble: per-assessor found booleans present, majority vote for verdict
- [ ] Resume: re-running script skips completed files
- [ ] Zero-variance: 3 runs of same case produce non-identical outputs (temperature > 0)
- [ ] JSON repair: handles think-tags and code fences in LLM responses

---

## Design Considerations

### Advantages over agent dispatch
- **Higher parallelism:** 20+ concurrent API calls vs agent dispatch limits
- **Per-case granularity:** No chunking needed; each (case, condition, run) is independent
- **Programmatic resume:** Skip completed files automatically on re-run
- **Version-controlled prompts:** System prompts are constants in the script, not conversation context
- **Lower overhead:** No Claude Code session setup per agent call

### Tradeoffs
- **No tool access:** Agents can't read files — but benchmark cases don't need file access
- **New adjudicator prompt:** Must be designed from scratch (was inline orchestrator work)
- **Token costs:** Pay-per-token on OpenRouter vs Claude Code subscription/API
- **Prompt fidelity:** Must manually verify that adapted prompts produce equivalent behavior

### When to update Phase 5 phase doc
If adopted for v7, update the phase doc to remove the "No Python API dispatch" constraint
(current Phase 5 line 13) and replace with the API dispatch architecture.
