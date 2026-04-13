# Defender Prompt Comparison — ml-lab Agent vs v7 API Prompts

> Compares `plugins/ml-lab/ml-defender.md` (agent) against
> `pipeline/prompts/defender_isolated.md` and
> `pipeline/prompts/multiround_2r_defender.md` (v7 API prompts),
> disregarding agent scaffolding (file I/O, mode dispatch, CLAUDE.md frontmatter).

---

## Shared DNA (identical in substance)

| Element | Agent | v7 isolated / v7 multiround |
|---|---|---|
| Persona framing | "original designer… intent behind every choice" | identical |
| Two-pass structure | Pass 1 analysis → Pass 2 verdict | identical |
| Calibration rule | multiple critical flaws → must not be `defense_wins` | identical (same wording) |
| Fast concession bullet | "fast concession on a real problem" | identical |
| "just a PoC" antipattern | present | present (says "prototype") |
| Strongest defense formula | "Yes, this is a simplification, but here is why…" | identical |
| Verdict tokens | `defense_wins\|critique_wins\|empirical_test_agreed` | identical |

---

## Meaningful Differences

### 1. Agent has three modes; v7 has two prompts

| Agent mode | v7 counterpart |
|---|---|
| Mode 1 — Initial Defense (no critic visible) | `defender_isolated.md` |
| Mode 2 — Debate Round (critic visible) | `multiround_2r_defender.md` |
| Mode 3 — Evidence-Informed Re-Defense (experimental results available) | **No v7 counterpart** |

Mode 3 was specific to multi-cycle ml-lab investigations where `CONCLUSIONS.md` is
available. It has no analogue in the fixed benchmark protocol.

---

### 2. Implementation soundness check

**Agent (Mode 1):**
> "Before defending any design choice, verify that the implementation is sound enough to
> produce interpretable results. Check that all parameters are explicitly set and
> appropriate for this problem, not inherited from defaults designed for a different use
> case. If the implementation has a configuration flaw that would silently invalidate the
> results, identify it here."

**`defender_isolated.md`:**
> "Before defending any design choice, verify that the methodology is sound enough to
> produce interpretable results."

The specific parameter-default pre-flight check is absent in v7. This check was added to
the agent in response to a known calibration failure (v6 lesson: silent misconfiguration).
The attenuation is appropriate because benchmark cases describe methodologies rather than
runnable code — but the general soundness check framing is preserved.

---

### 3. Per-point verdict labels

**Agent (Pass 2):** assigns per-point labels before an overall verdict:
- `Concede` — critique is correct
- `Rebut` — critique is wrong
- `Mark as empirically open` — cannot be resolved by argument alone

**v7 prompts:** skip per-point labels; go directly to aggregate verdict
(`defense_wins | critique_wins | empirical_test_agreed`).

This is intentional. In v7, per-issue triage is delegated to the adjudicator
(`adjudicator.md`). The defender's role is limited to prose rebuttal + aggregate verdict.

---

### 4. Output target

| | Agent | v7 |
|---|---|---|
| Mode 1 output | `DEFENSE.md` (file write) | `{"defender_raw": "...", "verdict": "..."}` (JSON) |
| Mode 2 output | Appended to `DEBATE.md` | `{"defender_raw": "...", "verdict": "..."}` (JSON) |

---

### 5. Debate round protocol

**Agent (Mode 2):** explicit rules — do not re-litigate resolved points; advance arguments
with new evidence or reasoning; evaluate proposed empirical tests for soundness.

**`multiround_2r_defender.md`:** simplified — respond point by point, concede genuine
flaws, explain misunderstood design intent.

The richer protocol is unnecessary because `multiround_2r` is fixed at exactly 2 rounds
with no stop-detection negotiation.

---

## Summary

The core reasoning structure and persona calibration are faithfully preserved across both
v7 defender prompts. The main substantive delta is the **attenuation of the
implementation soundness check** in `defender_isolated.md` — the parameter-specific
pre-flight language from the agent is gone, replaced by a more general soundness framing.
This is appropriate given that benchmark cases are methodology descriptions rather than
runnable code, but worth flagging for any future re-calibration of defender strictness.
