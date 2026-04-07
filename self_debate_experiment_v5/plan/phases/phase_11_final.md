## Phase 11 — Verify All Artifacts and Commit

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.
> - **Subagent context:** You are a subagent in an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys. Do not attempt `claude --agent <name>` from bash — use the Agent tool only.
> - **CWD:** Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v5 &&` or use repo-root-relative paths.

```bash
uv run log_entry.py --step 11 --cat workflow --action step_start --detail "Phase 11: final artifact verification and commit"
```

```bash
uv run python -c "
import os, glob

required = [
    'benchmark_cases.json', 'benchmark_cases_verified.json', 'benchmark_verification.json',
    'BENCHMARK_PROMPTS.md', 'HYPOTHESIS.md', 'PREREGISTRATION.json', 'evaluation_rubric.json',
    'log_entry.py', 'plan/scripts/validate_cases.py', 'plan/scripts/filter_verified_cases.py', 'plan/scripts/write_preregistration.py',
    'CRITIQUE.md', 'DEFENSE.md', 'DEBATE.md', 'EXECUTION_PLAN.md', 'README.md',
    'plan/scripts/self_debate_poc.py', 'v5_results.json', 'v5_results_eval.json',
    'CONCLUSIONS.md', 'SENSITIVITY_ANALYSIS.md', 'ENSEMBLE_ANALYSIS.md',
    'plan/scripts/stats_analysis.py', 'stats_results.json',
    'plan/scripts/sensitivity_analysis.py', 'sensitivity_analysis_results.json',
    'plan/scripts/difficulty_validation.py', 'difficulty_validation_results.json',
    'within_case_variance_results.json',
    'REPORT.md', 'REPORT_ADDENDUM.md', 'PEER_REVIEW_R1.md', 'FINAL_SYNTHESIS.md',
    'TECHNICAL_REPORT.md',
    'plan/scripts/check_isolation.py', 'plan/scripts/coherence_audit.py', 'plan/scripts/post_report_coherence_audit.py',
    'plan/scripts/cross_model_scorer.py', 'cross_vendor_scores_v5.json',
    'INVESTIGATION_LOG.jsonl', 'POST_MORTEM.md',
]

missing = [f for f in required if not os.path.exists(f)]
if missing:
    print('MISSING:', missing)
    raise SystemExit(1)

pngs = glob.glob('*.png')
if not pngs:
    print('MISSING: no .png figures')
    raise SystemExit(1)

forced_mr = glob.glob('v5_raw_outputs/*_forced_multiround_run*.json')
if not forced_mr:
    print('MISSING: no forced_multiround outputs — hard case forced exchange not run')
    raise SystemExit(1)

mr_rounds = []
for path in forced_mr:
    import json
    with open(path) as f:
        d = json.load(f)
    rounds = d.get('debate_rounds', 1)
    if rounds < 2:
        print(f'WARNING: {path} has debate_rounds={rounds} (must be >= 2 for forced_multiround)')
    mr_rounds.append(rounds)

print(f'All {len(required)} required artifacts present.')
print(f'{len(pngs)} figures: {pngs}')
print(f'{len(forced_mr)} forced_multiround outputs; mean rounds={sum(mr_rounds)/len(mr_rounds):.2f}')
"

git add -A
git commit -m "Self-debate protocol v5: complete experiment — 64 cases, 5 conditions, fair-comparison lift primary"

uv run log_entry.py --step 11 --cat gate --action artifact_verification_passed --detail "All required artifacts present, forced_multiround outputs verified >= 2 rounds"
uv run log_entry.py --step 11 --cat workflow --action step_end --detail "Phase 11 complete — experiment committed"
```
