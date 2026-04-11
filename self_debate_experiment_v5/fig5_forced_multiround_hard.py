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

with open("stats_results.json") as f:
    stats = json.load(f)

# Per-condition per-dimension means for hard cases
cases = data["cases"]
hard_cases = [c for c in cases if c["difficulty"] == "hard"]

dims = ["IDR", "IDP", "DRQ", "FVC"]

def get_dim_means(cond, case_list):
    from collections import defaultdict
    dim_vals = defaultdict(list)
    for c in case_list:
        cond_data = c.get(cond, {})
        for run in cond_data.get("runs", []):
            for dim in dims:
                v = run["scores"].get(dim)
                if v is not None:
                    dim_vals[dim].append(v)
    return {dim: (sum(vals)/len(vals) if vals else None) for dim, vals in dim_vals.items()}

fm_means = get_dim_means("forced_multiround", hard_cases)
mr_means = get_dim_means("multiround", hard_cases)

# Use rescored IDR/IDP for FM and MR (hard critique cases only)
# From earlier analysis: FM rescored IDR=1.0, IDP=0.9259; MR-hard rescored IDR=1.0, IDP=0.9537
fm_means["IDR"] = 1.0000
fm_means["IDP"] = 0.9259
mr_means["IDR"] = 1.0000
mr_means["IDP"] = 0.9537

fig, ax = plt.subplots(figsize=(9, 5))

x = np.arange(len(dims))
width = 0.35

fm_vals = [fm_means[d] if fm_means[d] is not None else 0 for d in dims]
mr_vals = [mr_means[d] if mr_means[d] is not None else 0 for d in dims]

bars_fm = ax.bar(x - width/2, fm_vals, width, label="Forced Multiround (hard, n=42)", color="#8e44ad", alpha=0.85)
bars_mr = ax.bar(x + width/2, mr_vals, width, label="Multiround (hard, n=42)", color="#27ae60", alpha=0.85)

ax.set_xticks(x)
ax.set_xticklabels(dims, fontsize=11)
ax.set_ylabel("Mean Score", fontsize=10)
ax.set_title("Forced Multiround vs Multiround on Hard Cases\n(IDR/IDP from rescored values; H2: FM should exceed MR — FAILS)", fontsize=10)
ax.set_ylim(0.85, 1.05)
ax.legend(fontsize=9)
ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)

for bars, vals in [(bars_fm, fm_vals), (bars_mr, mr_vals)]:
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                f"{v:.4f}", ha="center", va="bottom", fontsize=8)

# Annotate Wilcoxon result
wilcox = stats["wilcoxon_forced_multiround"]["forced_multiround_vs_multiround_hard"]
ax.text(0.98, 0.05,
        f"Wilcoxon W={wilcox['W']}, p={wilcox['p']:.3f}\n(not significant)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

# Note about IDR
ax.text(0.02, 0.97,
        "IDR/IDP: rescored from raw text (leakage-corrected)\n3 FM critique cases with null verdicts excluded from IDR/IDP",
        transform=ax.transAxes, ha="left", va="top", fontsize=7, style="italic",
        color="grey")

plt.tight_layout()
plt.savefig("forced_multiround_hard.png", dpi=150)
print("Saved forced_multiround_hard.png")
