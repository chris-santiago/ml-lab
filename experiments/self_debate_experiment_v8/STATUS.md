# v8 Execution Status

**Objective:** Fix ml-lab's zero DER (defense exoneration rate) via prompt iteration, measured by
penalty-aware scoring. [→ OBJECTIVE.md]

**Branch:** `feat/v8-defender-iteration`  
**Last updated:** 2026-04-18

---

## What's Done

### Framework — Path B Pipeline [→ MODELS.md §Technical Architecture]

| Artifact | Status | Notes |
|---|---|---|
| `scripts/model_selector.py` | ✅ Done | `load()` + `model_generator()` (independent random draws); N→n bug fixed |
| `scripts/run_pipeline.py` | ✅ Done | Async critic→defender→adjudicator via OpenRouter; resume, seed file, dry-run, rich progress |
| `scripts/scorer.py` | ✅ Done | MCC, DER, IDR, FAR, FHR, ARR, VS (per-case majority + global kappa), Brier losses (critic + defender), AOR, wDCR, CER, NIT rate, FCE; penalty-aware scoring |

---

### Prompts [→ PROMPTS.md §Baseline Audit, §Interventions]

All three prompts rewritten from v7 baselines. Root causes addressed:

| Prompt | Status | Key changes from v7 |
|---|---|---|
| `prompts/CRITIC.md` | ✅ Done | NIT filter (exit path for "nothing found"), severity 0–10 scale, `flaw_category` field with 13-slug taxonomy, `no_material_findings` flag |
| `prompts/DEFENDER.md` | ✅ Done | Removed 5 concession instructions; added EXONERATE path + `defense_wins` MUST rule; presumption of soundness framing; removed implementation soundness pre-check bias |
| `prompts/ADJUDICATOR.md` | ✅ Done | Presumption of soundness; point verdict threshold rules; significance filter (MINOR → INFORMATIONAL not PENDING); experiment proposal gate |

These implement Interventions A, B, and C from PROMPTS.md. They are **starting versions** — not yet
validated. Canary iteration will determine which changes hold.

---

### Planning Docs

| Doc | Status | Change |
|---|---|---|
| `plan/EVALUATION.md` | ✅ Fixed | DER corrected from Precision→Recall on class SOUND; AOR added to metric table; VS split into per-case fraction + global Kappa |
| `plan/METRICS.md` | ✅ Fixed | AOR definition added after DCR; bottleneck diagnosis block added; Intervention C leading indicator updated from vague to `AOR ↓` |

---

### Canary Cases [→ CASES.md §Canary Set Composition, §Gate 1, §Gate 2]

| Task | Status | Notes |
|---|---|---|
| Case selection from v7 pool | ✅ Done | 42 cases: 20 defense / 12 regular / 10 mixed |
| v8 `flaw_category` labeling | ✅ Done | All 42 cases labeled; provenance in `label_cases.py` (original 40) + `_reshuffle_labels.json` (7 additions) |
| `canary_difficulty` labeling | ✅ Done | Defense: easy/medium/hard to exonerate; regular: easy/medium/hard flaw detection; mixed: low/medium/high ambiguity |
| Diversity reshuffle | ✅ Done | Swapped 3 homogeneous `context_dependent` synthetic mixed for 3 RC paper cases; added 2 regular for coverage; added 2 confirmed-hard defense cases |
| Gate 2 coverage check | ⚠️ Partial | 7 of 9 regular v8 categories covered in canary. **Gaps: `synthetic_data_assump` (zero v7 cases exist — full gap), `implicit_dist_assump` (unassigned in labeling pass)** |
| Defense difficulty balance | ⚠️ Partial | Current: 10 easy / 7 medium / 3 hard. Target: ~7/9/4. Three harder candidates deferred pending Gate 1 audit (see below) |

**Gate 1 deferred — 3 defense candidates with possible real flaws:**

| Case | Concern |
|---|---|
| `eval_scenario_897` | Temporal split + random incident assignment may be a genuine contradiction |
| `eval_scenario_068` | "AUPRC at fixed FPR" may be an invalid metric definition (real flaw, not just hard) |
| `hyp_204_case` | Feature-asymmetric model comparison may be genuinely confounded |

These were v7-labeled defense cases. Do not include until manually audited.

---

## Pre-Run Checklist [→ PROTOCOL.md §Pre-Run Checklist]

- [ ] **Phase 0 — Existence proof passed** [→ PROTOCOL.md §Phase 0, OBJECTIVE.md §Phase 0]
      Hand-craft ideal defender prompt on one obviously-sound case. Verify a model CAN produce
      `defense_wins`. If it cannot, execute fallback (dispatch to each pool model).
      _Blocks everything. Do not proceed to Phase 1 without this._

- [ ] **Phase 0.5 — Scoring validation complete** [→ PROTOCOL.md §Phase 0.5, SCORING.md §v7 Comparability]
      Run v7 prompts (unchanged) through the penalty-aware scorer. Record DER/IDR/FHR/ARR baseline.
      This establishes whether v7 DER=0.00 was a scoring artifact or a genuine prompt failure.
      _Canary baseline is meaningless without this._

- [ ] **IDR confirmed ≥ 0.75 under new scoring** [→ PROTOCOL.md §Phase 0.5]
      If IDR drops below 0.75 on v7 prompts, recalibrate the penalty function before any prompt work.

- [ ] **Phase 1 — Transcript reading complete** [→ PROTOCOL.md §Phase 1]
      Read all v7 defense-case transcripts. Classify failure mode distribution across the 6 types.
      Determines intervention priority (A vs B vs C first).
      _Pure human-work phase. Cannot be automated._

- [ ] **Gate 1 — Ground truth audit complete** [→ CASES.md §Gate 1]
      Audit all 20 canary defense cases. Confirm CONFIRMED SOUND / UNCERTAIN / HAS REAL FLAW.
      Fix or replace any HAS REAL FLAW cases before running.
      _Priority: audit the 3 deferred flagged cases above._

- [ ] **Gate 2 — Taxonomy coverage check complete** [→ CASES.md §Gate 2]
      Current gaps: `synthetic_data_assump` (no v7 source — needs new case generation),
      `implicit_dist_assump` (needs 1 additional case). Minimum 5 cases/category; target 10.
      _Blocking for full benchmark, not for canary iteration._

- [ ] **Model pool validated on OpenRouter** [→ MODELS.md §Pool Validation and Aging]
      Confirm all 12 models are currently listed and callable. Substitute any deprecated models
      per substitution rule. Confirm context limits match table.

- [ ] **qwq-32b decision made** [→ MODELS.md §qwq-32b]
      Choose: (a) remove from pool → use `qwen/qwen-2.5-72b-instruct`, (b) keep + handle
      reasoning trace parsing, (c) restrict to adjudicator role only.

- [ ] **Model seed file generated** [→ MODELS.md §Seed Control, PROTOCOL.md §Phase 2]
      Generate fixed model assignments for 42 canary cases × 3 runs = 126 evaluations.
      Format per MODELS.md §Seed assignment format. Hold constant across all canary iterations.

- [ ] **FHR baseline defined** [→ OBJECTIVE.md §Success Criteria]
      FHR target listed as "Define pre-run" — must set target before first canary run.

---

## Open Questions / Deferred

| Item | Source | Status |
|---|---|---|
| Gate 1 audit of 3 flagged defense candidates | CASES.md §Gate 1 | Deferred — manual review required |
| `synthetic_data_assump` coverage gap | CASES.md §Gate 2 | No v7 cases exist; needs new generation |
| Success deliverable defined | OBJECTIVE.md §Success Deliverable | Open question in plan — not resolved |
| Full benchmark scope (280 cases vs audited subset) | CASES.md §Sizing Reference | Depends on Gate 1/2 audit outcome |
| Statistical test for full benchmark | EVALUATION.md | McNemar's test via `scorer.py --compare` |

---

## Prompt Iteration Log [→ PROMPTS.md §Prompt Changelog Template]

_No iterations run yet. First entry will be the Phase 0.5 baseline._

| Version | Change | DER before | DER after | Verdict |
|---|---|---|---|---|
| baseline | v7 prompts under penalty-aware scoring | — | TBD | — |
| critic-v1 | NIT filter + severity taxonomy + flaw_category | TBD | — | pending |
| defender-v1 | Presumption of soundness + EXONERATE path | TBD | — | pending |
| adjudicator-v1 | Cost model + significance filter | TBD | — | pending |

---

## Labeling Provenance

| File | Covers | Status |
|---|---|---|
| `label_cases.py` | Original 40 cases (LABELS dict) | Should be committed |
| `_reshuffle_labels.json` | 7 additions from reshuffle pass | Should be committed |
| `canary_cases.json` | Final 42 labeled cases | ✅ Committed (d424ad4) |
| `canary_full.json` | Raw v7 source for all 42 cases | ✅ Committed (d424ad4) |
