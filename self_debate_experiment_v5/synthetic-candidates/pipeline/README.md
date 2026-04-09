# Case Generation Pipeline

Generates synthetic ML benchmark cases for the v5 debate evaluation experiment. Each case is a proposed experiment design — sound or deliberately corrupted — with full ground truth metadata for scoring the debate protocol.

---

## Directory Layout

```
pipeline/
├── orchestrator.py          # Main entry point — runs all 5 stages end-to-end
├── select_cases.py          # Post-hoc stratified case selection
├── patch_smoke_scores.py    # Backfill smoke scores into an assembled batch
├── test_scoring.py          # Unit tests for IDR/IDP/FVC scoring logic
├── openrouter_models.json   # Available OpenRouter model catalog (reference)
├── prompts/
│   ├── stage1_hypothesis_generator.md    # Stage 1: generate hypothesis
│   ├── stage2_design_writer.md           # Stage 2: write sound experiment design
│   ├── stage3_corruption_node.md         # Stage 3: inject N flaws into design
│   └── stage4_ground_truth_assembler.md  # Stage 4: assemble case + ground truth
└── run/                     # Ephemeral per-run outputs (gitignored)
    ├── stage1/hypotheses.json            # All hypotheses for current batch
    ├── stage2/{mech_id}_design.json      # Per-case sound design
    ├── stage3/{mech_id}_corruption.json  # Per-case corruption report
    ├── stage4/{mech_id}.json             # Per-case assembled case
    └── stage5/{mech_id}_smoke.json       # Per-case smoke test scores
```

Assembled cases are written one level up (in `synthetic-candidates/`) as `cases_{start}-{end}.json`. The `run/` directory is cleared on each new batch.

---

## Prerequisites

- `uv` installed (`brew install uv` or see https://docs.astral.sh/uv/)
- `OPENROUTER_API_KEY` set — via `UV.env` in the repo root (loaded automatically by `uv run`) or exported in your shell
- All scripts use PEP 723 inline headers — run with `uv run`, never `python3`

---

## Generating Cases

### Basic batch

```bash
cd self_debate_experiment_v5/synthetic-candidates

uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 100 \
  --start-case-id 200
```

Writes `cases_200-299.json` when complete.

### With all options

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 100 \
  --start-case-id 200 \
  --seed 42              \  # RNG seed for corruption level sampling
  --concurrency 5        \  # Parallel workers (tune to API rate limits)
  --max-recycles 2          # Max retries per case on structural failure
```

### Resume an interrupted run

If the run was interrupted after some cases completed Stage 4, resume picks up where it left off:

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 100 \
  --start-case-id 200 \
  --resume
```

### Dry run (no API calls)

Verifies prompt construction and placeholder filling without spending tokens:

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 5 \
  --start-case-id 1 \
  --dry-run
```

### Override a model for a specific stage

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 20 \
  --start-case-id 1 \
  --stage3-model openai/o3
```

### Skip smoke test (debug Stages 2–4 only)

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/orchestrator.py \
  --batch-size 10 \
  --start-case-id 1 \
  --no-smoke
```

---

## Default Models

| Stage | Default | Role |
|-------|---------|------|
| Stage 1 | `openai/gpt-5.4-mini` | Hypothesis generation |
| Stage 2 | `anthropic/claude-haiku-4.5` | Sound design writer |
| Stage 3 | `openai/gpt-5.4` | Corruption node — keep powerful |
| Stage 4 | `qwen/qwen3-235b-a22b-2507` | Ground truth assembler |
| Smoke | `anthropic/claude-sonnet-4.6` | Smoke tester — calibrated to experiment baseline |
| Scorer | `openai/gpt-5.4-mini` | Smoke score extractor |

**Important:** Model IDs on OpenRouter use dot notation (e.g. `anthropic/claude-haiku-4.5`), not the native Anthropic API format (`anthropic/claude-haiku-4-5-20251001`).

---

## Selecting Cases Post-Hoc

After generating one or more batches, use `select_cases.py` to build a balanced subset for the experiment.

### Select with difficulty filter

Exclude cases where Sonnet found everything on the first pass (`proxy_mean` = 1.0 = too easy):

```bash
uv run pipeline/select_cases.py \
  --per-stratum 15 \
  --max-proxy 0.83
```

### Select by total N (balanced across strata)

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/select_cases.py \
  --n 60 \
  --seed 42
```

### Single batch

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/select_cases.py \
  --input cases_300-499.json \
  --per-stratum 15 \
  --max-proxy 0.83
```

### Auto-glob all batches (recommended)

No `--input` needed — the script globs `cases_*.json` from `synthetic-candidates/` automatically:

```bash
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/select_cases.py \
  --per-stratum 20 \
  --max-proxy 0.83 \
  --seed 42
```

Output: `selected_cases_all.json`

### Per-tier targets

Override the default `--per-stratum` for specific tiers, or skip a tier entirely with `0`:

```bash
# Fewer defense_wins, skip 3+ flaw cases
uv --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  run pipeline/select_cases.py \
  --per-stratum 25 \
  --tier-0 10 \
  --tier-many 0 \
  --max-proxy 0.83

# Only critique cases, custom targets per tier
uv run --env-file /Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/UV.env \
  pipeline/select_cases.py \
  --tier-0 0 \
  --tier-1 30 \
  --tier-2 20 \
  --tier-many 15 \
  --max-proxy 0.83
```

Tiers: `--tier-0` = defense_wins, `--tier-1` = 1-flaw critique, `--tier-2` = 2-flaw critique, `--tier-many` = 3+ flaw critique.

**Strata** are `(correct_verdict × corruption_tier)`:
- `defense_wins / 0 flaws`
- `critique / 1 flaw`
- `critique / 2 flaws`
- `critique / 3+ flaws`

Within each stratum, cases are ranked by `proxy_mean` ascending (hardest first) and interleaved across domains and ML task types.

---

## Backfilling Smoke Scores

If a batch was assembled before smoke score embedding was added to the pipeline, run this before the next batch clears `pipeline/run/`:

```bash
uv run pipeline/patch_smoke_scores.py --input cases_100-199.json
```

This reads Stage 5 output from `pipeline/run/stage5/` and embeds `proxy_mean` and `smoke_scores` into the assembled JSON in-place. Must be run while `pipeline/run/` still contains the relevant batch's outputs.

---

## Smoke Score Interpretation

Each case's `_pipeline` block contains:

```json
"_pipeline": {
  "proxy_mean": 0.0,
  "smoke_scores": {"IDR": 0.0, "IDP": 1.0, "FVC": 0.0}
}
```

| Metric | Meaning | Good = |
|--------|---------|--------|
| `IDR` | Issue Detection Recall — fraction of planted flaws Sonnet found | Low (Sonnet missed the flaw) |
| `IDP` | Issue Detection Precision — Sonnet didn't raise false alarms | High (Sonnet didn't invent problems) |
| `FVC` | Final Verdict Correctness — Sonnet's approve/critique matched ground truth | Low (Sonnet got the verdict wrong) |
| `proxy_mean` | Mean of applicable metrics | Low (Sonnet was wrong; case is hard) |

`defense_wins` cases target `proxy_mean ≈ 0.0`. Hard critique cases have `proxy_mean < 0.83`.
