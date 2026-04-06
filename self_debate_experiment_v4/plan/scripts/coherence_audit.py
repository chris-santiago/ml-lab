# coherence_audit.py
# /// script
# requires-python = ">=3.10"
# ///
import json, re, sys

errors = []

with open('sensitivity_analysis_results.json') as f:
    sens = json.load(f)
with open('stats_results.json') as f:
    stats = json.load(f)
with open('v4_results.json') as f:
    v4 = json.load(f)

fc_lift = sens['fair_comparison']['lift_isolated_vs_baseline']
iso_mean = stats['bootstrap_cis']['isolated_debate_mean']['point']
baseline_mean = stats['bootstrap_cis']['baseline_mean']['point']

with open('CONCLUSIONS.md') as f:
    conclusions = f.read()
with open('SENSITIVITY_ANALYSIS.md') as f:
    sensitivity = f.read()

def extract_floats(text, pattern):
    return [float(m) for m in re.findall(pattern, text)]

# Check isolated mean in CONCLUSIONS
iso_mentions = extract_floats(conclusions, r'isolated.*?(\d+\.\d{3,4})')
if iso_mentions:
    mismatch = [v for v in iso_mentions if abs(v - iso_mean) > 0.005]
    if mismatch:
        errors.append(f'CONCLUSIONS.md isolated_debate mean mismatch: found {mismatch}, expected ~{iso_mean}')

# Check fair-comparison lift in SENSITIVITY_ANALYSIS
if fc_lift is not None:
    fc_mentions = extract_floats(sensitivity, r'fair.*?comparison.*?([+-]?\d+\.\d{3,4})')
    if fc_mentions:
        mismatch = [v for v in fc_mentions if abs(abs(v) - abs(fc_lift)) > 0.01]
        if mismatch:
            errors.append(f'SENSITIVITY_ANALYSIS.md fair-comparison lift mismatch: found {mismatch}, expected ~{fc_lift}')

# Check pass count
v4_pass_count = v4['debate_pass_count']
conclusions_pass = extract_floats(conclusions, r'(\d+)/\d+.*?pass')
if conclusions_pass and int(conclusions_pass[0]) != v4_pass_count:
    errors.append(f'Pass count mismatch: CONCLUSIONS says {int(conclusions_pass[0])}, v4_results says {v4_pass_count}')

# Check that CONCLUSIONS leads with fair-comparison lift (not raw lift)
first_500 = conclusions[:500].lower()
if 'raw lift' in first_500 and 'fair' not in first_500:
    errors.append('CONCLUSIONS.md appears to lead with raw lift rather than fair-comparison lift — violates reporting norms')

# Check forced_multiround hollow-round exclusion consistency
# - forced_multiround hollow-round exclusion is applied consistently: primary results must state hollow_rate and case count; secondary table must be present if any hollow cases exist
with open('ENSEMBLE_ANALYSIS.md') as f:
    ensemble = f.read()
ensemble_lower = ensemble.lower()
if 'forced_multiround' in ensemble_lower or 'forced multiround' in ensemble_lower:
    if 'hollow' not in ensemble_lower:
        errors.append('ENSEMBLE_ANALYSIS.md contains forced_multiround results but missing hollow-round section — hollow-round exclusion must be documented')
    if 'hollow_rate' not in ensemble_lower and 'hollow rate' not in ensemble_lower:
        errors.append('ENSEMBLE_ANALYSIS.md: primary forced_multiround results must state hollow_rate and case count')
    if re.search(r'hollow.*?(?:case|round)', ensemble_lower) and 'secondary' not in ensemble_lower:
        errors.append('ENSEMBLE_ANALYSIS.md: secondary table (including hollow-round cases) must be present if any hollow cases exist')

if errors:
    print('COHERENCE AUDIT FAILED:')
    for e in errors:
        print(f'  {e}')
    print('\nFix before drafting REPORT.md.')
    sys.exit(1)
else:
    print('Pre-report coherence audit passed.')
