# v7 Experimental Design: Prospective Validation of the Convergent/Divergent Framework

## Context

v6 produced three findings: ensemble > debate at matched 3× compute (FC delta +0.0287,
CI [+0.0154, +0.0434]); debate ≈ baseline; multiround advantage on convergent tasks
(FVC_mixed=0.3667) but at ~5× compute, not 3×. Peer review identified five weaknesses:

| Weakness | v7 Fix |
|---|---|
| Multiround advantage at ~5×, not 3× | `multiround_2r`: fixed 3 API calls |
| Convergent/divergent framework post-hoc | Pre-register P1/P2 before Phase 5 |
| ETD ceiling: 100% = 1.0, no signal | Remove ETD from primary battery |
| 40 mixed cases underpowered | Scale to 80 mixed cases |
| H1a non-significance ≠ equivalence | Pre-specified CI ±0.015 FC |

**Submission:** Single submission to EMNLP ARR May 2026 (deadline: May 25, 2026). No v6 submission in parallel. (Decision logged: journal `28a0393d`)

---

## Execution Rules

1. **Script invocations:** `uv run` only. Never `python` or `python3` directly.
2. **Agent invocation:** Not used for Phase 5. All Claude calls go through `pipeline/phase5_benchmark.py` via OpenRouter API (see `API_DISPATCH_PLAN.md`). Agents (`ml-critic`, `ml-defender`) may still be used for Phase 4 self-review.
3. **Working directory:** CWD is always repo root (`ml-lab/`). All bash commands must use `cd experiments/self_debate_experiment_v7 &&` or repo-root-relative paths.
4. **Log entries:** Always use `uv run .project-log/journal_log.py`. Never write JSONL manually.
5. **Context scoping:** When executing a phase, read only the reference documents listed for that phase. Do not preload all references.

---

## Reference Documents

| Document | Description | Used by phases |
|---|---|---|
| [design_decisions.md](references/design_decisions.md) | Conditions, case composition, scoring battery, statistical tests, open questions | 0, 1, 2, 3, 5, 7 |
| [hypotheses.md](references/hypotheses.md) | P1/P2 pre-registration predictions, H1a–H5, equivalence bounds | 3, 4, 5, 7 |
| [API_DISPATCH_PLAN.md](references/API_DISPATCH_PLAN.md) | Phase 5 benchmark runner design (OpenRouter async script) | 0, 5 |
| [schema_b.md](references/schema_b.md) | Schema B field table + format constraints (reused from v6) | 0, 2 |
| [v6_lessons.md](references/v6_lessons.md) | Key lessons from v6 that constrain v7 design | 0, 1, 2, 4, 5 |

---

## Phase Index

| Phase | Title | File | Gate |
|---|---|---|---|
| 0 | Setup | [phase_00_setup.md](phases/phase_00_setup.md) | `multiround_2r` system prompts committed; scoring engine updated (ETD removed); API dispatch script scaffolded |
| 1 | RC Data Acquisition | [phase_01_rc_acquisition.md](phases/phase_01_rc_acquisition.md) | `rc_cases_raw.json` with ≥30 ReScience C papers |
| 2 | Case Library Assembly | [phase_02_case_assembly.md](phases/phase_02_case_assembly.md) | `benchmark_cases_v7_raw.json` passes Schema B; 280 cases (160 regular / 80 mixed / 40 defense) |
| 3 | Pilot & Calibration | [phase_03_pilot.md](phases/phase_03_pilot.md) | `baseline_fc_mean < 0.80`; ≥160 regular + ≥80 mixed pass filter |
| 4 | Pre-Experiment Self-Review | [phase_04_self_review.md](phases/phase_04_self_review.md) | `HYPOTHESIS.md` committed with P1/P2 + H1a–H5 + equivalence bounds; coherence audit passes as named gate |
| 5 | Benchmark Run | [phase_05_benchmark.md](phases/phase_05_benchmark.md) | All output files pass schema + zero-variance check |
| 6 | Cross-Model Scoring | [phase_06_scoring.md](phases/phase_06_scoring.md) | `v7_rescored_idr_idp.json` complete |
| 7 | Analysis | [phase_07_analysis.md](phases/phase_07_analysis.md) | `v7_results.json` with all 8 hypothesis tests (P1, P2, H1a–H5) |
| 8 | Sensitivity & Robustness | [phase_08_sensitivity.md](phases/phase_08_sensitivity.md) | `SENSITIVITY_ANALYSIS.md`; `multiround_2r` variance audit |
| 9 | Cross-Vendor Validation | [phase_09_cross_vendor.md](phases/phase_09_cross_vendor.md) | Spot-check 10% of cases; agreement metrics reported |
| 10 | Reporting | [phase_10_reporting.md](phases/phase_10_reporting.md) | All artifacts + `/artifact-sync` + coherence audit + paper rewrite complete |

---

## Files

### Create (new)
| File | Purpose |
|---|---|
| `pipeline/phase5_benchmark.py` | API dispatch benchmark runner (see `API_DISPATCH_PLAN.md`) |
| `pipeline/prompts/multiround_2r_defender.md` | Defender system prompt variant — sees critic output (debate variant) |
| `pipeline/prompts/adjudicator.md` | Adjudicator system prompt (new for API dispatch; was inline in v6) |
| `HYPOTHESIS.md` | Pre-registered hypotheses (commit before Phase 5) |
| `v7_cases_sanitized.json` | Benchmark cases with ground truth stripped |

### Reuse from v6 (copy + adapt)
| File | Change |
|---|---|
| `pipeline/rc_extractor.py` | Target 30–40 papers (was 25) |
| `pipeline/orchestrator.py` | Mixed case target 80 (was 40); defense case target 40 (new stratum) |
| `pipeline/select_cases.py` | Updated stratum sizes |
| `pipeline/normalize_cases.py` | No change needed |
| `v6_scoring.py` → `v7_scoring.py` | Remove ETD from primary battery; add equivalence CI checks (H1a ±0.015, H5 ±0.03); add H4, H5 tests |
