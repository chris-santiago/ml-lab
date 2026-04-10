# sensitivity_analysis.py
# /// script
# requires-python = ">=3.10"
# ///
# v5: DC=N/A for baseline — no structural correction needed.
# Reports: fair-comparison lift (primary), raw lift (secondary), dimension-stratified analysis.
import json

with open('v5_results.json') as f:
    d = json.load(f)
results = d['cases']

fair_dims = ['IDR', 'IDP', 'DRQ', 'FVC']
debate_only_dims = ['DC', 'ETD']

def dim_mean(results_list, condition, dims):
    vals = [run['scores'].get(dim) for r in results_list for run in r[condition]['runs']
            for dim in dims if run['scores'].get(dim) is not None]
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

# PRE-5: Method A — per-case-mean aggregation (average of each case's fair_comparison_mean)
def per_case_fc_mean(results_list, condition):
    vals = [r[condition].get('fair_comparison_mean') for r in results_list
            if r.get(condition, {}).get('fair_comparison_mean') is not None]
    return round(sum(vals) / len(vals), 4) if vals else None

pc_isolated = per_case_fc_mean(results, 'isolated_debate')
pc_baseline = per_case_fc_mean(results, 'baseline')
pc_lift = round(pc_isolated - pc_baseline, 4) if pc_isolated is not None and pc_baseline is not None else None

# PRE-5: Method B — per-dimension lift (average of per-dimension means)
# fc_isolated / fc_baseline already computed above via dim_mean
pd_lift = fc_lift_isolated  # dim_mean is the per-dimension method

# PRE-5: Divergence check (threshold: 0.05)
pre5_divergence = round(abs(pc_lift - pd_lift), 4) if pc_lift is not None and pd_lift is not None else None
pre5_flagged = pre5_divergence is not None and pre5_divergence > 0.05
pre5_warning = (
    f"PRE-5 ALERT: Method A lift ({pc_lift:+.4f}) and Method B lift ({pd_lift:+.4f}) "
    f"diverge by {pre5_divergence:.4f} > 0.05. Aggregate fc_lift may be confounded by "
    f"stratum composition. Report both values in CONCLUSIONS.md."
    if pre5_flagged else None
)

sensitivity_output = {
    'primary_metric': 'fair_comparison_lift',
    'note': 'v5: DC=N/A for baseline; no structural penalty correction needed. Fair-comparison lift is the natural primary metric.',
    'pre5_lift_comparison': {
        'method_a_per_case_mean_lift': pc_lift,
        'method_b_per_dimension_lift': pd_lift,
        'divergence': pre5_divergence,
        'flagged': pre5_flagged,
        'warning': pre5_warning,
        'description': (
            'Method A: average of per-case fair_comparison_mean values (each case mean computed '
            'over its non-null applicable dimensions). '
            'Method B: per-dimension means averaged across applicable cases, then averaged across dims. '
            'Flagged if divergence > 0.05 (PRE-5 requirement).'
        ),
    },
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

print(f"Fair-comparison lift (Method A per-case):  {pc_lift:+.4f}" if pc_lift is not None else "Fair-comparison lift (Method A): N/A")
print(f"Fair-comparison lift (Method B per-dim):   {pd_lift:+.4f}" if pd_lift is not None else "Fair-comparison lift (Method B): N/A")
print(f"Raw lift isolated vs baseline:             {raw_lift:+.4f}")
if pre5_flagged:
    print(f"\n*** {pre5_warning} ***")
else:
    print(f"PRE-5 divergence check: {'N/A' if pre5_divergence is None else f'{pre5_divergence:.4f} — PASS'}")
