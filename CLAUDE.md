# ml-debate-lab

## Project Origin

This project started from a single question: can FastText-encoded device IDs and attributes be used as features for ML model consumption? The initial experiment ran in interactive Claude Code session. Once the process proved worth keeping, it became a saved monolith prompt — a single Claude command that ran end-to-end.

That monolith was refactored into modular agent dispatches as complexity grew, but the granularity got too fine and the agents lost overall context. The architecture consolidated back toward a mostly-monolithic structure with two agents debating each other, with context carefully bounded and controlled. That eventually became a reusable Claude plugin.

The plugin raised a new question: how do you evaluate the debate protocol itself? That led to a series of meta-evaluation experiments (v2, v3, v4) — testing whether the critic/defender debate structure actually surfaces real ML methodology flaws. Each round revealed calibration problems: cases were too easy, flaws were too obvious, baselines were too weak.

v5 is the response to that — generating a harder, more rigorous benchmark case library before running the main experiment. The case generation pipeline has itself undergone the same architectural recursion: monolith LLM prompt → agentic multi-stage prompt → Python-orchestrated multi-LLM pipeline with concurrent execution, validation gates, and automated smoke testing.

The original FastText idea has now recursed several levels deep into its own evaluation infrastructure.

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
- Set API keys in `.claude/settings.local.json` (gitignored) or in `UV.env` (gitignored) — `UV.env` is loaded automatically by `uv run` to inject env vars into the uv runtime
- Cross-vendor scoring (Phase 9) additionally requires: `CROSS_VENDOR_API_KEY`, `CROSS_VENDOR_BASE_URL`, `CROSS_VENDOR_MODEL`

## Key Patterns
- **Log entries:** Always use `uv run log_entry.py` — manual JSONL appends break schema and sequence monotonicity
- **Phase execution:** Phases are sequential and not independently runnable; each depends on prior phase outputs

## Artifact Sync
After any experiment, analysis step, or issue resolution — run `/artifact-sync` before marking work complete.
This command updates all artifacts, then runs a three-check coherence audit (conflicts, staleness, completeness).

## Agent Sync
After editing any file in `agents/` — run `/sync-agents` to copy the updated files to `~/.claude/agents/`.

