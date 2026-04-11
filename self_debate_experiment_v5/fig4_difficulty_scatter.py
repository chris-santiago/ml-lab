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

with open("difficulty_validation_results.json") as f:
    dv = json.load(f)

# Get per-case baseline means (critique only)
cases = data["cases"]
critique_cases = [c for c in cases if c["category"] == "critique"]

# Numeric encoding: medium=0, hard=1
diff_map = {"medium": 0, "hard": 1}
x_vals = []
y_vals = []
labels = []
for c in critique_cases:
    baseline_mean = c.get("baseline", {}).get("mean")
    if baseline_mean is not None:
        x_vals.append(diff_map[c["difficulty"]])
        y_vals.append(baseline_mean)
        labels.append(c["case_id"])

x_arr = np.array(x_vals)
y_arr = np.array(y_vals)

# Add jitter to x for visibility
rng = np.random.default_rng(42)
x_jitter = x_arr + rng.uniform(-0.08, 0.08, len(x_arr))

fig, ax = plt.subplots(figsize=(8, 5))

colors = ["#3498db" if x == 0 else "#e74c3c" for x in x_vals]
ax.scatter(x_jitter, y_arr, c=colors, alpha=0.6, s=40, edgecolors="none")

# Means per difficulty
medium_mean = dv["means_by_difficulty"]["medium"]
hard_mean = dv["means_by_difficulty"]["hard"]
ax.hlines(medium_mean, -0.2, 0.2, colors="#3498db", linewidth=2, label=f"Medium mean ({medium_mean:.4f})")
ax.hlines(hard_mean, 0.8, 1.2, colors="#e74c3c", linewidth=2, label=f"Hard mean ({hard_mean:.4f})")

# Trend line
z = np.polyfit(x_arr, y_arr, 1)
p = np.poly1d(z)
x_line = np.linspace(-0.15, 1.15, 100)
ax.plot(x_line, p(x_line), "--", color="grey", linewidth=1.0, alpha=0.7, label="Linear trend")

rho = dv["spearman_rho"]
pval = dv["p_value"]
ax.text(0.98, 0.05,
        f"Spearman ρ = {rho:.3f}\np = {pval:.3f}\n(n={dv['non_defense_wins_n']} critique cases)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

ax.set_xticks([0, 1])
ax.set_xticklabels(["Medium", "Hard"], fontsize=11)
ax.set_xlabel("Difficulty Label", fontsize=10)
ax.set_ylabel("Baseline Mean Score", fontsize=10)
ax.set_title("Difficulty Label vs Baseline Performance\n(Critique cases only; ρ ≈ 0 indicates labels do not predict performance)", fontsize=10)
ax.set_xlim(-0.3, 1.3)
ax.set_ylim(0.5, 1.05)

from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#3498db", markersize=8, label="Medium cases"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#e74c3c", markersize=8, label="Hard cases"),
    Line2D([0], [0], color="#3498db", linewidth=2, label=f"Medium mean ({medium_mean:.4f})"),
    Line2D([0], [0], color="#e74c3c", linewidth=2, label=f"Hard mean ({hard_mean:.4f})"),
    Line2D([0], [0], linestyle="--", color="grey", label="Linear trend"),
]
ax.legend(handles=legend_elements, fontsize=8, loc="lower left")

plt.tight_layout()
plt.savefig("difficulty_scatter.png", dpi=150)
print("Saved difficulty_scatter.png")
