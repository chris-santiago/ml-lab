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
| Defense difficulty balance | ✅ At target | Current: 10 easy / 7 medium / 6 hard (23 total). Gate 1 audit complete. |

**Gate 1 audit log:**

| Case | Verdict | Notes |
|---|---|---|
| `eval_scenario_897` | ✅ CONFIRMED SOUND (promoted) | UNCERTAIN → fixed: task_prompt rewritten to eliminate cross-period leakage ambiguity. Added as hard defense case. [→ decision ff5f4f51] |
| `eval_scenario_068` | ✅ CONFIRMED SOUND (promoted) | UNCERTAIN → fixed: "AUPRC at fixed FPR" was a category error; rewritten to Precision@FPR=10% with ROC-threshold framing. Added as hard defense case. [→ decision efea9209] |
| `hyp_204_case` | ✅ CONFIRMED SOUND (no rewrite) | Feature asymmetry is intentional — hypothesis tests full system vs. simple classifier; ablation (LambdaMART baseline-features-only) explicitly decomposes contributions. Added as hard defense case. [→ decision 00d25460] |

Also fixed: canary_full.json was out of sync with canary_cases.json (7 additions missing, 5 stale present). Both now at 43 cases. [→ discovery ff3a889d]

---

## Pre-Run Checklist [→ PROTOCOL.md §Pre-Run Checklist]

- [x] **Phase 0 — Existence proof passed** [→ PROTOCOL.md §Phase 0, OBJECTIVE.md §Phase 0]
      4-run controlled test on eval_scenario_858 (easy defense, IR/semantic search).
      Fixed critic=gpt-4o-mini, fixed adjudicator=mistral-small-2603, variable defender
      (claude-3-haiku, llama-4-maverick, deepseek-v3.2, gemma-4-31b-it). All 4 → defense_wins.
      [→ experiment 7a83d0a4] Two pipeline issues found and resolved:
      EXONERATE threshold validation [→ issue 7e829305, resolution 2931e241] and
      flaw_category taxonomy enforcement [→ issue f2d5f2f5, resolution bab135ab].
      Both fixed in run_pipeline.py (VALID_FLAW_CATEGORIES constant + defender warnings).

- [~] **Phase 0.5 — SUPERSEDED** [→ decision logged in journal]
      Original purpose: distinguish scoring artifact from prompt failure as cause of v7 DER=0.00.
      Superseded because: (1) v7 failure mode is documented — sycophantic concessions, not scorer
      miscounting; (2) Phase 0 confirms scorer functions correctly on live runs; (3) v7 prompts +
      v8 scorer is an uninterpretable counterfactual since both changed simultaneously; (4) the
      IDR ≥ 0.75 gate is better enforced by the first canary run on 12 real regular cases.
      _IDR floor still applies — checked on first canary iteration, not pre-run._

- [x] **Phase 1 — Transcript reading complete** [→ PROTOCOL.md §Phase 1, phase1_audit.json]
      Read all 40 v7 defense-case transcripts (multiround_2r condition, 120 runs total).
      Audit trail: `phase1_audit.json` — one entry per case with failure_mode, key_evidence,
      intervention_target, case_valid, consensus, needs_human_review.

      **Methodology:** Cases classified in three batches. First 5 classified interactively with user
      to calibrate discriminating rules; subagent ran batches 2 and 3 autonomously, reporting back
      for review. Classification applied three sequential rules: (1) case_valid check — read
      task_prompt for genuine fatal flaws before assigning a failure mode; (2) hypothesis-first check
      — identify whether critic attacked stated hypothesis or a reframed version; (3) design-has-the-
      answer check — scan task_prompt sections for explicit design controls addressing each critique.
      rc_rescience cases required an additional replication-scope check: critiques targeting original
      paper theory vs. critiques targeting the replication methodology itself.

      **Distribution (40 cases):**

      | Mode | Label | Count | % | Original target |
      |---|---|---|---|---|
      | 6 | Noise accumulation | 23 | 57.5% | A |
      | 3 | Weak rebuttal | 9 | 22.5% | B |
      | 2 | Partial concession | 4 | 10.0% | B |
      | 1 | Full concession | 2 | 5.0% | B |
      | 5 | Unfalsifiable critique | 2 | 5.0% | A |
      | 4 | Correct rebuttal, overridden | 0 | 0.0% | C |

      **Additional findings:**
      - `case_valid=false`: 3 cases (eval_scenario_789, eval_scenario_794,
        rc_rescience_2021_eaton2022reproduction_journal) — genuine design errors in these cases;
        critics were correct; these should be excluded or rewritten in the benchmark.
      - Mode 4 weak signals in 3 cases (harrison run2, luisa2022thompson Issue 1, mast2022 Run 0):
        defender made correct rebuttal, verdict still non-defense. No clean Mode 4 cases.
      - rc_rescience dominant failure: defenders never deployed replication-scope framing;
        conceded original-paper theory critiques as if defending the original authors.

      **Intervention priority decision (updated):** Mode 6 dominant pattern (57.5%) was initially
      mapped to Intervention A. On review: the critic's job is to surface all possible issues —
      filtering is the defender's and adjudicator's responsibility. Mode 6 is therefore re-read as
      primarily a B+C problem: defender needs confidence to dismiss individually-weak critiques;
      adjudicator needs severity aggregation (one significant flaw) rather than count aggregation
      (n partial concessions). See intervention discussion in journal. [→ decision TBD]

- [x] **Gate 1 — Ground truth audit complete** [→ CASES.md §Gate 1]
      All 3 deferred candidates audited and resolved: eval_scenario_897 (rewrite, promoted),
      eval_scenario_068 (rewrite, promoted), hyp_204_case (confirmed sound, no rewrite).
      All added as hard defense cases. Canary now 45 cases: 23 defense / 12 regular / 10 mixed.

- [ ] **Gate 2 — Taxonomy coverage check complete** [→ CASES.md §Gate 2]
      Current gaps: `synthetic_data_assump` (no v7 source — needs new case generation),
      `implicit_dist_assump` (needs 1 additional case). Minimum 5 cases/category; target 10.
      _Blocking for full benchmark, not for canary iteration._

- [x] **Model pool validated on OpenRouter** [→ MODELS.md §Pool Validation and Aging]
      Models sourced directly from OpenRouter website — available by construction.

- [x] **qwq-32b decision made** [→ MODELS.md §qwq-32b]
      Keep in pool. Reasoning trace parsing handled by `strip_think_tags()` in run_pipeline.py.
      Cost accounted for in MODELS.md estimate. CER inflation risk monitored via MES.

- [x] **Model seed file generated** [→ MODELS.md §Seed Control, PROTOCOL.md §Phase 2]
      canary_seeds.json: 42 cases × 3 runs = 126 assignments. random.seed(42), independent
      draws per run from 12-model pool. Hold constant across all canary iterations.

- [x] **FHR baseline defined** [→ OBJECTIVE.md §Success Criteria]
      No pre-run absolute target meaningful without data. Resolved: FHR floor is
      ≤ canary-run-1 + 0.05 (non-regression). First canary run sets the baseline.
      OBJECTIVE.md updated.

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
