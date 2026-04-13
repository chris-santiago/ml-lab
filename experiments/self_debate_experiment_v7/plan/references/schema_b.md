# Unified Schema B Definition

> **FROZEN — Source of Truth.** This is the canonical normalization contract for all v7 benchmark cases. Do not modify field names, types, or constraints. Any pipeline code that reads or writes cases must conform to this schema. Changes to case structure require a new schema version, not edits here.

The normalization target consumed by `self_debate_poc.py`. All pipeline outputs must validate
against this schema before case selection.

| Field | Type | Scoring function | Source: RC | Source: Synthetic |
|---|---|---|---|---|
| `case_id` | string | metadata | `rc_<id>` | from orchestrator |
| `hypothesis` | string | metadata | from paper title | from Stage 1 |
| `domain` | string | metadata | from RC report | from Stage 1 |
| `ml_task_type` | string | metadata | from RC report | from Stage 1 |
| `category` | `"regular"` / `"mixed"` / `"defense"` | `score_run()` | from `ground_truth_type` | from orchestrator |
| `difficulty` | `"medium"` / `"hard"` / `null` | metadata | `null` at normalization | `null` at normalization |
| `task_prompt` | string | read by agents | isolated methodology (no critique text) | `design_narrative` |
| `ground_truth.correct_position` | `"critique_wins"` / `"defense_wins"` / `"empirical_test_agreed"` | `score_run()` | from `ground_truth_type` | from Stage 3 |
| `ideal_debate_resolution.type` | string | DRQ/FVC scoring | `"critique_wins"` / `"defense_wins"` / `"mixed"` | from Stage 3 |
| `scoring_targets.acceptable_resolutions` | flat string array | `compute_fvc()` line 168 | `["critique_wins"]` / `["defense_wins"]` / `["empirical_test_agreed"]` | from Stage 3 |
| `scoring_targets.must_find_issue_ids` | string array | `compute_idr()` | from RC flaw `issue_id` | from Stage 3 |
| `scoring_targets.must_not_claim` | string array | `compute_idp()` | from RC-3 extraction | from Stage 3 |
| `planted_issues` | array | `compute_idr()` | from RC flaw records | from Stage 3 |
| `sound_design_reference` | string / `null` | metadata only | `null` | design narrative |
| `is_real_paper_case` | bool | metadata | `true` | `false` |
| `_pipeline.case_type` | `"rc"` / `"regular"` / `"mixed"` / `"defense"` | metadata | `"rc"` | `"regular"` / `"mixed"` / `"defense"` |
| `_pipeline.proxy_mean` | float / `null` | **NOT used for gating** | `null` | stored for traceability only |

---

## Critical Format Constraints

1. `acceptable_resolutions` MUST be a **flat string array** — `self_debate_poc.py` line 168 reads
   `st.get('acceptable_resolutions', [ideal_resolution])` without unwrapping. A nested object
   or single string will silently break `compute_fvc()`.

2. `difficulty` is `null` at normalization; Phase 3 pilot fills it via baseline FC proxy
   (FC < 0.60 → `"hard"`, 0.60–0.80 → `"medium"`). All 160 regular cases must be labeled
   before Phase 4 commit. `_pipeline.proxy_mean` is stored but **NOT** used as a difficulty
   gate (PM3 prevention).

3. RC `planted_issues` entries have `corruption_id = null` — scoring engine reads `issue_id` only.

---

## Changelog

- **v7 update (2026-04-12):** `category` added `"defense"` (new stratum, n=40).
  `correct_position` values aligned with model verdict space (`"critique_wins"` /
  `"defense_wins"` / `"empirical_test_agreed"`) — v6 used routing labels (`"critique"` /
  `"defense"` / `"mixed"`); v7 enables direct FVC scoring via `verdict == correct_position`.
  `_pipeline.case_type` added `"defense"`. Difficulty labeling method changed from GPT-4o
  rubric to baseline FC proxy. See `design_decisions.md §2–§3` for rationale.
