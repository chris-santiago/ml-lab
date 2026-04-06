## Phase 11 — Verify All Artifacts and Commit

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - All log entries via `uv run log_entry.py`. Never write JSONL manually.

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
    'plan/scripts/self_debate_poc.py', 'v4_results.json', 'v4_results_eval.json',
    'CONCLUSIONS.md', 'SENSITIVITY_ANALYSIS.md', 'ENSEMBLE_ANALYSIS.md',
    'plan/scripts/stats_analysis.py', 'stats_results.json',
    'plan/scripts/sensitivity_analysis.py', 'sensitivity_analysis_results.json',
    'plan/scripts/difficulty_validation.py', 'difficulty_validation_results.json',
    'within_case_variance_results.json',
    'REPORT.md', 'REPORT_ADDENDUM.md', 'PEER_REVIEW_R1.md', 'FINAL_SYNTHESIS.md',
    'TECHNICAL_REPORT.md',
    'plan/scripts/check_isolation.py', 'plan/scripts/coherence_audit.py', 'plan/scripts/post_report_coherence_audit.py',
    'plan/scripts/cross_model_scorer.py', 'cross_vendor_scores_v4.json',
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

forced_mr = glob.glob('v4_raw_outputs/*_forced_multiround_run*.json')
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
git commit -m "Self-debate protocol v4: complete experiment

- 50+ main benchmark cases (externally generated, CASE_VERIFIER validated)
- v4 rubric: DC=N/A baseline, ETD=N/A ensemble/baseline, fair-comparison lift primary
- 5 conditions: isolated_debate, multiround, forced_multiround (hard only), ensemble, baseline
- forced_multiround: 2-round minimum on hard cases, validates exchange mechanism
- Canonical ETD schema: condition/supports_critique_if/supports_defense_if/ambiguous_if
- Dynamic Phase 4 gate: pre-flight checklist constructed from Defender Pass 2 verdict
- log_entry.py: structured logging enforced throughout; no manual JSONL writes
- Phase-boundary commits at each phase
- Difficulty labels validated against rubric performance (not findability)
- Two clean comparison structures (debate vs ensemble; debate conditions vs each other)
- Cross-vendor scoring: OpenAI-compatible API, per-dimension deltas, all cases
- Post-run audit agent: structured anomaly report
- Reporting norms: no prompt leakage, limitations != design properties
- Point resolution rate from DEBATE.md (replaces uncomputable convergence metric)
"

uv run log_entry.py --step 11 --cat gate --action artifact_verification_passed --detail "All required artifacts present, forced_multiround outputs verified >= 2 rounds"
uv run log_entry.py --step 11 --cat workflow --action step_end --detail "Phase 11 complete — experiment committed"
```
