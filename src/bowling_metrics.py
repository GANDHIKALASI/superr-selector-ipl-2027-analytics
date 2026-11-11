"""
SupeRR Selector Season 2 - Rajasthan Royals IPL 2027 Auction Analytics
Module: bowling_metrics.py
Author: Senior Cricket Data Scientist & Quantitative Sports Analyst
Purpose: Advanced bowling analytics computing legal bowling figures, runs conceded,
         pressure-specific metrics, death overs, and differential performance.
"""

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BowlingMetrics")

VALID_BOWLER_WICKETS = {"Bowled", "Caught", "LBW", "Stump", "Hit Wicket"}

def compute_bowling_metrics(df, min_legal_balls=120, pressure_threshold=55.0):
    """
    Computes comprehensive bowling metrics across all eligible bowlers.
    Splits performance into Normal context (pressure_bowl < threshold) and
    Pressure context (pressure_bowl >= threshold), with death-overs isolation
    and differential comparison against individual baseline.
    """
    logger.info("Computing advanced bowling analytics...")

    # Tag bowler pressure split
    df["is_pressure_bowl"] = (df["pressure_score_bowl"] >= pressure_threshold).astype(int)

    records = []
    for (player_id, player_name), grp in df.groupby(["bowler_id", "bowler_name"]):
        # Total legal balls bowled
        legal_balls_all = grp["is_legal"].sum()
        if legal_balls_all < min_legal_balls:
            continue

        grp_legal = grp[grp["is_legal"] == 1]
        grp_norm = grp[grp["is_pressure_bowl"] == 0]
        grp_pres = grp[grp["is_pressure_bowl"] == 1]

        # 1. CORE OVERALL METRICS
        # Runs conceded: runs off bat + wides + no-balls + extra2_runs (no byes/legbyes!)
        total_runs_conceded = grp["bowler_runs_conceded"].sum()
        total_wickets = grp["is_bowler_wicket"].sum()
        total_overs = legal_balls_all / 6.0
        total_dots = grp["is_dot_ball"].sum()
        total_boundaries = (grp["is_four"] | grp["is_six"]).sum()

        overall_economy = (total_runs_conceded / legal_balls_all) * 6.0
        overall_avg = total_runs_conceded / max(1, total_wickets) if total_wickets > 0 else total_runs_conceded
        overall_sr = legal_balls_all / max(1, total_wickets) if total_wickets > 0 else legal_balls_all
        overall_dot_pct = (total_dots / legal_balls_all) * 100.0
        overall_boundary_pct = (total_boundaries / legal_balls_all) * 100.0
        wickets_per_over = total_wickets / max(0.1, total_overs)

        # 2. NORMAL BASELINE METRICS
        norm_legal = grp_norm["is_legal"].sum()
        norm_runs = grp_norm["bowler_runs_conceded"].sum()
        norm_wkts = grp_norm["is_bowler_wicket"].sum()
        norm_dots = grp_norm["is_dot_ball"].sum()
        norm_boundaries = (grp_norm["is_four"] | grp_norm["is_six"]).sum()

        norm_economy = (norm_runs / norm_legal) * 6.0 if norm_legal > 0 else 0.0
        norm_avg = norm_runs / max(1, norm_wkts) if norm_wkts > 0 else norm_runs
        norm_sr = norm_legal / max(1, norm_wkts) if norm_wkts > 0 else norm_legal
        norm_dot_pct = (norm_dots / norm_legal) * 100.0 if norm_legal > 0 else 0.0
        norm_boundary_pct = (norm_boundaries / norm_legal) * 100.0 if norm_legal > 0 else 0.0
        norm_wkt_rate = (norm_wkts / norm_legal) * 100.0 if norm_legal > 0 else 0.0

        # 3. PRESSURE METRICS
        pres_legal = grp_pres["is_legal"].sum()
        pres_runs = grp_pres["bowler_runs_conceded"].sum()
        pres_wkts = grp_pres["is_bowler_wicket"].sum()
        pres_dots = grp_pres["is_dot_ball"].sum()
        pres_boundaries = (grp_pres["is_four"] | grp_pres["is_six"]).sum()

        pres_economy = (pres_runs / pres_legal) * 6.0 if pres_legal > 0 else 0.0
        pres_avg = pres_runs / max(1, pres_wkts) if pres_wkts > 0 else pres_runs
        pres_sr = pres_legal / max(1, pres_wkts) if pres_wkts > 0 else pres_legal
        pres_dot_pct = (pres_dots / pres_legal) * 100.0 if pres_legal > 0 else 0.0
        pres_boundary_pct = (pres_boundaries / pres_legal) * 100.0 if pres_legal > 0 else 0.0
        pres_wkt_rate = (pres_wkts / pres_legal) * 100.0 if pres_legal > 0 else 0.0

        # 4. DEATH-OVER SPECIFIC PERFORMANCE (OVERS 16-20)
        grp_death = grp[grp["innings_phase"] == "Death"]
        death_legal = grp_death["is_legal"].sum()
        death_runs = grp_death["bowler_runs_conceded"].sum()
        death_wkts = grp_death["is_bowler_wicket"].sum()
        death_economy = (death_runs / death_legal) * 6.0 if death_legal > 0 else 0.0
        death_dot_pct = (grp_death["is_dot_ball"].sum() / death_legal) * 100.0 if death_legal > 0 else 0.0

        # 5. CONTINUOUS PRESSURE-WEIGHTED METRICS
        w_bowl = grp_legal["pressure_score_bowl"].values / 100.0
        w_sum = w_bowl.sum()
        w_economy = (np.sum(w_bowl * (grp_legal["bowler_runs_conceded"].values * 6.0)) / max(0.01, w_sum))
        w_dot_pct = (np.sum(w_bowl * grp_legal["is_dot_ball"].values) / max(0.01, w_sum)) * 100.0
        w_boundary_pct = (np.sum(w_bowl * (grp_legal["is_four"] | grp_legal["is_six"]).values) / max(0.01, w_sum)) * 100.0

        # 6. DIFFERENTIAL METRICS (PRESSURE VS NORMAL)
        delta_economy = pres_economy - norm_economy  # negative is better (lower economy under pressure)
        delta_dot_pct = pres_dot_pct - norm_dot_pct  # positive is better (more dots under pressure)
        delta_boundary_pct = pres_boundary_pct - norm_boundary_pct  # negative is better
        delta_wkt_rate = pres_wkt_rate - norm_wkt_rate  # positive is better
        economy_retention = pres_economy / max(1.0, norm_economy)

        # 7. MATCH-LEVEL CONSISTENCY UNDER PRESSURE
        # Economy in pressure situations per match
        pres_by_match = grp_pres.groupby("match_id").agg(
            p_runs=("bowler_runs_conceded", "sum"),
            p_balls=("is_legal", "sum"),
            p_wkts=("is_bowler_wicket", "sum")
        )
        pres_by_match = pres_by_match[pres_by_match["p_balls"] >= 6]
        if len(pres_by_match) >= 3:
            match_econ = (pres_by_match["p_runs"] / pres_by_match["p_balls"]) * 6.0
            cv_pres_economy = match_econ.std() / max(1.0, match_econ.mean())
            # Good spell under pressure: Econ <= 8.5 or >= 2 wickets
            good_spells = ((match_econ <= 8.5) | (pres_by_match["p_wkts"] >= 2)).sum()
            pres_success_rate = (good_spells / len(pres_by_match)) * 100.0
        else:
            cv_pres_economy = 1.2
            pres_success_rate = 35.0

        # Format split
        ipl_balls = grp_legal[grp_legal["is_ipl"] == True]["is_legal"].sum()
        t20i_balls = legal_balls_all - ipl_balls
        ipl_pres_balls = grp_pres[grp_pres["is_ipl"] == True]["is_legal"].sum()

        records.append({
            "player_id": player_id,
            "player_name": player_name,
            "total_matches": grp["match_id"].nunique(),
            "total_legal_balls": legal_balls_all,
            "total_overs": round(total_overs, 1),
            "total_runs_conceded": total_runs_conceded,
            "total_wickets": total_wickets,
            "overall_economy": round(overall_economy, 2),
            "overall_avg": round(overall_avg, 2),
            "overall_sr": round(overall_sr, 2),
            "overall_dot_pct": round(overall_dot_pct, 2),
            "overall_boundary_pct": round(overall_boundary_pct, 2),
            "wickets_per_over": round(wickets_per_over, 3),
            # Normal baseline
            "norm_legal_balls": norm_legal,
            "norm_runs_conceded": norm_runs,
            "norm_wickets": norm_wkts,
            "norm_economy": round(norm_economy, 2),
            "norm_avg": round(norm_avg, 2),
            "norm_dot_pct": round(norm_dot_pct, 2),
            "norm_boundary_pct": round(norm_boundary_pct, 2),
            # Pressure metrics
            "pres_legal_balls": pres_legal,
            "pres_runs_conceded": pres_runs,
            "pres_wickets": pres_wkts,
            "pres_economy": round(pres_economy, 2),
            "pres_avg": round(pres_avg, 2),
            "pres_sr": round(pres_sr, 2),
            "pres_dot_pct": round(pres_dot_pct, 2),
            "pres_boundary_pct": round(pres_boundary_pct, 2),
            "pres_wkt_rate": round(pres_wkt_rate, 2),
            # Death overs
            "death_legal_balls": death_legal,
            "death_economy": round(death_economy, 2),
            "death_wickets": death_wkts,
            "death_dot_pct": round(death_dot_pct, 2),
            # Continuous weighted
            "weighted_economy": round(w_economy, 2),
            "weighted_dot_pct": round(w_dot_pct, 2),
            "weighted_boundary_pct": round(w_boundary_pct, 2),
            # Differential
            "delta_economy": round(delta_economy, 2),
            "delta_dot_pct": round(delta_dot_pct, 2),
            "delta_boundary_pct": round(delta_boundary_pct, 2),
            "delta_wkt_rate": round(delta_wkt_rate, 2),
            "economy_retention": round(economy_retention, 3),
            # Consistency
            "cv_pres_economy": round(cv_pres_economy, 2),
            "pres_success_rate": round(pres_success_rate, 2),
            # Format split
            "ipl_legal_balls": ipl_balls,
            "t20i_legal_balls": t20i_balls,
            "ipl_pres_legal_balls": ipl_pres_balls,
            "ipl_ratio": round(ipl_balls / max(1, legal_balls_all), 3)
        })

    df_res = pd.DataFrame(records)
    logger.info(f"Bowling analytics computed for {len(df_res)} qualifying bowlers.")
    return df_res

if __name__ == "__main__":
    from preprocessing import load_and_preprocess_data
    from pressure_model import compute_pressure_indices
    df, _, _, _, _ = load_and_preprocess_data()
    df = compute_pressure_indices(df)
    bowl_metrics = compute_bowling_metrics(df, min_legal_balls=150)
    print("Top 10 Bowlers by Pressure Wickets:\n", bowl_metrics.sort_values("pres_wickets", ascending=False)[["player_name", "total_wickets", "pres_wickets", "pres_legal_balls", "norm_economy", "pres_economy", "delta_economy"]].head(10))

