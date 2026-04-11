# self_debate_poc.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Self-Debate Protocol v6 — Scoring Engine

Changes from v5:
- 6 conditions: adds biased_debate; forced_multiround → conditional_fm
- DC dropped entirely (v5 empirical: mean_abs_delta = 0.0 across all conditions — redundant)
- Mixed case support: correct_position == 'mixed' nulls IDR/IDP (no planted flaws, no
  must-not-claim list, no definitive verdict). ETD is the sole primary signal on mixed cases.
- Pass criterion for mixed cases: ETD >= 0.5 (partial credit; condition + one criterion).
- ETD fires on mixed cases in debate conditions only (ETD_CONDITIONS).
- ETD analysis block in summary: mean ETD by condition for mixed cases only.
- biased_debate added to ETD_CONDITIONS (persona-primed agents, same protocol as isolated_debate)
- conditional_fm replaces forced_multiround (round 2 gated on unresolved disagreement)

Inherited from v5 (unchanged logic):
- ETD = N/A for ensemble_3x and baseline (no adversarial exchange)
- ETD = N/A when ideal_resolution is critique_wins or defense_wins
- Single canonical ETD schema: condition/supports_critique_if/supports_defense_if/ambiguous_if
- DRQ not capped for any condition
- Fair-comparison lift (IDR/IDP/DRQ/FVC) as primary metric for regular cases
"""

import json
from collections import Counter
from pathlib import Path
import argparse

OUTPUT_DIR = Path.cwd()

parser = argparse.ArgumentParser()
parser.add_argument('--cases', default='benchmark_cases_verified.json')
parser.add_argument('--output', default='v6_results.json')
parser.add_argument('--rescore-file', default='v6_rescored_idr_idp.json',
                    help='Rescored IDR/IDP JSON. Pass empty string to disable.')
parser.add_argument('--h1a-threshold', type=float, default=None,
                    help='Pre-registered H1a fc_lift threshold from HYPOTHESIS.md Phase 3. '
                         'If omitted, computed adaptively: max(0.03, min(0.10, (1-baseline_fc)*0.5)).')
args, _ = parser.parse_known_args()

CASES_FILE = OUTPUT_DIR / args.cases
RESULTS_FILE = OUTPUT_DIR / args.output
EVAL_RESULTS_FILE = OUTPUT_DIR / args.output.replace('.json', '_eval.json')

CONDITIONS = ['isolated_debate', 'biased_debate', 'multiround', 'conditional_fm', 'ensemble_3x', 'baseline']
FAIR_COMPARISON_DIMS = ['IDR', 'IDP', 'DRQ', 'FVC']
PRIMARY_SCORING_DIMS = ['IDR', 'IDP', 'DRQ', 'ETD', 'FVC']

# Debate conditions where ETD is applicable (adversarial exchange present)
ETD_CONDITIONS = {'isolated_debate', 'biased_debate', 'multiround', 'conditional_fm'}


def load_cases():
    with open(CASES_FILE) as f:
        cases = json.load(f)
    # Schema B guard: detect raw batch files passed directly to the scorer
    for c in cases:
        if 'ground_truth' not in c:
            raise ValueError(
                f"Case {c.get('case_id', '?')} is not in Schema B format "
                f"(missing 'ground_truth'). Run normalize_cases.py first to produce "
                f"benchmark_cases_raw.json, then pass that to --cases."
            )
    return cases


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


def compute_drq(verdict, acceptable_resolutions, ideal_resolution):
    """DRQ not capped for any condition."""
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
    ETD = N/A for ensemble_3x and baseline (no adversarial exchange).
    ETD = N/A when ideal_resolution is critique_wins or defense_wins.
    ETD fires on mixed cases in debate conditions — this is the primary use case in v6.
    """
    if condition in ('ensemble_3x', 'baseline'):
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


def attribute_failure(scores, condition, passes, correct_position):
    if passes:
        return 'none'
    if condition == 'baseline':
        return 'protocol'
    if correct_position == 'mixed':
        # ETD-only cases: failure is always agent (didn't produce the empirical test)
        return 'agent'
    failed = [k for k, v in scores.items() if v is not None and v < 0.5]
    if 'IDR' in failed:
        return 'agent'
    if 'DRQ' in failed or 'FVC' in failed:
        return 'protocol'
    return 'ambiguous'


def score_run(case, output, condition, rescored=None):
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
    # None when key absent (Phase 5 not yet outputting it); [] when present but empty
    all_issues_adjudicated = output.get('all_issues_adjudicated')
    empirical_test = output.get('empirical_test')

    scores = {}
    if correct_position == 'defense':
        scores['IDR'] = None
        scores['IDR_novel'] = None
        scores['IDP'] = None
        scores['IDP_adj'] = None
    elif correct_position == 'mixed':
        # Mixed cases: no planted flaws, no must-not-claim list, no definitive verdict.
        # IDR/IDP are structurally inapplicable. ETD is the sole primary signal.
        scores['IDR'] = None
        scores['IDR_novel'] = None
        scores['IDP'] = None
        scores['IDP_adj'] = None
    else:
        # idr_documented: primary IDR (recall against documented RC flaws)
        if rescored and rescored.get('idr_documented') is not None:
            scores['IDR'] = rescored['idr_documented']
        else:
            scores['IDR'] = compute_idr(must_find_ids, issues_found)
        # idr_novel: novel valid concerns the debate raised (secondary; reported separately)
        scores['IDR_novel'] = rescored.get('idr_novel') if rescored else None
        # idp_raw: precision from all_issues_raised (primary, v5-comparable)
        if rescored and rescored.get('idp_raw') is not None:
            scores['IDP'] = rescored['idp_raw']
        else:
            scores['IDP'] = compute_idp(all_issues_raised, must_find_ids, must_not_claim)
        # IDP_adj: prefer rescore JSON value; fall back to inline computation
        if rescored and rescored.get('idp_adj') is not None:
            scores['IDP_adj'] = rescored['idp_adj']
        else:
            scores['IDP_adj'] = (
                compute_idp(all_issues_adjudicated, must_find_ids, must_not_claim)
                if all_issues_adjudicated is not None else None
            )

    scores['DRQ'] = compute_drq(verdict, acceptable_resolutions, ideal_resolution)
    scores['ETD'] = compute_etd(empirical_test, ideal_resolution, condition)
    scores['FVC'] = compute_fvc(verdict, acceptable_resolutions, ideal_resolution)

    # Pass criterion differs for mixed cases.
    # Mixed: ETD >= 0.5 — partial ETD credit (condition + one criterion) is sufficient.
    # Standard: mean(non-null primary dims) >= 0.65 AND all >= 0.5.
    if correct_position == 'mixed':
        etd_score = scores.get('ETD')
        passes = etd_score is not None and etd_score >= 0.5
        mean = etd_score if etd_score is not None else 0.0
    else:
        primary_vals = [scores[d] for d in PRIMARY_SCORING_DIMS if scores.get(d) is not None]
        mean = round(sum(primary_vals) / len(primary_vals), 4) if primary_vals else 0.0
        passes = mean >= 0.65 and all(v >= 0.5 for v in primary_vals)

    return {
        'scores': scores,
        'mean': mean,
        'passes': passes,
        'verdict': verdict,
        'failure_attribution': attribute_failure(scores, condition, passes, correct_position),
        'issues_found': issues_found,
        'missed_issues': [i for i in must_find_ids if i not in issues_found],
        'false_positive_issues': [i for i in all_issues_raised if i in must_not_claim],
        'false_positive_issues_adj': [i for i in (all_issues_adjudicated or []) if i in must_not_claim],
    }


def fair_comparison_mean(runs, dims=FAIR_COMPARISON_DIMS):
    """Mean across fair-comparison dimensions only (IDR, IDP, DRQ, FVC)."""
    vals = [run['scores'].get(d) for run in runs for d in dims if run['scores'].get(d) is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def aggregate_runs(run_results):
    means = [r['mean'] for r in run_results]
    avg = round(sum(means) / len(means), 4) if means else 0.0
    std = round((sum((m - avg)**2 for m in means) / len(means))**0.5, 4) if means else 0.0
    fc_mean = fair_comparison_mean(run_results)
    return {'mean': avg, 'std': std, 'fair_comparison_mean': fc_mean,
            'passes': sum(1 for r in run_results if r['passes']), 'runs': run_results}


def compute_ensemble_union_idr(run_outputs, must_find_ids, rescored_list):
    """
    Union IDR for ensemble_3x: an issue is 'found' if ANY assessor found it.

    Prefers per-assessor found_booleans from the Phase 6 rescore file (semantic matching).
    Falls back to raw issues_found union when rescore is absent or lacks found_booleans.

    Returns None when must_find_ids is empty (defense/mixed — IDR structurally N/A).
    """
    if not must_find_ids:
        return None
    union_found = set()
    for i, output in enumerate(run_outputs):
        rescored = rescored_list[i] if rescored_list else None
        if rescored and 'found_booleans' in rescored:
            # Phase 6 semantic matching: per-issue boolean per assessor
            fb = rescored['found_booleans']
            union_found.update(iid for iid in must_find_ids if fb.get(iid, False))
        else:
            # Raw string matching: issue_id present in issues_found list
            issues_found = output.get('issues_found', [])
            union_found.update(iid for iid in must_find_ids if iid in issues_found)
    return round(len(union_found) / len(must_find_ids), 4)


def apply_ensemble_corrections(run_results, run_outputs, rescored_list,
                                must_find_ids, acceptable_resolutions, ideal_resolution,
                                correct_position):
    """
    Post-process run_results for ensemble_3x per the v6 split rule (PLAN.md §7):
      - IDR (recall):     union across all assessors — any-assessor-found credit
      - FVC, DRQ (verdict quality): computed from the majority verdict across assessors
      - IDP:              per-assessor averaged (unchanged — precision is per-assessor)

    Issues_found / missed_issues remain per-assessor for audit-trail visibility.
    Mutates run_results in-place; returns metadata dict for _ensemble_meta.
    """
    if not run_results:
        return {}

    # Union IDR (None for defense/mixed where must_find_ids is empty)
    union_idr = compute_ensemble_union_idr(run_outputs, must_find_ids, rescored_list)

    # Majority verdict: most common verdict string across all assessors
    verdicts = [o.get('verdict') for o in run_outputs if o.get('verdict')]
    majority_verdict = Counter(verdicts).most_common(1)[0][0] if verdicts else None
    majority_fvc = (
        compute_fvc(majority_verdict, acceptable_resolutions, ideal_resolution)
        if majority_verdict else None
    )
    majority_drq = (
        compute_drq(majority_verdict, acceptable_resolutions, ideal_resolution)
        if majority_verdict else None
    )

    for run in run_results:
        # IDR override (only for cases where IDR is applicable)
        if union_idr is not None and correct_position not in ('defense', 'mixed'):
            run['scores']['IDR'] = union_idr
        # FVC and DRQ override (majority verdict, all case types)
        if majority_fvc is not None:
            run['scores']['FVC'] = majority_fvc
        if majority_drq is not None:
            run['scores']['DRQ'] = majority_drq

        # Recompute per-run mean and passes with updated scores
        if correct_position == 'mixed':
            # Mixed: ETD >= 0.5 pass criterion — ETD is N/A for ensemble (no adversarial exchange)
            etd_score = run['scores'].get('ETD')
            run['mean'] = etd_score if etd_score is not None else 0.0
            run['passes'] = etd_score is not None and etd_score >= 0.5
        else:
            primary_vals = [
                run['scores'][d] for d in PRIMARY_SCORING_DIMS
                if run['scores'].get(d) is not None
            ]
            run['mean'] = round(sum(primary_vals) / len(primary_vals), 4) if primary_vals else 0.0
            run['passes'] = run['mean'] >= 0.65 and all(v >= 0.5 for v in primary_vals)

    return {
        'union_idr': union_idr,
        'majority_verdict': majority_verdict,
        'per_run_verdicts': [o.get('verdict') for o in run_outputs],
    }


def etd_mean_for_condition(results, condition):
    """Mean ETD score across all runs of a condition, nulls excluded."""
    vals = []
    for r in results:
        cond_data = r.get(condition, {})
        for run in cond_data.get('runs', []):
            etd = run['scores'].get('ETD')
            if etd is not None:
                vals.append(etd)
    return round(sum(vals) / len(vals), 4) if vals else None


def main():
    cases = load_cases()
    raw_dir = OUTPUT_DIR / 'v6_raw_outputs'
    all_results = []
    eval_results = []

    # Load rescored IDR/IDP if available
    rescore_map = {}
    rescore_path = OUTPUT_DIR / args.rescore_file if args.rescore_file else None
    if rescore_path and rescore_path.exists():
        rescore_map = json.load(open(rescore_path)).get('scores', {})
        print(f'Loaded rescored IDR/IDP for {len(rescore_map)} files from {rescore_path.name}')
    else:
        print('WARNING: No rescore file found — using original (leakage-inflated) IDR/IDP')

    for case in cases:
        cid = case['case_id']
        difficulty = case['difficulty']
        correct_position = case['ground_truth']['correct_position']
        ideal = case['ideal_debate_resolution']['type']
        acceptable = case['scoring_targets'].get('acceptable_resolutions', [ideal])
        must_find_ids = case['scoring_targets'].get('must_find_issue_ids', [])

        case_result = {
            'case_id': cid,
            'category': case.get('category', correct_position),
            'difficulty': difficulty,
            'correct_position': correct_position,
            'ideal_resolution': ideal,
            'acceptable_resolutions': acceptable,
            'must_find': must_find_ids,
        }

        for condition in CONDITIONS:
            if condition == 'conditional_fm' and difficulty != 'hard':
                case_result[condition] = {'mean': None, 'std': None, 'fair_comparison_mean': None,
                                          'passes': None, 'runs': [], 'note': 'not_applicable_difficulty'}
                continue

            if condition == 'ensemble_3x':
                # Load all assessor outputs before scoring — required for union IDR computation.
                # Standard conditions can stream-and-score; ensemble must pre-load all 3 runs.
                loaded = []
                for run_idx in range(1, 4):
                    path = raw_dir / f"{cid}_{condition}_run{run_idx}.json"
                    if not path.exists():
                        print(f"WARNING: Missing {path}")
                        continue
                    with open(path) as f:
                        output = json.load(f)
                    loaded.append((path, output, rescore_map.get(path.name)))

                run_results = [
                    score_run(case, output, condition, rescored=rescored)
                    for _, output, rescored in loaded
                ]

                # Apply v6 split rule: union IDR + majority-vote FVC/DRQ
                ensemble_meta = apply_ensemble_corrections(
                    run_results,
                    [o for _, o, _ in loaded],
                    [r for _, _, r in loaded],
                    must_find_ids, acceptable, ideal, correct_position,
                )
                case_result[condition] = aggregate_runs(run_results)
                case_result[condition]['_ensemble_meta'] = ensemble_meta
            else:
                run_results = []
                for run_idx in range(1, 4):
                    path = raw_dir / f"{cid}_{condition}_run{run_idx}.json"
                    if not path.exists():
                        print(f"WARNING: Missing {path}")
                        continue
                    with open(path) as f:
                        output = json.load(f)
                    rescored = rescore_map.get(path.name)
                    run_results.append(score_run(case, output, condition, rescored=rescored))
                case_result[condition] = aggregate_runs(run_results)

        all_results.append(case_result)

        first = case_result['isolated_debate']['runs'][0] if case_result['isolated_debate']['runs'] else {}
        eval_results.append({
            'case_id': cid,
            'correct_position': correct_position,
            'scores': first.get('scores', {}),
            'pass_fail': 'pass' if case_result['isolated_debate']['passes'] >= 2 else 'fail',
            'found_planted_issues': first.get('issues_found', []),
            'missed_planted_issues': first.get('missed_issues', []),
            'false_positive_issues': first.get('false_positive_issues', []),
            'was_resolution_valid': first.get('verdict') in acceptable if first else False,
            'failure_attribution': first.get('failure_attribution', 'none'),
        })

    # Split regular vs mixed for separate analysis
    regular_results = [r for r in all_results if r['correct_position'] != 'mixed']
    mixed_results   = [r for r in all_results if r['correct_position'] == 'mixed']

    n = len(all_results)
    n_regular = len(regular_results)
    n_mixed = len(mixed_results)

    # -----------------------------------------------------------------------
    # Regular case summary
    # -----------------------------------------------------------------------
    isolated_means    = [r['isolated_debate']['mean'] for r in regular_results]
    biased_means      = [r['biased_debate']['mean'] for r in regular_results]
    multiround_means  = [r['multiround']['mean'] for r in regular_results]
    cfm_means         = [r['conditional_fm']['mean'] for r in regular_results]
    ensemble_means    = [r['ensemble_3x']['mean'] for r in regular_results]
    baseline_means    = [r['baseline']['mean'] for r in regular_results]

    isolated_fc = [r['isolated_debate']['fair_comparison_mean'] for r in regular_results
                   if r['isolated_debate']['fair_comparison_mean'] is not None]
    baseline_fc = [r['baseline']['fair_comparison_mean'] for r in regular_results
                   if r['baseline']['fair_comparison_mean'] is not None]
    ensemble_fc = [r['ensemble_3x']['fair_comparison_mean'] for r in regular_results
                   if r['ensemble_3x']['fair_comparison_mean'] is not None]
    fc_lift = round(
        sum(isolated_fc) / len(isolated_fc) - sum(baseline_fc) / len(baseline_fc), 4
    ) if isolated_fc and baseline_fc else None
    # H2: isolated_debate vs ensemble_3x (union IDR) — compute-matched structure test
    h2_fc_lift_isolated_vs_ensemble = round(
        sum(isolated_fc) / len(isolated_fc) - sum(ensemble_fc) / len(ensemble_fc), 4
    ) if isolated_fc and ensemble_fc else None

    bm_isolated   = round(sum(isolated_means) / n_regular, 4) if n_regular else None
    bm_biased     = round(sum(biased_means) / n_regular, 4) if n_regular else None
    bm_multiround = round(sum(multiround_means) / n_regular, 4) if n_regular else None
    bm_cfm        = round(sum(cfm_means) / n_regular, 4) if n_regular else None
    bm_ensemble_3x   = round(sum(ensemble_means) / n_regular, 4) if n_regular else None
    bm_baseline   = round(sum(baseline_means) / n_regular, 4) if n_regular else None
    d_pass_count  = sum(1 for r in regular_results if r['isolated_debate']['passes'] >= 2)
    d_pass_frac   = round(d_pass_count / n_regular, 4) if n_regular else None

    # H1a adaptive threshold — HYPOTHESIS.md formula: max(0.03, min(0.10, (1 - pilot_baseline_fc_mean) * 0.5))
    # Uses observed baseline FC mean as proxy; identical to pilot value if run after Phase 3.
    # Override with --h1a-threshold to use the exact pre-registered value.
    if args.h1a_threshold is not None:
        h1a_threshold = args.h1a_threshold
    elif baseline_fc:
        h1a_threshold = max(0.03, min(0.10, (1.0 - sum(baseline_fc) / len(baseline_fc)) * 0.5))
    else:
        h1a_threshold = 0.10  # upper-bound fallback when no baseline data
    benchmark_passes = (
        bm_isolated is not None and bm_isolated >= 0.65
        and d_pass_frac is not None and d_pass_frac >= 0.75
        and fc_lift is not None and fc_lift >= h1a_threshold
    )

    hard_results = [r for r in regular_results if r['difficulty'] == 'hard']
    cfm_hard = [r['conditional_fm']['mean'] for r in hard_results if r['conditional_fm']['mean'] is not None]
    mr_hard = [r['multiround']['mean'] for r in hard_results if r['multiround']['mean'] is not None]

    # IDP_adj means by condition (regular cases only; None when field absent in run outputs)
    idp_adj_means = {}
    for cond in CONDITIONS:
        vals = [
            run['scores'].get('IDP_adj')
            for r in regular_results
            for run in r.get(cond, {}).get('runs', [])
            if run['scores'].get('IDP_adj') is not None
        ]
        idp_adj_means[cond] = round(sum(vals) / len(vals), 4) if vals else None

    # IDR_novel means by condition (regular cases only; None when rescore file absent)
    idr_novel_means = {}
    for cond in CONDITIONS:
        vals = [
            run['scores'].get('IDR_novel')
            for r in regular_results
            for run in r.get(cond, {}).get('runs', [])
            if run['scores'].get('IDR_novel') is not None
        ]
        idr_novel_means[cond] = round(sum(vals) / len(vals), 4) if vals else None

    # -----------------------------------------------------------------------
    # ETD analysis — mixed cases only  [NEW v6]
    # ETD fires only in debate conditions × mixed cases. This block reports
    # mean ETD and pass rate (ETD >= 0.5) per condition across mixed cases.
    # -----------------------------------------------------------------------
    etd_analysis = {}
    if mixed_results:
        for cond in ETD_CONDITIONS:
            etd_scores = []
            for r in mixed_results:
                for run in r.get(cond, {}).get('runs', []):
                    etd = run['scores'].get('ETD')
                    if etd is not None:
                        etd_scores.append(etd)
            etd_analysis[cond] = {
                'n_observations': len(etd_scores),
                'mean_etd': round(sum(etd_scores) / len(etd_scores), 4) if etd_scores else None,
                'full_credit_rate': round(
                    sum(1 for e in etd_scores if e >= 1.0) / len(etd_scores), 4
                ) if etd_scores else None,
                'partial_credit_rate': round(
                    sum(1 for e in etd_scores if e >= 0.5) / len(etd_scores), 4
                ) if etd_scores else None,
                'zero_rate': round(
                    sum(1 for e in etd_scores if e == 0.0) / len(etd_scores), 4
                ) if etd_scores else None,
            }
        mixed_pass_count = sum(
            1 for r in mixed_results if r['isolated_debate']['passes'] >= 2
        )
        etd_analysis['mixed_pass_count'] = mixed_pass_count
        etd_analysis['mixed_pass_fraction'] = round(mixed_pass_count / n_mixed, 4) if n_mixed else None
        etd_analysis['n_mixed_cases'] = n_mixed
        etd_analysis['note'] = (
            'ETD fires only in debate conditions (isolated_debate, biased_debate, multiround, conditional_fm) '
            'on mixed cases. Pass criterion for mixed: ETD >= 0.5.'
        )

    # -----------------------------------------------------------------------
    # H1b: FVC lift for mixed cases — HYPOTHESIS.md H1b
    # mean FVC(isolated_debate, mixed) > mean FVC(baseline, mixed)
    # PASS if bootstrap CI lower bound > 0 (computed separately from this raw data).
    # -----------------------------------------------------------------------
    h1b_fvc_mixed: dict = {}
    if mixed_results:
        for cond in CONDITIONS:
            fvc_vals = []
            for r in mixed_results:
                for run in r.get(cond, {}).get('runs', []):
                    fvc = run['scores'].get('FVC')
                    if fvc is not None:
                        fvc_vals.append(fvc)
            h1b_fvc_mixed[f'mean_fvc_{cond}'] = round(sum(fvc_vals) / len(fvc_vals), 4) if fvc_vals else None
        iso_fvc = h1b_fvc_mixed.get('mean_fvc_isolated_debate')
        base_fvc = h1b_fvc_mixed.get('mean_fvc_baseline')
        ens_fvc = h1b_fvc_mixed.get('mean_fvc_ensemble_3x')
        h1b_fvc_mixed['fvc_lift_isolated_vs_baseline'] = (
            round(iso_fvc - base_fvc, 4)
            if iso_fvc is not None and base_fvc is not None
            else None
        )
        # H2 mixed: isolated_debate vs ensemble_3x (majority-vote FVC) — structure test
        h1b_fvc_mixed['fvc_diff_isolated_vs_ensemble'] = (
            round(iso_fvc - ens_fvc, 4)
            if iso_fvc is not None and ens_fvc is not None
            else None
        )
        h1b_fvc_mixed['n_mixed_cases'] = n_mixed

    summary = {
        'protocol': 'v6_six_conditions_plus_mixed',
        'n_cases_total': n,
        'n_regular': n_regular,
        'n_mixed': n_mixed,
        # Regular case metrics
        'benchmark_isolated_debate_mean': bm_isolated,
        'benchmark_biased_debate_mean': bm_biased,
        'benchmark_multiround_mean': bm_multiround,
        'benchmark_conditional_fm_mean': bm_cfm,
        'benchmark_ensemble_3x_mean': bm_ensemble_3x,
        'benchmark_baseline_mean': bm_baseline,
        'fair_comparison_lift_isolated_vs_baseline': fc_lift,
        'h2_fc_lift_isolated_vs_ensemble': h2_fc_lift_isolated_vs_ensemble,
        'raw_lift_isolated_vs_baseline': round(bm_isolated - bm_baseline, 4) if bm_isolated and bm_baseline else None,
        'debate_pass_count': d_pass_count,
        'debate_pass_fraction': d_pass_frac,
        'benchmark_passes': benchmark_passes,
        'h1a_threshold': h1a_threshold,
        'conditional_fm_hard_mean': round(sum(cfm_hard) / len(cfm_hard), 4) if cfm_hard else None,
        'multiround_hard_mean': round(sum(mr_hard) / len(mr_hard), 4) if mr_hard else None,
        # H1b / ETD / mixed case metrics
        'h1b_fvc_mixed': h1b_fvc_mixed,
        'etd_analysis': etd_analysis,
        # IDP_adj: post-adjudication precision (regular cases; None when Phase 5 field absent)
        'idp_adj_means': idp_adj_means,
        # IDR_novel: novel concerns raised by debate not in RC report (secondary; None when rescore absent)
        'idr_novel_means': idr_novel_means,
        'cases': all_results,
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    with open(EVAL_RESULTS_FILE, 'w') as f:
        json.dump(eval_results, f, indent=2)

    print("=" * 80)
    print("V6 BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"  Regular cases: {n_regular}  |  Mixed cases: {n_mixed}  |  Total: {n}")
    print()
    if n_regular:
        print(f"{'Case':<32} {'Iso':>5} {'Bias':>5} {'MR':>5} {'CFM*':>5} {'Ens':>5} {'Base':>5} Pass")
        print("-" * 88)
        for r in regular_results:
            cfm_val = r['conditional_fm']['mean']
            cfm_str = f"{cfm_val:>5.3f}" if cfm_val is not None else "  N/A"
            passed = 'YES' if r['isolated_debate']['passes'] >= 2 else 'NO'
            bias_mean = r.get('biased_debate', {}).get('mean')
            bias_str = f"{bias_mean:>5.3f}" if bias_mean is not None else "  N/A"
            print(f"{r['case_id']:<32} {r['isolated_debate']['mean']:>5.3f} {bias_str} {r['multiround']['mean']:>5.3f} {cfm_str} {r['ensemble_3x']['mean']:>5.3f} {r['baseline']['mean']:>5.3f} {passed}")
        print("-" * 88)
        print(f"{'REGULAR BENCHMARK':<32} {bm_isolated:>5.3f} {'N/A':>5} {bm_multiround:>5.3f} {'N/A':>5} {bm_ensemble_3x:>5.3f} {bm_baseline:>5.3f}")
        print(f"\n* conditional_fm: hard cases only")
        print(f"\nFair-comparison lift (IDR/IDP/DRQ/FVC): {fc_lift:+.4f}" if fc_lift else "\nFair-comparison lift: N/A")
        print(f"Raw lift isolated vs baseline:           {bm_isolated - bm_baseline:+.4f}" if bm_isolated and bm_baseline else "")
        print(f"Isolated debate pass rate: {d_pass_count}/{n_regular} ({d_pass_frac:.1%})")
        h2_str = f"{h2_fc_lift_isolated_vs_ensemble:+.4f}" if h2_fc_lift_isolated_vs_ensemble is not None else "N/A"
        print(f"\nH2 FC lift isolated vs ensemble (union IDR): {h2_str}")
        print(f"  (>0 = debate beats compute-matched ensemble; <0 = ensemble >= debate)")
        print(f"\nH1a threshold (adaptive): {h1a_threshold:.4f}  {'(pre-registered)' if args.h1a_threshold else '(computed from observed baseline FC)'}")
        print(f"REGULAR BENCHMARK: {'PASSES' if benchmark_passes else 'FAILS'}")

    if mixed_results and etd_analysis:
        print()
        print("=" * 80)
        print("ETD ANALYSIS (mixed cases)")
        print("=" * 80)
        print(f"  N mixed cases: {n_mixed}  |  Pass criterion: ETD >= 0.5")
        print(f"  Mixed pass rate (isolated, ≥2/3 runs): {etd_analysis['mixed_pass_count']}/{n_mixed} ({etd_analysis['mixed_pass_fraction']:.1%})")
        print()
        for cond in ETD_CONDITIONS:
            ea = etd_analysis.get(cond, {})
            mean_etd = ea.get('mean_etd')
            full = ea.get('full_credit_rate')
            partial = ea.get('partial_credit_rate')
            zero = ea.get('zero_rate')
            n_obs = ea.get('n_observations', 0)
            print(f"  {cond:<24} n={n_obs}  mean={mean_etd or 'N/A':>5}  "
                  f"full={full or 0:.0%}  partial={partial or 0:.0%}  zero={zero or 0:.0%}")

    if mixed_results and h1b_fvc_mixed:
        print()
        print("H1b / H2 FVC ANALYSIS (mixed cases — HYPOTHESIS.md H1b, H2)")
        iso_fvc = h1b_fvc_mixed.get('mean_fvc_isolated_debate')
        base_fvc = h1b_fvc_mixed.get('mean_fvc_baseline')
        ens_fvc_print = h1b_fvc_mixed.get('mean_fvc_ensemble_3x')
        h1b_lift = h1b_fvc_mixed.get('fvc_lift_isolated_vs_baseline')
        h2_fvc_diff = h1b_fvc_mixed.get('fvc_diff_isolated_vs_ensemble')
        print(f"  isolated_debate FVC: {iso_fvc}")
        print(f"  baseline FVC:        {base_fvc}")
        print(f"  ensemble_3x FVC:     {ens_fvc_print}  (majority-vote verdict)")
        print(f"  H1b FVC lift (iso vs base):     {h1b_lift:+.4f}" if h1b_lift is not None else "  H1b FVC lift: N/A")
        print(f"  H2  FVC diff (iso vs ensemble): {h2_fvc_diff:+.4f}" if h2_fvc_diff is not None else "  H2  FVC diff: N/A")
        print("  (Bootstrap CI for PASS/FAIL computed separately)")

    if n_regular and any(v is not None for v in idp_adj_means.values()):
        print()
        print("IDP_adj ANALYSIS (regular cases — post-adjudication precision)")
        print("  IDP_raw = precision from all_issues_raised (Critic raw output)")
        print("  IDP_adj = precision from all_issues_adjudicated (post-Defender exchange)")
        for cond in CONDITIONS:
            raw_idp = idp_adj_means.get(cond)
            adj_str = f"{raw_idp:.4f}" if raw_idp is not None else "N/A (field absent)"
            print(f"  {cond:<24} IDP_adj mean: {adj_str}")

    if n_regular and any(v is not None for v in idr_novel_means.values()):
        print()
        print("IDR_novel ANALYSIS (regular cases — novel concerns beyond RC report)")
        print("  IDR_documented = recall against flaws documented in RC report (primary)")
        print("  IDR_novel      = novel valid concerns debate raised that reproducer missed (secondary)")
        for cond in CONDITIONS:
            val = idr_novel_means.get(cond)
            val_str = f"{val:.4f}" if val is not None else "N/A (rescore absent)"
            print(f"  {cond:<24} IDR_novel mean: {val_str}")


if __name__ == '__main__':
    main()
