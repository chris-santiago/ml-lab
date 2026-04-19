# ml-lab Port Plan — v8 Debate Protocol

*Created: 2026-04-19 | Source: self_debate_experiment_v8*

This document tracks everything that must be ported from the v8 multi-round debate experiment into the ml-lab plugin (`plugins/ml-lab/`). Items are grouped by component. Check off each item as it lands.

---

## Background

The v8 experiment developed a structured, multi-round debate protocol that replaces ml-lab's existing prose-based critic/defender debate. Key calibration improvements:

- **Options A+C**: resolve/mitigate distinction for DEFER; DEFER > CONCEDE reframing
- **FATAL text-citation gate**: REBUT-DESIGN on FATAL findings requires specific methodology text
- **Question 4 / conclusion-survival test**: DEFER requires confirming primary conclusion survives the flaw
- **FATAL DEFER backstop**: `derive_verdict()` maps DEFER + orig_sev ≥ 7 + adj_sev ≥ 6 → `critique_wins`
- **Stage 4 user-message framing**: explicit three-path framing (REBUT / DEFER / CONCEDE)

The port is not incremental — it is replacing the prose debate protocol with a structured JSON protocol end-to-end.

### Architectural difference: fixed stages vs. convergence loop

The original ml-lab debate runs until **convergence or max_rounds** — critic and defender exchange rounds until all points are resolved or the cap is hit. v8 used a fixed 4-stage pipeline (Critic R1 → Defender R1 → Critic R2 → Defender R2) for calibration control, abandoning open-ended convergence.

The port must preserve both: the structured citation-challenge mechanism from v8 AND the convergence-loop capability from the original design. See the **Debate Loop Architecture** section below.

---

## Mode Change

- [ ] **Make debate mode the default** in `ml-lab.md` (currently ensemble)
- [ ] **Demote ensemble to opt-in** — document that ensemble is a high-recall sweep tool (no precision filter, no verdict), not the recommended path for go/no-go decisions
- [ ] Update ml-lab.md description and example prompts to reflect debate-as-default

---

## Debate Loop Architecture

The ported protocol generalizes the v8 fixed stages into two reusable stage types:

```
Stage A (Initial, runs once):
  ml-critic (R1) → ml-defender (R1)

Stage B (Challenge, repeatable):
  ml-critic-r2 → ml-defender-r2 → derive_verdict()
```

The orchestrator runs Stage A once, then loops Stage B until a stopping condition is met:

| Stopping condition | Action |
|---|---|
| `derive_verdict()` stable for 2 consecutive rounds (same case verdict, no finding moved) | Stop — converged |
| All advancing findings have adj_sev ≤ 3 or produced `defense_wins`/`critique_wins` | Stop — fully resolved |
| No finding changed `rebuttal_type` or `adj_sev` since the previous Stage B round | Stop — no movement |
| `max_rounds` reached | Force-resolve residual DEFERs; apply derive_verdict() and stop |

**Force-resolution at cap:** Any finding still in DEFER at max_rounds is treated as unresolved. The orchestrator applies derive_verdict() with current adj_sev values — the FATAL DEFER backstop fires if applicable; otherwise residual DEFERs yield ETA.

### Final vs. intermediate rounds

DEFENDER_R2.md currently uses "final rebuttal" framing, which is only correct in the last Stage B round. For intermediate rounds the framing must change:

- [ ] Add `is_final_round` parameter to the Stage B defender user message
- [ ] When `is_final_round=false`: "Produce your current position — the debate may continue if unresolved"
- [ ] When `is_final_round=true`: current DEFENDER_R2.md language ("produce your **final** rebuttal")
- [ ] CRITIC_R2.md needs no change — it is already designed to evaluate the defender's current citations regardless of round number

### Recommended defaults

- [ ] `min_rounds = 1` (always run at least one full Stage B cycle)
- [ ] `max_rounds = 3` (balances thoroughness against cost; configurable)
- [ ] Convergence check after each Stage B round before dispatching the next

---

## New Agent: ml-critic-r2

Currently absent from ml-lab. This agent is load-bearing — without it, the DEFENDER_R2 constraints (FATAL gate, question 4) have no adversarial pressure to work against.

- [ ] Create `plugins/ml-lab/ml-critic-r2.md` from `prompts/CRITIC_R2.md`
- [ ] Output schema: per-finding `challenge_verdict` (ACCEPT / CHALLENGE / PARTIAL), `updated_severity`, `reasoning`
- [ ] Register agent in ml-lab.md orchestration flow (dispatched between Defender R1 and Defender R2)

---

## Critic (ml-critic.md)

Port from: `prompts/CRITIC.md`

- [ ] **Severity scale**: adopt 1–10 numeric scale (currently prose-based in ml-lab)
- [ ] **FATAL / MATERIAL / MINOR taxonomy**: FATAL ≥ 7, MATERIAL 4–6, MINOR 1–3
- [ ] **NIT suppression**: NIT findings (severity 1–2 or flagged `suppressed: true`) excluded from advancing findings
- [ ] **Structured output schema**: `finding_id`, `severity`, `suppressed`, `title`, `description`, `failure_mechanism`, `proposed_resolution`
- [ ] **Calibration rules**: update ml-critic.md to match v8 CRITIC.md calibration guidance

---

## Defender R1 (ml-defender.md — Mode 1)

Port from: `prompts/DEFENDER.md`

- [ ] **7 rebuttal types**: CONCEDE / REBUT-DESIGN / REBUT-SCOPE / REBUT-EVIDENCE / REBUT-IMMATERIAL / DEFER / EXONERATE (currently 3 in ml-lab: Concede / Rebut / Empirically open)
- [ ] **Severity adjustments**: per-type ranges (REBUT-DESIGN: −3 to −5, REBUT-EVIDENCE: −4 to −6, REBUT-IMMATERIAL: −1 to −2, DEFER/CONCEDE: 0)
- [ ] **REBUT-IMMATERIAL restriction**: MINOR only (orig_sev 1–3)
- [ ] **Resolve/mitigate distinction (Option A)**: REBUT-DESIGN requires elimination, not just mitigation → DEFER if only mitigates
- [ ] **DEFER > CONCEDE reframing (Option C)**: DEFER = partial design answer; CONCEDE = no design answer
- [ ] **Question 4 — conclusion survival test**: before DEFER, confirm primary conclusion survives if critique is correct; if no → CONCEDE
- [ ] **CONCEDE scan rule**: scan methodology for named controls before conceding FATAL/MATERIAL findings
- [ ] **Structured JSON output schema**: `finding_id`, `original_severity`, `rebuttal_type`, `severity_adjustment`, `adjusted_severity`, `justification`
- [ ] **Overall verdict field**: `overall_verdict` (defense_wins / empirical_test_agreed / critique_wins)

---

## Defender R2 (ml-defender.md — Mode 2)

Port from: `prompts/DEFENDER_R2.md`

- [ ] **Three-path framing**: REBUT / DEFER / CONCEDE (not binary defend-or-concede)
- [ ] **FATAL REBUT-DESIGN text-citation gate**: orig_sev ≥ 7 → REBUT-DESIGN requires specific named methodology text, not logical inference
- [ ] **Resolve/mitigate test on R2 challenges**: challenged REBUT-DESIGN must pass same resolve test; if only mitigates → switch to DEFER
- [ ] **Question 4 in R2 context**: maintained from Defender R1 — still required for DEFER at Stage 4
- [ ] **R2 challenge response field**: `r2_challenge_response` (MAINTAINED / CONCEDED / STRENGTHENED / DEFERRED)
- [ ] **Severity adjustment caps**: same as R1 (no escalation in R2)
- [ ] **DEFER substantive test**: all four questions required (including question 4)
- [ ] **Structured JSON output schema** matching DEFENDER_R2.md format

---

## Verdict Derivation

Port from: `scripts/run_multiround.py` → `derive_verdict()`

Currently absent from ml-lab (orchestrator reads prose verdict from DEFENSE.md).

- [ ] **Implement `derive_verdict()` as deterministic logic** in the orchestration flow — replaces prose-reading
- [ ] **Core rules**:
  - `adj_sev ≤ 3` → defense_wins (regardless of rebuttal type)
  - `CONCEDE + adj_sev > 3` → critique_wins
  - `DEFER` → empirical_test_agreed (base case)
  - `REBUT* + adj_sev ≥ 7` → empirical_test_agreed (high residual)
  - `REBUT* + adj_sev 4–6 + orig_sev ≥ 7` → empirical_test_agreed (FATAL not fully cleared)
  - `REBUT* + adj_sev ≤ 6 + orig_sev < 7` → defense_wins
- [ ] **Constitutional overrides** (applied after main rules):
  - `CONCEDE + adj_sev ≥ 7` → critique_wins (constitutional)
  - `DEFER + adj_sev ≤ 3` → defense_wins (constitutional)
  - ~~`DEFER + orig_sev ≥ 7 + adj_sev ≥ 6` → critique_wins~~ **DO NOT PORT** — tested in canary_run3, caused systematic over-blocking on ETA and defense_wins cases. The correct mechanism for conclusion-invalidating DEFERs is question 4 (prompt-level), not a severity-based verdict override.
- [ ] **Case-level aggregation**: critique_wins beats ETA beats defense_wins across all point verdicts
- [ ] **Short-circuit handling**: no advancing findings → defense_wins (skip debate stages)

---

## Orchestrator (ml-lab.md)

### Stage A (once)
- [ ] **Update Step 3 (critique)** — dispatch ml-critic with structured JSON output schema; suppress NIT findings before passing to defender
- [ ] **Add Step 3.5 (defender R1)** — dispatch ml-defender Mode 1 with structured JSON schema; short-circuit to defense_wins if no advancing findings

### Stage B loop (repeatable, max_rounds)
- [ ] **Add Step 3.6 (critic R2 — per round)** — dispatch ml-critic-r2 with current defender rebuttal state; ACCEPT/CHALLENGE/PARTIAL per finding
- [ ] **Add Step 3.7 (defender R2 — per round)** — dispatch ml-defender Mode 2; pass `is_final_round` based on stopping condition evaluation
- [ ] **Add Step 3.8 (verdict derivation — per round)** — apply `derive_verdict()` to current defender R2 JSON; check stopping conditions
- [ ] **Convergence check** — compare current derive_verdict() output against previous round; if stable and no finding moved → stop loop
- [ ] **Force-resolution at cap** — if max_rounds reached, apply derive_verdict() to final state; log any residual DEFERs as force-resolved

### Orchestrator plumbing
- [ ] **Remove prose verdict extraction** from DEFENSE.md / DEBATE.md — verdict comes from derive_verdict() only
- [ ] **Thread finding state across rounds** — orchestrator must carry `original_severity` from Round 1 critic through all subsequent rounds (needed for FATAL backstop in derive_verdict())
- [ ] **Log round count and convergence reason** in journal entry for each debate run
- [ → known calibration note at ml-lab.md:808 — zero defense_wins in 480 runs (pre-v8). Update post-port validation.]
- [ ] **Update known limitations** in ml-lab.md to reflect v8 calibration state

---

## README Updates

The README (`README.md` at repo root) must be updated as the final step of the port. It is a public-facing document — changes should reflect finalized behavior, not in-progress work. Do not update until the port is validated.

### Part 1 changes (Using ml-lab)

- [ ] **Default mode description** — update the opening paragraph and "What ml-lab Does" section: debate is now the default, ensemble is opt-in. The current text reads *"ensemble of independent critics (default) or an adversarial critic-defender debate (opt-in)"* — reverse this.
- [ ] **Ensemble description** — reframe as a high-recall sweep tool: no precision filter, no structured verdict, appropriate when the user wants a comprehensive finding list and will triage manually.
- [ ] **Debate mode description** — update to reflect the v8 protocol: structured 4-question DEFER test, 7 rebuttal types, `derive_verdict()` deterministic verdict, convergence loop up to `max_rounds`. Remove references to prose-based DEFENSE.md verdict extraction.
- [ ] **Workflow diagram** — update Step 3 flow to show Stage A (Critic R1 → Defender R1) + Stage B loop (Critic R2 → Defender R2 → derive_verdict(), up to max_rounds).
- [ ] **New agents list** — add `ml-critic-r2` to the installed agent set; update manual install instructions.

### Part 2 changes (The Experiment Behind ml-lab)

- [ ] **Protocol Decision section** — add a paragraph summarizing the v8 calibration work and why debate is now the recommended default. Key points:
  - Study 1/2 showed multiround superior on ambiguity judgment (FVC_mixed +0.225 vs. ensemble) — that case for debate is now stronger with v8 calibration fixes
  - v8 addressed the two main failure modes identified in Study 2: zero `defense_wins` (over-concession) and uncaught conclusion-invalidating flaws (over-DEFER)
  - Reference the v8 experiment for the specific interventions

- [ ] **"What Failed" section** — add a v8 subsection documenting the calibration problems diagnosed and fixes applied:
  - `isolated_debate` failure mode: blind defender without structured rebuttal types → corrupted valid critiques ~10% of the time. v8 fix: 7-type rebuttal taxonomy with REBUT-DESIGN/REBUT-SCOPE/REBUT-EVIDENCE constraints that prevent over-broad rebuttal.
  - DEFER overuse: defenders used DEFER as a safe default rather than engaging with genuine flaws. v8 fix: Options A+C (resolve/mitigate distinction, DEFER > CONCEDE reframing), question 4 (conclusion-survival test).
  - REBUT-DESIGN on FATAL findings without methodology citation: defenders cited design intent rather than specific text. v8 fix: FATAL text-citation gate requiring named controls, not inference.
  - Critic short-circuits (no_material_findings on flawed designs): traced to specific weak models (haiku, maverick). v8 fix: model pool pruning + structured NIT suppression.

- [ ] **"Where Debate Still Matters" section** — update to reflect that with v8 calibration, debate is now the recommended path for all cases (not just ambiguous ones), while ensemble remains available for high-recall sweeps.

- [ ] **Known limitations** — update the zero `defense_wins` note (currently at line 808 of ml-lab.md and referenced in README). Post-port validation results should replace the "unsolved problem" framing if Sonnet produces `defense_wins` on clean cases.

---

## What Does NOT Port

These are v8 meta-evaluation tools — they measure protocol accuracy, not run the protocol:

| Component | Reason |
|-----------|--------|
| IDR / AER / DER / FDR / MCC metrics | Benchmark evaluation of the protocol, not part of the protocol |
| `canary_seeds.json` / `probe_*` scripts | Experiment harness for calibration testing |
| `run_multiround.py` orchestration | Replaced by ml-lab.md + agent dispatches |
| Ground-truth labels (`correct_position`) | Meta-evaluation only |

---

## Port Sequence (recommended)

Order matters — each layer depends on the one below it.

1. **Critic output schema** — all downstream components depend on structured finding IDs and severity
2. **Defender R1 output schema** — rebuttal types and severity adjustments must be in place
3. **ml-critic-r2 agent** — must exist before Defender R2 constraints are meaningful
4. **Defender R2 + derive_verdict()** — final verdict logic; depends on structured R2 challenge verdicts
5. **ml-lab.md orchestration** — wire the four stages into the Step 3 flow
6. **Mode default change** — switch ensemble → debate default after validation

---

## Faithfulness Tests (no API calls)

Before declaring the port complete, the following unit tests must pass against the ported implementation. They encode v8's final findings as executable specifications — no LLM calls required.

Tests live in `experiments/self_debate_experiment_v8/tests/` during development, then migrate to `plugins/ml-lab/tests/` post-port. The same test file should pass in both locations if the port is faithful.

### 1. `derive_verdict()` rules

One test per named rule. These act as executable documentation of the verdict logic:

- [ ] `DEFER + adj_sev ≤ 3` → `defense_wins` (constitutional override, not ETA)
- [ ] `CONCEDE + adj_sev ≥ 7` → `critique_wins` (constitutional override)
- [ ] `CONCEDE + adj_sev 4–6` → `critique_wins`
- [ ] `REBUT* + orig_sev ≥ 7 + adj_sev 4–6` → `empirical_test_agreed` (FATAL not fully cleared)
- [ ] `REBUT* + orig_sev ≥ 7 + adj_sev ≥ 7` → `empirical_test_agreed` (high residual)
- [ ] `REBUT* + orig_sev < 7 + adj_sev ≤ 6` → `defense_wins`
- [ ] `DEFER + adj_sev > 3` → `empirical_test_agreed` (base case)
- [ ] Empty rebuttals → `defense_wins` (short-circuit)
- [ ] `critique_wins` beats `empirical_test_agreed` beats `defense_wins` in case-level aggregation
- [ ] Mixed point verdicts: one `critique_wins` + two `defense_wins` → case `critique_wins`

### 2. Rebuttal schema and taxonomy constraints

- [ ] `REBUT-IMMATERIAL` on MATERIAL finding (orig_sev 4–6) → validation error
- [ ] `REBUT-IMMATERIAL` on FATAL finding (orig_sev ≥ 7) → validation error
- [ ] `REBUT-DESIGN` severity adjustment outside −3 to −5 range → validation error
- [ ] `REBUT-EVIDENCE` severity adjustment outside −4 to −6 range → validation error
- [ ] `adjusted_severity` = `original_severity + severity_adjustment` with floor 0
- [ ] `DEFER` severity adjustment must be 0
- [ ] `CONCEDE` severity adjustment must be 0
- [ ] Missing required field (`finding_id`, `rebuttal_type`, `adjusted_severity`) → validation error

### 3. Convergence loop stopping conditions

- [ ] Same `case_verdict` + no finding changed `rebuttal_type` or `adj_sev` across two rounds → converged
- [ ] `case_verdict` flipped between rounds → not converged, continue
- [ ] `max_rounds` reached → force-resolve, apply `derive_verdict()` to final state regardless
- [ ] `is_final_round=true` passed to defender on final round; `is_final_round=false` on intermediate rounds

### Key v8 findings encoded as tests (faithfulness checklist)

| v8 finding | Test |
|---|---|
| REBUT-IMMATERIAL restricted to MINOR only | Schema validation on MATERIAL/FATAL finding |
| FATAL not fully cleared → ETA (not defense_wins) | REBUT-DESIGN + orig≥7 + adj 4–6 |
| DEFER + adj≤3 → defense_wins (not ETA) | Constitutional override test |
| critique_wins beats ETA in aggregation | Mixed-finding aggregation |
| Short-circuit on no advancing findings | Empty rebuttals = defense_wins |
| Conclusion-survival test (question 4) | DEFER justification requires all 4 answers |

---

## Validation Gate (post-port)

Before declaring the port complete, run the Phase 0 existence proof cases and the canary probe cases against the ported ml-lab agents (using Sonnet):

- [ ] `eval_scenario_858` (GT: defense_wins) — should remain defense_wins
- [ ] `eval_scenario_185` (GT: empirical_test_agreed) — should remain ETA; backstop must not fire
- [ ] `eval_scenario_862` (GT: empirical_test_agreed) — same
- [ ] `eval_scenario_812` (GT: critique_wins) — should produce critique_wins in majority of runs
- [ ] `eval_scenario_852` (GT: critique_wins) — same
