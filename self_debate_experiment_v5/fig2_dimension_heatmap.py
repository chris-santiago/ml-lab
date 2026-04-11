# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

with open("stats_results.json") as f:
    stats = json.load(f)

dim_agg = stats["dimension_aggregates"]

# Fair dims panel: IDR, IDP, DRQ, FVC
# Debate-only dims panel: DC (ETD is N/A for all)
fair_dims = ["IDR", "IDP", "DRQ", "FVC"]
debate_dims = ["DC"]
conditions = ["isolated_debate", "multiround", "forced_multiround", "ensemble", "baseline"]
cond_labels = ["Isolated\nDebate", "Multiround", "Forced\nMultiround\n(hard only)", "Ensemble", "Baseline"]

# Build fair dims matrix
fair_matrix = []
for cond in conditions:
    row = []
    for dim in fair_dims:
        if cond == "forced_multiround":
            # Not in dimension_aggregates directly; use computed values
            # From analysis: IDR=0.750, IDP=0.944, DRQ=0.929, FVC=0.929 (v5_results.json per-run)
            fm_vals = {"IDR": 0.750, "IDP": 0.9444, "DRQ": 0.9286, "FVC": 0.9286}
            row.append(fm_vals[dim])
        else:
            v = dim_agg.get(cond, {}).get(dim)
            row.append(v if v is not None else np.nan)
    fair_matrix.append(row)

# Build debate dims matrix
debate_matrix = []
for cond in conditions:
    row = []
    for dim in debate_dims:
        if cond == "forced_multiround":
            debate_vals = {"DC": 0.750}
            row.append(debate_vals[dim])
        else:
            v = dim_agg.get(cond, {}).get(dim)
            row.append(v if v is not None else np.nan)
    debate_matrix.append(row)

fair_arr = np.array(fair_matrix, dtype=float)
debate_arr = np.array(debate_matrix, dtype=float)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5),
                                gridspec_kw={"width_ratios": [4, 1]})

cmap = plt.cm.YlGn.copy()
cmap.set_bad("lightgrey")

# Fair dims
im1 = ax1.imshow(fair_arr, cmap=cmap, vmin=0.5, vmax=1.0, aspect="auto")
ax1.set_xticks(range(len(fair_dims)))
ax1.set_xticklabels(fair_dims, fontsize=10)
ax1.set_yticks(range(len(conditions)))
ax1.set_yticklabels(cond_labels, fontsize=9)
ax1.set_title("Fair-Comparison Dimensions\n(IDR/IDP/DRQ/FVC)", fontsize=10)
for i in range(len(conditions)):
    for j in range(len(fair_dims)):
        v = fair_arr[i, j]
        txt = f"{v:.3f}" if not np.isnan(v) else "N/A"
        ax1.text(j, i, txt, ha="center", va="center", fontsize=9,
                 color="black" if not np.isnan(v) else "grey")

plt.colorbar(im1, ax=ax1, fraction=0.035, label="Score")

# Debate-only dims
im2 = ax2.imshow(debate_arr, cmap=cmap, vmin=0.5, vmax=1.0, aspect="auto")
ax2.set_xticks(range(len(debate_dims)))
ax2.set_xticklabels(debate_dims, fontsize=10)
ax2.set_yticks(range(len(conditions)))
ax2.set_yticklabels([], fontsize=9)
ax2.set_title("Debate-Only\n(DC; ETD=N/A)", fontsize=10)
for i in range(len(conditions)):
    for j in range(len(debate_dims)):
        v = debate_arr[i, j]
        txt = f"{v:.3f}" if not np.isnan(v) else "N/A"
        ax2.text(j, i, txt, ha="center", va="center", fontsize=9,
                 color="black" if not np.isnan(v) else "grey")

plt.colorbar(im2, ax=ax2, fraction=0.12, label="Score")

grey_patch = mpatches.Patch(color="lightgrey", label="N/A (structural exclusion)")
fig.legend(handles=[grey_patch], loc="lower center", fontsize=8, ncol=1)

fig.suptitle("v5 Dimension Heatmap: Condition x Dimension\n(Grey = N/A; IDR/IDP are rescored values)", fontsize=11)
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.savefig("dimension_heatmap.png", dpi=150)
print("Saved dimension_heatmap.png")
