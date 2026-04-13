# Data Acquisition — v7

**Date:** 2026-04-13
**Extraction model:** `openai/gpt-5.4` (RC-2 and RC-3, via OpenRouter)

---

## Sources

| Source | Reports fetched | Notes |
|---|---|---|
| OpenReview (RC 2020–2023) | 0 | All 12 venue patterns returned 403 Forbidden |
| ReScience C (GitHub MLRC) | 80 | Full yield from `ReScience/MLRC` repo |
| **Total** | **80** | |

## Pipeline Results

| Stage | Input | Output | Notes |
|---|---|---|---|
| RC-1 (fetch) | — | 80 reports | ReScience C only; OpenReview API blocked |
| RC-2 (flaw extraction) | 80 | 80 (0 failed) | GPT-5.4, 22s wall time |
| RC-3 (must_not_claim) | 80 | 73 usable | 7 skipped (no extractable flaws) |
| RC-4 (filter + gate) | 73 | 73 passed (0 rejected) | No contamination hits |

## Yield by Stratum

| Category | RC yield | v7 target | Synthetic needed |
|---|---|---|---|
| critique (→ regular) | 5 | 160 | ~155 |
| mixed | 50 | 80 | ~30 |
| defense | 18 | 40 | ~22 |
| **Total** | **73** | **280** | **~207** |

## Yield Gate Decision

**LOW YIELD** — regular < 60 (got 5). Supplement all three strata with synthetic
generation pipeline (Phase 2).

Note: GPT-5.4 classified significantly fewer cases as pure `critique` compared to
v6's GPT-4o (5 vs 22). More cases landed in `mixed` (50 vs 45) and `defense` (18 vs 8).
The newer model appears more conservative about labeling ambiguous methodology as
clear-cut flawed.

## Defense Case Source

RC provides 18 of 40 needed defense cases. Remaining 22 will be generated synthetically
with `correct_position = "defense_wins"` and `is_synthetic_defense: true` flag
(per Phase 1 step 1.4).

## Pipeline Path

**RC + synthetic supplement** for all three strata. No RC-only path available.

## Output

`pipeline/run/rc_candidates/rc_cases_raw.json` — 73 cases (5 critique, 50 mixed, 18 defense)
