# cross_model_scorer.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "anthropic>=0.39",
# ]
# ///
# Cross-vendor IDR validation using an external model family.
# Requires CROSS_VENDOR_API_KEY, CROSS_VENDOR_BASE_URL, CROSS_VENDOR_MODEL env vars.
# All other calls in this plan use session auth — this is the ONLY exception.
# The external model must be from a different company than Anthropic.

import anthropic, json, os

EXTERNAL_API_KEY = os.environ["CROSS_VENDOR_API_KEY"]
EXTERNAL_BASE_URL = os.environ["CROSS_VENDOR_BASE_URL"]
EXTERNAL_MODEL = os.environ["CROSS_VENDOR_MODEL"]

external_client = anthropic.Anthropic(
    api_key=EXTERNAL_API_KEY,
    base_url=EXTERNAL_BASE_URL,
)

with open('benchmark_cases_verified.json') as f:
    cases = json.load(f)
with open('v3_results.json') as f:
    v3 = json.load(f)

isolated_debate_idr_by_case = {
    r['case_id']: round(sum(
        run['scores']['IDR'] for run in r['isolated_debate']['runs']
        if run['scores'].get('IDR') is not None
    ) / max(1, sum(1 for run in r['isolated_debate']['runs'] if run['scores'].get('IDR') is not None)), 4)
    for r in v3['cases']
}

results = []
for case in cases:
    if case['ground_truth']['correct_position'] == 'defense':
        continue
    must_find = case['scoring_targets']['must_find_issue_ids']
    if not must_find:
        continue

    prompt = f"""You are independently evaluating an ML scenario. Determine which listed methodological issues are identifiable from the scenario description.

SCENARIO:
{case['task_prompt']}

ISSUES TO IDENTIFY:
{json.dumps(must_find, indent=2)}

For each issue ID: is this present and identifiable by a competent ML practitioner reading only the scenario above?

Respond ONLY with a JSON object: {{"issue_id": true/false, ...}}
No preamble, no explanation, no markdown fences."""

    try:
        response = external_client.messages.create(
            model=EXTERNAL_MODEL, max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        # Find the first TextBlock — some models (e.g. MiniMax-M2.7) return a
        # ThinkingBlock before the text response
        text_block = next((b for b in response.content if hasattr(b, 'text')), None)
        if text_block is None:
            raise ValueError(f"No text block in response; content types: {[type(b).__name__ for b in response.content]}")
        raw = text_block.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        found = json.loads(raw)
        idr = round(sum(1 for v in found.values() if v) / len(must_find), 4)
        error = None
    except Exception as e:
        found = None; idr = None; error = str(e)

    isolated_idr = isolated_debate_idr_by_case.get(case['case_id'])
    results.append({
        'case_id': case['case_id'], 'category': case['category'],
        'difficulty': case['difficulty'],
        'external_IDR': idr, 'isolated_debate_IDR': isolated_idr,
        'model': EXTERNAL_MODEL, 'error': error
    })
    print(f"{case['case_id']}: external={idr} isolated_debate={isolated_idr}" + (f" ERR:{error}" if error else ""))

with open('cross_vendor_scores_v3.json', 'w') as f:
    json.dump(results, f, indent=2)

valid = [r for r in results if r['external_IDR'] is not None and r['isolated_debate_IDR'] is not None]
if valid:
    ext_idr = sum(r['external_IDR'] for r in valid) / len(valid)
    iso_idr = sum(r['isolated_debate_IDR'] for r in valid) / len(valid)
    delta = abs(ext_idr - iso_idr)
    print(f"\nExternal ({EXTERNAL_MODEL}) IDR: {ext_idr:.3f}")
    print(f"Isolated debate IDR: {iso_idr:.3f}")
    print(f"Delta: {delta:.3f} — {'MATERIAL (>0.1): same-company bias may be a factor' if delta > 0.1 else 'not material'}")
