# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "rich>=13.0",
# ]
# ///
"""
select_cases.py — v7 Pipeline Phase 2 (Part 2) + Phase 3 integration

Stratified case selection from the normalized benchmark pool.

Reads:
  benchmark_cases_raw.json  — normalized pool from normalize_cases.py
  pilot_results.json        — (optional) Phase 3 GPT-4o pilot scoring results.
                              If present, enables difficulty gating and filtering.

Writes:
  benchmark_cases_verified.json  — final case library for Phase 5 runs

Target stratification (PLAN.md Design Decision §2):
  Regular (critique_wins): 160  (57%)
  Defense (category):       40  (14%)
  Mixed cases:              80  (29%)
  Total:                   280

PM3 recurrence prevention (CRITICAL):
  _pipeline.proxy_mean is stored for traceability only and is NEVER used
  as a difficulty gate input. Difficulty gates use Phase 3 pilot rubric
  performance (GPT-4o scorer) exclusively.
  This script will WARN and abort if proxy_mean is passed via --gate-by-proxy.

Mixed stratum diversity constraints (PLAN.md §2):
  - Minimum 3 distinct domain clusters
  - No single domain > 30% of mixed stratum

Phase 3 pilot integration:
  If pilot_results.json exists, each case gets:
  - difficulty = "medium" | "hard" (from pilot rubric performance)
  - pilot_baseline_fc (for ceiling gate)
  Cases where pilot_baseline_fc > 0.80 are discarded (ceiling effect).
  Hard-stop gate: pilot_fc_mean < 0.80 AND ≥ 80 regular + 30 mixed pass filter.

Usage:
  Before Phase 3 (no pilot yet):
    uv run pipeline/select_cases.py
    uv run pipeline/select_cases.py --tier-mixed 40 --tier-critique 60 --tier-defense 20

  After Phase 3 (with pilot):
    uv run pipeline/select_cases.py --pilot pilot_results.json

  Dry run (preview without writing):
    uv run pipeline/select_cases.py --dry-run
"""

import argparse
import json
import random
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

PIPELINE_DIR = Path(__file__).parent
EXPERIMENT_DIR = PIPELINE_DIR.parent

# Default stratification targets (v7 — design_decisions.md §2)
DEFAULT_TIER_CRITIQUE = 160   # regular cases (all correct_position values)
DEFAULT_TIER_DEFENSE  = 40    # defense category cases
DEFAULT_TIER_MIXED    = 80

# Diversity constraints for mixed stratum
MIN_MIXED_DOMAIN_CLUSTERS = 3
MAX_MIXED_DOMAIN_FRACTION = 0.30

# Phase 3 hard-stop gate
PILOT_CEILING_THRESHOLD = 0.80   # discard cases where baseline_fc > this
PILOT_HARD_STOP_FC_MEAN = 0.80   # abort if pilot mean >= this (no headroom) — matches HYPOTHESIS.md H1a N/A condition
PHASE3_MIN_REGULAR = 80
PHASE3_MIN_MIXED   = 30

# Difficulty thresholds (applied to pilot GPT-4o baseline FC)
# Hard: GPT-4o baseline FC <= 0.45 (model fails or barely succeeds)
# Medium: GPT-4o baseline FC > 0.45 and <= ceiling_threshold
DIFFICULTY_HARD_THRESHOLD = 0.45


def _domain_cluster(case: dict) -> str:
    """
    Extract a domain cluster label from a case.
    Uses 'domain' field, normalizing whitespace and case.
    Falls back to 'ml_task_type' if domain is empty.
    """
    domain = (case.get("domain") or "").strip().lower()
    if not domain:
        domain = (case.get("ml_task_type") or "unknown").strip().lower()
    # Normalize to short label: first 3 words
    words = domain.split()[:3]
    return " ".join(words) if words else "unknown"


def load_pool(pool_path: Path) -> list[dict]:
    if not pool_path.exists():
        console.print(f"[red]ERROR: Pool file not found: {pool_path}[/red]")
        console.print("Run 'uv run pipeline/normalize_cases.py' first.")
        sys.exit(1)
    cases = json.loads(pool_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        console.print(f"[red]ERROR: {pool_path} is not a JSON array[/red]")
        sys.exit(1)
    return cases


def load_pilot_results(pilot_path: Path) -> dict[str, dict]:
    """
    Load pilot results file.
    Expected format:
      {
        "cases": {
          "<case_id>": {
            "baseline_fc_mean": float,      # GPT-4o scored baseline performance
            "difficulty": "medium" | "hard" | null
          },
          ...
        },
        "pilot_fc_mean": float,
        "n_cases": int
      }
    Returns: {case_id: {baseline_fc_mean, difficulty}}
    """
    if not pilot_path.exists():
        return {}
    try:
        data = json.loads(pilot_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "cases" in data:
            return data["cases"]
        # Flat format fallback: {case_id: {baseline_fc_mean, ...}}
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[yellow]Warning: could not load pilot results — {exc}[/yellow]")
    return {}


def apply_pilot_labels(
    cases: list[dict],
    pilot: dict[str, dict],
    ceiling_threshold: float = PILOT_CEILING_THRESHOLD,
) -> tuple[list[dict], list[str]]:
    """
    Apply pilot difficulty labels and ceiling filter to cases.
    Returns (filtered_cases, discarded_case_ids).

    PM3 note: difficulty is set from pilot rubric performance (GPT-4o).
    _pipeline.proxy_mean is NOT read here.
    """
    filtered = []
    discarded = []

    for case in cases:
        cid = case["case_id"]
        pilot_data = pilot.get(cid, {})
        baseline_fc = pilot_data.get("baseline_fc_mean")

        # Ceiling gate: discard cases where GPT-4o baseline FC > threshold
        if baseline_fc is not None and baseline_fc > ceiling_threshold:
            discarded.append(cid)
            continue

        # Set difficulty from pilot if available; otherwise keep existing
        if "difficulty" in pilot_data and pilot_data["difficulty"] is not None:
            case["difficulty"] = pilot_data["difficulty"]
        elif baseline_fc is not None and case.get("difficulty") is None:
            # Infer difficulty from pilot baseline FC
            if baseline_fc <= DIFFICULTY_HARD_THRESHOLD:
                case["difficulty"] = "hard"
            else:
                case["difficulty"] = "medium"

        # Store pilot baseline FC for reference (not for gating)
        if baseline_fc is not None:
            case["_pipeline"]["pilot_baseline_fc"] = baseline_fc

        filtered.append(case)

    return filtered, discarded


def stratified_select(
    cases: list[dict],
    tier_critique: int,
    tier_defense: int,
    tier_mixed: int,
    seed: int = 42,
    _prefer_hard: bool = True,
) -> tuple[list[dict], dict]:
    """
    Stratified selection from the pool.
    Returns (selected_cases, selection_stats).

    Selection order within each stratum:
    1. Hard cases preferred (higher difficulty = more signal)
    2. RC cases preferred over synthetic (higher validity)
    3. Random within tied groups (seeded)

    Mixed stratum diversity enforcement:
    - ≥3 distinct domain clusters
    - No domain > 30% of mixed
    """
    rng = random.Random(seed)

    def sort_key(case: dict):
        # Primary: difficulty (hard first)
        difficulty_rank = {"hard": 0, "medium": 1, None: 2}
        d = difficulty_rank.get(case.get("difficulty"), 2)
        # Secondary: RC cases first
        is_real = 0 if case.get("is_real_paper_case") else 1
        # Tertiary: random (for tie-breaking)
        return (d, is_real, rng.random())

    # Split by stratum
    # v7: critique pool = all regular cases (critique_wins OR defense_wins correct_position)
    # v7: defense pool  = cases with category='defense' (separate stratum, not regular sub-type)
    # v7: mixed pool    = cases with category='mixed'
    critique_pool = [c for c in cases if c.get("category") == "regular"]
    defense_pool  = [c for c in cases if c.get("category") == "defense"]
    mixed_pool    = [c for c in cases if c.get("category") == "mixed"]

    # Sort each stratum
    critique_pool.sort(key=sort_key)
    defense_pool.sort(key=sort_key)
    mixed_pool.sort(key=sort_key)

    # Select critique and defense straightforwardly
    selected_critique = critique_pool[:tier_critique]
    selected_defense = defense_pool[:tier_defense]

    # Mixed selection with diversity enforcement
    selected_mixed = _select_mixed_with_diversity(
        mixed_pool, tier_mixed, rng
    )

    selected = selected_critique + selected_defense + selected_mixed

    stats = {
        "n_selected": len(selected),
        "n_critique": len(selected_critique),
        "n_defense": len(selected_defense),
        "n_mixed": len(selected_mixed),
        "n_critique_available": len(critique_pool),
        "n_defense_available": len(defense_pool),
        "n_mixed_available": len(mixed_pool),
        "critique_shortfall": max(0, tier_critique - len(selected_critique)),
        "defense_shortfall": max(0, tier_defense - len(selected_defense)),
        "mixed_shortfall": max(0, tier_mixed - len(selected_mixed)),
    }
    return selected, stats


def _select_mixed_with_diversity(
    pool: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:
    """
    Select mixed cases with domain diversity enforcement.
    Constraint: ≥3 distinct domain clusters, no domain > 30% of selected.
    """
    if not pool:
        return []

    max_per_domain = max(1, int(target * MAX_MIXED_DOMAIN_FRACTION))

    selected = []
    domain_counts: dict[str, int] = {}

    # Two passes:
    # Pass 1: take up to max_per_domain from each domain in priority order
    for case in pool:
        if len(selected) >= target:
            break
        domain = _domain_cluster(case)
        count = domain_counts.get(domain, 0)
        if count < max_per_domain:
            selected.append(case)
            domain_counts[domain] = count + 1

    # Pass 2: fill remaining slots (relax domain constraint)
    selected_ids = {c["case_id"] for c in selected}
    remaining = [c for c in pool if c["case_id"] not in selected_ids]
    rng.shuffle(remaining)
    for case in remaining:
        if len(selected) >= target:
            break
        selected.append(case)

    # Check diversity
    n_clusters = len({_domain_cluster(c) for c in selected})
    if n_clusters < MIN_MIXED_DOMAIN_CLUSTERS:
        console.print(
            f"  [yellow]Mixed diversity warning: only {n_clusters} domain cluster(s) "
            f"(target ≥{MIN_MIXED_DOMAIN_CLUSTERS}). "
            "Consider generating mixed cases across more domains.[/yellow]"
        )

    return selected


def phase3_hard_stop_check(
    cases: list[dict],
    pilot: dict[str, dict],
    min_regular: int = PHASE3_MIN_REGULAR,
    min_mixed: int   = PHASE3_MIN_MIXED,
) -> tuple[bool, str]:
    """
    Phase 3 hard-stop gate (PLAN.md Phase 3 spec):
      - pilot_fc_mean < 0.80  (sufficient headroom — matches HYPOTHESIS.md H1a N/A condition)
      - ≥80 regular + 30 mixed pass the ceiling filter

    Returns (gate_passes, reason_if_failed).
    """
    if not pilot:
        return True, ""  # no pilot data = pre-Phase-3, skip gate

    pilot_fc_values: list[float] = [
        float(v["baseline_fc_mean"])
        for v in pilot.values()
        if v.get("baseline_fc_mean") is not None
    ]
    if not pilot_fc_values:
        return True, ""

    pilot_fc_mean = sum(pilot_fc_values) / len(pilot_fc_values)

    n_regular = sum(1 for c in cases if c.get("category") == "regular")
    n_mixed   = sum(1 for c in cases if c.get("category") == "mixed")

    if pilot_fc_mean >= PILOT_HARD_STOP_FC_MEAN:
        return False, (
            f"HARD STOP: pilot_fc_mean = {pilot_fc_mean:.4f} ≥ {PILOT_HARD_STOP_FC_MEAN} "
            "(baseline ceiling too high — insufficient headroom for H1a). "
            "Generate harder cases or lower difficulty target."
        )

    if n_regular < min_regular or n_mixed < min_mixed:
        return False, (
            f"HARD STOP: insufficient cases after pilot filter "
            f"(regular={n_regular} need ≥{min_regular}, mixed={n_mixed} need ≥{min_mixed})"
        )

    return True, ""


def print_selection_report(
    selected: list[dict],
    stats: dict,
    pilot: dict[str, dict],
) -> None:
    """Print a detailed selection report."""
    console.print()

    table = Table(title="Selection Summary", show_header=True)
    table.add_column("Stratum")
    table.add_column("Selected", justify="right")
    table.add_column("Available", justify="right")
    table.add_column("Target", justify="right")
    table.add_column("Shortfall", justify="right")

    def shortfall_str(n):
        return f"[red]-{n}[/red]" if n > 0 else "[green]0[/green]"

    v7_total = DEFAULT_TIER_CRITIQUE + DEFAULT_TIER_DEFENSE + DEFAULT_TIER_MIXED
    table.add_row("Regular",  str(stats["n_critique"]),   str(stats["n_critique_available"]),  str(DEFAULT_TIER_CRITIQUE), shortfall_str(stats["critique_shortfall"]))
    table.add_row("Defense",  str(stats["n_defense"]),    str(stats["n_defense_available"]),   str(DEFAULT_TIER_DEFENSE),  shortfall_str(stats["defense_shortfall"]))
    table.add_row("Mixed",    str(stats["n_mixed"]),      str(stats["n_mixed_available"]),     str(DEFAULT_TIER_MIXED),    shortfall_str(stats["mixed_shortfall"]))
    table.add_row("Total",    str(stats["n_selected"]),   "—",                                 str(v7_total),              shortfall_str(max(0, v7_total - stats["n_selected"])))
    console.print(table)

    # Difficulty breakdown
    n_hard = sum(1 for c in selected if c.get("difficulty") == "hard")
    n_medium = sum(1 for c in selected if c.get("difficulty") == "medium")
    n_null = sum(1 for c in selected if c.get("difficulty") is None)
    console.print(f"\nDifficulty:  hard={n_hard}  medium={n_medium}  unassigned={n_null}")

    # Source breakdown
    n_rc = sum(1 for c in selected if c.get("is_real_paper_case"))
    n_synth = len(selected) - n_rc
    console.print(f"Source:      RC={n_rc}  synthetic={n_synth}")

    # Mixed domain diversity
    mixed_cases = [c for c in selected if c.get("category") == "mixed"]
    if mixed_cases:
        domain_counts: dict[str, int] = {}
        for c in mixed_cases:
            d = _domain_cluster(c)
            domain_counts[d] = domain_counts.get(d, 0) + 1
        n_clusters = len(domain_counts)
        max_frac = max(cnt / len(mixed_cases) for cnt in domain_counts.values()) if mixed_cases else 0.0
        diversity_ok = n_clusters >= MIN_MIXED_DOMAIN_CLUSTERS and max_frac <= MAX_MIXED_DOMAIN_FRACTION
        status = "[green]OK[/green]" if diversity_ok else "[yellow]WARNING[/yellow]"
        console.print(
            f"Mixed diversity: {n_clusters} domain clusters, "
            f"max domain fraction = {max_frac:.0%}  {status}"
        )
        if n_clusters < MIN_MIXED_DOMAIN_CLUSTERS:
            console.print(f"  [yellow]→ Need ≥{MIN_MIXED_DOMAIN_CLUSTERS} clusters[/yellow]")
        if max_frac > MAX_MIXED_DOMAIN_FRACTION:
            console.print(f"  [yellow]→ Max domain fraction exceeded ({MAX_MIXED_DOMAIN_FRACTION:.0%} limit)[/yellow]")

    # Pilot summary if available
    if pilot:
        pilot_values: list[float] = [
            float(v["baseline_fc_mean"]) for v in pilot.values()
            if v.get("baseline_fc_mean") is not None
        ]
        if pilot_values:
            pilot_mean = sum(pilot_values) / len(pilot_values)
            console.print(
                f"\nPilot baseline FC mean: {pilot_mean:.4f} "
                f"(threshold < {PILOT_HARD_STOP_FC_MEAN:.2f})"
            )

    # Shortfall warnings
    if stats["critique_shortfall"] > 0:
        console.print(
            f"\n[yellow]⚠ Critique shortfall: {stats['critique_shortfall']} cases. "
            "Run orchestrator.py to generate more synthetic regular cases.[/yellow]"
        )
    if stats["defense_shortfall"] > 0:
        console.print(
            f"[yellow]⚠ Defense shortfall: {stats['defense_shortfall']} cases.[/yellow]"
        )
    if stats["mixed_shortfall"] > 0:
        console.print(
            f"[yellow]⚠ Mixed shortfall: {stats['mixed_shortfall']} cases. "
            "Run orchestrator.py --mixed to generate more mixed cases.[/yellow]"
        )


def _sanitize_case(case: dict) -> dict:
    """Strip ground-truth fields for Phase 5 benchmark runner input.

    Removes: ground_truth.correct_position/correct_verdict/final_verdict,
    scoring_targets.must_find_issue_ids/acceptable_resolutions/must_not_claim,
    planted_issues. Leaves all other fields intact.
    """
    import copy
    c = copy.deepcopy(case)
    c.pop("planted_issues", None)
    gt = c.get("ground_truth", {})
    for field in ("correct_position", "correct_verdict", "final_verdict"):
        gt.pop(field, None)
    st = c.get("scoring_targets", {})
    for field in ("must_find_issue_ids", "acceptable_resolutions",
                  "must_not_claim", "must_not_claim_details"):
        st.pop(field, None)
    return c


def main():
    parser = argparse.ArgumentParser(
        description="select_cases.py — stratified case selection for v7 benchmark"
    )
    parser.add_argument(
        "--pool",
        default="benchmark_cases_v7_raw.json",
        help="Input pool file (default: benchmark_cases_v7_raw.json in experiment root)",
    )
    parser.add_argument(
        "--output",
        default="benchmark_cases_v7_verified.json",
        help="Output file (default: benchmark_cases_v7_verified.json in experiment root)",
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help=(
            "Strip ground-truth fields before writing. Removes correct_position, "
            "must_find_issue_ids, acceptable_resolutions, planted_issues, must_not_claim. "
            "Use to produce v7_cases_sanitized.json for Phase 5 benchmark runner."
        ),
    )
    parser.add_argument(
        "--pilot",
        default=None,
        help="Phase 3 pilot results JSON (enables difficulty gating + ceiling filter)",
    )
    parser.add_argument(
        "--tier-critique",
        type=int,
        default=DEFAULT_TIER_CRITIQUE,
        help=f"Target N critique cases (default: {DEFAULT_TIER_CRITIQUE})",
    )
    parser.add_argument(
        "--tier-defense",
        type=int,
        default=DEFAULT_TIER_DEFENSE,
        help=f"Target N defense cases (default: {DEFAULT_TIER_DEFENSE})",
    )
    parser.add_argument(
        "--tier-mixed",
        type=int,
        default=DEFAULT_TIER_MIXED,
        help=f"Target N mixed cases (default: {DEFAULT_TIER_MIXED})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for tie-breaking selection (default: 42)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview selection without writing output",
    )
    parser.add_argument(
        "--gate-by-proxy",
        action="store_true",
        default=False,
        help=(
            argparse.SUPPRESS  # hidden flag that explicitly fails if used
        ),
    )
    args = parser.parse_args()

    # PM3 guard: refuse to gate by proxy_mean
    if args.gate_by_proxy:
        console.print(
            "[red]ERROR: --gate-by-proxy is explicitly prohibited (PM3 recurrence prevention).[/red]\n"
            "proxy_mean did not predict rubric performance in v5 (Spearman ρ = +0.046).\n"
            "Use Phase 3 pilot results (--pilot) for difficulty gating instead."
        )
        sys.exit(1)

    console.rule("[bold blue]select_cases.py[/bold blue]")

    # Load pool
    pool_path = EXPERIMENT_DIR / args.pool
    output_path = EXPERIMENT_DIR / args.output

    console.print(f"Pool:   {pool_path}")
    console.print(f"Output: {output_path}")

    cases = load_pool(pool_path)
    console.print(f"Pool size: {len(cases)} cases\n")

    # Load pilot results if provided
    pilot: dict[str, dict] = {}
    if args.pilot:
        pilot_path = EXPERIMENT_DIR / args.pilot
        pilot = load_pilot_results(pilot_path)
        console.print(f"Pilot results: {len(pilot)} cases loaded from {pilot_path}")

        # Apply difficulty labels and ceiling filter
        console.print("Applying pilot difficulty labels and ceiling filter...")
        cases, discarded = apply_pilot_labels(
            cases, pilot, ceiling_threshold=PILOT_CEILING_THRESHOLD
        )
        console.print(
            f"  After ceiling filter: {len(cases)} kept, "
            f"{len(discarded)} discarded (baseline FC > {PILOT_CEILING_THRESHOLD:.2f})"
        )
        if discarded:
            console.print(
                f"  [dim]Discarded IDs: {', '.join(discarded[:10])}"
                f"{'...' if len(discarded) > 10 else ''}[/dim]"
            )

        # Phase 3 hard-stop gate
        gate_passes, gate_reason = phase3_hard_stop_check(
            cases, pilot,
            min_regular=PHASE3_MIN_REGULAR,
            min_mixed=PHASE3_MIN_MIXED,
        )
        if not gate_passes:
            console.print(f"\n[red]{gate_reason}[/red]")
            sys.exit(1)
        else:
            console.print("  [green]Phase 3 hard-stop gate: PASS[/green]")
    else:
        console.print(
            "[dim]No pilot file provided — selecting without difficulty gating. "
            "Run Phase 3 and rerun with --pilot to apply ceiling filter.[/dim]\n"
        )

    # Stratified selection
    selected, stats = stratified_select(
        cases,
        tier_critique=args.tier_critique,
        tier_defense=args.tier_defense,
        tier_mixed=args.tier_mixed,
        seed=args.seed,
    )

    # Report
    print_selection_report(selected, stats, pilot)

    if args.dry_run:
        console.print(f"\n[dim]DRY RUN: would write {len(selected)} cases to {output_path}[/dim]")
        if args.sanitize:
            console.print("[dim]  --sanitize: ground-truth fields would be stripped[/dim]")
        return

    # Apply sanitization if requested (produces Phase 5 input — no ground-truth leakage)
    output_cases = [_sanitize_case(c) for c in selected] if args.sanitize else selected

    # Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_cases, indent=2), encoding="utf-8")
    if args.sanitize:
        console.print(f"\n[green]✓ Wrote {len(output_cases)} sanitized cases → {output_path}[/green]")
        console.print("[dim]Ground-truth fields stripped for Phase 5 benchmark runner.[/dim]")
    else:
        console.print(f"\n[green]✓ Wrote {len(output_cases)} cases → {output_path}[/green]")
        console.print("Run Phase 3 pilot (if not done) then rerun with --pilot to apply ceiling filter.")


if __name__ == "__main__":
    main()
