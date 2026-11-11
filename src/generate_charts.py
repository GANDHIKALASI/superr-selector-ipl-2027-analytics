"""
SupeRR Selector Season 2 - Publication-Grade Chart Generator
Generates dark-royal themed charts (NO neon, NO bright blue) strictly from recalculated outputs.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG_DARK = "#090D1C"
CARD_BG = "#10152D"
PINK = "#E84D87"
GOLD = "#D6B46A"
GREEN = "#24C58A"
WHITE = "#F4F5FA"
MUTED = "#A1A8BC"
GRID = "#1C2442"


def apply_royal_style(ax, fig):
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=MUTED, labelsize=9.5)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color(GRID)
    ax.grid(axis="x", color=GRID, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)


def generate_all_charts(outputs_dir="outputs"):
    os.makedirs(outputs_dir, exist_ok=True)
    bat = pd.read_csv(os.path.join(outputs_dir, "top_10_batters.csv")).sort_values("rank", ascending=False)
    bowl = pd.read_csv(os.path.join(outputs_dir, "top_10_bowlers.csv")).sort_values("rank", ascending=False)
    overall = pd.read_csv(os.path.join(outputs_dir, "top_10_overall.csv")).sort_values("rank", ascending=False)

    # 1. Batting Comparison: Normal SR vs Pressure SR
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    apply_royal_style(ax, fig)
    y = np.arange(len(bat))
    h = 0.36
    ax.barh(y - h/2, bat["norm_sr"], height=h, color="#334168", label="Normal Baseline SR (P < 50)")
    ax.barh(y + h/2, bat["pres_sr"], height=h, color=PINK, label="Pressure SR (P ≥ 50)")
    for i, (_, r) in enumerate(bat.iterrows()):
        ax.text(r["pres_sr"] + 3, i + h/2, f"{r['pres_sr']:.1f} ({r['delta_sr']:+.1f})", va="center", color=WHITE, fontsize=8.5, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"#{int(r['rank'])} {r['player_name']}" for _, r in bat.iterrows()], color=WHITE, fontweight="bold")
    ax.set_xlabel("Strike Rate (Runs per 100 Balls)", color=MUTED, fontsize=10)
    ax.set_title("Top 10 Batters: Normal Baseline vs Pressure Strike Rate", color=WHITE, fontsize=12.5, fontweight="bold", pad=12)
    ax.set_xlim(0, max(bat["pres_sr"]) * 1.24)
    ax.legend(facecolor=BG_DARK, edgecolor=GRID, labelcolor=WHITE, loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(outputs_dir, "batting_scatter.png"), facecolor=BG_DARK)
    plt.close(fig)

    # 2. Bowling Comparison: Normal Econ vs Pressure Econ
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    apply_royal_style(ax, fig)
    y = np.arange(len(bowl))
    ax.barh(y - h/2, bowl["norm_economy"], height=h, color="#334168", label="Normal Baseline Econ (P < 55)")
    ax.barh(y + h/2, bowl["pres_economy"], height=h, color=GREEN, label="Pressure Econ (P ≥ 55)")
    for i, (_, r) in enumerate(bowl.iterrows()):
        ax.text(max(r["pres_economy"], r["norm_economy"]) + 0.15, i, f"Pres {r['pres_economy']:.2f} ({r['delta_economy']:+.2f})", va="center", color=WHITE, fontsize=8.5, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"#{int(r['rank'])} {r['player_name']}" for _, r in bowl.iterrows()], color=WHITE, fontweight="bold")
    ax.set_xlabel("Economy Rate (Runs per Over — Lower is Better)", color=MUTED, fontsize=10)
    ax.set_title("Top 10 Bowlers: Normal Baseline vs Pressure Economy", color=WHITE, fontsize=12.5, fontweight="bold", pad=12)
    ax.set_xlim(0, max(bowl["norm_economy"].max(), bowl["pres_economy"].max()) * 1.28)
    ax.legend(facecolor=BG_DARK, edgecolor=GRID, labelcolor=WHITE, loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(outputs_dir, "bowling_scatter.png"), facecolor=BG_DARK)
    plt.close(fig)

    # 3. Final Top 10 Overall (Precision-Weighted Cross-Role)
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    apply_royal_style(ax, fig)
    y = np.arange(len(overall))
    colors_bar = []
    for r_cat in overall["primary_role"]:
        if "Genuine All-Rounder" in r_cat or "All-Rounder" in r_cat:
            colors_bar.append(GOLD)
        elif "Batter" in r_cat:
            colors_bar.append(PINK)
        else:
            colors_bar.append(GREEN)
    ax.barh(y, overall["overall_reliability_score"], height=0.58, color=colors_bar)
    for i, (_, r) in enumerate(overall.iterrows()):
        ax.text(r["overall_reliability_score"] + 0.8, i, f"{r['overall_reliability_score']:.1f}  (Z_adj +{r['cross_role_z_score']:.2f}, w={r['precision_weight']:.2f})", va="center", color=WHITE, fontsize=8.5, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"#{int(r['rank'])} {r['player_name']}" for _, r in overall.iterrows()], color=WHITE, fontweight="bold")
    ax.set_xlabel("Uncertainty-Adjusted Overall Reliability Index [0–100]", color=MUTED, fontsize=10)
    ax.set_title("Final Top 10 Overall Auction Targets (Precision-Weighted Cross-Role)", color=WHITE, fontsize=12.5, fontweight="bold", pad=12)
    ax.set_xlim(0, 108)
    # Custom Legend
    from matplotlib.patches import Patch
    legend_els = [
        Patch(facecolor=GREEN, label="Specialist Bowler"),
        Patch(facecolor=GOLD, label="All-Rounder (Dual/Primary)"),
        Patch(facecolor=PINK, label="Specialist Batter")
    ]
    ax.legend(handles=legend_els, facecolor=BG_DARK, edgecolor=GRID, labelcolor=WHITE, loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(outputs_dir, "reliability_bars.png"), facecolor=BG_DARK)
    plt.close(fig)

    # 4. Bootstrap 95% CI Forest Plot (Batters + Bowlers side-by-side)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=180)
    for ax in (ax1, ax2):
        apply_royal_style(ax, fig)

    yb = np.arange(len(bat))
    ax1.errorbar(
        bat["pres_sr"], yb,
        xerr=[bat["pres_sr"] - bat["ci_lower"], bat["ci_upper"] - bat["pres_sr"]],
        fmt="o", color=PINK, ecolor=GOLD, elinewidth=2, capsize=4, markersize=6
    )
    ax1.set_yticks(yb)
    ax1.set_yticklabels([f"{r['player_name']} ({int(r['pres_balls_faced'])}b)" for _, r in bat.iterrows()], color=WHITE, fontsize=8.5)
    ax1.set_title("Top 10 Batters: 95% Bootstrap CI (Pres SR)", color=WHITE, fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Pressure Strike Rate", color=MUTED, fontsize=9)

    ybw = np.arange(len(bowl))
    ax2.errorbar(
        bowl["pres_economy"], ybw,
        xerr=[bowl["pres_economy"] - bowl["ci_lower"], bowl["ci_upper"] - bowl["pres_economy"]],
        fmt="o", color=GREEN, ecolor=GOLD, elinewidth=2, capsize=4, markersize=6
    )
    ax2.set_yticks(ybw)
    ax2.set_yticklabels([f"{r['player_name']} ({int(r['pres_legal_balls'])}b)" for _, r in bowl.iterrows()], color=WHITE, fontsize=8.5)
    ax2.set_title("Top 10 Bowlers: 95% Bootstrap CI (Pres Econ)", color=WHITE, fontsize=10.5, fontweight="bold")
    ax2.set_xlabel("Pressure Economy (Lower = Better)", color=MUTED, fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(outputs_dir, "bootstrap_ci_forest.png"), facecolor=BG_DARK)
    plt.close(fig)
    print("Regenerated all 4 analytical PNG charts in outputs/.")


if __name__ == "__main__":
    generate_all_charts()

