"""
SupeRR Selector Season 2 - Rajasthan Royals IPL 2027 Auction Analytics
Module: pressure_model.py
Author: Senior Cricket Data Scientist & Quantitative Sports Analyst
Purpose: Mathematically rigorous, context-aware continuous pressure modeling
         for batting and bowling situations in T20 cricket.
"""

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PressureModel")

def compute_pressure_indices(df, par_score_default=170.0):
    """
    Computes continuous context-aware pressure scores [0, 100] for both
    batting (pressure_bat) and bowling (pressure_bowl) on every delivery.

    Mathematical Construction:
    --------------------------
    1. Second Innings (Chasing):
       - Rate Stress Factor:
         S_rate = 1 / (1 + exp(-0.45 * (RRR - 9.5)))
       - Resource Scarcity (Wickets):
         S_wicket = ((11 - wickets_in_hand) / 10)^1.2
       - Temporal Urgency:
         S_urgency = 1 - (balls_remaining / max_balls)^0.75
       - Match Closeness / Contestability:
         z = (runs_needed - balls_remaining * (1.35 - 0.07 * (10 - wickets_in_hand))) / sqrt(balls_remaining * 1.8 + 1)
         P_win = 1 / (1 + exp(1.1 * z))
         C_match = 4 * P_win * (1 - P_win)
       - Raw Batting Pressure:
         P_bat_chase = 100 * (0.38 * S_rate + 0.32 * S_wicket + 0.20 * S_urgency + 0.10 * S_rate * S_urgency) * (0.35 + 0.65 * C_match)

    2. First Innings (Setting Target):
       - Projected Score using resource curve:
         R_res = (balls_remaining / max_balls)^0.65 * (wickets_in_hand / 10)^0.5
         S_proj = cum_runs + par_score * R_res
         Delta_par = (par_score - S_proj) / par_score
       - Raw Batting Pressure:
         P_bat_first = 100 * (0.35 * clip((Delta_par + 0.20) / 0.45, 0, 1) +
                              0.35 * (cum_wickets / 9)^1.2 +
                              0.30 * (1 - balls_remaining / max_balls)^1.5)

    3. Super Overs (Innings >= 3):
       - High-leverage sudden-death environment:
         P = min(100, 85 + 2.5 * ball_num)

    4. Bowling Context Modulation:
       - Bowler defending in high-leverage close finishes faces intense stress.
       - If batting team has lost 7+ wickets and game is out of reach, bowler pressure is minimal.
       - Bowling pressure modulates situation difficulty and defensive responsibility.
    """
    logger.info("Calculating context-aware continuous pressure indices...")

    # Safe copies of core series
    innings = df["innings"].values
    balls_rem = np.maximum(0, df["balls_remaining"].values)
    max_balls = np.maximum(1, df["max_balls"].values)
    runs_needed = np.maximum(0, df["runs_needed"].values)
    wickets_in_hand = np.clip(df["wickets_in_hand_before"].values, 0, 10)
    cum_wickets = np.clip(df["cum_wickets_before"].values, 0, 10)
    cum_runs = df["cum_team_runs_before"].values
    rrr = df["rrr"].values
    innings_ball = df["innings_ball_num"].values

    # --- 1. SECOND INNINGS CALCULATIONS ---
    # Rate stress
    s_rate = 1.0 / (1.0 + np.exp(-0.45 * (rrr - 9.5)))

    # Wicket scarcity
    s_wicket = np.power(np.maximum(0, 11 - wickets_in_hand) / 10.0, 1.2)

    # Urgency (temporal horizon)
    s_urgency = 1.0 - np.power(balls_rem / max_balls, 0.75)

    # Contestability / Closeness via Win Probability proxy
    # z represents standardized run surplus/deficit relative to expected run rate
    expected_run_rate_per_ball = 1.35 - 0.07 * (10 - wickets_in_hand)
    z = (runs_needed - balls_rem * expected_run_rate_per_ball) / np.sqrt(balls_rem * 1.8 + 1.0)
    p_win = 1.0 / (1.0 + np.exp(np.clip(1.1 * z, -12.0, 12.0)))
    c_match = 4.0 * p_win * (1.0 - p_win)

    p_bat_chase = 100.0 * (0.38 * s_rate + 0.32 * s_wicket + 0.20 * s_urgency + 0.10 * s_rate * s_urgency) * (0.35 + 0.65 * c_match)
    p_bat_chase = np.clip(p_bat_chase, 0.0, 100.0)

    # Bowler pressure in 2nd innings:
    # High when match is close (c_match is high) and RRR is reachable or death overs
    # Suppressed when batting team is 7+ down with high required rate (clean-up mode)
    bowler_suppression = np.where((wickets_in_hand <= 2) & (rrr > 14.0), 0.40, 1.0)
    p_bowl_chase = 100.0 * (0.42 * (1.0 - s_rate * 0.4) + 0.28 * s_urgency + 0.30 * c_match) * bowler_suppression
    # Bowler pressure is highest when defending small margins in death overs
    death_defense_boost = np.where((balls_rem <= 30) & (rrr >= 7.0) & (rrr <= 14.0) & (wickets_in_hand >= 4), 1.25, 1.0)
    p_bowl_chase = np.clip(p_bowl_chase * death_defense_boost, 0.0, 100.0)

    # --- 2. FIRST INNINGS CALCULATIONS ---
    r_res = np.power(balls_rem / max_balls, 0.65) * np.power(np.maximum(1, wickets_in_hand) / 10.0, 0.5)
    s_proj = cum_runs + par_score_default * r_res
    delta_par = (par_score_default - s_proj) / par_score_default

    # Batting pressure: Crisis from lost wickets + par deficit + death acceleration
    crisis_factor = np.power(np.clip(cum_wickets / 9.0, 0.0, 1.0), 1.2)
    deficit_factor = np.clip((delta_par + 0.20) / 0.45, 0.0, 1.0)
    death_accel_factor = np.power(1.0 - balls_rem / max_balls, 1.5)

    p_bat_first = 100.0 * (0.35 * deficit_factor + 0.35 * crisis_factor + 0.30 * death_accel_factor)
    p_bat_first = np.clip(p_bat_first, 0.0, 100.0)

    # Bowler pressure in 1st innings:
    # High in death overs (overs 16-20) and when batting team is accelerating well ahead of par
    lead_factor = np.clip((-delta_par + 0.10) / 0.40, 0.0, 1.0)
    p_bowl_first = 100.0 * (0.40 * death_accel_factor + 0.35 * lead_factor + 0.25 * (1.0 - crisis_factor))
    p_bowl_first = np.clip(p_bowl_first, 0.0, 100.0)

    # --- 3. SUPER OVERS (Innings >= 3) ---
    p_super = np.clip(85.0 + 2.5 * innings_ball, 85.0, 100.0)

    # Combine into unified continuous pressure series
    p_bat = np.where(innings == 1, p_bat_first,
            np.where(innings == 2, p_bat_chase, p_super))

    p_bowl = np.where(innings == 1, p_bowl_first,
             np.where(innings == 2, p_bowl_chase, p_super))

    df["pressure_score_bat"] = np.round(p_bat, 2)
    df["pressure_score_bowl"] = np.round(p_bowl, 2)

    # Unified baseline pressure score (mean of bat and bowl context or role-specific)
    df["pressure_score"] = np.round((df["pressure_score_bat"] + df["pressure_score_bowl"]) / 2.0, 2)

    # Discretized categories for interpretability
    # Official thresholds: Low [0, 35), Moderate [35, 60), High [60, 80), Extreme [80, 100]
    bins = [-1.0, 35.0, 60.0, 80.0, 100.1]
    labels = ["Low", "Moderate", "High", "Extreme"]
    df["pressure_category_bat"] = pd.cut(df["pressure_score_bat"], bins=bins, labels=labels)
    df["pressure_category_bowl"] = pd.cut(df["pressure_score_bowl"], bins=bins, labels=labels)
    df["pressure_category"] = pd.cut(df["pressure_score"], bins=bins, labels=labels)

    logger.info("Pressure calculation complete.")
    logger.info(f"Batting Pressure distribution: Mean={df['pressure_score_bat'].mean():.2f}, Median={df['pressure_score_bat'].median():.2f}")
    logger.info(f"Bowling Pressure distribution: Mean={df['pressure_score_bowl'].mean():.2f}, Median={df['pressure_score_bowl'].median():.2f}")

    return df

def get_pressure_threshold_variants(df, thresholds_dict=None):
    """
    Performs sensitivity analysis by applying alternative pressure threshold sets.
    """
    if thresholds_dict is None:
        thresholds_dict = {
            "Standard": [-1.0, 35.0, 60.0, 80.0, 100.1],
            "Aggressive_High": [-1.0, 30.0, 50.0, 75.0, 100.1],
            "Conservative_High": [-1.0, 40.0, 65.0, 85.0, 100.1]
        }
    
    results = {}
    for name, b in thresholds_dict.items():
        results[name] = pd.cut(df["pressure_score"], bins=b, labels=["Low", "Moderate", "High", "Extreme"]).value_counts(normalize=True) * 100
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    from preprocessing import load_and_preprocess_data
    df, _, _, _, _ = load_and_preprocess_data()
    df = compute_pressure_indices(df)
    print("Pressure category distribution for Batters:\n", df["pressure_category_bat"].value_counts(normalize=True)*100)
    print("Pressure category distribution for Bowlers:\n", df["pressure_category_bowl"].value_counts(normalize=True)*100)

