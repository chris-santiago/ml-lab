# Phase 9 — Reporting

> **Reminders:** `uv run` only. CWD: repo root.

---

## Steps

### 9.1 Run `/artifact-sync`
Per `CLAUDE.md`: run `/artifact-sync` before marking work complete. This updates all
artifacts, runs the three-check coherence audit (conflicts, staleness, completeness).

### 9.2 Dispatch `report-writer`
Agent prompt:
```
Write REPORT.md and TECHNICAL_REPORT.md for the v7 experiment.

Sources (numbers come ONLY from these):
- v7_results.json — all metrics, CIs, p-values, equivalence CI results
- CONCLUSIONS.md — hypothesis verdicts and framework verdict
- SENSITIVITY_ANALYSIS.md — variance audit, bootstrap stability
- HYPOTHESIS.md — pre-registered predictions (P1, P2)
- benchmark_cases_v7_raw.json — case counts and stratum composition

Key findings to highlight:
1. Framework verdict (P1 + P2): CONFIRMED or NOT CONFIRMED
2. H1a equivalence result: debate EQUIVALENT to baseline within ±0.015 FC
3. ensemble_3x vs multiround_2r IDR delta (P1) with CI
4. multiround_2r vs ensemble_3x FVC_mixed delta (P2) with CI
5. H4: ensemble_3x > baseline IDR with CI (promoted from v6 post-hoc)
6. H5: union pooling precision parity (1/3 vs 3/3 flagged) within ±0.03
7. Defense exoneration rate by condition
8. multiround_2r variance relative to other conditions

Do not source numbers from README, v6 artifacts, or pilot_results.json.
```

### 9.3 Log and commit
Use `/log-commit` (ml-journal skill). Commit message should list:
- `REPORT.md`, `TECHNICAL_REPORT.md` created
- Artifact sync complete

---

## Outputs
- `REPORT.md`
- `TECHNICAL_REPORT.md`

## Gate
`REPORT.md` and `TECHNICAL_REPORT.md` written. Artifact sync complete.
