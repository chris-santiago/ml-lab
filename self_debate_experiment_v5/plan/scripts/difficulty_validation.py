# difficulty_validation.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
#   "scipy>=1.11",
# ]
# ///
import json, numpy as np
from scipy import stats as scipy_stats

with open('v5_results.json') as f:
    d = json.load(f)
results = d['cases']

diff_map = {'easy': 0, 'medium': 1, 'hard': 2}
non_dw = [r for r in results if r['correct_position'] != 'defense']
diffs = [diff_map[r['difficulty']] for r in non_dw]
baselines = [r['baseline']['mean'] for r in non_dw]
rho, pval = scipy_stats.spearmanr(diffs, baselines)

output = {
    'non_defense_wins_n': len(non_dw),
    'spearman_rho': float(rho), 'p_value': float(pval),
    'interpretation': 'Negative rho = harder labels -> lower baseline scores (correct direction)',
    'means_by_difficulty': {
        diff: round(float(np.mean([r['baseline']['mean'] for r in non_dw if r['difficulty'] == diff])), 4)
        for diff in ['easy', 'medium', 'hard'] if any(r['difficulty'] == diff for r in non_dw)
    },
    'note': 'v5 difficulty defined by rubric performance, not findability. Rho should be negative and significant.'
}
with open('difficulty_validation_results.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f"Difficulty validation: rho={rho:.3f}, p={pval:.4f}")
if rho > -0.1 or pval > 0.1:
    print("WARNING: Difficulty labels may not predict rubric performance. Review case design.")
