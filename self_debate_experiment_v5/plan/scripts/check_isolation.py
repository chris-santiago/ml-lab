# check_isolation.py
# /// script
# requires-python = ">=3.10"
# ///
# Scans isolated_debate and forced_multiround defender outputs for isolation breaches.
# Note: multiround NOT checked — Defender intentionally sees Critique there.
import json, re
from pathlib import Path

raw_dir = Path('v5_raw_outputs')
breaches = []

patterns_to_check = list(raw_dir.glob('*_isolated_debate_run*.json')) + \
                    list(raw_dir.glob('*_forced_multiround_run*.json'))

for path in sorted(patterns_to_check):
    with open(path) as f:
        run = json.load(f)
    # forced_multiround is adversarial (Defender sees Critique) — only check isolated_debate
    if run.get('condition') == 'forced_multiround':
        continue
    defender_raw = run.get('defender_raw', '')
    critic_raw = run.get('critic_raw', '')
    critic_claims = re.findall(r'(?:Issue \d+|^\d+\.)[^\n]+', critic_raw, re.MULTILINE)
    for claim in critic_claims[:3]:
        snippet = claim.strip()[:60]
        if len(snippet) > 20 and snippet.lower() in defender_raw.lower():
            breaches.append({
                'file': str(path),
                'case_id': run['case_id'],
                'run': run['run'],
                'matched_snippet': snippet
            })
            break

if breaches:
    print(f'ISOLATION BREACHES DETECTED: {len(breaches)}')
    for b in breaches:
        print(f'  {b["file"]}: matched "{b["matched_snippet"]}"')
    raise SystemExit('Fix isolation breaches before scoring — results are contaminated')
else:
    n = len(list(raw_dir.glob('*_isolated_debate_run*.json')))
    print(f'Isolation check passed — {n} isolated debate runs clean')
