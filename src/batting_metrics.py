"""
SupeRR Selector Season 2 - Rajasthan Royals IPL 2027 Auction Analytics
Module: batting_metrics.py
Author: Senior Cricket Data Scientist & Quantitative Sports Analyst
Purpose: Advanced batting analytics computing core, pressure-specific,
         and differential (pressure vs normal baseline) performance metrics.
"""

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BattingMetrics")

def compute_batting_metrics(df, min_balls_faced=120, pressure_threshold=50.0):
    """
    Computes comprehensive batting metrics across all eligible batters.
    Splits performance into Normal context (pressure < threshold) and
    Pressure context (pressure >= threshold), while also evaluating
    continuous pressure-weighted metrics and match-level consistency.
    """
    logger.info("Computing advanced batting analytics...")

    # Define pressure split
    df["is_pressure_bat"] = (df["pressure_score_bat"] >= pressure_threshold).astype(int)

    # Eligible balls faced by batter (exclude wides)
    df_bat = df[df["is_batter_ball_faced"] == 1].copy()

    records = []
    # Group by striker
    for (player_id, player_name), grp in df_bat.groupby(["striker_id", "striker_name"]):
        total_balls = len(grp)
        if total_balls < min_balls_faced:
            continue

        # Split into Normal vs Pressure
        grp_norm = grp[grp["is_pressure_bat"] == 0]
        grp_pres = grp[grp["is_pressure_bat"] == 1]

        # 1. CORE OVERALL METRICS
        total_runs = grp["runs"].sum()
        total_fours = grp["is_four"].sum()
        total_sixes = grp["is_six"].sum()
        total_boundaries = total_fours + total_sixes
        total_dots = grp["is_dot_ball"].sum()
        
        # Dismissals where striker was out
        dismissals_all = (grp["is_wicket"] & (grp["dismissed_player_id"] == player_id)).sum()
        total_innings = grp["match_id"].nunique()

        overall_sr = (total_runs / total_balls) * 100.0
        overall_avg = total_runs / max(1, dismissals_all) if dismissals_all > 0 else total_runs
        overall_boundary_pct = (total_boundaries / total_balls) * 100.0
        overall_dot_pct = (total_dots / total_balls) * 100.0
        overall_dismissal_rate = (dismissals_all / total_balls) * 100.0
        balls_per_dismissal = total_balls / max(1, dismissals_all)
        runs_per_innings = total_runs / max(1, total_innings)

        # 2. NORMAL BASELINE METRICS
        norm_balls = len(grp_norm)
        norm_runs = grp_norm["runs"].sum()
        norm_dots = grp_norm["is_dot_ball"].sum()
        norm_boundaries = (grp_norm["is_four"] | grp_norm["is_six"]).sum()
        norm_dismissals = (grp_norm["is_wicket"] & (grp_norm["dismissed_player_id"] == player_id)).sum()

        norm_sr = (norm_runs / norm_balls) * 100.0 if norm_balls > 0 else 0.0
        norm_avg = norm_runs / max(1, norm_dismissals) if norm_dismissals > 0 else norm_runs
        norm_boundary_pct = (norm_boundaries / norm_balls) * 100.0 if norm_balls > 0 else 0.0
        norm_dot_pct = (norm_dots / norm_balls) * 100.0 if norm_balls > 0 else 0.0
        norm_dismissal_rate = (norm_dismissals / norm_balls) * 100.0 if norm_balls > 0 else 0.0

        # 3. PRESSURE METRICS
        pres_balls = len(grp_pres)
        pres_runs = grp_pres["runs"].sum()
        pres_dots = grp_pres["is_dot_ball"].sum()
        pres_fours = grp_pres["is_four"].sum()
        pres_sixes = grp_pres["is_six"].sum()
        pres_boundaries = pres_fours + pres_sixes
        pres_dismissals = (grp_pres["is_wicket"] & (grp_pres["dismissed_player_id"] == player_id)).sum()
        pres_innings = grp_pres["match_id"].nunique()

        pres_sr = (pres_runs / pres_balls) * 100.0 if pres_balls > 0 else 0.0
        pres_avg = pres_runs / max(1, pres_dismissals) if pres_dismissals > 0 else pres_runs
        pres_boundary_pct = (pres_boundaries / pres_balls) * 100.0 if pres_balls > 0 else 0.0
        pres_dot_pct = (pres_dots / pres_balls) * 100.0 if pres_balls > 0 else 0.0
        pres_dismissal_rate = (pres_dismissals / pres_balls) * 100.0 if pres_balls > 0 else 0.0
        pres_contribution_per_match = pres_runs / max(1, pres_innings)

        # 4. CONTINUOUS PRESSURE-WEIGHTED METRICS
        w_bat = grp["pressure_score_bat"].values / 100.0
        w_sum = w_bat.sum()
        w_sr = (np.sum(w_bat * grp["runs"].values) / max(0.01, w_sum)) * 100.0
        w_boundary_pct = (np.sum(w_bat * (grp["is_four"] | grp["is_six"]).values) / max(0.01, w_sum)) * 100.0
        w_dot_pct = (np.sum(w_bat * grp["is_dot_ball"].values) / max(0.01, w_sum)) * 100.0

        # 5. DIFFERENTIAL METRICS (PRESSURE VS NORMAL)
        delta_sr = pres_sr - norm_sr
        delta_boundary_pct = pres_boundary_pct - norm_boundary_pct
        delta_dot_pct = pres_dot_pct - norm_dot_pct  # negative is better (fewer dots under pressure)
        delta_dismissal_rate = pres_dismissal_rate - norm_dismissal_rate
        sr_retention_ratio = pres_sr / max(1.0, norm_sr)

        # 6. MATCH-LEVEL CONSISTENCY UNDER PRESSURE
        # Runs scored in pressure situations per match
        pres_match_runs = grp_pres.groupby("match_id")["runs"].sum()
        if len(pres_match_runs) >= 3:
            # Coefficient of Variation (lower is more consistent)
            cv_pres_runs = pres_match_runs.std() / max(1.0, pres_match_runs.mean())
            # Match success rate under pressure (scored >= 15 runs or SR >= 140 with >= 8 balls)
            pres_match_balls = grp_pres.groupby("match_id").size()
            pres_match_sr = (pres_match_runs / pres_match_balls) * 100.0
            high_impact_matches = ((pres_match_runs >= 15) | ((pres_match_sr >= 140.0) & (pres_match_balls >= 8))).sum()
            pres_success_rate = (high_impact_matches / len(pres_match_runs)) * 100.0
        else:
            cv_pres_runs = 1.5
            pres_success_rate = 30.0

        # 7. IPL VS T20I SAMPLE BREAKDOWN
        ipl_balls = len(grp[grp["is_ipl"] == True])
        t20i_balls = total_balls - ipl_balls
        ipl_pres_balls = len(grp_pres[grp_pres["is_ipl"] == True])

        records.append({
            "player_id": player_id,
            "player_name": player_name,
            "total_matches": grp["match_id"].nunique(),
            "total_innings": total_innings,
            "total_balls_faced": total_balls,
            "total_runs": total_runs,
            "overall_avg": round(overall_avg, 2),
            "overall_sr": round(overall_sr, 2),
            "overall_boundary_pct": round(overall_boundary_pct, 2),
            "overall_dot_pct": round(overall_dot_pct, 2),
            "overall_dismissal_rate": round(overall_dismissal_rate, 2),
            "balls_per_dismissal": round(balls_per_dismissal, 2),
            "runs_per_innings": round(runs_per_innings, 2),
            "fours": total_fours,
            "sixes": total_sixes,
            # Normal baseline
            "norm_balls_faced": norm_balls,
            "norm_runs": norm_runs,
            "norm_sr": round(norm_sr, 2),
            "norm_avg": round(norm_avg, 2),
            "norm_boundary_pct": round(norm_boundary_pct, 2),
            "norm_dot_pct": round(norm_dot_pct, 2),
            "norm_dismissals": norm_dismissals,
            # Pressure metrics
            "pres_balls_faced": pres_balls,
            "pres_runs": pres_runs,
            "pres_sr": round(pres_sr, 2),
            "pres_avg": round(pres_avg, 2),
            "pres_boundary_pct": round(pres_boundary_pct, 2),
            "pres_dot_pct": round(pres_dot_pct, 2),
            "pres_dismissals": pres_dismissals,
            "pres_dismissal_rate": round(pres_dismissal_rate, 2),
            "pres_contribution_per_match": round(pres_contribution_per_match, 2),
            # Continuous weighted
            "weighted_sr": round(w_sr, 2),
            "weighted_boundary_pct": round(w_boundary_pct, 2),
            "weighted_dot_pct": round(w_dot_pct, 2),
            # Differential metrics
            "delta_sr": round(delta_sr, 2),
            "delta_boundary_pct": round(delta_boundary_pct, 2),
            "delta_dot_pct": round(delta_dot_pct, 2),
            "delta_dismissal_rate": round(delta_dismissal_rate, 2),
            "sr_retention_ratio": round(sr_retention_ratio, 3),
            # Consistency
            "cv_pres_runs": round(cv_pres_runs, 2),
            "pres_success_rate": round(pres_success_rate, 2),
            # Format split
            "ipl_balls_faced": ipl_balls,
            "t20i_balls_faced": t20i_balls,
            "ipl_pres_balls_faced": ipl_pres_balls,
            "ipl_ratio": round(ipl_balls / total_balls, 3)
        })

    df_res = pd.DataFrame(records)
    logger.info(f"Batting analytics computed for {len(df_res)} qualifying batters.")
    return df_res

if __name__ == "__main__":
    from preprocessing import load_and_preprocess_data
    from pressure_model import compute_pressure_indices
    df, _, _, _, _ = load_and_preprocess_data()
    df = compute_pressure_indices(df)
    bat_metrics = compute_batting_metrics(df, min_balls_faced=150)
    print("Top 10 Batters by Pressure Runs:\n", bat_metrics.sort_values("pres_runs", ascending=False)[["player_name", "total_runs", "pres_runs", "pres_balls_faced", "norm_sr", "pres_sr", "delta_sr"]].head(10))

