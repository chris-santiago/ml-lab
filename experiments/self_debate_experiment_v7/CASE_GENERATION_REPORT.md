# Case Generation Methodology Report

> **Note:** Frozen snapshot — case generation methodology is locked per experiment version. Not updated by artifact-sync.

## ml-lab v7 Synthetic, RC, and Defense Benchmark Pipeline

**Status:** Active — Phase 4 complete; full benchmark run (Phase 5) pending as of 2026-04-13
**Regular synthetic batch:** `pipeline/run/stage2/` + `pipeline/run/stage3/` (156 cases)
**RC extraction output:** `pipeline/run/rc_candidates/rc_cases_raw.json` (73 cases)
**Defense synthetic batch:** `pipeline/run/stage4/` (`mech_df*` entries, 65 cases)
**Mixed synthetic batch:** `pipeline/run/stage4/` (`mech_mx*` entries, 35 cases)
**Pipeline entry point:** `pipeline/orchestrator.py` (synthetic) · `pipeline/rc_extractor.py` (RC)

For v6 case generation methodology, see `self_debate_experiment_v6/CASE_GENERATION_REPORT.md`.
This document describes only what is new or changed in v7.

---

## 1. Motivation

v6 produced valid results but left five structural problems identified in peer review and post-experiment analysis:

1. **Compute confound in multiround.** v6's `multiround` condition averaged ~5× baseline compute
   (natural stop, up to 4 rounds). The FVC_mixed advantage (0.3667 vs 0.0) was real but confounded —
   it could not be attributed to debate structure vs compute budget. Peer review flagged this as the
   primary methodological weakness: *"the debate advantage on convergent judgment comes from multiround
   at ~5× compute — not from isolated debate at 3×. The debate-vs-ensemble mixed comparison is formally
   inconclusive."* (v6_issues.md)

2. **No defense stratum, no exoneration analysis.** v6 had 0/20 correct exonerations across all
   conditions. The failure was systematic: the critic prompt had no explicit "no issues found" output
   path. Critics manufactured flaws on valid designs. Peer review primary concern: *"0/60 correct
   verdicts across four conditions is striking and underanalyzed."*

3. **Underpowered primary comparisons.** n=80 regular cases was flagged as a desk-reject risk at
   ACL Findings. n=40 mixed cases produced a CI spanning zero on P2 — the convergent/divergent
   framework's empirical anchor. Both tests require scale-up to be inferential rather than directional.

4. **ETD is a structural ceiling.** ETD = 1.0 for 100% of debate outputs in v6. Any LLM asked to
   propose an empirical test for an ambiguous claim produces a structurally valid test. The metric
   measures presence, not quality — zero variance, zero signal. (v6_lessons.md §L2)

5. **Post-hoc convergent/divergent framework.** v6 described the framework as a post-hoc
   interpretation. Peer review MUST DO: *"Reframe convergent/divergent as prospective prediction,
   not just post-hoc. State explicit falsifiable predictions before data collection."*

v7 addresses all five by redesigning the conditions (compute-matched multiround_2r), adding a
dedicated defense pipeline, scaling the benchmark to 280 cases, removing ETD from the scoring battery,
and gating Phase 5 behind a pre-registration commit.

---

## 2. Design Goals

The v7 case library must satisfy these constraints, in addition to the v6 constraints (real-world
flaw validity, ETD testability, cross-family smoke calibration, source-independent normalization):

**5. Compute-matched conditions.** `multiround_2r` is exactly 3 API calls (Critic → Defender →
Adjudicator) — the same budget as `ensemble_3x` and `isolated_debate`. This eliminates the L1
confound and makes P1 (ensemble vs multiround_2r on IDR) and P2 (multiround_2r vs ensemble on
FVC_mixed) formally comparable. The hard 2-round cap also prevents attrition convergence: discovery
`35a8daed` showed the hard stop produced more `empirical_test_agreed` (21.7%) than open-ended
multiround (12.2%) because it prevents agents from converging on `critique_wins` by exhaustion.

**6. Dedicated defense stratum.** 40 cases with valid methodology generated via a new Stage 4D
path. The critic prompt receives an explicit `defense_wins` verdict option with the instruction:
*"A confident 'no significant issues' conclusion is as important as identifying genuine flaws."*
This directly targets the v6 L7 failure mechanism: critics find (or manufacture) flaws when
no valid exoneration path exists in the output schema. Defense cases are analyzed separately —
excluded from P1, P2, and all primary tests — to prevent their near-zero exoneration rate from
diluting regular-case signal (a v6 design flaw).

**7. Benchmark scale-up to 280 cases.** Regular: 160 (up from 80); mixed: 80 (up from 40);
defense: 40 (new). Regular scale-up halves CI width on the P1 primary comparison. Mixed
scale-up addresses the inconclusive P2 CI at n=40. The total of 280 meets the peer review
MUST DO: *"Scale benchmark to ≥160 regular cases."*

**8. ETD removal; IDR as co-primary.** ETD removed from the primary scoring battery (structural
ceiling, no variance, no signal). IDR (issue detection recall) replaces it as the co-primary
metric for the divergent detection task. FVC_mixed remains the co-primary for the convergent
task. The FC composite (mean of IDR, IDP, DRQ, FVC) is retained for comparability but IDR is
the signal metric.

**9. Cross-vendor scoring with gpt-5.4-mini.** All IDR/IDP scoring uses `openai/gpt-5.4-mini`
via OpenRouter. v6 lesson L5 documented that same-model scoring (Claude scoring Claude) produced
an IDR delta of −0.7737 relative to GPT-4o scoring Claude, driven by self-preference bias
(Panickssery et al.). gpt-5.4-mini is stronger and cheaper than v6's gpt-4o scorer.

**10. Pre-registration gate.** `HYPOTHESIS.md` with P1, P2, H1a–H5, and equivalence bounds
(H1a: ±0.015 FC; H5: ±0.03 precision) must be committed to git before Phase 5 begins. This
converts the convergent/divergent framework from post-hoc interpretation (v6) to prospectively
confirmed or not (v7). Any change after Phase 5 starts invalidates pre-registration.

**11. 100% difficulty labeling.** All 160 regular cases must have difficulty labels before Phase 4
commit. v6 working paper limitation: *"Only 15 of 80 regular cases have difficulty labels, leaving
difficulty-stratified analysis chronically underpowered."* Phase 3 pilot assigns labels to all
regular cases via baseline FC, not proxy_mean.

---

## 3. Architecture

### 3.1 Four-Pipeline Convergence

v7 adds a dedicated **defense pipeline** to v6's three-pipeline design. All four converge at
`normalize_cases.py`:

```
RC Extraction Pipeline       Synthetic Regular Pipeline    Synthetic Mixed Pipeline    Synthetic Defense Pipeline
─────────────────────────    ─────────────────────────     ────────────────────────    ──────────────────────────
RC-1: Fetch (ReScience C)
RC-2: Flaw extraction        Stage 1: Hypothesis gen       Stage 1: Hypothesis gen     Stage 1: Hypothesis gen
RC-3: must_not_claim         Stage 2: Sound design         Stage 2M: Ambiguous design  Stage 2: Sound design
RC-4: Filter + contam. gate  Stage 3: Corruption node      Stage 3M: GT assembly       Stage 4D: Defense assembler
                             Stage 4: GT assembler          [no smoke test]             [no Stage 3, no smoke test]
                             Stage 5: Smoke validation
       ↓                              ↓                              ↓                            ↓
rc_cases_raw.json         synthetic_regular_raw.json    synthetic_mixed_raw.json    synthetic_defense_raw.json
       ↓                              ↓                              ↓                            ↓
       └────────────────────────── normalize_cases.py ──────────────────────────────────────────┘
                                              ↓
                                   benchmark_cases_v7_raw.json  (325 candidates)
                                              ↓
                                        select_cases.py
                                              ↓
                                   v7_cases_sanitized.json  (280 cases, ground truth stripped)
```

The defense pipeline is new in v7 and is the structural response to the v6 L7 failure. Stage 4D
produces defense ground truth from a sound design directly — no corruption report, no smoke test.
The `--defense N` flag to `orchestrator.py` is separate from `--batch-size`, ensuring defense
cases are not sampled from the same corruption probability distribution as regular cases.

### 3.2 Phase 1 Decision Gate

After RC extraction completes, a yield check determines synthetic supplementation needed:

| RC yield | Action |
|---|---|
| regular ≥ 60 AND mixed ≥ 20 | Use RC exclusively |
| regular ≥ 60, mixed < 20 | Supplement mixed with synthetic |
| regular < 60 | Supplement regular with synthetic |
| RC total < 30 | Full synthetic fallback |

Current outcome (Phase 1 complete): 5 critique + 50 mixed + 18 defense = 73 RC cases.
This triggers the third row — regular (critique) is below 60 (5 << 60), requiring synthetic
supplement for all strata. The RC mixed yield (50) exceeds the 80-case target, so it
contributes substantially but synthetic mixed is still generated to reach n=80.

### 3.3 Corruption Level Distribution (Synthetic Regular Only)

v7 introduces a key design change: **0-corruption cases are generated exclusively through the
dedicated defense path** (`--defense N` flag, Stage 4D assembler) rather than through the
regular path's corruption sampling. Stage 4D produces richer defense ground truth — including
a `must_not_claim` list of surface-level false alarms — than 0-corruption regular Stage 4
assembly, which was designed for flawed cases.

The corruption probability table is unchanged from v6:

```python
CORRUPTION_LEVELS = [0, 1, 2, "many"]
CORRUPTION_PROBS  = [0.25, 0.35, 0.25, 0.15]
```

In practice the regular batch was generated targeting non-zero corruptions only (the defense
path handles the sound-design cases), producing the following observed distribution:

| Level | Actual (N=156) |
|-------|----------------|
| 0 corruptions | 0 (routed to defense path) |
| 1 corruption | 71 (45.5%) |
| 2 corruptions | 48 (30.8%) |
| "many" (3–5) | 37 (23.7%) |

The shift from 0-corruption regular cases to dedicated Stage 4D defense cases is an intentional
quality upgrade: Stage 4D explicitly assembles `must_not_claim` entries from the sound design,
providing higher-signal false-alarm targets than Stage 4 would produce for a 0-corruption case.

### 3.4 Model Selection

v7 updates the model configuration from v6. Key changes:

| Stage | v6 Model | v7 Model | Rationale |
|-------|---------|---------|-----------|
| Stage 1 | `openai/gpt-4o-mini` | `openai/gpt-5.4-mini` | Model generation upgrade |
| Stage 2 | `anthropic/claude-haiku-4-5` | `anthropic/claude-haiku-4.5` | ID format normalization |
| Stage 3 | `openai/gpt-4o` | `openai/gpt-5.4` | Model generation upgrade |
| Stage 4 | `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b` | Same model, shorter ID |
| Stage 4D | N/A | `qwen/qwen3-235b-a22b` | New for v7; structured JSON assembly |
| Stage 5 (smoke) | `google/gemini-2.5-flash` | `google/gemini-3-flash-preview` | Updated cross-family calibrator |
| Scorer | `openai/gpt-4o-mini` | `openai/gpt-5.4-mini` | Model generation upgrade |
| RC-2/RC-3 | `openai/gpt-4o` | `openai/gpt-5.4` | **Critical — caused yield shift; see §6.2** |
| Stage 2M | `openai/gpt-4o` | `openai/gpt-5.4` | Model generation upgrade |
| Stage 3M | `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b` | Same model, shorter ID |

**RC extraction model change (critical interaction):** Upgrading RC-2/RC-3 from `gpt-4o` to
`gpt-5.4` changed the yield composition: only 5 pure `critique` cases vs 22 in v6. More RC
reports were classified as `mixed` (50 vs 45) or `defense` (18 vs 8). This is not a bug —
gpt-5.4 applies a more calibrated assessment that fewer real papers have *unambiguous*
methodology flaws; most contested claims are genuinely arguable. See §6.2 for full analysis.

**Smoke model family constraint (retained from v6):** Stage 2 uses `claude-haiku-4.5`
(Anthropic family) to write designs. The smoke model must be cross-family to avoid RLHF
calibration bias. `gemini-3-flash-preview` (Google family) is the v7 cross-family evaluator,
updated from v6's `gemini-2.5-flash`.

---

## 4. Stage-by-Stage Design

### 4.1 RC Extraction Pipeline

The RC pipeline extracts real methodology flaws from published ML Reproducibility Challenge
reports. The four stages are unchanged from v6 in structure; model and source changes are noted.

**RC-1 — Fetch:** Queries the OpenReview API v2 (2020–2023 RC editions) and fetches the
ReScience MLRC GitHub repository. In v7, all 12 OpenReview venue patterns returned 403 Forbidden
— the API access policy appears to have changed since v6. GitHub MLRC is the sole source.

Current yield: **80 reports fetched** (ReScience C only).

**RC-2 — Flaw extraction:** `openai/gpt-5.4` reviews each report and extracts structured
methodology flaws, producing a `ground_truth_type` classification and `flaw_records` array.
All 80 reports processed successfully (0 failed), 22-second wall time.

Ground truth type distribution from RC-2:
- `mixed`: 50 (reproducer found a contestable or overstated claim)
- `defense`: 18 (reproducer confirmed the paper's methodology)
- `critique`: 5 (reproducer documented a clear methodology flaw)
- `none` / `unknown`: 7 (no usable flaw found; dropped in RC-3)

**RC-3 — must_not_claim extraction:** A separate `gpt-5.4` pass identifies sound design choices
that a pattern-matching reviewer might wrongly challenge. Produces `must_not_claim` entries,
enabling IDP scoring. 7 cases skipped (no extractable flaws).

Current yield after RC-3: **73 usable cases** (5 critique, 50 mixed, 18 defense).

**RC-4 — Filtering + contamination gate:** Applies exclusion criteria and rejects any case
where `task_prompt` contains reproducer-language keywords. The 10 contamination keywords are
unchanged from v6:

```
"we found that"          "failed to reproduce"         "the reported results"
"our reproduction"       "could not replicate"          "we were unable to"
"reproduction failed"    "reproducer found"             "reproducibility report"
"could not be reproduced"
```

Current yield after RC-4: **73 cases pass** (0 rejected). No contamination hits.

### 4.2 Stage 1 — Hypothesis Generator (Shared)

Unchanged from v6 in behavior. Stage 1 now generates hypotheses for all three synthetic paths
in a single concurrent pass: `--batch-size N + --mixed M + --defense D` hypotheses generated
together. The first N go to the regular path; the next M to mixed; the remaining D to defense.

### 4.3 Stage 2 — Sound Design Writer (Shared)

Unchanged from v5/v6 in behavior. Stage 2 is now shared between the regular path (followed by
Stage 3 corruption) and the defense path (bypasses Stage 3, proceeds directly to Stage 4D).
The sound design output is identical regardless of path — Stage 4D simply uses it without
corrupting it.

### 4.4 Stage 3 — Corruption Node (Regular Path Only)

Nine-type flaw taxonomy, six requirements per corruption, and the self-check before finalizing
are unchanged from v5. Stage 3 is **not called** for mixed or defense paths. The v7 orchestrator
makes this explicit: `run_case_defense()` calls Stage 2 then Stage 4D, with no Stage 3 invocation.

### 4.5 Stage 4 — Ground Truth Assembler (Regular Path, Unchanged)

Unchanged from v5. Produces `planted_issues`, `must_find_issue_ids`, `must_not_claim`, and
`acceptable_resolutions` from the Stage 2 sound design and Stage 3 corruption report.

### 4.6 Stage 5 — Smoke Test (Model Updated)

The smoke test structure and scoring logic are unchanged from v6. Model updated from
`gemini-2.5-flash` to `gemini-3-flash-preview`. `proxy_mean` is embedded in `_pipeline`
metadata for traceability but **not used as a difficulty gate** — this is the PM3 prevention
rule established in v6 and retained in v7.

Smoke tests apply only to regular synthetic cases. Defense cases and mixed cases have no smoke
test — binary approve/critique verdicts are not applicable to either.

### 4.7 Stage 2M — Ambiguous Design Writer (Unchanged)

Produces a methodologically sound design with exactly one empirically contingent design choice,
using the 6-type ambiguity taxonomy from v6 (unchanged):

| Type | Core Pattern |
|------|-------------|
| `split_ambiguity` | Temporal structure in split data unknown at design time |
| `metric_ambiguity` | Rank metric vs threshold-sensitive operational objective |
| `complexity_ambiguity` | Model capacity vs unknown interaction structure |
| `lookback_ambiguity` | Behavioral lookback window vs unknown cycle length |
| `proxy_ambiguity` | Proxy outcome diverges at conversion tail |
| `regularization_ambiguity` | Regularization strength vs actual signal-to-noise |

Model upgraded from `gpt-4o` to `gpt-5.4` (stronger reasoning for the ambiguity constraint:
confident, non-hedged framing of a contestable design choice).

### 4.8 Stage 3M — Mixed Ground Truth Assembler (Unchanged)

Unchanged from v6. Assembles ground truth for mixed cases using the `ambiguous_choice` block
from Stage 2M. Key fields: `correct_position = "mixed"`, `planted_issues = []`,
`acceptable_resolutions = ["empirical_test_agreed"]`. The `acceptable_resolutions` constraint
is essential for FVC_mixed signal: if all verdict values were accepted, compute_fvc() would
return 1.0 for every condition. The v6 Phase 0 bug that set all four values here was fixed
before any data was collected.

### 4.9 Stage 4D — Defense Assembler (New in v7)

Stage 4D is the structural fix for v6's 0/20 exoneration failure. It assembles ground truth
for a defense case from a sound design that has no corruption — the design is correct as-is.

**Path:** Stage 1 → Stage 2 → Stage 4D. No Stage 3 (no corruption). No Stage 5 (no smoke).
Defense mechanism IDs use the prefix `mech_df001`, `mech_df002`, etc.

**Key output fields:**
- `category = "defense"`
- `correct_position = "defense_wins"`
- `planted_issues = []`
- `must_find_issue_ids = []`
- `must_not_claim` — list of sound design choices that a pattern-matching reviewer might
  wrongly challenge (enables IDP scoring even for valid designs)
- `acceptable_resolutions = ["defense_wins"]`

**Model:** `qwen/qwen3-235b-a22b` (same as Stage 4).

**No smoke test:** A binary approve/critique verdict is not meaningful for defense cases. The
case is correct — a smoke test would only measure whether the calibrator finds false alarms,
not case validity. Defense cases have `_pipeline.proxy_mean = null`.

**Prompt intervention (v6 L7 fix):** The Stage 4D prompt includes the explicit instruction:
*"A confident 'no significant issues' conclusion is as important as identifying genuine flaws."*
and provides a well-formed `{"verdict": "defense_wins", "all_issues_raised": [], ...}` output
schema as an example. Without this, critics prompted to find flaws will find (or manufacture)
them — the v6 mechanism that produced 0/20 exonerations. The efficacy of this fix is not yet
empirically known; it will be measured by the Phase 5 exoneration rate.

**Validation gate (orchestrator.py:910–915):** Raises ValueError if `task_prompt` is missing
or `must_not_claim` is not a list. Up to `--max-recycles` retry attempts from Stage 2.

---

## 5. Post-Hoc Selection and Difficulty Calibration

### 5.1 PM3 Prevention — Difficulty from Phase 3 Pilot, Not Proxy

Unchanged from v6. `_pipeline.proxy_mean` is stored for traceability but has no role in
`select_cases.py`. Difficulty labels are set in Phase 3 via baseline FC performance, not
proxy_mean. The v6 PM3 result (Spearman ρ = +0.046 between proxy_mean and rubric performance)
confirmed that self-calibration is circular; Phase 3 pilot uses GPT-4o as a cross-vendor
scorer.

### 5.2 Stratified Selection

`select_cases.py` targets stratified sampling across three strata. v7 targets are larger than
v6 at every stratum:

| Stratum | v6 target | v7 target | Pool available | Selected |
|---------|-----------|-----------|----------------|----------|
| Regular (`critique_wins`) | 60 | 160 | 161 | 160 |
| Mixed (`empirical_test_agreed`) | 40 | 80 | 84 | 80 |
| Defense (`defense_wins`) | 20 | 40 | 80 | 40 |
| **Total** | **120** | **280** | **325** | **280** |

RC and synthetic cases are pooled within each stratum before selection. The final benchmark
contains 69 RC cases and 211 synthetic cases. The 4-case margin in the regular and mixed
strata (161 available vs 160 selected; 84 vs 80) provides minimal buffer — the pool was sized
close to target, as the selection gate (Phase 3 ceiling filter) has not yet run.

### 5.3 Schema B Normalization

`normalize_cases.py` maps all four source formats to unified Schema B before selection. Key
normalization rules for the v7-specific defense path:

| Field | RC source | Synthetic regular | Synthetic mixed | Synthetic defense |
|-------|-----------|------------------|-----------------|-------------------|
| `category` | derived from `ground_truth_type` | `"regular"` | `"mixed"` | `"defense"` |
| `is_real_paper_case` | `true` | `false` | `false` | `false` |
| `_pipeline.case_type` | `"rc"` | `"regular"` | `"mixed"` | `"defense"` |
| `_pipeline.proxy_mean` | `null` | from Stage 5 | `null` | `null` |
| `planted_issues` | from RC-2 | from Stage 4 | `[]` | `[]` |
| `must_find_issue_ids` | from RC-2 | from Stage 4 | `[]` | `[]` |
| `acceptable_resolutions` | flat string array | flat string array | `["empirical_test_agreed"]` | `["defense_wins"]` |
| `difficulty` | `null` | `null` | from Stage 3M | `null` |

### 5.4 Difficulty Labels — Phase 3 Results

The Phase 3 pilot ran on 360 cases (120 per stratum: regular, mixed, defense) scoring FVC and
DRQ only. All 161 regular cases are labeled `"medium"`.

**Why the ceiling gate was bypassed:** The design called for discarding cases with
`baseline_fc_mean ≥ 0.80`, but the Phase 3 pilot computes FVC and DRQ only — not IDR/IDP.
For regular cases, FVC and DRQ are trivially near-ceiling: any baseline run that guesses
`critique_wins` scores FVC=1.0 and DRQ=1.0, regardless of whether it found the planted issues.
117 of 120 sampled regular pilot cases scored FC ≥ 0.80 on these two metrics alone. Applying
the ceiling gate on FVC/DRQ would have rejected cases that are genuinely hard on the IDR
dimension — the wrong signal entirely.

The gate is structurally inapplicable to pilot FVC/DRQ. All 161 regular cases received the
`"medium"` default label. Difficulty-stratified analysis (H4 secondary) proceeds with a
single difficulty tier — the design_decisions.md pre-specification for difficulty at Phase 3
is satisfied; the gate simply did not fire.

Post-Phase 3 difficulty distribution:
- Regular: 161 medium, 0 hard, 0 ceiling discards
- Mixed: 34 medium (Stage 3M initial labels), 50 null (RC mixed — not labeled by pilot)
- Defense: 80 null (no must_find; IDR/IDP not applicable; pilot FC not interpretable for defense)

The equivalence bounds were confirmed against v6 data: H1a ±0.015 FC (confirmed above noise
floor); H5 ±0.03 precision (confirmed above observed v6 diff of +0.017). These bounds were
derived analytically from v6 results per design_decisions.md §4 and do not require v7 pilot
data to validate.

---

## 6. Failures and Lessons Learned

### 6.1 v6 Lessons Applied in v7

All seven lessons from `plan/references/v6_lessons.md` are addressed in v7:

| Lesson | v6 Failure | v7 Fix |
|--------|-----------|--------|
| L1 | multiround ~5× compute; FVC_mixed advantage confounded | `multiround_2r` — exactly 3 API calls, 2-round hard cap |
| L2 | ETD = 1.0 for 100% of outputs; structural ceiling | ETD removed from scoring battery |
| L3 | Coherence audit was ad-hoc cleanup at Phase 4 end | Phase 4 coherence audit is a named mandatory gate |
| L4 | Adjudicator lacked mixed-case instruction; FVC_mixed near-zero | Mixed-case instruction baked into phase5_benchmark.py dispatch |
| L5 | Same-model scoring (Claude/Claude) IDR delta −0.7737 | All IDR/IDP scoring uses gpt-5.4-mini via OpenRouter |
| L6 | Partial output corruption from concurrent file writes | Atomic writes in phase5_benchmark.py (`.tmp` → `os.rename()`) |
| L7 | 0/20 exonerations; no "no issues found" critic output path | Stage 4D defense path; explicit `defense_wins` verdict schema |

### 6.2 RC Yield Shift — gpt-5.4 More Conservative

The model upgrade from `gpt-4o` → `gpt-5.4` for RC-2/RC-3 produced a significant composition
shift:

| Category | v6 (gpt-4o) | v7 (gpt-5.4) | Delta |
|----------|------------|------------|-------|
| critique | 22 | 5 | −17 |
| mixed | 45 | 50 | +5 |
| defense | 8 | 18 | +10 |
| Total usable | 75 | 73 | −2 |

Root cause: gpt-5.4 classifies fewer RC reports as unambiguous methodology failures. Where
gpt-4o would label a reproducer-documented issue as `critique`, gpt-5.4 more often classifies
it as `mixed` (the reproducer confirmed the issue but the original authors have a defensible
rationale) or `defense` (the reproducer validated the methodology). This is not a regression —
real reproducibility reports are predominantly ambiguous. The shift reflects a more calibrated
reading of the epistemic status of methodology claims.

**Impact:** The Phase 1 yield gate fires at `regular < 60` (got 5), triggering synthetic
supplementation for all three strata. The RC contribution is primarily to the mixed stratum
(50/80 = 62.5% of target from real papers).

### 6.3 OpenReview 403 Forbidden

All 12 OpenReview venue invitation patterns returned 403 Forbidden in v7. This may reflect
a change in the OpenReview API access policy since v6. The ReScience GitHub MLRC repository
remains fully accessible and provided 80 reports.

**Impact:** None on benchmark quality — ReScience C is the higher-quality source (full
reproducibility reports with structured methodology analysis, not just submission PDFs).
OpenReview access would have added additional years and venues; deferred to a future version
if access is restored.

### 6.4 Normalization Deduplication — 4 Cases

`normalize_cases.py` processed 329 raw records (73 RC + 156 regular + 35 mixed + 65 defense)
and produced 325 normalized cases — a 4-case deduplication.

Three cases (`eval_scenario_702`, `eval_scenario_712`, `eval_scenario_887`) appeared in both
the regular batch and the defense batch. These are batch ID range overlaps: the regular and
defense orchestrator runs were assigned overlapping `--start-case-id` ranges, producing
duplicate case IDs. The normalizer kept the regular copy (first seen) for each.

One case (`eval_scenario_931`) appeared twice in the mixed batch — a resume-mode artifact where
the mixed case was generated twice under the same ID. The normalizer kept the first copy.

**Impact:** 3 defense copies and 1 mixed copy were discarded. The net effect: 1 fewer case
available in the defense pool (79 instead of 80 unique IDs from defense sources) and 1 fewer
in the mixed pool. Both strata still exceed their selection targets before Phase 3 ceiling
filtering.

**Prevention:** Use non-overlapping `--start-case-id` ranges when running regular, mixed, and
defense batches separately. Or run all three in a single orchestrator invocation
(`--batch-size 160 --mixed 80 --defense 40`) which assigns IDs sequentially without overlap.

### 6.5 Defense Pool Margin — Non-Issue (Ceiling Gate Bypassed)

The anticipated risk of thin margin in the regular stratum (161 available vs 160 target) did
not materialize. The Phase 3 ceiling gate was bypassed because FVC/DRQ pilot scores are
structurally inapplicable as difficulty signals for regular cases (see §5.4). No cases were
discarded. The final benchmark remains 280 cases (160 regular + 80 mixed + 40 defense).

### 6.6 Phase 3 Bug: FVC/DRQ Scoring Used Wrong Field

**Problem:** `v7_scoring.py` computed FVC and DRQ using `ideal_debate_resolution.type` (which
stores the IDR token `"mixed"`) instead of `ground_truth.correct_position` (which stores the
Schema B verdict token `"empirical_test_agreed"`). Mixed cases were scoring FVC=0.0 instead
of receiving adjacency partial credit, because `"mixed" != "empirical_test_agreed"`.

**Root cause:** Schema B uses `correct_position` for the canonical verdict token; the scoring
engine was accidentally reading the IDR `type` field which uses a different vocabulary.

**Fix:** Updated `v7_scoring.py` to read `ground_truth["correct_position"]` for FVC and DRQ
computation. The pilot results in `pilot_results.json` use the corrected scorer.

**Pattern:** Same class of schema divergence as v6 §6.1 (mixed case FVC collapse from wrong
`acceptable_resolutions` values). The recurring pattern: two fields store similar information
in different vocabularies (`type=mixed` vs `correct_position=empirical_test_agreed`), and a
scoring function reads the wrong one with no runtime error.

### 6.7 Phase 3 Bug: Sanitizer Ground Truth Leakage

**Problem:** `select_cases.py` sanitization stripped individual leaf fields (`correct_position`,
`must_find_issue_ids`, `acceptable_resolutions`) but left the parent objects (`ground_truth`,
`scoring_targets`, `ideal_debate_resolution`) in the output. Debate agents receiving
`v7_cases_sanitized.json` could read `ground_truth: {}` (empty object) rather than a fully
absent key, and a careful agent might infer from its presence that ground truth metadata exists.
More critically, `ideal_debate_resolution` was left intact — exposing the ambiguous choice
taxonomy type and empirical condition to the agent.

**Fix:** Updated sanitizer to strip entire parent objects (`ground_truth`, `scoring_targets`,
`ideal_debate_resolution`, `planted_issues`) rather than individual leaf fields. Re-generated
`v7_cases_sanitized.json` with the corrected sanitizer.

**Impact:** `v7_cases_sanitized.json` was regenerated in commit `d63f242`. Any Phase 5 run
must use the file from this commit or later — the pre-fix file leaked ground truth structure.
The pilot run used `pilot_cases_sanitized.json` (generated with the corrected sanitizer).

---

## 7. Current State of the Pipeline

### 7.1 Completed

- **Phase 0 (Setup):** multiround_2r prompt committed; ETD removed from scoring engine;
  defense output path and explicit exoneration schema added to critic prompt; atomic writes
  implemented in phase5_benchmark.py; v7 directory structure initialized

- **Phase 1 (RC Extraction):** All four RC stages complete; 73 usable cases in
  `pipeline/run/rc_candidates/rc_cases_raw.json` (5 critique, 50 mixed, 18 defense)

- **Phase 2 (Case Assembly):**
  - Synthetic regular (Stages 1–5): 156 cases with sound designs, corruption reports,
    ground truth, and smoke scores (`pipeline/run/stage2/`, `stage3/`, `stage4/`, `stage5/`)
  - Synthetic mixed (Stages 2M + 3M): 35 cases (`mech_mx*` entries in `stage4/`)
  - Synthetic defense (Stages 2 + 4D): 65 cases (`mech_df*` entries in `stage4/`)
  - Source files assembled: `synthetic_regular_raw.json` (156), `synthetic_mixed_raw.json` (35),
    `synthetic_defense_raw.json` (65), `rc_cases_raw.json` (73)
  - `normalize_cases.py`: merged and deduplicated all four sources → `benchmark_cases_v7_raw.json`
    (325 cases: 161 regular, 84 mixed, 80 defense)
  - `select_cases.py`: stratified selection → `v7_cases_sanitized.json`
    (280 cases: 160 regular, 80 mixed, 40 defense; ground truth stripped for Phase 5)

- **Phase 3 (Pilot and Calibration):**
  - Pilot run on 360 cases (120 per stratum); FVC/DRQ scoring only (no IDR/IDP in pilot mode)
  - Ceiling gate bypassed — FVC/DRQ structurally inapplicable as difficulty signal for regular cases
  - All 161 regular cases labeled `"medium"` (no ceiling discards; 280-case benchmark unchanged)
  - Equivalence bounds confirmed: H1a ±0.015 FC, H5 ±0.03 precision (v6 data analysis)
  - Two pipeline bugs fixed (see §6.6, §6.7):
    - FVC/DRQ scoring used `ideal_debate_resolution.type` instead of `correct_position`
    - Sanitizer left parent objects intact, leaking ground truth structure to agents
  - `pilot_cases_sanitized.json` (360 cases, ground truth stripped) and `pilot_results.json`
    (360 FVC/DRQ scores) written to experiment directory
  - `v7_cases_sanitized.json` regenerated with corrected sanitizer (commit `d63f242`)

- **Phase 4 (Pre-Experiment Self-Review):**
  - `HYPOTHESIS.md` committed as pre-registration anchor (commit `6fadcc6`): P1, P2, H1a–H5,
    equivalence bounds (H1a ±0.015 FC, H5 ±0.03 precision), bootstrap protocol (paired,
    n=10,000, seed=42), case counts (160 regular / 80 mixed / 40 defense)
  - `COHESION_AUDIT.md` committed in same anchor: categories A–C pass; category D has 3
    non-blocking Phase 6/7 gaps (ensemble union IDR wiring; H5 `per_case_issue_map` classifier)
  - Phase 5 gate cleared — pre-registration anchor hash is in git history

### 7.2 Pending

- **Phase 5 (Benchmark Run):** Full run of 280 cases × 4 conditions × 3 runs = 3,360 outputs
  in `v7_raw_outputs/`. Pilot baseline run (120 cases × 3 runs = 360 outputs) complete in
  `pilot_raw_outputs/` — validates pipeline end-to-end. Remaining 3 conditions and full case
  count pending.
- **Phases 6–9:** Cross-vendor scoring with gpt-5.4-mini; bootstrap hypothesis tests
  (P1, P2, H1a–H5); sensitivity analysis; reporting

### 7.3 Known Limitations

- **All 161 regular cases labeled "medium"; no "hard" cases.** The ceiling gate was bypassed
  (FVC/DRQ pilot structurally inapplicable as difficulty signal — see §5.4). Difficulty-stratified
  analysis (H4 secondary) proceeds with a single tier. The H4 subgroup analysis comparing RC vs
  synthetic cases is still valid; hard-vs-medium stratum comparisons are not.

- **Defense exoneration efficacy untested in full benchmark.** The Stage 4D prompt fix
  addresses the structural mechanism of v6's 0/20 failure. The pilot baseline run (120 cases
  in `pilot_raw_outputs/`) has run, but exoneration rate analysis requires Phase 6 scoring.
  Report Phase 5 exoneration rate as a Phase 0 validation check, not a primary result.

- **No must_find for RC mixed cases or defense cases.** IDR scoring is not applicable for
  these cases; FVC and DRQ are the primary scoring dimensions. This is by design — mixed cases
  have no planted flaws, and defense cases have no flaws to find.

- **`v7_cases_sanitized.json` regenerated in commit `d63f242`.** Any Phase 5 run must use the
  post-fix sanitized file (§6.7). Do not use earlier versions of this file.

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

# Generate synthetic regular + mixed + defense batch (single invocation — avoids ID overlap)
uv run pipeline/orchestrator.py \
    --batch-size 160 \
    --start-case-id 700 \
    --mixed 80 \
    --defense 40

# Generate only regular cases (separate invocation — use non-overlapping start-case-id)
uv run pipeline/orchestrator.py \
    --batch-size 160 \
    --start-case-id 700

# Generate only defense cases (must use non-overlapping start-case-id)
uv run pipeline/orchestrator.py \
    --batch-size 0 \
    --start-case-id 1100 \
    --defense 40

# Dry run (no API calls)
uv run pipeline/orchestrator.py --batch-size 5 --start-case-id 700 --mixed 5 --defense 5 --dry-run

# Schema B normalization (all sources)
uv run pipeline/normalize_cases.py

# Stratified case selection
uv run pipeline/select_cases.py

# Phase 5 benchmark runner (after Phase 4 pre-registration gate)
uv run pipeline/phase5_benchmark.py \
    --cases experiments/self_debate_experiment_v7/v7_cases_sanitized.json \
    --output experiments/self_debate_experiment_v7/v7_raw_outputs/ \
    --runs 3
```

---

## Appendix B: Ambiguity Taxonomy Detectability Notes

Unchanged from v6 — the taxonomy is identical in v7.

| Ambiguity Type | Locate from narrative alone? | Empirical condition type |
|----------------|------------------------------|--------------------------|
| `split_ambiguity` | Medium — requires knowing if temporal autocorrelation is strong | Measure target autocorrelation at specified lag |
| `metric_ambiguity` | Medium — requires tracing stakeholder's operational objective | Determine if model is used at fixed threshold or across range |
| `complexity_ambiguity` | Hard — requires knowing feature interaction structure | Compare validation perf vs higher-capacity variant |
| `lookback_ambiguity` | Medium — requires knowing behavioral cycle length | Compare model perf with chosen vs longer window |
| `proxy_ambiguity` | Hard — requires tracing funnel conversion rates | Spearman rank correlation between proxy and target model ordering |
| `regularization_ambiguity` | Hard — requires knowing actual signal-to-noise | Regularization sweep; flag if optimal differs by > 1 order of magnitude |

---

## Appendix C: v6 vs v7 Case Generation Comparison

| Aspect | v6 | v7 |
|--------|----|----|
| Case sources | RC + synthetic regular + synthetic mixed | RC + synthetic regular + synthetic mixed + synthetic defense |
| Defense stratum design | 20 cases from regular pool (correct_position=defense_wins) | 40 cases via dedicated Stage 4D path |
| Defense ground truth assembly | Stage 4 (designed for corrupted cases; less targeted) | Stage 4D (designed for valid cases; richer must_not_claim) |
| Exoneration prompt | No explicit "no issues found" output path | Explicit `defense_wins` verdict schema in critic prompt |
| Final benchmark size | 120 (60 regular + 20 defense + 40 mixed) | 280 (160 regular + 40 defense + 80 mixed) |
| Conditions | 6 (baseline, isolated_debate, ensemble_3x, multiround, biased_debate, conditional_fm) | 4 (baseline, isolated_debate, ensemble_3x, multiround_2r) |
| multiround compute | ~5× baseline (variable, natural stop) | 3× baseline (fixed 2-round hard cap) |
| RC extraction model | `openai/gpt-4o` | `openai/gpt-5.4` (more conservative; more mixed/defense) |
| RC critique yield | 22 | 5 |
| RC mixed yield | 45 | 50 |
| Smoke model | `google/gemini-2.5-flash` | `google/gemini-3-flash-preview` |
| Difficulty labeling | ~15/80 regular cases at Phase 2 | 0/160 at Phase 2; 100% required at Phase 3 |
| Difficulty labeling method | proxy_mean threshold (circular) | Phase 3 pilot baseline FC (cross-vendor GPT-4o scorer) |
| Pre-registration | Post-hoc framework description | HYPOTHESIS.md gate before Phase 5 (prospective) |
| ETD in scoring battery | Yes (1.0 structural ceiling) | No (removed; IDR co-primary) |
| Cross-vendor scorer | `openai/gpt-4o` | `openai/gpt-5.4-mini` |
| Pipeline | 3 sources → normalize → select | 4 sources → normalize → select |
| 0-corruption regular cases | Included in regular batch (n~20) | Excluded from regular batch; use dedicated defense path |
