# within_case_variance.py
# /// script
# requires-python = ">=3.10"
# ///
"""Within-case variance analysis for v4 benchmark."""
import json
with open('v4_results.json') as f:
    d = json.load(f)
output = {'experiment': 'within_case_variance_v4', 'n_runs_per_case': 3, 'cases': {}}
high_var = []
for r in d['cases']:
    cid = r['case_id']
    output['cases'][cid] = {
        cond: {'std': r[cond]['std'], 'mean': r[cond]['mean']}
        for cond in ['isolated_debate', 'multiround', 'ensemble', 'baseline']
        if r[cond]['std'] is not None
    }
    if r['isolated_debate']['std'] and r['isolated_debate']['std'] > 0.1:
        high_var.append({'case_id': cid, 'isolated_debate_std': r['isolated_debate']['std']})
output['high_variance_cases'] = high_var
output['summary'] = {cond: round(sum(r[cond]['std'] for r in d['cases'] if r[cond]['std'] is not None) /
                                  max(1, sum(1 for r in d['cases'] if r[cond]['std'] is not None)), 4)
                     for cond in ['isolated_debate', 'multiround', 'ensemble', 'baseline']}
import json as _j
with open('within_case_variance_results.json', 'w') as f:
    _j.dump(output, f, indent=2)
print('Within-case variance written. High variance cases:', len(high_var))
