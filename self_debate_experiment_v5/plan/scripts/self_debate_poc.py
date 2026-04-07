# self_debate_poc.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Self-Debate Protocol v5 — Scoring Engine

Key changes from v3:
- DC = N/A for baseline (structural inapplicability, consistent with ETD N/A treatment)
- ETD = N/A for ensemble and baseline (no adversarial exchange; no contested-point structure)
- Single canonical ETD output schema: condition/supports_critique_if/supports_defense_if/ambiguous_if
- 5 conditions: isolated_debate, multiround, forced_multiround, ensemble, baseline
- DRQ NOT capped for any condition (DC=N/A removes need for structural override)
- Fair-comparison lift (IDR/IDP/IDJ/DRQ/FVC) as primary metric
- forced_multiround runs on hard cases only
- DC demoted to diagnostic-only: excluded from per-case mean and pass/fail criterion.
  Kept in scores dict for reporting and failure attribution. DC/FVC delta computed
  per condition as a divergence diagnostic in summary output.
"""

import json
from pathlib import Path
import argparse

OUTPUT_DIR = Path.cwd()

parser = argparse.ArgumentParser()
parser.add_argument('--cases', default='benchmark_cases_verified.json')
parser.add_argument('--output', default='v5_results.json')
args, _ = parser.parse_known_args()

CASES_FILE = OUTPUT_DIR / args.cases
RESULTS_FILE = OUTPUT_DIR / args.output
EVAL_RESULTS_FILE = OUTPUT_DIR / args.output.replace('.json', '_eval.json')

CONDITIONS = ['isolated_debate', 'multiround', 'forced_multiround', 'ensemble', 'baseline']
FAIR_COMPARISON_DIMS = ['IDR', 'IDP', 'IDJ', 'DRQ', 'FVC']
PRIMARY_SCORING_DIMS = ['IDR', 'IDP', 'IDJ', 'DRQ', 'ETD', 'FVC']  # DC excluded — diagnostic-only


def load_cases():
    with open(CASES_FILE) as f:
        return json.load(f)


def compute_idr(must_find_ids, issues_found):
    if not must_find_ids:
        return None
    found = [i for i in must_find_ids if i in issues_found]
    return round(len(found) / len(must_find_ids), 4)


def compute_idp(all_issues_raised, must_find_ids, must_not_claim):
    if not all_issues_raised:
        return 1.0
    invalid = [i for i in all_issues_raised if i in must_not_claim]
    valid = [i for i in all_issues_raised if i in must_find_ids]
    denominator = len(valid) + len(invalid)
    if denominator == 0:
        return 1.0
    frac = len(valid) / denominator
    if frac >= 0.9:
        return 1.0
    elif frac >= 0.5:
        return 0.5
    return 0.0


def compute_idj(must_find_ids, addressed_but_incorrectly_ids, justifications_challenged):
    """
    IDJ = fraction of addressed_but_incorrectly must_find issues where
    model correctly challenged the stated justification.
    N/A if no addressed_but_incorrectly issues in this case.
    """
    abi = [i for i in must_find_ids if i in addressed_but_incorrectly_ids]
    if not abi:
        return None
    challenged = [i for i in abi if i in justifications_challenged]
    frac = len(challenged) / len(abi)
    if frac >= 0.9: return 1.0
    elif frac >= 0.5: return 0.5
    return 0.0


def compute_fvc(verdict, acceptable_resolutions, ideal_resolution):
    if verdict in acceptable_resolutions:
        return 1.0
    adjacents = {
        ('critique_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'critique_wins'),
        ('defense_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'defense_wins'),
    }
    if (verdict, ideal_resolution) in adjacents:
        return 0.5
    return 0.0


def compute_dc(verdict, acceptable_resolutions, ideal_resolution, condition):
    """
    DC = N/A for baseline — structural inapplicability.
    Baseline has no Defender role. Penalizing absence of a role the condition was
    never designed to fill is not a legitimate comparison. Pre-registered in v5.
    """
    if condition == 'baseline':
        return None  # N/A — not 0.0
    return compute_fvc(verdict, acceptable_resolutions, ideal_resolution)


def compute_drq(verdict, acceptable_resolutions, ideal_resolution):
    """
    DRQ not capped for any condition in v5.
    DC=N/A for baseline removes the need for a structural cap on DRQ.
    """
    adjacents = {
        ('critique_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'critique_wins'),
        ('defense_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'defense_wins'),
    }
    if verdict == ideal_resolution:
        return 1.0
    elif verdict in acceptable_resolutions:
        return 0.5
    elif (verdict, ideal_resolution) in adjacents:
        return 0.5
    return 0.0


def compute_etd(empirical_test, ideal_resolution, condition):
    """
    ETD = N/A for ensemble and baseline (no adversarial exchange).
    ETD = N/A when ideal_resolution is critique_wins or defense_wins.
    Single canonical schema: condition/supports_critique_if/supports_defense_if/ambiguous_if
    """
    if condition in ('ensemble', 'baseline'):
        return None  # N/A — no adversarial exchange
    if ideal_resolution in ('critique_wins', 'defense_wins'):
        return None  # N/A — no contested territory
    if not empirical_test or not isinstance(empirical_test, dict):
        return 0.0
    has_condition = bool(empirical_test.get('condition'))
    has_supports_critique = bool(empirical_test.get('supports_critique_if'))
    has_supports_defense = bool(empirical_test.get('supports_defense_if'))
    # ambiguous_if is informative but does not increase score beyond full credit
    if has_condition and has_supports_critique and has_supports_defense:
        return 1.0
    elif has_condition and (has_supports_critique or has_supports_defense):
        return 0.5
    return 0.0


def attribute_failure(scores, condition, passes):
    if passes:
        return 'none'
    if condition == 'baseline':
        return 'protocol'
    failed = [k for k, v in scores.items() if v is not None and v < 0.5]
    if 'DC' in failed:
        return 'agent'
    if 'IDR' in failed:
        return 'agent'
    if 'DRQ' in failed or 'FVC' in failed:
        return 'protocol'
    return 'ambiguous'


def score_run(case, output, condition):
    gt = case['ground_truth']
    st = case['scoring_targets']
    idr_obj = case['ideal_debate_resolution']

    correct_position = gt['correct_position']
    ideal_resolution = idr_obj['type']
    acceptable_resolutions = st.get('acceptable_resolutions', [ideal_resolution])
    must_find_ids = st.get('must_find_issue_ids', [])
    must_not_claim = st.get('must_not_claim', [])

    verdict = output.get('verdict')
    issues_found = output.get('issues_found', [])
    all_issues_raised = output.get('all_issues_raised', [])
    empirical_test = output.get('empirical_test')
    addressed_but_incorrectly_ids = [
        p['issue_id'] for p in case.get('planted_issues', [])
        if p.get('addressed_but_incorrectly')
    ]
    justifications_challenged = output.get('justifications_challenged', [])

    scores = {}
    if correct_position == 'defense':
        scores['IDR'] = None
        scores['IDP'] = None
        scores['DC'] = None  # defense_wins: N/A per v5 rubric
    else:
        scores['IDR'] = compute_idr(must_find_ids, issues_found)
        scores['IDP'] = compute_idp(all_issues_raised, must_find_ids, must_not_claim)
        scores['DC'] = compute_dc(verdict, acceptable_resolutions, ideal_resolution, condition)

    scores['DRQ'] = compute_drq(verdict, acceptable_resolutions, ideal_resolution)
    scores['ETD'] = compute_etd(empirical_test, ideal_resolution, condition)
    scores['FVC'] = compute_fvc(verdict, acceptable_resolutions, ideal_resolution)
    scores['IDJ'] = compute_idj(must_find_ids, addressed_but_incorrectly_ids, justifications_challenged)

    # DC is diagnostic-only — excluded from primary mean and pass/fail criterion
    primary_vals = [scores[d] for d in PRIMARY_SCORING_DIMS if scores.get(d) is not None]
    mean = round(sum(primary_vals) / len(primary_vals), 4) if primary_vals else 0.0
    passes = mean >= 0.65 and all(v >= 0.5 for v in primary_vals)

    return {
        'scores': scores,
        'mean': mean,
        'passes': passes,
        'verdict': verdict,
        'failure_attribution': attribute_failure(scores, condition, passes),
        'issues_found': issues_found,
        'missed_issues': [i for i in must_find_ids if i not in issues_found],
        'false_positive_issues': [i for i in all_issues_raised if i in must_not_claim],
    }


def fair_comparison_mean(runs, dims=FAIR_COMPARISON_DIMS):
    """Mean across fair-comparison dimensions only (IDR, IDP, IDJ, DRQ, FVC)."""
    vals = [run['scores'].get(d) for run in runs for d in dims if run['scores'].get(d) is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def aggregate_runs(run_results):
    means = [r['mean'] for r in run_results]
    avg = round(sum(means) / len(means), 4) if means else 0.0
    std = round((sum((m - avg)**2 for m in means) / len(means))**0.5, 4) if means else 0.0
    fc_mean = fair_comparison_mean(run_results)
    return {'mean': avg, 'std': std, 'fair_comparison_mean': fc_mean,
            'passes': sum(1 for r in run_results if r['passes']), 'runs': run_results}


def main():
    cases = load_cases()
    raw_dir = OUTPUT_DIR / 'v5_raw_outputs'
    all_results = []
    eval_results = []

    for case in cases:
        cid = case['case_id']
        difficulty = case['difficulty']
        ideal = case['ideal_debate_resolution']['type']
        acceptable = case['scoring_targets'].get('acceptable_resolutions', [ideal])

        case_result = {
            'case_id': cid,
            'category': case['category'],
            'difficulty': difficulty,
            'correct_position': case['ground_truth']['correct_position'],
            'ideal_resolution': ideal,
            'acceptable_resolutions': acceptable,
            'must_find': case['scoring_targets'].get('must_find_issue_ids', []),
        }

        for condition in CONDITIONS:
            # forced_multiround only runs on hard cases
            if condition == 'forced_multiround' and difficulty != 'hard':
                case_result[condition] = {'mean': None, 'std': None, 'fair_comparison_mean': None,
                                          'passes': None, 'runs': [], 'note': 'not_applicable_difficulty'}
                continue

            run_results = []
            for run_idx in range(1, 4):
                path = raw_dir / f"{cid}_{condition}_run{run_idx}.json"
                if not path.exists():
                    print(f"WARNING: Missing {path}")
                    continue
                with open(path) as f:
                    output = json.load(f)
                run_results.append(score_run(case, output, condition))
            case_result[condition] = aggregate_runs(run_results)

        all_results.append(case_result)

        first = case_result['isolated_debate']['runs'][0] if case_result['isolated_debate']['runs'] else {}
        eval_results.append({
            'case_id': cid,
            'scores': first.get('scores', {}),
            'pass_fail': 'pass' if case_result['isolated_debate']['passes'] >= 2 else 'fail',
            'found_planted_issues': first.get('issues_found', []),
            'missed_planted_issues': first.get('missed_issues', []),
            'false_positive_issues': first.get('false_positive_issues', []),
            'was_resolution_valid': first.get('verdict') in acceptable if first else False,
            'failure_attribution': first.get('failure_attribution', 'none'),
        })

    n = len(all_results)
    isolated_means = [r['isolated_debate']['mean'] for r in all_results]
    multiround_means = [r['multiround']['mean'] for r in all_results]
    ensemble_means = [r['ensemble']['mean'] for r in all_results]
    baseline_means = [r['baseline']['mean'] for r in all_results]

    # Fair-comparison means (IDR/IDP/IDJ/DRQ/FVC only)
    isolated_fc = [r['isolated_debate']['fair_comparison_mean'] for r in all_results if r['isolated_debate']['fair_comparison_mean'] is not None]
    baseline_fc = [r['baseline']['fair_comparison_mean'] for r in all_results if r['baseline']['fair_comparison_mean'] is not None]
    fc_lift = round(sum(isolated_fc) / len(isolated_fc) - sum(baseline_fc) / len(baseline_fc), 4) if isolated_fc and baseline_fc else None

    bm_isolated = round(sum(isolated_means) / n, 4)
    bm_multiround = round(sum(multiround_means) / n, 4)
    bm_ensemble = round(sum(ensemble_means) / n, 4)
    bm_baseline = round(sum(baseline_means) / n, 4)
    d_pass_count = sum(1 for r in all_results if r['isolated_debate']['passes'] >= 2)
    d_pass_frac = round(d_pass_count / n, 4)
    # Primary criterion uses fair-comparison lift
    benchmark_passes = bm_isolated >= 0.65 and d_pass_frac >= 0.75 and (fc_lift is not None and fc_lift >= 0.10)

    # Hard cases only: forced_multiround comparison
    hard_results = [r for r in all_results if r['difficulty'] == 'hard']
    fm_hard = [r['forced_multiround']['mean'] for r in hard_results if r['forced_multiround']['mean'] is not None]
    mr_hard = [r['multiround']['mean'] for r in hard_results if r['multiround']['mean'] is not None]

    # DC/FVC divergence diagnostic — checks whether DC adds signal beyond FVC
    dc_fvc_diagnostic = {}
    for cond in CONDITIONS:
        deltas = []
        for r in all_results:
            cond_data = r.get(cond, {})
            for run in cond_data.get('runs', []):
                dc = run['scores'].get('DC')
                fvc = run['scores'].get('FVC')
                if dc is not None and fvc is not None:
                    deltas.append(abs(dc - fvc))
        dc_fvc_diagnostic[cond] = {
            'n_comparable_runs': len(deltas),
            'mean_abs_delta': round(sum(deltas) / len(deltas), 4) if deltas else None,
            'divergent_runs': sum(1 for d in deltas if d > 0.2),
            'divergence_rate': round(sum(1 for d in deltas if d > 0.2) / len(deltas), 4) if deltas else None,
        }

    summary = {
        'benchmark_isolated_debate_mean': bm_isolated,
        'benchmark_multiround_mean': bm_multiround,
        'benchmark_ensemble_mean': bm_ensemble,
        'benchmark_baseline_mean': bm_baseline,
        'fair_comparison_lift_isolated_vs_baseline': fc_lift,
        'raw_lift_isolated_vs_baseline': round(bm_isolated - bm_baseline, 4),
        'debate_pass_count': d_pass_count,
        'debate_pass_fraction': d_pass_frac,
        'benchmark_passes': benchmark_passes,
        'forced_multiround_hard_mean': round(sum(fm_hard) / len(fm_hard), 4) if fm_hard else None,
        'multiround_hard_mean': round(sum(mr_hard) / len(mr_hard), 4) if mr_hard else None,
        'protocol': 'v5_five_conditions',
        'dc_fvc_diagnostic': dc_fvc_diagnostic,
        'cases': all_results
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    with open(EVAL_RESULTS_FILE, 'w') as f:
        json.dump(eval_results, f, indent=2)

    print("=" * 80)
    print("V4 BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Case':<32} {'Iso':>5} {'MR':>5} {'FM*':>5} {'Ens':>5} {'Base':>5} Pass")
    print("-" * 80)
    for r in all_results:
        fm_val = r['forced_multiround']['mean']
        fm_str = f"{fm_val:>5.3f}" if fm_val is not None else "  N/A"
        passed = 'YES' if r['isolated_debate']['passes'] >= 2 else 'NO'
        print(f"{r['case_id']:<32} {r['isolated_debate']['mean']:>5.3f} {r['multiround']['mean']:>5.3f} {fm_str} {r['ensemble']['mean']:>5.3f} {r['baseline']['mean']:>5.3f} {passed}")
    print("-" * 80)
    print(f"{'BENCHMARK':<32} {bm_isolated:>5.3f} {bm_multiround:>5.3f} {'N/A':>5} {bm_ensemble:>5.3f} {bm_baseline:>5.3f}")
    print(f"\n* forced_multiround: hard cases only")
    print(f"\nFair-comparison lift (IDR/IDP/IDJ/DRQ/FVC): {fc_lift:+.4f}" if fc_lift else "\nFair-comparison lift: N/A")
    print(f"Raw lift isolated vs baseline:           {bm_isolated - bm_baseline:+.4f}")
    print(f"Isolated debate pass rate: {d_pass_count}/{n} ({d_pass_frac:.1%})")
    print(f"\nBENCHMARK OVERALL: {'PASSES' if benchmark_passes else 'FAILS'}")


if __name__ == '__main__':
    main()
