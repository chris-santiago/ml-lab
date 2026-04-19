# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
run_multiround.py — v8 Multi-Round Debate Pipeline

Runs a 4-stage debate protocol on a set of benchmark cases:

  Stage 1 — Critic R1   (CRITIC.md):      hypothesis → structured findings
  Stage 2 — Defender R1 (DEFENDER.md):    findings → rebuttals + cited_text
  Stage 3 — Critic R2   (CRITIC_R2.md):   rebuttals → citation challenges (ACCEPT/CHALLENGE/PARTIAL)
  Stage 4 — Defender R2 (DEFENDER_R2.md): challenges → final rebuttals
  Verdict — derive_verdict():             deterministic, from Defender R2 output

The hypothesis: on flawed cases, R2 critic challenges fabricated/tangential citations,
forcing the R2 defender to concede. On sound cases, citations hold up, so R2 defender
output is near-identical to R1.

Usage:
  uv run scripts/run_multiround.py \\
    --cases canary_cases.json \\
    --seed-file probe_run3_seeds.json \\
    --output-dir v8_raw_outputs/multiround \\
    --max-concurrent 20

  # Dry run (validates setup, no API calls)
  uv run scripts/run_multiround.py --cases canary_cases.json --dry-run
"""

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from model_selector import load as _ms_load, model_generator  # noqa: E402

from openai import AsyncOpenAI
from rich.console import Console
from rich.markup import escape as rich_escape
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
    prompts = {}
    for name in ["CRITIC", "DEFENDER", "CRITIC_R2", "DEFENDER_R2"]:
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
    if not MODELS_FILE.exists():
        console.print(f"[red]ERROR: models.json not found: {MODELS_FILE}[/red]")
        sys.exit(1)
    return _ms_load(MODELS_FILE)


def load_seed_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Response parsing (shared with run_pipeline.py)
# ---------------------------------------------------------------------------

def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _sanitize_json_string(text: str) -> str:
    text = re.sub(r'(?<!\\)\n', r'\\n', text)
    text = re.sub(r'(?<!\\)\r', r'\\r', text)
    text = re.sub(r'(?<!\\)\t', r'\\t', text)
    return text


def extract_json(text: str) -> dict:
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
    if not raw_text:
        raise ValueError("Empty response from API")
    try:
        return extract_json(raw_text)
    except (json.JSONDecodeError, ValueError) as e:
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
    if "findings" not in data:
        raise ValueError("Critic output missing 'findings' array")
    for f in data["findings"]:
        for field in ("finding_id", "severity", "severity_label", "suppressed"):
            if field not in f:
                raise ValueError(f"Finding missing required field '{field}': {f}")
    return data


def validate_defender_output(data: dict, stage_label: str = "Defender") -> dict:
    if "rebuttals" not in data:
        raise ValueError(f"{stage_label} output missing 'rebuttals' array")
    if "overall_verdict" not in data:
        raise ValueError(f"{stage_label} output missing 'overall_verdict'")
    for r in data["rebuttals"]:
        for field in ("finding_id", "rebuttal_type", "adjusted_severity"):
            if field not in r:
                raise ValueError(f"Rebuttal missing required field '{field}': {r}")
        if isinstance(r.get("adjusted_severity"), (int, float)):
            r["adjusted_severity"] = max(0, r["adjusted_severity"])
    return data


def validate_critic_r2_output(data: dict) -> dict:
    if "challenges" not in data:
        raise ValueError("Critic R2 output missing 'challenges' array")
    for c in data["challenges"]:
        for field in ("finding_id", "challenge_verdict", "updated_severity"):
            if field not in c:
                raise ValueError(f"Challenge missing required field '{field}': {c}")
        if c.get("challenge_verdict") not in ("ACCEPT", "CHALLENGE", "PARTIAL"):
            console.print(
                f"  [yellow]WARN: challenge_verdict '{c.get('challenge_verdict')}' "
                f"not in (ACCEPT, CHALLENGE, PARTIAL)[/yellow]"
            )
    return data


# ---------------------------------------------------------------------------
# Verdict derivation (identical to run_pipeline.py)
# ---------------------------------------------------------------------------

def derive_verdict(defender_output: dict) -> dict:
    rebuttals = defender_output.get("rebuttals", [])
    point_verdicts = []

    for rb in rebuttals:
        adj_sev = rb.get("adjusted_severity", 0)
        orig_sev = rb.get("original_severity", adj_sev)
        rtype = rb.get("rebuttal_type", "CONCEDE")
        fid = rb.get("finding_id", "?")

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
                pv = "empirical_test_agreed"
                rule = f"adj_sev={adj_sev} ≥ 7, {rtype} → empirical_test_agreed (high residual)"
            elif orig_sev >= 7:
                pv = "empirical_test_agreed"
                rule = (f"adj_sev={adj_sev} (4-6), orig_sev={orig_sev} ≥ 7, {rtype} → "
                        f"empirical_test_agreed (FATAL not fully cleared)")
            else:
                pv = "defense_wins"
                rule = f"adj_sev={adj_sev}, orig_sev={orig_sev} < 7, {rtype} → defense_wins"
        else:
            pv = "critique_wins"
            rule = f"adj_sev={adj_sev}, unknown rebuttal_type={rtype} → critique_wins (conservative)"

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
                    f"after {wait:.0f}s: {type(exc).__name__}: {rich_escape(str(exc))}[/yellow]"
                )
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("call_api: exhausted retries without success or exception")


# ---------------------------------------------------------------------------
# User message builders
# ---------------------------------------------------------------------------

def build_critic_user_msg(task_prompt: str) -> str:
    return (
        "## Proof-of-Concept Under Review\n\n"
        "The following is the complete proof-of-concept for this ML investigation. "
        "It includes the hypothesis, experiment design, and methodology. "
        "There is no separate implementation code file — the experiment design document "
        "below IS the full PoC. Review it for methodology flaws.\n\n"
        f"{task_prompt}"
    )


def build_defender_r1_user_msg(task_prompt: str, critic_output: dict) -> str:
    advancing = [f for f in critic_output.get("findings", []) if not f.get("suppressed", False)]
    findings_json = json.dumps(advancing, indent=2)
    return (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Critic Findings (FATAL, MATERIAL, and MINOR only — NIT suppressed)\n\n"
        f"```json\n{findings_json}\n```\n\n"
        f"Produce your structured rebuttal JSON as specified in your instructions."
    )


def build_critic_r2_user_msg(
    task_prompt: str,
    critic_r1_output: dict,
    defender_r1_output: dict,
) -> str:
    """Build R2 critic message: original findings + defender R1 rebuttals including cited_text."""
    advancing = [f for f in critic_r1_output.get("findings", []) if not f.get("suppressed", False)]
    rebuttals = defender_r1_output.get("rebuttals", [])

    findings_json = json.dumps(advancing, indent=2)
    rebuttals_json = json.dumps(rebuttals, indent=2)

    return (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Your Original Findings (R1)\n\n"
        f"```json\n{findings_json}\n```\n\n"
        f"## Defender R1 Rebuttals (including cited_text)\n\n"
        f"```json\n{rebuttals_json}\n```\n\n"
        f"For each finding where the defender used REBUT-DESIGN or REBUT-SCOPE, evaluate "
        f"the `cited_text` field. Does it directly address the specific failure mechanism "
        f"you identified? Produce your structured challenge JSON as specified."
    )


def build_defender_r2_user_msg(
    task_prompt: str,
    critic_r1_output: dict,
    defender_r1_output: dict,
    critic_r2_output: dict,
) -> str:
    """Build R2 defender message: original findings + R1 rebuttals + R2 challenges."""
    advancing = [f for f in critic_r1_output.get("findings", []) if not f.get("suppressed", False)]
    rebuttals = defender_r1_output.get("rebuttals", [])
    challenges = critic_r2_output.get("challenges", [])

    findings_json = json.dumps(advancing, indent=2)
    rebuttals_json = json.dumps(rebuttals, indent=2)
    challenges_json = json.dumps(challenges, indent=2)

    return (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Original Critic Findings (R1)\n\n"
        f"```json\n{findings_json}\n```\n\n"
        f"## Your R1 Rebuttals\n\n"
        f"```json\n{rebuttals_json}\n```\n\n"
        f"## Critic R2 Challenges (citation review)\n\n"
        f"```json\n{challenges_json}\n```\n\n"
        f"The critic has reviewed your citations. For each CHALLENGE or PARTIAL verdict, "
        f"you must either defend your citation with a stronger argument, provide a better "
        f"verbatim quote, or concede if no direct design control exists. "
        f"Produce your final structured rebuttal JSON as specified."
    )


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
    case_id = case["case_id"]
    stratum = case.get("stratum") or case.get("category", "unknown")
    task_prompt = case["task_prompt"]

    if dry_run:
        console.print(
            f"  [dim]DRY RUN {case_id} run{run_id} | "
            f"critic={model_assignment['critic'][:25]} "
            f"defender={model_assignment['defender'][:25]}[/dim]"
        )
        return _dry_run_result(case, run_id, model_assignment)

    # Stage 1 — Critic R1
    console.print(f"  [dim]{case_id} run{run_id} → Stage 1 (Critic R1)[/dim]")
    critic_r1_raw = await call_api(
        sem, client, model_assignment["critic"],
        prompts["critic"], build_critic_user_msg(task_prompt), config
    )
    critic_r1_output = validate_critic_output(critic_r1_raw)

    # Early exit if no material findings
    advancing = [f for f in critic_r1_output.get("findings", []) if not f.get("suppressed", False)]
    if not advancing:
        console.print(f"  [green]{case_id} run{run_id}: no material findings → defense_wins (short-circuit)[/green]")
        adjudicator_output = {
            "point_verdicts": [],
            "case_verdict": "defense_wins",
            "case_rationale": "no advancing findings from critic R1",
            "preflight_checklist": [],
            "proposed_experiments": [],
        }
        return {
            "case_id": case_id,
            "stratum": stratum,
            "flaw_category": case.get("flaw_category"),
            "run_id": run_id,
            "model_assignments": model_assignment,
            "critic_r1_output": critic_r1_output,
            "defender_r1_output": None,
            "critic_r2_output": None,
            "defender_r2_output": None,
            "adjudicator_output": adjudicator_output,
            "multiround": True,
        }

    # Stage 2 — Defender R1
    console.print(f"  [dim]{case_id} run{run_id} → Stage 2 (Defender R1)[/dim]")
    defender_r1_raw = await call_api(
        sem, client, model_assignment["defender"],
        prompts["defender"], build_defender_r1_user_msg(task_prompt, critic_r1_output), config
    )
    defender_r1_output = validate_defender_output(defender_r1_raw, stage_label="Defender R1")

    # Stage 3 — Critic R2 (citation challenge)
    console.print(f"  [dim]{case_id} run{run_id} → Stage 3 (Critic R2)[/dim]")
    critic_r2_raw = await call_api(
        sem, client, model_assignment["critic"],
        prompts["critic_r2"],
        build_critic_r2_user_msg(task_prompt, critic_r1_output, defender_r1_output),
        config,
    )
    critic_r2_output = validate_critic_r2_output(critic_r2_raw)

    # Stage 4 — Defender R2 (final rebuttals)
    console.print(f"  [dim]{case_id} run{run_id} → Stage 4 (Defender R2)[/dim]")
    defender_r2_raw = await call_api(
        sem, client, model_assignment["defender"],
        prompts["defender_r2"],
        build_defender_r2_user_msg(
            task_prompt, critic_r1_output, defender_r1_output, critic_r2_output
        ),
        config,
    )
    defender_r2_output = validate_defender_output(defender_r2_raw, stage_label="Defender R2")

    # Verdict — derived from Defender R2 output
    adjudicator_output = derive_verdict(defender_r2_output)

    return {
        "case_id": case_id,
        "stratum": stratum,
        "flaw_category": case.get("flaw_category"),
        "run_id": run_id,
        "model_assignments": model_assignment,
        "critic_r1_output": critic_r1_output,
        "defender_r1_output": defender_r1_output,
        "critic_r2_output": critic_r2_output,
        "defender_r2_output": defender_r2_output,
        # scorer.py reads adjudicator_output.case_verdict — this field is kept for compatibility
        "critic_output": critic_r1_output,
        "defender_output": defender_r2_output,
        "adjudicator_output": adjudicator_output,
        "multiround": True,
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
        "critic_r1_output": {"findings": [], "no_material_findings": True},
        "defender_r1_output": defender_output,
        "critic_r2_output": {"challenges": []},
        "defender_r2_output": defender_output,
        "critic_output": {"findings": [], "no_material_findings": True},
        "defender_output": defender_output,
        "adjudicator_output": derive_verdict(defender_output),
        "multiround": True,
    }


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def output_path(output_dir: Path, case_id: str, run_id: int) -> Path:
    return output_dir / f"{case_id}__run{run_id}.json"


def write_output(output_dir: Path, result: dict) -> None:
    final = output_path(output_dir, result["case_id"], result["run_id"])
    tmp = final.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    os.rename(str(tmp), str(final))


def scan_completed(output_dir: Path) -> set[tuple[str, int]]:
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
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(output_dir: Path, cases: list[dict]) -> None:
    """Print a per-case verdict summary from written output files."""
    case_lookup = {c["case_id"]: c for c in cases}
    results_by_case: dict[str, list[str]] = {}

    for f in sorted(output_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cid = data.get("case_id", "?")
            verdict = data.get("adjudicator_output", {}).get("case_verdict", "?")
            results_by_case.setdefault(cid, []).append(verdict)
        except Exception:
            pass

    console.print("\n[bold]Multi-Round Results Summary[/bold]")
    console.print(f"{'Case ID':<30} {'GT':<15} {'Verdicts'}")
    console.print("-" * 80)
    for case_id, verdicts in sorted(results_by_case.items()):
        gt = case_lookup.get(case_id, {}).get("ground_truth", {}).get("correct_position", "?")
        v_str = ", ".join(verdicts)
        match_sym = "[green]✓[/green]" if all(v == gt for v in verdicts) else "[red]✗[/red]"
        console.print(f"{case_id:<30} {gt:<15} {v_str} {match_sym}")


# ---------------------------------------------------------------------------
# Main loop
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
                if seed_entry:
                    model_assignment = seed_entry
                else:
                    draw = next(model_gen)
                    model_assignment = {
                        "critic": draw[0],
                        "defender": draw[1],
                        "adjudicator": draw[2] if len(draw) > 2 else "derived",
                    }
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
        TextColumn("[bold blue]v8 Multi-Round[/bold blue]"),
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
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="v8 Multi-Round Debate Pipeline")
    parser.add_argument("--cases", required=True, help="Path to cases JSON file")
    parser.add_argument("--output-dir", default="v8_raw_outputs/multiround")
    parser.add_argument("--seed-file", help="Fixed model assignments JSON")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-concurrent", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-only", action="store_true",
                        help="Print summary of existing outputs without running anything")
    args = parser.parse_args()

    cases_path = EXPERIMENT_DIR / args.cases
    if not cases_path.exists():
        cases_path = Path(args.cases)
    if not cases_path.exists():
        console.print(f"[red]ERROR: Cases file not found: {args.cases}[/red]")
        sys.exit(1)

    all_cases = json.loads(cases_path.read_text(encoding="utf-8"))
    seeds = None
    if args.seed_file:
        seed_path = EXPERIMENT_DIR / args.seed_file
        if not seed_path.exists():
            seed_path = Path(args.seed_file)
        seeds = load_seed_file(seed_path)
        # Filter cases to only those in the seed file
        seed_case_ids = set(seeds.keys())
        filtered = [c for c in all_cases if c["case_id"] in seed_case_ids]
        console.print(
            f"Seed file: {len(seed_case_ids)} cases → filtered from {len(all_cases)} to {len(filtered)}"
        )
        all_cases = filtered

    output_dir = EXPERIMENT_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.summary_only:
        print_summary(output_dir, all_cases)
        return

    if not args.dry_run and "OPENROUTER_API_KEY" not in os.environ:
        console.print("[red]ERROR: OPENROUTER_API_KEY not set[/red]")
        sys.exit(1)

    config = Config(
        temperature=args.temperature,
        timeout=args.timeout,
        retries=args.retries,
    )

    model_pool = load_model_pool() if not args.dry_run else ["mock-model-a", "mock-model-b", "mock-model-c"]
    model_gen = model_generator(model_pool, n=2)

    console.print(f"[bold]v8 Multi-Round Pipeline[/bold]")
    console.print(f"Cases: {len(all_cases)} | Runs: {args.runs} | Output: {output_dir}")
    console.print(f"Stages: Critic R1 → Defender R1 → Critic R2 → Defender R2 → derive_verdict()")
    console.print(f"Max concurrent: {args.max_concurrent} | Temperature: {config.temperature}")

    stats = asyncio.run(run_benchmark(
        cases=all_cases,
        output_dir=output_dir,
        runs=args.runs,
        config=config,
        dry_run=args.dry_run,
        max_concurrent=args.max_concurrent,
        seeds=seeds,
        model_gen=model_gen,
    ))

    console.print(f"\n[bold]Done.[/bold] Completed: {stats['completed']} | Failed: {stats['failed']}")

    if not args.dry_run:
        print_summary(output_dir, all_cases)


if __name__ == "__main__":
    main()
