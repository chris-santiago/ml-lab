# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai>=1.0",
#   "rich>=13.0",
# ]
# ///
"""
run_ensemble.py — v8 Ensemble Critic Protocol

Runs 3 independent critics on each case (concurrently), union-pools their
findings, then runs one defender against the pooled findings.

  Stage 1 — Critics ×3 (CRITIC.md):  3 concurrent critic calls, different models
  Stage 2 — Pool findings:            union of all non-suppressed findings,
                                      deduplicated by flaw_category + severity bucket
  Stage 3 — Defender (DEFENDER.md):  single defender sees pooled findings
  Verdict — derive_verdict():         deterministic, same as run_pipeline.py

Hypothesis:
  On flawed cases: 3 critics independently flag the real flaw → pooled findings
  have high-severity consensus → harder for defender to rebut.
  On sound cases: critics diverge (find different minor concerns) → pooled findings
  have more volume but lower per-finding severity → defender rebuts more easily.

Usage:
  uv run scripts/run_ensemble.py \\
    --cases canary_cases.json \\
    --seed-file probe_run3_seeds.json \\
    --output-dir v8_raw_outputs/ensemble_probe \\
    --max-concurrent 100

  # Dry run
  uv run scripts/run_ensemble.py --cases canary_cases.json --dry-run
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
    if not MODELS_FILE.exists():
        console.print(f"[red]ERROR: models.json not found: {MODELS_FILE}[/red]")
        sys.exit(1)
    return _ms_load(MODELS_FILE)


def load_seed_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Shared parsing/validation utilities (same as run_pipeline.py)
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


def validate_critic_output(data: dict) -> dict:
    if "findings" not in data:
        raise ValueError("Critic output missing 'findings' array")
    for f in data["findings"]:
        for field in ("finding_id", "severity", "severity_label", "suppressed"):
            if field not in f:
                raise ValueError(f"Finding missing required field '{field}': {f}")
    return data


def validate_defender_output(data: dict) -> dict:
    if "rebuttals" not in data:
        raise ValueError("Defender output missing 'rebuttals' array")
    if "overall_verdict" not in data:
        raise ValueError("Defender output missing 'overall_verdict'")
    for r in data["rebuttals"]:
        for field in ("finding_id", "rebuttal_type", "adjusted_severity"):
            if field not in r:
                raise ValueError(f"Rebuttal missing required field '{field}': {r}")
        if isinstance(r.get("adjusted_severity"), (int, float)):
            r["adjusted_severity"] = max(0, r["adjusted_severity"])
    return data


# ---------------------------------------------------------------------------
# Verdict derivation (identical to run_pipeline.py — no citation changes)
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
# Finding pool logic
# ---------------------------------------------------------------------------

def pool_findings(critic_outputs: list[dict]) -> list[dict]:
    """Union-pool findings from multiple critics.

    Strategy: collect all non-suppressed findings from all critics,
    renumber sequentially (EF1, EF2, ...), and annotate each with which
    critic it came from. Preserves all findings — no deduplication —
    so the defender sees the full ensemble signal.

    The defender prompt is designed to handle repeated findings across critics
    by recognizing common root causes.
    """
    pooled = []
    seq = 1
    for critic_idx, output in enumerate(critic_outputs):
        for f in output.get("findings", []):
            if not f.get("suppressed", False):
                entry = dict(f)
                entry["finding_id"] = f"EF{seq}"
                entry["_source_critic"] = critic_idx
                entry["_original_finding_id"] = f.get("finding_id", "?")
                pooled.append(entry)
                seq += 1
    return pooled


def build_critic_user_msg(task_prompt: str) -> str:
    return (
        "## Proof-of-Concept Under Review\n\n"
        "The following is the complete proof-of-concept for this ML investigation. "
        "It includes the hypothesis, experiment design, and methodology. "
        "There is no separate implementation code file — the experiment design document "
        "below IS the full PoC. Review it for methodology flaws.\n\n"
        f"{task_prompt}"
    )


def build_ensemble_defender_user_msg(task_prompt: str, pooled_findings: list[dict]) -> str:
    """Build defender user message showing ensemble-pooled findings."""
    findings_json = json.dumps(pooled_findings, indent=2)
    n_critics = len({f.get("_source_critic") for f in pooled_findings})
    return (
        f"## Methodology Under Review\n\n{task_prompt}\n\n"
        f"## Ensemble Critic Findings ({n_critics} independent critics — findings union-pooled)\n\n"
        f"The following findings come from {n_critics} independent critics reviewing the "
        f"same methodology. Findings with overlapping root causes from different critics "
        f"represent stronger consensus. Produce a single structured rebuttal covering all findings.\n\n"
        f"```json\n{findings_json}\n```\n\n"
        f"Produce your structured rebuttal JSON as specified in your instructions."
    )


# ---------------------------------------------------------------------------
# Single ensemble run
# ---------------------------------------------------------------------------

async def run_one_ensemble(
    case: dict,
    run_id: int,
    model_assignment: dict,
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    prompts: dict,
    config: Config,
    dry_run: bool,
    critic_models: list[str],
) -> dict:
    case_id = case["case_id"]
    stratum = case.get("stratum") or case.get("category", "unknown")
    task_prompt = case["task_prompt"]

    if dry_run:
        console.print(
            f"  [dim]DRY RUN {case_id} run{run_id} | "
            f"critics={[m[:20] for m in critic_models]} "
            f"defender={model_assignment['defender'][:20]}[/dim]"
        )
        return _dry_run_result(case, run_id, model_assignment, critic_models)

    # Stage 1 — 3 concurrent critic calls
    console.print(f"  [dim]{case_id} run{run_id} → Stage 1 (Ensemble Critics ×{len(critic_models)})[/dim]")
    critic_user_msg = build_critic_user_msg(task_prompt)
    critic_tasks = [
        call_api(sem, client, m, prompts["critic"], critic_user_msg, config)
        for m in critic_models
    ]
    raw_results = await asyncio.gather(*critic_tasks, return_exceptions=True)

    critic_outputs = []
    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            console.print(
                f"  [yellow]Critic {i} ({critic_models[i]}) failed: "
                f"{type(result).__name__}: {rich_escape(str(result))} — skipping[/yellow]"
            )
            critic_outputs.append({"findings": [], "no_material_findings": True, "_failed": True})
        else:
            try:
                critic_outputs.append(validate_critic_output(result))
            except ValueError as e:
                console.print(f"  [yellow]Critic {i} validation failed: {e} — skipping[/yellow]")
                critic_outputs.append({"findings": [], "no_material_findings": True, "_failed": True})

    # Pool findings
    pooled_findings = pool_findings(critic_outputs)
    console.print(
        f"  [dim]{case_id} run{run_id}: pooled {len(pooled_findings)} findings "
        f"from {len(critic_outputs)} critics[/dim]"
    )

    # Early exit if no material findings after pooling
    if not pooled_findings:
        console.print(f"  [green]{case_id} run{run_id}: no pooled findings → defense_wins[/green]")
        adjudicator_output = {
            "point_verdicts": [],
            "case_verdict": "defense_wins",
            "case_rationale": "no advancing findings from ensemble critics",
            "preflight_checklist": [],
            "proposed_experiments": [],
        }
        return {
            "case_id": case_id,
            "stratum": stratum,
            "flaw_category": case.get("flaw_category"),
            "run_id": run_id,
            "model_assignments": {**model_assignment, "critics": critic_models},
            "critic_outputs": critic_outputs,
            "pooled_findings": pooled_findings,
            "defender_output": None,
            "critic_output": {"findings": [], "no_material_findings": True},
            "adjudicator_output": adjudicator_output,
            "ensemble": True,
        }

    # Stage 2 — Single defender on pooled findings
    console.print(f"  [dim]{case_id} run{run_id} → Stage 2 (Defender on pooled findings)[/dim]")
    defender_raw = await call_api(
        sem, client, model_assignment["defender"],
        prompts["defender"],
        build_ensemble_defender_user_msg(task_prompt, pooled_findings),
        config,
    )
    defender_output = validate_defender_output(defender_raw)

    # Verdict
    adjudicator_output = derive_verdict(defender_output)

    return {
        "case_id": case_id,
        "stratum": stratum,
        "flaw_category": case.get("flaw_category"),
        "run_id": run_id,
        "model_assignments": {**model_assignment, "critics": critic_models},
        "critic_outputs": critic_outputs,
        "pooled_findings": pooled_findings,
        # scorer.py compatibility fields
        "critic_output": {"findings": pooled_findings, "no_material_findings": len(pooled_findings) == 0},
        "defender_output": defender_output,
        "adjudicator_output": adjudicator_output,
        "ensemble": True,
    }


def _dry_run_result(
    case: dict,
    run_id: int,
    model_assignment: dict,
    critic_models: list[str],
) -> dict:
    defender_output = {
        "rebuttals": [
            {"finding_id": "EF1", "original_severity": 5,
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
        "model_assignments": {**model_assignment, "critics": critic_models},
        "critic_outputs": [{"findings": [], "no_material_findings": True}] * len(critic_models),
        "pooled_findings": [],
        "critic_output": {"findings": [], "no_material_findings": True},
        "defender_output": defender_output,
        "adjudicator_output": derive_verdict(defender_output),
        "ensemble": True,
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
# Summary
# ---------------------------------------------------------------------------

def print_summary(output_dir: Path, cases: list[dict]) -> None:
    case_lookup = {c["case_id"]: c for c in cases}
    results_by_case: dict[str, list] = {}

    for f in sorted(output_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cid = data.get("case_id", "?")
            verdict = data.get("adjudicator_output", {}).get("case_verdict", "?")
            n_findings = len(data.get("pooled_findings", []))
            results_by_case.setdefault(cid, []).append((verdict, n_findings))
        except Exception:
            pass

    console.print("\n[bold]Ensemble Results Summary[/bold]")
    console.print(f"{'Case ID':<30} {'GT':<15} {'Verdicts (pooled findings)':}")
    console.print("-" * 90)
    for case_id, runs in sorted(results_by_case.items()):
        gt = case_lookup.get(case_id, {}).get("ground_truth", {}).get("correct_position", "?")
        v_str = ", ".join(f"{v}({n})" for v, n in runs)
        verdicts = [v for v, _ in runs]
        match_sym = "[green]✓[/green]" if all(v == gt for v in verdicts) else "[red]✗[/red]"
        console.print(f"{case_id:<30} {gt:<15} {v_str} {match_sym}")


# ---------------------------------------------------------------------------
# Model assignment for ensemble: critic pool uses 3 models per run
# ---------------------------------------------------------------------------

def pick_ensemble_models(
    seed_entry: dict | None,
    model_pool: list[str],
    run_id: int,
    case_id: str,
) -> tuple[list[str], str]:
    """Return (list_of_3_critic_models, defender_model).

    If seed_entry exists, uses seed critic + 2 additional models drawn
    from the pool (deterministically by position to avoid duplicates).
    The defender is always from the seed if available.
    """
    if seed_entry:
        seed_critic = seed_entry.get("critic")
        defender = seed_entry.get("defender")
        # Pick 2 additional critics from pool, skipping seed_critic and defender
        additional = [m for m in model_pool if m != seed_critic and m != defender]
        # Use run_id and case_id hash for deterministic picks
        import hashlib
        h = int(hashlib.sha256(f"{case_id}:{run_id}".encode()).hexdigest(), 16)
        idx1 = h % len(additional)
        idx2 = (h // len(additional)) % len(additional)
        if idx2 == idx1:
            idx2 = (idx2 + 1) % len(additional)
        critic_models = [seed_critic, additional[idx1], additional[idx2]]
        return critic_models, defender
    else:
        # Random draw: 3 critics + 1 defender (4 unique models)
        from random import sample
        pool = sample(model_pool, min(4, len(model_pool)))
        return pool[:3], pool[3] if len(pool) > 3 else pool[0]


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
    model_pool: list[str],
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
                critic_models, defender_model = pick_ensemble_models(
                    seed_entry, model_pool, run_id, case["case_id"]
                )
                model_assignment = {
                    "critic": critic_models[0],
                    "defender": defender_model,
                    "adjudicator": "derived",
                }
                all_tasks.append((case, run_id, model_assignment, critic_models))

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
        TextColumn("[bold blue]v8 Ensemble[/bold blue]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_bar = progress.add_task("running", total=len(all_tasks))

        async def process_one(case, run_id, model_assignment, critic_models):
            try:
                result = await run_one_ensemble(
                    case, run_id, model_assignment, sem, client, prompts,
                    config, dry_run, critic_models
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
            process_one(case, run_id, model_assignment, critic_models)
            for case, run_id, model_assignment, critic_models in all_tasks
        ])

    return stats


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="v8 Ensemble Critic Protocol")
    parser.add_argument("--cases", required=True, help="Path to cases JSON file")
    parser.add_argument("--output-dir", default="v8_raw_outputs/ensemble")
    parser.add_argument("--seed-file", help="Fixed model assignments JSON (reused for critic seed)")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-concurrent", type=int, default=100)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
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

    model_pool = (
        load_model_pool() if not args.dry_run
        else [f"mock-model-{c}" for c in "abcdefghij"]
    )

    console.print(f"[bold]v8 Ensemble Protocol[/bold]")
    console.print(f"Cases: {len(all_cases)} | Runs: {args.runs} | Output: {output_dir}")
    console.print(f"Stages: Critics ×3 (concurrent) → pool findings → Defender → derive_verdict()")
    console.print(f"Max concurrent: {args.max_concurrent} | Temperature: {config.temperature}")

    stats = asyncio.run(run_benchmark(
        cases=all_cases,
        output_dir=output_dir,
        runs=args.runs,
        config=config,
        dry_run=args.dry_run,
        max_concurrent=args.max_concurrent,
        seeds=seeds,
        model_pool=model_pool,
    ))

    console.print(f"\n[bold]Done.[/bold] Completed: {stats['completed']} | Failed: {stats['failed']}")

    if not args.dry_run:
        print_summary(output_dir, all_cases)


if __name__ == "__main__":
    main()
