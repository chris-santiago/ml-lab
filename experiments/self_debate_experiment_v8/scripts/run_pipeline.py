# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
run_pipeline.py — v8 Debate Pipeline Runner

Runs the v8 two-stage pipeline (critic → defender) on a set of benchmark cases
via OpenRouter. Verdict derivation is deterministic — applied by derive_verdict()
from the defender's structured output fields, with no LLM adjudicator call.

PIPELINE STAGES
---------------
  Stage 1 — Critic:   receives task_prompt (hypothesis + PoC code)
                      outputs structured findings JSON
  Stage 2 — Defender: receives task_prompt + critic findings JSON
                      outputs structured rebuttals JSON
  Verdict:            derive_verdict() applies point verdict rules mechanically
                      from (adjusted_severity, rebuttal_type) per finding.
                      No LLM call. Output stored as adjudicator_output for
                      scorer.py schema compatibility.

OUTPUT SCHEMA
-------------
One JSON file per run, named {case_id}__run{run_id}.json, matching the
input schema expected by scripts/scorer.py.

MODEL SELECTION
---------------
  --seed-file: Fixed model assignments for canary iteration loop (holds model
               draws constant across prompt iterations so metric changes reflect
               the prompt, not different model draws). Seed files may contain a
               third "adjudicator" model slot — it is stored for traceability
               but never called.
  No seed file: Draws 2 models per run (critic, defender).

RESUME LOGIC
------------
  Already-completed output files are detected and skipped automatically.
  Safe to interrupt and re-run.

Usage:
  # Canary run (fixed seeds, 40 cases x 3 runs)
  uv run scripts/run_pipeline.py \\
    --cases v8_cases.json \\
    --output-dir v8_raw_outputs/defender-v1 \\
    --seed-file scripts/canary_seeds.json \\
    --max-concurrent 100

  # Full benchmark run (random draws)
  uv run scripts/run_pipeline.py \\
    --cases v8_cases.json \\
    --output-dir v8_raw_outputs/defender-v1-full \\
    --runs 3 \\
    --max-concurrent 100

  # Dry run (validates prompts and case schema, no API calls)
  uv run scripts/run_pipeline.py --cases v8_cases.json --dry-run
"""

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# model_selector lives in the same scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))
from model_selector import load as _ms_load, model_generator  # noqa: E402

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
PROMPTS_DIR = EXPERIMENT_DIR / "prompts"
MODELS_FILE = EXPERIMENT_DIR / "models.json"

console = Console()

VALID_VERDICTS = {"critique_wins", "defense_wins", "empirical_test_agreed"}

VALID_FLAW_CATEGORIES = {
    # regular
    "signal_leakage", "eval_inflation", "missing_baselines", "distribution_shift",
    "metric_limitations", "unverified_prereqs", "implicit_dist_assump",
    "synthetic_data_assump", "silent_misconfig",
    # mixed
    "uncertain_significance", "fixable_flaw", "defensible_unconventional",
    "ambiguous_evidence", "context_dependent", "below_threshold",
}


@dataclass
class Config:
    temperature: float
    timeout: float
    retries: int
    max_tokens: int = 8192


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompts() -> dict[str, str]:
    """Load critic and defender system prompts from prompts/ dir.

    ADJUDICATOR.md is a verdict derivation spec — it documents the rules
    implemented in derive_verdict() but is not sent to any model.
    """
    prompts = {}
    for name in ["CRITIC", "DEFENDER"]:
        path = PROMPTS_DIR / f"{name}.md"
        if not path.exists():
            console.print(f"[red]ERROR: Missing prompt file: {path}[/red]")
            sys.exit(1)
        prompts[name.lower()] = path.read_text(encoding="utf-8")
    return prompts


# ---------------------------------------------------------------------------
# Model pool
# ---------------------------------------------------------------------------

def load_model_pool() -> list[str]:
    """Load model IDs from models.json."""
    if not MODELS_FILE.exists():
        console.print(f"[red]ERROR: models.json not found: {MODELS_FILE}[/red]")
        sys.exit(1)
    return _ms_load(MODELS_FILE)


def assign_models(draw: list[str]) -> dict[str, str]:
    """Map a model draw to named role assignments.

    Only critic and defender are called. The third slot is kept for seed file
    compatibility and traceability but is never used for an API call.
    """
    return {
        "critic": draw[0],
        "defender": draw[1],
        "adjudicator": draw[2] if len(draw) > 2 else "derived",
    }


def load_seed_file(path: Path) -> dict:
    """Load seed file: {case_id: {run_id (str): {critic, defender, adjudicator}}}."""
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks (qwq-32b and similar reasoning models)."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _sanitize_json_string(text: str) -> str:
    """Fix common LLM JSON serialization issues: control chars inside strings,
    invalid backslash escapes. Applied after fence extraction."""
    # Replace literal control chars (tab, newline, CR) inside string values
    # by scanning char-by-char is slow; use regex to catch unescaped newlines
    # inside what looks like a JSON string span.
    text = re.sub(r'(?<!\\)\n', r'\\n', text)
    text = re.sub(r'(?<!\\)\r', r'\\r', text)
    text = re.sub(r'(?<!\\)\t', r'\\t', text)
    return text


def extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM response, handling code fences and think tags."""
    text = strip_think_tags(text)

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Second attempt: sanitize control chars that models emit inside strings
            try:
                return json.loads(_sanitize_json_string(candidate))
            except json.JSONDecodeError:
                pass

    return json.loads(text)


_NO_FINDINGS_PATTERNS = (
    "no findings above nit",
    "no material findings",
    "no advancing findings",
    "no fatal, material",
    "methodology is sound",
    "no flaws identified",
    "no significant findings",
)


def parse_response(raw_text: str) -> dict:
    """Parse LLM response into structured dict. Raises ValueError on failure."""
    if not raw_text:
        raise ValueError("Empty response from API")
    try:
        return extract_json(raw_text)
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: plain-text "no findings" response — synthesize valid critic JSON
        lower = raw_text.lower()
        if any(pat in lower for pat in _NO_FINDINGS_PATTERNS):
            return {
                "findings": [],
                "no_material_findings": True,
                "summary": raw_text.strip()[:300],
                "_parse_fallback": True,
            }
        raise ValueError(f"JSON parse failed: {e}\nRaw (first 500 chars): {raw_text[:500]}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_critic_output(data: dict) -> dict:
    """Validate critic output has required fields. Returns data or raises ValueError."""
    if "findings" not in data:
        raise ValueError("Critic output missing 'findings' array")
    for f in data["findings"]:
        for field in ("finding_id", "severity", "severity_label", "suppressed"):
            if field not in f:
                raise ValueError(f"Finding missing required field '{field}': {f}")
        if not isinstance(f["severity"], int) or not (0 <= f["severity"] <= 10):
            raise ValueError(f"Finding severity out of range [0,10]: {f['severity']}")
        cat = f.get("flaw_category")
        if cat is not None and not f.get("suppressed", False) and cat not in VALID_FLAW_CATEGORIES:
            console.print(
                f"  [yellow]WARN: flaw_category '{cat}' in {f['finding_id']} not in taxonomy "
                f"— scorer will mark unmatched[/yellow]"
            )
    return data


def validate_defender_output(data: dict) -> dict:
    """Validate defender output has required fields."""
    if "rebuttals" not in data:
        raise ValueError("Defender output missing 'rebuttals' array")
    if "overall_verdict" not in data:
        raise ValueError("Defender output missing 'overall_verdict'")
    v = data["overall_verdict"]
    if v not in VALID_VERDICTS:
        console.print(f"  [yellow]WARN: Defender overall_verdict '{v}' invalid, keeping as-is[/yellow]")
    for r in data["rebuttals"]:
        for field in ("finding_id", "rebuttal_type", "adjusted_severity"):
            if field not in r:
                raise ValueError(f"Rebuttal missing required field '{field}': {r}")
        # Enforce floor=0 — defenders sometimes output negative adjusted_severity
        if isinstance(r.get("adjusted_severity"), (int, float)):
            r["adjusted_severity"] = max(0, r["adjusted_severity"])

    # Constitutional constraint: defense_wins impossible if CONCEDE + adjusted_severity >= 7
    if v == "defense_wins":
        fatal_concedes = [
            r["finding_id"] for r in data["rebuttals"]
            if r.get("rebuttal_type") == "CONCEDE" and r.get("adjusted_severity", 0) >= 7
        ]
        if fatal_concedes:
            console.print(
                f"  [red]WARN: CONSTITUTIONAL VIOLATION — defense_wins + CONCEDE "
                f"with adjusted_severity >= 7: {fatal_concedes}[/red]"
            )
        # EXONERATE threshold: defense_wins requires all adjusted_severity <= 3
        over_threshold = [
            r["finding_id"] for r in data["rebuttals"]
            if r.get("adjusted_severity", 0) > 3
        ]
        if over_threshold:
            console.print(
                f"  [yellow]WARN: defense_wins claimed but finding(s) {over_threshold} "
                f"have adjusted_severity > 3 (EXONERATE requires all <= 3)[/yellow]"
            )
    return data



# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

async def call_api(
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_msg: str,
    config: Config,
) -> dict:
    """Single API call to OpenRouter with retry and timeout. Returns parsed JSON dict."""
    for attempt in range(config.retries + 1):
        try:
            async with sem:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model,
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
                    f"after {wait:.0f}s: {type(exc).__name__}: {exc}[/yellow]"
                )
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("call_api: exhausted retries without success or exception")


# ---------------------------------------------------------------------------
# User message builders
# ---------------------------------------------------------------------------

def build_critic_user_msg(task_prompt: str) -> str:
    """Wrap task_prompt with framing that makes clear no separate code file exists."""
    return (
        "## Proof-of-Concept Under Review\n\n"
        "The following is the complete proof-of-concept for this ML investigation. "
        "It includes the hypothesis, experiment design, and methodology. "
        "There is no separate implementation code file — the experiment design document "
        "below IS the full PoC. Review it for methodology flaws.\n\n"
        f"{task_prompt}"
    )


def build_defender_user_msg(task_prompt: str, critic_output: dict) -> str:
    """Build the defender's user message: task + critic structured findings."""
    advancing = [f for f in critic_output.get("findings", []) if not f.get("suppressed", False)]
    findings_json = json.dumps(advancing, indent=2)
    return (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Critic Findings (FATAL, MATERIAL, and MINOR only — NIT suppressed)\n\n"
        f"```json\n{findings_json}\n```\n\n"
        f"Produce your structured rebuttal JSON as specified in your instructions."
    )


def derive_verdict(defender_output: dict) -> dict:
    """Derive case verdict deterministically from defender structured output.

    Implements the point verdict table from prompts/ADJUDICATOR.md.
    No LLM call — verdict is a pure function of (original_severity, adjusted_severity,
    rebuttal_type).

    Point verdict rules (applied in order, constitutional overrides last):
      adj_sev <= 3                              → defense_wins  (any rebuttal_type)
      adj_sev 4-6, CONCEDE                      → critique_wins
      adj_sev 4-6, REBUT-*, orig_sev < 7        → defense_wins
      adj_sev 4-6, REBUT-*, orig_sev >= 7       → empirical_test_agreed
        (FATAL finding partially rebutted — must fully clear to ≤3 for exoneration)
      adj_sev 4-6, DEFER                        → empirical_test_agreed
      adj_sev >= 7, CONCEDE                     → critique_wins
      adj_sev >= 7, REBUT-*                     → empirical_test_agreed
      adj_sev >= 7, DEFER                       → empirical_test_agreed

    Constitutional overrides:
      CONCEDE + adj_sev >= 7  → force critique_wins
      DEFER   + adj_sev <= 3  → override to defense_wins (minor deferred questions
                                 do not block exoneration)

    Case verdict precedence:
      Any point critique_wins → case critique_wins
      No critique_wins, any empirical_test_agreed → empirical_test_agreed
      All defense_wins → defense_wins
    """
    rebuttals = defender_output.get("rebuttals", [])
    point_verdicts = []

    for rb in rebuttals:
        adj_sev = rb.get("adjusted_severity", 0)
        orig_sev = rb.get("original_severity", adj_sev)
        rtype = rb.get("rebuttal_type", "CONCEDE")
        fid = rb.get("finding_id", "?")

        # Apply table
        if adj_sev <= 3:
            pv = "defense_wins"
            rule = f"adj_sev={adj_sev} ≤ 3 → defense_wins"
        elif rtype == "CONCEDE":
            pv = "critique_wins"
            rule = f"adj_sev={adj_sev}, CONCEDE → critique_wins"
        elif rtype == "DEFER":
            pv = "empirical_test_agreed"
            rule = f"adj_sev={adj_sev}, DEFER → empirical_test_agreed"
        elif rtype.startswith("REBUT") or rtype == "EXONERATE":
            if adj_sev >= 7:
                # High residual severity — even a rebuttal doesn't fully clear it
                pv = "empirical_test_agreed"
                rule = f"adj_sev={adj_sev} ≥ 7, {rtype} → empirical_test_agreed (high residual)"
            elif orig_sev >= 7:
                # FATAL finding partially rebutted to 4-6 — must reach ≤3 to exonerate
                pv = "empirical_test_agreed"
                rule = (f"adj_sev={adj_sev} (4-6), orig_sev={orig_sev} ≥ 7, {rtype} → "
                        f"empirical_test_agreed (FATAL not fully cleared)")
            else:
                pv = "defense_wins"
                rule = f"adj_sev={adj_sev}, orig_sev={orig_sev} < 7, {rtype} → defense_wins"
        else:
            pv = "critique_wins"
            rule = f"adj_sev={adj_sev}, unknown rebuttal_type={rtype} → critique_wins (conservative)"

        # Constitutional overrides
        if rtype == "CONCEDE" and adj_sev >= 7:
            pv = "critique_wins"
            rule = f"constitutional: CONCEDE + adj_sev={adj_sev} ≥ 7 → critique_wins"
        elif rtype == "DEFER" and adj_sev <= 3:
            pv = "defense_wins"
            rule = f"constitutional: DEFER + adj_sev={adj_sev} ≤ 3 → defense_wins"

        point_verdicts.append({
            "finding_id": fid,
            "adjusted_severity": adj_sev,
            "rebuttal_type": rtype,
            "point_verdict": pv,
            "rule_applied": rule,
        })

    # Case verdict by strict precedence
    if any(pv["point_verdict"] == "critique_wins" for pv in point_verdicts):
        n = sum(1 for pv in point_verdicts if pv["point_verdict"] == "critique_wins")
        case_verdict = "critique_wins"
        rationale = f"{n} point(s) reached critique_wins"
    elif any(pv["point_verdict"] == "empirical_test_agreed" for pv in point_verdicts):
        n = sum(1 for pv in point_verdicts if pv["point_verdict"] == "empirical_test_agreed")
        case_verdict = "empirical_test_agreed"
        rationale = f"{n} point(s) deferred; no critique_wins"
    else:
        case_verdict = "defense_wins"
        rationale = "all points resolved to defense_wins" if point_verdicts else "no advancing findings"

    return {
        "point_verdicts": point_verdicts,
        "case_verdict": case_verdict,
        "case_rationale": rationale,
        "preflight_checklist": [],
        "proposed_experiments": [],
    }


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------

async def run_one(
    case: dict,
    run_id: int,
    model_assignment: dict,
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    prompts: dict,
    config: Config,
    dry_run: bool,
) -> dict:
    """Execute one full critic → defender → adjudicator run for a single case."""
    case_id = case["case_id"]
    stratum = case.get("stratum") or case.get("category", "unknown")
    task_prompt = case["task_prompt"]

    if dry_run:
        console.print(
            f"  [dim]DRY RUN {case_id} run{run_id} | "
            f"critic={model_assignment['critic'][:20]}... "
            f"defender={model_assignment['defender'][:20]}...[/dim]"
        )
        return _dry_run_result(case, run_id, model_assignment)

    # Stage 1 — Critic
    critic_raw = await call_api(
        sem, client, model_assignment["critic"],
        prompts["critic"], build_critic_user_msg(task_prompt), config
    )
    critic_output = validate_critic_output(critic_raw)

    # Stage 2 — Defender (sees critic findings)
    defender_user_msg = build_defender_user_msg(task_prompt, critic_output)
    defender_raw = await call_api(
        sem, client, model_assignment["defender"],
        prompts["defender"], defender_user_msg, config
    )
    defender_output = validate_defender_output(defender_raw)

    # Verdict — derived deterministically from defender structured output
    adjudicator_output = derive_verdict(defender_output)

    return {
        "case_id": case_id,
        "stratum": stratum,
        "flaw_category": case.get("flaw_category"),
        "run_id": run_id,
        "model_assignments": model_assignment,
        "critic_output": critic_output,
        "defender_output": defender_output,
        "adjudicator_output": adjudicator_output,
    }


def _dry_run_result(case: dict, run_id: int, model_assignment: dict) -> dict:
    defender_output = {
        "rebuttals": [
            {"finding_id": "F1", "original_severity": 5,
             "rebuttal_type": "CONCEDE", "severity_adjustment": 0,
             "adjusted_severity": 5, "justification": "[DRY RUN]"}
        ],
        "overall_verdict": "critique_wins",
    }
    return {
        "case_id": case["case_id"],
        "stratum": case.get("stratum") or case.get("category", "unknown"),
        "flaw_category": case.get("flaw_category"),
        "run_id": run_id,
        "model_assignments": model_assignment,
        "critic_output": {
            "findings": [
                {"finding_id": "F1", "severity": 5, "severity_label": "MATERIAL",
                 "suppressed": False, "flaw_category": None,
                 "claim": "[DRY RUN]", "failure_mechanism": "[DRY RUN]",
                 "evidence_test": "[DRY RUN]"}
            ],
            "no_material_findings": False,
        },
        "defender_output": defender_output,
        "adjudicator_output": derive_verdict(defender_output),
    }


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def output_path(output_dir: Path, case_id: str, run_id: int) -> Path:
    return output_dir / f"{case_id}__run{run_id}.json"


def write_output(output_dir: Path, result: dict) -> None:
    """Write result JSON atomically via .tmp rename."""
    final = output_path(output_dir, result["case_id"], result["run_id"])
    tmp = final.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    os.rename(str(tmp), str(final))


def scan_completed(output_dir: Path) -> set[tuple[str, int]]:
    """Return set of (case_id, run_id) tuples already written to output_dir."""
    completed = set()
    for f in output_dir.glob("*.json"):
        parts = f.stem.split("__")
        if len(parts) == 2 and parts[1].startswith("run"):
            try:
                json.loads(f.read_text(encoding="utf-8"))
                completed.add((parts[0], int(parts[1][3:])))
            except (json.JSONDecodeError, ValueError):
                console.print(f"  [yellow]Skipping corrupt file: {f.name}[/yellow]")
    return completed


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

async def run_benchmark(
    cases: list[dict],
    output_dir: Path,
    runs: int,
    config: Config,
    dry_run: bool,
    max_concurrent: int,
    seeds: dict | None,
    model_gen,
) -> dict:
    """Run the full benchmark. Returns summary stats."""
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    sem = asyncio.Semaphore(max_concurrent)
    prompts = load_prompts()

    completed = scan_completed(output_dir) if not dry_run else set()
    all_tasks = []
    for case in cases:
        for run_id in range(runs):
            if (case["case_id"], run_id) not in completed:
                seed_entry = None
                if seeds:
                    seed_entry = seeds.get(case["case_id"], {}).get(str(run_id))
                    if not seed_entry:
                        console.print(
                            f"[yellow]WARN: No seed for {case['case_id']} run{run_id} "
                            f"— using random draw[/yellow]"
                        )
                model_assignment = seed_entry if seed_entry else assign_models(next(model_gen))
                all_tasks.append((case, run_id, model_assignment))

    if completed:
        console.print(f"[green]Resuming: {len(completed)} already completed[/green]")
    console.print(
        f"Tasks remaining: {len(all_tasks)} "
        f"({len(cases)} cases × {runs} runs − {len(completed)} completed)"
    )

    if not all_tasks:
        console.print("[green]All tasks already completed![/green]")
        return {"completed": len(completed), "failed": 0, "skipped": len(completed)}

    stats = {"completed": 0, "failed": 0, "skipped": len(completed)}

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]v8 Pipeline[/bold blue]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_bar = progress.add_task("running", total=len(all_tasks))

        async def process_one(case, run_id, model_assignment):
            try:
                result = await run_one(
                    case, run_id, model_assignment, sem, client, prompts, config, dry_run
                )
                if not dry_run:
                    write_output(output_dir, result)
                stats["completed"] += 1
            except Exception as exc:
                from rich.markup import escape as rich_escape
                console.print(
                    f"  [red]FAIL: {case['case_id']} run{run_id}: "
                    f"{type(exc).__name__}: {rich_escape(str(exc))}[/red]"
                )
                stats["failed"] += 1
            finally:
                progress.advance(task_bar)

        await asyncio.gather(*[
            process_one(case, run_id, model_assignment)
            for case, run_id, model_assignment in all_tasks
        ])

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="v8 Pipeline Runner — critic → defender → adjudicator via OpenRouter"
    )
    parser.add_argument("--cases", required=True,
                        help="Path to benchmark cases JSON (relative to experiment dir)")
    parser.add_argument("--output-dir", default="v8_raw_outputs",
                        help="Output directory for per-run JSON files (default: v8_raw_outputs)")
    parser.add_argument("--runs", type=int, default=3,
                        help="Runs per case (default: 3)")
    parser.add_argument("--max-concurrent", type=int, default=100,
                        help="Max concurrent API calls (default: 100)")
    parser.add_argument("--seed-file", default=None,
                        help="Fixed model seed file for canary iteration loop "
                             "(relative to experiment dir); omit for random draws")
    parser.add_argument("--temperature", type=float, default=1.0,
                        help="Sampling temperature (default: 1.0)")
    parser.add_argument("--timeout", type=float, default=180.0,
                        help="Per-request timeout in seconds (default: 180)")
    parser.add_argument("--retries", type=int, default=2,
                        help="Max retries per API call (default: 2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate schema and prompts without making API calls")
    args = parser.parse_args()

    if not args.dry_run and not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]ERROR: OPENROUTER_API_KEY not set[/red]")
        sys.exit(1)

    cases_path = EXPERIMENT_DIR / args.cases
    if not cases_path.exists():
        console.print(f"[red]ERROR: Cases file not found: {cases_path}[/red]")
        sys.exit(1)

    output_dir = EXPERIMENT_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    pool = load_model_pool()

    seeds = None
    if args.seed_file:
        seed_path = EXPERIMENT_DIR / args.seed_file
        if not seed_path.exists():
            console.print(f"[red]ERROR: Seed file not found: {seed_path}[/red]")
            sys.exit(1)
        seeds = load_seed_file(seed_path)
        console.print(f"[green]Using fixed model seeds from {seed_path.name}[/green]")

    config = Config(
        temperature=args.temperature,
        timeout=args.timeout,
        retries=args.retries,
    )

    console.rule("[bold blue]v8 Pipeline Runner[/bold blue]")
    console.print(f"Cases:       {len(cases)}")
    console.print(f"Runs:        {args.runs}")
    console.print(f"Pool:        {len(pool)} models")
    console.print(f"Seeds:       {'fixed (' + args.seed_file + ')' if seeds else 'random'}")
    console.print(f"Concurrency: {args.max_concurrent}")
    console.print(f"Temperature: {args.temperature}  |  Timeout: {args.timeout}s  |  Retries: {args.retries}")
    console.print(f"Output:      {output_dir}")
    if args.dry_run:
        console.print("[yellow]DRY RUN — no API calls[/yellow]")
    console.print()

    gen = model_generator(pool)
    stats = asyncio.run(
        run_benchmark(cases, output_dir, args.runs, config, args.dry_run,
                      args.max_concurrent, seeds, gen)
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
