# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open("v5_results.json") as f:
    data = json.load(f)

conditions = ["baseline", "isolated_debate", "multiround", "ensemble", "forced_multiround"]
labels = ["Baseline", "Isolated\nDebate", "Multiround", "Ensemble", "Forced\nMultiround\n(hard only)"]
means = [
    data["benchmark_baseline_mean"],
    data["benchmark_isolated_debate_mean"],
    data["benchmark_multiround_mean"],
    data["benchmark_ensemble_mean"],
    data["forced_multiround_hard_mean"],
]

# Bootstrap CIs from stats_results.json
with open("stats_results.json") as f:
    stats = json.load(f)

cis = stats["bootstrap_cis"]
ci_lo = [
    cis["baseline_mean"]["ci"][0],
    cis["isolated_debate_mean"]["ci"][0],
    cis["multiround_mean"]["ci"][0],
    cis["ensemble_mean"]["ci"][0],
    None,  # no bootstrap CI for forced_multiround
]
ci_hi = [
    cis["baseline_mean"]["ci"][1],
    cis["isolated_debate_mean"]["ci"][1],
    cis["multiround_mean"]["ci"][1],
    cis["ensemble_mean"]["ci"][1],
    None,
]

colors = ["#7f8c8d", "#2980b9", "#27ae60", "#e67e22", "#8e44ad"]

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(conditions))
bars = ax.bar(x, means, color=colors, width=0.55, edgecolor="white", linewidth=0.5)

# Error bars for conditions with CIs
for i, (lo, hi, m) in enumerate(zip(ci_lo, ci_hi, means)):
    if lo is not None:
        ax.errorbar(i, m, yerr=[[m - lo], [hi - m]], fmt="none", color="black", capsize=4, linewidth=1.2)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Mean Score (primary dims)", fontsize=10)
ax.set_title("v5 Experiment: Per-Condition Overall Mean Score\n(IDR/IDP/DRQ/FVC; error bars = 95% bootstrap CI where available)", fontsize=10)
ax.set_ylim(0.88, 1.0)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.3f}"))
ax.axhline(0.65, color="red", linestyle="--", linewidth=0.8, label="Pass threshold (0.65)")
ax.legend(fontsize=8)

# Annotate bars
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
            f"{mean:.4f}", ha="center", va="bottom", fontsize=8)

ax.text(len(conditions) - 1, means[-1] - 0.007,
        "Hard cases only\n(n=42)", ha="center", fontsize=7, color="#8e44ad")

plt.tight_layout()
plt.savefig("per_condition_comparison.png", dpi=150)
print("Saved per_condition_comparison.png")
