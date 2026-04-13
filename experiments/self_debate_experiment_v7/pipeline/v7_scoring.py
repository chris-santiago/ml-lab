# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "tqdm"]
# ///
"""
v7_scoring.py — Cross-Model Semantic Scoring + Analysis Engine

Three modes:
  --mode pilot    Phase 3: Lightweight pilot scoring (FVC + DRQ only, no API calls)
  --mode score    Phase 6: Cross-vendor scoring via gpt-5.4-mini (OpenRouter)
  --mode analyze  Phase 7: Bootstrap hypothesis tests (P1, P2, H1a-H5)

Phase 3 (pilot mode):
  Reads raw baseline outputs and ground-truth cases, computes FVC and DRQ locally
  (no cross-vendor API calls). FC = mean(DRQ, FVC) — conservative upper bound on
  full 4-dimension FC. Outputs a list of per-output results for difficulty gating.

Phase 6 (score mode):
  Produces v7_rescored_idr_idp.json with per-file score vectors.
  Scope:
    - IDR (idr_documented, idr_novel): regular cases only (correct_position == 'critique_wins')
    - IDP (idp_raw, idp_adj): regular cases only
    - Defense + mixed cases: nulls written; no API call needed for IDR/IDP

Phase 7 (analyze mode):
  Consumes v7_rescored_idr_idp.json + v7_raw_outputs + benchmark_cases_v7_raw.json
  Produces v7_results.json with all 8 hypothesis tests.

Output schema for score mode (keyed by filename):
  {filename: {idr_documented, idr_novel, idp_raw, idp_adj, found_booleans}}

Usage:
  uv run pipeline/v7_scoring.py --mode pilot --input pilot_raw_outputs \\
    --cases benchmark_cases_v7_raw.json --output pilot_results.json
  uv run pipeline/v7_scoring.py --mode score [--dry-run] [--concurrency 20]
  uv run pipeline/v7_scoring.py --mode analyze --raw v7_raw_outputs \\
    --scores v7_rescored_idr_idp.json --cases benchmark_cases_v7_raw.json \\
    --output v7_results.json --bootstrap-n 10000 --seed 42
"""

import argparse
import asyncio
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: openai package required. Run: uv run pipeline/v7_scoring.py")
    sys.exit(1)

parser = argparse.ArgumentParser(description="v7 scoring + analysis engine")
parser.add_argument("--mode", choices=["pilot", "score", "analyze"], default=None,
                    help="Operating mode (inferred as 'pilot' when --input is provided)")
# Score mode args
parser.add_argument("--dry-run", action="store_true", help="Skip API calls, produce null scores")
parser.add_argument("--concurrency", type=int, default=20)
parser.add_argument("--model", default="openai/gpt-5.4-mini",
                    help="OpenRouter model for cross-vendor scoring (default: openai/gpt-5.4-mini)")
parser.add_argument("--cases", default="benchmark_cases_v7_raw.json")
parser.add_argument("--score-output", default="v7_rescored_idr_idp.json")
parser.add_argument("--resume", action="store_true", help="Skip files already in output")
# Pilot mode args
parser.add_argument("--input", help="Input directory of raw benchmark outputs (pilot mode)")
# Analyze mode args
parser.add_argument("--raw", default="v7_raw_outputs", help="Directory of raw benchmark outputs")
parser.add_argument("--scores", default="v7_rescored_idr_idp.json", help="Rescored IDR/IDP file")
parser.add_argument("--output", default="v7_results.json", help="Analysis results output")
parser.add_argument("--hypothesis-file", default="HYPOTHESIS.md")
parser.add_argument("--bootstrap-n", type=int, default=10000)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

# Infer mode from arguments when not explicitly provided
if args.mode is None:
    if args.input:
        args.mode = "pilot"
    else:
        parser.error("--mode is required (or provide --input for pilot mode)")

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / args.raw
CASES_FILE = BASE_DIR / args.cases

CONDITIONS = ["baseline", "isolated_debate", "ensemble_3x", "multiround_2r"]

# v7 scoring dimensions — ETD removed (v6 lesson L2: structural ceiling, no signal)
FAIR_COMPARISON_DIMS = ["IDR", "IDP", "DRQ", "FVC"]

# Adjacency set for partial-credit scoring
_ADJACENTS = {
    ("critique_wins", "empirical_test_agreed"),
    ("empirical_test_agreed", "critique_wins"),
    ("defense_wins", "empirical_test_agreed"),
    ("empirical_test_agreed", "defense_wins"),
}


# ===========================================================================
# Phase 6 — Cross-vendor scoring (score mode)
# ===========================================================================

def load_case_index(cases_file):
    """Load case metadata into a lookup dict keyed by case_id."""
    cases = json.load(open(cases_file))
    idx = {}
    for c in cases:
        cid = c["case_id"]
        idx[cid] = {
            "correct_position": c["ground_truth"]["correct_position"],
            "category": c.get("category", "regular"),
            "must_find_ids": c["scoring_targets"].get("must_find_issue_ids", []),
            "must_not_claim_details": c["scoring_targets"].get("must_not_claim_details", []),
            "planted_issues": {
                pi["issue_id"]: pi["description"]
                for pi in c.get("planted_issues", [])
            },
        }
    return idx


def build_idr_idp_prompt(critic_raw, all_issues_raised, all_issues_adjudicated,
                          planted_descriptions, must_not_claim_details):
    """Build a single prompt that scores both IDR and IDP in one call."""
    issues_block = "\n".join(
        f"  [{iid}] {desc}"
        for iid, desc in planted_descriptions.items()
    )
    false_claims_block = "\n".join(
        f"  [{d['claim_id']}] CLAIM: {d['claim']}\n    WHY WRONG: {d['why_wrong']}"
        for d in must_not_claim_details
    ) if must_not_claim_details else "  (none)"

    raised_block = "\n".join(f"  - {issue}" for issue in all_issues_raised)
    adj_block = "\n".join(f"  - {issue}" for issue in (all_issues_adjudicated or all_issues_raised))

    return f"""You are evaluating a methodological critique of an ML research paper.

CRITIQUE TEXT:
{critic_raw}

---
TASK 1 — IDR (Issue Detection Rate):
For each PLANTED ISSUE below, determine if the critique semantically addresses it — meaning the critique raises a concern that substantially overlaps in meaning with the planted issue, even if not using the same words.

PLANTED ISSUES (must find):
{issues_block}

---
TASK 2 — IDP (Issue Detection Precision):
Review the issues listed below. For each FALSE CLAIM, determine if any raised issue substantially matches that false claim — meaning the critic raised an incorrect or misleading concern that maps to the false claim.

RAISED ISSUES (raw):
{raised_block}

RAISED ISSUES (adjudicated):
{adj_block}

FALSE CLAIMS (must not raise):
{false_claims_block}

---
OUTPUT: Respond with JSON only. No prose before or after.

{{
  "idr_found": {{
    "<issue_id>": true_or_false,
    ...
  }},
  "idp_raw_false_claim_ids": ["<claim_id_if_raised_in_raw>", ...],
  "idp_adj_false_claim_ids": ["<claim_id_if_raised_in_adjudicated>", ...],
  "idr_novel_count": <integer — count of issues in critique that are valid new concerns NOT in planted issues and NOT false claims>
}}"""


def compute_idp_from_false_claims(false_claim_ids, all_issues_count):
    """Convert false claim IDs to IDP score using the binned scale."""
    if all_issues_count == 0:
        return 1.0
    n_invalid = len(false_claim_ids)
    n_valid = all_issues_count - n_invalid
    frac = n_valid / all_issues_count
    if frac >= 0.9:
        return 1.0
    elif frac >= 0.5:
        return 0.5
    return 0.0


async def call_scorer(client, prompt, semaphore, model, filename=""):
    """Call cross-vendor scorer via OpenRouter with JSON extraction."""
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"\nWARN: JSON parse error for {filename}: {e}")
            return None
        except Exception as e:
            print(f"\nERROR calling scorer for {filename}: {e}")
            return None


async def score_file(client, output_path, case_meta, semaphore, model, dry_run):
    """Score a single output file. Returns (filename, score_dict)."""
    filename = output_path.name
    output_data = json.load(open(output_path))
    correct_position = case_meta.get("correct_position", "critique_wins")

    score = {
        "idr_documented": None,
        "idr_novel": None,
        "idp_raw": None,
        "idp_adj": None,
        "found_booleans": {},
    }

    # Defense or mixed: IDR/IDP are N/A — no planted flaws to match against
    if correct_position in ("defense_wins", "empirical_test_agreed"):
        return filename, score

    # Regular (critique) case: IDR + IDP via cross-vendor scorer
    must_find_ids = case_meta["must_find_ids"]
    planted_descriptions = {
        iid: case_meta["planted_issues"][iid]
        for iid in must_find_ids
        if iid in case_meta["planted_issues"]
    }
    must_not_claim_details = case_meta["must_not_claim_details"]

    if not must_find_ids:
        score["idr_documented"] = 1.0
        score["idr_novel"] = 0.0
        score["idp_raw"] = 1.0
        score["idp_adj"] = 1.0
        return filename, score

    # NOTE: For ensemble_3x, this scores only the top-level merged output.
    # Phase 6 step 6.4 must add per-assessor scoring for union IDR (H5).
    critic_raw = output_data.get("critic_raw", "")
    all_issues_raised = output_data.get("all_issues_raised", [])
    all_issues_adjudicated = output_data.get("all_issues_adjudicated", all_issues_raised)

    if dry_run:
        score["idr_documented"] = 0.75
        score["idr_novel"] = 0.0
        score["idp_raw"] = 1.0
        score["idp_adj"] = 1.0
        score["found_booleans"] = {iid: True for iid in must_find_ids}
        return filename, score

    prompt = build_idr_idp_prompt(
        critic_raw, all_issues_raised, all_issues_adjudicated,
        planted_descriptions, must_not_claim_details,
    )
    result = await call_scorer(client, prompt, semaphore, model, filename)

    if result:
        idr_found = result.get("idr_found", {})
        idp_raw_false = result.get("idp_raw_false_claim_ids", [])
        idp_adj_false = result.get("idp_adj_false_claim_ids", [])
        novel_count = result.get("idr_novel_count", 0)

        if must_find_ids:
            n_found = sum(1 for iid in must_find_ids if idr_found.get(iid, False))
            score["idr_documented"] = round(n_found / len(must_find_ids), 4)
            score["found_booleans"] = {
                iid: bool(idr_found.get(iid, False)) for iid in must_find_ids
            }
        else:
            score["idr_documented"] = 1.0
            score["found_booleans"] = {}

        denom = max(len(must_find_ids), 1)
        score["idr_novel"] = round(min(novel_count / denom, 1.0), 4)

        score["idp_raw"] = compute_idp_from_false_claims(
            idp_raw_false, len(all_issues_raised)
        )
        score["idp_adj"] = compute_idp_from_false_claims(
            idp_adj_false, len(all_issues_adjudicated or all_issues_raised)
        )
    else:
        score["idr_documented"] = 0.5
        score["idr_novel"] = 0.0
        score["idp_raw"] = 1.0
        score["idp_adj"] = 1.0
        score["found_booleans"] = {iid: False for iid in must_find_ids}

    return filename, score


async def run_scoring():
    """Phase 6: score all raw output files with cross-vendor model."""
    output_file = BASE_DIR / args.score_output

    print(f"Loading cases from {CASES_FILE}...")
    case_index = load_case_index(CASES_FILE)

    existing = {}
    if args.resume and output_file.exists():
        existing = json.load(open(output_file)).get("scores", {})
        print(f"Resuming: {len(existing)} files already scored")

    all_files = sorted(RAW_DIR.glob("*.json"))
    if not all_files:
        print(f"ERROR: No files found in {RAW_DIR}")
        sys.exit(1)

    to_score = [f for f in all_files if f.name not in existing]
    print(f"Files to score: {len(to_score)} / {len(all_files)} total")

    if args.dry_run:
        print("DRY RUN — no API calls will be made")

    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )

    semaphore = asyncio.Semaphore(args.concurrency)
    scores = dict(existing)

    tasks = []
    for f in to_score:
        output_data = json.load(open(f))
        cid = output_data.get("case_id", "")
        case_meta = case_index.get(cid, {
            "correct_position": "critique_wins",
            "must_find_ids": [],
            "planted_issues": {},
            "must_not_claim_details": [],
        })
        tasks.append(score_file(client, f, case_meta, semaphore, args.model, args.dry_run))

    print(f"\nRunning {len(tasks)} scoring tasks with concurrency={args.concurrency}...")

    batch_size = 100
    with tqdm(total=len(tasks), unit="file") as pbar:
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for r in results:
                if isinstance(r, BaseException):
                    print(f"\nERROR: {r}")
                elif r is not None:
                    fname, score = r[0], r[1]
                    scores[fname] = score
            pbar.update(len(batch))

            json.dump(
                {"scores": scores, "model": args.model, "total": len(scores)},
                open(output_file, "w"), indent=2,
            )

    print(f"\nDone. Scored {len(scores)} files.")
    idr_vals = [s["idr_documented"] for s in scores.values() if s["idr_documented"] is not None]
    idp_vals = [s["idp_raw"] for s in scores.values() if s["idp_raw"] is not None]
    print(f"IDR documented: n={len(idr_vals)}, mean={sum(idr_vals)/len(idr_vals):.3f}" if idr_vals else "IDR: none")
    print(f"IDP raw:        n={len(idp_vals)}, mean={sum(idp_vals)/len(idp_vals):.3f}" if idp_vals else "IDP: none")

    json.dump(
        {"scores": scores, "model": args.model, "total": len(scores)},
        open(output_file, "w"), indent=2,
    )
    print(f"Saved to {output_file}")


# ===========================================================================
# Phase 7 — Analysis engine (analyze mode)
# ===========================================================================

# Scoring functions (from v6 self_debate_poc.py, adapted for v7)

def compute_idr(must_find_ids, found_booleans):
    """IDR from cross-vendor found_booleans dict."""
    if not must_find_ids:
        return None
    n_found = sum(1 for iid in must_find_ids if found_booleans.get(iid, False))
    return round(n_found / len(must_find_ids), 4)


def compute_fvc(verdict, acceptable_resolutions, ideal_resolution):
    """Final Verdict Correctness."""
    if verdict in acceptable_resolutions:
        return 1.0
    if (verdict, ideal_resolution) in _ADJACENTS:
        return 0.5
    return 0.0


def compute_drq(verdict, acceptable_resolutions, ideal_resolution):
    """Decision Resolution Quality."""
    if verdict == ideal_resolution:
        return 1.0
    elif verdict in acceptable_resolutions:
        return 0.5
    elif (verdict, ideal_resolution) in _ADJACENTS:
        return 0.5
    return 0.0


def compute_fc(scores_dict):
    """FC composite = mean of non-null fair-comparison dimensions (IDR, IDP, DRQ, FVC)."""
    vals = [scores_dict[d] for d in FAIR_COMPARISON_DIMS if scores_dict.get(d) is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def compute_ensemble_union_idr(assessor_results_list, must_find_ids, rescored_list):
    """Union IDR for ensemble_3x: found if ANY assessor found it."""
    if not must_find_ids:
        return None
    union_found = set()
    for i in range(len(assessor_results_list)):
        rescored = rescored_list[i] if i < len(rescored_list) else None
        if rescored and "found_booleans" in rescored:
            fb = rescored["found_booleans"]
            union_found.update(iid for iid in must_find_ids if fb.get(iid, False))
    return round(len(union_found) / len(must_find_ids), 4)


# Bootstrap infrastructure

def paired_bootstrap_ci(
    values_a: list[float],
    values_b: list[float],
    n_bootstrap: int = 10000,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict:
    """
    Paired bootstrap 95% CI on (values_a - values_b).
    Returns point_estimate, ci_lower, ci_upper.
    """
    assert len(values_a) == len(values_b), "Paired bootstrap requires equal-length arrays"
    n = len(values_a)
    diffs = [a - b for a, b in zip(values_a, values_b)]
    point_estimate = sum(diffs) / n

    rng = random.Random(seed)
    boot_diffs = []
    for _ in range(n_bootstrap):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        boot_mean = sum(diffs[i] for i in indices) / n
        boot_diffs.append(boot_mean)

    boot_diffs.sort()
    lo_idx = int(n_bootstrap * (alpha / 2))
    hi_idx = int(n_bootstrap * (1 - alpha / 2)) - 1

    return {
        "point_estimate": round(point_estimate, 6),
        "ci_lower": round(boot_diffs[lo_idx], 6),
        "ci_upper": round(boot_diffs[hi_idx], 6),
        "n": n,
        "n_bootstrap": n_bootstrap,
        "seed": seed,
    }


def one_sided_bootstrap_ci(
    values_a: list[float],
    values_b: list[float],
    n_bootstrap: int = 10000,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict:
    """
    One-sided paired bootstrap: test whether A > B.
    CI lower bound > 0 → A significantly greater than B.
    """
    result = paired_bootstrap_ci(values_a, values_b, n_bootstrap, seed, alpha=alpha * 2)
    # One-sided: use the alpha quantile as the lower bound
    diffs = [a - b for a, b in zip(values_a, values_b)]
    n = len(diffs)
    rng = random.Random(seed)
    boot_diffs = []
    for _ in range(n_bootstrap):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        boot_mean = sum(diffs[i] for i in indices) / n
        boot_diffs.append(boot_mean)
    boot_diffs.sort()

    lo_idx = int(n_bootstrap * alpha)
    return {
        "point_estimate": result["point_estimate"],
        "ci_lower": round(boot_diffs[lo_idx], 6),
        "ci_upper": None,  # one-sided — no upper bound
        "n": n,
        "n_bootstrap": n_bootstrap,
        "seed": seed,
    }


def check_equivalence(ci_lower: float, ci_upper: float, bound: float) -> bool:
    """
    Pre-specified CI equivalence check.
    Returns True if the 95% CI falls entirely within [-bound, +bound].
    Used for H1a (±0.015 FC) and H5 (±0.03 precision).
    """
    return ci_lower >= -bound and ci_upper <= bound


# Hypothesis test runners

def test_p1(case_scores: dict, bootstrap_n: int, seed: int) -> dict:
    """P1: IDR ensemble_3x > multiround_2r on regular cases (n=160)."""
    ensemble = case_scores.get("ensemble_3x", {})
    multiround = case_scores.get("multiround_2r", {})
    common_ids = sorted(set(ensemble.keys()) & set(multiround.keys()))
    a = [ensemble[cid]["IDR"] for cid in common_ids if ensemble[cid].get("IDR") is not None
         and multiround[cid].get("IDR") is not None]
    b = [multiround[cid]["IDR"] for cid in common_ids if ensemble[cid].get("IDR") is not None
         and multiround[cid].get("IDR") is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": "No regular cases with IDR"}
    result = one_sided_bootstrap_ci(a, b, bootstrap_n, seed)
    verdict = "PASS" if result["ci_lower"] > 0 else "FAIL"
    return {**result, "test": "P1", "verdict": verdict, "metric": "IDR",
            "comparison": "ensemble_3x > multiround_2r", "subset": "regular"}


def test_p2(case_scores: dict, bootstrap_n: int, seed: int) -> dict:
    """P2: FVC_mixed multiround_2r > ensemble_3x on mixed cases (n=80)."""
    multiround = case_scores.get("multiround_2r", {})
    ensemble = case_scores.get("ensemble_3x", {})
    common_ids = sorted(set(multiround.keys()) & set(ensemble.keys()))
    a = [multiround[cid]["FVC"] for cid in common_ids if multiround[cid].get("FVC") is not None
         and ensemble[cid].get("FVC") is not None]
    b = [ensemble[cid]["FVC"] for cid in common_ids if multiround[cid].get("FVC") is not None
         and ensemble[cid].get("FVC") is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": "No mixed cases with FVC"}
    result = one_sided_bootstrap_ci(a, b, bootstrap_n, seed)
    verdict = "PASS" if result["ci_lower"] > 0 else "FAIL"
    return {**result, "test": "P2", "verdict": verdict, "metric": "FVC_mixed",
            "comparison": "multiround_2r > ensemble_3x", "subset": "mixed"}


def test_h1a(case_scores: dict, bootstrap_n: int, seed: int) -> dict:
    """H1a: FC isolated_debate ≈ baseline on regular cases. Equivalence bound ±0.015."""
    isolated = case_scores.get("isolated_debate", {})
    baseline = case_scores.get("baseline", {})
    common_ids = sorted(set(isolated.keys()) & set(baseline.keys()))
    a = [isolated[cid]["FC"] for cid in common_ids if isolated[cid].get("FC") is not None
         and baseline[cid].get("FC") is not None]
    b = [baseline[cid]["FC"] for cid in common_ids if isolated[cid].get("FC") is not None
         and baseline[cid].get("FC") is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": "No regular cases with FC"}
    result = paired_bootstrap_ci(a, b, bootstrap_n, seed)
    equiv = check_equivalence(result["ci_lower"], result["ci_upper"], 0.015)
    verdict = "PASS" if equiv else "FAIL"
    return {**result, "test": "H1a", "verdict": verdict, "metric": "FC",
            "comparison": "isolated_debate ≈ baseline", "subset": "regular",
            "equivalence_bound": 0.015}


def test_h2(case_scores: dict, bootstrap_n: int, seed: int, subset: str) -> dict:
    """H2: ensemble_3x vs isolated_debate (two-sided). Subset: 'regular' (FC) or 'mixed' (FVC)."""
    ensemble = case_scores.get("ensemble_3x", {})
    isolated = case_scores.get("isolated_debate", {})
    metric = "FC" if subset == "regular" else "FVC"
    common_ids = sorted(set(ensemble.keys()) & set(isolated.keys()))
    a = [ensemble[cid][metric] for cid in common_ids if ensemble[cid].get(metric) is not None
         and isolated[cid].get(metric) is not None]
    b = [isolated[cid][metric] for cid in common_ids if ensemble[cid].get(metric) is not None
         and isolated[cid].get(metric) is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": f"No {subset} cases with {metric}"}
    result = paired_bootstrap_ci(a, b, bootstrap_n, seed)
    # Two-sided: significant if CI doesn't contain 0
    if result["ci_lower"] > 0 or result["ci_upper"] < 0:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    test_name = f"H2_{subset[:3]}"
    return {**result, "test": test_name, "verdict": verdict, "metric": metric,
            "comparison": f"ensemble_3x vs isolated_debate", "subset": subset}


def test_h3(case_scores: dict, bootstrap_n: int, seed: int) -> dict:
    """H3: FVC_mixed multiround_2r > isolated_debate on mixed cases (n=80)."""
    multiround = case_scores.get("multiround_2r", {})
    isolated = case_scores.get("isolated_debate", {})
    common_ids = sorted(set(multiround.keys()) & set(isolated.keys()))
    a = [multiround[cid]["FVC"] for cid in common_ids if multiround[cid].get("FVC") is not None
         and isolated[cid].get("FVC") is not None]
    b = [isolated[cid]["FVC"] for cid in common_ids if multiround[cid].get("FVC") is not None
         and isolated[cid].get("FVC") is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": "No mixed cases with FVC"}
    result = one_sided_bootstrap_ci(a, b, bootstrap_n, seed)
    verdict = "PASS" if result["ci_lower"] > 0 else "FAIL"
    return {**result, "test": "H3", "verdict": verdict, "metric": "FVC_mixed",
            "comparison": "multiround_2r > isolated_debate", "subset": "mixed"}


def test_h4(case_scores: dict, bootstrap_n: int, seed: int) -> dict:
    """H4: IDR ensemble_3x > baseline on regular cases (n=160)."""
    ensemble = case_scores.get("ensemble_3x", {})
    baseline = case_scores.get("baseline", {})
    common_ids = sorted(set(ensemble.keys()) & set(baseline.keys()))
    a = [ensemble[cid]["IDR"] for cid in common_ids if ensemble[cid].get("IDR") is not None
         and baseline[cid].get("IDR") is not None]
    b = [baseline[cid]["IDR"] for cid in common_ids if ensemble[cid].get("IDR") is not None
         and baseline[cid].get("IDR") is not None]
    if not a:
        return {"verdict": "INCONCLUSIVE", "reason": "No regular cases with IDR"}
    result = one_sided_bootstrap_ci(a, b, bootstrap_n, seed)
    verdict = "PASS" if result["ci_lower"] > 0 else "FAIL"
    return {**result, "test": "H4", "verdict": verdict, "metric": "IDR",
            "comparison": "ensemble_3x > baseline", "subset": "regular"}


def test_h5(h5_data: dict, bootstrap_n: int, seed: int) -> dict:
    """
    H5: Union pooling precision parity.
    Precision of 1/3-flagged issues ≈ 3/3-flagged issues.
    Equivalence bound ±0.03.

    h5_data should contain per-case precision values for each tier,
    computed in Phase 6 step 6.4 (per_case_issue_map).
    """
    tier_1of3 = h5_data.get("precision_1of3", [])
    tier_3of3 = h5_data.get("precision_3of3", [])
    if not tier_1of3 or not tier_3of3:
        return {"verdict": "INCONCLUSIVE", "reason": "No H5 tier data available",
                "test": "H5"}
    # Bootstrap on mean precision difference
    result = paired_bootstrap_ci(tier_1of3, tier_3of3, bootstrap_n, seed)
    equiv = check_equivalence(result["ci_lower"], result["ci_upper"], 0.03)
    verdict = "PASS" if equiv else "FAIL"
    return {**result, "test": "H5", "verdict": verdict,
            "metric": "precision_parity",
            "comparison": "1/3-flagged ≈ 3/3-flagged",
            "equivalence_bound": 0.03}


def run_analysis():
    """Phase 7: Run all hypothesis tests and produce v7_results.json."""
    print("Analysis mode — this is a scaffold. Full implementation runs in Phase 7.")
    print(f"Bootstrap: n={args.bootstrap_n}, seed={args.seed}")
    print(f"Raw outputs: {RAW_DIR}")
    print(f"Scores file: {BASE_DIR / args.scores}")
    print(f"Cases file: {CASES_FILE}")
    print(f"Output: {BASE_DIR / args.output}")

    # Verify required files exist
    scores_path = BASE_DIR / args.scores
    output_path = BASE_DIR / args.output

    for path, label in [(CASES_FILE, "cases"), (scores_path, "scores")]:
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            print("Run Phase 5 (benchmark) and Phase 6 (scoring) first.")
            sys.exit(1)

    if not RAW_DIR.exists():
        print(f"ERROR: Raw outputs directory not found: {RAW_DIR}")
        sys.exit(1)

    # Load data
    cases_list = json.load(open(CASES_FILE))
    cases_by_id = {c["case_id"]: c for c in cases_list}
    scores_data = json.load(open(scores_path))
    rescored = scores_data.get("scores", {})

    # Accumulate per-condition per-case score lists, then average after the loop
    regular_score_lists = defaultdict(lambda: defaultdict(list))
    mixed_score_lists = defaultdict(lambda: defaultdict(list))

    raw_files = sorted(RAW_DIR.glob("*.json"))
    print(f"Loading {len(raw_files)} raw output files...")

    for f in raw_files:
        output = json.load(open(f))
        cid = output.get("case_id", "")
        condition = output.get("condition", "")
        case = cases_by_id.get(cid)
        if not case:
            continue

        category = case.get("category", "regular")
        gt = case["ground_truth"]
        st = case["scoring_targets"]
        idr_obj = case["ideal_debate_resolution"]
        correct_position = gt["correct_position"]
        ideal_resolution = idr_obj["type"]
        acceptable = st.get("acceptable_resolutions", [ideal_resolution])
        must_find_ids = st.get("must_find_issue_ids", [])

        # Get rescored values
        file_rescore = rescored.get(f.name, {})

        # Compute scores
        verdict = output.get("verdict", "")

        # IDR
        if correct_position in ("defense_wins", "empirical_test_agreed"):
            idr_val = None
        elif file_rescore.get("idr_documented") is not None:
            idr_val = file_rescore["idr_documented"]
        else:
            idr_val = compute_idr(must_find_ids, file_rescore.get("found_booleans", {}))

        # IDP
        if correct_position in ("defense_wins", "empirical_test_agreed"):
            idp_val = None
        elif file_rescore.get("idp_raw") is not None:
            idp_val = file_rescore["idp_raw"]
        else:
            idp_val = 1.0

        drq_val = compute_drq(verdict, acceptable, ideal_resolution)
        fvc_val = compute_fvc(verdict, acceptable, ideal_resolution)

        score_dict = {"IDR": idr_val, "IDP": idp_val, "DRQ": drq_val, "FVC": fvc_val}
        score_dict["FC"] = compute_fc(score_dict)

        if category == "regular":
            regular_score_lists[condition][cid].append(score_dict)
        elif category == "mixed":
            mixed_score_lists[condition][cid].append(score_dict)

    # Average accumulated runs into final per-case dicts
    def _avg_score_lists(score_lists, dims):
        result = defaultdict(lambda: defaultdict(dict))
        for cond, cases in score_lists.items():
            for cid, run_list in cases.items():
                avg = {}
                for dim in dims:
                    vals = [r[dim] for r in run_list if r.get(dim) is not None]
                    avg[dim] = round(sum(vals) / len(vals), 4) if vals else None
                result[cond][cid] = avg
        return result

    regular_scores = _avg_score_lists(
        regular_score_lists, FAIR_COMPARISON_DIMS + ["FC"]
    )
    mixed_scores = _avg_score_lists(
        mixed_score_lists, ["DRQ", "FVC", "FC"]
    )

    # Run tests
    results = {}
    bn, sd = args.bootstrap_n, args.seed

    results["P1"] = test_p1(regular_scores, bn, sd)
    results["P2"] = test_p2(mixed_scores, bn, sd)
    results["H1a"] = test_h1a(regular_scores, bn, sd)
    results["H2_reg"] = test_h2(regular_scores, bn, sd, "regular")
    results["H2_mix"] = test_h2(mixed_scores, bn, sd, "mixed")
    results["H3"] = test_h3(mixed_scores, bn, sd)
    results["H4"] = test_h4(regular_scores, bn, sd)
    # H5 requires per_case_issue_map from Phase 6 step 6.4 — placeholder
    results["H5"] = test_h5({}, bn, sd)

    # Framework verdict
    p1_pass = results["P1"].get("verdict") == "PASS"
    p2_pass = results["P2"].get("verdict") == "PASS"
    if p1_pass and p2_pass:
        framework = "CONFIRMED"
    elif p1_pass or p2_pass:
        framework = "PARTIAL"
    else:
        framework = "NOT CONFIRMED"
    results["framework_verdict"] = framework

    # Write results
    json.dump(results, open(output_path, "w"), indent=2)
    print(f"\nResults written to {output_path}")
    print(f"Framework verdict: {framework}")
    for test_name, test_result in results.items():
        if isinstance(test_result, dict) and "verdict" in test_result:
            pe = test_result.get("point_estimate", "N/A")
            v = test_result["verdict"]
            print(f"  {test_name}: {v} (delta={pe})")


# ===========================================================================
# Phase 3 — Pilot scoring (pilot mode)
# ===========================================================================


def run_pilot():
    """Phase 3: Lightweight pilot scoring — FVC + DRQ only, no API calls.

    Reads raw baseline outputs and ground-truth cases. Computes FVC and DRQ
    locally. FC = mean(DRQ, FVC) — conservative upper bound on full FC since
    IDR typically pulls it down. Outputs a list matching plan step 3.4 format.
    """
    input_dir = BASE_DIR / args.input if args.input else RAW_DIR
    output_path = BASE_DIR / args.output

    print("Pilot scoring — no API calls (FVC + DRQ only)")
    print(f"Input:  {input_dir}")
    print(f"Cases:  {CASES_FILE}")
    print(f"Output: {output_path}")

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)

    cases_list = json.load(open(CASES_FILE))
    cases_by_id = {c["case_id"]: c for c in cases_list}

    raw_files = sorted(input_dir.glob("*.json"))
    if not raw_files:
        print(f"ERROR: No JSON files in {input_dir}")
        sys.exit(1)

    results = []
    for f in raw_files:
        output = json.load(open(f))
        cid = output.get("case_id", "")
        case = cases_by_id.get(cid)
        if not case:
            continue

        category = case.get("category", "regular")
        st = case["scoring_targets"]
        idr_obj = case["ideal_debate_resolution"]
        ideal_resolution = idr_obj["type"]
        acceptable = st.get("acceptable_resolutions", [ideal_resolution])

        verdict = output.get("verdict", "")

        fvc = compute_fvc(verdict, acceptable, ideal_resolution)
        drq = compute_drq(verdict, acceptable, ideal_resolution)
        fc = round((fvc + drq) / 2, 4)

        results.append({
            "case_id": cid,
            "fc": fc,
            "fvc": fvc,
            "drq": drq,
            "category": category,
        })

    # Summary
    fc_values = [r["fc"] for r in results]
    mean_fc = sum(fc_values) / len(fc_values) if fc_values else 0

    by_cat: dict[str, list[float]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r["fc"])

    print(f"\nScored {len(results)} outputs from {len(raw_files)} files")
    print(f"Overall FC mean: {mean_fc:.4f}")
    for cat in sorted(by_cat):
        vals = by_cat[cat]
        cat_mean = sum(vals) / len(vals)
        print(f"  {cat}: n={len(vals)}, FC mean={cat_mean:.4f}")

    # Difficulty gate check (plan step 3.4)
    regular_fcs = [r["fc"] for r in results if r["category"] == "regular"]
    if regular_fcs:
        reg_mean = sum(regular_fcs) / len(regular_fcs)
        if reg_mean >= 0.80:
            print(f"\n⚠ CEILING WARNING: regular baseline FC mean = {reg_mean:.4f} ≥ 0.80")
            print("  Cases may be too easy. Consider harder case generation.")
        else:
            print(f"\n✓ Difficulty gate: regular FC mean = {reg_mean:.4f} < 0.80")

    json.dump(results, open(output_path, "w"), indent=2)
    print(f"\nSaved {len(results)} results → {output_path}")


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    if args.mode == "pilot":
        run_pilot()
    elif args.mode == "score":
        asyncio.run(run_scoring())
    elif args.mode == "analyze":
        run_analysis()
