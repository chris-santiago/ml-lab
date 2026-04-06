## Phase 10 — Cross-Vendor Scorer

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

> **Purpose:** Score ALL cases using an external model family to rule out same-company scoring bias across all rubric dimensions (not just IDR). Issue 11 and 16 remediation.

> **Only step requiring an external API key. The corrected API pattern uses the OpenAI-compatible endpoint.**

```bash
export CROSS_VENDOR_API_KEY="your_key_here"
export CROSS_VENDOR_BASE_URL="https://api.minimax.io/v1"   # or your chosen provider
export CROSS_VENDOR_MODEL="MiniMax-M1"                      # or your chosen model
```

> **Script:** `plan/scripts/cross_model_scorer.py` — cross-vendor per-dimension validation using an external OpenAI-compatible API. Scores IDR, IDP, and FVC on ALL cases. Strips `<think>` tags from responses. Computes per-dimension deltas between Claude and external model scores. Flags bias if any delta > 0.1. Writes `cross_vendor_scores_v4.json`. Requires `CROSS_VENDOR_API_KEY` and `CROSS_VENDOR_BASE_URL` env vars. Dep: openai>=1.0.

```bash
uv run log_entry.py --step 10 --cat workflow --action step_start --detail "Phase 10: cross-vendor scoring — external model validation of all dimensions"
CROSS_VENDOR_API_KEY=your_key \
CROSS_VENDOR_BASE_URL=https://api.minimax.io/v1 \
CROSS_VENDOR_MODEL=MiniMax-M1 \
uv run plan/scripts/cross_model_scorer.py
uv run log_entry.py --step 10 --cat exec --action run_cross_vendor_scorer --detail "cross_model_scorer.py complete — per-dimension deltas computed for all cases" --artifact cross_vendor_scores_v4.json
uv run log_entry.py --step 10 --cat write --action write_cross_vendor_scores --detail "cross_vendor_scores_v4.json written" --artifact cross_vendor_scores_v4.json
uv run log_entry.py --step 10 --cat workflow --action step_end --detail "Phase 10 complete"
```

**Phase 10 commit:**
```bash
git add self_debate_experiment_v4/cross_model_scorer.py \
        self_debate_experiment_v4/cross_vendor_scores_v4.json
git commit -m "chore: snapshot v4 phase 10 artifacts — cross-vendor scoring results [none]"
uv run log_entry.py --step 10 --cat exec --action commit_phase_artifacts --detail "committed phase 10 artifacts: cross_model_scorer.py, cross_vendor_scores_v4.json"
```

---
