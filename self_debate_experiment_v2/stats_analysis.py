"""
Statistical analysis for Self-Debate Protocol v2.

Addresses Issue 8 (open_issues.md): bootstrap confidence intervals and
paired Wilcoxon signed-rank tests on per-case deltas.

Produces stats_results.json with all outputs.

Usage:
    cd self_debate_experiment_v2/
    python stats_analysis.py
"""

import json
import random
import math
import os

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)


def extract_means(results_json):
    """Return {case_id: (debate_mean, baseline_mean)} from self_debate_results.json."""
    return {
        c["case_id"]: (c["debate_mean"], c["baseline_mean"])
        for c in results_json["cases"]
    }


def extract_ensemble_means(ensemble_json):
    """Return {case_id: ensemble_mean} from clean_ensemble_results.json."""
    return {c["case_id"]: c["ensemble_mean"] for c in ensemble_json["cases"]}


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_ci(values, stat_fn, n_resamples=10_000, ci=0.95, seed=42):
    """
    Bootstrap confidence interval for stat_fn applied to values.
    Returns (point_estimate, lower, upper).
    """
    rng = random.Random(seed)
    n = len(values)
    point = stat_fn(values)
    bootstrap_stats = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(n)]
        bootstrap_stats.append(stat_fn(sample))
    bootstrap_stats.sort()
    alpha = (1 - ci) / 2
    lo_idx = int(math.floor(alpha * n_resamples))
    hi_idx = int(math.ceil((1 - alpha) * n_resamples)) - 1
    return point, bootstrap_stats[lo_idx], bootstrap_stats[hi_idx]


def mean(values):
    return sum(values) / len(values)


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank test (two-sided)
# ---------------------------------------------------------------------------

def wilcoxon_signed_rank(x, y):
    """
    Paired two-sided Wilcoxon signed-rank test.
    Returns (W_statistic, p_value_approx, n_nonzero).
    Uses normal approximation for n >= 10.
    """
    diffs = [a - b for a, b in zip(x, y)]
    nonzero = [(abs(d), d) for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return 0, 1.0, 0

    # Rank absolute differences (average ties)
    nonzero.sort(key=lambda t: t[0])
    ranks = []
    i = 0
    while i < n:
        j = i
        while j < n and nonzero[j][0] == nonzero[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2  # 1-indexed average
        for k in range(i, j):
            ranks.append((avg_rank, nonzero[k][1]))
        i = j

    W_plus = sum(r for r, d in ranks if d > 0)
    W_minus = sum(r for r, d in ranks if d < 0)
    W = min(W_plus, W_minus)

    # Normal approximation (valid for n >= 10)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    # Continuity correction
    z = (W - mu + 0.5) / sigma if W > mu else (W - mu - 0.5) / sigma
    z = abs(z)

    # Two-sided p-value via standard normal CDF approximation
    p = 2 * (1 - _norm_cdf(z))
    return W, round(p, 6), n


def _norm_cdf(x):
    """Standard normal CDF using error function approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ---------------------------------------------------------------------------
# Effect size: rank-biserial correlation r = 1 - 2W / (n*(n+1)/2)
# ---------------------------------------------------------------------------

def rank_biserial(W, n):
    max_W = n * (n + 1) / 2
    return round(1 - 2 * W / max_W, 4) if max_W > 0 else 0.0


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    debate_data = load_json(os.path.join(base_dir, "self_debate_results.json"))
    ensemble_data = load_json(os.path.join(base_dir, "clean_ensemble_results.json"))

    debate_baseline = extract_means(debate_data)
    ensemble_means = extract_ensemble_means(ensemble_data)

    case_ids = sorted(debate_baseline.keys())
    debate_scores = [debate_baseline[c][0] for c in case_ids]
    baseline_scores = [debate_baseline[c][1] for c in case_ids]
    ensemble_scores = [ensemble_means[c] for c in case_ids]
    debate_vs_baseline_deltas = [d - b for d, b in zip(debate_scores, baseline_scores)]
    debate_vs_ensemble_deltas = [d - e for d, e in zip(debate_scores, ensemble_scores)]

    results = {}

    # --- Bootstrap CIs -------------------------------------------------
    print("Computing bootstrap CIs (10,000 resamples)...")

    debate_mean_pt, debate_mean_lo, debate_mean_hi = bootstrap_ci(debate_scores, mean)
    baseline_mean_pt, baseline_mean_lo, baseline_mean_hi = bootstrap_ci(baseline_scores, mean)
    ensemble_mean_pt, ensemble_mean_lo, ensemble_mean_hi = bootstrap_ci(ensemble_scores, mean)
    lift_db_pt, lift_db_lo, lift_db_hi = bootstrap_ci(debate_vs_baseline_deltas, mean)
    lift_de_pt, lift_de_lo, lift_de_hi = bootstrap_ci(debate_vs_ensemble_deltas, mean)

    results["bootstrap_cis"] = {
        "n_resamples": 10_000,
        "ci_level": 0.95,
        "debate_mean":     {"point": round(debate_mean_pt, 4),   "ci_lo": round(debate_mean_lo, 4),   "ci_hi": round(debate_mean_hi, 4)},
        "baseline_mean":   {"point": round(baseline_mean_pt, 4), "ci_lo": round(baseline_mean_lo, 4), "ci_hi": round(baseline_mean_hi, 4)},
        "ensemble_mean":   {"point": round(ensemble_mean_pt, 4), "ci_lo": round(ensemble_mean_lo, 4), "ci_hi": round(ensemble_mean_hi, 4)},
        "lift_debate_vs_baseline": {"point": round(lift_db_pt, 4), "ci_lo": round(lift_db_lo, 4), "ci_hi": round(lift_db_hi, 4)},
        "lift_debate_vs_ensemble": {"point": round(lift_de_pt, 4), "ci_lo": round(lift_de_lo, 4), "ci_hi": round(lift_de_hi, 4)},
    }

    # --- Wilcoxon tests ------------------------------------------------
    print("Running paired Wilcoxon signed-rank tests...")

    W_db, p_db, n_db = wilcoxon_signed_rank(debate_scores, baseline_scores)
    r_db = rank_biserial(W_db, n_db)
    W_de, p_de, n_de = wilcoxon_signed_rank(debate_scores, ensemble_scores)
    r_de = rank_biserial(W_de, n_de)

    results["wilcoxon_tests"] = {
        "note": "Two-sided paired Wilcoxon signed-rank test. Normal approximation with continuity correction. Effect size = rank-biserial correlation.",
        "debate_vs_baseline": {
            "W": W_db, "p_value": p_db, "n_nonzero_pairs": n_db,
            "rank_biserial_r": r_db,
            "interpretation": "p < 0.05 → debate lift over baseline is statistically significant" if p_db < 0.05 else "p >= 0.05 → not significant at alpha=0.05"
        },
        "debate_vs_ensemble": {
            "W": W_de, "p_value": p_de, "n_nonzero_pairs": n_de,
            "rank_biserial_r": r_de,
            "interpretation": "p < 0.05 → debate lift over ensemble is statistically significant" if p_de < 0.05 else "p >= 0.05 → not significant at alpha=0.05"
        },
    }

    # --- Per-case delta summary ----------------------------------------
    results["per_case_deltas"] = {
        c: {
            "debate": round(d, 4),
            "baseline": round(b, 4),
            "ensemble": round(e, 4),
            "delta_debate_vs_baseline": round(d - b, 4),
            "delta_debate_vs_ensemble": round(d - e, 4),
        }
        for c, d, b, e in zip(case_ids, debate_scores, baseline_scores, ensemble_scores)
    }

    # --- Summary printout ---------------------------------------------
    print("\n=== Bootstrap CIs (95%) ===")
    bc = results["bootstrap_cis"]
    print(f"  Debate mean:   {bc['debate_mean']['point']:.4f}  [{bc['debate_mean']['ci_lo']:.4f}, {bc['debate_mean']['ci_hi']:.4f}]")
    print(f"  Baseline mean: {bc['baseline_mean']['point']:.4f}  [{bc['baseline_mean']['ci_lo']:.4f}, {bc['baseline_mean']['ci_hi']:.4f}]")
    print(f"  Ensemble mean: {bc['ensemble_mean']['point']:.4f}  [{bc['ensemble_mean']['ci_lo']:.4f}, {bc['ensemble_mean']['ci_hi']:.4f}]")
    print(f"  Lift D vs B:   {bc['lift_debate_vs_baseline']['point']:.4f}  [{bc['lift_debate_vs_baseline']['ci_lo']:.4f}, {bc['lift_debate_vs_baseline']['ci_hi']:.4f}]")
    print(f"  Lift D vs E:   {bc['lift_debate_vs_ensemble']['point']:.4f}  [{bc['lift_debate_vs_ensemble']['ci_lo']:.4f}, {bc['lift_debate_vs_ensemble']['ci_hi']:.4f}]")

    print("\n=== Wilcoxon Signed-Rank Tests ===")
    wt = results["wilcoxon_tests"]
    d = wt["debate_vs_baseline"]
    print(f"  Debate vs Baseline: W={d['W']:.1f}, p={d['p_value']:.6f}, r={d['rank_biserial_r']:.4f}  → {d['interpretation']}")
    d = wt["debate_vs_ensemble"]
    print(f"  Debate vs Ensemble: W={d['W']:.1f}, p={d['p_value']:.6f}, r={d['rank_biserial_r']:.4f}  → {d['interpretation']}")

    # Save
    out_path = os.path.join(base_dir, "stats_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
