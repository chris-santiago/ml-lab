# ml-debate-lab

## Experiment Structure
- v2: complete — results in `self_debate_experiment_v2/`
- v3: complete — results in `self_debate_experiment_v3/`; issues tracked in `POST_MORTEM.md`
- v4: in preparation — entry point: `self_debate_experiment_v4/plan/PLAN.md`; phases: `plan/phases/`; scripts: `plan/scripts/`; benchmark cases: `synthetic-candidates/`
- Benchmark case metadata (must_find, acceptable_resolutions, correct_position, ideal_resolution): `plan/scripts/self_debate_poc.py`
- Agent reference copies: `agents/`
- Investigation logs: `INVESTIGATION_LOG.jsonl` in the experiment directory (JSONL, one entry per action)

## Artifact Sync
After any experiment, analysis step, or issue resolution — run `/artifact-sync` before marking work complete.
This command updates all artifacts, then runs a three-check coherence audit (conflicts, staleness, completeness).

## Agent Sync
After editing any file in `agents/` — run `/sync-agents` to copy the updated files to `~/.claude/agents/`.
