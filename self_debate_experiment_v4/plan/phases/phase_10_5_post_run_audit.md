## Phase 10.5 — Post-Run Audit Agent (NEW)

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> Automated anomaly detection to supplement manual post-mortem. Issue 8 remediation.

```bash
uv run log_entry.py --step 10.5 --cat workflow --action step_start --detail "Phase 10.5: post-run audit agent — anomaly detection on raw outputs and scoring"
```

**Agent prompt:**

Spawn a general-purpose agent with the following materials:
- v4_raw_outputs/ (sample: first 20 files + any flagged high-variance cases)
- self_debate_poc.py source
- v4_results_eval.json
- stats_results.json

Instruct the agent to check for these known failure modes from v3:
1. Schema mismatch: are ETD empirical_test fields using the canonical schema
   (condition/supports_critique_if/supports_defense_if/ambiguous_if)?
   Flag any file using the old schema (measure/success_criterion/failure_criterion).
2. Isolation status: are there any isolated_debate defender_raw outputs that contain
   verbatim Critic language? (check_isolation.py should have caught these, but verify)
3. Pass/fail anomalies: are there cases in v4_results_eval.json marked fail despite
   all applicable dimension scores >= 0.5 and mean >= 0.65?
4. ETD scoring: are there empirical_test_agreed cases where ETD=0.0 despite a populated
   empirical_test field in the raw output? Flag each such case.
5. DC scoring: are there any baseline runs where DC != null? (should be N/A in v4)
6. Forced multiround: do all forced_multiround raw outputs have debate_rounds >= 2?
   Flag any with debate_rounds == 1.
7. **Hollow forced-round detection:** For each forced_multiround case, compare round 1 vs round 2 snapshots.
   Flag as hollow if: round2_verdict == round1_verdict AND round2_points_resolved == 0.
   Log each hollow case: decision/hollow_forced_round_detected with case_id and round data in meta.
   Compute hollow_rate = hollow_cases / total_forced_multiround_cases.
   If hollow_rate > 0.5: log a CRITICAL anomaly — majority of forced rounds are hollow; mechanism validation is compromised.

The agent produces a structured anomaly report with:
- anomaly_type, case_id, file_path, severity, evidence, recommended_action
for each finding.

Write the anomaly report to POST_MORTEM.md (structured — not just prose).
Log the result:
uv run log_entry.py --step 10.5 --cat audit --action post_run_audit_complete \
  --detail "Anomaly report complete" --meta '{"anomaly_count": N, "critical_count": N}'

If any `critical` anomalies are found, resolve them before Phase 11.

```bash
uv run log_entry.py --step 10.5 --cat write --action write_post_mortem --detail "POST_MORTEM.md written: structured anomaly report from post-run audit agent" --artifact POST_MORTEM.md
uv run log_entry.py --step 10.5 --cat workflow --action step_end --detail "Phase 10.5 complete"
```

**Phase 10.5 commit:**
```bash
git add self_debate_experiment_v4/POST_MORTEM.md
git commit -m "chore: snapshot v4 phase 10.5 artifacts — post-run audit and post-mortem [none]"
uv run log_entry.py --step 10.5 --cat exec --action commit_phase_artifacts --detail "committed phase 10.5 artifacts: POST_MORTEM.md"
```

---
