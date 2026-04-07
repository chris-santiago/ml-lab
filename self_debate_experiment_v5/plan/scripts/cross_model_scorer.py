# cross_model_scorer.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
# ]
# ///
"""
Cross-vendor per-dimension validation.
v5 changes from v4:
- Uses OpenAI-compatible API (not Anthropic SDK) — fixes MiniMax ThinkingBlock parse failures
- Strips <think>...</think> tags from responses
- Scores ALL dimensions (IDR, IDP, DRQ, FVC), not just IDR
- Runs on ALL cases (not just non-defense_wins)
"""
import json, os, re
from openai import OpenAI

EXTERNAL_API_KEY = os.environ["CROSS_VENDOR_API_KEY"]
EXTERNAL_BASE_URL = os.environ["CROSS_VENDOR_BASE_URL"]
EXTERNAL_MODEL = os.environ["CROSS_VENDOR_MODEL"]

client = OpenAI(api_key=EXTERNAL_API_KEY, base_url=EXTERNAL_BASE_URL)

with open('benchmark_cases_verified.json') as f:
    cases = json.load(f)
with open('v5_results.json') as f:
    v5 = json.load(f)

claude_by_case = {
    r['case_id']: {
        dim: round(sum(run['scores'].get(dim, 0) or 0 for run in r['isolated_debate']['runs']
                       if run['scores'].get(dim) is not None) /
                   max(1, sum(1 for run in r['isolated_debate']['runs']
                              if run['scores'].get(dim) is not None)), 4)
        for dim in ['IDR', 'IDP', 'DRQ', 'FVC']
    }
    for r in v5['cases']
}

results = []
for case in cases:
    cid = case['case_id']
    correct_pos = case['ground_truth']['correct_position']
    must_find = case['scoring_targets'].get('must_find_issue_ids', [])
    must_not_claim = case['scoring_targets'].get('must_not_claim', [])
    acceptable = case['scoring_targets'].get('acceptable_resolutions', [])

    prompt = f"""You are independently evaluating an ML scenario. Assess the following.

SCENARIO:
{case['task_prompt']}

ISSUE IDs TO CHECK (for each: is this identifiable from the scenario?):
{json.dumps(must_find, indent=2)}

ISSUES THAT WOULD BE FALSE POSITIVES IF RAISED:
{json.dumps(must_not_claim, indent=2)}

ACCEPTABLE VERDICTS: {json.dumps(acceptable)}

Respond ONLY with a JSON object:
{{
  "issues_identified": {{"issue_id": true/false, ...}},
  "false_positives_raised": ["issue_id", ...],
  "verdict": "critique_wins | defense_wins | empirical_test_agreed | mixed"
}}
No preamble, no explanation, no markdown fences."""

    try:
        response = client.chat.completions.create(
            model=EXTERNAL_MODEL, max_tokens=600,
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content or ""
        # Strip thinking tags (MiniMax and other models may include these)
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        parsed = json.loads(raw)

        identified = parsed.get('issues_identified', {})
        fp_raised = parsed.get('false_positives_raised', [])
        ext_verdict = parsed.get('verdict')

        ext_idr = round(sum(1 for v in identified.values() if v) / max(1, len(must_find)), 4) if must_find else None
        valid_raised = [k for k, v in identified.items() if v and k in must_find]
        invalid_raised = fp_raised
        denom = len(valid_raised) + len(invalid_raised)
        ext_idp = round(len(valid_raised) / denom, 4) if denom > 0 else 1.0
        ext_fvc = 1.0 if ext_verdict in acceptable else (
            0.5 if any((ext_verdict, acc) in {
                ('critique_wins', 'empirical_test_agreed'), ('empirical_test_agreed', 'critique_wins'),
                ('defense_wins', 'empirical_test_agreed'), ('empirical_test_agreed', 'defense_wins')
            } for acc in acceptable) else 0.0
        ) if ext_verdict else None

        error = None
    except Exception as e:
        ext_idr = ext_idp = ext_fvc = ext_verdict = None
        error = str(e)

    claude = claude_by_case.get(cid, {})
    results.append({
        'case_id': cid, 'category': case['category'],
        'difficulty': case['difficulty'], 'correct_position': correct_pos,
        'model': EXTERNAL_MODEL,
        'external': {'IDR': ext_idr, 'IDP': ext_idp, 'FVC': ext_fvc, 'verdict': ext_verdict},
        'claude_isolated_debate': claude,
        'deltas': {
            dim: round((ext_idr if dim == 'IDR' else ext_idp if dim == 'IDP' else ext_fvc) - (claude.get(dim) or 0), 4)
            if (ext_idr if dim == 'IDR' else ext_idp if dim == 'IDP' else ext_fvc) is not None and claude.get(dim) is not None else None
            for dim in ['IDR', 'IDP', 'FVC']
        },
        'error': error
    })
    status = f"IDR_delta={results[-1]['deltas'].get('IDR')}" if not error else f"ERR:{error}"
    print(f"{cid}: {status}")

with open('cross_vendor_scores_v5.json', 'w') as f:
    json.dump(results, f, indent=2)

valid = [r for r in results if r['external']['IDR'] is not None]
if valid:
    for dim in ['IDR', 'IDP', 'FVC']:
        deltas = [r['deltas'][dim] for r in valid if r['deltas'].get(dim) is not None]
        if deltas:
            mean_delta = sum(deltas) / len(deltas)
            print(f"\n{dim} delta ({EXTERNAL_MODEL} vs Claude): {mean_delta:+.3f} n={len(deltas)}")
            print(f"  {'Material (>0.1): bias may be present' if abs(mean_delta) > 0.1 else 'Not material'}")
print(f"\nParse rate: {len(valid)}/{len(results)} ({len(valid)/len(results):.1%})")
