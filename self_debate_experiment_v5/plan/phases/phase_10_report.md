## Phase 10 — Final Report, Peer Review, and Synthesis

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

> **Reporting norms apply fully in this phase.** See top-level Reporting Norms section.

> **Prerequisite:** Phase 9 (cross-vendor scorer) and Phase 9.5 (post-run audit) must complete before Phase 10 begins. REPORT.md's Limitations section requires `cross_vendor_scores_v5.json` (Phase 9) and POST_MORTEM.md (Phase 9.5).

```bash
uv run log_entry.py --step 10 --cat workflow --action step_start --detail "Phase 10: final report, peer review, and FINAL_SYNTHESIS"
```

**Instruction:**

Generate the final artifacts. Reporting norms apply throughout:
1. No prompt leakage (no "Results mode." preamble or similar)
2. Limitations are threats to validity, not design properties
3. Lead with fair-comparison lift

1. REPORT.md — dispatch report-writer (Mode 1):

   Provide: CONCLUSIONS.md, stats_results.json, SENSITIVITY_ANALYSIS.md,
   ENSEMBLE_ANALYSIS.md, PREREGISTRATION.json, evaluation_rubric.json,
   HYPOTHESIS.md, CRITIQUE.md, DEFENSE.md, cross_vendor_scores_v5.json,
   POST_MORTEM.md

   Experiment-specific context (pass in dispatch prompt):
   - Related work: Irving 2018, Du 2023, Liang 2023, Khan 2024, Zheng 2023,
     ChatEval, Wang 2023 self-consistency
   - 5 conditions: isolated_debate, multiround, forced_multiround, ensemble, baseline
   - Fair-comparison dims: IDR/IDP/DRQ/FVC (ETD and DC excluded from debate-vs-baseline)
   - Primary metric: fair-comparison lift
   - Two comparison tables:
     Table A: debate vs ensemble on IDR/IDP/DRQ/FVC — include ETD exclusion rationale
     Table B: isolated vs multiround vs forced_multiround on all dims
   - Closed-loop scoring confound mitigation: cross_vendor_scores_v5.json (Phase 9)

2. REPORT_ADDENDUM.md — production re-evaluation (orchestrator-written):
   - **Deployment scenario**: What would using this protocol in production look like?
     Describe the operational setup (model, conditions, latency, cost per case).
   - **Benchmark-to-production transfer**: Which findings from REPORT.md generalize
     to production scenarios and which are benchmark-specific artifacts.
   - **Unresolved limitations at scale**: For each limitation named in REPORT.md's
     Limitations section, state whether it applies at production scale and whether
     it has been mitigated. Do NOT dismiss any named limitation without evidence.
   - **Deployment recommendation**: explicit trust/distrust verdict under specified
     conditions. If fc_lift < 0.10 (hypothesis rejected), the recommendation must
     not use "production-ready" or "validated" without qualification.
   - **Quantitative consistency requirement**: any numbers cited from the benchmark
     (means, lifts, pass rates) must match REPORT.md exactly — copy from
     stats_results.json, do not paraphrase.

3. PEER_REVIEW_R1.md — Round 1 (research-reviewer, Opus):
   Dispatch research-reviewer on REPORT.md.
   After receiving review, write remediation plan for all MAJOR issues.
   Present plan for LEAD approval before addressing.
   Address approved findings. Append ## Response section.

   Round 2 only if Round 1 had MAJOR issues:
   research-reviewer-lite on updated REPORT.md (providing PEER_REVIEW_R1.md context).
   Write PEER_REVIEW_R2.md. Append ## Response.

   Cap: 2 rounds maximum.

4. FINAL_SYNTHESIS.md — Lead synthesis (orchestrator-written):
   - What the benchmark tested
   - Whether the protocol worked (evidence from failure_attribution)
   - Where it failed and why
   - Forced multiround: did the mechanism add value on hard cases?
   - Closed-loop confound: what Phase 9 cross-vendor results show
   - What changes for v5
   - Concrete recommendation: when to trust / distrust the protocol
   - Complete artifact inventory

**Logging:**
```bash
uv run log_entry.py --step 10 --cat subagent --action dispatch_report_writer_mode1 --detail "report-writer (Opus, Mode 1) dispatched with full artifact set" --artifact REPORT.md
uv run log_entry.py --step 10 --cat write --action write_report --detail "REPORT.md written: abstract, related work, design, results, hypothesis verdicts, limitations" --artifact REPORT.md
uv run log_entry.py --step 10 --cat write --action write_report_addendum --detail "REPORT_ADDENDUM.md written: production re-evaluation" --artifact REPORT_ADDENDUM.md
uv run log_entry.py --step 10 --cat subagent --action dispatch_research_reviewer_r1 --detail "research-reviewer (Opus) dispatched on REPORT.md for Round 1 peer review" --artifact PEER_REVIEW_R1.md
uv run log_entry.py --step 10 --cat write --action write_peer_review_r1 --detail "PEER_REVIEW_R1.md written with ## Response section" --artifact PEER_REVIEW_R1.md
# If Round 2 was needed:
# uv run log_entry.py --step 10 --cat subagent --action dispatch_research_reviewer_r2 --detail "research-reviewer-lite dispatched for Round 2 peer review" --artifact PEER_REVIEW_R2.md
# uv run log_entry.py --step 10 --cat write --action write_peer_review_r2 --detail "PEER_REVIEW_R2.md written with ## Response section" --artifact PEER_REVIEW_R2.md
uv run log_entry.py --step 10 --cat write --action write_final_synthesis --detail "FINAL_SYNTHESIS.md written: protocol assessment, recommendations, artifact inventory" --artifact FINAL_SYNTHESIS.md
uv run log_entry.py --step 10 --cat workflow --action step_end --detail "Phase 10 complete"
```

**Phase 10 commit:**
```bash
git add self_debate_experiment_v5/REPORT.md self_debate_experiment_v5/REPORT_ADDENDUM.md \
        self_debate_experiment_v5/PEER_REVIEW_R1.md self_debate_experiment_v5/FINAL_SYNTHESIS.md
git commit -m "v5 Phase 10: REPORT, peer review, FINAL_SYNTHESIS"
```

---
