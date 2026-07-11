# Agents

All agents are subagents dispatched via the Agent tool from the main session. They run with isolated context — each agent sees only the artifacts passed to it.

## ml-critic

**Role:** Adversarial critic — finds flaws the PoC hasn't tested.

**Dispatched by:** `/ml-lab` skill at Step 3.

- **Debate mode:** dispatched once (Stage A.1)
- **Ensemble mode:** dispatched 3 times independently with no cross-visibility

**Persona:** Skeptical ML engineer with an applied mathematics background. Looks for fundamental flaws in the proof-of-concept.

**Modes:**

| Mode | When | Input |
|------|------|-------|
| Initial critique (Step 3) | First review cycle | PoC code + hypothesis |
| Debate rounds (Step 5) | Open-ended debate | Prior exchange history |
| Evidence-informed re-critique | Macro-iteration cycles 2+ | Prior critique + experimental results |

**Output:** `CRITIQUE.md` (debate) or `CRITIQUE_{1,2,3}.md` (ensemble) with severity-tagged findings (FATAL, MATERIAL, MINOR).

---

## ml-critic-r2

**Role:** R2 challenger — issues ACCEPT/CHALLENGE/PARTIAL verdicts on defender rebuttals.

**Dispatched by:** `/ml-lab` skill at Step 3, Stage B only (debate mode).

**Not used in ensemble mode.**

**Input:** Defender's rebuttal for a specific finding.

**Output:** Per-finding verdict with justification. Fed into `derive_verdict()` for deterministic case-level verdict computation.

---

## ml-defender

**Role:** Design defender — argues for the implementation against adversarial critique.

**Dispatched by:** `/ml-lab` skill at Step 3 (debate mode only).

**Not used in ensemble mode.**

**Persona:** The original designer who understands the intent behind every choice.

**Rebuttal taxonomy (7 types):**

| Type | Meaning |
|------|---------|
| CONCEDE | Finding is valid; will fix |
| REBUT-DESIGN | Design choice was intentional and correct |
| REBUT-SCOPE | Finding is out of scope for this investigation |
| REBUT-EVIDENCE | Evidence doesn't support the claimed severity |
| REBUT-IMMATERIAL | Finding is real but doesn't affect conclusions |
| DEFER | Will address as pre-flight item before main run |
| EXONERATE | Finding is based on a misunderstanding |

**Modes:**

| Mode | When | Input |
|------|------|-------|
| Initial defense (Stage A.2) | After critic R1 | Critic findings + PoC |
| Structured R2 response (Stage B.2) | After critic-r2 challenge | R2 verdict + prior exchange |
| Evidence-informed re-defense | Macro-iteration cycles 2+ | Prior defense + experimental results |

**Output:** `DEFENSE.md` with per-finding structured rebuttals.

---

## research-reviewer

**Role:** Adversarial peer reviewer — Opus-class claim audit (prior art / folklore / incorrect / tautology) then execution review of `REPORT.md`, ending in a submit / reframe / kill disposition.

**Dispatched by:** `/ml-lab` skill at Step 10, Round 1.

**Output:** `PEER_REVIEW_R1.md` with a per-claim audit, severity-tagged findings, and a disposition. A `kill` disposition halts the Step 10 loop and is surfaced to the user (see the workflow reference).

---

## research-reviewer-lite

**Role:** Verification reviewer — Haiku-class follow-up review.

**Dispatched by:** `/ml-lab` skill at Step 10, Rounds 2–3.

**Purpose:** Verify that remediation addressed the Round 1 findings without introducing new issues. Lighter weight than the full reviewer.

---

## report-writer

**Role:** Produces technical reports from investigation artifacts.

**Dispatched by:** `/ml-lab` skill at Steps 8 and 11.

**Modes:**

| Mode | Output | Input |
|------|--------|-------|
| Mode 1 (Step 8) | `REPORT.md` | Analytical artifacts + quantitative results |
| Mode 2 (Step 11) | `TECHNICAL_REPORT.md` | All available artifacts (results-mode synthesis) |

---

## readme-rewriter

**Role:** Outside-reader README rewriter.

**Dispatched by:** `/ml-lab` skill at Step 13 (user-confirmed).

**Process:** diagnose (as first-time reader) → outline (proposed structure) → rewrite (complete README optimized for external audiences).

---

## intent-monitor

**Role:** Pre-registration drift monitor.

**Dispatched by:** `/intent-watch` skill.

**Process:** Indexes binding constraints from a source-of-truth document, detects recent git changes, evaluates diffs for conflicts. Emits a clean-pass line or structured conflict report.

---

## pipeline-reviewer

**Role:** Fidelity judgment gate for promoted Metaflow flows.

**Dispatched by:** Pipeline promotion workflow, after a flow is scaffolded and before it is run. Blocking — a FAIL verdict halts promotion.

**Model:** Sonnet.

**Scope:** Guards intent-fidelity invariants only. Does not run the flow, does not police DAG shape, and does not duplicate the deterministic flow-lint's mechanical checks.

**Inputs:** Promoted flow source + the investigation's source-of-truth document(s) (one or more of `HYPOTHESIS.md`, the original PoC, `CONCLUSIONS.md`, `PLAN.md`, or any document the dispatching agent designates as authoritative).

**The five judgment checks:**

| Check ID | Invariant | Failure it catches |
|---|---|---|
| `split_convention` | Flow uses the same split strategy (shared vs. independent data streams) as the original PoC | Changing split convention silently alters variance structure across arms |
| `reshuffle_symmetry` | Per-epoch shuffling or resampling is applied identically to all methods | Asymmetric reshuffling gives one method a silent optimization advantage |
| `axes_match_source` | Swept axes (hyperparameter grids, dataset sizes, etc.) match the source-of-truth in identity and range | Silently added, dropped, or re-ranged axes change which regime is under evaluation |
| `metric_quantity` | Each metric's implementation computes the quantity its name claims | A metric reporting the wrong quantity passes all type/shape checks while drawing the verdict from the wrong signal |
| `sweep_override` | Flow does not perform per-experiment selection (sweep-then-pick-best) where the source-of-truth used a fixed configuration | Selection effect inflates results beyond what the original PoC measured |

**Output:** A single JSON object with a `findings` array (one entry per check, each with `check_id`, `verdict`, `evidence`, `source_of_truth_ref`, `intent_mismatch`, and `actionable_fix`), a top-level `blocking` boolean (`true` if any finding is FAIL), and a `summary` string. All five checks must appear even when the verdict is PASS.
