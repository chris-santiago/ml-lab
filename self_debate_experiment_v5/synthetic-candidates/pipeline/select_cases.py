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
    # Auto-glob all cases_*.json from synthetic-candidates/ and merge (recommended)
    uv run pipeline/select_cases.py --per-stratum 15 --max-proxy 0.83

    # Single file
    uv run pipeline/select_cases.py --input cases_200-299.json --per-stratum 15
    uv run pipeline/select_cases.py --input cases_200-299.json --n 60 --max-proxy 0.85

Output:
    selected_cases_all.json      (when auto-globbing, written to synthetic-candidates/)
    selected_cases_200-299.json  (when --input given, same dir as input)
    Or override with --output.
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
    tier_targets: dict[str, int] | None = None,
) -> list[dict]:
    """
    tier_targets maps tier label → target count, overriding per_stratum for that tier.
    Keys: "0", "1", "2", "3+".  Set to 0 to skip a tier entirely.
    """
    rng = random.Random(seed)
    tier_targets = tier_targets or {}

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

    # Determine per-stratum default
    n_strata = len(strata)
    if per_stratum is None and n_total is not None:
        per_stratum = max(1, n_total // n_strata)
    elif per_stratum is None:
        per_stratum = 15

    selected: list[dict] = []
    for key in sorted(strata.keys()):
        verdict, tier = key
        stratum_cases = strata[key]

        target = tier_targets.get(tier, per_stratum)
        if target == 0:
            console.print(f"  [dim]{verdict} / tier={tier}: skipped (--tier-{tier} 0)[/dim]")
            continue

        # Sort by difficulty ascending (harder = lower proxy → debated more productively)
        stratum_cases.sort(key=proxy_score)

        # Within each domain: interleave by ml_task_type, maintaining proxy order
        by_domain: dict[str, list] = defaultdict(list)
        for c in stratum_cases:
            by_domain[c.get("domain", "unknown")].append(c)
        for domain in by_domain:
            by_domain[domain] = interleave_by_task(by_domain[domain], rng)

        chosen = round_robin_domains(by_domain, target, rng)
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

CASES_DIR = Path(__file__).parent.parent  # synthetic-candidates/


def load_inputs(patterns: list[str]) -> tuple[list[dict], Path]:
    """
    Resolve input patterns to a merged, deduplicated case list.
    Returns (cases, default_output_dir).

    If patterns is empty, auto-globs cases_*.json from CASES_DIR.
    Each pattern may be a literal path or a glob expression.
    Deduplicates by case_id — last file wins on collision.
    """
    if not patterns:
        paths = sorted(CASES_DIR.glob("cases_*.json"))
        if not paths:
            raise FileNotFoundError(f"No cases_*.json files found in {CASES_DIR}")
        auto_glob = True
    else:
        paths = []
        for pat in patterns:
            expanded = sorted(CASES_DIR.glob(pat)) or sorted(Path().glob(pat))
            if not expanded:
                # Try as a literal path
                p = Path(pat)
                if p.exists():
                    expanded = [p]
                else:
                    raise FileNotFoundError(f"No files matched: {pat}")
            paths.extend(expanded)
        auto_glob = False

    by_id: dict[str, dict] = {}
    for path in paths:
        batch = json.loads(path.read_text(encoding="utf-8"))
        for c in batch:
            by_id[c["case_id"]] = c
        console.print(f"  Loaded {len(batch):>4} cases ← {path.name}")

    cases = list(by_id.values())
    if len(paths) > 1:
        console.print(f"  [dim]Merged {len(paths)} files → {len(cases)} unique cases[/dim]")

    out_dir = CASES_DIR if auto_glob else paths[0].parent
    return cases, out_dir, auto_glob


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--input", nargs="*", default=None, metavar="PATH_OR_GLOB",
        help="Case file(s) or glob pattern (e.g. 'cases_*.json'). "
             "Omit to auto-glob all cases_*.json from synthetic-candidates/.",
    )
    p.add_argument("--output", default=None, help="Output path (default: selected_cases_all.json or selected_<input>)")
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
        help="Maximum proxy_mean to include (1.0 = include all; 0.83 = exclude trivial cases)",
    )
    p.add_argument("--seed", type=int, default=42)
    g = p.add_argument_group(
        "per-tier overrides",
        "Override --per-stratum for a specific tier. Set to 0 to skip that tier entirely.\n"
        "  --tier-0      defense_wins (sound designs)\n"
        "  --tier-1      critique, 1 flaw\n"
        "  --tier-2      critique, 2 flaws\n"
        "  --tier-many   critique, 3+ flaws",
    )
    g.add_argument("--tier-0",    type=int, default=None, metavar="N", dest="tier_0")
    g.add_argument("--tier-1",    type=int, default=None, metavar="N", dest="tier_1")
    g.add_argument("--tier-2",    type=int, default=None, metavar="N", dest="tier_2")
    g.add_argument("--tier-many", type=int, default=None, metavar="N", dest="tier_many")
    args = p.parse_args()

    tier_targets: dict[str, int] = {}
    if args.tier_0    is not None: tier_targets["0"]  = args.tier_0
    if args.tier_1    is not None: tier_targets["1"]  = args.tier_1
    if args.tier_2    is not None: tier_targets["2"]  = args.tier_2
    if args.tier_many is not None: tier_targets["3+"] = args.tier_many

    patterns = args.input or []
    cases, out_dir, auto_glob = load_inputs(patterns)

    has_proxy = sum(1 for c in cases if c.get("_pipeline", {}).get("proxy_mean") is not None)
    if has_proxy == 0:
        console.print(
            "[yellow]Warning: no proxy_mean found — all cases treated as equal difficulty (0.5).[/yellow]\n"
            "[dim]Run patch_smoke_scores.py to backfill scores into older batches.[/dim]"
        )
    else:
        console.print(f"  proxy_mean embedded in {has_proxy}/{len(cases)} cases")

    console.print()
    selected = select(cases, args.per_stratum, args.n, args.min_proxy, args.max_proxy, args.seed, tier_targets)
    console.print()
    summary_table(selected, cases)

    if args.output:
        out_path = Path(args.output)
    elif auto_glob or len(patterns) > 1:
        out_path = out_dir / "selected_cases_all.json"
    else:
        input_path = Path(patterns[0]) if patterns else out_dir
        out_path = out_dir / f"selected_{input_path.name}"

    out_path.write_text(json.dumps(selected, indent=2), encoding="utf-8")
    console.print(f"\n[green]Wrote {len(selected)} cases → {out_path}[/green]")


if __name__ == "__main__":
    main()
