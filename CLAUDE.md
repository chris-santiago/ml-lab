# ml-debate-lab

## Prerequisites
- `uv` must be installed — no pyproject.toml exists; all scripts use PEP 723 inline headers
- All scripts must be run via `uv run <script>.py` (never `python3` directly)
- Agents (`ml-critic`, `ml-defender`, etc.) must be installed in `~/.claude/agents/` — copy from `agents/` or run `/plugin install`

## Experiment Structure
- v2: complete — results in `self_debate_experiment_v2/`
- v3: complete — results in `self_debate_experiment_v3/`; issues tracked in `POST_MORTEM.md`
- v4: complete — results in `self_debate_experiment_v4/`
- v5: active — entry point: `self_debate_experiment_v5/plan/PLAN.md`; phases: `plan/phases/`; scripts: `plan/scripts/`; benchmark cases: `synthetic-candidates/`
- Benchmark case metadata (must_find, acceptable_resolutions, correct_position, ideal_resolution): `plan/scripts/self_debate_poc.py`
- Agent reference copies: `agents/`
- Investigation logs: `INVESTIGATION_LOG.jsonl` in the experiment directory (JSONL, one entry per action)

## External LLM APIs
- External LLM calls use **OpenRouter** via the OpenAI SDK (`OPENROUTER_API_KEY` env var required)
- Currently used in the synthetic case generation pipeline; will expand to parts of the main experiment pipeline
- Main experiment scripts that run inside Claude Code agents do not call external APIs directly
- Set API keys in `.claude/settings.local.json` (gitignored) — not in environment or committed files
- Cross-vendor scoring (Phase 9) additionally requires: `CROSS_VENDOR_API_KEY`, `CROSS_VENDOR_BASE_URL`, `CROSS_VENDOR_MODEL`

## Key Patterns
- **Log entries:** Always use `uv run log_entry.py` — manual JSONL appends break schema and sequence monotonicity
- **Phase execution:** Phases are sequential and not independently runnable; each depends on prior phase outputs

## Artifact Sync
After any experiment, analysis step, or issue resolution — run `/artifact-sync` before marking work complete.
This command updates all artifacts, then runs a three-check coherence audit (conflicts, staleness, completeness).

## Agent Sync
After editing any file in `agents/` — run `/sync-agents` to copy the updated files to `~/.claude/agents/`.
