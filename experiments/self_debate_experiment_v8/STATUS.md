# v8 Execution Status

**Objective:** Fix ml-lab's zero DER (defense exoneration rate) via prompt iteration, measured by
penalty-aware scoring. [→ OBJECTIVE.md]

**Branch:** `feat/v8-defender-iteration`  
**Last updated:** 2026-04-19 (question-4 DEFER gate + canary_run3/run4 complete; backstop reverted; ML_LAB_PORT_PLAN.md written)

---

## What's Done

### Framework — Path B Pipeline [→ MODELS.md §Technical Architecture]

| Artifact | Status | Notes |
|---|---|---|
| `scripts/model_selector.py` | ✅ Done | `load()` + `model_generator()` (independent random draws); N→n bug fixed |
| `scripts/run_pipeline.py` | ✅ Done | Async critic→defender→adjudicator via OpenRouter; resume, seed file, dry-run, rich progress |
| `scripts/scorer.py` | ✅ Done | MCC, DER, IDR, FAR, FHR, ARR, VS (per-case majority + global kappa), Brier losses (critic + defender), AOR, wDCR, CER, NIT rate, FCE; penalty-aware scoring |
| `scripts/run_pipeline.py` | ✅ Updated | **Adjudicator LLM call removed.** Pipeline is now critic → defender → `derive_verdict()`. Verdict derived deterministically from (original_severity, adjusted_severity, rebuttal_type) per finding; no API call, no sampling variance. [→ decision c93e0fb6] |
| `scripts/run_pipeline.py` | ✅ Updated | **Canary run 1 bug fixes:** (1) `adjusted_severity` floor clamped to `max(0, value)` in `validate_defender_output()` — defenders were emitting negative values trivially clearing the ≤3 threshold. (2) `build_critic_user_msg()` wrapper added — framing clarifies no separate code file exists, fixing "please provide implementation code" parse failures. (3) `max_tokens` raised to 8192 — unterminated JSON from output truncation. (4) `_sanitize_json_string()` added to `extract_json()` — handles literal control chars in model JSON output. (5) Plain-text no-findings fallback in `parse_response()`. [→ discovery 2b3ebbd8] |
| `scripts/run_pipeline.py` | ✅ Updated | **`derive_verdict()` FATAL rule:** FATAL findings (original_severity ≥ 7) partially rebutted to adj_sev 4–6 now yield `empirical_test_agreed` instead of `defense_wins`. Full clearance to adj_sev ≤ 3 required for exoneration. [→ discovery 2b3ebbd8] |

---

### Prompts [→ PROMPTS.md §Baseline Audit, §Interventions]

| Prompt | Status | Key changes |
|---|---|---|
| `prompts/CRITIC.md` | ✅ Done | NIT filter, severity 0–10 scale, `flaw_category` taxonomy, `no_material_findings` flag |
| `prompts/DEFENDER.md` | ✅ Updated | Added critic-exhaustiveness framing block; DEFER section-scan instruction. [→ experiment f634bda9] |
| `prompts/DEFENDER.md` | ✅ Updated | **Canary run 1 fix:** REBUT-IMMATERIAL restricted to MINOR findings (original sev 1–3) only; adjustment tightened to −1 to −2. All other adjustment caps tightened: REBUT-DESIGN −2 to −4, REBUT-SCOPE −2 to −4, REBUT-EVIDENCE −3 to −5. Proportionality guidance added. [→ discovery 2b3ebbd8] |
| `prompts/ADJUDICATOR.md` | ✅ Retired as LLM prompt | Now serves as spec document for `derive_verdict()`. Updated to reflect FATAL-finding rule: original_sev ≥ 7 + adj_sev 4–6 + REBUT-* → `empirical_test_agreed`. [→ decision c93e0fb6, discovery 2b3ebbd8] |
| `prompts/DEFENDER_R2.md` | ✅ Added | R2 defender prompt for multi-round protocol. Mirrors DEFENDER.md rebuttal logic with three-path decision tree (REBUT/DEFER/CONCEDE) for ACCEPT/CHALLENGE/PARTIAL verdicts from R2 critic. |
| `prompts/DEFENDER.md` | ✅ Updated | **Substantive DEFER requirement:** DEFER must name (1) specific settling experiment, (2) result that vindicates the design and mechanism, (3) result that validates the critique and what changes. "I'm not sure" is not a valid DEFER. [→ experiment ab4ee47f] |
| `prompts/DEFENDER_R2.md` | ✅ Updated | Same 3-question DEFER requirement applied to R2 pass. Invalid `challenge_verdict=DEFER` from R2 critic coerced to CHALLENGE in `run_multiround.py`. [→ experiment ab4ee47f] |
| `prompts/DEFENDER.md` | ✅ Updated | **Options A+C:** Resolve/mitigate distinction added — REBUT-DESIGN requires control *eliminates* mechanism; if only mitigates → DEFER. DEFER reframed as stronger than CONCEDE (design has partial answer vs. no answer). [→ commit 50bf6b4] |
| `prompts/DEFENDER_R2.md` | ✅ Updated | Same Options A+C applied to R2 pass — resolve/mitigate test in decision tree step 2; DEFER>CONCEDE reframing added. [→ commit 50bf6b4] |
| `scripts/run_multiround.py` | ✅ Updated | **Stage 4 framing fix:** `build_defender_r2_user_msg` rewritten to name all three R2 paths (REBUT/DEFER/CONCEDE) with explicit conditions. Old binary "defend or concede" framing suppressed DEFER awareness. [→ commit dd87a4f] |
| `prompts/DEFENDER_R2.md` | ✅ Updated | **FATAL REBUT-DESIGN text-citation gate:** REBUT-DESIGN on orig_sev ≥ 7 findings requires citation of specific named methodology text — logical inferences about what the design "implies" do not qualify. No specific text → DEFER or CONCEDE. [→ commit 2cb8406] |
| `prompts/DEFENDER.md` | ✅ Updated | **Question-4 conclusion-survival DEFER gate:** 4th required DEFER question — "Can the experiment's primary conclusion remain valid even if the critique is correct?" If the flaw would invalidate the primary metric or affect conditions asymmetrically, CONCEDE is required instead of DEFER. [→ commit 3b14db5] |
| `prompts/DEFENDER_R2.md` | ✅ Updated | Same question-4 conclusion-survival test applied to R2 pass. [→ commit 3b14db5] |
| `scripts/run_multiround.py` | ✅ REVERTED | **FATAL DEFER backstop added then reverted:** Rule `DEFER + orig_sev ≥ 7 + adj_sev ≥ 6 → critique_wins` added in derive_verdict(). Fired indiscriminately on any FATAL DEFER regardless of whether the flaw was conclusion-invalidating — caused widespread false critique_wins on ETA and defense_wins cases (canary_run3). Reverted. **DO NOT PORT.** The prompt-level question 4 is the correct mechanism. [→ commit 3b14db5; reverted] |

**Intervention priority (post question-4 + canary_run4):**
- Options A+C + Stage 4 framing fix: both validated — probe_ac3 confirmed ETA recovery; Opus 4.6 test confirmed IDR failure is prompt calibration, not capability ceiling.
- Question 4 (conclusion-survival test): added to DEFENDER.md + DEFENDER_R2.md. canary_run4 confirms IDR lift from 0.000 (run2) to ~0.60 while AER is dramatically better than backstop run3. Real signal.
- FATAL DEFER backstop: **REVERTED** — over-fires on any FATAL DEFER, blocking legitimate ETA/defense_wins cases. DO NOT PORT. Smarter backstop would need a `conclusion_survives` field from DEFER output JSON.
- IDR ceiling with Q4 alone: ~0.60 (705 regresses to ETA without backstop; 185 produces false CW on ETA case). Remaining IDR gap is partially addressable but requires either (a) field-level output from defenders confirming conclusion survival or (b) stronger Sonnet agents in ml-lab context.
- Pool: 8 models. haiku and maverick removed. Seeds patched.

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

- [x] **Pool trimmed to 8 models** [→ canary run 1 diagnostics + probe_ac3 + probe_stage4b]
      `xiaomi/mimo-v2-flash` dropped (extreme per-run variance + inverted critiques). [→ experiment f634bda9]
      `z-ai/glm-4.7-flash` dropped (4/27 timeouts/empty in canary run 1).
      `anthropic/claude-3-haiku` dropped (short-circuits as critic; malformed JSON as defender). [→ experiment 4919d0ee]
      `meta-llama/llama-4-maverick` dropped (same short-circuit pattern on critique_wins cases). [→ today]
      Pool now 8 models. canary_seeds.json, probe_ac_seeds.json, probe_stage4_seeds.json all patched.

- [x] **Model seed file generated** [→ MODELS.md §Seed Control, PROTOCOL.md §Phase 2]
      canary_seeds.json: 45 cases × 3 runs = 135 assignments. Holds constant across canary iterations.
      Patched twice: haiku critic exclusion (seed=99), then full haiku + maverick removal (seed=88).

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

## Protocol and Scoring Reframe

**Documented 2026-04-18 — based on user clarification of ml-lab design intent**

ml-lab is not a binary critic-wins / defender-wins system. It is a structured methodology review with three possible outcomes, each valid:

| Verdict | Meaning | Correct when |
|---|---|---|
| `critique_wins` | Undeniable flaw — no valid defense exists | Planted flaw with no design control |
| `empirical_test_agreed` | Genuine ambiguity — both sides argue well, empirical evidence needed | Real concern, methodology partially addresses it, significance is uncertain |
| `defense_wins` | Critic raised non-issues or misread the design | Sound methodology, no material flaws |

**`empirical_test_agreed` is a designed and expected outcome, not a failure mode.** The system explicitly anticipates ambiguity — this mirrors hard real-world cases where reasonable experts disagree. The correct protocol response is "run the experiment; data decides."

**Implication for scoring targets:**

Prior scoring framed IDR as rate of `critique_wins` on flawed cases. This was wrong — it penalized `empirical_test_agreed` on cases where the flaw is real but genuinely uncertain in significance. The correct FDR (Flaw Detection Rate) should be:

```
FDR = rate of NOT defense_wins on FLAWED cases
    = (critique_wins + empirical_test_agreed) / total flawed cases
```

DER (Defense Exoneration Rate) remains `defense_wins` / total SOUND cases. But `empirical_test_agreed` on a sound case is now acceptable — it means the system found genuine uncertainty, which may warrant an experiment even if the hypothesis was sound.

FAR (False Alarm Rate) should specifically track `critique_wins` on SOUND cases — the worst error mode (false accusation of an undeniable flaw on a sound design).

**Implication for protocol choice:**

ml-lab supports two primary protocols — both are valid, chosen by the user at the start:
- **Ensemble**: 3 independent critics, findings union-pooled, single defender pass
- **Multi-round**: R1 critic → R1 defender → R2 critic challenges → R2 defender

The prior canary iterations tested single-round (not either intended protocol). The correct evaluation should test the protocol ml-lab actually runs. Running full canary on single-round measures a baseline that doesn't reflect intended use.

**Defender calibration direction (from user):**
- Both critic and defender should stand firm for their full allotted rounds
- DEFER is the correct call for genuine ambiguity — not CONCEDE under pressure
- CONCEDE is reserved for undeniable flaws with no design control anywhere in the methodology
- The CONCEDE trigger in DEFENDER.md was over-aggressive; softened to allow DEFER on ambiguous cases

---

## Canary Run Log

*(Metrics use correct_position-aware scoring. DER = defense_wins recall on sound cases; FDR = NOT defense_wins on flawed; AER = ETA on ETA cases; IDR = critique_wins on 5 undeniable-flaw cases; FHR = ETA rate on clear-verdict cases.)*

| Run | Protocol | Key changes | DER | FDR | AER | IDR | FHR | MCC | Notes |
|---|---|---|---|---|---|---|---|---|---|
| canary_run1 | single-round | Framing block + DEFER instruction + deterministic verdict + 10-model pool | 1.00 | — | — | 0.083 | — | +0.169 | Pre-reframe; IDR used old binary metric. DER fixed; over-rebuttal |
| canary_run2 | single-round | REBUT-IMMATERIAL → MINOR; tighter caps; FATAL floor rule | 0.565 | — | — | 0.083 | — | +0.079 | Caps over-tightened: DER collapsed, IDR unchanged |
| canary_multiround_run1 | multi-round | Restored caps; CONCEDE trigger; 3-outcome reframe; re-labeled 6 ETA cases | 0.471 | 0.786 | 0.739 | 0.000 | 0.773 | −0.107 | ETA over-prediction: DEFER free path, FATAL rule fires on partial rebuttals |
| canary_multiround_run2 | multi-round | Substantive DEFER (3-question requirement) in DEFENDER.md + DEFENDER_R2.md | 0.588 | 0.536 | 0.217 | 0.600 | 0.227 | −0.064 | IDR recovered; AER collapsed (overcorrection) — IDR/AER tradeoff open |
| canary_multiround_run3 | multi-round | Options A+C + Stage 4 fix + FATAL text-citation gate + Q4 + **FATAL DEFER backstop** | ~0.10 | est. | ~0.05 | ~0.80 | — | — | Backstop over-fires on all FATAL DEFERs: 862 (confirmed ETA) → 3/3 CW; widespread DW/ETA flip to CW. 20 failures (14.8%). Only 4 cases correct. Backstop reverted. [→ experiment acd59c3e] |
| canary_multiround_run4 | multi-round | Same as run3 with backstop reverted; Q4 only | est. | est. | ~0.65 | ~0.60 | est. | est. | Q4 alone: IDR 0.000→~0.60 (801 2/2, 852 2/3, hyp_037 2/3). AER recovered vs run3. 705 regresses to ETA without backstop. 185 false CW on ETA case. 23 failures (17%). Net: meaningful improvement over run2 baseline. [→ experiment 3b22f651] |

---

### Multi-Round + Ensemble Probe Results (2026-04-18)

**Probe cases:** eval_scenario_858 (SOUND, defense) and eval_scenario_777 (FLAWED, regular)
**Seeds:** probe_run3_seeds.json (3 runs each, same model assignments across all protocol variants)

**Under original scoring (IDR = rate of `critique_wins` on FLAWED):**

| Protocol | 858 DER | 777 IDR | Notes |
|---|---|---|---|
| Single-round run3 (restored caps, CONCEDE trigger) | 3/3 = 1.00 | not measured | Pre-citation baseline |
| Multi-round + citation req | 0/2 = 0.00 | 2/3 = 0.67 | Citations dampened sound defense; over-concession on 858 |
| Multi-round (no citation req, DEFER guidance) | 1/3 = 0.33 | 1/2 = 0.50 | Defenders still conceding FATAL on sound case R1 |
| Ensemble (3 critics, no citations) | 0/2 = 0.00 | 1/3 = 0.33 | Spurious sev=9 from 3rd critic → FATAL rule fires on sound case |

**Under revised scoring (FDR = NOT `defense_wins` on FLAWED, `empirical_test_agreed` counts as correct):**

| Protocol | 858 (sound) no-false-alarm | 777 FDR | Notes |
|---|---|---|---|
| Multi-round (no citation, DEFER guidance) | 1/3 acceptable (1 ETA, 2 CW false alarms) | 1/2 = 0.50 (1 ETA ✓, 1 DW ✗) | False alarms from R1 defender conceding FATAL on sound |
| Ensemble | 2/2 acceptable (both ETA, no false alarms) | 2/3 = 0.67 (1 CW, 1 ETA, 1 DW) | ETA on sound = acceptable; ensemble narrows but doesn't eliminate misses |

**Key findings:**
- Citation requirement: indiscriminate — fires on sound cases as readily as flawed ones. Reverted.
- Multi-round concession pressure: R2 challenge creates pressure to update toward CONCEDE even when sound. DEFER guidance in DEFENDER_R2.md partially mitigates but doesn't eliminate it.
- Ensemble + FATAL rule: a spurious sev=9 from any critic → minimum adj_sev=4 → FATAL rule → ETA on sound case. Under new framing this is *acceptable* (not a false alarm in the old sense).
- `empirical_test_agreed` on flawed cases: correct outcome. 777 run0 (multi-round): critics found real orig=9/8 flaws, defender partially rebutted to adj=4 — ETA is the right verdict here.
- Dominant failure on 777: defenders bringing FATAL findings to adj_sev ≤ 3 via REBUT-DESIGN without conceding. FDR failure mode is over-rebuttal, not missing flaws entirely.

**Structural observations:**
- Single-round is the only protocol that consistently gives defense_wins on sound cases (DER=1.00)
- But single-round is not the intended ml-lab protocol
- Multi-round's R2 challenge step creates asymmetric pressure regardless of protocol variant
- The DEFER → ETA path is the system's designed resolution for genuine ambiguity; it was being suppressed by over-aggressive CONCEDE prompting

**canary_run1 failure analysis** [→ discovery 2b3ebbd8]:
- IDR=0.083 (11/12 flawed cases falsely exonerated)
- Dominant pattern: REBUT-IMMATERIAL misapplied to FATAL findings (sev 8–9) with −6 to −8 adjustments
- Floor bug: adjusted_severity going negative, trivially clearing the ≤3 threshold
- Cumulative zeroing: 8–10 findings all knocked to 0 with no concessions (wDCR=0.015)
- FATAL partially rebutted to adj_sev 4–6 still yielded `defense_wins` under old table

**Fixes applied before canary_run2:**
1. Code: `max(0, adjusted_severity)` floor enforcement in `validate_defender_output()`
2. DEFENDER.md: REBUT-IMMATERIAL restricted to MINOR (orig sev 1–3); adj −1 to −2
3. DEFENDER.md: All other adjustment caps tightened (REBUT-DESIGN −2 to −4, etc.)
4. derive_verdict(): orig_sev ≥ 7 + adj_sev 4–6 + REBUT-* → `empirical_test_agreed`

**canary_run2 failure analysis:**
- DER collapsed (1.00 → 0.565): caps over-tightened for REBUT-DESIGN/SCOPE/EVIDENCE.
  21 of 29 blocked defense findings had orig_sev 7–8; with −5 max they would reach adj_sev ≤ 3.
  8 sev-9 findings remain blocked even with −5 cap (FATAL rule applies; empirical_test_agreed correct).
- IDR still 0.083: CONCEDE trigger missing. 17 REBUT-DESIGN findings on flawed cases reach adj_sev ≤ 3
  regardless of cap level — defenders writing plausible-sounding but factually unsupported justifications.
  Cap changes cannot fix this; requires an explicit CONCEDE instruction.
- AOR jumped 0.017 → 0.308: FATAL rule is functioning (derive_verdict overrides on 31% of findings).

**Fixes applied before canary_run3:**
1. DEFENDER.md: Adjustment caps restored — REBUT-DESIGN −3 to −5, REBUT-SCOPE −3 to −5, REBUT-EVIDENCE −4 to −6
2. DEFENDER.md: CONCEDE trigger added — if no explicit methodology control addresses a FATAL/MATERIAL
   finding AND it would affect the primary metric, CONCEDE is required; do not fabricate design justifications

---

## Re-Labeling Pass (2026-04-18)

**Trigger:** Protocol and scoring reframe — `empirical_test_agreed` is now a valid and expected outcome for genuinely ambiguous cases. Prior labels applied `critique_wins` to all regular (flawed) cases, which was correct only for undeniable flaws (leakage, direct metric mismatch). Cases where a competent defender can produce a mechanistically valid partial rebuttal, and the significance is empirically uncertain, should be `empirical_test_agreed`.

**Labeling criterion (refined 2026-04-18, decision bdd068dd):**

- `defense_wins`: Two valid paths:
  1. Critic concerns are **clearly invalid** — scope errors, factual misreads, or strawman attacks. The critic is wrong.
  2. Critic concerns are **real but genuinely trivial** — they won't materially affect the primary metric or the experiment's conclusions. The defender correctly uses REBUT-IMMATERIAL.
  *Note: "planted_issues=[]" is not sufficient for this label. The right test is whether a competent critic would find anything real and material to push back on.*

- `empirical_test_agreed`: The design is sound but **real uncertainties remain that could materially affect conclusions**. Mitigation is not proof — when both critic and defender could be right, experiment provides empirical evidence. This is the **expected and correct outcome for most serious ML designs** with acknowledged limitations.

- `critique_wins`: No design control can rebut this. Undeniable flaws: preprocessing leakage, test-set contamination, direct hypothesis/metric mismatch. A competent defender scanning the methodology finds nothing to cite.

**Second re-labeling pass complete (2026-04-19):** All 23 `defense_wins` cases reviewed under the refined criterion. 6 re-labeled to `empirical_test_agreed`:

| Case | Reason |
|---|---|
| eval_scenario_858 | Proxy label validity (agent clicks) — ~300-query sanity check can't detect large-scale invalidity |
| eval_scenario_848 | 30-day phishing grace period → training labels ≥30 days behind current campaigns |
| eval_scenario_862 | 1–7 day label lag + 1-month test set — phishing campaigns evolve in days |
| eval_scenario_868 | 7-day dwell staleness + undefined 4-source label aggregation conflict resolution |
| eval_scenario_hyp_140_0 | 7-day alert disposition window selects for fast-resolution incidents only |
| hyp_155 | 30-day label exclusion window + frozen graph can't adapt to new senders in test |

Reviewed but kept `defense_wins`: hyp_204_case — subagent flagged 30-day maturation window, but this applies uniformly across all splits (no train/test asymmetry), unlike phishing staleness cases.

**Final case distribution (45 total):**

| Label | Count | % |
|---|---|---|
| `defense_wins` | 17 | 38% |
| `empirical_test_agreed` | 23 | 51% |
| `critique_wins` | 5 | 11% |

(Stratum counts unchanged: 23 defense / 12 regular / 10 mixed — correct_position now diverges from stratum for 12 cases.)

**Changes (7 cases re-labeled):**

| Case | Old | New | Reason |
|---|---|---|---|
| hyp_016_case_1 | critique_wins | empirical_test_agreed | Max-risk AUC limitation — defender can argue temporal patterns still show up in discrimination; horizon-specific test needs empirical verification |
| eval_scenario_773 | critique_wins | empirical_test_agreed | Unequal baseline tuning — whether tuning explains the gap requires running the experiment |
| eval_scenario_777 | critique_wins | empirical_test_agreed | Cohort restriction (≥12 months history) is defensible scope decision for a sequence model |
| eval_scenario_185 | critique_wins | empirical_test_agreed | Analyst escalation labels — "prioritizing analyst responses" is a valid SOC operational framing; proxy validity is genuinely uncertain |
| rc_rescience_2021_wang2022 | critique_wins | empirical_test_agreed | Partial reproduction with ambiguous results — some experiments worked, some didn't |
| eval_scenario_844 | critique_wins | empirical_test_agreed | Demand vs. fulfillment label proxy — whether they're correlated enough requires empirical verification |
| rc_rescience_2021_kirca2022 | critique_wins | empirical_test_agreed | Reproducibility ambiguity — central claims might hold despite documentation gaps |

**Unchanged (critique_wins, 5 cases):**

| Case | Flaw type | Why unchanged |
|---|---|---|
| eval_scenario_705 | Preprocessing leakage on full corpus | Undeniable — future data influenced scalers, no design scan rebuts this |
| hyp_037_stage4 | Preprocessing leakage on full corpus | Same |
| eval_scenario_801 | Stratified split (not chronological) + preprocessing leakage | Both issues are undeniable temporal leakage |
| eval_scenario_812 | Span-level hypothesis, report-level metric | Direct hypothesis/metric mismatch — no design rationale explains testing X with a metric for Y |
| eval_scenario_852 | Test set used in model selection | Test contamination is undeniable |

*(Post-first-pass intermediate distribution: 23 defense_wins / 17 ETA / 5 critique_wins — superseded by second pass at top of this section. Final distribution: 17 / 23 / 5.)*

**Files updated:** `canary_cases.json`, `canary_full.json` — `correct_position`, `final_verdict`, `correct_verdict`, and `ideal_debate_resolution.type` updated for all 7 cases.

---

## Future Consideration: Case Regeneration for 3-Outcome Framework

**Added 2026-04-18 — flag for next benchmark planning cycle**

The current canary set was generated under a binary flaw/sound framing and then re-labeled to fit the three-outcome system. The distribution reflects what was available from v7 (23 defense / 17 ETA / 5 critique_wins), not an intentional design toward the three outcomes. Consider regenerating cases purpose-built for this framework:

- **`critique_wins` cases (~20% target):** Unmistakable, undeniable flaws — preprocessing leakage that spans train/test, direct hypothesis-metric mismatches, explicit test contamination. A defender scanning the entire methodology finds nothing to cite. These should be relatively rare in real practice, which is why the target is ~20% rather than a third.

- **`defense_wins` cases (~40% target):** Sound methodology where a critic can raise plausible-sounding concerns, but a prepared defender scanning the task_prompt finds explicit controls, stated design rationales, or scope decisions that directly address every concern. The test is whether the system avoids false alarms.

- **`empirical_test_agreed` cases (~40% target):** The hardest category to construct well. The flaw should be real but not undeniable — a competent defender can produce a valid partial rebuttal (citing a scope decision, a stated control, or a design tradeoff), yet the significance of the flaw for the primary conclusion genuinely requires empirical verification. These cases test whether the system correctly surfaces ambiguity rather than forcing a winner.

**Generation guidance for ETA cases:** The most realistic ETA cases arise from: (a) unequal baseline tuning (tuning gap could explain the delta — but maybe not); (b) proxy label validity (label is imperfect but correlated — whether correlation is sufficient needs testing); (c) distribution shift within stated scope (methodology acknowledges limitation but doesn't quantify it); (d) partial reproducibility where some experiments transfer and others don't. Cases with planted flaws where a standard experimental ablation would settle the question are ideal ETA targets.

---

## Labeling Provenance

| File | Covers | Status |
|---|---|---|
| `label_cases.py` | Original 40 cases (LABELS dict) | Should be committed |
| `_reshuffle_labels.json` | 7 additions from reshuffle pass | Should be committed |
| `canary_cases.json` | Final 45 labeled cases | ✅ Committed |
| `canary_full.json` | Raw v7 source for all 45 cases | ✅ Committed |
| `canary_seeds.json` | 45 × 3 model assignments, seed=42, 10-model pool | ✅ Committed (ee419cf) |
