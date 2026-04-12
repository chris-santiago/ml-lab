# /// script
# requires-python = ">=3.11"
# ///
"""
Minimum test: ensemble_3x vs baseline on IDR (paired bootstrap).

This is the formally untested gap from v6: H2 compared debate vs ensemble,
but ensemble vs baseline was only descriptive (+0.1005 IDR gap).
This script runs the paired bootstrap on existing v6_results.json data.
No new LLM calls required.
"""

import json
import random

random.seed(42)


def bootstrap_paired_mean_diff(pairs, n_boot=10_000, one_sided=False):
    n = len(pairs)
    if n == 0:
        return None, None, None, None
    case_diffs = [a - b for a, b in pairs]
    obs = sum(case_diffs) / n
    boot_means = []
    for _ in range(n_boot):
        sample = [case_diffs[random.randint(0, n - 1)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    if one_sided:
        ci_lo = boot_means[int(0.05 * n_boot)]
        ci_hi = boot_means[int(0.95 * n_boot)]
    else:
        ci_lo = boot_means[int(0.025 * n_boot)]
        ci_hi = boot_means[int(0.975 * n_boot)]
    p_val = sum(1 for d in boot_means if d <= 0) / n_boot
    return round(obs, 4), round(ci_lo, 4), round(ci_hi, 4), round(p_val, 4)


def get_baseline_idr(case, condition="baseline"):
    runs = case.get(condition, {}).get("runs", [])
    idrs = [r["scores"]["IDR"] for r in runs if r.get("scores", {}).get("IDR") is not None]
    return sum(idrs) / len(idrs) if idrs else None


def get_ensemble_idr(case):
    meta = case.get("ensemble_3x", {}).get("_ensemble_meta", {})
    return meta.get("union_idr")


with open("self_debate_experiment_v6/v6_results.json") as f:
    data = json.load(f)

cases = data["cases"]

# --- Filter sets (matching v6_analysis.py convention) ---
regular = [c for c in cases if c.get("category") == "regular"]
critique = [c for c in regular if c.get("correct_position") == "critique"]

print(f"Total cases: {len(cases)}")
print(f"Regular cases: {len(regular)}")
print(f"Critique-only cases: {len(critique)}")
print()

for label, subset in [("All regular (n=80)", regular), ("Critique only (n=60)", critique)]:
    pairs = []
    skipped = 0
    for c in subset:
        ens_idr = get_ensemble_idr(c)
        base_idr = get_baseline_idr(c)
        if ens_idr is None or base_idr is None:
            skipped += 1
            continue
        pairs.append((ens_idr, base_idr))

    obs, ci_lo, ci_hi, p_val = bootstrap_paired_mean_diff(pairs, n_boot=10_000)
    ens_mean = sum(p[0] for p in pairs) / len(pairs)
    base_mean = sum(p[1] for p in pairs) / len(pairs)
    verdict = "PASS (ensemble > baseline)" if (ci_lo or 0) > 0 else ("INCONCLUSIVE" if (ci_hi or 0) > 0 else "FAIL")

    print(f"=== {label} ===")
    print(f"  n pairs:       {len(pairs)}  (skipped: {skipped})")
    print(f"  ensemble IDR:  {ens_mean:.4f}")
    print(f"  baseline IDR:  {base_mean:.4f}")
    print(f"  observed diff: {obs:+.4f}")
    print(f"  95% CI:        [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"  p (one-sided): {p_val:.4f}")
    print(f"  verdict:       {verdict}")
    print()
