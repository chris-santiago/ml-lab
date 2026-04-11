# Phase 5 — Benchmark Run

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

> **⚠ DISPATCH ARCHITECTURE (decision 09206a5b — do not re-litigate)**
> - **Two agents only:** `ml-critic` and `ml-defender`. There is no adjudicator agent.
> - **Adjudication is inline:** for `isolated_debate` and `biased_debate`, the orchestrating Claude Code session dispatches critic and defender independently, then synthesizes their outputs directly — no separate agent call.
> - **No Python API dispatch:** Python scripts (`uv run`) handle file management, schema validation, and scoring only. All Claude work happens via Agent tool calls from this session. Never call Claude via OpenRouter or direct API from experiment scripts.
> - **Persona priming** for `biased_debate`: prepend priming text to the prompt passed to each agent — not system prompt injection.

## Required Reading
- [design_decisions.md §4](../references/design_decisions.md#4-conditions-6) — 6 conditions table + compute accounting
- [design_decisions.md §5](../references/design_decisions.md#5-conditional-forced-multiround-gate) — conditional FM gate logic (also inlined below)
- [design_decisions.md §6](../references/design_decisions.md#6-persona-biased-debate) — persona priming text for biased_debate
- [hypotheses.md](../references/hypotheses.md) — what outputs are needed to test all 6 hypotheses
- [v5_mitigations.md](../references/v5_mitigations.md) — zero-variance check rationale (PM1 pattern)

## Key Constraints
- **Zero-variance contamination check:** after each batch, verify within-case variance > 0 across all 3 runs. Identical outputs across all 3 runs signals answer-key leakage.
- No answer-key fields (`ground_truth`, `scoring_targets`, `planted_issues`) passed to agents.
- Per-assessor `found` booleans must be stored in every output JSON for ensemble union IDR computation.
- `ETD_CONDITIONS = {'isolated_debate', 'multiround', 'conditional_fm', 'biased_debate'}` — ETD fires on mixed cases only for these conditions.

---

## Conditional FM Gate (inline — dispatch-time logic)

```
After round 1 adjudication:
  IF point_resolution_rate == 1.0  → STOP (all points resolved)
  ELIF adjudicator verdict matches both agents' round 1 stated positions → STOP
  ELSE → force round 2
```

Apply this gate per-case during `conditional_fm` dispatch.

---

## Steps

### 5.1 Confirm pre-run state
- `HYPOTHESIS.md` committed to git ✓
- `benchmark_cases_verified.json` exists with all required Schema B fields ✓
- Scoring engine changes from Phase 0 committed ✓
- Biased debate agent variants available in `pipeline/prompts/` ✓

### 5.2 Run all 6 conditions × N cases × 3 runs

**Execution:**
```bash
cd self_debate_experiment_v6 && uv run self_debate_poc.py --cases benchmark_cases_verified.json
```

**Per-condition dispatch protocol:**

**`baseline`:**
- Single-pass critique; no adversarial structure
- Agent receives `task_prompt` only — no ground truth fields
- Output stored as `v6_raw_outputs/{case_id}_baseline_run{idx}.json`

**`isolated_debate`:**
- Critic dispatched independently; Defender dispatched independently (neither sees the other)
- Orchestrator adjudicates both outputs
- Output: both `critic_raw` and `defender_raw` stored, plus adjudicator synthesis
- `all_issues_raised` from critic_raw; `all_issues_adjudicated` from adjudicator synthesis
- **Mixed-case adjudicator instruction (PRE-1):** When case `correct_position == 'mixed'`, the
  adjudicator prompt must include: "For this case, valid verdicts are: `critique_wins`,
  `defense_wins`, `empirical_test_agreed`. Use `empirical_test_agreed` when both sides have
  made substantive points that can only be resolved empirically." This applies to
  isolated_debate, biased_debate, multiround, and conditional_fm.

**`biased_debate`:**
- Same structure as `isolated_debate`
- Critic system prompt prepended with: *"You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and treat methodological gaps as real concerns until shown otherwise."*
- Defender system prompt prepended with: *"You are responding to a combative reviewer who frequently focuses on insignificant issues and overstates concerns. Be selective about what you concede."*
- Persona priming injected before dispatch; not stored in output (record priming hash only)

**`multiround`:**
- Defender sees Critic output; natural stopping up to 4 rounds
- Stop when: critic/defender agree, or 4 rounds reached
- All round transcripts stored

**`conditional_fm`:**
- Round 1: same as `multiround`
- After round 1 adjudication: apply the conditional FM gate (see inlined logic above)
- Force round 2 only if gate fires; otherwise stop
- Store `point_resolution_rate` per round and `gate_fired` boolean in output

**`ensemble_3x`:**
- 3 independent assessors (3 separate baseline-style runs, no cross-assessor visibility)
- Per-assessor `found` booleans stored for union IDR computation
- Final verdict: majority-vote (NOT union) — union only for IDR recall

### 5.3 Output schema validation after each batch
After completing each condition's batch, validate all output files:
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json, glob
files = glob.glob('v6_raw_outputs/*.json')
errors = []
for f in files:
    try:
        d = json.load(open(f))
        required = ['case_id','condition','run_idx','critic_raw','all_issues_raised','all_issues_adjudicated']
        for field in required:
            if field not in d:
                errors.append(f'{f}: missing {field}')
    except Exception as e:
        errors.append(f'{f}: {e}')
print(f'{len(errors)} errors across {len(files)} files' if errors else f'All {len(files)} files valid')
"
```

### 5.4 Zero-variance contamination check after each batch
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json, glob, collections
from itertools import groupby
files = glob.glob('v6_raw_outputs/*.json')
by_case_condition = collections.defaultdict(list)
for f in files:
    d = json.load(open(f))
    key = (d['case_id'], d['condition'])
    by_case_condition[key].append(d.get('verdict', None))
zero_variance = [(k, vs) for k, vs in by_case_condition.items()
                 if len(vs) == 3 and len(set(str(v) for v in vs)) == 1]
print(f'{len(zero_variance)} zero-variance cases (identical outputs across all 3 runs)')
if zero_variance:
    print('WARNING: identical outputs signal answer-key leakage')
    for k, v in zero_variance[:5]: print(f'  {k}: {v}')
"
```
If zero-variance cases found: halt, investigate leakage vector before continuing.

### 5.5 Expected volume
~120 cases × 6 conditions × 3 runs = **2,160 files**

---

## Verification
- [ ] Union IDR (IDR only): per-assessor `found` booleans stored in each ensemble output; majority-vote retained for verdict
- [ ] Zero-variance check run after each batch (identical outputs = leakage)
- [ ] Schema validation: all 2,160 output files pass before scoring

## Outputs
- `v6_raw_outputs/{case_id}_{condition}_run{idx}.json` (~2,160 files)

## Gate
All output files pass schema validation. Zero-variance check passes (no contamination detected).
