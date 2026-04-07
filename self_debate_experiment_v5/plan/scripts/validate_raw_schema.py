# validate_raw_schema.py
# /// script
# requires-python = ">=3.10"
# ///
"""
V4 Raw Output Schema Validator

Enforces that all files in v5_raw_outputs/ conform to the v5 raw output contract.
For forced_multiround specifically, validates both required fields:
  - debate_rounds (int >= 2)
  - rounds (list of per-round snapshots, len >= 2)

Run BEFORE self_debate_poc.py. The scoring engine does not read debate_rounds or rounds,
so a field mismatch there goes undetected through all 750+ scored runs and only surfaces
in Phase 10.5 post-run audit — after scoring is complete and hard to redo.

Usage:
    uv run plan/scripts/validate_raw_schema.py [--raw-dir v5_raw_outputs]

Exit 0 if all checks pass. Exit 1 if any errors found.
"""

import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--raw-dir', default='v5_raw_outputs')
args, _ = parser.parse_known_args()

RAW_DIR = Path.cwd() / args.raw_dir

CONDITIONS = {'isolated_debate', 'multiround', 'forced_multiround', 'ensemble', 'baseline'}
VALID_VERDICTS = {'critique_wins', 'defense_wins', 'empirical_test_agreed'}

# Fields required in every output file
BASE_REQUIRED = ['case_id', 'run', 'condition', 'verdict', 'issues_found', 'all_issues_raised']

# Additional fields required for multiround and forced_multiround
MULTIROUND_REQUIRED = ['debate_rounds', 'points_resolved', 'points_force_resolved',
                       'point_resolution_rate']

# fields required in each entry of the forced_multiround rounds array (R1 hollow-round fix)
ROUND_SNAPSHOT_REQUIRED = ['round', 'verdict', 'points_resolved', 'points_open']

errors = []
warnings = []


def validate_file(path: Path) -> None:
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception as e:
        errors.append(f"{path.name}: JSON parse error — {e}")
        return

    name = path.name
    condition = d.get('condition', '')

    # --- Base schema ---
    for field in BASE_REQUIRED:
        if field not in d:
            errors.append(f"{name}: missing required field '{field}'")

    # Condition field validity
    if condition and condition not in CONDITIONS:
        warnings.append(f"{name}: unrecognized condition '{condition}'")

    # Verdict validity
    verdict = d.get('verdict')
    if verdict and verdict not in VALID_VERDICTS:
        warnings.append(f"{name}: unexpected verdict value '{verdict}'")

    # issues_found and all_issues_raised must be lists
    for list_field in ('issues_found', 'all_issues_raised'):
        val = d.get(list_field)
        if val is not None and not isinstance(val, list):
            errors.append(f"{name}: '{list_field}' must be a list, got {type(val).__name__}")

    # --- Multiround / forced_multiround extended fields ---
    if condition in ('multiround', 'forced_multiround'):
        for field in MULTIROUND_REQUIRED:
            if field not in d:
                errors.append(f"{name}: multiround condition missing required field '{field}'")

    # --- Forced_multiround: rounds array (R4 schema contract) ---
    if condition == 'forced_multiround':
        debate_rounds = d.get('debate_rounds')
        if debate_rounds is None:
            errors.append(
                f"{name}: forced_multiround missing 'debate_rounds' — "
                "Phase 10.5 Check #6 reads this field; scoring engine does not, "
                "so this mismatch is invisible until the post-run audit"
            )
        elif not isinstance(debate_rounds, int):
            errors.append(
                f"{name}: 'debate_rounds' must be int, got {type(debate_rounds).__name__}"
            )
        elif debate_rounds < 2:
            errors.append(
                f"{name}: forced_multiround 'debate_rounds' = {debate_rounds} "
                "(must be >= 2 per pre-registered protocol)"
            )

        rounds = d.get('rounds')
        if rounds is None:
            errors.append(
                f"{name}: forced_multiround missing 'rounds' array — "
                "Phase 10.5 Check #7 (hollow-round detection) requires this field; "
                "without it, hollow_rate = 0.0 (silent false negative)"
            )
        elif not isinstance(rounds, list):
            errors.append(
                f"{name}: 'rounds' must be list, got {type(rounds).__name__}"
            )
        else:
            if len(rounds) < 2:
                errors.append(
                    f"{name}: forced_multiround 'rounds' has {len(rounds)} entry "
                    "(must be >= 2; forced protocol requires minimum 2 exchange rounds)"
                )
            # Per-round snapshot schema
            for i, snapshot in enumerate(rounds):
                if not isinstance(snapshot, dict):
                    errors.append(f"{name}: rounds[{i}] must be a dict, got {type(snapshot).__name__}")
                    continue
                for field in ROUND_SNAPSHOT_REQUIRED:
                    if field not in snapshot:
                        errors.append(
                            f"{name}: rounds[{i}] missing field '{field}' "
                            "(required for hollow-round detection)"
                        )
                # points_resolved must be int (not float, not None)
                pr = snapshot.get('points_resolved')
                if pr is not None and not isinstance(pr, int):
                    errors.append(
                        f"{name}: rounds[{i}]['points_resolved'] must be int, "
                        f"got {type(pr).__name__}"
                    )

            # Consistency check: len(rounds) should equal debate_rounds
            if isinstance(debate_rounds, int) and len(rounds) != debate_rounds:
                warnings.append(
                    f"{name}: len(rounds)={len(rounds)} != debate_rounds={debate_rounds} "
                    "(they should agree)"
                )


if not RAW_DIR.exists():
    print(f"ERROR: {RAW_DIR} does not exist. Run Phase 6 first.")
    sys.exit(1)

files = sorted(RAW_DIR.glob('*.json'))
if not files:
    print(f"ERROR: No JSON files found in {RAW_DIR}")
    sys.exit(1)

for path in files:
    validate_file(path)

# Summary stats
fm_files = [p for p in files if 'forced_multiround' in p.name]
mr_files = [p for p in files if '_multiround_' in p.name and 'forced' not in p.name]

print(f"Schema validation: {len(files)} files checked")
print(f"  forced_multiround: {len(fm_files)}  multiround: {len(mr_files)}  other: {len(files) - len(fm_files) - len(mr_files)}")
print(f"  Errors: {len(errors)}  Warnings: {len(warnings)}")

if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print(f"  WARN: {w}")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  ERR:  {e}")
    print(
        "\nSchema validation FAILED.\n"
        "Fix all errors before running self_debate_poc.py.\n"
        "The scoring engine silently ignores debate_rounds and rounds — schema errors\n"
        "are invisible to scoring but break Phase 10.5 audit checks."
    )
    sys.exit(1)

print("\nSchema validation PASSED. Safe to run self_debate_poc.py.")
