# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Compute v5 ensemble FC mean with union-of-issues IDR substituted in.

Union IDR rule: an issue is found if ANY assessor (critic) found it — not majority.
This replaces the majority-vote suppression that depresses ensemble IDR.

FC dims: IDR (rescored), IDP (rescored), DRQ, FVC.
DC is excluded (diagnostic-only per ENSEMBLE_ANALYSIS.md, DC=FVC everywhere).
ETD: N/A for all v5 cases (no mixed cases).

Baseline to reproduce: ENSEMBLE_ANALYSIS.md ensemble FC mean = 0.9247.
  - v5_results.json FC mean = 0.9366 (uses original pre-rescore IDR/IDP)
  - ENSEMBLE_ANALYSIS.md FC mean = 0.9247 (uses rescored IDR/IDP)
  - Source of difference: rescore pass lowered IDR from ~0.9 to 0.7679

Strategy:
  - Critique cases (n=80): rescored IDR + rescored IDP from rescore file + DRQ/FVC from results
  - Defense cases (n=30): IDR=None, IDP=None (N/A by protocol) + DRQ/FVC from results
  - Union substitution only changes IDR for critique cases
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent

# --- Load data ---
with open(BASE / "v5_rescored_idr_idp.json") as f:
    rescore = json.load(f)
with open(BASE / "v5_results.json") as f:
    v5 = json.load(f)

rescore_scores = rescore["scores"]
cases = v5["cases"]

# --- Build rescore lookup: (case_id, run_num) -> entry ---
# Keys: eval_scenario_616_ensemble_run2.json OR hyp_077_ensemble_run3.json
def parse_key(key: str):
    m = re.match(r"(.+)_ensemble_run(\d+)\.json", key)
    if not m:
        return None, None
    return m.group(1), int(m.group(2))

rescore_lookup = {}
for key, entry in rescore_scores.items():
    if "ensemble" not in key:
        continue
    case_id, run_num = parse_key(key)
    if case_id is None:
        continue
    rescore_lookup[(case_id, run_num)] = entry

print(f"Rescore lookup: {len(rescore_lookup)} ensemble entries (critique cases only)")
print(f"Cases in v5_results.json: {len(cases)}")
print()

# --- Union IDR computation ---
def compute_union_idr(idr_detail: dict) -> float | None:
    """Union rule: issue is found if any assessor found it."""
    if not idr_detail:
        return None
    issue_scores = []
    for issue_data in idr_detail.values():
        assessors = issue_data.get("assessor_results", [])
        if assessors:
            union_found = any(a["found"] for a in assessors)
        else:
            union_found = issue_data.get("found", False)
        issue_scores.append(1.0 if union_found else 0.0)
    return sum(issue_scores) / len(issue_scores)

def fc_mean(*vals) -> float | None:
    """FC mean over non-None values."""
    valid = [v for v in vals if v is not None]
    return sum(valid) / len(valid) if valid else None

# --- Per-case per-run computation ---
case_results = []

for case in cases:
    case_id = case["case_id"]
    correct_pos = case.get("correct_position", "critique")
    ens_data = case.get("ensemble", {})
    if not ens_data or "runs" not in ens_data:
        continue

    runs = ens_data["runs"]
    is_critique = (correct_pos == "critique")

    run_maj_fc = []
    run_union_fc = []
    run_maj_idr = []
    run_union_idr = []

    for i, run in enumerate(runs):
        run_num = i + 1
        raw_scores = run.get("scores", {})
        drq = raw_scores.get("DRQ")
        fvc = raw_scores.get("FVC")

        if is_critique:
            entry = rescore_lookup.get((case_id, run_num))
            if entry is None:
                # Fallback: use raw scores (hyp_ case IDs not in rescore? Check)
                rescored_idr = raw_scores.get("IDR")
                rescored_idp = raw_scores.get("IDP")
                idr_detail = {}
            else:
                rescored_idr = entry.get("rescored_idr")
                rescored_idp = entry.get("rescored_idp")
                idr_detail = entry.get("idr_detail", {})

            # Majority FC
            maj_fc = fc_mean(rescored_idr, rescored_idp, drq, fvc)
            run_maj_fc.append(maj_fc)
            if rescored_idr is not None:
                run_maj_idr.append(rescored_idr)

            # Union IDR
            union_idr = compute_union_idr(idr_detail) if idr_detail else rescored_idr
            union_fc = fc_mean(union_idr, rescored_idp, drq, fvc)
            run_union_fc.append(union_fc)
            if union_idr is not None:
                run_union_idr.append(union_idr)

        else:
            # Defense case: IDR=None, IDP=None by protocol
            # FC uses only DRQ and FVC
            def_fc = fc_mean(None, None, drq, fvc)  # = (drq + fvc) / 2
            run_maj_fc.append(def_fc)
            run_union_fc.append(def_fc)  # unchanged for defense

    def safe_mean(lst):
        valid = [x for x in lst if x is not None]
        return sum(valid) / len(valid) if valid else None

    case_results.append({
        "case_id": case_id,
        "correct_pos": correct_pos,
        "majority_fc": safe_mean(run_maj_fc),
        "union_fc": safe_mean(run_union_fc),
        "majority_idr": safe_mean(run_maj_idr),
        "union_idr": safe_mean(run_union_idr),
    })

# --- Grand means ---
all_maj_fc = [r["majority_fc"] for r in case_results if r["majority_fc"] is not None]
all_union_fc = [r["union_fc"] for r in case_results if r["union_fc"] is not None]
critique_maj_idr = [r["majority_idr"] for r in case_results if r["correct_pos"] == "critique" and r["majority_idr"] is not None]
critique_union_idr = [r["union_idr"] for r in case_results if r["correct_pos"] == "critique" and r["union_idr"] is not None]

grand_maj_fc = sum(all_maj_fc) / len(all_maj_fc)
grand_union_fc = sum(all_union_fc) / len(all_union_fc)
grand_maj_idr = sum(critique_maj_idr) / len(critique_maj_idr)
grand_union_idr = sum(critique_union_idr) / len(critique_union_idr)

# Critique-only FC
crit_maj_fc = [r["majority_fc"] for r in case_results if r["correct_pos"] == "critique" and r["majority_fc"] is not None]
crit_union_fc = [r["union_fc"] for r in case_results if r["correct_pos"] == "critique" and r["union_fc"] is not None]
def_fc_all = [r["majority_fc"] for r in case_results if r["correct_pos"] == "defense" and r["majority_fc"] is not None]

print("=" * 65)
print("  v5 ENSEMBLE FC MEAN — MAJORITY vs UNION-OF-ISSUES IDR")
print("=" * 65)
print(f"  Cases:  {len(case_results)} total  "
      f"({len(crit_maj_fc)} critique, {len(def_fc_all)} defense)")
print()
print("  ── IDR (critique cases only) ─────────────────────────────")
print(f"  Majority IDR mean:      {grand_maj_idr:.4f}   [expected: 0.7679]")
print(f"  Union IDR mean:         {grand_union_idr:.4f}")
print(f"  IDR delta:              +{grand_union_idr - grand_maj_idr:.4f}")
print()
print("  ── FC mean (4 dims: IDR, IDP, DRQ, FVC) ─────────────────")
print(f"  Majority FC mean:       {grand_maj_fc:.4f}   [expected: 0.9247]")
print(f"  Union FC mean:          {grand_union_fc:.4f}")
print(f"  FC delta:               +{grand_union_fc - grand_maj_fc:.4f}")
print()

# Key comparison table
print("  ── Condition comparison ──────────────────────────────────")
print(f"  {'Condition':<25} {'FC mean':>8}  {'vs baseline':>12}  {'vs isolated':>12}")
print(f"  {'─'*25} {'─'*8}  {'─'*12}  {'─'*12}")
print(f"  {'isolated_debate':<25} {'0.9477':>8}  {'+0.0211':>12}  {'—':>12}")
print(f"  {'baseline':<25} {'0.9266':>8}  {'—':>12}  {'-0.0211':>12}")
print(f"  {'ensemble (majority IDR)':<25} {grand_maj_fc:>8.4f}  {grand_maj_fc - 0.9266:>+12.4f}  {grand_maj_fc - 0.9477:>+12.4f}")
print(f"  {'ensemble (union IDR)':<25} {grand_union_fc:>8.4f}  {grand_union_fc - 0.9266:>+12.4f}  {grand_union_fc - 0.9477:>+12.4f}")
print()

print("  ── Per-stratum FC means ──────────────────────────────────")
print(f"  critique cases (n={len(crit_maj_fc)}):")
print(f"    majority FC:  {sum(crit_maj_fc)/len(crit_maj_fc):.4f}")
print(f"    union FC:     {sum(crit_union_fc)/len(crit_union_fc):.4f}")
print(f"    delta:        +{(sum(crit_union_fc)/len(crit_union_fc)) - (sum(crit_maj_fc)/len(crit_maj_fc)):.4f}")
print(f"  defense cases (n={len(def_fc_all)}):")
print(f"    FC mean:      {sum(def_fc_all)/len(def_fc_all):.4f}  (unchanged — IDR N/A)")
print()

# --- Run-level IDR change stats ---
changed_runs = 0
total_idr_runs = 0
idr_gains = []
for case in cases:
    case_id = case["case_id"]
    if case.get("correct_position") != "critique":
        continue
    ens_data = case.get("ensemble", {})
    if not ens_data:
        continue
    for i in range(len(ens_data["runs"])):
        run_num = i + 1
        entry = rescore_lookup.get((case_id, run_num))
        if not entry:
            continue
        idr_detail = entry.get("idr_detail", {})
        if not idr_detail:
            continue
        total_idr_runs += 1
        maj_idr = entry["rescored_idr"]
        union_idr = compute_union_idr(idr_detail)
        if union_idr is not None and union_idr != maj_idr:
            changed_runs += 1
            idr_gains.append(union_idr - maj_idr)

print(f"  ── Run-level IDR change stats ────────────────────────────")
print(f"  Critique ensemble runs:            {total_idr_runs}")
print(f"  Runs where union IDR > majority:   {changed_runs}/{total_idr_runs}  ({100*changed_runs/total_idr_runs:.1f}%)")
if idr_gains:
    print(f"  Mean IDR gain per changed run:     +{sum(idr_gains)/len(idr_gains):.4f}")
    print(f"  Max IDR gain in a single run:      +{max(idr_gains):.4f}")
print()
print("  ── Interpretation ────────────────────────────────────────")
print(f"  Union IDR (+{grand_union_idr - grand_maj_idr:.4f} on IDR) → +{grand_union_fc - grand_maj_fc:.4f} on FC mean")
print(f"  Multiplier: 1/{4} (IDR is 1 of 4 FC dims) × correction factor")
print(f"  Expected naive: +{(grand_union_idr - grand_maj_idr)/4:.4f}  Actual: +{grand_union_fc - grand_maj_fc:.4f}")
print()
note = ""
if grand_union_fc > 0.9266:
    note = f"  ★ Union ensemble FC ({grand_union_fc:.4f}) > baseline ({0.9266:.4f}) by {grand_union_fc - 0.9266:.4f}"
if grand_union_fc > 0.9477:
    note += f"\n  ★ Union ensemble FC ({grand_union_fc:.4f}) > isolated_debate (0.9477)"
if note:
    print(note)
