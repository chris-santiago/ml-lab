# v3 Experiment Post-Mortem

Issues identified during and after execution of `claude_code_plan_v3_experiment.md`. Each issue is scoped to whether it affected current results (active) or should be fixed in a future run (future).

---

## Issue 1 — INVESTIGATION_LOG coverage is incomplete

**Scope:** Future fix  
**Severity:** Minor — audit quality, not result validity

The plan's logging directive (line 780) covers Phase 6 onward only. It defers to the ml-lab agent's `## Investigation Log` schema rather than embedding it, which means log quality depends on the executor consulting that section. Phases 0–5 (case validation, preregistration, scoring engine build, protocol self-review) and Phases 7–9 (stats, reports, peer review) have no explicit logging directives.

ml-lab's logging section specifies ~60 lines of rules covering all category codes (`gate`, `write`, `read`, `subagent`, `exec`, `decision`, `debate`, `review`, `audit`, `workflow`), entry timing, and per-step logging rhythm. The v3 plan has one paragraph.

**What to fix in v4:** Embed the full logging schema directly in the plan and add explicit logging directives to each phase, not just Phase 6.

---
