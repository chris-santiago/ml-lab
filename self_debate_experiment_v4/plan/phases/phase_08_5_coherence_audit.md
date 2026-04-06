## Phase 8.5 — Pre-report Numerical Consistency Check

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **Script:** `plan/scripts/coherence_audit.py` — pre-report numerical consistency check. Cross-references numbers in CONCLUSIONS.md and SENSITIVITY_ANALYSIS.md against `stats_results.json`, `v4_results.json`, `sensitivity_analysis_results.json`. Also checks forced_multiround hollow-round documentation in ENSEMBLE_ANALYSIS.md. Raises SystemExit on inconsistencies.

```bash
uv run log_entry.py --step 8.5 --cat workflow --action step_start --detail "Phase 8.5: pre-report numerical consistency check"
uv run plan/scripts/coherence_audit.py
# Must pass before Phase 9
uv run log_entry.py --step 8.5 --cat audit --action coherence_audit_passed --detail "Pre-report coherence audit passed — numbers consistent across CONCLUSIONS.md and SENSITIVITY_ANALYSIS.md" --artifact coherence_audit.py
uv run log_entry.py --step 8.5 --cat gate --action pre_report_gate --detail "Coherence audit gate cleared; proceeding to Phase 9"
uv run log_entry.py --step 8.5 --cat workflow --action step_end --detail "Phase 8.5 complete"
```

**Phase 8.5 commit:**
```bash
git add self_debate_experiment_v4/coherence_audit.py
git commit -m "chore: snapshot v4 phase 8.5 artifacts — pre-report coherence audit script [none]"
uv run log_entry.py --step 8.5 --cat exec --action commit_phase_artifacts --detail "committed phase 8.5 artifacts: coherence_audit.py"
```

---
