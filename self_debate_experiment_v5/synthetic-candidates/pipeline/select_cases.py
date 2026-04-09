# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.0"]
# ///
"""
Post-hoc stratified case selection for the debate protocol.

Balances across (correct_verdict × corruption_tier × domain × ml_task_type)
to enable meaningful within-group statistics.

Primary strata:
  defense_wins / tier=0
  critique     / tier=1
  critique     / tier=2
  critique     / tier=3+

Within each stratum: round-robin across domains (then ml_task_types within domain).
Ranked by proxy_mean ascending — harder cases (Sonnet wrong) preferred.
Proxy_mean is read from _pipeline.proxy_mean if embedded; otherwise treats all
cases as equal difficulty (proxy=0.5).

Usage:
    uv run pipeline/select_cases.py --input cases_100-199.json --per-stratum 15
    uv run pipeline/select_cases.py --input cases_100-199.json --n 60
    uv run pipeline/select_cases.py --input cases_100-199.json --n 60 --min-proxy 0.0 --max-proxy 0.85

Output:
    selected_cases_100-199.json  (same dir as input, unless --output given)
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def corruption_tier(case: dict) -> str:
    n = case.get("_pipeline", {}).get("num_corruptions") or case.get("num_corruptions", 0)
    if n is None or n == 0:
        return "0"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    return "3+"


def proxy_score(case: dict) -> float:
    """Lower is harder. Missing → 0.5 (unknown, treated as middle difficulty)."""
    v = case.get("_pipeline", {}).get("proxy_mean")
    return v if v is not None else 0.5


# ---------------------------------------------------------------------------
# Selection algorithm
# ---------------------------------------------------------------------------

def interleave_by_task(cases: list[dict], rng: random.Random) -> list[dict]:
    """Re-order a list of cases to alternate ml_task_types."""
    by_task: dict[str, list] = defaultdict(list)
    for c in cases:
        by_task[c.get("ml_task_type", "unknown")].append(c)
    task_keys = list(by_task.keys())
    rng.shuffle(task_keys)
    result: list[dict] = []
    iters = {t: iter(cs) for t, cs in by_task.items()}
    while iters:
        done = []
        for t in task_keys:
            if t not in iters:
                continue
            try:
                result.append(next(iters[t]))
            except StopIteration:
                done.append(t)
        for t in done:
            del iters[t]
            task_keys.remove(t)
    return result


def round_robin_domains(by_domain: dict[str, list], target: int, rng: random.Random) -> list[dict]:
    """Pick `target` cases by cycling across domains."""
    domains = list(by_domain.keys())
    rng.shuffle(domains)
    iters = {d: iter(cs) for d, cs in by_domain.items()}
    chosen: list[dict] = []
    while len(chosen) < target:
        made_progress = False
        stale = []
        for d in domains:
            if len(chosen) >= target:
                break
            if d not in iters:
                continue
            try:
                chosen.append(next(iters[d]))
                made_progress = True
            except StopIteration:
                stale.append(d)
        for d in stale:
            del iters[d]
            domains.remove(d)
        if not made_progress:
            break  # all domains exhausted
    return chosen


def select(
    cases: list[dict],
    per_stratum: int | None,
    n_total: int | None,
    min_proxy: float,
    max_proxy: float,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)

    # Optional difficulty filter
    pool = [c for c in cases if min_proxy <= proxy_score(c) <= max_proxy]
    if len(pool) < len(cases):
        console.print(
            f"  [dim]Difficulty filter [{min_proxy:.2f}, {max_proxy:.2f}]: "
            f"{len(pool)}/{len(cases)} cases kept[/dim]"
        )

    # Group into primary strata
    strata: dict[tuple, list] = defaultdict(list)
    for case in pool:
        verdict = case.get("correct_verdict", "unknown")
        tier = corruption_tier(case)
        strata[(verdict, tier)].append(case)

    # Determine per-stratum target
    n_strata = len(strata)
    if per_stratum is None and n_total is not None:
        per_stratum = max(1, n_total // n_strata)
    elif per_stratum is None:
        per_stratum = 15

    selected: list[dict] = []
    for key in sorted(strata.keys()):
        verdict, tier = key
        stratum_cases = strata[key]

        # Sort by difficulty ascending (harder = lower proxy → debated more productively)
        stratum_cases.sort(key=proxy_score)

        # Within each domain: interleave by ml_task_type, maintaining proxy order
        by_domain: dict[str, list] = defaultdict(list)
        for c in stratum_cases:
            by_domain[c.get("domain", "unknown")].append(c)
        for domain in by_domain:
            by_domain[domain] = interleave_by_task(by_domain[domain], rng)

        chosen = round_robin_domains(by_domain, per_stratum, rng)
        selected.extend(chosen)

        proxies = [proxy_score(c) for c in chosen]
        avg_proxy = sum(proxies) / len(proxies) if proxies else 0.0
        domains_used = len({c.get("domain") for c in chosen})
        tasks_used = len({c.get("ml_task_type") for c in chosen})
        console.print(
            f"  [cyan]{verdict}[/cyan] / tier={tier}: "
            f"{len(chosen)}/{len(stratum_cases)} selected  "
            f"avg_proxy={avg_proxy:.3f}  "
            f"domains={domains_used}  tasks={tasks_used}"
        )

    return selected


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def summary_table(selected: list[dict], pool: list[dict]) -> None:
    avail: dict[tuple, int] = defaultdict(int)
    for c in pool:
        avail[(c.get("correct_verdict", "?"), corruption_tier(c))] += 1

    sel_groups: dict[tuple, list] = defaultdict(list)
    for c in selected:
        sel_groups[(c.get("correct_verdict", "?"), corruption_tier(c))].append(c)

    t = Table(title=f"Selection summary  (total selected: {len(selected)})")
    t.add_column("correct_verdict")
    t.add_column("corruption_tier", justify="center")
    t.add_column("selected", justify="right")
    t.add_column("available", justify="right")
    t.add_column("domains", justify="right")
    t.add_column("ml_task_types", justify="right")
    t.add_column("avg_proxy", justify="right")
    t.add_column("min_proxy", justify="right")

    for key in sorted(set(list(avail.keys()) + list(sel_groups.keys()))):
        verdict, tier = key
        group = sel_groups[key]
        n_sel = len(group)
        n_avail = avail[key]
        if n_sel == 0:
            t.add_row(verdict, tier, "0", str(n_avail), "-", "-", "-", "-")
            continue
        domains = len({c.get("domain") for c in group})
        tasks = len({c.get("ml_task_type") for c in group})
        proxies = [proxy_score(c) for c in group]
        avg_p = sum(proxies) / len(proxies)
        min_p = min(proxies)
        t.add_row(
            verdict, tier,
            str(n_sel), str(n_avail),
            str(domains), str(tasks),
            f"{avg_p:.3f}", f"{min_p:.3f}",
        )

    console.print(t)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="Path to assembled cases JSON file")
    p.add_argument("--output", default=None, help="Output path (default: selected_<input>)")
    p.add_argument(
        "--per-stratum", type=int, default=None,
        help="Cases per (verdict × tier) stratum (overrides --n)",
    )
    p.add_argument(
        "--n", type=int, default=None,
        help="Total target N — divided equally across strata",
    )
    p.add_argument(
        "--min-proxy", type=float, default=0.0,
        help="Minimum proxy_mean to include (0.0 = no lower bound)",
    )
    p.add_argument(
        "--max-proxy", type=float, default=1.0,
        help="Maximum proxy_mean to include (1.0 = include all; 0.85 = exclude trivial cases)",
    )
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    input_path = Path(args.input)
    cases: list[dict] = json.loads(input_path.read_text(encoding="utf-8"))
    console.print(f"Loaded {len(cases)} cases from {input_path.name}")

    has_proxy = sum(1 for c in cases if c.get("_pipeline", {}).get("proxy_mean") is not None)
    if has_proxy == 0:
        console.print(
            "[yellow]Warning: no proxy_mean found in _pipeline — all cases treated as equal difficulty (0.5).[/yellow]\n"
            "[dim]Re-run with the updated orchestrator to embed smoke scores at assembly time.[/dim]"
        )
    else:
        console.print(f"  proxy_mean available for {has_proxy}/{len(cases)} cases")

    console.print()
    selected = select(cases, args.per_stratum, args.n, args.min_proxy, args.max_proxy, args.seed)
    console.print()
    summary_table(selected, cases)

    out_path = Path(args.output) if args.output else input_path.parent / f"selected_{input_path.name}"
    out_path.write_text(json.dumps(selected, indent=2), encoding="utf-8")
    console.print(f"\n[green]Wrote {len(selected)} cases → {out_path}[/green]")


if __name__ == "__main__":
    main()
