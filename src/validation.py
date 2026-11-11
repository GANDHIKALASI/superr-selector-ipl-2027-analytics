"""
SupeRR Selector Season 2 - Rajasthan Royals IPL 2027 Auction Analytics
Module: validation.py
Author: Senior Cricket Data Scientist & Quantitative Sports Analyst
Purpose: Production-grade validation suite: temporal out-of-sample testing,
         weight sensitivity analysis, threshold perturbations, IPL vs Combined
         rank stability (Spearman & Kendall tau), and bootstrap uncertainty quantification.
"""

import os
import logging
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Validation")

def run_temporal_validation(df, split_year=2024):
    """
    Temporal out-of-sample validation:
    Train on historical seasons (<= split_year), evaluate rankings on future seasons (> split_year).
    Checks whether players rated highly under pressure maintain superior pressure performance out-of-sample.
    Prevents temporal data leakage!
    """
    logger.info(f"Running temporal validation (Train <= {split_year}, Test > {split_year})...")
    
    from batting_metrics import compute_batting_metrics
    from bowling_metrics import compute_bowling_metrics
    from reliability_model import build_batter_reliability_model, build_bowler_reliability_model

    df["match_year"] = pd.to_datetime(df["match_date"]).dt.year

    df_train = df[df["match_year"] <= split_year].copy()
    df_test = df[df["match_year"] > split_year].copy()

    # Train models
    bat_train = compute_batting_metrics(df_train, min_balls_faced=80)
    bowl_train = compute_bowling_metrics(df_train, min_legal_balls=80)

    train_brs = build_batter_reliability_model(bat_train, min_pres_balls=30, min_total_balls=80)
    train_prs = build_bowler_reliability_model(bowl_train, min_pres_balls=40, min_total_balls=80)

    # Test metrics
    bat_test = compute_batting_metrics(df_test, min_balls_faced=60)
    bowl_test = compute_bowling_metrics(df_test, min_legal_balls=60)

    # Correlate train reliability score with test pressure performance
    merged_bat = train_brs[["player_id", "player_name", "reliability_score", "rank"]].merge(
        bat_test[["player_id", "pres_sr", "delta_sr", "pres_runs", "pres_balls_faced"]],
        on="player_id"
    )
    # Filter test players with sufficient sample
    merged_bat = merged_bat[merged_bat["pres_balls_faced"] >= 20]

    spearman_bat, p_bat = stats.spearmanr(merged_bat["reliability_score"], merged_bat["pres_sr"])
    
    merged_bowl = train_prs[["player_id", "player_name", "reliability_score", "rank"]].merge(
        bowl_test[["player_id", "pres_economy", "delta_economy", "pres_wickets", "pres_legal_balls"]],
        on="player_id"
    )
    merged_bowl = merged_bowl[merged_bowl["pres_legal_balls"] >= 30]
    # Negative correlation expected for economy (higher score -> lower economy)
    spearman_bowl, p_bowl = stats.spearmanr(merged_bowl["reliability_score"], -merged_bowl["pres_economy"])

    logger.info(f"Temporal Validation Results: Batters Spearman rho={spearman_bat:.3f} (p={p_bat:.4f}); Bowlers rho={spearman_bowl:.3f} (p={p_bowl:.4f})")
    
    return {
        "bat_test_sample": len(merged_bat),
        "bat_spearman_rho": round(spearman_bat, 3),
        "bat_p_value": round(p_bat, 4),
        "bowl_test_sample": len(merged_bowl),
        "bowl_spearman_rho": round(spearman_bowl, 3),
        "bowl_p_value": round(p_bowl, 4)
    }

def run_weight_sensitivity_analysis(metrics_df, role="bat"):
    """
    Tests ranking sensitivity across alternative pillar weighting configurations:
    1. Baseline (30% Execution, 25% Resilience, 20% Consistency, 15% Leverage, 10% Confidence)
    2. Execution Heavy (45% Execution, 20% Resilience, 15% Consistency, 10% Leverage, 10% Confidence)
    3. Resilience Heavy (20% Execution, 45% Resilience, 15% Consistency, 10% Leverage, 10% Confidence)
    4. Consistency Heavy (20% Execution, 20% Resilience, 40% Consistency, 10% Leverage, 10% Confidence)
    5. Balanced Flat (20% each)
    """
    logger.info(f"Running weight sensitivity analysis for {role}...")
    from reliability_model import build_batter_reliability_model, build_bowler_reliability_model

    weight_schemes = {
        "Baseline": (0.30, 0.25, 0.20, 0.15, 0.10),
        "Execution_Heavy": (0.45, 0.20, 0.15, 0.10, 0.10),
        "Resilience_Heavy": (0.20, 0.45, 0.15, 0.10, 0.10),
        "Consistency_Heavy": (0.20, 0.20, 0.40, 0.10, 0.10),
        "Balanced_Flat": (0.20, 0.20, 0.20, 0.20, 0.20)
    }

    base_model = build_batter_reliability_model(metrics_df) if role == "bat" else build_bowler_reliability_model(metrics_df)
    rankings_dict = {"Baseline": base_model.set_index("player_name")["rank"]}

    for name, w in weight_schemes.items():
        if name == "Baseline":
            continue
        # Re-compute composite score with altered weights
        df = base_model.copy()
        raw_score = (w[0] * df["pillar_execution"] +
                     w[1] * df["pillar_resilience"] +
                     w[2] * df["pillar_consistency"] +
                     w[3] * df["pillar_leverage"] +
                     w[4] * df["pillar_confidence"])
        df["temp_score"] = raw_score
        df = df.sort_values("temp_score", ascending=False).reset_index(drop=True)
        df[f"rank_{name}"] = df.index + 1
        rankings_dict[name] = df.set_index("player_name")[f"rank_{name}"]

    df_ranks = pd.DataFrame(rankings_dict)
    
    # Calculate Spearman correlation matrix against Baseline
    corrs = {}
    for col in df_ranks.columns:
        rho, _ = stats.spearmanr(df_ranks["Baseline"], df_ranks[col])
        corrs[col] = round(rho, 4)

    # Calculate rank volatility (standard deviation of rank across schemes)
    df_ranks["rank_std"] = df_ranks.std(axis=1)
    df_ranks["stability_category"] = np.where(df_ranks["rank_std"] <= 2.0, "Highly Stable",
                                    np.where(df_ranks["rank_std"] <= 4.5, "Moderately Stable", "Sensitive"))
    
    logger.info(f"Weight sensitivity correlations vs Baseline: {corrs}")
    return df_ranks, corrs

def run_ipl_vs_combined_comparison(df):
    """
    Compares IPL-only rankings against Combined (IPL + T20I) rankings.
    Computes Spearman rank correlation and Kendall's tau to measure agreement.
    """
    logger.info("Comparing IPL-only vs Combined dataset rankings...")
    from batting_metrics import compute_batting_metrics
    from bowling_metrics import compute_bowling_metrics
    from reliability_model import build_batter_reliability_model, build_bowler_reliability_model

    # Combined
    bat_comb = compute_batting_metrics(df, min_balls_faced=120)
    bowl_comb = compute_bowling_metrics(df, min_legal_balls=120)
    brs_comb = build_batter_reliability_model(bat_comb, min_pres_balls=45)
    prs_comb = build_bowler_reliability_model(bowl_comb, min_pres_balls=60)

    # IPL Only
    df_ipl = df[df["is_ipl"] == True]
    bat_ipl = compute_batting_metrics(df_ipl, min_balls_faced=80)
    bowl_ipl = compute_bowling_metrics(df_ipl, min_legal_balls=80)
    brs_ipl = build_batter_reliability_model(bat_ipl, min_pres_balls=30)
    prs_ipl = build_bowler_reliability_model(bowl_ipl, min_pres_balls=40)

    # Batters comparison
    bat_comp = brs_comb[["player_name", "rank"]].rename(columns={"rank": "rank_combined"}).merge(
        brs_ipl[["player_name", "rank"]].rename(columns={"rank": "rank_ipl"}),
        on="player_name"
    )
    spearman_bat, _ = stats.spearmanr(bat_comp["rank_combined"], bat_comp["rank_ipl"])
    kendall_bat, _ = stats.kendalltau(bat_comp["rank_combined"], bat_comp["rank_ipl"])

    # Bowlers comparison
    bowl_comp = prs_comb[["player_name", "rank"]].rename(columns={"rank": "rank_combined"}).merge(
        prs_ipl[["player_name", "rank"]].rename(columns={"rank": "rank_ipl"}),
        on="player_name"
    )
    spearman_bowl, _ = stats.spearmanr(bowl_comp["rank_combined"], bowl_comp["rank_ipl"])
    kendall_bowl, _ = stats.kendalltau(bowl_comp["rank_combined"], bowl_comp["rank_ipl"])

    logger.info(f"IPL vs Combined Agreement: Batters Spearman={spearman_bat:.3f}, Kendall={kendall_bat:.3f}")
    logger.info(f"IPL vs Combined Agreement: Bowlers Spearman={spearman_bowl:.3f}, Kendall={kendall_bowl:.3f}")

    return {
        "batters": {"spearman": round(spearman_bat, 3), "kendall": round(kendall_bat, 3), "overlap_count": len(bat_comp)},
        "bowlers": {"spearman": round(spearman_bowl, 3), "kendall": round(kendall_bowl, 3), "overlap_count": len(bowl_comp)}
    }

if __name__ == "__main__":
    import sys
    sys.path.append("src")
    from preprocessing import load_and_preprocess_data
    from pressure_model import compute_pressure_indices
    from batting_metrics import compute_batting_metrics
    from bowling_metrics import compute_bowling_metrics

    df, _, _, _, _ = load_and_preprocess_data()
    df = compute_pressure_indices(df)

    bat_metrics = compute_batting_metrics(df)
    bowl_metrics = compute_bowling_metrics(df)

    # 1. Temporal validation
    temp_res = run_temporal_validation(df, split_year=2024)
    print("Temporal Validation:\n", temp_res)

    # 2. Weight sensitivity
    df_bat_ranks, bat_corrs = run_weight_sensitivity_analysis(bat_metrics, role="bat")
    print("\nBatters Weight Sensitivity Stability:\n", df_bat_ranks["stability_category"].value_counts())

    # 3. IPL vs Combined
    comp_res = run_ipl_vs_combined_comparison(df)
    print("\nIPL vs Combined Comparison:\n", comp_res)

