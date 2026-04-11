# Biased Debate Condition — Persona Priming Specification

**Reference:** PLAN.md §6 (Persona-Biased Debate)
**Consumed by:** Phase 5 benchmark run dispatch (not yet built)
**Status:** Pre-registered spec; implementation pending Phase 5

---

## What `biased_debate` Is

`biased_debate` is structurally identical to `isolated_debate`:
- Same protocol: Critic → Defender → Orchestrator adjudication
- Same compute: ~3x (N=3 runs per case)
- Same orchestrator
- Same scoring: IDR, IDP, IDP_adj, DRQ, ETD, FVC

The **only** difference is asymmetric persona priming injected as a system prompt prefix to each agent before dispatch.

---

## Priming Text

### Critic system prompt prefix

```
You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and treat methodological gaps as real concerns until shown otherwise.
```

### Defender system prompt prefix

```
You are responding to a combative reviewer who frequently focuses on insignificant issues and overstates concerns. Be selective about what you concede.
```

---

## Injection Mechanism

- **Where:** System prompt prefix — prepended to the existing agent system prompt before dispatch
- **When:** Conditional on `condition == 'biased_debate'`; no priming injected for any other condition
- **Scope:** Applied to both Critic and Defender dispatches within the same case run

For every other condition (`isolated_debate`, `multiround`, `conditional_fm`, `ensemble_3x`, `baseline`), agents receive no persona prefix.

---

## Rationale

The asymmetry is intentional:
- Biased Critic → sensitized to real flaws → expected higher IDR
- Biased Defender → concedes less, forces Critic to defend weak claims → expected higher IDP precision

**What this tests (Q4/H6):** Does persona framing alone, without any structural protocol change, improve debate quality? Comparison is `biased_debate` vs `isolated_debate` — matched compute, matched structure, prompt framing only.

**H6 prediction (from HYPOTHESIS.md):**
- `biased_debate` > `isolated_debate` on IDR (critic sensitivity) and IDP (defender selectivity)
- Directional improvement on mixed-case FVC and ETD
- If `biased_debate` <= `isolated_debate`: persona framing has no measurable effect beyond structural protocol

---

## ETD Applicability

Same as `isolated_debate` — ETD fires on mixed cases in `biased_debate`. `biased_debate` is included in `ETD_CONDITIONS` in `self_debate_poc.py`.

---

## IDP Diagnostic Note

From PLAN.md §7 IDP diagnostic: if IDP is flat across all debate conditions *including* `biased_debate`, this points to an orchestrator-level extraction bug (issues being copied from adjudicator synthesis rather than Critic raw output), not a persona/protocol limitation. Track `IDP_raw` vs `IDP_adj` separately per run.
