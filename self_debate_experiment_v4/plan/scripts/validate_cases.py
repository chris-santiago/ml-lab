# validate_cases.py
# /// script
# requires-python = ">=3.10"
# ///
import json, sys
from collections import Counter

input_file = sys.argv[1] if len(sys.argv) > 1 else 'benchmark_cases.json'
with open(input_file) as f:
    cases = json.load(f)

print(f'Total cases: {len(cases)}')
cats = Counter(c['category'] for c in cases)
print('By category:', dict(cats))

positions = Counter(c['ground_truth']['correct_position'] for c in cases)
print('By correct_position:', dict(positions))
mixed = sum(1 for c in cases if c['ground_truth']['correct_position'] == 'mixed')
print(f'Mixed-position: {mixed} (target >= 12)')

mf_sizes = Counter(len(c['scoring_targets']['must_find_issue_ids']) for c in cases)
print('Must-find sizes:', dict(mf_sizes))
large_mf = sum(1 for c in cases if len(c['scoring_targets']['must_find_issue_ids']) >= 3)
print(f'Cases with 3+ must_find: {large_mf} (target >= 20)')

has_mnc = sum(1 for c in cases if c['scoring_targets'].get('must_not_claim'))
print(f'Cases with must_not_claim: {has_mnc} (target >= 20)')

multi_accept = sum(1 for c in cases if len(c['scoring_targets'].get('acceptable_resolutions', [])) > 1)
print(f'Cases with multiple acceptable_resolutions: {multi_accept} (target >= 10)')

diff = Counter(c['difficulty'] for c in cases)
print('By difficulty:', dict(diff))

required = ['case_id', 'category', 'difficulty', 'task_prompt', 'ground_truth',
            'planted_issues', 'ideal_critique', 'ideal_defense',
            'ideal_debate_resolution', 'scoring_targets', 'verifier_status', 'notes']
for case in cases:
    missing = [f for f in required if f not in case]
    if missing:
        print(f"WARNING {case['case_id']}: missing {missing}")
    gt = case.get('ground_truth', {})
    if not gt.get('final_verdict'):
        print(f"WARNING {case['case_id']}: missing or empty ground_truth.final_verdict")
    idr = case.get('ideal_debate_resolution', {})
    if idr.get('type') == 'empirical_test_agreed' and not gt.get('required_empirical_test'):
        print(f"WARNING {case['case_id']}: empirical_test_agreed case missing ground_truth.required_empirical_test")

non_dw = [c for c in cases if c['ground_truth']['correct_position'] != 'defense']
has_red_herring = sum(1 for c in non_dw if c['scoring_targets'].get('must_not_claim'))
print(f'Non-defense_wins cases with must_not_claim: {has_red_herring}/{len(non_dw)} (target: all)')

hard_cases = [c for c in cases if c['difficulty'] == 'hard' and c['ground_truth']['correct_position'] != 'defense']
domain_expert_hard = sum(1 for c in hard_cases
                         if any(kw in (c.get('notes', '') + ' '.join(c.get('ideal_critique', []))).lower()
                                for kw in ['domain expertise', 'domain knowledge', 'clinical', 'epv', 'regulatory',
                                          'financial audit', 'inter-annotator', 'iaa', 'offline-online']))
print(f'Hard critique cases with domain expertise signals: {domain_expert_hard}/{len(hard_cases)} (target >= 8)')
if domain_expert_hard < 8:
    print('  WARNING: May not have enough domain-expertise hard cases')

# v4: check for hard/mixed/empirical_test_agreed cases (needed for forced_multiround)
hard_mixed_eta = sum(1 for c in cases
                     if c['difficulty'] == 'hard'
                     and c['ground_truth']['correct_position'] == 'mixed'
                     and c.get('ideal_debate_resolution', {}).get('type') == 'empirical_test_agreed')
print(f'Hard mixed empirical_test_agreed cases: {hard_mixed_eta} (target >= 8 per case gen prompt)')

assert len(cases) >= 50, 'Need at least 50 cases'
assert mixed >= 12, 'Need at least 12 mixed-position cases'
assert large_mf >= 20, 'Need at least 20 cases with 3+ must_find items'
print('\nValidation passed.')
