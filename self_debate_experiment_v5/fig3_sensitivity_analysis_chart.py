# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open("sensitivity_analysis_results.json") as f:
    sa = json.load(f)

with open("stats_results.json") as f:
    stats = json.load(f)

# Two bars: fair-comparison lift (primary) and raw lift
fc_lift = sa["fair_comparison"]["lift_isolated_vs_baseline"]  # Method B = 0.0112
raw_lift = sa["raw_lift"]["lift_isolated_vs_baseline"]  # 0.0097

# Bootstrap CI from stats (for fair comparison lift)
ci_data = stats["bootstrap_cis"]["fair_comparison_lift_isolated_vs_baseline"]
fc_point = ci_data["point"]  # 0.00966 (bootstrap estimate)
fc_ci_lo = ci_data["ci"][0]
fc_ci_hi = ci_data["ci"][1]

# Also include Method A vs Method B
method_a = sa["pre5_lift_comparison"]["method_a_per_case_mean_lift"]
method_b = sa["pre5_lift_comparison"]["method_b_per_dimension_lift"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

# Left panel: FC lift with bootstrap CI vs raw lift
lifts = [fc_point, raw_lift]
labels = ["Fair-Comparison Lift\n(primary, bootstrap)", "Raw Lift\n(all dims)"]
colors = ["#2980b9", "#7f8c8d"]
bars = ax1.bar(range(2), lifts, color=colors, width=0.45, edgecolor="white")

# Error bar for FC lift only
yerr_lo = fc_point - fc_ci_lo
yerr_hi = fc_ci_hi - fc_point
ax1.errorbar(0, fc_point, yerr=[[yerr_lo], [yerr_hi]], fmt="none",
             color="black", capsize=6, linewidth=1.5)

ax1.axhline(0.10, color="red", linestyle="--", linewidth=1.0, label="H1 threshold (+0.10)")
ax1.axhline(0.0, color="black", linestyle="-", linewidth=0.5)
ax1.set_xticks(range(2))
ax1.set_xticklabels(labels, fontsize=9)
ax1.set_ylabel("Lift (isolated_debate - baseline)", fontsize=9)
ax1.set_title("Fair-Comparison vs Raw Lift\n(Bootstrap CI shown for primary metric)", fontsize=9)
ax1.set_ylim(-0.02, 0.12)
ax1.legend(fontsize=8)

for bar, v in zip(bars, lifts):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
             f"+{v:.4f}", ha="center", va="bottom", fontsize=9)

ax1.text(0, fc_ci_lo - 0.004, f"CI: [{fc_ci_lo:.4f}, {fc_ci_hi:.4f}]",
         ha="center", fontsize=7, color="#2980b9")

# Right panel: Method A vs Method B comparison
method_vals = [method_a, method_b]
method_labels = ["Method A\n(per-case mean\nthen subtract)", "Method B\n(per-dim subtract\nthen average)"]
colors2 = ["#27ae60", "#e67e22"]
bars2 = ax2.bar(range(2), method_vals, color=colors2, width=0.45, edgecolor="white")
ax2.axhline(0.10, color="red", linestyle="--", linewidth=1.0, label="H1 threshold (+0.10)")
ax2.axhline(0.0, color="black", linestyle="-", linewidth=0.5)
ax2.set_xticks(range(2))
ax2.set_xticklabels(method_labels, fontsize=9)
ax2.set_ylabel("Fair-Comparison Lift", fontsize=9)
ax2.set_title("PRE-5 Method Comparison\n(Divergence = 0.0015; not flagged)", fontsize=9)
ax2.set_ylim(-0.02, 0.12)
ax2.legend(fontsize=8)

for bar, v in zip(bars2, method_vals):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
             f"+{v:.4f}", ha="center", va="bottom", fontsize=9)

fig.suptitle("v5 Sensitivity Analysis: Fair-Comparison Lift\n(H1 threshold = +0.10; observed = ~+0.010)", fontsize=11)
plt.tight_layout()
plt.savefig("sensitivity_analysis_chart.png", dpi=150)
print("Saved sensitivity_analysis_chart.png")
