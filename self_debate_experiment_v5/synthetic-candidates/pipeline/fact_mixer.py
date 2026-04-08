# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Stage 1.5 — Fact Mixer

Takes Stage 1 mechanism blueprints and produces two views of the methodology facts:
  - writer_view: shuffled facts with no role labels (for Stages 2-3)
  - metadata_view: same facts with role codes (for Stage 4)

Usage:
    uv run fact_mixer.py --input stage1_output.json --output-dir pipeline/stage1.5/
    uv run fact_mixer.py --input stage1_output.json --case mech_001  # single case
"""

import argparse
import json
import random
import sys
from pathlib import Path


def mix_facts(blueprint: dict, seed: int | None = None) -> tuple[dict, dict]:
    """
    Produce writer_view and metadata_view for a single mechanism blueprint.

    Writer view: list of facts with no role codes — all facts look identical.
    Metadata view: same list with role codes attached.

    The key isolation property: the writer view is identical to the metadata
    view except role codes are stripped. The memo writer cannot distinguish
    flaw facts from decoy or neutral facts.
    """
    rng = random.Random(seed)

    mechanism_id = blueprint["mechanism_id"]
    flaw_facts = blueprint.get("flaw_facts", [])
    decoy_facts = blueprint.get("decoy_facts", [])
    neutral_facts = blueprint.get("neutral_facts", [])

    # Build unified fact list with role codes (metadata view)
    all_facts_with_roles = []

    for fact in flaw_facts:
        all_facts_with_roles.append({
            "fact_id": fact["fact_id"],
            "role": "flaw",
            "phrasing": fact["neutralized_phrasing"],
            "domain_context": fact.get("domain_context", ""),
            # Role-specific metadata (not visible in writer view)
            "_addressed_but_incorrectly": fact["fact_id"] == blueprint.get("addressed_but_incorrectly_fact_id"),
            "_compound": fact["fact_id"] in blueprint.get("compound_fact_ids", []),
            "_compound_note": blueprint.get("compound_note") if fact["fact_id"] in blueprint.get("compound_fact_ids", []) else None,
        })

    for fact in decoy_facts:
        all_facts_with_roles.append({
            "fact_id": fact["fact_id"],
            "role": "decoy",
            "phrasing": fact["neutralized_phrasing"],
            "domain_context": fact.get("domain_context", ""),
            "_must_not_claim_type": fact.get("must_not_claim_type"),
            "_requires_external_knowledge": fact.get("requires_external_knowledge"),
        })

    for fact in neutral_facts:
        all_facts_with_roles.append({
            "fact_id": fact["fact_id"],
            "role": "neutral",
            "phrasing": fact["neutralized_phrasing"],
            "domain_context": "",
        })

    # Shuffle — same order for both views (reproducible with seed)
    rng.shuffle(all_facts_with_roles)

    # Writer view: strip role codes and internal metadata
    writer_facts = []
    for fact in all_facts_with_roles:
        writer_facts.append({
            "fact_id": fact["fact_id"],
            "phrasing": fact["phrasing"],
            "domain_context": fact["domain_context"],
        })

    writer_view = {
        "mechanism_id": mechanism_id,
        "target_domain": blueprint.get("target_domain", ""),
        "domain_specific_detail": blueprint.get("domain_specific_detail", ""),
        "category": blueprint.get("category", ""),
        "case_type": blueprint.get("case_type", ""),
        "facts": writer_facts,
        "total_facts": len(writer_facts),
        "note": "Facts are shuffled. Integrate all facts into the scenario brief naturally.",
    }

    # Metadata view: full role codes preserved
    metadata_view = {
        "mechanism_id": mechanism_id,
        "abstract_mechanism": blueprint.get("abstract_mechanism", ""),
        "flaw_type": blueprint.get("flaw_type", ""),
        "source_reference": blueprint.get("source_reference", ""),
        "ideal_resolution_type": blueprint.get("ideal_resolution_type", ""),
        "addressed_but_incorrectly_fact_id": blueprint.get("addressed_but_incorrectly_fact_id"),
        "addressed_but_incorrectly_justification": blueprint.get("addressed_but_incorrectly_justification"),
        "compound_fact_ids": blueprint.get("compound_fact_ids", []),
        "compound_note": blueprint.get("compound_note"),
        "defense_wins_false_concern_signals": blueprint.get("defense_wins_false_concern_signals"),
        "facts": all_facts_with_roles,
    }

    return writer_view, metadata_view


def process_batch(blueprints: list[dict], output_dir: Path, seed: int | None = None) -> None:
    """Process a batch of mechanism blueprints and write stage1.5 output files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    writer_views = []
    metadata_views = []

    for i, blueprint in enumerate(blueprints):
        mechanism_id = blueprint.get("mechanism_id", f"mech_{i:03d}")
        case_seed = (seed + i) if seed is not None else None

        writer_view, metadata_view = mix_facts(blueprint, seed=case_seed)
        writer_views.append(writer_view)
        metadata_views.append(metadata_view)

        # Write per-case files
        (output_dir / f"{mechanism_id}_writer_view.json").write_text(
            json.dumps(writer_view, indent=2), encoding="utf-8"
        )
        (output_dir / f"{mechanism_id}_metadata_view.json").write_text(
            json.dumps(metadata_view, indent=2), encoding="utf-8"
        )
        print(f"[{mechanism_id}] Mixed {len(writer_view['facts'])} facts "
              f"({sum(1 for f in metadata_view['facts'] if f['role'] == 'flaw')} flaw, "
              f"{sum(1 for f in metadata_view['facts'] if f['role'] == 'decoy')} decoy, "
              f"{sum(1 for f in metadata_view['facts'] if f['role'] == 'neutral')} neutral)")

    # Write batch files
    (output_dir / "all_writer_views.json").write_text(
        json.dumps(writer_views, indent=2), encoding="utf-8"
    )
    (output_dir / "all_metadata_views.json").write_text(
        json.dumps(metadata_views, indent=2), encoding="utf-8"
    )

    print(f"\n[fact_mixer] Processed {len(blueprints)} blueprints → {output_dir}/")
    print(f"  Writer views:   {output_dir}/all_writer_views.json")
    print(f"  Metadata views: {output_dir}/all_metadata_views.json")


KNOWN_SOURCES = {"real_paper", "benchmark"}


def validate_pipeline_source(blueprints: list[dict], expected_source: str | None = None) -> list[str]:
    """
    Validate that all blueprints carry a consistent pipeline_source tag.

    Catches two failure modes:
      1. Mixed batch — blueprints from different Stage 1 variants concatenated together
      2. Wrong source — user ran real_paper extractor when benchmark was intended (or vice versa)
    """
    errors = []
    sources_found = set()

    for blueprint in blueprints:
        mech_id = blueprint.get("mechanism_id", "unknown")
        source = blueprint.get("pipeline_source")
        if source is None:
            errors.append(f"{mech_id}: missing pipeline_source — was this generated by a Stage 1 prompt?")
        elif source not in KNOWN_SOURCES:
            errors.append(f"{mech_id}: unknown pipeline_source '{source}' (expected one of: {KNOWN_SOURCES})")
        else:
            sources_found.add(source)

    if len(sources_found) > 1:
        errors.append(f"Mixed batch: blueprints from multiple sources found: {sources_found}. "
                      "Do not concatenate real_paper and benchmark blueprints in the same batch.")

    if expected_source and not errors:
        actual = next(iter(sources_found), None)
        if actual and actual != expected_source:
            errors.append(f"Source mismatch: expected '{expected_source}' but batch contains '{actual}'. "
                          "Check that you ran the correct Stage 1 extractor.")

    return errors


def validate_blueprint(blueprint: dict) -> list[str]:
    """Return list of validation errors for a blueprint."""
    errors = []
    mech_id = blueprint.get("mechanism_id", "unknown")

    if blueprint.get("case_type") == "defense_wins":
        if not blueprint.get("defense_wins_false_concern_signals"):
            errors.append(f"{mech_id}: defense_wins case missing defense_wins_false_concern_signals")
        return errors  # defense_wins cases don't need flaw_facts

    flaw_facts = blueprint.get("flaw_facts", [])
    decoy_facts = blueprint.get("decoy_facts", [])

    if not flaw_facts:
        errors.append(f"{mech_id}: missing flaw_facts")
    if not decoy_facts:
        errors.append(f"{mech_id}: missing decoy_facts")
    if len(flaw_facts) + len(decoy_facts) < 4:
        errors.append(f"{mech_id}: too few total facts ({len(flaw_facts) + len(decoy_facts)} — need ≥4)")

    abi_id = blueprint.get("addressed_but_incorrectly_fact_id")
    if not abi_id:
        errors.append(f"{mech_id}: missing addressed_but_incorrectly_fact_id")
    elif abi_id not in {f["fact_id"] for f in flaw_facts}:
        errors.append(f"{mech_id}: addressed_but_incorrectly_fact_id '{abi_id}' not in flaw_facts")

    compound_ids = blueprint.get("compound_fact_ids", [])
    if len(compound_ids) < 2:
        errors.append(f"{mech_id}: compound_fact_ids must have ≥2 entries")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1.5 — Fact Mixer")
    parser.add_argument("--input", required=True, help="Path to Stage 1 output JSON (array of blueprints)")
    parser.add_argument("--output-dir", default="pipeline/stage1.5", help="Output directory for mixed fact files")
    parser.add_argument("--case", help="Process only this mechanism_id (for testing)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible shuffling")
    parser.add_argument("--validate-only", action="store_true", help="Validate blueprints without writing output")
    parser.add_argument("--expected-source", choices=list(KNOWN_SOURCES),
                        help="Enforce that all blueprints carry this pipeline_source tag (real_paper or benchmark)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        blueprints = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(blueprints, list):
        blueprints = [blueprints]

    # Filter to single case if requested
    if args.case:
        blueprints = [b for b in blueprints if b.get("mechanism_id") == args.case]
        if not blueprints:
            print(f"ERROR: No blueprint found with mechanism_id='{args.case}'", file=sys.stderr)
            sys.exit(1)

    # Validate pipeline source first (catches wrong extractor before per-blueprint checks)
    all_errors = validate_pipeline_source(blueprints, expected_source=args.expected_source)

    # Per-blueprint validation
    for blueprint in blueprints:
        all_errors.extend(validate_blueprint(blueprint))

    if all_errors:
        print("VALIDATION ERRORS:", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    if args.validate_only:
        print(f"[fact_mixer] Validation passed: {len(blueprints)} blueprints OK")
        return

    output_dir = Path(args.output_dir)
    process_batch(blueprints, output_dir, seed=args.seed)


if __name__ == "__main__":
    main()
