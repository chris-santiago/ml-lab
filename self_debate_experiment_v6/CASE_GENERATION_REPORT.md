# Case Generation Methodology Report

> **Note:** Frozen snapshot — case generation methodology is locked per experiment version. Not updated by artifact-sync.

## ml-lab v6 Synthetic and RC Benchmark Pipeline

**Status:** Active — Phase 3 complete; benchmark finalized as of 2026-04-11
**Regular synthetic batch:** `pipeline/run/stage2/` + `pipeline/run/stage3/` (80 cases)
**RC extraction output:** `pipeline/run/rc_candidates/rc_cases_raw.json` (75 cases)
**Pipeline entry point:** `pipeline/orchestrator.py` (synthetic) · `pipeline/rc_extractor.py` (RC)

For v5 case generation methodology, see `self_debate_experiment_v5/CASE_GENERATION_REPORT.md`.
This document describes only what is new or changed in v6.

---

## 1. Motivation

v5 generated a 110-case benchmark from entirely synthetic planted-corruption designs and the
primary hypothesis failed with a ceiling effect: baseline FC = 0.9452, leaving only ~0.05
headroom against a +0.10 threshold. Post-mortems identified three structural problems specific
to the synthetic case generation approach:

1. **Corruption detection is not methodology review.** Planted corruptions are known-legible
   bugs with exact ground truth. The protocol's actual use case — real methodology review —
   involves implicit, arguable, or combinatorial flaws where adversarial structure should add
   the most value. A benchmark built on planted corruptions measures a different task.

2. **No mixed cases.** The one dimension where v3 showed genuine debate advantage (+0.365 lift)
   was ETD — helping agents specify empirical tests for genuinely ambiguous decisions. v5 removed
   ETD entirely by having no mixed cases, making the primary lift signal necessarily ETD-free.

3. **Closed-loop calibration confound.** The v5 smoke test used Claude Sonnet (the main
   experiment model) to calibrate case difficulty. `proxy_mean` did not predict rubric
   performance (Spearman ρ = +0.046), suggesting that same-model calibration does not generalize
   to independent evaluation.

v6 addresses all three by replacing the purely synthetic benchmark with a three-pipeline
convergence: **RC extraction** (real reproducer-documented flaws), **synthetic regular** (planted
corruptions, extended from v5), and **synthetic mixed** (empirically contingent choices, new in v6).

---

## 2. Design Goals

The v6 case library must satisfy these constraints, in addition to the v5 constraints
(methodological correctness, difficulty, plausibility, ground truth completeness, coverage breadth,
and prospective voice):

7. **Real-world flaw validity** — cases derived from RC reports must measure *methodology review
   recall*, not corruption detection. Ground truth comes from an independent reproducer who did not
   know the answer in advance.

8. **ETD testability** — the benchmark must include genuinely ambiguous cases where the correct
   debate outcome is a well-specified empirical test, not a verdict. Mixed cases require a concrete
   measurement protocol in the ground truth.

9. **Cross-family smoke calibration** — difficulty calibration must not use the same model family
   as the design writer. Same-family RLHF conventions inflate or deflate proxy scores in ways that
   do not predict cross-family rubric performance.

10. **Source-independent normalization** — all three pipelines (RC, synthetic regular, synthetic
    mixed) must produce the same Schema B output before case selection. The downstream scoring
    engine must be source-agnostic.

---

## 3. Architecture

### 3.1 Three-Pipeline Convergence

Three independent pipelines converge at `normalize_cases.py` to produce unified Schema B, which
is then filtered by `select_cases.py`:

```
RC Extraction Pipeline          Synthetic Regular Pipeline      Synthetic Mixed Pipeline
─────────────────────────────   ─────────────────────────────   ────────────────────────
RC-1: Fetch (OpenReview + ReScience)
RC-2: Flaw extraction (GPT-4o)  Stage 1: Hypothesis gen         Stage 1: Hypothesis gen
RC-3: must_not_claim (GPT-4o)   Stage 2: Sound design writer    Stage 2M: Ambiguous design
RC-4: Filtering + contam. gate  Stage 3: Corruption node         Stage 3M: Ground truth assembly
                                Stage 4: Ground truth assembly
                                Stage 5: Smoke validation         [no smoke test]
         ↓                               ↓                                ↓
  rc_cases_raw.json          cases_NNN-MMM.json               cases_NNN-MMM.json
         ↓                               ↓                                ↓
         └────────────────── normalize_cases.py ───────────────────────────┘
                                         ↓
                                  benchmark_cases_raw.json
                                         ↓
                              select_cases.py (Phase 3 pilot gating)
                                         ↓
                              benchmark_cases_verified.json
```

The three pipelines share Stage 1 (hypothesis generation), which is called once per batch for
the full count of regular + mixed cases. RC cases do not use hypothesis generation — they derive
their hypothesis and domain from the original paper's title and abstract.

### 3.2 Phase 1 Decision Gate

After RC extraction completes, a yield check determines how much synthetic supplementation is
needed:

| RC yield | Action |
|---|---|
| regular >= 60 AND mixed >= 20 | Use RC exclusively |
| regular >= 60, mixed < 20 | Supplement mixed with synthetic pipeline |
| regular < 60 | Supplement regular cases with synthetic |
| RC total < 30 | Full synthetic fallback |

Current outcome (Phase 1 complete): 22 critique + 45 mixed + 8 defense = 75 RC cases.
This triggers the third row — regular (critique) is below 60, requiring synthetic supplement.
The RC mixed yield (45) exceeds the 40-case target, so no synthetic mixed supplement is needed.

### 3.3 Corruption Level Distribution (Synthetic Regular Only)

Corruption counts are sampled by Python before Stage 3 is called. The distribution and sampling
logic are identical to v5:

```python
CORRUPTION_LEVELS = [0, 1, 2, "many"]
CORRUPTION_PROBS  = [0.25, 0.35, 0.25, 0.15]
```

Actual distribution across the 80-case regular synthetic batch:

| Level | Target (N=80) | Actual |
|-------|--------------|--------|
| 0 corruptions | ~20 | 24 |
| 1 corruption | ~28 | 24 |
| 2 corruptions | ~20 | 23 |
| "many" (3–5) | ~12 | 9 |

Variance from target is expected at N=80 and is within normal sampling range.

### 3.4 Model Selection

v6 updates the model configuration from v5. The key change is the smoke model:

| Stage | v5 Model | v6 Model | Rationale |
|-------|---------|---------|-----------|
| Stage 1 | `openai/gpt-5.4-mini` | `openai/gpt-4o-mini` | OpenRouter ID update |
| Stage 2 | `anthropic/claude-haiku-4.5` | `anthropic/claude-haiku-4-5` | OpenRouter ID format |
| Stage 3 | `openai/gpt-5.4` | `openai/gpt-4o` | OpenRouter ID update |
| Stage 4 | `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b-2507` | Unchanged |
| Stage 5 (smoke) | `anthropic/claude-sonnet-4.6` | `google/gemini-2.5-flash` | **Family change — see note** |
| Scorer | `openai/gpt-5.4-mini` | `openai/gpt-4o-mini` | OpenRouter ID update |
| RC-2/RC-3 | N/A | `openai/gpt-4o` | New RC pipeline |
| Stage 2M | N/A | `openai/gpt-4o` | New mixed pipeline; needs strong reasoning |
| Stage 3M | N/A | `qwen/qwen3-235b-a22b-2507` | New mixed pipeline; structured JSON assembly |

**Smoke model family change (critical):** Stage 2 uses Claude Haiku to write designs. The v5
smoke model was Claude Sonnet. Because both share Anthropic RLHF fine-tuning conventions, Sonnet
is more likely to approve or critique in ways that align with Haiku's output patterns — creating
same-family calibration bias. v5 PM3 (proxy_mean → rubric performance Spearman ρ = +0.046)
confirmed this bias is real. Gemini 2.5 Flash is a cross-family evaluator with independent
calibration, breaking the RLHF dependency.

Note on OpenRouter model IDs: v5 §6.2 documented that OpenRouter uses dot notation for Anthropic
models (`anthropic/claude-haiku-4.5`). The v6 orchestrator uses dash notation
(`anthropic/claude-haiku-4-5`). The 80-case batch ran successfully with this format, suggesting
both are accepted by the current OpenRouter API — but verify against the model catalog if a
future batch returns HTTP 400 on Stage 2 calls.

---

## 4. Stage-by-Stage Design

### 4.1 RC Extraction Pipeline (Entirely New)

The RC pipeline does not use the hypothesis generation or corruption infrastructure. It extracts
real methodology flaws from published ML Reproducibility Challenge reports.

**RC-1 — Fetch:** Queries the OpenReview API v2 for submissions across RC editions (2020–2023),
trying multiple venue invitation patterns per year (12 patterns total across 4 years). Also fetches
the ReScience MLRC GitHub repository via the GitHub API. Output: `rc_candidates/reports_fetched.json`.

Current yield: 80 reports fetched across both sources.

**RC-2 — Flaw extraction:** GPT-4o reviews each report and extracts structured methodology flaws,
producing a `ground_truth_type` classification (`critique`, `defense`, `mixed`, or `none`) and
a `planted_issues` array for critique cases. The extraction prompt explicitly separates "what the
paper claims" from "what the reproducer found" — this separation is the primary contamination
prevention step.

Current yield: 80 records with the following ground_truth_type distribution:
- `mixed`: 45 (reproducer found a contestable or overstated claim)
- `critique`: 22 (reproducer documented a clear methodology flaw)
- `defense`: 8 (reproducer confirmed the paper's methodology)
- `none` / `unknown`: 5 (no usable flaw found)

**RC-3 — must_not_claim extraction:** A separate GPT-4o pass identifies sound design choices
in the original paper that a pattern-matching reviewer might wrongly challenge. These become
the `must_not_claim` entries, enabling IDP scoring. This is a distinct call from RC-2 because
it requires a different reasoning task: not "what did the reproducer find" but "what in this
design is correct and would a reviewer unfairly challenge it?"

Current yield: 75 records (5 dropped from RC-2 output during must_not_claim extraction).

**RC-4 — Filtering + contamination gate:** Applies exclusion criteria from `DATA_ACQUISITION.md`
and rejects any case where `task_prompt` contains reproducer-language keywords. This gate is
the structural analog of the v5 PM1 fix — PM1 contaminated IDR scoring by leaking answer keys
through the orchestrator context window; the RC contamination gate prevents the same pattern
from leaking through the data channel.

The 10 contamination keywords rejected:
```
"we found that"          "failed to reproduce"         "the reported results"
"our reproduction"       "could not replicate"          "we were unable to"
"reproduction failed"    "reproducer found"             "reproducibility report"
"could not be reproduced"
```

Additional exclusion reasons: no documented root cause, environment/compute failures only,
flaw description too vague (< 2 sentence equivalent), implementation bug in released code,
extraction failure.

Current yield: 75 cases pass RC-4 (from 80 fetched).

### 4.2 Stage 1 — Hypothesis Generator (Shared)

Unchanged from v5 in behavior. The hypothesis generator now runs for a combined count of regular
+ mixed cases in a single ThreadPoolExecutor pass: for a batch of 80 regular + 40 mixed, 120
hypotheses are generated concurrently. The first 80 are assigned to the regular pipeline; the
last 40 to the mixed pipeline.

Current batch: 120 hypotheses generated (80 regular + 40 mixed), spanning diverse ML task types
and domains with collision avoidance via threading lock.

### 4.3 Stage 2 — Sound Design Writer (Unchanged)

Produces a methodologically sound design from the Stage 1 hypothesis. Behavior is identical to
v5 — this stage is not modified in v6. The Stage 2 output feeds directly into the corruption node
(Stage 3) for regular cases, or is bypassed entirely for mixed cases which use Stage 2M instead.

Current status: 80 Stage 2 design files produced.

### 4.4 Stage 3 — Corruption Node (Unchanged)

Nine-type flaw taxonomy, six requirements per corruption, and the self-check before finalizing
are all unchanged from v5. See v5 CASE_GENERATION_REPORT.md §4.3 for the full specification.

Current status: 80 Stage 3 corruption files produced, with the corruption distribution shown in §3.3.

### 4.5 Stage 4 — Ground Truth Assembler (Regular Path, Unchanged)

Unchanged from v5. Produces `planted_issues`, `must_find_issue_ids`, `must_not_claim`, and
`acceptable_resolutions` metadata from the Stage 2 sound design and Stage 3 corruption report.

### 4.6 Stage 5 — Smoke Test (Model Changed)

The smoke test structure and scoring logic are unchanged from v5 (IDR, IDP, FVC, proxy_mean,
gate_pass). The model is changed from Claude Sonnet to Gemini 2.5 Flash (see §3.4).

**Critical change from v5:** `proxy_mean` is embedded in `_pipeline` metadata for traceability
but is **not used as a difficulty gate input** in `select_cases.py`. PM3 established that
same-model proxy scores do not predict cross-model rubric performance. Difficulty is now set
in Phase 3 using GPT-4o pilot scoring, not proxy filtering.

Smoke tests apply only to regular synthetic cases. Mixed cases have no smoke test — a binary
approve/critique verdict does not apply to empirically contingent designs.

### 4.7 Stage 2M — Ambiguous Design Writer (New)

Produces a methodologically sound design with exactly **one empirically contingent design choice**
— a decision that is genuinely defensible, genuinely challengeable, and unresolvable from the
design document alone without measurement. Uses a 6-type taxonomy of ambiguity:

| Type | Core Pattern |
|------|-------------|
| `split_ambiguity` | Stratified random split on data with plausible but unconfirmed temporal structure |
| `metric_ambiguity` | Rank metric appropriate for task type but potentially misaligned with tail-threshold operational objective |
| `complexity_ambiguity` | Model capacity appropriate for stated data size but unknown interaction structure |
| `lookback_ambiguity` | Fixed behavioral lookback window of unknown predictive horizon |
| `proxy_ambiguity` | Proxy outcome strongly correlated with target but diverges at conversion tail |
| `regularization_ambiguity` | Regularization strength chosen by convention; optimal depends on actual signal-to-noise |

The key design constraint: the ambiguous choice must appear as a **confident, reasoned engineering
decision** in the narrative — not hedged, not flagged, not presented as uncertain. The critic must
have to reason through the full methodology logic to locate the contestable dimension, not scan
for named anti-patterns or explicit hedges.

Output includes `structured_choices`, `design_narrative`, and a machine-readable `ambiguous_choice`
block containing `taxonomy_type`, `targeted_dimension`, `defensible_rationale`,
`legitimate_challenge`, and `empirical_condition`. The `ambiguous_choice` block is consumed by
Stage 3M; debate agents never see it.

A four-item self-check enforces: confidence framing, non-trivial challenge, non-trivial defense,
and concrete empirical condition specificity.

### 4.8 Stage 3M — Mixed Ground Truth Assembler (New)

Assembles the ground truth for mixed cases. Unlike Stage 4 (regular), this stage does not receive
a corruption report — there are no planted flaws. The sole source of ground truth is the
`ambiguous_choice` block from Stage 2M.

Key fields produced:

- **`correct_position`:** Always `"mixed"`
- **`ideal_debate_resolution`:** type=mixed, plus `condition`, `supports_critique_if`,
  `supports_defense_if`, `ambiguous_if` — together specifying the concrete empirical test that
  would resolve the dispute
- **`planted_issues`:** Always `[]`
- **`must_find_issue_ids`:** Always `[]`
- **`acceptable_resolutions`:** Always `["empirical_test_agreed"]`

The `acceptable_resolutions` value is the critical signal for H1b: baseline and ensemble conditions
will commit to `critique_wins` or `defense_wins` (FVC 0.0–0.5); debate conditions should produce
`empirical_test_agreed`. If all four verdict values were in `acceptable_resolutions`, compute_fvc()
would return 1.0 for every condition, collapsing H1b entirely. This bug was found and fixed in
Phase 0 — see §6.1.

Stage 3M validates that `ideal_debate_resolution.type == "mixed"` and that `condition`,
`supports_critique_if`, and `supports_defense_if` are all non-empty before accepting output.
A concreteness self-check requires the `condition` to name (a) what to measure, (b) on what
data, and (c) the threshold or comparison that determines the outcome.

---

## 5. Post-Hoc Selection and Difficulty Calibration

### 5.1 PM3 Prevention — Difficulty from Phase 3 Pilot, Not Proxy

The most significant change to post-hoc selection in v6 is the **elimination of proxy_mean as a
difficulty gate**. In v5, `select_cases.py --max-proxy 0.83` was the primary hardness filter.
PM3 established this does not work: proxy_mean (Claude Sonnet calibration) had Spearman ρ = +0.046
against rubric performance (also Claude-scored), confirming that self-calibration is circular.

In v6, `_pipeline.proxy_mean` is stored for traceability but has no role in `select_cases.py`.
Difficulty labels (`"medium"`, `"hard"`) are set in Phase 3, after running the baseline on ~30
candidate cases with GPT-4o scoring. Cases where `baseline_fc_mean > 0.80` are discarded;
the remaining pool is labeled by GPT-4o rubric performance, not proxy_mean.

### 5.2 Stratified Selection

`select_cases.py` targets stratified sampling across three strata: critique (60 regular),
defense_wins (20 regular), and mixed (40). Within each stratum, cases from all three pipelines
(RC and synthetic) are pooled and selected by difficulty label, then balanced across domains.

For RC critique cases, difficulty at normalization is `null` — filled by Phase 3 pilot GPT-4o
scoring. For synthetic regular cases, `_pipeline.proxy_mean` is stored but the `difficulty`
field is also `null` at normalization. For synthetic mixed cases, Stage 3M assigns an initial
`"medium"` or `"hard"` label based on the reasoning path required to identify and engage the
ambiguous choice — this is the only case where a difficulty label exists before Phase 3.

### 5.3 Schema B Normalization

`normalize_cases.py` maps all three source formats to a unified Schema B before selection.
Key normalization rules:

| Field | RC source | Synthetic regular | Synthetic mixed |
|-------|-----------|------------------|-----------------|
| `is_real_paper_case` | `true` | `false` | `false` |
| `_pipeline.case_type` | `"rc"` | `"regular"` | `"mixed"` |
| `_pipeline.proxy_mean` | `null` | from Stage 5 | `null` |
| `sound_design_reference` | `null` | from Stage 2 | same as `task_prompt` |
| `planted_issues[].corruption_id` | `null` | from Stage 3 | `null` (empty array) |
| `difficulty` | `null` | `null` | from Stage 3M |
| `acceptable_resolutions` | flat string array | flat string array | `["empirical_test_agreed"]` |

The `acceptable_resolutions` field must always be a **flat string array** — `self_debate_poc.py`
line 168 reads `st.get('acceptable_resolutions', [ideal_resolution])` without unwrapping. Nested
objects silently break scoring.

---

## 6. Failures and Lessons Learned

### 6.1 Phase 0 Bug — Mixed Case FVC Collapse (Fixed)

**Problem:** The `stage3_mixed_assembler.md` prompt shipped with
`acceptable_resolutions = ["mixed", "empirical_test_agreed", "critique_wins", "defense_wins"]`
— all four verdict values. This makes `compute_fvc()` return 1.0 for every condition on mixed
cases, collapsing H1b (the FVC lift test) before any data is collected.

**Root cause:** Spec-implementation divergence. PLAN.md, HYPOTHESIS.md, and MIXED_CASE_PLAN.md
all specified `["empirical_test_agreed"]` only. The prompt template was the outlier.

**Fix:** Changed to `["empirical_test_agreed"]` before Phase 1. No data was collected under the
broken version.

**Pattern:** This is structurally identical to PM1 (orchestrator `issues_found` literal match
contaminated IDR scoring) — an upstream artifact silently overrides the scoring engine's intended
behavior with no runtime error. Prompt template divergence from schema specification is the primary
recurrence vector.

### 6.2 RC Yield Skewed Toward Mixed

The RC extraction yielded 45 mixed, 22 critique, 8 defense (75 total). This skew was unexpected:
the prior assumption in PLAN.md was that RC reports would yield primarily critique cases with a
minority of mixed. In practice, GPT-4o classified most RC reports as contested or overstated claims
rather than clear methodology failures — which makes sense, since reproducers rarely find cases
where the methodology was simply wrong in an unambiguous way.

**Impact:** The RC yield meets the mixed target (40) from real papers without any synthetic
supplement. The critique target (60) requires synthetic supplement, as planned in the Phase 1
gate. The defense target (20) also requires synthetic supplement (8 RC + 24 synthetic = 32
available before difficulty filtering).

**No action needed** — the Phase 1 gate anticipated this case and the orchestrator has already
run 80 regular synthetic cases.

### 6.3 OpenRouter Model ID Format Ambiguity

v5 §6.2 documented that OpenRouter requires dot notation for Anthropic models
(`anthropic/claude-haiku-4.5`). The v6 orchestrator uses dash notation
(`anthropic/claude-haiku-4-5`). The 80-case Stage 2 batch succeeded with this format.

It is possible that OpenRouter now accepts both formats, or that the format has changed between
v5 and v6. If a future Stage 2 batch returns HTTP 400 errors, try the dot notation
(`anthropic/claude-haiku-4.5`) before investigating other causes.

### 6.4 Stage 5 Smoke Not Applicable to Mixed Cases

The smoke test produces a binary `approve | critique` verdict. This verdict is undefined for
mixed cases — the correct outcome is `empirical_test_agreed`, which is not a verdict a single
reviewer produces. Running smoke on mixed cases would produce meaningless proxy_mean values that
could contaminate difficulty calibration if they were ever accidentally used as a gate.

The orchestrator enforces this: mixed cases (`mech_mx*`) are never passed to `run_smoke_test()`.
Their `_pipeline.proxy_mean` is set to `null` by Stage 3M.

---

## 7. Current State of the Pipeline

### 7.1 Completed

- **Phase 0 (Setup):** `acceptable_resolutions` bug fixed in `stage3_mixed_assembler.md`;
  `pipeline/run/` excluded from git; v6 directory structure initialized; 120 hypotheses generated
- **Phase 1 (RC Extraction):** All four RC stages complete; 75 usable cases in `rc_cases_raw.json`
- **Synthetic regular (Stages 1–3):** 80 cases with designs and corruption reports produced
- **Phase 2 Assembly (complete):**
  - Stage 4 (ground truth assembly): 120 files produced (80 regular + 40 mixed/Stage 3M output)
  - Stage 5 (smoke test): 80 files produced (regular only); proxy_mean stored for traceability
  - Synthetic mixed (Stages 2M + 3M): 40 designs (`mech_mx*`) + 40 ground truth files produced
  - `normalize_cases.py`: merged all three sources to Schema B → `benchmark_cases_raw.json` (195 candidates)
  - `select_cases.py`: stratified pool produced → `benchmark_cases_verified.json`
- **Phase 3 Pilot and Calibration (complete):**
  - GPT-4o pilot scorer run on 30 candidate cases (cross-model, no closed-loop confound)
  - `pilot_fc_mean` = 0.6500; threshold formula: `max(0.03, min(0.10, 0.1750))` = **0.1000**
  - 5 ceiling cases discarded (`baseline_fc_mean > 0.80`)
  - H1a threshold pre-registered at 0.1000 in `HYPOTHESIS.md` before Phase 5
  - Final benchmark: **120 cases** (60 critique + 20 defense + 40 mixed) in `benchmark_cases_verified.json`

### 7.3 Known Limitations

- **RC mixed skew (resolved):** RC contributed 45 mixed cases against a 40-case target.
  Post-normalization stratified selection reduced this to 40 while balancing domain coverage.
  The final 120-case benchmark meets the stratum targets exactly.
- **Difficulty null at normalization (resolved):** Difficulty labels were `null` at normalization
  for all sources except Stage 3M. The Phase 3 pilot gate (`baseline_fc_mean < 0.80`) discarded
  5 ceiling cases. Remaining cases are labeled by GPT-4o rubric performance, not proxy_mean.
- **No must_find for RC mixed cases:** RC mixed cases have `must_find_issue_ids = []` and
  `planted_issues = []` — the same as synthetic mixed. IDR scoring on these cases is not
  applicable; ETD and FVC are the scoring dimensions.

---

## Appendix A: CLI Reference

```bash
# RC extraction (all four stages)
uv run pipeline/rc_extractor.py --all

# RC extraction (individual stages)
uv run pipeline/rc_extractor.py --stage rc1        # fetch (no LLM calls)
uv run pipeline/rc_extractor.py --stage rc2        # flaw extraction
uv run pipeline/rc_extractor.py --stage rc3        # must_not_claim
uv run pipeline/rc_extractor.py --stage rc4        # filter + contamination gate

# Discover valid OpenReview venues
uv run pipeline/rc_extractor.py --stage rc1 --discover-venues

# Generate synthetic regular + mixed batch
uv run pipeline/orchestrator.py \
    --batch-size 80 \
    --start-case-id 700 \
    --mixed 40 \
    --seed 42 \
    --concurrency 5

# Dry run (no API calls)
uv run pipeline/orchestrator.py --batch-size 5 --start-case-id 700 --mixed 5 --dry-run

# Schema B normalization (all sources)
uv run pipeline/normalize_cases.py

# Stratified case selection
uv run pipeline/select_cases.py --tier-mixed 40
```

---

## Appendix B: Ambiguity Taxonomy Detectability Notes

| Ambiguity Type | Locate from narrative alone? | Empirical condition type |
|----------------|------------------------------|--------------------------|
| `split_ambiguity` | Medium — requires knowing if temporal autocorrelation is strong | Measure target autocorrelation at specified lag |
| `metric_ambiguity` | Medium — requires tracing stakeholder's operational objective | Determine if model is used at fixed threshold or across range |
| `complexity_ambiguity` | Hard — requires knowing feature interaction structure | Compare validation perf vs higher-capacity variant |
| `lookback_ambiguity` | Medium — requires knowing behavioral cycle length | Compare model perf with chosen vs longer window |
| `proxy_ambiguity` | Hard — requires tracing funnel conversion rates | Spearman rank correlation between proxy and target model ordering |
| `regularization_ambiguity` | Hard — requires knowing actual signal-to-noise | Regularization sweep; flag if optimal differs by > 1 order of magnitude |

---

## Appendix C: v5 vs v6 Case Generation Comparison

| Aspect | v5 | v6 |
|--------|----|----|
| Case source | Synthetic planted corruptions only | RC reports + synthetic regular + synthetic mixed |
| Mixed cases | 0 | Up to 40 (RC or synthetic) |
| ETD testability | N/A | Enabled via Stage 2M/3M pipeline |
| Difficulty calibration | proxy_mean (Claude Sonnet smoke) | Phase 3 pilot rubric (GPT-4o scorer) |
| Smoke model | Claude Sonnet (same family as Stage 2 Haiku) | Gemini 2.5 Flash (cross-family) |
| proxy_mean used for gating? | Yes (`--max-proxy 0.83`) | No (stored for traceability only) |
| Pipeline stages | 5 (linear) | 3–5 (per path) + RC 4-stage + normalization |
| Schema normalization | None | Schema B via normalize_cases.py |
| Contamination prevention | N/A | 10-keyword RC-4 gate on task_prompt |
| Flaw types | 9 (corruption taxonomy) | 9 (regular) + 6 (ambiguity taxonomy, mixed) |
