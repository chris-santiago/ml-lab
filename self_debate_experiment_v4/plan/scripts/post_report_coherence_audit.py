# post_report_coherence_audit.py
# /// script
# requires-python = ">=3.10"
# ///
import json, re, sys
from pathlib import Path

errors = []
warnings = []

# Check 1: Claim consistency across CONCLUSIONS, REPORT, ENSEMBLE_ANALYSIS
docs = {}
for fname in ['CONCLUSIONS.md', 'REPORT.md', 'ENSEMBLE_ANALYSIS.md']:
    p = Path(fname)
    if p.exists():
        docs[fname] = p.read_text()
    else:
        errors.append(f'Missing required document: {fname}')

if len(docs) == 3:
    def extract_lifts(text):
        return [float(m) for m in re.findall(r'(?:lift|improvement).*?([+-]?\d+\.\d{3,4})', text, re.IGNORECASE)]
    lifts_c = extract_lifts(docs.get('CONCLUSIONS.md', ''))
    lifts_r = extract_lifts(docs.get('REPORT.md', ''))
    if lifts_c and lifts_r:
        if abs(max(abs(x) for x in lifts_c) - max(abs(x) for x in lifts_r)) > 0.01:
            errors.append('Headline lift inconsistency between CONCLUSIONS.md and REPORT.md')

# Check 2: README currency
readme = Path('README.md')
if readme.exists():
    rt = readme.read_text()
    if 'v4' not in rt.lower():
        warnings.append('README.md does not mention v4 experiment')
    if 'CONCLUSIONS' not in rt and 'REPORT' not in rt:
        warnings.append('README.md does not reference CONCLUSIONS.md or REPORT.md')
else:
    errors.append('README.md missing')

# Check 3: Peer review resolution
for pr_file in ['PEER_REVIEW_R1.md', 'PEER_REVIEW.md']:
    pr = Path(pr_file)
    if pr.exists():
        pr_text = pr.read_text()
        if '## Response' not in pr_text:
            errors.append(f'{pr_file}: missing ## Response section')
        unresolved = re.findall(r'(?:MAJOR|major issue).*?(?:unresolved|not addressed|still open)', pr_text, re.IGNORECASE)
        if unresolved:
            errors.append(f'{pr_file}: {len(unresolved)} potentially unresolved MAJOR issues')
        break

# Check 4: Hypothesis closure
for fname in ['CONCLUSIONS.md', 'REPORT.md', 'FINAL_SYNTHESIS.md']:
    doc = Path(fname)
    if not doc.exists():
        errors.append(f'{fname} missing — cannot verify hypothesis closure')
        continue
    text = doc.read_text()
    if not any(kw in text.lower() for kw in ['hypothesis', 'verdict', 'supported', 'rejected', 'confirmed']):
        errors.append(f'{fname}: no hypothesis verdict found')

# Check 5: Reporting norms compliance
report_text = docs.get('REPORT.md', '')
if report_text:
    first_line = report_text.strip().split('\n')[0].lower()
    if any(kw in first_line for kw in ['results mode', 'mode:', 'framing:', 'findings stated']):
        errors.append('REPORT.md starts with a mode declaration — violates reporting norms (Issue 17)')

# Check 6: Quantitative cross-check
with open('stats_results.json') as f:
    stats = json.load(f)
with open('v4_results.json') as f:
    v4 = json.load(f)

if report_text:
    iso_mean = stats['bootstrap_cis']['isolated_debate_mean']['point']
    iso_mentions = [float(m) for m in re.findall(r'isolated.*?(\d+\.\d{3,4})', report_text)]
    bad_iso = [v for v in iso_mentions if abs(v - iso_mean) > 0.005]
    if bad_iso:
        errors.append(f'REPORT.md: isolated_debate mean mismatch — found {bad_iso}, authoritative={iso_mean:.4f}')
    pass_count = v4.get('debate_pass_count', 0)
    pass_mentions = re.findall(r'(\d+)/\d+.*?pass', report_text)
    if pass_mentions and int(pass_mentions[0]) != pass_count:
        errors.append(f'REPORT.md: pass count mismatch')

if errors:
    print('POST-REPORT COHERENCE AUDIT FAILED:')
    for e in errors:
        print(f'  ERROR: {e}')
    if warnings:
        for w in warnings:
            print(f'  WARN: {w}')
    sys.exit(1)
else:
    print('Post-report coherence audit passed.')
    for w in warnings:
        print(f'  WARN: {w}')
