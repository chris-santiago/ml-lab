## Phase 9.5 — Post-report Coherence Audit

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **Script:** `plan/scripts/post_report_coherence_audit.py` — post-report coherence audit across CONCLUSIONS.md, REPORT.md, ENSEMBLE_ANALYSIS.md. Checks claim consistency, README currency, peer review resolution, hypothesis closure, reporting norms compliance (no prompt leakage), and quantitative cross-checks. Raises SystemExit on failures.

```bash
uv run log_entry.py --step 9.5 --cat workflow --action step_start --detail "Phase 9.5: post-report coherence audit across all documents"
uv run plan/scripts/post_report_coherence_audit.py
# Must pass before Phase 9.75
uv run log_entry.py --step 9.5 --cat audit --action post_report_coherence_audit_passed --detail "Post-report coherence audit passed — all documents consistent" --artifact post_report_coherence_audit.py
uv run log_entry.py --step 9.5 --cat gate --action post_report_gate --detail "Post-report coherence gate cleared; proceeding to Phase 9.75"
uv run log_entry.py --step 9.5 --cat workflow --action step_end --detail "Phase 9.5 complete"
```

**Phase 9.5 commit:**
```bash
git add self_debate_experiment_v4/post_report_coherence_audit.py
git commit -m "chore: snapshot v4 phase 9.5 artifacts — post-report coherence audit script [none]"
uv run log_entry.py --step 9.5 --cat exec --action commit_phase_artifacts --detail "committed phase 9.5 artifacts: post_report_coherence_audit.py"
```

---
