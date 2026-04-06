# sensitivity_analysis.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
# ]
# ///
# v4: DC=N/A for baseline — no structural correction needed.
# Reports: fair-comparison lift (primary), raw lift (secondary), dimension-stratified analysis.
import json
import numpy as np

with open('v4_results.json') as f:
    d = json.load(f)
results = d['cases']

fair_dims = ['IDR', 'IDP', 'DRQ', 'FVC']
debate_only_dims = ['DC', 'ETD']

def dim_mean(results_list, condition, dims):
    vals = [run['scores'].get(dim) for r in results_list for run in r[condition]['runs']
            if run['scores'].get(dim) is not None for dim in dims]
    return round(sum(vals) / len(vals), 4) if vals else None

# Fair-comparison analysis
fc_isolated = dim_mean(results, 'isolated_debate', fair_dims)
fc_baseline = dim_mean(results, 'baseline', fair_dims)
fc_ensemble = dim_mean(results, 'ensemble', fair_dims)
fc_multiround = dim_mean(results, 'multiround', fair_dims)

fc_lift_isolated = round((fc_isolated or 0) - (fc_baseline or 0), 4) if fc_isolated and fc_baseline else None
fc_lift_ensemble = round((fc_isolated or 0) - (fc_ensemble or 0), 4) if fc_isolated and fc_ensemble else None

# Raw means (all applicable dims per condition)
raw_isolated = round(sum(r['isolated_debate']['mean'] for r in results) / len(results), 4)
raw_baseline = round(sum(r['baseline']['mean'] for r in results) / len(results), 4)
raw_lift = round(raw_isolated - raw_baseline, 4)

sensitivity_output = {
    'primary_metric': 'fair_comparison_lift',
    'note': 'v4: DC=N/A for baseline; no structural penalty correction needed. Fair-comparison lift is the natural primary metric.',
    'fair_comparison': {
        'dims': fair_dims,
        'isolated_debate_mean': fc_isolated,
        'baseline_mean': fc_baseline,
        'ensemble_mean': fc_ensemble,
        'multiround_mean': fc_multiround,
        'lift_isolated_vs_baseline': fc_lift_isolated,
        'lift_isolated_vs_ensemble': fc_lift_ensemble,
    },
    'raw_lift': {
        'isolated_debate_mean': raw_isolated,
        'baseline_mean': raw_baseline,
        'lift_isolated_vs_baseline': raw_lift,
        'note': 'Raw means include debate-only dimensions (DC, ETD) where applicable per condition. DC and ETD are N/A for baseline, so raw baseline mean reflects IDR/IDP/DRQ/FVC only.',
    },
    'dimension_stratified': {
        'fair_dims': {cond: dim_mean(results, cond, fair_dims) for cond in
                      ['isolated_debate', 'multiround', 'ensemble', 'baseline']},
        'debate_only_dims': {cond: dim_mean(results, cond, debate_only_dims) for cond in
                             ['isolated_debate', 'multiround']},
    },
}

with open('sensitivity_analysis_results.json', 'w') as f:
    json.dump(sensitivity_output, f, indent=2)

print(f"Fair-comparison lift isolated vs baseline: {fc_lift_isolated:+.4f}" if fc_lift_isolated else "Fair-comparison lift: N/A")
print(f"Raw lift isolated vs baseline:             {raw_lift:+.4f}")
