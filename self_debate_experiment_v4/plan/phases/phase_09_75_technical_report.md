## Phase 9.75 — Technical Report (Results Mode)

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

```bash
uv run log_entry.py --step 9.75 --cat workflow --action step_start --detail "Phase 9.75: writing TECHNICAL_REPORT.md in results mode"
```

**Instruction:**

Write TECHNICAL_REPORT.md in results mode.

Rules for results mode:
- State findings as facts, not conclusions
- Limitations are stated as threats to validity with evidence and mitigation.
  The "design property" label is reserved for intentional choices with rationale
  that do not undermine result validity. Failure modes are limitations, not design properties.
- Do not speculate about what a larger study would show
- Do not include forward-looking content — that belongs in FINAL_SYNTHESIS.md
- Include all quantitative results with confidence intervals
- The first line must be a section header or abstract heading.
  Do NOT begin with "Results mode.", "Mode: ...", or any internal directive.

Required sections:
1. Abstract — 150 words max, leading with fair-comparison lift
2. Method — benchmark construction (5 conditions), case types, rubric, pre-registration
3. Results — per-condition means with CIs, Wilcoxon tests (fair dims), dimension aggregates,
   two comparison structures, forced_multiround on hard cases
4. Production Re-evaluation — from REPORT_ADDENDUM.md, condensed
5. Limitations — threats to validity with evidence and mitigation
6. Conclusion — one paragraph, quantitative, no speculation

**Logging:**
```bash
uv run log_entry.py --step 9.75 --cat write --action write_technical_report --detail "TECHNICAL_REPORT.md written in results mode: abstract, method, results, limitations, conclusion" --artifact TECHNICAL_REPORT.md
uv run log_entry.py --step 9.75 --cat workflow --action step_end --detail "Phase 9.75 complete"
```

**Phase 9.75 commit:**
```bash
git add self_debate_experiment_v4/TECHNICAL_REPORT.md
git commit -m "chore: snapshot v4 phase 9.75 artifacts — technical report in results mode [none]"
uv run log_entry.py --step 9.75 --cat exec --action commit_phase_artifacts --detail "committed phase 9.75 artifacts: TECHNICAL_REPORT.md"
```

---
