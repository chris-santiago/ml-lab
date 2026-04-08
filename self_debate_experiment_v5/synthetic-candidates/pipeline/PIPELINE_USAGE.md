# Case Generation Pipeline — Usage Guide

This pipeline replaces the monolithic `REAL_PAPER_CASE_GENERATION_PROMPT.md` with a 7-stage context-isolated workflow. The pipeline handles **generation only** — scoring and difficulty calibration use the existing smoke test process in `diagnostics/HAIKU_SMOKE_TEST_INSTRUCTIONS.md`.

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
    stage1_mechanism_extractor.md   # Selects flaw mechanisms, produces blueprints
    stage2_scenario_architect.md    # Designs the scenario brief
    stage3_memo_writer.md           # Writes the team advocacy memo
    stage4_metadata_assembler.md    # Constructs the answer key
    stage5_leakage_auditor.md       # Evaluates memo for leakage (blind)
  fact_mixer.py                     # Stage 1.5: shuffles facts, strips role labels
  trigger_phrase_list.md            # Reference: banned constructions for Stage 3
  PIPELINE_USAGE.md                 # This file
```

---

## Running the Pipeline

### Step 1 — Generate mechanism blueprints (Stage 1)

Paste `prompts/stage1_mechanism_extractor.md` into your LLM with placeholders filled:
- `{{BATCH_SIZE}}`: number of cases (e.g., 15)
- `{{PREVIOUS_BATCH_USAGE}}`: JSON of sources/domains already used, or `{}`

Save the JSON output to `pipeline/run/stage1_blueprints.json`.

### Step 2 — Run Fact Mixer (Stage 1.5)

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run pipeline/fact_mixer.py \
  --input pipeline/run/stage1_blueprints.json \
  --output-dir pipeline/run/stage1.5/ \
  --seed 42
```

Produces per-case `writer_view` (no role labels) and `metadata_view` (with role labels) files.

### Step 3 — Scenario Architect (Stage 2, one per case)

Paste `prompts/stage2_scenario_architect.md` with placeholders from the writer view:
- `{{TARGET_DOMAIN}}`, `{{DOMAIN_SPECIFIC_DETAIL}}`, `{{CATEGORY}}` — from `writer_view` fields
- `{{WRITER_VIEW_FACTS}}` — the `facts` array from `mech_NNN_writer_view.json`

Save output to `pipeline/run/stage2/mech_NNN_scenario.json`.

### Step 4 — Memo Writer (Stage 3, one per case)

Paste `prompts/stage3_memo_writer.md` with:
- `{{SCENARIO_BRIEF}}` — full JSON from Stage 2 output

Save the memo text to `pipeline/run/stage3/mech_NNN_memo.txt`.

### Step 5 — Run Stages 4 and 5 in parallel (one per case)

**Stage 5 first (keeps it truly blind):**

Paste `prompts/stage5_leakage_auditor.md` with:
- `{{TASK_PROMPT}}` — memo text from Stage 3

Save to `pipeline/run/stage5/mech_NNN_audit.json`.

**Stage 4:**

Paste `prompts/stage4_metadata_assembler.md` with:
- `{{MECHANISM_BLUEPRINT}}` — full metadata view from `mech_NNN_metadata_view.json`
- `{{METADATA_VIEW}}` — same file
- `{{LEAKAGE_AUDIT}}` — Stage 5 JSON output
- `{{TASK_PROMPT}}` — memo text from Stage 3
- `{{CASE_ID}}` — assign `eval_scenario_NNN`

Save to `pipeline/run/cases/mech_NNN.json`.

### Step 6 — Assemble final batch

```bash
cd self_debate_experiment_v5/synthetic-candidates
python3 -c "
import json, glob
cases = [json.load(open(f)) for f in sorted(glob.glob('pipeline/run/cases/*.json'))]
print(f'{len(cases)} cases assembled')
json.dump(cases, open('real_paper_cases_batchN.json', 'w'), indent=2)
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
