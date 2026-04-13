# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "rich>=13.0",
# ]
# ///
"""
normalize_cases.py — v7 Pipeline Phase 2 (Part 1)

Reads all synthetic and RC case sources, normalizes to unified Schema B,
validates every field, and outputs benchmark_cases_raw.json.

Sources read (any combination present):
  Synthetic: cases_*.json in experiment root (from orchestrator assemble_batch)
  RC:        pipeline/run/rc_candidates/rc_cases_raw.json (from rc_extractor RC-4)

Output:
  benchmark_cases_raw.json  — overcomplete candidate pool (~150+ cases)

Schema B fields validated (per PLAN.md "Unified Schema B Definition"):
  case_id, hypothesis, domain, ml_task_type, category, difficulty,
  task_prompt, ground_truth.correct_position, ideal_debate_resolution.type,
  scoring_targets.acceptable_resolutions (flat string array),
  scoring_targets.must_find_issue_ids, scoring_targets.must_not_claim,
  planted_issues, sound_design_reference, is_real_paper_case,
  _pipeline.case_type, _pipeline.proxy_mean

Usage:
    uv run pipeline/normalize_cases.py
    uv run pipeline/normalize_cases.py --output custom_pool.json
    uv run pipeline/normalize_cases.py --strict  # abort on any validation failure
    uv run pipeline/normalize_cases.py --dry-run  # show what would be normalized
"""

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PIPELINE_DIR = Path(__file__).parent
EXPERIMENT_DIR = PIPELINE_DIR.parent
RC_CANDIDATES_DIR = PIPELINE_DIR / "run" / "rc_candidates"

VALID_CORRECT_POSITIONS = {"critique_wins", "defense_wins", "empirical_test_agreed"}
VALID_IDR_TYPES = {"critique_wins", "defense_wins", "mixed"}
VALID_ACCEPTABLE = {"critique_wins", "defense_wins", "empirical_test_agreed"}
VALID_CATEGORIES = {"regular", "mixed", "defense"}
VALID_PIPELINE_CASE_TYPES = {"rc", "regular", "mixed", "defense"}

# ---------------------------------------------------------------------------
# Schema B construction helpers
# ---------------------------------------------------------------------------


def _verdict_to_correct_position(correct_verdict: str) -> str:
    """Map stage4 correct_verdict (or RC correct_position) → Schema B canonical value.

    Stage 4 outputs "critique" or "defense_wins". RC extractor may output
    short-form tokens or canonical tokens. All are mapped to canonical Schema B values.
    """
    return {
        # stage4 short forms
        "critique":              "critique_wins",
        "defense":               "defense_wins",
        "mixed":                 "empirical_test_agreed",
        # already canonical (pass-through)
        "critique_wins":         "critique_wins",
        "defense_wins":          "defense_wins",
        "empirical_test_agreed": "empirical_test_agreed",
    }.get(correct_verdict, "critique_wins")


def _correct_position_to_idr_type(correct_position: str) -> str:
    """Derive ideal_debate_resolution.type from canonical correct_position."""
    return {
        "critique_wins":         "critique_wins",
        "defense_wins":          "defense_wins",
        "empirical_test_agreed": "mixed",
    }.get(correct_position, "critique_wins")


def _correct_position_to_acceptable_resolutions(correct_position: str) -> list[str]:
    """
    Derive acceptable_resolutions (flat string array) from canonical correct_position.
    This is the authoritative mapping — NOT derived from stage4 resolution objects.

    self_debate_poc.py line 168 reads:
        st.get('acceptable_resolutions', [ideal_resolution])
    and uses: `verdict in acceptable_resolutions` — must be flat strings.
    """
    return {
        "critique_wins":         ["critique_wins"],
        "defense_wins":          ["defense_wins"],
        "empirical_test_agreed": ["empirical_test_agreed"],
    }.get(correct_position, ["critique_wins"])


def _normalize_must_not_claim(raw_must_not_claim) -> tuple[list[str], list[dict]]:
    """
    Normalize must_not_claim to (flat_id_list, details_list).

    Stage4 output: list of objects {claim: str, why_wrong: str}
    Schema B target:
      must_not_claim = ["claim_001", "claim_002"]  — flat IDs
      must_not_claim_details = [{claim_id, claim, why_wrong}]

    Stage3m / RC output: already split as (flat_ids, details_list) — pass through.
    """
    if not raw_must_not_claim:
        return [], []

    # If it's a list of strings, already flat IDs
    if isinstance(raw_must_not_claim, list) and all(
        isinstance(item, str) for item in raw_must_not_claim
    ):
        return raw_must_not_claim, []

    # If it's a list of objects with {claim, why_wrong} (stage4 format)
    if isinstance(raw_must_not_claim, list) and all(
        isinstance(item, dict) for item in raw_must_not_claim
    ):
        flat_ids = []
        details = []
        for idx, item in enumerate(raw_must_not_claim, start=1):
            claim_id = item.get("claim_id") or f"claim_{idx:03d}"
            flat_ids.append(claim_id)
            details.append({
                "claim_id": claim_id,
                "claim": item.get("claim", ""),
                "why_wrong": item.get("why_wrong", ""),
            })
        return flat_ids, details

    return [], []


def _normalize_planted_issues(planted_issues: list) -> list[dict]:
    """
    Ensure each planted_issues entry has issue_id and corruption_id fields.
    RC cases: corruption_id = null (per PLAN.md Schema B spec).
    Synthetic cases: corruption_id comes from the corruption report.
    """
    normalized = []
    for issue in planted_issues:
        if not isinstance(issue, dict):
            continue
        entry = dict(issue)
        if "issue_id" not in entry:
            continue  # skip malformed entries
        if "corruption_id" not in entry:
            entry["corruption_id"] = None
        normalized.append(entry)
    return normalized


# ---------------------------------------------------------------------------
# Synthetic case normalizer (stage4 + stage3m output → Schema B)
# ---------------------------------------------------------------------------


def normalize_synthetic_case(raw: dict) -> dict | None:
    """
    Normalize a single synthetic case (from orchestrator stage4 / stage3m) to Schema B.
    Returns the normalized case dict, or None if the case cannot be normalized.
    """
    pipeline = raw.get("_pipeline", {})
    case_type = pipeline.get("case_type", "regular")

    if case_type == "mixed":
        return _normalize_synthetic_mixed(raw)
    if case_type == "defense":
        return _normalize_synthetic_defense(raw)
    return _normalize_synthetic_regular(raw)


def _normalize_synthetic_regular(raw: dict) -> dict | None:
    case_id = raw.get("case_id")
    if not case_id:
        return None

    # Derive correct_position from correct_verdict (stage4 field)
    correct_verdict = raw.get("correct_verdict", "")
    correct_position = _verdict_to_correct_position(correct_verdict)
    idr_type = _correct_position_to_idr_type(correct_position)
    acceptable_resolutions = _correct_position_to_acceptable_resolutions(correct_position)

    # must_not_claim: stage4 may output as list of objects
    raw_mnc = raw.get("must_not_claim", [])
    # Also check scoring_targets.must_not_claim if present
    scoring_targets_raw = raw.get("scoring_targets", {})
    if isinstance(scoring_targets_raw, dict) and scoring_targets_raw.get("must_not_claim"):
        raw_mnc = scoring_targets_raw["must_not_claim"]

    mnc_flat, mnc_details = _normalize_must_not_claim(raw_mnc)

    # must_find_issue_ids
    must_find = raw.get("must_find_issue_ids", [])
    if not must_find and isinstance(scoring_targets_raw, dict):
        must_find = scoring_targets_raw.get("must_find_issue_ids", [])

    # planted_issues
    planted = _normalize_planted_issues(raw.get("planted_issues", []))

    pipeline = raw.get("_pipeline", {})

    return {
        "case_id": case_id,
        "hypothesis": raw.get("hypothesis", ""),
        "domain": raw.get("domain", ""),
        "ml_task_type": raw.get("ml_task_type", ""),
        "category": "regular",
        "difficulty": None,  # filled by Phase 3 pilot
        "task_prompt": raw.get("task_prompt", ""),
        "ground_truth": {
            "correct_position": correct_position,
            "final_verdict": correct_verdict,
            "correct_verdict": correct_verdict,
        },
        "ideal_debate_resolution": {
            "type": idr_type,
        },
        "planted_issues": planted,
        "scoring_targets": {
            "must_find_issue_ids": must_find,
            "must_not_claim": mnc_flat,
            "must_not_claim_details": mnc_details,
            "acceptable_resolutions": acceptable_resolutions,
        },
        "sound_design_reference": raw.get("sound_design_reference"),
        "is_real_paper_case": False,
        "_pipeline": {
            "case_type": "regular",
            "mechanism_id": pipeline.get("mechanism_id", ""),
            "num_corruptions": pipeline.get("num_corruptions"),
            "corruption_ids": pipeline.get("corruption_ids", []),
            "proxy_mean": pipeline.get("proxy_mean"),
            "smoke_scores": pipeline.get("smoke_scores", {}),
        },
    }


def _normalize_synthetic_mixed(raw: dict) -> dict | None:
    """
    Normalize a stage3m mixed case. Most fields pass through since stage3m
    already outputs near-Schema B. Key task: validate acceptable_resolutions.
    """
    case_id = raw.get("case_id")
    if not case_id:
        return None

    gt = raw.get("ground_truth", {})
    idr = raw.get("ideal_debate_resolution", {})
    st_raw = raw.get("scoring_targets", {})

    # Validate/fix acceptable_resolutions
    ar = st_raw.get("acceptable_resolutions", [])
    if not isinstance(ar, list) or not all(isinstance(s, str) for s in ar):
        ar = ["empirical_test_agreed"]
    # Force to correct value for any deviation — not just the "all 4 verdicts" case
    if set(ar) != {"empirical_test_agreed"}:
        ar = ["empirical_test_agreed"]

    # must_not_claim: stage3m already outputs flat IDs
    mnc_flat = st_raw.get("must_not_claim", [])
    mnc_details = st_raw.get("must_not_claim_details", [])
    if not isinstance(mnc_flat, list):
        mnc_flat = []

    pipeline = raw.get("_pipeline", {})

    return {
        "case_id": case_id,
        "hypothesis": raw.get("hypothesis", ""),
        "domain": raw.get("domain", ""),
        "ml_task_type": raw.get("ml_task_type", ""),
        "category": "mixed",
        "difficulty": raw.get("difficulty"),  # stage3m assigns difficulty
        "task_prompt": raw.get("task_prompt", ""),
        "ground_truth": {
            "correct_position": "empirical_test_agreed",
            "final_verdict": gt.get("final_verdict", "Empirically contested"),
            "required_empirical_test": gt.get("required_empirical_test", {}),
        },
        "ideal_debate_resolution": {
            "type": idr.get("type", "mixed"),
            "condition": idr.get("condition", ""),
            "supports_critique_if": idr.get("supports_critique_if", ""),
            "supports_defense_if": idr.get("supports_defense_if", ""),
            "ambiguous_if": idr.get("ambiguous_if"),
        },
        "planted_issues": [],
        "scoring_targets": {
            "must_find_issue_ids": [],
            "must_not_claim": mnc_flat,
            "must_not_claim_details": mnc_details,
            "acceptable_resolutions": ar,
        },
        "sound_design_reference": raw.get("sound_design_reference"),
        "is_real_paper_case": False,
        "_pipeline": {
            "case_type": "mixed",
            "mechanism_id": pipeline.get("mechanism_id", ""),
            "num_corruptions": 0,
            "corruption_ids": [],
            "proxy_mean": None,
            "smoke_scores": {},
        },
    }


def _normalize_synthetic_defense(raw: dict) -> dict | None:
    """
    Normalize a stage4_defense output to Schema B.
    category='defense', correct_position='defense_wins', no planted issues.
    """
    case_id = raw.get("case_id")
    if not case_id:
        return None

    pipeline = raw.get("_pipeline", {})
    must_not_claim_raw = raw.get("must_not_claim", [])
    # Check scoring_targets.must_not_claim fallback
    st_raw = raw.get("scoring_targets", {})
    if isinstance(st_raw, dict) and st_raw.get("must_not_claim"):
        must_not_claim_raw = st_raw["must_not_claim"]
    mnc_flat, mnc_details = _normalize_must_not_claim(must_not_claim_raw)

    return {
        "case_id": case_id,
        "hypothesis": raw.get("hypothesis", ""),
        "domain": raw.get("domain", ""),
        "ml_task_type": raw.get("ml_task_type", ""),
        "category": "defense",
        "difficulty": None,
        "task_prompt": raw.get("task_prompt", ""),
        "ground_truth": {
            "correct_position": "defense_wins",
            "final_verdict": "defense_wins",
            "correct_verdict": "defense_wins",
        },
        "ideal_debate_resolution": {
            "type": "defense_wins",
        },
        "planted_issues": [],
        "scoring_targets": {
            "must_find_issue_ids": [],
            "must_not_claim": mnc_flat,
            "must_not_claim_details": mnc_details,
            "acceptable_resolutions": ["defense_wins"],
        },
        "sound_design_reference": raw.get("sound_design_reference"),
        "is_real_paper_case": False,
        "_pipeline": {
            "case_type": "defense",
            "mechanism_id": pipeline.get("mechanism_id", ""),
            "num_corruptions": 0,
            "corruption_ids": [],
            "proxy_mean": None,
            "smoke_scores": {},
        },
    }


# ---------------------------------------------------------------------------
# RC case normalizer (rc_cases_raw.json → Schema B)
# ---------------------------------------------------------------------------


def normalize_rc_case(raw: dict) -> dict | None:
    """
    Normalize a single RC case (from rc_extractor RC-4) to Schema B.
    """
    report_id = raw.get("report_id", "")
    if not report_id:
        return None

    case_id = report_id if report_id.startswith("rc_") else f"rc_{report_id}"

    # Map through canonical mapper so RC extractor's short-form tokens become Schema B values
    _raw_cp = raw.get("correct_position", "critique_wins")
    correct_position = _verdict_to_correct_position(_raw_cp)
    idr_type = raw.get("ideal_debate_resolution_type") or _correct_position_to_idr_type(correct_position)

    # acceptable_resolutions: already a flat string array from rc_extractor
    ar = raw.get("acceptable_resolutions", [])
    if not isinstance(ar, list) or not all(isinstance(s, str) for s in ar):
        ar = _correct_position_to_acceptable_resolutions(correct_position)

    # Convert flaw_records to planted_issues (RC uses flaw_records, Schema B uses planted_issues)
    flaw_records = raw.get("flaw_records", [])
    planted_issues = []
    for flaw in flaw_records:
        if not isinstance(flaw, dict) or not flaw.get("issue_id"):
            continue
        planted_issues.append({
            "issue_id": flaw["issue_id"],
            "corruption_id": None,  # RC cases have no corruption — per PLAN.md Schema B
            "flaw_type": flaw.get("flaw_type", "other"),
            "description": flaw.get("description", ""),
            "severity": flaw.get("severity", "major"),
            "detectability": None,
            "compound": False,
            "source": "reproducer_documented",
        })

    must_find = raw.get("must_find_issue_ids", [])
    must_not_claim = raw.get("must_not_claim", [])
    must_not_claim_details = raw.get("must_not_claim_details", [])

    # For RC mixed cases, include ideal_debate_resolution fields if available
    ideal_resolution_fields: dict = {"type": idr_type}
    if correct_position == "empirical_test_agreed":
        ideal_resolution_fields.update({
            "condition": raw.get("mixed_rationale", ""),
            "supports_critique_if": "",
            "supports_defense_if": "",
            "ambiguous_if": None,
        })

    rc_meta = raw.get("_rc_metadata", {})
    title = raw.get("title", "")

    return {
        "case_id": case_id,
        "hypothesis": title,
        "domain": raw.get("domain", ""),  # may be empty — Phase 3 can fill
        "ml_task_type": raw.get("ml_task_type", ""),
        "category": "mixed" if correct_position == "empirical_test_agreed" else "regular",
        "difficulty": None,
        "task_prompt": raw.get("task_prompt", ""),
        "ground_truth": {
            "correct_position": correct_position,
            "final_verdict": idr_type,
        },
        "ideal_debate_resolution": ideal_resolution_fields,
        "planted_issues": planted_issues,
        "scoring_targets": {
            "must_find_issue_ids": must_find,
            "must_not_claim": must_not_claim,
            "must_not_claim_details": must_not_claim_details,
            "acceptable_resolutions": ar,
        },
        "sound_design_reference": None,
        "is_real_paper_case": True,
        "_pipeline": {
            "case_type": "rc",
            "mechanism_id": report_id,
            "num_corruptions": None,
            "corruption_ids": [],
            "proxy_mean": None,
            "smoke_scores": {},
            "rc_source": rc_meta.get("source", ""),
            "rc_submission_id": rc_meta.get("submission_id", ""),
            "rc_report_url": raw.get("report_url", ""),
        },
    }


# ---------------------------------------------------------------------------
# Schema B validation
# ---------------------------------------------------------------------------


def validate_schema_b(case: dict, _strict: bool = False) -> list[str]:
    """
    Validate a case against Schema B requirements.
    Returns a list of violation strings (empty = valid).
    """
    issues = []
    cid = case.get("case_id", "?")

    # Required top-level string fields
    for field in ("case_id", "hypothesis", "task_prompt"):
        if not case.get(field):
            issues.append(f"{cid}: missing required field '{field}'")

    # category
    category = case.get("category")
    if category not in VALID_CATEGORIES:
        issues.append(f"{cid}: invalid category '{category}' (must be regular|mixed|defense)")

    # ground_truth
    gt = case.get("ground_truth", {})
    cp = gt.get("correct_position")
    if cp not in VALID_CORRECT_POSITIONS:
        issues.append(f"{cid}: invalid ground_truth.correct_position '{cp}'")

    # ideal_debate_resolution
    idr = case.get("ideal_debate_resolution", {})
    idr_type = idr.get("type")
    if idr_type not in VALID_IDR_TYPES:
        issues.append(f"{cid}: invalid ideal_debate_resolution.type '{idr_type}'")

    # scoring_targets
    st = case.get("scoring_targets", {})
    if not isinstance(st, dict):
        issues.append(f"{cid}: scoring_targets must be a dict")
    else:
        # Critical: acceptable_resolutions must be flat string array
        ar = st.get("acceptable_resolutions")
        if not isinstance(ar, list):
            issues.append(f"{cid}: scoring_targets.acceptable_resolutions must be a list")
        elif not all(isinstance(s, str) for s in ar):
            issues.append(
                f"{cid}: scoring_targets.acceptable_resolutions must be flat string array "
                f"(found non-string elements)"
            )
        elif not ar:
            issues.append(f"{cid}: scoring_targets.acceptable_resolutions is empty")

        # must_find_issue_ids and must_not_claim must be lists
        for key in ("must_find_issue_ids", "must_not_claim"):
            val = st.get(key)
            if not isinstance(val, list):
                issues.append(f"{cid}: scoring_targets.{key} must be a list")

    # planted_issues must be a list
    if not isinstance(case.get("planted_issues"), list):
        issues.append(f"{cid}: planted_issues must be a list")

    # is_real_paper_case must be bool
    if not isinstance(case.get("is_real_paper_case"), bool):
        issues.append(f"{cid}: is_real_paper_case must be a bool")

    # _pipeline
    pl = case.get("_pipeline", {})
    if not isinstance(pl, dict):
        issues.append(f"{cid}: _pipeline must be a dict")
    else:
        ct = pl.get("case_type")
        if ct not in VALID_PIPELINE_CASE_TYPES:
            issues.append(f"{cid}: _pipeline.case_type '{ct}' invalid")

    # Category/correct_position consistency check
    if category == "mixed" and cp != "empirical_test_agreed":
        issues.append(f"{cid}: category=mixed but correct_position={cp!r} (expected 'empirical_test_agreed')")
    if cp == "empirical_test_agreed" and category != "mixed":
        issues.append(f"{cid}: correct_position=empirical_test_agreed but category={category!r} (expected 'mixed')")
    if category == "defense" and cp != "defense_wins":
        issues.append(f"{cid}: category=defense but correct_position={cp!r} (expected 'defense_wins')")

    return issues


# ---------------------------------------------------------------------------
# Source readers
# ---------------------------------------------------------------------------


def read_synthetic_cases(experiment_dir: Path) -> list[dict]:
    """
    Read all cases_*.json batch files from the experiment directory.
    These are the assembled outputs from orchestrator.py --assemble.
    """
    batch_files = sorted(experiment_dir.glob("cases_*.json"))
    if not batch_files:
        console.print("  [dim]No cases_*.json batch files found in experiment root.[/dim]")
        return []

    cases = []
    for f in batch_files:
        try:
            batch = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(batch, list):
                cases.extend(batch)
                console.print(f"  [green]✓[/green] {f.name}: {len(batch)} cases")
            else:
                console.print(f"  [yellow]✗ {f.name}: not a JSON array, skipping[/yellow]")
        except (json.JSONDecodeError, OSError) as exc:
            console.print(f"  [red]✗ {f.name}: read error — {exc}[/red]")

    return cases


def read_rc_cases(rc_candidates_dir: Path) -> list[dict]:
    """
    Read rc_cases_raw.json from the RC candidates directory.
    """
    rc_path = rc_candidates_dir / "rc_cases_raw.json"
    if not rc_path.exists():
        console.print(f"  [dim]No RC cases found at {rc_path} — skipping.[/dim]")
        return []
    try:
        cases = json.loads(rc_path.read_text(encoding="utf-8"))
        console.print(f"  [green]✓[/green] rc_cases_raw.json: {len(cases)} RC cases")
        return cases
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"  [red]✗ rc_cases_raw.json: read error — {exc}[/red]")
        return []


# ---------------------------------------------------------------------------
# Main normalization logic
# ---------------------------------------------------------------------------


def normalize_all(
    experiment_dir: Path,
    rc_candidates_dir: Path,
    output_path: Path,
    strict: bool = False,
    dry_run: bool = False,
) -> tuple[list[dict], list[str]]:
    """
    Normalize all sources, validate Schema B, return (cases, all_violations).
    """
    console.rule("[bold blue]normalize_cases.py[/bold blue]")
    console.print(f"Experiment dir:   {experiment_dir}")
    console.print(f"RC candidates:    {rc_candidates_dir}")
    console.print(f"Output:           {output_path}")
    console.print()

    # --- Read synthetic ---
    console.print("[bold]Reading synthetic cases...[/bold]")
    raw_synthetic = read_synthetic_cases(experiment_dir)
    console.print(f"  Total synthetic raw: {len(raw_synthetic)}")

    # --- Read RC ---
    console.print("\n[bold]Reading RC cases...[/bold]")
    raw_rc = read_rc_cases(rc_candidates_dir)
    console.print(f"  Total RC raw: {len(raw_rc)}")

    if not raw_synthetic and not raw_rc:
        console.print("\n[yellow]No cases found from any source.[/yellow]")
        console.print("Run orchestrator.py and/or rc_extractor.py --all first.")
        return [], []

    # --- Normalize ---
    normalized: list[dict] = []
    norm_errors: list[str] = []
    seen_ids: set[str] = set()

    console.print("\n[bold]Normalizing synthetic cases...[/bold]")
    n_synth_ok = n_synth_skip = 0
    for raw in raw_synthetic:
        case = normalize_synthetic_case(raw)
        if case is None:
            norm_errors.append(f"Synthetic {raw.get('case_id', '?')}: normalize returned None")
            n_synth_skip += 1
            continue
        cid = case["case_id"]
        if cid in seen_ids:
            console.print(f"  [yellow]Duplicate case_id {cid} — skipping[/yellow]")
            n_synth_skip += 1
            continue
        seen_ids.add(cid)
        normalized.append(case)
        n_synth_ok += 1
    console.print(f"  Normalized: {n_synth_ok}  Skipped: {n_synth_skip}")

    console.print("\n[bold]Normalizing RC cases...[/bold]")
    n_rc_ok = n_rc_skip = 0
    for raw in raw_rc:
        case = normalize_rc_case(raw)
        if case is None:
            norm_errors.append(f"RC {raw.get('report_id', '?')}: normalize returned None")
            n_rc_skip += 1
            continue
        cid = case["case_id"]
        if cid in seen_ids:
            console.print(f"  [yellow]Duplicate RC case_id {cid} — skipping[/yellow]")
            n_rc_skip += 1
            continue
        seen_ids.add(cid)
        normalized.append(case)
        n_rc_ok += 1
    console.print(f"  Normalized: {n_rc_ok}  Skipped: {n_rc_skip}")

    # --- Validate ---
    console.print(f"\n[bold]Validating {len(normalized)} cases against Schema B...[/bold]")
    all_violations: list[str] = list(norm_errors)
    valid_cases: list[dict] = []

    for case in normalized:
        violations = validate_schema_b(case)
        if violations:
            all_violations.extend(violations)
            if strict:
                continue  # drop invalid cases in strict mode
        valid_cases.append(case)

    n_violations = len(all_violations)
    if n_violations:
        console.print(f"  [yellow]{n_violations} validation issue(s) found:[/yellow]")
        for v in all_violations[:20]:
            console.print(f"    [yellow]• {v}[/yellow]")
        if n_violations > 20:
            console.print(f"    ... and {n_violations - 20} more")
    else:
        console.print(f"  [green]All {len(valid_cases)} cases passed Schema B validation[/green]")

    # --- Composition summary ---
    n_regular  = sum(1 for c in valid_cases if c.get("category") == "regular")
    n_mixed    = sum(1 for c in valid_cases if c.get("category") == "mixed")
    n_defense  = sum(1 for c in valid_cases if c.get("category") == "defense")
    n_rc       = sum(1 for c in valid_cases if c.get("is_real_paper_case", False))
    n_synth    = len(valid_cases) - n_rc

    n_critique = sum(
        1 for c in valid_cases
        if c.get("ground_truth", {}).get("correct_position") == "critique_wins"
    )
    n_defense_wins = sum(
        1 for c in valid_cases
        if c.get("category") == "regular"
        and c.get("ground_truth", {}).get("correct_position") == "defense_wins"
    )

    table = Table(title="Normalized Pool Composition", show_header=True)
    table.add_column("Dimension")
    table.add_column("Count", justify="right")
    table.add_column("v7 Target")
    table.add_row("Total cases",              str(len(valid_cases)), "≥ 280")
    table.add_row("  Regular (critique_wins + defense_wins)", str(n_regular), "≥ 160")
    table.add_row("    Critique (critique_wins)",  str(n_critique),    "≥ 120")
    table.add_row("    Defense_wins (regular)",    str(n_defense_wins), "≥ 40")
    table.add_row("  Mixed",                  str(n_mixed),   "≥ 80")
    table.add_row("  Defense (category)",     str(n_defense), "≥ 40")
    table.add_row("  RC (real paper)",        str(n_rc),      "")
    table.add_row("  Synthetic",              str(n_synth),   "")
    console.print(table)

    # Phase 1 decision gate check
    console.print("\n[bold]Phase 1 decision gate:[/bold]")
    n_rc_regular = sum(
        1 for c in valid_cases
        if c.get("is_real_paper_case") and c.get("category") == "regular"
    )
    n_rc_mixed = sum(
        1 for c in valid_cases
        if c.get("is_real_paper_case") and c.get("category") == "mixed"
    )
    if n_rc_regular >= 60 and n_rc_mixed >= 20:
        console.print("  [green]GATE PASS: RC yield sufficient (regular ≥ 60 AND mixed ≥ 20)[/green]")
    elif n_rc_regular >= 60:
        console.print(
            f"  [yellow]PARTIAL: RC regular ≥ 60 but mixed < 20 "
            f"(RC mixed={n_rc_mixed}). Run synthetic mixed pipeline to supplement.[/yellow]"
        )
    else:
        console.print(
            f"  [yellow]LOW YIELD: RC regular < 60 (got {n_rc_regular}). "
            "Supplement with synthetic cases.[/yellow]"
        )

    if dry_run:
        console.print(f"\n[dim]DRY RUN: would write {len(valid_cases)} cases to {output_path}[/dim]")
        return valid_cases, all_violations

    # --- Write ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(valid_cases, indent=2), encoding="utf-8")
    console.print(f"\n[green]✓ Wrote {len(valid_cases)} normalized cases → {output_path}[/green]")

    return valid_cases, all_violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="normalize_cases.py — normalize RC + synthetic to Schema B"
    )
    parser.add_argument(
        "--output",
        default="benchmark_cases_v7_raw.json",
        help="Output filename in experiment root (default: benchmark_cases_v7_raw.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Drop cases that fail Schema B validation (default: warn but keep)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be normalized without writing output",
    )
    args = parser.parse_args()

    output_path = EXPERIMENT_DIR / args.output
    _, violations = normalize_all(
        experiment_dir=EXPERIMENT_DIR,
        rc_candidates_dir=RC_CANDIDATES_DIR,
        output_path=output_path,
        strict=args.strict,
        dry_run=args.dry_run,
    )

    if violations and args.strict:
        console.print(f"\n[red]Strict mode: {len(violations)} violations found. Exiting.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
