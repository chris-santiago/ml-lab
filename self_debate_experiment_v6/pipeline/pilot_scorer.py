# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
pilot_scorer.py — Phase 3 Pilot Calibration Scorer

Independently evaluates pilot cases with GPT-4o (via OpenRouter) to produce
unbiased difficulty labels (PM2 closed-loop confound prevention).

For each case: sends task_prompt + ground truth to GPT-4o as an independent
reviewer. Computes IDR/IDP/DRQ/FVC, derives baseline_fc_mean per case.
Outputs pilot_results.json for select_cases.py --pilot.

Reads:  benchmark_cases_verified.json  (or --cases)
        OPENROUTER_API_KEY env var
Writes: pilot_results.json              (or --output)

Output format (select_cases.py --pilot):
  {
    "cases": {
      "<case_id>": {"baseline_fc_mean": float, "difficulty": "hard"|"medium"},
      ...
    },
    "pilot_fc_mean": float,
    "h1a_threshold": float,
    "n_cases": int,
    "model": "<model>"
  }

Difficulty thresholds (from select_cases.py):
  hard:   baseline_fc_mean <= 0.45
  medium: 0.45 < baseline_fc_mean <= 0.80
  discard (ceiling): baseline_fc_mean > 0.80

Phase 3 hard-stop gate (enforced by select_cases.py --pilot):
  pilot_fc_mean < 0.80 AND >= 80 regular + 30 mixed pass ceiling filter

Usage:
  uv run pipeline/pilot_scorer.py --pilot-size 30
  uv run pipeline/pilot_scorer.py --pilot-size 0   # score all cases
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

from openai import AsyncOpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.table import Table

PIPELINE_DIR = Path(__file__).parent
EXPERIMENT_DIR = PIPELINE_DIR.parent

console = Console()

# Difficulty thresholds — mirrors select_cases.py constants
DIFFICULTY_HARD_THRESHOLD = 0.45
PILOT_CEILING_THRESHOLD = 0.80

# Fair-comparison scoring adjacency set — mirrors self_debate_poc.py
_ADJACENTS = {
    ("critique_wins", "empirical_test_agreed"),
    ("empirical_test_agreed", "critique_wins"),
    ("defense_wins", "empirical_test_agreed"),
    ("empirical_test_agreed", "defense_wins"),
}


def build_scoring_prompt(case: dict) -> str:
    must_find = case["scoring_targets"].get("must_find_issue_ids", [])
    mnc_details = case["scoring_targets"].get("must_not_claim_details", [])
    acceptable = case["scoring_targets"].get("acceptable_resolutions", [])

    if mnc_details:
        mnc_text = "\n".join(
            f"- [{m.get('claim_id', m.get('id', '?'))}] {m['claim']} (why it is NOT a flaw: {m['why_wrong']})"
            for m in mnc_details
        )
    else:
        mnc_text = "(none)"

    return f"""You are independently evaluating an ML methodology for soundness.

METHODOLOGY:
{case["task_prompt"]}

ISSUE IDs TO CHECK (for each: is this issue identifiable as a genuine flaw in the methodology above?):
{json.dumps(must_find, indent=2)}

DESIGN CHOICES THAT ARE VALID (do NOT flag these as flaws):
{mnc_text}

ACCEPTABLE VERDICTS: {json.dumps(acceptable)}

Respond ONLY with a JSON object:
{{
  "issues_identified": {{"<issue_id>": true/false, ...}},
  "false_positives_raised": ["<mnc_id>", ...],
  "verdict": "critique_wins | defense_wins | empirical_test_agreed"
}}
No preamble, no explanation, no markdown fences."""


def parse_response(raw: str) -> dict:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end] if start >= 0 else raw)


def compute_scores(parsed: dict, case: dict) -> dict:
    """
    Compute IDR/IDP/DRQ/FVC from GPT-4o's independent assessment.
    Mirrors self_debate_poc.py scoring logic exactly.
    """
    correct_position = case["ground_truth"]["correct_position"]
    ideal = case["ideal_debate_resolution"]["type"]
    must_find = case["scoring_targets"].get("must_find_issue_ids", [])
    must_not_claim = case["scoring_targets"].get("must_not_claim", [])
    acceptable = case["scoring_targets"].get("acceptable_resolutions", [ideal])

    identified = parsed.get("issues_identified", {})
    fp_raised = parsed.get("false_positives_raised", [])
    verdict = parsed.get("verdict")

    # IDR — issue detection recall
    # N/A for defense cases (no planted flaws) and mixed cases (no definitive issue list)
    if correct_position in ("defense", "mixed") or not must_find:
        idr = None
    else:
        found = sum(1 for v in identified.values() if v)
        idr = round(found / len(must_find), 4)

    # IDP — issue detection precision
    # N/A for defense and mixed cases (mirrors score_run() lines 182-193)
    if correct_position in ("defense", "mixed"):
        idp = None
    else:
        valid_raised = [k for k, v in identified.items() if v and k in must_find]
        invalid_raised = [x for x in fp_raised if x in must_not_claim]
        denom = len(valid_raised) + len(invalid_raised)
        if denom == 0:
            idp = 1.0
        else:
            frac = len(valid_raised) / denom
            if frac >= 0.9:
                idp = 1.0
            elif frac >= 0.5:
                idp = 0.5
            else:
                idp = 0.0

    # DRQ — resolution quality (mirrors compute_drq)
    if verdict == ideal:
        drq = 1.0
    elif verdict in acceptable:
        drq = 0.5
    elif verdict and (verdict, ideal) in _ADJACENTS:
        drq = 0.5
    else:
        drq = 0.0

    # FVC — fair-comparison verdict (mirrors compute_fvc)
    # Adjacent credit uses (verdict, ideal), not (verdict, acceptable)
    if verdict in acceptable:
        fvc = 1.0
    elif verdict and (verdict, ideal) in _ADJACENTS:
        fvc = 0.5
    else:
        fvc = 0.0

    # baseline_fc_mean = mean(non-null fair-comparison dims: IDR, IDP, DRQ, FVC)
    vals = [v for v in [idr, idp, drq, fvc] if v is not None]
    fc_mean = round(sum(vals) / len(vals), 4) if vals else 0.0

    return {
        "IDR": idr, "IDP": idp, "DRQ": drq, "FVC": fvc,
        "fc_mean": fc_mean, "verdict": verdict,
    }


def select_pilot_cases(cases: list[dict], pilot_size: int) -> list[dict]:
    """
    Stratified pilot selection.
    Proportional to target strata: critique 50%, defense 17%, mixed 33%.
    Returns cases in stratum order: critique → defense → mixed.
    """
    if pilot_size <= 0:
        return list(cases)

    critique = [c for c in cases if c.get("category") == "regular"
                and c["ground_truth"]["correct_position"] == "critique"]
    defense  = [c for c in cases if c.get("category") == "regular"
                and c["ground_truth"]["correct_position"] == "defense"]
    mixed    = [c for c in cases if c.get("category") == "mixed"]

    # Target proportions: 60:20:40 → 50%, 17%, 33%
    n_critique = round(pilot_size * 0.50)
    n_defense  = round(pilot_size * 0.17)
    n_mixed    = pilot_size - n_critique - n_defense

    selected = (
        critique[:n_critique] +
        defense[:n_defense] +
        mixed[:n_mixed]
    )
    return selected[:pilot_size]  # guard against rounding overflow


async def score_one(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    case: dict,
    model: str,
    timeout: float,
    retries: int = 2,
) -> dict:
    cid = case["case_id"]
    prompt = build_scoring_prompt(case)
    error = None
    scores = None

    for attempt in range(retries + 1):
        try:
            async with sem:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model,
                        max_tokens=512,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt},
                        ],
                    ),
                    timeout=timeout,
                )
            raw = resp.choices[0].message.content or ""
            parsed = parse_response(raw)
            scores = compute_scores(parsed, case)
            error = None
            break
        except Exception as exc:
            error = str(exc)
            if attempt < retries:
                await asyncio.sleep(2.0 ** attempt)

    return {"case_id": cid, "scores": scores, "error": error}


async def run_pilot(cases: list[dict], args) -> list[dict]:
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    sem = asyncio.Semaphore(args.max_concurrent)

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Pilot scoring[/bold blue]"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("scoring", total=len(cases))

        async def score_and_advance(case):
            result = await score_one(client, sem, case, args.model, args.timeout)
            progress.advance(task)
            return result

        results = await asyncio.gather(*[score_and_advance(c) for c in cases])

    return list(results)


def build_pilot_results(results: list[dict], model: str) -> dict:
    cases_out: dict[str, dict] = {}
    for r in results:
        if r["error"] or r["scores"] is None:
            console.print(f"  [yellow]SKIP {r['case_id']}: {r['error']}[/yellow]")
            continue
        fc = r["scores"]["fc_mean"]
        difficulty = None
        if fc is not None:
            if fc <= DIFFICULTY_HARD_THRESHOLD:
                difficulty = "hard"
            elif fc <= PILOT_CEILING_THRESHOLD:
                difficulty = "medium"
            # fc > 0.80: difficulty stays None (will be ceiling-filtered by select_cases.py)
        cases_out[r["case_id"]] = {
            "baseline_fc_mean": fc,
            "difficulty": difficulty,
        }

    valid_fc = [v["baseline_fc_mean"] for v in cases_out.values() if v["baseline_fc_mean"] is not None]
    pilot_fc_mean = round(sum(valid_fc) / len(valid_fc), 4) if valid_fc else None
    h1a = round(max(0.03, min(0.10, (1.0 - pilot_fc_mean) * 0.5)), 4) if pilot_fc_mean is not None else None

    return {
        "cases": cases_out,
        "pilot_fc_mean": pilot_fc_mean,
        "h1a_threshold": h1a,
        "n_cases": len(cases_out),
        "model": model,
    }


def print_summary(pilot: dict, results: list[dict]) -> None:
    console.print()
    table = Table(title="Pilot Scoring Summary", show_header=True)
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    pilot_fc = pilot.get("pilot_fc_mean")
    h1a = pilot.get("h1a_threshold")
    n = pilot.get("n_cases", 0)

    cases_data = pilot.get("cases", {})
    n_hard = sum(1 for v in cases_data.values() if v.get("difficulty") == "hard")
    n_medium = sum(1 for v in cases_data.values() if v.get("difficulty") == "medium")
    n_ceiling = sum(1 for v in cases_data.values() if v.get("baseline_fc_mean", 0) > PILOT_CEILING_THRESHOLD)
    n_errors = sum(1 for r in results if r["error"])

    table.add_row("Cases scored", str(n))
    table.add_row("Errors / skipped", str(n_errors))
    table.add_row("pilot_fc_mean", f"{pilot_fc:.4f}" if pilot_fc is not None else "N/A")
    table.add_row("H1a threshold", f"{h1a:.4f}" if h1a is not None else "N/A")
    table.add_row("Hard (FC ≤ 0.45)", str(n_hard))
    table.add_row("Medium (0.45 < FC ≤ 0.80)", str(n_medium))
    table.add_row("Ceiling fails (FC > 0.80)", str(n_ceiling))

    gate_ok = pilot_fc is not None and pilot_fc < PILOT_CEILING_THRESHOLD
    gate_str = "[green]PASS[/green]" if gate_ok else "[red]FAIL — insufficient headroom[/red]"
    table.add_row("Pilot FC gate (< 0.80)", gate_str)

    console.print(table)

    if pilot_fc is not None:
        console.print(
            f"\n[bold]H1a threshold set to:[/bold] {h1a:.4f}  "
            f"(formula: max(0.03, min(0.10, (1 − {pilot_fc:.4f}) × 0.5)))"
        )
    console.print(
        "\n[dim]Run: uv run pipeline/select_cases.py --pilot pilot_results.json[/dim]"
    )


def main():
    parser = argparse.ArgumentParser(
        description="pilot_scorer.py — Phase 3 pilot calibration scorer"
    )
    parser.add_argument(
        "--cases", default="benchmark_cases_verified.json",
        help="Input benchmark cases file (default: benchmark_cases_verified.json)",
    )
    parser.add_argument(
        "--output", default="pilot_results.json",
        help="Output pilot results file (default: pilot_results.json)",
    )
    parser.add_argument(
        "--pilot-size", type=int, default=30,
        help="Number of cases to score, stratified (0 = all, default: 30)",
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=20,
        help="Max concurrent GPT-4o requests (default: 20)",
    )
    parser.add_argument(
        "--timeout", type=float, default=90.0,
        help="Per-request timeout seconds (default: 90)",
    )
    parser.add_argument(
        "--model", default="openai/gpt-4o",
        help="OpenRouter model ID (default: openai/gpt-4o)",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]ERROR: OPENROUTER_API_KEY not set[/red]")
        sys.exit(1)

    console.rule("[bold blue]pilot_scorer.py — Phase 3[/bold blue]")
    console.print(f"Model:      {args.model}")
    console.print(f"Timeout:    {args.timeout}s  |  Concurrency: {args.max_concurrent}")

    cases_path = EXPERIMENT_DIR / args.cases
    output_path = EXPERIMENT_DIR / args.output

    if not cases_path.exists():
        console.print(f"[red]ERROR: {cases_path} not found. Run normalize_cases.py + select_cases.py first.[/red]")
        sys.exit(1)

    all_cases = json.loads(cases_path.read_text(encoding="utf-8"))
    pilot_cases = select_pilot_cases(all_cases, args.pilot_size)

    n_c = sum(1 for c in pilot_cases if c.get("category") == "regular" and c["ground_truth"]["correct_position"] == "critique")
    n_d = sum(1 for c in pilot_cases if c.get("category") == "regular" and c["ground_truth"]["correct_position"] == "defense")
    n_m = sum(1 for c in pilot_cases if c.get("category") == "mixed")
    console.print(f"\nPilot cases: {len(pilot_cases)}  (critique={n_c}  defense={n_d}  mixed={n_m})")
    console.print(f"Output:     {output_path}\n")

    results = asyncio.run(run_pilot(pilot_cases, args))

    pilot = build_pilot_results(results, args.model)
    print_summary(pilot, results)

    output_path.write_text(json.dumps(pilot, indent=2), encoding="utf-8")
    console.print(f"\n[green]✓ Wrote {pilot['n_cases']} cases → {output_path}[/green]")


if __name__ == "__main__":
    main()
