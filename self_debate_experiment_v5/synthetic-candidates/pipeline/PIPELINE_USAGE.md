# Case Generation Pipeline — Usage Guide

This pipeline replaces the monolithic `REAL_PAPER_CASE_GENERATION_PROMPT.md` with a 7-stage context-isolated workflow. Three execution modes are supported.

---

## Why This Pipeline Exists

The monolithic prompt failed 5 consecutive smoke tests because the LLM that knows the answer writes the memo and evaluates it. The key insight: if the memo writer doesn't know which facts are flaws, it can't signal the answer.

This pipeline enforces that:
- **Stage 3 (Memo Writer)** sees only scenario context and methodology facts — no role codes, no flaw labels
- **Stage 5 (Leakage Auditor)** sees only the memo — no answer key, no categories, no flaw taxonomy
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
  orchestrator.py                   # Stage 7: scores, routes, assembles final batch
  trigger_phrase_list.md            # Reference: banned constructions for Stage 3
  PIPELINE_USAGE.md                 # This file
  stage1_output/                    # Created during run
  stage1.5/                         # Created by fact_mixer.py
  stage2/                           # Created during run
  stage3/                           # Created during run
  stage4/                           # Created during run (complete case JSONs)
  stage5/                           # Created during run (leakage audit reports)
  cases/                            # Accepted cases (input to score-only mode)
```

---

## Mode A — Manual (Copy/Paste to External LLM)

Best for: initial use, testing with any LLM, debugging individual stages

### Step 1: Generate mechanism blueprints (Stage 1)

1. Open `prompts/stage1_mechanism_extractor.md`
2. Fill in the placeholders at the bottom:
   - `{{BATCH_SIZE}}`: number of cases (e.g., 15)
   - `{{PREVIOUS_BATCH_USAGE}}`: JSON of sources/domains already used, or `{}`
3. Paste the full prompt into your external LLM (GPT-4o, Gemini Pro, etc.)
4. Save the JSON output to `pipeline/stage1_output/blueprints.json`

### Step 2: Run Fact Mixer (Stage 1.5)

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run pipeline/fact_mixer.py \
  --input pipeline/stage1_output/blueprints.json \
  --output-dir pipeline/stage1.5/ \
  --seed 42
```

This produces per-case files in `pipeline/stage1.5/`:
- `mech_001_writer_view.json` — facts without role labels (for Stages 2-3)
- `mech_001_metadata_view.json` — facts with role labels (for Stage 4)

### Step 3: For each case — Scenario Architect (Stage 2)

1. Open `prompts/stage2_scenario_architect.md`
2. Fill in the placeholders from the writer view file:
   - `{{TARGET_DOMAIN}}`: from `writer_view.target_domain`
   - `{{DOMAIN_SPECIFIC_DETAIL}}`: from `writer_view.domain_specific_detail`
   - `{{CATEGORY}}`: from `writer_view.category`
   - `{{WRITER_VIEW_FACTS}}`: paste the `facts` array from `mech_001_writer_view.json`
3. Paste the filled prompt into your LLM
4. Save the JSON output to `pipeline/stage2/mech_001_scenario.json`

### Step 4: For each case — Memo Writer (Stage 3)

1. Open `prompts/stage3_memo_writer.md`
2. Fill in `{{SCENARIO_BRIEF}}` with the full JSON from Stage 2 output
3. Paste the filled prompt into your LLM
4. Save the memo text to `pipeline/stage3/mech_001_memo.txt`

### Step 5: For each case — Run Stages 4 and 5 in parallel

**Stage 5 (Leakage Auditor) — do this first to be truly blind:**
1. Open `prompts/stage5_leakage_auditor.md`
2. Fill in `{{TASK_PROMPT}}` with the memo from Stage 3
3. Paste into your LLM
4. Save the JSON output to `pipeline/stage5/mech_001_audit.json`

**Stage 4 (Metadata Assembler):**
1. Open `prompts/stage4_metadata_assembler.md`
2. Fill in:
   - `{{MECHANISM_BLUEPRINT}}`: full metadata view from `pipeline/stage1.5/mech_001_metadata_view.json`
   - `{{METADATA_VIEW}}`: same file
   - `{{LEAKAGE_AUDIT}}`: the Stage 5 JSON output
   - `{{TASK_PROMPT}}`: the memo text from Stage 3
   - `{{CASE_ID}}`: assign an opaque ID like `eval_scenario_315`
3. Paste into your LLM
4. Save the JSON output to `pipeline/cases/mech_001.json`

### Step 6: Score and assemble (Stages 6+7)

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run pipeline/orchestrator.py \
  --mode score-only \
  --cases-dir pipeline/cases/ \
  --output pipeline/batch_output.json
```

This runs each case through Haiku (requires `ANTHROPIC_API_KEY`), applies the 4-dimension proxy rubric, routes rejected cases (printed to console), and writes accepted cases to `batch_output.json`.

### Step 7: Copy accepted cases to synthetic-candidates

```bash
# Review batch_output.json, then copy accepted cases:
cp pipeline/batch_output.json real_paper_cases_batchN.json
```

---

## Mode B — API Automation (Python + External LLM API)

Best for: unattended end-to-end generation with OpenAI or other APIs

### Prerequisites

```bash
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

### Current state

The orchestrator.py `--mode auto` is a scaffold. The Stage 6 Haiku scoring is fully implemented (using `anthropic` SDK). The Stage 1-5 LLM calls use the prompt templates in `prompts/` but require you to wire in your preferred API client.

**Recommended implementation pattern:**
```python
# Pseudo-code for Stage 1 API call
prompt_text = Path("pipeline/prompts/stage1_mechanism_extractor.md").read_text()
prompt_text = prompt_text.replace("{{BATCH_SIZE}}", "15")
prompt_text = prompt_text.replace("{{PREVIOUS_BATCH_USAGE}}", "{}")

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt_text}],
    response_format={"type": "json_object"},
)
blueprints = json.loads(response.choices[0].message.content)
```

Each stage follows the same pattern: read prompt template, fill placeholders, call API, parse JSON output.

---

## Mode C — Claude Code Subagents

Best for: running within Claude Code with subagent dispatch

### Generate dispatch instructions

```bash
cd self_debate_experiment_v5/synthetic-candidates
uv run pipeline/orchestrator.py \
  --mode claude-code \
  --batch-size 15
```

This prints step-by-step subagent dispatch instructions tailored to the batch size and prompt paths.

### Model recommendations per stage

| Stage | Recommended model | Reason |
|-------|------------------|--------|
| Stage 1 — Mechanism Extractor | `opus` or `sonnet` | Complex library reasoning, diversity constraints |
| Stage 2 — Scenario Architect | `sonnet` | Domain design, moderate complexity |
| Stage 3 — Memo Writer | `sonnet` | Writing quality matters; shorter context |
| Stage 4 — Metadata Assembler | `opus` or `sonnet` | Careful schema construction, cross-referencing |
| Stage 5 — Leakage Auditor | `sonnet` | Must be blind; fresh context is critical |
| Stage 6 — Difficulty Scorer | `haiku` | Matches the gate calibration model |

---

## Recycling Guide

When Stage 7 rejects a case, it routes it back with a reason and route:

| Route | Meaning | Action |
|-------|---------|--------|
| `stage1` | Flaw too findable OR decoys not tempting | Regenerate mechanism blueprint with different source or stronger decoy facts |
| `stage2` | Verdict leakage OR voice issues in memo | Regenerate scenario brief with different framing |
| `stage3` | (rare) Memo writer missed a critical fact | Regenerate memo with fact emphasized |

Maximum 3 recycling loops per case before escalating to operator.

---

## Smoke Test After Generation

After assembling `batch_output.json`:

1. Move accepted cases to `synthetic-candidates/real_paper_cases_batchN.json`
2. Re-run preflight to merge with `benchmark_cases.json`:
   ```bash
   cd self_debate_experiment_v5
   /preflight
   ```
3. Run the Haiku smoke test per `diagnostics/HAIKU_SMOKE_TEST_INSTRUCTIONS.md`
4. Gate: ≥9/14 hard cases scoring mean < 0.55

---

## Troubleshooting

**fact_mixer.py validation errors:**
- `missing flaw_facts` → Stage 1 output missing `flaw_facts` array for this case
- `addressed_but_incorrectly_fact_id not in flaw_facts` → The ABI fact ID doesn't match any flaw fact
- `compound_fact_ids must have ≥2 entries` → Need at least 2 facts that together reveal the flaw

**Memo reads in reviewer voice (Stage 5 finds voice_assessment != team_advocacy):**
- Route back to Stage 3 with note: "Rewrite in first-person team voice throughout. Do not use 'the team', 'the document', or any third-person framing."

**Haiku scores IDR=1 on all cases (gate FAIL, all ceiling):**
- The flaw facts in Stage 1 are still too recognizable. Use Stage 1 again with a note: "Provide more domain-specific operational noise. The abstract mechanism must be embedded 2+ layers deep in field-specific terminology."

**Stage 4 flags MISSING_FLAW_FACT:**
- The memo writer didn't include a flaw-bearing fact. Route to Stage 2 for a new scenario brief that makes the missing fact more central to the methodology.
