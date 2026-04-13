# v6 → v7 Pipeline Design Audit

> **Purpose:** Systematic comparison of every v7 pipeline script and prompt against v6. Each
> change is classified as **INTENTIONAL** (authorized by v7 plan references), **AMBIGUOUS**
> (not contradicted by the plan but not explicitly authorized), or **ERRANT** (contradicts
> the v7 plan and should be fixed). Reference citations point to the authoritative plan
> documents under `plan/references/`.
>
> **Audit date:** 2026-04-13  
> **Branch:** feat/v7-phase1-rc-acquisition  
> **Methodology:** `diff -u` on shared files; direct read for new v7-only files; all findings
> checked against `design_decisions.md`, `hypotheses.md`, `API_DISPATCH_PLAN.md`,
> `model_assignments.md`, `v6_issues.md`, `v6_lessons.md`.

---

## Summary

| Category | Count |
|---|---|
| INTENTIONAL | 47 |
| AMBIGUOUS | 3 |
| ERRANT | 0 |

**No breaking changes found.** All three ambiguous items are cosmetic or documentation gaps, not
behavioral defects. Phase 4 coherence audit should resolve all three before Phase 5 begins.

---

## File Coverage

| File | Type | Status |
|---|---|---|
| `pipeline/orchestrator.py` | Shared script | Changed |
| `pipeline/normalize_cases.py` | Shared script | Changed |
| `pipeline/select_cases.py` | Shared script | Changed |
| `pipeline/rc_extractor.py` | Shared script | Changed |
| `pipeline/prompts/stage1_hypothesis_generator.md` | Shared prompt | Identical (no diff) |
| `pipeline/prompts/stage2_design_writer.md` | Shared prompt | Identical (no diff) |
| `pipeline/prompts/stage2_mixed_writer.md` | Shared prompt | Identical (no diff) |
| `pipeline/prompts/stage3_corruption_node.md` | Shared prompt | Identical (no diff) |
| `pipeline/prompts/stage3_mixed_assembler.md` | Shared prompt | Identical (no diff) |
| `pipeline/prompts/stage4_ground_truth_assembler.md` | Shared prompt | Changed |
| `pipeline/prompts/stage4_defense_assembler.md` | **v7-only (new)** | New |
| `pipeline/prompts/critic.md` | **v7-only (new)** | New |
| `pipeline/prompts/defender_isolated.md` | **v7-only (new)** | New |
| `pipeline/prompts/multiround_2r_defender.md` | **v7-only (new)** | New |
| `pipeline/prompts/adjudicator.md` | **v7-only (new)** | New |
| `pipeline/phase5_benchmark.py` | **v7-only (new)** | New |
| `pipeline/v7_scoring.py` | **v7-only (new)** | New (replaces `pilot_scorer.py`) |
| `pipeline/pilot_scorer.py` | **v6-only (removed)** | Removed |
| `pipeline/BIASED_DEBATE_SPEC.md` | **v6-only (removed)** | Removed |

---

## 1. Shared Scripts

### 1.1 `orchestrator.py`

| Change | Description | Verdict | Reference |
|---|---|---|---|
| Module docstring | Updated from "v6 extension: adds mixed-case" to "v7 case generation (regular + mixed paths)" plus defense path description | INTENTIONAL | `design_decisions.md §2` |
| `--defense N` CLI flag | New argument adds defense case count; mechanism IDs `mech_df001…` | INTENTIONAL | `design_decisions.md §2 (n=40 defense stratum)` |
| `DEFAULT_MODELS` model slugs | All 8 models upgraded per generation/slug table | INTENTIONAL | `model_assignments.md "Changes from v6"` |
| `run_stage1_all()` | Extended to generate hypotheses for `batch_size + mixed_count + defense_count` | INTENTIONAL | `design_decisions.md §2` |
| `run_stage4_defense()` | New function: assembles ground truth for defense cases via `stage4_defense_assembler.md`; no corruption report; outputs `correct_position='defense_wins'`, `planted_issues=[]` | INTENTIONAL | `design_decisions.md §2; v6_lessons L7` |
| `run_case_defense()` | New function: Stage 2 → Stage 4D pipeline with recycle logic; no Stage 3, no smoke test | INTENTIONAL | `design_decisions.md §2: "Defense path: Stage 1 → Stage 2 → Stage 4D, no smoke test"` |
| `assemble_batch()` total calculation | `batch_size + mixed_count` → `batch_size + mixed_count + defense_count` | INTENTIONAL | `design_decisions.md §2` |
| `assemble_batch()` regular filter | `case_type != 'mixed'` → `case_type == 'regular'` | INTENTIONAL | 3-stratum design requires explicit filter; `'defense'` cases would otherwise be miscounted as regular |
| Summary logging | Adds `[blue]{N} defense[/blue]` to case count printout | INTENTIONAL | Follows defense path addition |
| `config` dict | Adds `"defense_count": args.defense_count` | INTENTIONAL | Required by defense path |
| Usage example | Updated to `--batch-size 160 --mixed 80 --defense 40` | INTENTIONAL | `design_decisions.md §2` target counts |
| `argparse` description | "Pipeline Orchestrator v6 — regular + mixed" → "v7 — regular + mixed" | AMBIGUOUS | Updated version but still omits "defense" from description despite defense path addition; cosmetic gap, not breaking |

### 1.2 `normalize_cases.py`

| Change | Description | Verdict | Reference |
|---|---|---|---|
| Module docstring | CLI description updated; sources now explicit CLI flags rather than auto-discovery | INTENTIONAL | Explicit flags prevent silent missing-source failures |
| Output filename | `benchmark_cases_raw.json` → `benchmark_cases_v7_raw.json` | INTENTIONAL | Prevents v6 file collision |
| Input CLI flags | `--rc`, `--synthetic-regular`, `--synthetic-mixed`, `--synthetic-defense` replace implicit auto-discovery | INTENTIONAL | Explicit is better than magic glob for multi-stratum pipeline |
| `VALID_CORRECT_POSITIONS` | `{"critique", "defense", "mixed"}` → `{"critique_wins", "defense_wins", "empirical_test_agreed"}` | INTENTIONAL | Canonicalization; v6 stored short-form tokens breaking scoring |
| `VALID_ACCEPTABLE` | Aliases `"mixed"` and `"defense"` removed; set is now strictly canonical | INTENTIONAL | Canonicalization; normalizer now ensures canonical output before validation |
| `VALID_CATEGORIES` | Adds `"defense"` | INTENTIONAL | `design_decisions.md §2` |
| `VALID_PIPELINE_CASE_TYPES` | Adds `"defense"` | INTENTIONAL | `design_decisions.md §2` |
| `_verdict_to_correct_position()` | Now maps short-form → canonical (`"critique"` → `"critique_wins"`, `"mixed"` → `"empirical_test_agreed"`) with pass-through for already-canonical tokens | INTENTIONAL | Bug fix: v6 pipeline stored short-form tokens; `normalize_cases.py` fix is the bridge |
| `_correct_position_to_idr_type()` | Keys updated from short-form to canonical | INTENTIONAL | Follows token canonicalization |
| `_correct_position_to_acceptable_resolutions()` | Keys updated from short-form to canonical | INTENTIONAL | Follows token canonicalization |
| `_normalize_synthetic_regular()` ground_truth | `final_verdict`/`correct_verdict` now set from `correct_position` (canonical) not raw `correct_verdict` (stage4 short-form) | INTENTIONAL | Bug fix: v6 was storing `"critique"` instead of `"critique_wins"` in these fields |
| `_normalize_synthetic_mixed()` ground_truth | `correct_position` changed from `"mixed"` → `"empirical_test_agreed"`; `correct_verdict` field added | INTENTIONAL | Schema B canonicalization; `correct_verdict` field was missing in v6 |
| `_normalize_synthetic_defense()` | New normalizer for defense path; `correct_position='defense_wins'`, `planted_issues=[]`, `must_find_issue_ids=[]` | INTENTIONAL | `design_decisions.md §2; v6_lessons L7` |
| `_normalize_rc_case()` correct_position | Now run through `_verdict_to_correct_position()` mapper | INTENTIONAL | RC extractor may output short-form tokens; mapper handles them uniformly |
| `_normalize_rc_case()` category assignment | Adds `"defense"` branch: `correct_position == 'defense_wins'` → `category = 'defense'` | INTENTIONAL | `design_decisions.md §2` |
| `_normalize_rc_case()` ground_truth | Adds `correct_verdict` field | INTENTIONAL | Schema B completeness |
| `_normalize_rc_case()` mixed check | `correct_position == 'mixed'` → `correct_position == 'empirical_test_agreed'` | INTENTIONAL | Follows token canonicalization |
| Validation: category/correct_position | Checks updated to canonical tokens; defense/defense_wins cross-check added | INTENTIONAL | Follows token canonicalization and defense stratum |
| `VALID_IDR_TYPES` | Still contains `"mixed"` (not `"empirical_test_agreed"`) | AMBIGUOUS | IDR type vocabulary is intentionally distinct from correct_position vocabulary (`ideal_debate_resolution.type` uses `"mixed"` as shorthand); `_correct_position_to_idr_type` maps `empirical_test_agreed → "mixed"`. Not an error, but the asymmetry is subtle and undocumented |

### 1.3 `select_cases.py`

| Change | Description | Verdict | Reference |
|---|---|---|---|
| Module docstring | Updated stratification counts: 60/20/40 → 160/40/80 | INTENTIONAL | `design_decisions.md §2` |
| `DEFAULT_TIER_CRITIQUE` | 60 → 160 | INTENTIONAL | `design_decisions.md §2` |
| `DEFAULT_TIER_DEFENSE` | 20 → 40 | INTENTIONAL | `design_decisions.md §2` |
| `DEFAULT_TIER_MIXED` | 40 → 80 | INTENTIONAL | `design_decisions.md §2` |
| `--pool` default | `benchmark_cases_raw.json` → `benchmark_cases_v7_raw.json` | INTENTIONAL | Consistent with normalize_cases.py v7 output filename |
| `--output` default | `benchmark_cases_verified.json` → `benchmark_cases_v7_verified.json` | INTENTIONAL | v7 file naming |
| `_load_pilot_results()` | Added list-format handling (`[{case_id, fc, ...}]`) in addition to dict format | INTENTIONAL | v7 `v7_scoring.py --mode pilot` emits list format; dict format was v6 `pilot_scorer.py` format |
| `critique_pool` filter | Was: `category == 'regular' AND correct_position == 'critique'`; now: `category == 'regular'` | INTENTIONAL | In v7, defense is a separate category (not a sub-type of regular). All regular cases have `correct_position == 'critique_wins'`. The old filter would silently exclude hypothetical regular+defense_wins cases that no longer exist. |
| `defense_pool` filter | Was: `category == 'regular' AND correct_position == 'defense'`; now: `category == 'defense'` | INTENTIONAL | Defense is a top-level stratum in v7, not a sub-type of regular; `design_decisions.md §2` |
| `_sanitize_case()` + `--sanitize` flag | New function strips ground-truth fields; produces sanitized input for Phase 5 benchmark runner | INTENTIONAL | `v6_lessons L6`: ground-truth leakage prevention; `API_DISPATCH_PLAN.md` §Resume |
| Summary table row labels | "Critique" → "Regular" | INTENTIONAL | Correct label for v7 stratum |
| Summary total | Hardcoded `120` → computed `v7_total` (280) | INTENTIONAL | `design_decisions.md §2` |

### 1.4 `rc_extractor.py`

| Change | Description | Verdict | Reference |
|---|---|---|---|
| Module docstring | Model references updated: `GPT-4o` → `GPT-5.4` in stage descriptions | INTENTIONAL | `model_assignments.md` |
| `DEFAULT_MODELS` | `rc2`/`rc3`: `openai/gpt-4o` → `openai/gpt-5.4` | INTENTIONAL | `model_assignments.md` |
| `--concurrency` default | 4 → 100 (help text already said "default: 100" in v6 — code and docs were inconsistent) | INTENTIONAL | High concurrency rule (memory); also repairs a pre-existing v6 bug where help text and code default disagreed |
| `run_rc4` parameter | `_config` → `config` (underscore removal) | INTENTIONAL | Function now uses `config` for `target_count`; leading underscore implied unused, which was wrong in v7 |
| `--target-count` flag + cap logic | New optional flag caps final RC-4 output by extraction confidence rank | INTENTIONAL | Phase 1 operational control: allows targeting exactly the RC cases needed for v7 pool without manual filtering |

---

## 2. Shared Prompts

### Stage 1–3, stage3_mixed_assembler (5 files)

**No changes.** All five prompts are byte-for-byte identical between v6 and v7. Case generation
prompts (hypothesis, design, corruption, mixed assembly) are unchanged because these pipeline
stages are unchanged in v7. The defense path adds `stage4_defense_assembler.md` rather than
modifying existing stages.

### `stage4_ground_truth_assembler.md`

| Change | Description | Verdict | Reference |
|---|---|---|---|
| Scope header added | New note at top directing readers to `stage3_mixed_assembler.md` for mixed cases and `stage4_defense_assembler.md` for defense cases | INTENTIONAL | Documentation clarity with 3 assemblers now in scope |
| `correct_verdict` template token | `"critique | defense_wins"` → `"critique_wins | defense_wins"` | INTENTIONAL | Canonical token; trains LLM to output `critique_wins` not `critique`; normalizer handles fallback but canonical output is preferred |

---

## 3. New v7-Only Files

### 3.1 `stage4_defense_assembler.md` (new prompt)

**Authorized by:** `design_decisions.md §2` (defense stratum n=40); `v6_lessons L7` (0/20 exoneration
rate diagnosed; explicit `defense_wins` output path required).

| Design element | Conforms to plan? | Notes |
|---|---|---|
| `correct_verdict: "defense_wins"` always | YES | `design_decisions.md §2`: "correct_position='defense_wins'"  |
| `planted_issues: []` always | YES | Defense cases have no planted flaws by definition |
| `must_find_issue_ids: []` always | YES | Nothing to find; IDR/IDP undefined for defense |
| `must_not_claim` field with 3–5 entries | YES | v6_lessons L7: "the critic is prompted to find flaws and will find or manufacture them" — must_not_claim captures legitimate design choices that look suspicious but are not flaws |
| `acceptable_resolutions: ["defense_wins"]` | YES | `design_decisions.md §2` |
| `difficulty_justification` field | YES | Required for Phase 3 difficulty gating |

### 3.2 `critic.md` (new prompt)

**Authorized by:** `API_DISPATCH_PLAN.md §3.1` (adapted from `plugins/ml-lab/ml-critic.md`).

| Design element | Conforms to plan? | Notes |
|---|---|---|
| Skeptical ML engineer persona | YES | `API_DISPATCH_PLAN.md §3.1`: "Persona: skeptical ML engineer with applied mathematics background" |
| Numbered issues structure (claim, mechanism, evidence) | YES | `API_DISPATCH_PLAN.md §3.1`: "critique structure: numbered issues, each with (1) specific claim, (2) why it might be wrong with mechanism, (3) what constitutes evidence" |
| Focus areas match spec | YES | Synthetic data, evaluation flaws, missing baselines, distributional assumptions, leakage, failure modes, metric limitations, silent misconfiguration, prerequisite assumptions — all present |
| `defense_wins` verdict path with `all_issues_raised: []` | YES | `design_decisions.md §2`: "v7 Phase 0 adds an explicit JSON path {'verdict': 'defense_wins', 'all_issues_raised': [], ...} with the prompt instruction: 'A confident no significant issues conclusion is as important as identifying genuine flaws'" |
| `empirical_test_agreed` as a valid verdict | YES | Required for mixed cases; `design_decisions.md §2` |
| JSON-only output (no prose wrapper) | YES | `API_DISPATCH_PLAN.md §3.1` output format |
| No file-reading instructions | YES | `API_DISPATCH_PLAN.md §3.1`: "strips Mode 1/2/3 file-reading instructions (no HYPOTHESIS.md/poc.py in benchmark context)" |

### 3.3 `defender_isolated.md` (new prompt)

**Authorized by:** `API_DISPATCH_PLAN.md §3.2` (adapted from `plugins/ml-lab/ml-defender.md`,
isolated variant).

| Design element | Conforms to plan? | Notes |
|---|---|---|
| No cross-visibility: "You have NOT seen any critic output" | YES | `API_DISPATCH_PLAN.md §3.2`: "Isolated defender: does NOT see critic output. Prompt says 'Anticipate likely criticisms and pre-emptively defend the design.'" |
| Two-pass structure | YES | `API_DISPATCH_PLAN.md §3.2`: "Two-pass structure: Pass 1 = full analysis, Pass 2 = verdict selection" |
| Critical verdict calibration rule | YES | `API_DISPATCH_PLAN.md §3.2`: "if Pass 1 identifies multiple critical flaws, overall verdict must not be defense_wins" |
| Fast concession on genuine flaws | YES | `API_DISPATCH_PLAN.md §3.2` calibration rule |
| JSON-only output | YES | `API_DISPATCH_PLAN.md §3.2` output format |

### 3.4 `multiround_2r_defender.md` (new prompt)

**Authorized by:** `API_DISPATCH_PLAN.md §3.2` (debate variant, defender sees critic output).
This prompt is the key mechanism for H3 (information-passing isolation test).

| Design element | Conforms to plan? | Notes |
|---|---|---|
| Defender receives full critic output | YES | `design_decisions.md §1`: "multiround_2r: defender-visibility (defender sees critic) and a hard 2-round cap"; H3 depends on this distinction |
| Point-by-point response structure | YES | `API_DISPATCH_PLAN.md §3.2`: "Respond to the critic's analysis point by point" |
| Same calibration rules as isolated variant | YES | `API_DISPATCH_PLAN.md §3.2` |
| JSON-only output | YES | Same schema as isolated defender |
| Distinction from isolated_debate enforced | YES | The word "Debate" in title and "AND a critic's analysis" in task make the condition difference explicit — directly supports H3 mechanism test |

### 3.5 `adjudicator.md` (new prompt)

**Authorized by:** `API_DISPATCH_PLAN.md §3.3` ("entirely new — no existing agent to adapt from").

| Design element | Conforms to plan? | Notes |
|---|---|---|
| Neutral stance | YES | `API_DISPATCH_PLAN.md §3.3`: "Neutral stance — not biased toward critic or defender" |
| Per-issue triage (SURVIVES/DROP) | YES | `API_DISPATCH_PLAN.md §3.3`: determines if defender response adequately addresses each issue |
| DROP only when rebuttal is clearly sufficient | YES | `API_DISPATCH_PLAN.md §3.3` conservative DROP rule |
| Mixed-case instruction in prompt file | **ABSENT** | `v6_lessons L4`: "the adjudicator must receive an explicit instruction for mixed cases." The prompt file contains no mixed-case language. **However**, `phase5_benchmark.py` injects this instruction at runtime via `_build_adjudicator_input(is_mixed=True)` and the module-level `MIXED_CASE_ADJUDICATOR_SUFFIX` constant. The implementation is correct, but the prompt file alone is misleading. → **AMBIGUOUS** |
| JSON-only output | YES | `API_DISPATCH_PLAN.md §3.3` output format |
| Empty `all_issues_adjudicated` path for full defense | YES | Prompt documents this case |

### 3.6 `phase5_benchmark.py` (new script)

**Authorized by:** `API_DISPATCH_PLAN.md` (the entire document describes this script).

| Design element | Conforms to plan? | Notes |
|---|---|---|
| 4 conditions only: `baseline`, `isolated_debate`, `ensemble_3x`, `multiround_2r` | YES | `design_decisions.md §1`; `API_DISPATCH_PLAN.md` v7 delta: "drop biased_debate and conditional_fm handlers" |
| No `biased_debate` handler | YES | Confirmed: `grep "biased" phase5_benchmark.py` returns empty. `BIASED_DEBATE_SPEC.md` correctly retired. |
| No `conditional_fm` handler | YES | `design_decisions.md §1`: dropped due to selection confound |
| `isolated_debate`: critic and defender run concurrently via `asyncio.gather` | YES | `API_DISPATCH_PLAN.md §Condition Dispatch`: "critic and defender run concurrently via asyncio.gather" |
| `multiround_2r`: exactly 3 API calls (critic → defender-sees-critic → adjudicator) | YES | `design_decisions.md §1`: "Exactly 3 API calls. No stop-detection. No conditional branching. No loop. Hard 2-round cap." |
| `ensemble_3x`: 3 parallel calls + per-assessor `assessor_results` stored | YES | Required for H5 per-assessor IDR; `design_decisions.md §3` |
| `_build_adjudicator_input(is_mixed=)` injects mixed-case suffix | YES | Satisfies `v6_lessons L4` |
| Atomic writes (`.tmp` → `os.rename()`) | YES | `v6_lessons L6`: "v6 produced cases where json.load() failed on partially-written files during concurrent execution" |
| Resume logic: skip completed `(case_id, condition, run_idx)` tuples | YES | `API_DISPATCH_PLAN.md §Resume/Idempotency` |
| `--max-concurrent` default 100 | YES | High concurrency rule |
| `VALID_VERDICTS` enforcement | YES | Post-parse verdict validation prevents schema drift |
| Model default: `anthropic/claude-sonnet-4.6` | YES | `model_assignments.md`: "phase5_benchmark.py → anthropic/claude-sonnet-4.6" |

### 3.7 `v7_scoring.py` (new script, replaces `pilot_scorer.py`)

**Authorized by:** `design_decisions.md §3` (scoring battery), `hypotheses.md H5`,
`model_assignments.md`.

| Design element | Conforms to plan? | Notes |
|---|---|---|
| Cross-vendor scorer: `openai/gpt-5.4-mini` | YES | `design_decisions.md §3`: "all IDR/IDP scoring in v7 uses openai/gpt-5.4-mini via OpenRouter"; `v6_lessons L5` |
| ETD removed from scoring dimensions | YES | `design_decisions.md §3`: "ETD removed — structural ceiling, no signal"; `v6_lessons L2` |
| `FAIR_COMPARISON_DIMS = ["IDR", "IDP", "DRQ", "FVC"]` | YES | `design_decisions.md §3` scoring battery |
| Defense/mixed cases: IDR/IDP nulls, no API call | YES | `design_decisions.md §3`: "IDR/IDP undefined for defense cases"; `scoring_targets.must_find_issue_ids` is empty |
| `ensemble_3x` per-assessor IDR + H5 classification | YES | `hypotheses.md H5`; `design_decisions.md §3`: "per_assessor_found boolean array must be present" |
| Union IDR for ensemble_3x | YES | `design_decisions.md §3`: "an issue is 'found' if any of the 3 assessors found it" |
| `--mode score` + `--mode analyze` combined in one script | YES | Single-script design per `API_DISPATCH_PLAN.md §Key Source Files` |
| `--concurrency` default 100 | YES | High concurrency rule |
| DRQ near-miss pairs: `(defense_wins, empirical_test_agreed)` | YES | Partial credit for defense_wins↔empirical_test_agreed transitions is a reasonable DRQ design; both verdicts indicate the reviewer was not far wrong |

---

## 4. Removed v6-Only Files

| File | Removal justified by | Verdict |
|---|---|---|
| `pipeline/pilot_scorer.py` | Replaced by `v7_scoring.py` which handles both Phase 3 pilot scoring (via `--mode pilot`) and Phase 6 cross-vendor scoring (via `--mode score`). v7 unifies these in one script with cross-vendor scorer, eliminating same-model pilot scoring. | INTENTIONAL (`v6_lessons L5`; `design_decisions.md §3`) |
| `pipeline/BIASED_DEBATE_SPEC.md` | `biased_debate` condition is dropped from v7. `design_decisions.md §1` explicitly states: "biased_debate — Bias sensitivity was an interesting secondary result in v6 but is not a primary claim in the paper." No `biased_debate` handler exists in `phase5_benchmark.py`. | INTENTIONAL (`design_decisions.md §1`) |

---

## 5. Ambiguous Items — Phase 4 Action Required

These three items are not breaking but should be resolved before Phase 4 pre-registration commit:

### A1 — orchestrator.py argparse description (cosmetic gap)

```
"Pipeline Orchestrator v7 — regular + mixed case generation"
```

The description omits the defense path despite orchestrator now supporting 3 paths. Should be:

```
"Pipeline Orchestrator v7 — regular + mixed + defense case generation"
```

**Risk:** Low. This is the `--help` text only and does not affect behavior.  
**Fix:** 1-line edit to `orchestrator.py`.

### A2 — `VALID_IDR_TYPES` vocabulary asymmetry (documentation gap)

`normalize_cases.py` contains `VALID_IDR_TYPES = {"critique_wins", "defense_wins", "mixed"}`.
The `"mixed"` token here is the `ideal_debate_resolution.type` vocabulary, which is intentionally
distinct from the `correct_position` vocabulary (`"empirical_test_agreed"`). The function
`_correct_position_to_idr_type` maps `"empirical_test_agreed"` → `"mixed"`.

This is correct, but a reader seeing both `VALID_CORRECT_POSITIONS` (all-canonical) and
`VALID_IDR_TYPES` (uses `"mixed"`) may conclude the latter is a bug.

**Risk:** Low. No behavioral impact; the mapping is correct and the sets validate different fields.  
**Fix:** Add a comment in `normalize_cases.py` near `VALID_IDR_TYPES` explaining the vocabulary split.

### A3 — adjudicator.md mixed-case instruction is runtime-only (documentation gap)

`adjudicator.md` contains no mixed-case instruction. The instruction is injected at runtime
by `phase5_benchmark.py`'s `_build_adjudicator_input(is_mixed=True)` which appends
`MIXED_CASE_ADJUDICATOR_SUFFIX`. This satisfies `v6_lessons L4` behaviorally, but someone
reading `adjudicator.md` alone will not know the mixed-case instruction exists.

**Risk:** Low. If the prompt is ever adapted for a new context, the runtime injection may be
missed. Also obscures that the adjudicator behaves differently on mixed vs. regular cases.  
**Fix:** Add a comment at the top of `adjudicator.md`:

```
> Note: When processing mixed cases, the calling script appends an additional
> instruction: "This is a mixed case. Valid verdicts: critique_wins, defense_wins,
> empirical_test_agreed. Use empirical_test_agreed when both sides made substantive
> points only resolvable empirically."
> See phase5_benchmark.py MIXED_CASE_ADJUDICATOR_SUFFIX.
```

---

## 6. Key Invariants Confirmed

These were the highest-risk items to verify — all confirmed correct:

| Invariant | Status | Evidence |
|---|---|---|
| No `biased_debate` handler in `phase5_benchmark.py` | CONFIRMED | `grep "biased" phase5_benchmark.py` → empty |
| No `conditional_fm` handler in `phase5_benchmark.py` | CONFIRMED | Condition handler dict has exactly 4 keys |
| Mixed-case adjudicator injection active (L4) | CONFIRMED | `_build_adjudicator_input(is_mixed=)` + `MIXED_CASE_ADJUDICATOR_SUFFIX` in `phase5_benchmark.py` |
| Atomic writes in phase5_benchmark.py (L6) | CONFIRMED | `.tmp` → `os.rename()` pattern present |
| Cross-vendor scorer (L5) | CONFIRMED | `v7_scoring.py` uses `openai/gpt-5.4-mini`; `CROSS_VENDOR_API_KEY` env var |
| ETD removed from scoring battery (L2) | CONFIRMED | `FAIR_COMPARISON_DIMS = ["IDR", "IDP", "DRQ", "FVC"]` — no ETD |
| Union IDR for ensemble_3x (design_decisions §3) | CONFIRMED | `v7_scoring.py` `compute_ensemble_union_idr` + per-assessor rescoring |
| `defense_wins` verdict path in critic.md (L7) | CONFIRMED | Explicit `all_issues_raised: []` JSON path with "no significant issues" instruction |
| Defense cases excluded from P1/P2/H1a/H2/H4 (design_decisions §3) | CONFIRMED | `v7_scoring.py` writes nulls for IDR/IDP on defense/mixed cases; primary hypothesis tests operate on regular cases only |
| `multiround_2r` exactly 3 API calls, no loop (design_decisions §1) | CONFIRMED | `run_multiround_2r` function: critic → defender → adjudicator, no iteration |
