# Case Generation Pipeline — Usage Guide

This pipeline replaces the monolithic `REAL_PAPER_CASE_GENERATION_PROMPT.md` with a multi-stage context-isolated workflow. The pipeline handles **generation only** — scoring and difficulty calibration use the existing smoke test process in `diagnostics/HAIKU_SMOKE_TEST_INSTRUCTIONS.md`.

---

## Why This Pipeline Exists

The monolithic prompt failed 5 consecutive smoke tests because the LLM that knows the answer writes the memo and evaluates it. The fix: context isolation at three boundaries.

- **Stage 3 (Memo Writer)** sees only scenario context and a shuffled fact list — no role codes, no flaw labels
- **Stage 5 (Leakage Auditor)** sees only the memo — no answer key, no category, no flaw taxonomy  
- **Stage 4 (Metadata Assembler)** has the full answer key but did NOT write the memo

---

## Directory Structure

```
pipeline/
  prompts/
    stage1_mechanism_extractor.md   # Stage 1 for real paper transpositions
    stage1_benchmark_extractor.md   # Stage 1 for benchmark category cases
    stage2_scenario_architect.md    # Designs the scenario brief
    stage3_memo_writer.md           # Writes the team advocacy memo
    stage4_metadata_assembler.md    # Constructs the answer key
    stage5_leakage_auditor.md       # Evaluates memo for leakage (blind)
  fact_mixer.py                     # Stage 1.5: shuffles facts, strips role labels
  orchestrator.py                   # Automated end-to-end runner (all stages via OpenRouter)
  trigger_phrase_list.md            # Reference: banned constructions for Stage 3
  PIPELINE_USAGE.md                 # This file
```

---

## Automated Mode (Recommended)

Run all stages end-to-end with a single command:

```bash
cd self_debate_experiment_v5/synthetic-candidates
OPENROUTER_API_KEY=your_key uv run pipeline/orchestrator.py \
  --extractor-source real_paper \
  --batch-size 15 \
  --start-case-id 310
```

Output file is named automatically by case ID range: `cases_310-324.json`.

The orchestrator runs Stages 1–6 automatically, including:
- Auto-recycling cases that fail the leakage audit (up to `--max-recycles` attempts)
- Smoke test (Stage 6) against a configurable model
- Final batch assembly filtering to `verifier_status: "pending"` cases only

### Key options

| Option | Default | Description |
|---|---|---|
| `--max-recycles N` | 2 | Max recycle attempts per case |
| `--no-smoke` | off | Skip Stage 6 smoke test |
| `--resume` | off | Skip cases with existing Stage 4 output |
| `--dry-run` | off | Print prompts without API calls |
| `--stage1-model MODEL` | `google/gemini-2.5-pro` | Override Stage 1 model |
| `--stage5-model MODEL` | `anthropic/claude-sonnet-4.6` | Override Stage 5 model |
| `--smoke-model MODEL` | `anthropic/claude-haiku-4.5` | Override smoke test model |
| `--models JSON` | — | Batch-override multiple models |

All models are OpenRouter model strings. Use different models for Stage 1 and Stage 5 to avoid circular bias (generator and auditor sharing the same priors).

---

## Running the Pipeline

### Choosing a Stage 1 extractor

| Use case | Stage 1 prompt |
|---|---|
| Real paper transpositions | `prompts/stage1_mechanism_extractor.md` |
| Benchmark category cases | `prompts/stage1_benchmark_extractor.md` |

Stages 2–5, `fact_mixer.py`, and the smoke test are identical for both. The only change is which Stage 1 prompt you run. Each extractor stamps `pipeline_source` into its output; `fact_mixer.py` validates this field and will error if blueprints from different extractors are mixed in the same batch.

---

### Step 1 — Generate mechanism blueprints (Stage 1)

Fill the placeholders in the appropriate Stage 1 prompt (`stage1_mechanism_extractor.md` or `stage1_benchmark_extractor.md`) and instruct an agent to read the file and execute it:
- `{{EXTRACTOR_SOURCE}}`: `real_paper` or `benchmark` — matches the prompt you chose above
- `{{BATCH_SIZE}}`: number of cases (e.g., 15)
- `{{BATCH_NUMBER}}`: sequential batch number for this run (e.g., 4)
- `{{PREVIOUS_BATCH_USAGE}}`: JSON of sources/domains already used, or `{}`

Save the JSON output to `pipeline/run/stage1_blueprints.json`.

### Step 2 — Run Fact Mixer (Stage 1.5)

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run pipeline/fact_mixer.py \
  --input pipeline/run/stage1_blueprints.json \
  --output-dir pipeline/run/stage1.5/ \
  --seed 42 \
  --expected-source {{EXTRACTOR_SOURCE}}
```

Set `{{EXTRACTOR_SOURCE}}` to `real_paper` or `benchmark` to match the Stage 1 prompt you used. `--expected-source` is optional but recommended — it catches the case where the wrong extractor was run before you invest time in Stages 2–5.

Produces per-case `writer_view` (no role labels) and `metadata_view` (with role labels) files.

**Steps 3–5 run once per case.** In all file paths below, replace `NNN` with the zero-padded mechanism number from the `mechanism_id` field in the Stage 1 output (e.g., `mech_001`, `mech_002`). For `{{CASE_ID}}`, assign `eval_scenario_NNN` using the next available case number — check the highest existing `case_id` in `benchmark_cases.json` and increment from there (batch3 ended at `eval_scenario_309`, so the next batch starts at `eval_scenario_310`).

### Step 3 — Scenario Architect (Stage 2, one per case)

Fill the placeholders in `prompts/stage2_scenario_architect.md` and instruct an agent to read the file and execute it:
- `{{TARGET_DOMAIN}}`, `{{DOMAIN_SPECIFIC_DETAIL}}`, `{{CATEGORY}}` — from the `mech_NNN_writer_view.json` fields of the same name
- `{{WRITER_VIEW_FACTS}}` — the `facts` array from `mech_NNN_writer_view.json`

Save output to `pipeline/run/stage2/mech_NNN_scenario.json`.

### Step 4 — Memo Writer (Stage 3, one per case)

Fill the placeholder in `prompts/stage3_memo_writer.md` and instruct an agent to read the file and execute it:
- `{{SCENARIO_BRIEF}}` — full JSON from `pipeline/run/stage2/mech_NNN_scenario.json`

Save the memo text to `pipeline/run/stage3/mech_NNN_memo.txt`.

### Step 5 — Run Stages 4 and 5 in parallel (one per case)

**Stage 5 first (keeps it truly blind):**

Fill the placeholder in `prompts/stage5_leakage_auditor.md` and instruct an agent to read the file and execute it:
- `{{TASK_PROMPT}}` — memo text from `pipeline/run/stage3/mech_NNN_memo.txt`

Save to `pipeline/run/stage5/mech_NNN_audit.json`.

**Stage 4:**

Fill the placeholders in `prompts/stage4_metadata_assembler.md` and instruct an agent to read the file and execute it:
- `{{MECHANISM_BLUEPRINT}}` — full JSON from `pipeline/run/stage1.5/mech_NNN_metadata_view.json`
- `{{METADATA_VIEW}}` — same file
- `{{LEAKAGE_AUDIT}}` — full JSON from `pipeline/run/stage5/mech_NNN_audit.json`
- `{{TASK_PROMPT}}` — memo text from `pipeline/run/stage3/mech_NNN_memo.txt`
- `{{CASE_ID}}` — the case ID assigned for this mechanism (e.g., `eval_scenario_401`)

Save to `pipeline/run/cases/mech_NNN.json`.

### Step 6 — Assemble final batch

Replace `{{START_ID}}` and `{{END_ID}}` with the actual case ID range (e.g., `310` and `324`):

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run python -c "
import json, glob
cases = [json.load(open(f)) for f in sorted(glob.glob('pipeline/run/cases/*.json'))
         if '_attempt_' not in f]
print(f'{len(cases)} cases assembled')
json.dump(cases, open('cases_{{START_ID}}-{{END_ID}}.json', 'w'), indent=2)
"
```

### Step 7 — Run smoke test

Follow `diagnostics/HAIKU_SMOKE_TEST_INSTRUCTIONS.md`.  
Gate: ≥9/14 hard cases scoring mean < 0.55.

For cases that fail: re-run the relevant stage with a note explaining the failure mode (see Recycling Guide below).

---

## Recycling Guide

When the smoke test shows a case failing the gate, route it back manually:

| Symptom | Route back to | Note to include |
|---------|--------------|-----------------|
| IDR=1.0, case too easy | Stage 1 | "Use different source or deeper transposition" |
| Leakage auditor finds reviewer voice | Stage 2 | "New scenario approach — current framing signals the flaw" |
| FVC=1.0 but IDR failed | Stage 2 | "Restructure decoy placement — verdict readable without finding flaw" |
| MISSING_FLAW_FACT in Stage 4 notes | Stage 2 | "Re-emphasize missing fact in scenario brief" |

---

## Troubleshooting

**fact_mixer.py validation errors:**
- `missing flaw_facts` — Stage 1 output is missing the `flaw_facts` array
- `addressed_but_incorrectly_fact_id not in flaw_facts` — ABI fact ID mismatch
- `compound_fact_ids must have ≥2 entries` — need at least 2 compound facts

**Stage 5 finds `voice_assessment != team_advocacy`:**  
Route to Stage 3 with: "Rewrite entirely in first-person team voice. No 'the team', 'the document', or third-person framing anywhere."

**All critique/mixed cases ceiling at IDR=1.0:**  
Route to Stage 1 with: "Flaw facts are too recognizable. Embed the mechanism 2+ layers deep in field-specific terminology."
