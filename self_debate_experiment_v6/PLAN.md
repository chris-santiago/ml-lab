# v6 Experimental Design: Does the ml-lab Debate Protocol Add Value?

## Context

v5 tested whether adversarial debate (critic + defender) outperforms single-pass critique on
110 synthetic binary-verdict cases. The primary hypothesis **failed**: fc_lift = +0.0097
(threshold +0.10, CI [-0.0013, +0.0217]). But v5 was structurally unable to answer the question:

1. **Ceiling effect** — baseline scored 0.9452, leaving only ~0.05 headroom. The threshold was uninformative.
2. **No mixed cases** — ETD (the one dimension where v3 showed genuine debate advantage: +0.365 lift) was N/A for all 110 cases.
3. **Closed-loop confound** — Claude scored Claude outputs. Cross-vendor IDR delta = -0.7737.
4. **Majority-vote artifact** — ensemble IDR suppressed from 0.8725 (union) to 0.7679 (majority-vote).
5. **Hollow forced rounds** — 20.5% of forced_multiround rounds were vacuous (no new points resolved).

v3 retrospective revealed the debate protocol's only clear advantage was **ETD-specific**:
helping models specify empirical tests for genuinely ambiguous cases. IDR/IDP/FVC showed zero
debate advantage even in v3 (all lift from ETD: +0.365; IDR/IDP/FVC delta = 0.0).

v6 is designed to definitively answer three questions:
- **Q1:** Does ml-lab debate add value over single-pass baseline?
- **Q2:** Does it add value over a compute-matched ensemble?
- **Q3:** Is forced multiround superior to natural stopping?

---

## Design Decisions

### 1. Case Source: RC Reports (Primary) + Synthetic Mixed (Supplement)

**Regular cases (critique/defense):** sourced from ML Reproducibility Challenge (RC) reports
via OpenReview API + ReScience C. RC reports contain post-hoc documented flaws from independent
reproducers — measuring *methodology review recall*, not planted corruption detection.

**Mixed cases:** generated via the synthetic pipeline (already built: `stage2_mixed_writer.md`,
`stage3_mixed_assembler.md`, `orchestrator.py --mixed`). RC reports may also yield natural
mixed cases ("paper mostly sound but X is overstated"), but the synthetic pipeline guarantees
sufficient volume and controlled ambiguity taxonomy.

**Decision gate — run after Phase 1, before Phase 2 commits:**

| RC yield | Action |
|---|---|
| regular >= 60 AND mixed >= 20 | Use RC exclusively |
| regular >= 60, mixed < 20 | Supplement mixed with synthetic pipeline |
| regular < 60 | Supplement regular cases with synthetic (lower proxy threshold) |
| RC total < 30 | Full synthetic fallback: v5 architecture + lower ceiling target + mixed cases |

**Critical-path risk:** RC extraction pipeline (`pipeline/rc_extractor.py`) does not yet exist.
Build and validate yield in Phase 1 before committing Phase 2.

---

### 2. Case Composition: Target N = 120

| Stratum | Source | Target N | % |
|---|---|---|---|
| Critique cases (flawed designs) | RC reports | 60 | 50% |
| Defense_wins (sound designs) | RC reports or synthetic | 20 | 17% |
| Mixed cases (empirically contingent) | Synthetic + RC natural | 40 | 33% |
| **Total** | | **120** | |

**Difficulty calibration:**
- Pilot Phase (Phase 3): run baseline on ~30 candidate cases
- **Hard gate:** discard cases where baseline FC mean > 0.80 (retain cases with genuine headroom)
- Use **cross-model proxy scoring** (GPT-4o) for difficulty filtering — not Claude
- Final N informed by pilot results; if pilot variance is high, increase N

---

### 3. Pipeline Architecture

Three pipelines converge at `normalize_cases.py` to produce unified Schema B, consumed by
`self_debate_poc.py`:

| Stage | RC Extraction | Synthetic Regular | Synthetic Mixed |
|---|---|---|---|
| 1 | RC-1: Fetch (OpenReview API, ReScience C) | Stage 1: Hypothesis gen | Stage 1: Hypothesis gen |
| 2 | RC-2: Flaw extraction (GPT-4o) | Stage 2: Corrupt design | Stage 2-mixed: Ambiguous design |
| 3 | RC-3: `must_not_claim` extraction (GPT-4o) | Stage 3: Ground truth assembly | Stage 3-mixed: Ground truth assembly |
| 4 | RC-4: Filtering + contamination gate | Stage 4: Case assembly | ↑ (3 stages only) |
| 5 | — | Stage 5: Smoke validation | — |
| ↓ | `rc_cases_raw.json` | `synthetic_regular_raw.json` | `synthetic_mixed_raw.json` |
| Normalize | `normalize_cases.py` (RC → Schema B) | `normalize_cases.py` (synth → Schema B) | `normalize_cases.py` (synth → Schema B) |
| Select | `select_cases.py` (stratified, difficulty-gated from Phase 3 pilot) | ← same | ← same |
| Output | `benchmark_cases_verified.json` (Schema B, all sources) | ← same | ← same |

**⚠ Blocking bug (fixed in Phase 0):** `stage3_mixed_assembler.md` as shipped set
`acceptable_resolutions = ["mixed", "empirical_test_agreed", "critique_wins", "defense_wins"]`.
This made `compute_fvc()` return 1.0 for every condition, collapsing H1b. Fixed to
`["empirical_test_agreed"]` only. PLAN.md, HYPOTHESIS.md, and MIXED_CASE_PLAN.md all agree
on this value — the prompt template was the outlier.

**Schema B fields consumed by `self_debate_poc.py`:**
- `ground_truth.correct_position` — read by `score_run()`
- `ideal_debate_resolution.type` — read by DRQ/FVC scoring
- `scoring_targets.acceptable_resolutions` — **flat string array** (line 168: `st.get('acceptable_resolutions', ...)`)
- `scoring_targets.must_find_issue_ids` — read by `compute_idr()`
- `scoring_targets.must_not_claim` — read by `compute_idp()`

---

### 4. Conditions (6)

| Condition | Description | Compute | Primary comparisons |
|---|---|---|---|
| `baseline` | Single-pass critique; no adversarial structure | 1x | Reference for all |
| `isolated_debate` | Critic + Defender isolated; orchestrator adjudicates | ~3x | Q1 (vs baseline), Q2 (vs ensemble) |
| `biased_debate` | Same as isolated_debate, but agents persona-primed (see below) | ~3x | Q4 (vs isolated_debate) |
| `multiround` | Defender sees Critic output; natural stopping up to 4 rounds | ~3–6x | Q3 reference |
| `conditional_fm` | Round 2 gated on unresolved disagreement (see gate below) | ~3–6x | Q3 (vs multiround) |
| `ensemble_3x` | 3 independent assessors; union-of-issues IDR | 3x | Q2 compute-matched |

**Compute accounting for Q2 (the structure test):**
The fairest test of whether debate *structure* adds value (not just additional compute) is
`isolated_debate` (~3x) vs `ensemble_3x` (3x) at matched compute. If ensemble >= debate,
adversarial structure adds no value over independent redundancy.

---

### 5. Conditional Forced Multiround Gate

Replaces unconditional `forced_multiround` from v5. Concrete gate:

```
After round 1 adjudication:
  IF point_resolution_rate == 1.0  → STOP (all points resolved)
  ELIF adjudicator verdict matches both agents' round 1 stated positions → STOP
  ELSE → force round 2
```

**Rationale from v5 data:** All 24 hollow rounds (20.5%) came from defense_wins cases where
there was no genuine disagreement. This gate would have prevented all 24. Target hollow rate < 10%.

---

### 6. Persona-Biased Debate

`biased_debate` is structurally identical to `isolated_debate` — same protocol, same compute,
same orchestrator. The only difference is asymmetric persona priming injected into each agent's
system prompt before dispatch:

**Critic priming:**
> "You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and
> treat methodological gaps as real concerns until shown otherwise."

**Defender priming:**
> "You are responding to a combative reviewer who frequently focuses on insignificant issues
> and overstates concerns. Be selective about what you concede."

**Expected mechanism:** The biased critic is sensitized to real flaws (higher IDR); the biased
defender concedes less, forcing the critic to defend weaker claims under pressure.

**IDP note:** v5 IDP was flat at 0.8549 across all conditions on the synthetic benchmark.
v6 uses RC reports with a lower ceiling and different case structure — IDP behavior on genuine
RC flaws may differ. IDP is retained in H6 as a full prediction, not just a diagnostic probe.
If IDP remains flat under the new benchmark, that points to an orchestrator extraction issue
(see orchestrator audit in Phase 0 and `all_issues_adjudicated` field below).

**What this tests (Q4):** Does persona framing alone, without changing the protocol structure,
improve debate quality? Comparison is `biased_debate` vs `isolated_debate` — matched compute,
matched structure, prompt framing only.

**ETD applicability:** Same as `isolated_debate` — ETD fires on mixed cases.

---

### 7. Scoring Dimensions

DC is **dropped entirely** — it was fully redundant with FVC in v5
(mean_abs_delta = 0.0 across all conditions, all 330 comparable runs). Carrying it adds
no signal and introduces reporting confusion.

| Dimension | Regular cases | Mixed cases | Scorer |
|---|---|---|---|
| **IDR** (Issue Detection Rate) | Primary | N/A | GPT-4o (cross-model) |
| **IDP** (Issue Detection Precision) | Primary | N/A | GPT-4o (cross-model) |
| **DRQ** (Decision Resolution Quality) | Primary | Primary (vs `empirical_test_agreed`) | Rule-based |
| **FVC** (Final Verdict Correctness) | Primary | **Co-primary** (vs `empirical_test_agreed`) | Rule-based |
| **ETD** (Empirical Test Design) | N/A | Debate conditions only | GPT-4o (cross-model) |

**Cross-model scoring:** GPT-4o (primary) for IDR, IDP, ETD semantic scoring. Addresses the
closed-loop confound. Absolute scores are **not** comparable to v5 — only within-v6 lift
comparisons are valid.

**Union IDR for ensemble — split rule:** any-assessor-found credit for IDR; majority-vote
retained for the final verdict. The split is intentional: union recovers recall (v5: 0.8725
vs. majority 0.7679) while the conservative majority rule preserves precision on the verdict
itself. Do not union the verdict — that would inflate FVC by accepting minority verdicts.

---

### 8. Why Mixed-Case FVC Is the Primary Signal

On mixed cases, `acceptable_resolutions = ['empirical_test_agreed']`. Expected behavior
by condition:

| Condition | Expected verdict | FVC |
|---|---|---|
| `baseline` | Commits to `critique_wins` or `defense_wins` | 0.0–0.5 |
| `ensemble_3x` | Each assessor picks a side; no adversarial exchange | low |
| `isolated_debate` | Adversarial exchange surfaces ambiguity; `empirical_test_agreed` | high |
| `multiround` | Same as isolated, with more rounds | high |
| `conditional_fm` | Same + gated forcing | high |

Mixed-case FVC is comparable across **all 6 conditions** (unlike ETD, which is N/A for
baseline/ensemble). It directly tests the mechanism claim: adversarial structure should cause
agents to recognize ambiguity rather than commit to one side. This is the cleanest answer to
both Q1 and Q2 simultaneously. `biased_debate` should outperform `isolated_debate` here if
persona priming improves sensitivity to ambiguity.

---

## Hypotheses (Pre-Registered)

Pre-registration must be committed to git **before Phase 5 (benchmark run) begins**.
See `HYPOTHESIS.md` for the full formal document.

### Co-Primary

**H1a — Regular case lift:**
```
fc_mean(isolated_debate, regular) - fc_mean(baseline, regular) >= threshold
```
- Fair-comparison dims: IDR, IDP, DRQ, FVC
- `threshold = max(0.03, min(0.10, (1.0 - baseline_pilot_fc_mean) * 0.5))` — set after Phase 3
- Bootstrap 95% CI; one-sided test

**H1b — Mixed case FVC lift:**
```
mean FVC(isolated_debate, mixed) > mean FVC(baseline, mixed)
```
- One-sided bootstrap test, CI excludes 0
- The cleanest structural test: debate should produce `empirical_test_agreed` where baseline commits to a side

### Secondary

**H2 — Debate vs compute-matched ensemble:**
```
fc_mean(isolated_debate) vs fc_mean(ensemble_union_idr)  [regular cases]
mean FVC(isolated_debate, mixed) vs mean FVC(ensemble, mixed)  [mixed cases]
```
- Two-sided. If ensemble >= debate on both, adversarial structure adds no value over
  independent redundancy at matched compute.

**H3 — Conditional FM vs natural multiround:**
```
FM hard mean > MR hard mean  [Wilcoxon signed-rank, hard cases only]
hollow round rate < 10%  [quality gate for conditional gate]
```

### Exploratory

**H4 — ETD quality by debate mode:**
Mean ETD across isolated_debate, multiround, conditional_fm, biased_debate on mixed cases.
Directional prediction (from v3 evidence and `V5_INSIGHTS_AND_AVENUES.md` Avenue 1):
`multiround > isolated_debate` on ETD specifically — the back-and-forth exchange is where
empirical test specification should emerge, not a single exchange round. Full credit (1.0)
rate and partial credit (0.5) rate reported separately per condition.

**H5 — Cross-model scorer agreement:**
Report IDR/IDP/ETD agreement between GPT-4o (primary) and Claude (secondary).
Quantify confound magnitude; flag if IDR delta > 0.50.

**H6 — Persona-biasing improves debate quality (Q4):**
```
fc_mean(biased_debate, regular) vs fc_mean(isolated_debate, regular)
mean FVC(biased_debate, mixed) vs mean FVC(isolated_debate, mixed)
mean ETD(biased_debate, mixed) vs mean ETD(isolated_debate, mixed)
```
- Two-sided bootstrap, 95% CI
- Prediction: biased_debate > isolated_debate on IDR (critic sensitivity) and IDP (defender
  selectivity); directional improvement on mixed FVC and ETD
- If biased_debate <= isolated_debate: persona framing has no measurable effect on debate
  quality beyond the structural protocol

---

## RC Extraction Pipeline Specification

Four sequential stages implemented in `pipeline/rc_extractor.py`.

| Stage | What | Model | Output |
|---|---|---|---|
| RC-1: Fetch | OpenReview API (RC 2020–2023) + ReScience C (GitHub) | N/A | `rc_candidates/reports_fetched.json` |
| RC-2: Flaw extraction | Report text → structured flaw records | GPT-4o | Per-report flaw JSON |
| RC-3: `must_not_claim` extraction | Separate LLM pass for sound design choices | GPT-4o | Appended to flaw records |
| RC-4: Filtering + contamination gate | Exclusion criteria + `task_prompt` keyword gate | N/A | `rc_candidates/rc_cases_raw.json` |

**RC flaw record schema (produced by RC-2):**

```json
{
  "issue_id": "rc_<report_id>_<flaw_idx>",
  "flaw_type": "methodology | evaluation | statistical | reproducibility | other",
  "description": "...",
  "severity": "minor | major | critical",
  "source": "reproducer_documented",
  "ground_truth_type": "critique | defense | mixed",
  "rc_report_id": "...",
  "original_paper_title": "..."
}
```

**`task_prompt` contamination prevention (critical — PM1 recurrence risk):**
RC reports contain both the original methodology AND the reproducer's critique. If `task_prompt`
includes critique text, debate agents receive the answer key through the data channel — the same
pattern as PM1 but through the input rather than the context window.

- **Primary approach:** extract methodology from the original paper's abstract + methods section
- **Fallback:** use RC report's "original claims" summary (describes methodology without critique)
- **RC-2 prompt instruction:** explicitly separates "what the paper claims" from "what the reproducer found"
- **RC-4 contamination gate:** reject any case where `task_prompt` matches any of:
  `["we found that", "failed to reproduce", "the reported results", "our reproduction", "could not replicate"]`

**RC case categories:**

- `critique`: RC report documents a methodology flaw → maps to regular critique cases
- `defense`: RC report confirms paper with no flaws → maps to defense_wins cases
- `mixed`: RC report identifies a contestable choice ("mostly sound but X is overstated") → maps to mixed cases

---

## Unified Schema B Definition

The normalization target consumed by `self_debate_poc.py`. All pipeline outputs must validate
against this schema before case selection.

| Field | Type | Scoring function | Source: RC | Source: Synthetic |
|---|---|---|---|---|
| `case_id` | string | metadata | `rc_<id>` | from orchestrator |
| `hypothesis` | string | metadata | from paper title | from Stage 1 |
| `domain` | string | metadata | from RC report | from Stage 1 |
| `ml_task_type` | string | metadata | from RC report | from Stage 1 |
| `category` | `"regular"` / `"mixed"` | `score_run()` | from `ground_truth_type` | from orchestrator |
| `difficulty` | `"medium"` / `"hard"` / `null` | metadata | `null` at normalization | `null` at normalization |
| `task_prompt` | string | read by agents | isolated methodology (no critique text) | `design_narrative` |
| `ground_truth.correct_position` | string | `score_run()` | from `ground_truth_type` | from Stage 3 |
| `ideal_debate_resolution.type` | string | DRQ/FVC scoring | `"critique_wins"` / `"defense_wins"` / `"mixed"` | from Stage 3 |
| `scoring_targets.acceptable_resolutions` | flat string array | `compute_fvc()` line 168 | `["critique_wins"]` / `["defense_wins"]` / `["empirical_test_agreed"]` | from Stage 3 |
| `scoring_targets.must_find_issue_ids` | string array | `compute_idr()` | from RC flaw `issue_id` | from Stage 3 |
| `scoring_targets.must_not_claim` | string array | `compute_idp()` | from RC-3 extraction | from Stage 3 |
| `planted_issues` | array | `compute_idr()` | from RC flaw records | from Stage 3 |
| `sound_design_reference` | string / `null` | metadata only | `null` | design narrative |
| `is_real_paper_case` | bool | metadata | `true` | `false` |
| `_pipeline.case_type` | `"rc"` / `"regular"` / `"mixed"` | metadata | `"rc"` | `"regular"` / `"mixed"` |
| `_pipeline.proxy_mean` | float / `null` | **NOT used for gating** | `null` | stored for traceability only |

**Critical format constraints:**

- `acceptable_resolutions` MUST be a flat string array — `self_debate_poc.py` line 168 reads
  `st.get('acceptable_resolutions', [ideal_resolution])` without unwrapping
- `difficulty` is `null` at normalization; Phase 3 pilot fills it via GPT-4o rubric performance.
  `_pipeline.proxy_mean` is stored but NOT used as a difficulty gate (PM3 prevention).
- RC `planted_issues` entries have `corruption_id = null` — scoring engine reads `issue_id` only

---

## v5 Weakness Mitigation

Per-journal-post-mortem mapping: failure mode → specific v6 design decision that prevents recurrence.

| PM | Hash | Failure mode | v6 Mitigation |
|---|---|---|---|
| 1 | `45eee14b` | Orchestrator `issues_found` literal match contaminated IDR scoring | GPT-4o semantic scoring from `critic_raw`; smoke literal match sandboxed to `gate_pass` only |
| 2 | `bc3a08d0` | Closed-loop confound: Claude scored Claude outputs (cross-vendor IDR delta = −0.77) | GPT-4o primary scorer for IDR/IDP/ETD; Claude secondary for H5 confound quantification only |
| 3 | `358b7a5a` | Same-model benchmark calibration: `proxy_mean` didn't predict rubric performance (Spearman ρ = +0.046) | Difficulty from Phase 3 pilot (GPT-4o scorer); `proxy_mean` stored for traceability, NOT used for gating |
| 4 | `fee829a4` | H1 threshold (+0.10) exceeded total available headroom (~0.05) | Dynamic threshold: `max(0.03, min(0.10, (1 − pilot_fc_mean) × 0.5))`; hard stop if `pilot_fc_mean ≥ 0.80` |
| 5 | `3363672c` | Majority-vote IDR suppressed ensemble recall (0.77 vs 0.87 union) | Union IDR for ensemble (any-assessor-found); majority-vote for verdict only |

**Explicit constraint:** `_pipeline.proxy_mean` is **NOT** an input to `select_cases.py`. The Stage 5 smoke test role is structural validation (`gate_pass`) only.

**PM class note:** The `stage3_mixed_assembler.md` `acceptable_resolutions` bug (fixed in Phase 0) is structurally identical to PM1: an upstream artifact silently overrides the scoring engine's intended behavior, making a primary hypothesis untestable with no runtime error. Spec-implementation divergence in prompt templates is the primary recurrence vector. The verification checklist grep item exists to catch future instances.

---

## Execution Phases

### Phase 0: Setup
- **[BLOCKING BUG — already fixed]** `stage3_mixed_assembler.md` `acceptable_resolutions`
  changed from `["mixed", "empirical_test_agreed", "critique_wins", "defense_wins"]` →
  `["empirical_test_agreed"]` only. Including all four verdicts makes `compute_fvc()` return
  1.0 for every condition, collapsing H1b. See Pipeline Architecture §3 for full context.
- **[DESIGN DOC]** DRQ ceiling of 0.5 for mixed cases is **intentional**: no agent produces
  a literal `"mixed"` verdict, so `ideal_debate_resolution.type = "mixed"` means DRQ maxes
  at 0.5 for mixed cases. FVC and ETD are co-primary. Do not "fix" this ceiling.
- Verify `uv`, agents installed in `~/.claude/agents/`
- Confirm env vars: `OPENROUTER_API_KEY`, `CROSS_VENDOR_API_KEY`
- Create v6 directory structure
- Update `self_debate_poc.py`:
  - Drop DC entirely
  - Union IDR for ensemble (any-assessor-found); majority-vote retained for verdict
  - Rename `forced_multiround` → `conditional_fm`
  - Add `biased_debate` to `CONDITIONS` and `ETD_CONDITIONS`
  - ⚠ `ETD_CONDITIONS` currently `{'isolated_debate', 'multiround', 'forced_multiround'}` — must add `biased_debate` and `conditional_fm`
- Audit orchestrator prompt and add `all_issues_adjudicated` as a new output field:
  - `all_issues_raised` — unchanged: issues from Critic raw output (used for existing IDP)
  - `all_issues_adjudicated` — NEW: issues from adjudicator synthesis after Defender exchange
  - Both fields stored in every output file; both fed to the scorer
  - Phase 7 reports IDP from each separately: `IDP_raw` (current definition) and `IDP_adj`
    (adjudicator-filtered, the "true" precision after adversarial challenge)
- RC scoring scope: **bidirectional with LLM** — score both (a) recall against documented RC
  flaws and (b) novel valid concerns the debate surfaces that the reproducer missed (GPT-4o
  scored). Both score types saved separately in rescore JSON for independent analysis.
  Commit to `HYPOTHESIS.md` before Phase 5.
- Create `biased_debate` agent prompt variants (critic + defender persona priming)
- Commit updated scoring engine and agent variants before any runs

### Phase 1: RC Data Acquisition
Build `pipeline/rc_extractor.py` and execute four stages (see RC Extraction Pipeline
Specification section for full schema and contamination prevention spec):

- **RC-1 (Fetch):** OpenReview API (RC 2020–2023) + ReScience C GitHub clone
  → `rc_candidates/reports_fetched.json`
- **RC-2 (Flaw extraction, GPT-4o):** Report text → structured flaw records;
  prompt explicitly separates "what the paper claims" from "what the reproducer found"
  → per-report flaw JSON
- **RC-3 (`must_not_claim` extraction, GPT-4o):** Separate LLM pass; identify sound design
  choices a pattern-matching reviewer might wrongly challenge → appended to flaw records
- **RC-4 (Filtering + contamination gate):** Apply exclusion criteria from `DATA_ACQUISITION.md`;
  **reject** any case where `task_prompt` contains reproducer-language keywords
  (`"we found that"`, `"failed to reproduce"`, `"could not replicate"`, etc.) — this is the
  PM1 recurrence prevention gate (see v5 Weakness Mitigation section)
- **Output:** `rc_candidates/rc_cases_raw.json`
- **Gate:** count usable cases; apply decision table (Design Decision §1)

### Phase 2: Case Library Assembly
**`normalize_cases.py` — Schema B field mapping (see Unified Schema B Definition section):**
- RC cases: `issue_id` → `planted_issues[].issue_id` + `must_find_issue_ids`;
  `corruption_id = null`; `sound_design_reference = null`; `is_real_paper_case = true`;
  `_pipeline.case_type = "rc"`
- Synthetic cases: pass through; `is_real_paper_case = false`;
  `_pipeline.case_type = "regular"` or `"mixed"`
- All cases: `difficulty = null` at normalization — filled by Phase 3 pilot rubric performance
- `acceptable_resolutions` must be a flat string array everywhere
- Validation gate: all normalized cases pass Schema B field check before selection

**`select_cases.py` — stratification and gating:**
- Target stratification: 60 critique + 20 defense + 40 mixed (Design Decision §2)
- Difficulty gating from **Phase 3 pilot rubric performance** (GPT-4o scorer)
- `_pipeline.proxy_mean` stored for traceability; **NOT** used as difficulty gate input
  (PM3 recurrence prevention — see v5 Weakness Mitigation section)
- Mixed stratum diversity: minimum 3 distinct domain clusters; no domain > 30% of mixed

**Execution:**
- Generate mixed cases: `uv run pipeline/orchestrator.py --mixed 40`
- If RC regular yield < 60: run synthetic regular cases with lower proxy threshold
- Normalize all sources: `uv run pipeline/normalize_cases.py`
- Select cases: `uv run pipeline/select_cases.py --tier-mixed 40`
- **Output:** `benchmark_cases_raw.json` (overcomplete candidate pool ~150+ cases)

### Phase 3: Pilot & Calibration
- Run baseline on ~30 candidate cases (Claude)
- Run same 30 with GPT-4o scorer
- Compute: `baseline_fc_mean`, `baseline_fvc_mixed`, cross-scorer agreement rate
- **Set H1a threshold:** `threshold = max(0.03, min(0.10, (1.0 - baseline_fc_mean) * 0.5))`
- **Set final N:** adjust up if pilot within-case variance > 0.05
- Discard cases where baseline FC > 0.80
- **Output:** `benchmark_cases_verified.json` (final case library)
- **Gate (hard stop):** `baseline_fc_mean < 0.80` AND `>= 80 regular + 30 mixed` pass filter

### Phase 4: Pre-Experiment Self-Review
- Dispatch `ml-critic` against `HYPOTHESIS.md` + evaluation rubric
- Dispatch `ml-defender`
- Up to 2 debate rounds
- **NEW from v5 lesson:** orchestrator prompt audit step — critic reviews batch agent context
  window composition to check for answer-key leakage vectors
- Generate PRE-1 through PRE-N pre-execution requirements
- Commit HYPOTHESIS.md + pre-execution requirements before Phase 5

### Phase 5: Benchmark Run
- 5 conditions × N cases × 3 runs
- Batch dispatch with isolation verification (no cross-condition context)
- `v6_raw_outputs/{case_id}_{condition}_run{idx}.json`
- Schema validation after each batch
- **Zero-variance contamination check:** after each batch, verify within-case variance > 0
  across all 3 runs — identical outputs across all 3 runs signals answer-key leakage
  (this is how v5 batch 2 contamination was detected; `V5_INSIGHTS_AND_AVENUES.md` Insight 6)
- **Expected volume:** ~120 × 6 × 3 = 2,160 files

### Phase 6: Cross-Model Scoring
- GPT-4o scores all 2,160 files on IDR/IDP/ETD
- **Bidirectional IDR:** two separate scores per file:
  - `idr_documented` — recall against documented RC flaws (primary)
  - `idr_novel` — novel valid concerns the debate raised that the reproducer missed (secondary)
  - Both saved in rescore JSON; primary analysis uses `idr_documented`; `idr_novel` reported separately
- **Dual IDP:**
  - `idp_raw` — precision from `all_issues_raised` (Critic raw; existing definition)
  - `idp_adj` — precision from `all_issues_adjudicated` (adjudicator synthesis; new field)
  - Both reported; `idp_raw` used for v5-comparable primary analysis
- ETD scoring on mixed-case debate outputs only
- Per-assessor `found` booleans stored for ensemble union IDR
- **Output:** `v6_rescored_idr_idp.json`

### Phase 7: Analysis
- `uv run self_debate_poc.py`
- All 5 hypothesis tests with bootstrap CIs
- Wilcoxon signed-rank for pairwise comparisons
- Per-case and per-dimension breakdowns
- Failure attribution taxonomy
- Within-case variance analysis
- **Output:** `v6_results.json`

### Phase 8: Sensitivity & Robustness
- Method A vs Method B aggregation divergence (flag if > 0.05)
- Threshold sensitivity analysis
- Per-dimension lift decomposition (where is the signal?)
- Difficulty stratification: validate labels predict rubric performance (Spearman rho)
- **IDP diagnostic (from v5 Insight 3):** If IDP is flat across all debate conditions
  (including biased_debate), audit whether `all_issues_raised` is extracted from Critic
  raw output vs. adjudicator synthesis. Flat IDP across all debate + biased_debate confirms
  orchestrator-level extraction bug, not a persona/protocol limitation.
- **FM hollow-round rate:** ⚠ Cannot validate conditional gate using v5 data — the v5
  schema repair pass set `point_resolution_rate = 0` as default for repaired files, making
  per-round hollow detection unreliable (`ENSEMBLE_ANALYSIS.md`). Use v6 native data only.
- **Output:** `SENSITIVITY_ANALYSIS.md`, `CONCLUSIONS.md`

### Phase 9: Cross-Vendor Validation
- Claude secondary scorer on same outputs
- Report Claude vs GPT-4o deltas on IDR/IDP/ETD
- Frame as confound quantification, not mitigation
- **Output:** `CROSS_VENDOR_VALIDATION.md`

### Phase 10: Reporting
- `REPORT.md` — full tables, limitations, related work
- `REPORT_ADDENDUM.md` — production deployment recommendation
- `ENSEMBLE_ANALYSIS.md` — union IDR analysis, debate vs ensemble
- `PEER_REVIEW_R1.md` — Opus peer review
- `FINAL_SYNTHESIS.md` — orchestrator synthesis
- `/artifact-sync` + coherence audit

---

## Files

### Create (new)
| File | Purpose |
|---|---|
| `PLAN.md` | This document |
| `HYPOTHESIS.md` | Pre-registered hypotheses (commit before Phase 5) |
| `pipeline/rc_extractor.py` | OpenReview API + ReScience C extraction |
| `pipeline/select_cases.py` | Case selection: mixed stratum + difficulty gate |
| `pipeline/normalize_cases.py` | Unify RC + synthetic schemas to benchmark format |

### Modify (existing v6)
| File | Change |
|---|---|
| `self_debate_poc.py` | Drop DC entirely; union IDR in ensemble scoring; `conditional_fm` condition |
| `pipeline/orchestrator.py` | `--rc-cases` input path for RC-sourced cases; conditional FM gate logic |
| `pipeline/prompts/stage3_mixed_assembler.md` | Fixed `acceptable_resolutions` bug (was all four verdicts; now `["empirical_test_agreed"]` only) |

### Reuse (no changes needed)
| File | Status |
|---|---|
| `pipeline/prompts/stage2_mixed_writer.md` | Ready |
| `V3_V5_CONTRAST.md` | Reference |
| `DATA_ACQUISITION.md` | Reference → implemented in `rc_extractor.py` |
| `MIXED_CASE_PLAN.md` | Reference → already implemented in `orchestrator.py` |

---

## Verification Checklist

- [ ] `stage3_mixed_assembler.md` outputs `acceptable_resolutions = ["empirical_test_agreed"]` only — grep to confirm
- [ ] All normalized cases pass Schema B field validation before Phase 3
- [ ] RC `task_prompt` passes contamination gate — no reproducer-language keywords present
- [ ] `_pipeline.proxy_mean` is NOT used as input to `select_cases.py` difficulty gating
- [ ] `acceptable_resolutions` is a flat string array (not nested object) in all benchmark case files
- [ ] Pilot gate: `baseline_fc_mean < 0.80`, >= 80 regular + 30 mixed pass filter
- [ ] Scoring isolation: GPT-4o scorer has no access to ground truth (answer keys)
- [ ] Conditional FM hollow rate < 10% (measure from v6 data only — v5 FM data unreliable due to schema repair)
- [ ] Union IDR (IDR only): per-assessor `found` booleans stored; majority-vote retained for verdict
- [ ] `ETD_CONDITIONS` in `self_debate_poc.py` includes `biased_debate` and `conditional_fm`
- [ ] RC scoring scope committed to HYPOTHESIS.md: bidirectional (recall + novel concerns, both saved)
- [ ] Orchestrator prompt audited: `all_issues_raised` extraction path verified (IDP mechanism)
- [ ] Cross-scorer: flag if GPT-4o vs Claude IDR delta > 0.50
- [ ] Zero-variance check run after each batch (identical outputs = leakage)
- [ ] Schema validation: all 2,160 output files pass before scoring
- [ ] All 6 hypotheses (H1a, H1b, H2, H3, H4, H6) have PASS/FAIL with CIs and effect sizes
- [ ] HYPOTHESIS.md committed to git before Phase 5
- [ ] `/artifact-sync` run after Phase 10

---

## Key Differences from v5

| Aspect | v5 | v6 |
|---|---|---|
| Case source | Synthetic planted corruptions | RC reports + synthetic mixed |
| Mixed cases | 0 (ETD always N/A) | 40 (33% of benchmark) |
| Baseline ceiling | 0.9452 | Target < 0.75 |
| IDR/IDP scorer | Claude (closed-loop) | GPT-4o (cross-model) |
| Ensemble IDR | Majority-vote (0.7679) | Union-of-issues |
| Forced multiround | Unconditional (20.5% hollow) | Conditional on unresolved disagreement |
| H1 threshold | +0.10 (fixed, no power analysis) | Set after pilot, <= 50% of headroom |
| DC dimension | Diagnostic-only | Dropped entirely |
| Primary signal | fc_lift on regular cases only | fc_lift (regular) + FVC lift (mixed) — co-primary |
| Compute matching | Implicit | Explicit: isolated ~3x = ensemble 3x |
| Conditions | 5 | 6 (adds biased_debate) |
| Ensemble aggregation | Majority IDR + majority verdict | Union IDR + majority verdict (split rule) |
| H4 (ETD) | Not tested | Directional: multiround > isolated on ETD |
| IDP mechanism | Unaudited (flat in v5) | Orchestrator extraction path audited before Phase 5 |
| Contamination detection | Post-hoc | Zero-variance check after each batch |
