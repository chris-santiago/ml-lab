# stats_analysis.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
#   "scipy>=1.11",
# ]
# ///
import json
import numpy as np
from scipy import stats as scipy_stats

with open('v5_results.json') as f:
    d = json.load(f)
results = d['cases']

isolated_means = [r['isolated_debate']['mean'] for r in results]
multiround_means = [r['multiround']['mean'] for r in results]
ensemble_means = [r['ensemble']['mean'] for r in results]
baseline_means = [r['baseline']['mean'] for r in results]

# Fair-comparison means (IDR/IDP/DRQ/FVC only)
fair_dims = ['IDR', 'IDP', 'DRQ', 'FVC']
debate_dims = ['IDR', 'IDP', 'DC', 'DRQ', 'ETD', 'FVC']

def dim_mean_for_runs(results_list, condition, dims):
    vals = [run['scores'].get(d) for r in results_list for run in r[condition]['runs']
            for d in dims if run['scores'].get(d) is not None]
    return round(sum(vals) / len(vals), 4) if vals else None

def bootstrap_ci(data, n=10000, ci=0.95):
    rng = np.random.default_rng(42)
    boot = [np.mean(rng.choice(data, len(data))) for _ in range(n)]
    alpha = (1 - ci) / 2
    return list(np.percentile(boot, [alpha * 100, (1 - alpha) * 100]))

def fair_diffs(results_list, cond_a, cond_b, dims):
    diffs = []
    for r in results_list:
        a_vals = [run['scores'].get(d) for run in r[cond_a]['runs']
                  for d in dims if run['scores'].get(d) is not None]
        b_vals = [run['scores'].get(d) for run in r[cond_b]['runs']
                  for d in dims if run['scores'].get(d) is not None]
        if a_vals and b_vals:
            diffs.append(np.mean(a_vals) - np.mean(b_vals))
    return diffs

def wilcoxon_test(diffs):
    diffs_nonzero = [x for x in diffs if x != 0]
    if len(diffs_nonzero) < 2:
        return None, None, None
    w, p = scipy_stats.wilcoxon(diffs, alternative='greater', correction=True)
    n = len(diffs_nonzero)
    r = float(1 - (2 * w) / (n * (n + 1))) if n > 0 else 0.0
    return float(w), float(p), r

# --- Comparison 1: debate vs ensemble (fair dims only) ---
ivb_fair = fair_diffs(results, 'isolated_debate', 'baseline', fair_dims)
ive_fair = fair_diffs(results, 'isolated_debate', 'ensemble', fair_dims)
mvb_fair = fair_diffs(results, 'multiround', 'baseline', fair_dims)
mvi_fair = fair_diffs(results, 'multiround', 'isolated_debate', fair_dims)

w1, p1, r1 = wilcoxon_test(ivb_fair)
w2, p2, r2 = wilcoxon_test(ive_fair)
w3, p3, r3 = wilcoxon_test(mvb_fair)
w4, p4, r4 = wilcoxon_test(mvi_fair)

# --- Comparison 2: debate conditions vs each other (all dims) ---
hard_results = [r for r in results if r['difficulty'] == 'hard']
fm_valid = [r for r in hard_results if r.get('forced_multiround', {}).get('mean') is not None]
fm_vs_mr = fair_diffs(fm_valid, 'forced_multiround', 'multiround', fair_dims) if fm_valid else []
w5, p5, r5 = wilcoxon_test(fm_vs_mr) if fm_vs_mr else (None, None, None)

mixed = [r for r in results if r['correct_position'] == 'mixed']
dw_cases = [r for r in results if r['correct_position'] == 'defense']

# Dimension aggregates
dim_agg = {}
for cond in ['isolated_debate', 'multiround', 'ensemble', 'baseline']:
    dim_agg[cond] = {}
    for dim in ['IDR', 'IDP', 'DC', 'DRQ', 'ETD', 'FVC']:
        vals = [run['scores'].get(dim) for r in results for run in r[cond]['runs']
                if run['scores'].get(dim) is not None]
        dim_agg[cond][dim] = round(sum(vals) / len(vals), 4) if vals else None

output = {
    'primary_metric': 'fair_comparison_lift_isolated_vs_baseline',
    'fair_comparison_dims': fair_dims,
    'bootstrap_cis': {
        'isolated_debate_mean': {'point': float(np.mean(isolated_means)), 'ci': bootstrap_ci(isolated_means)},
        'multiround_mean': {'point': float(np.mean(multiround_means)), 'ci': bootstrap_ci(multiround_means)},
        'ensemble_mean': {'point': float(np.mean(ensemble_means)), 'ci': bootstrap_ci(ensemble_means)},
        'baseline_mean': {'point': float(np.mean(baseline_means)), 'ci': bootstrap_ci(baseline_means)},
        'fair_comparison_lift_isolated_vs_baseline': {
            'point': float(np.mean(ivb_fair)) if ivb_fair else None,
            'ci': bootstrap_ci(ivb_fair) if ivb_fair else None
        },
        'raw_lift_isolated_vs_baseline': {
            'point': float(np.mean(isolated_means)) - float(np.mean(baseline_means)),
            'note': 'Raw lift; DC and ETD dims are N/A for baseline and excluded from mean computation'
        },
    },
    'wilcoxon_fair_dims': {
        'note': f'All tests on fair-comparison dims only: {fair_dims}',
        'isolated_vs_baseline': {'W': w1, 'p': p1, 'r': r1},
        'isolated_vs_ensemble': {'W': w2, 'p': p2, 'r': r2},
        'multiround_vs_baseline': {'W': w3, 'p': p3, 'r': r3},
        'multiround_vs_isolated': {'W': w4, 'p': p4, 'r': r4},
    },
    'wilcoxon_forced_multiround': {
        'note': 'Hard cases only; fair-comparison dims',
        'forced_multiround_vs_multiround_hard': {'W': w5, 'p': p5, 'r': r5,
                                                  'n_hard_cases': len(fm_valid)},
    },
    'mixed_position': {
        'n': len(mixed),
        'isolated_fair_mean': dim_mean_for_runs(mixed, 'isolated_debate', fair_dims),
        'ensemble_fair_mean': dim_mean_for_runs(mixed, 'ensemble', fair_dims),
    },
    'defense_wins': {
        'n': len(dw_cases),
        'ensemble_dc_mean': float(np.mean([
            run['scores'].get('DC') for r in dw_cases
            for run in r['ensemble']['runs'] if run['scores'].get('DC') is not None
        ])) if dw_cases else None,
        'pre_specified_criterion_met': None,
    },
    'dimension_aggregates': dim_agg,
    'within_case_variance': {
        cond: round(float(np.mean([r[cond]['std'] for r in results if r[cond]['std'] is not None])), 4)
        for cond in ['isolated_debate', 'multiround', 'ensemble', 'baseline']
    },
    'failure_attribution': {},
}

# Defense_wins criterion
if dw_cases:
    dc_pass = sum(1 for r in dw_cases
                  if r['ensemble']['runs'] and (r['ensemble']['runs'][0]['scores'].get('DC') or 0) >= 0.5)
    output['defense_wins']['pre_specified_criterion_met'] = dc_pass >= 0.6 * len(dw_cases)

# Failure attribution
failure_counts = {}
for r in results:
    for run in r['isolated_debate']['runs']:
        fa = run.get('failure_attribution', 'none')
        failure_counts[fa] = failure_counts.get(fa, 0) + 1
output['failure_attribution'] = failure_counts

with open('stats_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Primary metric — fair-comparison lift (isolated vs baseline): {output['bootstrap_cis']['fair_comparison_lift_isolated_vs_baseline']['point']:+.4f}")
print(f"Raw lift (isolated vs baseline): {output['bootstrap_cis']['raw_lift_isolated_vs_baseline']['point']:+.4f}")
for k, v in output['bootstrap_cis'].items():
    if isinstance(v, dict) and 'ci' in v and v['ci']:
        print(f"  {k}: {v['point']:.4f} CI={v['ci']}")
