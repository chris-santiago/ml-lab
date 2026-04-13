# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
phase5_benchmark.py — v7 API-Based Debate Benchmark Runner

Runs all 4 conditions x N cases x 3 runs via OpenRouter API.
Produces per-case JSON files matching the v7 output schema.

Conditions:
  baseline        — 1 API call (critic only)
  isolated_debate — 3 API calls (critic || defender, then adjudicator)
  ensemble_3x     — 3 parallel critic calls + majority vote + union IDR
  multiround_2r   — 3 sequential calls (critic -> defender -> adjudicator)

Usage:
  uv run pipeline/phase5_benchmark.py \\
    --cases v7_cases_sanitized.json \\
    --output-dir v7_raw_outputs \\
    --conditions baseline,isolated_debate,ensemble_3x,multiround_2r \\
    --max-concurrent 20 \\
    --model anthropic/claude-sonnet-4.6 \\
    --runs 3 \\
    --dry-run
"""

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

SCRIPT_DIR = Path(__file__).parent
EXPERIMENT_DIR = SCRIPT_DIR.parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"

console = Console()

ALL_CONDITIONS = ["baseline", "isolated_debate", "ensemble_3x", "multiround_2r"]
VALID_VERDICTS = {"critique_wins", "defense_wins", "empirical_test_agreed"}

MIXED_CASE_INJECTION = (
    "\n\nThis is a mixed case. Valid verdicts: critique_wins, defense_wins, "
    "empirical_test_agreed. Use empirical_test_agreed when both sides made "
    "substantive points only resolvable empirically."
)


@dataclass
class Config:
    model: str
    temperature: float
    timeout: float
    retries: int
    max_tokens: int = 4096


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompts() -> dict[str, str]:
    """Load all system prompts from pipeline/prompts/ directory."""
    prompts = {}
    for name in ["critic", "defender_isolated", "multiround_2r_defender", "adjudicator"]:
        path = PROMPTS_DIR / f"{name}.md"
        if not path.exists():
            console.print(f"[red]ERROR: Missing prompt file: {path}[/red]")
            sys.exit(1)
        prompts[name] = path.read_text(encoding="utf-8")
    return prompts


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from LLM responses."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM response, handling code fences and think tags."""
    text = strip_think_tags(text)

    # Try stripping code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Find outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Last resort: try parsing the whole thing
    return json.loads(text)


def parse_response(raw_text: str) -> dict:
    """Parse LLM response into structured dict. Raises ValueError on failure."""
    if not raw_text:
        raise ValueError("Empty response from API")
    try:
        return extract_json(raw_text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"JSON parse failed: {e}\nRaw (first 500 chars): {raw_text[:500]}")


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

async def call_api(
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    system_prompt: str,
    user_msg: str,
    config: Config,
) -> dict:
    """Make a single API call with retry and timeout. Returns parsed JSON dict."""
    for attempt in range(config.retries + 1):
        try:
            async with sem:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=config.model,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg},
                        ],
                    ),
                    timeout=config.timeout,
                )
            raw = resp.choices[0].message.content or ""
            return parse_response(raw)
        except Exception as exc:
            if attempt < config.retries:
                wait = 2.0 ** attempt
                console.print(
                    f"  [yellow]Retry {attempt + 1}/{config.retries} "
                    f"after {wait:.0f}s: {type(exc).__name__}[/yellow]"
                )
                await asyncio.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Atomic file write
# ---------------------------------------------------------------------------

def write_output(output_dir: Path, result: dict) -> Path:
    """Write result JSON atomically via .tmp rename."""
    case_id = result["case_id"]
    condition = result["condition"]
    run_idx = result["run_idx"]
    filename = f"{case_id}__{condition}__run{run_idx}.json"
    final_path = output_dir / filename
    tmp_path = output_dir / f"{filename}.tmp"

    tmp_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    os.rename(str(tmp_path), str(final_path))
    return final_path


# ---------------------------------------------------------------------------
# Resume logic
# ---------------------------------------------------------------------------

def scan_completed(output_dir: Path) -> set[tuple[str, str, int]]:
    """Scan output directory for completed (case_id, condition, run_idx) tuples."""
    completed = set()
    for f in output_dir.glob("*.json"):
        # Filename convention: {case_id}__{condition}__run{run_idx}.json
        # Double-underscore delimiter avoids ambiguity with case_id underscores
        parts = f.stem.split("__")
        if len(parts) == 3 and parts[2].startswith("run"):
            try:
                # Validate it's a parseable JSON file
                json.loads(f.read_text(encoding="utf-8"))  # validate parseable
                case_id = parts[0]
                condition = parts[1]
                run_idx = int(parts[2][3:])
                completed.add((case_id, condition, run_idx))
            except (json.JSONDecodeError, ValueError):
                console.print(f"  [yellow]Skipping corrupt file: {f.name}[/yellow]")
    return completed


# ---------------------------------------------------------------------------
# Condition handlers
# ---------------------------------------------------------------------------

async def run_baseline(
    case: dict, run_idx: int, sem: asyncio.Semaphore,
    client: AsyncOpenAI, prompts: dict, config: Config, dry_run: bool,
) -> dict:
    """Baseline: 1 API call (critic only). Every issue survives."""
    task_prompt = case["task_prompt"]

    if dry_run:
        console.print(f"  [dim]DRY RUN baseline: {case['case_id']} run{run_idx}[/dim]")
        console.print(f"    System prompt: critic ({len(prompts['critic'])} chars)")
        console.print(f"    User message: {len(task_prompt)} chars")
        return _dry_run_result(case, "baseline", run_idx)

    critic = await call_api(sem, client, prompts["critic"], task_prompt, config)

    return {
        "case_id": case["case_id"],
        "condition": "baseline",
        "run_idx": run_idx,
        "critic_raw": critic.get("critic_raw", ""),
        "defender_raw": None,
        "all_issues_raised": critic.get("all_issues_raised", []),
        "all_issues_adjudicated": critic.get("all_issues_raised", []),
        "verdict": _validate_verdict(critic.get("verdict", "")),
    }


async def run_isolated_debate(
    case: dict, run_idx: int, sem: asyncio.Semaphore,
    client: AsyncOpenAI, prompts: dict, config: Config, dry_run: bool,
) -> dict:
    """Isolated debate: critic || defender (no cross-visibility), then adjudicator."""
    task_prompt = case["task_prompt"]
    is_mixed = case.get("category") == "mixed"

    if dry_run:
        console.print(f"  [dim]DRY RUN isolated_debate: {case['case_id']} run{run_idx}[/dim]")
        return _dry_run_result(case, "isolated_debate", run_idx)

    # Critic and defender run concurrently — defender does NOT see critic output
    critic_task = call_api(sem, client, prompts["critic"], task_prompt, config)
    defender_task = call_api(
        sem, client, prompts["defender_isolated"], task_prompt, config
    )
    critic, defender = await asyncio.gather(critic_task, defender_task)

    # Adjudicator receives both
    adj_user_msg = _build_adjudicator_input(task_prompt, critic, defender, is_mixed)
    adjudicator = await call_api(
        sem, client, prompts["adjudicator"], adj_user_msg, config
    )

    return {
        "case_id": case["case_id"],
        "condition": "isolated_debate",
        "run_idx": run_idx,
        "critic_raw": critic.get("critic_raw", ""),
        "defender_raw": defender.get("defender_raw", ""),
        "all_issues_raised": critic.get("all_issues_raised", []),
        "all_issues_adjudicated": adjudicator.get("all_issues_adjudicated", []),
        "verdict": _validate_verdict(adjudicator.get("verdict", "")),
    }


async def run_ensemble_3x(
    case: dict, run_idx: int, sem: asyncio.Semaphore,
    client: AsyncOpenAI, prompts: dict, config: Config, dry_run: bool,
) -> dict:
    """Ensemble: 3 parallel critic calls + majority vote verdict + union issues."""
    task_prompt = case["task_prompt"]

    if dry_run:
        console.print(f"  [dim]DRY RUN ensemble_3x: {case['case_id']} run{run_idx}[/dim]")
        return _dry_run_result(case, "ensemble_3x", run_idx)

    # 3 independent critic calls in parallel
    tasks = [
        call_api(sem, client, prompts["critic"], task_prompt, config)
        for _ in range(3)
    ]
    results = await asyncio.gather(*tasks)

    # Majority vote for verdict
    verdicts = [_validate_verdict(r.get("verdict", "")) for r in results]
    verdict_counts = Counter(verdicts)
    majority_verdict = verdict_counts.most_common(1)[0][0]

    # Union of all issues raised (any-assessor-found)
    all_issues_union = []
    seen = set()
    for r in results:
        for issue in r.get("all_issues_raised", []):
            normalized = issue.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                all_issues_union.append(issue)

    # Per-assessor results for union IDR computation
    assessor_results = []
    for idx, r in enumerate(results):
        assessor_results.append({
            "assessor_idx": idx,
            "issues_raised": r.get("all_issues_raised", []),
            "verdict": _validate_verdict(r.get("verdict", "")),
            "critic_raw": r.get("critic_raw", ""),
        })

    return {
        "case_id": case["case_id"],
        "condition": "ensemble_3x",
        "run_idx": run_idx,
        "critic_raw": results[0].get("critic_raw", ""),
        "defender_raw": None,
        "all_issues_raised": all_issues_union,
        "all_issues_adjudicated": all_issues_union,
        "verdict": majority_verdict,
        "assessor_results": assessor_results,
    }


async def run_multiround_2r(
    case: dict, run_idx: int, sem: asyncio.Semaphore,
    client: AsyncOpenAI, prompts: dict, config: Config, dry_run: bool,
) -> dict:
    """Multiround 2-round: critic -> defender (sees critic) -> adjudicator. Exactly 3 calls."""
    task_prompt = case["task_prompt"]
    is_mixed = case.get("category") == "mixed"

    if dry_run:
        console.print(f"  [dim]DRY RUN multiround_2r: {case['case_id']} run{run_idx}[/dim]")
        return _dry_run_result(case, "multiround_2r", run_idx)

    # Call 1: Critic
    critic = await call_api(sem, client, prompts["critic"], task_prompt, config)

    # Call 2: Defender sees critic output
    defender_user_msg = (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Critic's Analysis\n\n{critic.get('critic_raw', '')}\n\n"
        f"## Issues Raised by Critic\n\n"
        + "\n".join(f"- {i}" for i in critic.get("all_issues_raised", []))
    )
    defender = await call_api(
        sem, client, prompts["multiround_2r_defender"], defender_user_msg, config
    )

    # Call 3: Adjudicator
    adj_user_msg = _build_adjudicator_input(task_prompt, critic, defender, is_mixed)
    adjudicator = await call_api(
        sem, client, prompts["adjudicator"], adj_user_msg, config
    )

    return {
        "case_id": case["case_id"],
        "condition": "multiround_2r",
        "run_idx": run_idx,
        "critic_raw": critic.get("critic_raw", ""),
        "defender_raw": defender.get("defender_raw", ""),
        "all_issues_raised": critic.get("all_issues_raised", []),
        "all_issues_adjudicated": adjudicator.get("all_issues_adjudicated", []),
        "verdict": _validate_verdict(adjudicator.get("verdict", "")),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONDITION_HANDLERS = {
    "baseline": run_baseline,
    "isolated_debate": run_isolated_debate,
    "ensemble_3x": run_ensemble_3x,
    "multiround_2r": run_multiround_2r,
}


def _validate_verdict(verdict: str) -> str:
    """Normalize verdict string; fall back to critique_wins if invalid."""
    v = verdict.strip().lower()
    if v in VALID_VERDICTS:
        return v
    console.print(f"  [yellow]WARN: Invalid verdict '{verdict}', defaulting to critique_wins[/yellow]")
    return "critique_wins"


def _build_adjudicator_input(
    task_prompt: str, critic: dict, defender: dict, is_mixed: bool
) -> str:
    """Build the user message for the adjudicator."""
    parts = [
        f"## Methodology Under Review\n\n{task_prompt}",
        f"## Critic's Analysis\n\n{critic.get('critic_raw', '')}",
        f"## Issues Raised by Critic\n\n"
        + "\n".join(f"- {i}" for i in critic.get("all_issues_raised", [])),
        f"## Defender's Response\n\n{defender.get('defender_raw', '')}",
        f"## Defender's Verdict: {defender.get('verdict', 'unknown')}",
    ]
    msg = "\n\n".join(parts)
    if is_mixed:
        msg += MIXED_CASE_INJECTION
    return msg


def _dry_run_result(case: dict, condition: str, run_idx: int) -> dict:
    """Generate a placeholder result for dry-run mode."""
    return {
        "case_id": case["case_id"],
        "condition": condition,
        "run_idx": run_idx,
        "critic_raw": "[DRY RUN]",
        "defender_raw": "[DRY RUN]" if condition != "baseline" else None,
        "all_issues_raised": ["[DRY RUN issue 1]", "[DRY RUN issue 2]"],
        "all_issues_adjudicated": ["[DRY RUN issue 1]"],
        "verdict": "critique_wins",
        **({"assessor_results": [
            {"assessor_idx": i, "issues_raised": [f"[DRY RUN assessor {i}]"],
             "verdict": "critique_wins", "critic_raw": "[DRY RUN]"}
            for i in range(3)
        ]} if condition == "ensemble_3x" else {}),
    }


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

async def run_benchmark(
    cases: list[dict],
    output_dir: Path,
    conditions: list[str],
    runs: int,
    config: Config,
    dry_run: bool,
    max_concurrent: int,
) -> dict:
    """Run the full benchmark. Returns summary stats."""
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    sem = asyncio.Semaphore(max_concurrent)
    prompts = load_prompts()

    # Build task list and check for completed work
    completed = scan_completed(output_dir) if not dry_run else set()
    all_tasks = []
    for case in cases:
        for condition in conditions:
            for run_idx in range(runs):
                key = (case["case_id"], condition, run_idx)
                if key not in completed:
                    all_tasks.append((case, condition, run_idx))

    if completed:
        console.print(f"[green]Resuming: {len(completed)} already completed[/green]")
    console.print(
        f"Tasks remaining: {len(all_tasks)} "
        f"({len(cases)} cases x {len(conditions)} conditions x {runs} runs "
        f"- {len(completed)} completed)"
    )

    if not all_tasks:
        console.print("[green]All tasks already completed![/green]")
        return {"completed": len(completed), "failed": 0, "skipped": len(completed)}

    stats = {"completed": 0, "failed": 0, "skipped": len(completed)}

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Benchmark[/bold blue]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_bar = progress.add_task("running", total=len(all_tasks))

        async def process_one(case, condition, run_idx):
            handler = CONDITION_HANDLERS[condition]
            try:
                result = await handler(
                    case, run_idx, sem, client, prompts, config, dry_run
                )
                if not dry_run:
                    write_output(output_dir, result)
                stats["completed"] += 1
            except Exception as exc:
                console.print(
                    f"  [red]FAIL: {case['case_id']} {condition} run{run_idx}: "
                    f"{type(exc).__name__}: {exc}[/red]"
                )
                stats["failed"] += 1
            finally:
                progress.advance(task_bar)

        # Process all tasks with controlled concurrency via semaphore
        await asyncio.gather(*[
            process_one(case, condition, run_idx)
            for case, condition, run_idx in all_tasks
        ])

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="v7 Debate Benchmark Runner — API dispatch via OpenRouter"
    )
    parser.add_argument(
        "--cases", required=True,
        help="Path to sanitized benchmark cases JSON (ground truth stripped)",
    )
    parser.add_argument(
        "--output-dir", default="v7_raw_outputs",
        help="Output directory for per-case JSON files (default: v7_raw_outputs)",
    )
    parser.add_argument(
        "--conditions", default=",".join(ALL_CONDITIONS),
        help=f"Comma-separated conditions (default: {','.join(ALL_CONDITIONS)})",
    )
    parser.add_argument(
        "--runs", type=int, default=3,
        help="Number of runs per (case, condition) pair (default: 3)",
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=20,
        help="Max concurrent API calls (default: 20)",
    )
    parser.add_argument(
        "--model", default="anthropic/claude-sonnet-4.6",
        help="OpenRouter model ID (default: anthropic/claude-sonnet-4.6)",
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0,
        help="Sampling temperature; must be >0 for zero-variance check (default: 1.0)",
    )
    parser.add_argument(
        "--timeout", type=float, default=180.0,
        help="Per-request timeout in seconds (default: 180)",
    )
    parser.add_argument(
        "--retries", type=int, default=2,
        help="Max retries per API call (default: 2)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print prompts and generate placeholder output without making API calls",
    )
    args = parser.parse_args()

    # Validate environment
    if not args.dry_run and not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]ERROR: OPENROUTER_API_KEY not set[/red]")
        sys.exit(1)

    # Parse conditions
    conditions = [c.strip() for c in args.conditions.split(",")]
    for c in conditions:
        if c not in ALL_CONDITIONS:
            console.print(f"[red]ERROR: Unknown condition '{c}'. Valid: {ALL_CONDITIONS}[/red]")
            sys.exit(1)

    # Resolve paths relative to experiment directory
    cases_path = EXPERIMENT_DIR / args.cases
    output_dir = EXPERIMENT_DIR / args.output_dir

    if not cases_path.exists():
        console.print(f"[red]ERROR: Cases file not found: {cases_path}[/red]")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load cases
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    console.rule("[bold blue]v7 Benchmark Runner[/bold blue]")
    console.print(f"Model:       {args.model}")
    console.print(f"Temperature: {args.temperature}")
    console.print(f"Timeout:     {args.timeout}s  |  Retries: {args.retries}")
    console.print(f"Concurrency: {args.max_concurrent}")
    console.print(f"Conditions:  {conditions}")
    console.print(f"Cases:       {len(cases)}  |  Runs: {args.runs}")
    console.print(f"Output:      {output_dir}")
    if args.dry_run:
        console.print("[yellow]DRY RUN — no API calls will be made[/yellow]")
    console.print()

    config = Config(
        model=args.model,
        temperature=args.temperature,
        timeout=args.timeout,
        retries=args.retries,
    )

    stats = asyncio.run(
        run_benchmark(cases, output_dir, conditions, args.runs, config, args.dry_run,
                      args.max_concurrent)
    )

    console.print()
    console.rule("[bold]Summary[/bold]")
    console.print(f"Completed: {stats['completed']}")
    console.print(f"Failed:    {stats['failed']}")
    console.print(f"Skipped:   {stats['skipped']} (already done)")

    if stats["failed"] > 0:
        console.print(f"\n[red]WARNING: {stats['failed']} tasks failed.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
