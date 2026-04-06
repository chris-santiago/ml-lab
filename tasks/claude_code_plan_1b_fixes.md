# Claude Code Execution Plan 1b — Fixes Requiring New Experiments

**Purpose:** Execute the remaining v2 fixes that require new agent runs, human review followed by re-computation, or new data collection. Run after Plan 1a. Skip this plan if Plan 2 (v3 experiment) is run in short succession — v3 supersedes all of these.

**Prerequisites:**
- Plan 1a complete and committed
- Python 3.11+ with `anthropic`, `scipy`, `numpy` packages
- No API key needed for Fixes 1–2 (session auth). Fix 3 requires human review only.

> **Skip condition:** If you are running Plan 2 (v3 experiment) within days, skip this plan entirely. The v3 experiment runs the ensemble on external cases (Fix 1), the within-case variance on non-converging cases (Fix 2), and re-examines leakage (Fix 3) properly as part of its design. Running 1b before v3 produces results that will be superseded immediately.

---

## Fix 1 — Run Ensemble Baseline on External Fault-Detection Cases

> **Status: NOT DONE** — superseded if v3 experiment runs. See skip condition above.

**What:** The 10-case external IDR benchmark was run with the debate protocol only. Without a parallel ensemble run on the same cases, you cannot claim the debate's external IDR advantage is structural rather than case-specific. This closes OQ-3 from the action plan.

**Estimated cost:** ~40 agent calls (4 per case × 10 cases).

Give Claude Code this instruction:

```
Run the compute-matched ensemble baseline on all 10 cases in
external_benchmark/cases.json.

For each case:
- Dispatch 3 independent assessors with only the task_prompt (no must-find labels,
  no coaching, no role identity)
- Synthesize into a unified verdict with ETD output constraint:
  "If issues are genuine but empirically resolvable, specify the empirical test:
  measure / success_criterion / failure_criterion — all three required."
- Score using the same rubric as the debate protocol
- The scorer receives synthesized output + must-find labels in a separate call

Write external_benchmark/ensemble_results.json with per-case scores and an aggregate
IDR mean. Compare to the debate IDR of 0.95 already in external_benchmark/results.json.

Report: does the ensemble match debate IDR on external cases, or does the debate
show a structural advantage here too?
```

```python
# After the run, compute the comparison:
# compare_external_ensemble.py
import json

with open('external_benchmark/results.json') as f:
    debate = json.load(f)
with open('external_benchmark/ensemble_results.json') as f:
    ensemble = json.load(f)

debate_idr = debate['aggregate']['debate']['mean_IDR']

ensemble_idrs = [c['ensemble_scores']['IDR'] for c in ensemble['cases']
                 if c['ensemble_scores'].get('IDR') is not None]
ensemble_idr = sum(ensemble_idrs) / len(ensemble_idrs) if ensemble_idrs else None

print(f"External debate IDR:   {debate_idr:.3f}")
print(f"External ensemble IDR: {ensemble_idr:.3f}" if ensemble_idr else "External ensemble IDR: N/A")
if ensemble_idr:
    delta = debate_idr - ensemble_idr
    print(f"Delta (debate - ensemble): {delta:+.3f}")
    print("Structural advantage on external cases:" if delta > 0.05 else "No material advantage — compute budget sufficient")
```

```bash
python3 compare_external_ensemble.py
```

Add the comparison to `external_benchmark/results.json` aggregate and add a paragraph to `self_debate_experiment_v2/REPORT.md §7.1`.

```bash
git add external_benchmark/ensemble_results.json external_benchmark/results.json \
        self_debate_experiment_v2/REPORT.md
git commit -m "Fix 1b-1: ensemble baseline on external fault-detection cases

- external_benchmark/ensemble_results.json: new ensemble run on all 10 external cases
- Debate vs ensemble IDR comparison added to external_benchmark/results.json aggregate
- REPORT.md §7.1: external ensemble comparison paragraph added
"
```

---

## Fix 2 — Within-Case Variance on Non-Converging Cases

> **Status: COMPLETED — 2026-04-05.** Results: si003 debate_std=0.0, rw001 debate_std=0.0, mm002 debate_std=0.048 (Outcome B — DC stochasticity on mixed-position case; Judge verdict stable). See `within_case_variance_nonconverging.json`.

**What:** The within-case variance experiment ran 3 repetitions only on cases with convergence=1.0 (salient, unambiguous flaws). Whether debate_std stays 0.0 on genuinely contested cases (convergence=0.5) is unknown. This is the correct stress test for the determinism claim. Closes OQ-3 from the action plan.

**Cases to run:** The three cases with convergence=0.5 in the original benchmark:
- `metric_mismatch_002` (mixed position — the ensemble catastrophic failure case)
- `scope_intent_003` (hard, genuine verdict divergence)
- `real_world_framing_001` (the reasoning/label disconnect case, post-fix)

**Estimated cost:** ~36 agent calls (3 cases × 3 runs × 4 calls per run).

Give Claude Code this instruction:

```
Run the full debate protocol 3 independent times on each of these three cases
from self_debate_experiment_v2/BENCHMARK_PROMPTS.md:
- metric_mismatch_002
- scope_intent_003
- real_world_framing_001

Use the patched ml-defender (two-pass structure already applied).
For each case and each run, record the debate mean score using the v2 rubric.
Compute std across 3 runs for each case.

This tests whether debate_std=0.0 holds on cases where Critic and Defender
genuinely disagree (convergence=0.5), not just on cases where both agents
independently find the same unambiguous flaw.

Write results to self_debate_experiment_v2/within_case_variance_nonconverging.json.
```

```python
# After the run:
# analyze_nonconverging_variance.py
import json

with open('self_debate_experiment_v2/within_case_variance_results.json') as f:
    original = json.load(f)
with open('self_debate_experiment_v2/within_case_variance_nonconverging.json') as f:
    new = json.load(f)

print("Original variance results (convergence=1.0 cases):")
for case in original['cases']:
    print(f"  {case['case_id']}: debate_std={case['variance_summary']['debate_std']}")

print("\nNon-converging case variance results (convergence=0.5 cases):")
for case in new['cases']:
    std = case['variance_summary']['debate_std']
    print(f"  {case['case_id']}: debate_std={std}")
    if std > 0.0:
        print(f"    -> NON-ZERO VARIANCE: protocol is not deterministic on contested cases")
    else:
        print(f"    -> Still deterministic")
```

```bash
python3 analyze_nonconverging_variance.py
```

Add finding to REPORT.md §8.1 (Within-Case Variance section) as a follow-up note.

```bash
git add self_debate_experiment_v2/within_case_variance_nonconverging.json \
        self_debate_experiment_v2/REPORT.md
git commit -m "Fix 1b-2: within-case variance on non-converging cases

- within_case_variance_nonconverging.json: 3-run variance on metric_mismatch_002,
  scope_intent_003, real_world_framing_001 (convergence=0.5 cases)
- REPORT.md §8.1: follow-up finding added
"
```

---

## Fix 3 — Flag External Benchmark Leakage Cases and Recompute Clean IDR

> **Status: NOT DONE** — requires 30 min human review of `external_benchmark/cases.json`. Superseded if v3 experiment runs.

**What:** 7 of 10 external cases required verifier rewrites because the flaw was visible in the source description. These cases are not individually flagged in the JSON. Requires human review of `external_benchmark/cases.json` to determine which cases had leakage, then recomputes IDR on the clean subset.

**Estimated effort:** 30 minutes of human review. No new agent calls.

**Step 1 — Human review:**

```bash
# Print all cases with their sources for review
python3 -c "
import json
with open('external_benchmark/cases.json') as f:
    cases = json.load(f)
with open('external_benchmark/results.json') as f:
    results = json.load(f)
result_by_id = {c['case_id']: c for c in results['cases']}

for case in cases:
    cid = case.get('case_id', case.get('id', 'unknown'))
    source = case.get('source', case.get('paper', 'no source'))
    notes = result_by_id.get(cid, {}).get('notes', '')
    print(f'{cid}')
    print(f'  Source: {source}')
    print(f'  Notes: {notes[:150]}')
    print()
"
```

For each case, manually assess: was the flaw visible in the original source title or description before rewriting? Mark each case `leakage_rewrite: true` or `leakage_rewrite: false`.

**Step 2 — Add flags to JSON:**

```python
# fix_external_leakage_flags.py
# Edit this script to fill in the leakage_rewrite values after human review
import json

# FILL THESE IN AFTER REVIEWING THE CASES:
leakage_flags = {
    # 'case_id': True/False
    # Example: 'ext_broken_baseline_001': False,
    #          'ext_metric_mismatch_001': True,
    # ... fill in all 10 cases
}

with open('external_benchmark/results.json') as f:
    d = json.load(f)

flagged = 0
for case in d['cases']:
    cid = case['case_id']
    if cid in leakage_flags:
        case['leakage_rewrite'] = leakage_flags[cid]
        if leakage_flags[cid]:
            flagged += 1

# Compute clean-subset IDR
clean = [c for c in d['cases'] if not c.get('leakage_rewrite', False)]
clean_idrs = [c['debate_scores']['IDR'] for c in clean
              if c['debate_scores'].get('IDR') is not None]
clean_idr = sum(clean_idrs) / len(clean_idrs) if clean_idrs else None

d['aggregate']['debate']['clean_subset_IDR'] = clean_idr
d['aggregate']['debate']['clean_subset_n'] = len(clean)
d['aggregate']['debate']['leakage_rewrite_count'] = flagged

with open('external_benchmark/results.json', 'w') as f:
    json.dump(d, f, indent=2)

print(f"Flagged {flagged}/10 cases as leakage_rewrite=True")
print(f"Clean subset: {len(clean)} cases")
print(f"Clean subset IDR: {clean_idr:.3f}" if clean_idr else "Clean subset IDR: N/A")
```

```bash
# After filling in leakage_flags above:
python3 fix_external_leakage_flags.py
```

Update REPORT.md §7.1 with the clean-subset IDR figure.

```bash
git add external_benchmark/results.json self_debate_experiment_v2/REPORT.md
git commit -m "Fix 1b-3: flag external benchmark leakage cases, recompute clean IDR

- external_benchmark/results.json: leakage_rewrite flags added per case
- clean_subset_IDR computed on non-leaked cases only
- REPORT.md §7.1: clean subset IDR reported alongside headline 0.95 figure
"
```

---

## Final Verification

```bash
python3 -c "
import json, os

# Check Fix 1
if os.path.exists('external_benchmark/ensemble_results.json'):
    print('Fix 1 (external ensemble): DONE')
else:
    print('Fix 1 (external ensemble): MISSING')

# Check Fix 2
if os.path.exists('self_debate_experiment_v2/within_case_variance_nonconverging.json'):
    print('Fix 2 (non-converging variance): DONE')
else:
    print('Fix 2 (non-converging variance): MISSING')

# Check Fix 3
with open('external_benchmark/results.json') as f:
    d = json.load(f)
cases_flagged = sum(1 for c in d['cases'] if 'leakage_rewrite' in c)
print(f'Fix 3 (leakage flags): {cases_flagged}/10 cases flagged')
clean_idr = d.get('aggregate', {}).get('debate', {}).get('clean_subset_IDR')
print(f'  Clean subset IDR: {clean_idr}')
"
```
