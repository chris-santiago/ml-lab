# filter_verified_cases.py
# /// script
# requires-python = ">=3.10"
# ///
import json

with open('benchmark_cases.json') as f:
    cases = json.load(f)
with open('benchmark_verification.json') as f:
    verifications = json.load(f)

ver = {v['case_id']: v for v in verifications}
keep = [c for c in cases if ver.get(c['case_id'], {}).get('decision') == 'keep']

mixed = sum(1 for c in keep if c['ground_truth']['correct_position'] == 'mixed')
dw = sum(1 for c in keep if c['ground_truth']['correct_position'] == 'defense')

print(f'Keep: {len(keep)} | Mixed: {mixed} | Defense_wins: {dw}')

if len(keep) < 40:
    print(f'\nERROR: Only {len(keep)} cases passed verification (need >= 40).')
    raise SystemExit('Insufficient cases — operator must re-run external LLM generation before proceeding')

if mixed < 10:
    print(f'\nERROR: Only {mixed} mixed-position cases passed (need >= 10).')
    raise SystemExit('Insufficient mixed-position cases')

if dw < 8:
    print(f'\nERROR: Only {dw} defense_wins cases passed (need >= 8).')
    raise SystemExit('Insufficient defense_wins cases')

with open('benchmark_cases_verified.json', 'w') as f:
    json.dump(keep, f, indent=2)
print(f'benchmark_cases_verified.json written: {len(keep)} cases')
