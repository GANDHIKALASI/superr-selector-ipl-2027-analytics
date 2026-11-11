"""
SupeRR Selector Season 2 - Rajasthan Royals IPL 2027 Auction Analytics
Module: reliability_model.py
Author: Senior Cricket Data Scientist & Quantitative Sports Analyst
Purpose: Statistically defensible Batter & Bowler Pressure Reliability Scores [0-100]
         integrating Empirical Bayes shrinkage, multi-pillar composite weighting,
         competition contextualization, and match-level bootstrap confidence intervals.
"""

import logging
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ReliabilityModel")

def robust_scale(series, lower_pct=5.0, upper_pct=95.0, invert=False):
    """
    Winsorized Min-Max scaling to map raw metrics into a robust [0, 100] scale.
    """
    s = series.copy().astype(float)
    q_low = np.percentile(s.dropna(), lower_pct)
    q_high = np.percentile(s.dropna(), upper_pct)
    if q_high <= q_low:
        return pd.Series(50.0, index=series.index)
    
    clipped = np.clip(s, q_low, q_high)
    scaled = (clipped - q_low) / (q_high - q_low) * 100.0
    if invert:
        scaled = 100.0 - scaled
    return scaled

def build_batter_reliability_model(bat_metrics, min_pres_balls=45, min_total_balls=150):
    """
    Constructs the Batter Pressure Reliability Score (BRS) [0-100].
    Applies Empirical Bayes shrinkage and combines 5 analytical pillars.
    """
    logger.info("Building Batter Pressure Reliability Model...")
    df = bat_metrics[(bat_metrics["total_balls_faced"] >= min_total_balls) & 
                     (bat_metrics["pres_balls_faced"] >= min_pres_balls)].copy()

    if len(df) == 0:
        raise ValueError("No batters met the eligibility criteria.")

    # 1. EMPIRICAL BAYES SHRINKAGE (Priors estimated directly from eligible candidate cohort)
    prior_sr = float(df["pres_sr"].mean()) if not df["pres_sr"].empty else 138.0
    k_sr = 60.0  # shrinkage pseudo-balls calibrated to batter sample distribution
    df["shrunk_pres_sr"] = (df["pres_balls_faced"] * df["pres_sr"] + k_sr * prior_sr) / (df["pres_balls_faced"] + k_sr)

    # Boundary pct prior
    prior_bp = float(df["pres_boundary_pct"].mean()) if not df["pres_boundary_pct"].empty else 17.5
    k_bp = 60.0
    df["shrunk_pres_bp"] = (df["pres_balls_faced"] * df["pres_boundary_pct"] + k_bp * prior_bp) / (df["pres_balls_faced"] + k_bp)

    # Dot pct prior (lower is better)
    prior_dp = float(df["pres_dot_pct"].mean()) if not df["pres_dot_pct"].empty else 38.0
    k_dp = 60.0
    df["shrunk_pres_dp"] = (df["pres_balls_faced"] * df["pres_dot_pct"] + k_dp * prior_dp) / (df["pres_balls_faced"] + k_dp)

    # Shrunk resilience differentials (prevents small-sample unshrunk spikes in Pillar 2)
    df["shrunk_delta_sr"] = df["shrunk_pres_sr"] - df["norm_sr"]
    df["shrunk_retention_ratio"] = df["shrunk_pres_sr"] / np.maximum(1.0, df["norm_sr"])
    df["shrunk_delta_bp"] = df["shrunk_pres_bp"] - df["norm_boundary_pct"]

    # 2. PILLAR 1: Absolute Pressure Execution (30%)
    p1_sr = robust_scale(df["shrunk_pres_sr"])
    p1_bp = robust_scale(df["shrunk_pres_bp"])
    p1_dp = robust_scale(df["shrunk_pres_dp"], invert=True)  # lower dots = higher score
    p1_avg = robust_scale(df["pres_avg"])
    pillar_1_execution = 0.40 * p1_sr + 0.25 * p1_bp + 0.20 * p1_dp + 0.15 * p1_avg

    # 3. PILLAR 2: Baseline Resilience & Retention (25%)
    p2_delta_sr = robust_scale(df["shrunk_delta_sr"])
    p2_retention = robust_scale(df["shrunk_retention_ratio"])
    p2_delta_bp = robust_scale(df["shrunk_delta_bp"])
    pillar_2_resilience = 0.45 * p2_delta_sr + 0.35 * p2_retention + 0.20 * p2_delta_bp

    # 4. PILLAR 3: Match-to-Match Consistency (20%)
    p3_cv = robust_scale(df["cv_pres_runs"], invert=True)  # lower CV = higher consistency
    p3_success = robust_scale(df["pres_success_rate"])
    pillar_3_consistency = 0.50 * p3_cv + 0.50 * p3_success

    # 5. PILLAR 4: Situation Leverage & Weighted Execution (15%)
    p4_wsr = robust_scale(df["weighted_sr"])
    p4_wbp = robust_scale(df["weighted_boundary_pct"])
    pillar_4_leverage = 0.60 * p4_wsr + 0.40 * p4_wbp

    # 6. PILLAR 5: Sample Confidence & Competition Quality (10%)
    # Sigmoid sample confidence
    n_balls = df["pres_balls_faced"].values
    sample_conf = 100.0 / (1.0 + np.exp(-0.035 * (n_balls - 90.0)))
    # IPL exposure boost (0 to 100)
    ipl_factor = df["ipl_ratio"].values * 100.0
    pillar_5_confidence = 0.60 * sample_conf + 0.40 * ipl_factor

    # FINAL COMPOSITE SCORE
    raw_brs = (0.30 * pillar_1_execution +
               0.25 * pillar_2_resilience +
               0.20 * pillar_3_consistency +
               0.15 * pillar_4_leverage +
               0.10 * pillar_5_confidence)

    df["pillar_execution"] = np.round(pillar_1_execution, 2)
    df["pillar_resilience"] = np.round(pillar_2_resilience, 2)
    df["pillar_consistency"] = np.round(pillar_3_consistency, 2)
    df["pillar_leverage"] = np.round(pillar_4_leverage, 2)
    df["pillar_confidence"] = np.round(pillar_5_confidence, 2)
    df["reliability_score"] = np.round(np.clip(raw_brs, 0.0, 100.0), 2)

    df = df.sort_values("reliability_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    logger.info(f"Batter Reliability Model built for {len(df)} batters. Top 1: {df.iloc[0]['player_name']} ({df.iloc[0]['reliability_score']})")
    return df

def build_bowler_reliability_model(bowl_metrics, min_pres_balls=60, min_total_balls=150):
    """
    Constructs the Bowler Pressure Reliability Score (PRS) [0-100].
    Applies Empirical Bayes shrinkage and combines 5 defensive pillars.
    """
    logger.info("Building Bowler Pressure Reliability Model...")
    df = bowl_metrics[(bowl_metrics["total_legal_balls"] >= min_total_balls) & 
                      (bowl_metrics["pres_legal_balls"] >= min_pres_balls)].copy()

    if len(df) == 0:
        raise ValueError("No bowlers met the eligibility criteria.")

    # 1. EMPIRICAL BAYES SHRINKAGE (Priors estimated directly from eligible candidate cohort)
    prior_econ = float(df["pres_economy"].mean()) if not df["pres_economy"].empty else 9.35
    k_econ = 80.0  # shrinkage pseudo-balls calibrated to bowling sample distribution
    df["shrunk_pres_economy"] = (df["pres_legal_balls"] * df["pres_economy"] + k_econ * prior_econ) / (df["pres_legal_balls"] + k_econ)

    # Dot pct prior
    prior_dp = float(df["pres_dot_pct"].mean()) if not df["pres_dot_pct"].empty else 33.0
    k_dp = 80.0
    df["shrunk_pres_dp"] = (df["pres_legal_balls"] * df["pres_dot_pct"] + k_dp * prior_dp) / (df["pres_legal_balls"] + k_dp)

    # Wicket rate prior
    prior_wr = float(df["pres_wkt_rate"].mean()) if not df["pres_wkt_rate"].empty else 5.2
    k_wr = 80.0
    df["shrunk_pres_wr"] = (df["pres_legal_balls"] * df["pres_wkt_rate"] + k_wr * prior_wr) / (df["pres_legal_balls"] + k_wr)

    # Death-over economy prior (shrinks 13-ball death samples toward cohort death mean)
    death_sub = df[df["death_legal_balls"] >= 30]["death_economy"]
    prior_death_econ = float(death_sub.mean()) if not death_sub.empty else 9.5
    k_death = 40.0
    df["shrunk_death_economy"] = (df["death_legal_balls"] * df["death_economy"] + k_death * prior_death_econ) / (df["death_legal_balls"] + k_death)

    # Shrunk resilience differentials
    df["norm_wkt_rate"] = df["pres_wkt_rate"] - df["delta_wkt_rate"]
    df["shrunk_delta_economy"] = df["shrunk_pres_economy"] - df["norm_economy"]
    df["shrunk_delta_dp"] = df["shrunk_pres_dp"] - df["norm_dot_pct"]
    df["shrunk_delta_wr"] = df["shrunk_pres_wr"] - df["norm_wkt_rate"]

    # 2. PILLAR 1: Absolute Pressure Execution (30%)
    p1_econ = robust_scale(df["shrunk_pres_economy"], invert=True)  # lower economy is better
    p1_dp = robust_scale(df["shrunk_pres_dp"])
    p1_wr = robust_scale(df["shrunk_pres_wr"])
    p1_avg = robust_scale(df["pres_avg"], invert=True)
    pillar_1_execution = 0.40 * p1_econ + 0.25 * p1_dp + 0.20 * p1_wr + 0.15 * p1_avg

    # 3. PILLAR 2: Baseline Resilience & Economy Control (25%)
    p2_delta_econ = robust_scale(df["shrunk_delta_economy"], invert=True)  # lower delta economy is better
    p2_delta_dp = robust_scale(df["shrunk_delta_dp"])
    p2_delta_wr = robust_scale(df["shrunk_delta_wr"])
    pillar_2_resilience = 0.50 * p2_delta_econ + 0.25 * p2_delta_dp + 0.25 * p2_delta_wr

    # 4. PILLAR 3: Match-to-Match Consistency (20%)
    p3_cv = robust_scale(df["cv_pres_economy"], invert=True)  # lower CV is better
    p3_success = robust_scale(df["pres_success_rate"])
    pillar_3_consistency = 0.50 * p3_cv + 0.50 * p3_success

    # 5. PILLAR 4: Death Overs & High-Leverage Mastery (15%)
    p4_death_econ = robust_scale(df["shrunk_death_economy"], invert=True)
    p4_death_dots = robust_scale(df["death_dot_pct"])
    p4_death_wkts = robust_scale(df["death_wickets"])
    pillar_4_leverage = 0.45 * p4_death_econ + 0.30 * p4_death_dots + 0.25 * p4_death_wkts

    # 6. PILLAR 5: Sample Confidence & Competition Quality (10%)
    n_balls = df["pres_legal_balls"].values
    sample_conf = 100.0 / (1.0 + np.exp(-0.02 * (n_balls - 150.0)))
    ipl_factor = df["ipl_ratio"].values * 100.0
    pillar_5_confidence = 0.60 * sample_conf + 0.40 * ipl_factor

    # FINAL COMPOSITE SCORE
    raw_prs = (0.30 * pillar_1_execution +
               0.25 * pillar_2_resilience +
               0.20 * pillar_3_consistency +
               0.15 * pillar_4_leverage +
               0.10 * pillar_5_confidence)

    df["pillar_execution"] = np.round(pillar_1_execution, 2)
    df["pillar_resilience"] = np.round(pillar_2_resilience, 2)
    df["pillar_consistency"] = np.round(pillar_3_consistency, 2)
    df["pillar_leverage"] = np.round(pillar_4_leverage, 2)
    df["pillar_confidence"] = np.round(pillar_5_confidence, 2)
    df["reliability_score"] = np.round(np.clip(raw_prs, 0.0, 100.0), 2)

    df = df.sort_values("reliability_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    logger.info(f"Bowler Reliability Model built for {len(df)} bowlers. Top 1: {df.iloc[0]['player_name']} ({df.iloc[0]['reliability_score']})")
    return df

def run_match_level_bootstrap(df_raw, player_ids, role="bat", n_bootstraps=300):
    """
    Performs match-level cluster bootstrap resampling to compute
    95% confidence intervals and standard errors for reliability scores.
    Crucial: Resamples MATCHES, not deliveries, preserving intraday correlation!
    """
    logger.info(f"Running match-level bootstrap ({n_bootstraps} iterations) for {len(player_ids)} {role} players...")
    unique_matches = df_raw["match_id"].unique()
    n_matches = len(unique_matches)
    rng = np.random.default_rng(42)

    bootstrap_scores = {pid: [] for pid in player_ids}

    # Pre-filter deliveries of target players to accelerate bootstrap loop
    if role == "bat":
        df_target = df_raw[df_raw["striker_id"].isin(player_ids)].copy()
        for i in range(n_bootstraps):
            sampled_matches = rng.choice(unique_matches, size=n_matches, replace=True)
            match_counts = pd.Series(sampled_matches).value_counts()
            
            # Subsample
            sample_df = df_target[df_target["match_id"].isin(match_counts.index)].copy()
            # Weight by match occurrences in sample
            sample_df["m_weight"] = sample_df["match_id"].map(match_counts)
            
            # Fast score approximation on resampled data
            for pid in player_ids:
                p_sub = sample_df[sample_df["striker_id"] == pid]
                if len(p_sub) == 0:
                    continue
                pres_sub = p_sub[p_sub["pressure_score_bat"] >= 50.0]
                if len(pres_sub) == 0:
                    continue
                
                # Check match cluster count for player
                n_matches_player = pres_sub["match_id"].nunique()
                if n_matches_player <= 2:
                    # Two-stage bootstrap: Resample deliveries with replacement to capture intra-match execution variance
                    drawn_balls = pres_sub.sample(n=len(pres_sub), replace=True, random_state=rng)
                    sr_sample = (drawn_balls["runs"].sum() / max(1, len(drawn_balls))) * 100.0
                else:
                    w = p_sub["m_weight"].values
                    pres_mask = (p_sub["pressure_score_bat"] >= 50.0).values
                    pres_balls = np.sum(w * pres_mask)
                    if pres_balls < 10:
                        continue
                    pres_runs = np.sum(w * pres_mask * p_sub["runs"].values)
                    sr_sample = (pres_runs / max(1, pres_balls)) * 100.0
                bootstrap_scores[pid].append(sr_sample)
    else:
        df_target = df_raw[df_raw["bowler_id"].isin(player_ids)].copy()
        for i in range(n_bootstraps):
            sampled_matches = rng.choice(unique_matches, size=n_matches, replace=True)
            match_counts = pd.Series(sampled_matches).value_counts()
            
            sample_df = df_target[df_target["match_id"].isin(match_counts.index)].copy()
            sample_df["m_weight"] = sample_df["match_id"].map(match_counts)
            
            for pid in player_ids:
                p_sub = sample_df[sample_df["bowler_id"] == pid]
                if len(p_sub) == 0:
                    continue
                pres_sub = p_sub[(p_sub["pressure_score_bowl"] >= 55.0) & (p_sub["is_legal"] == 1)]
                if len(pres_sub) == 0:
                    continue
                
                n_matches_player = pres_sub["match_id"].nunique()
                if n_matches_player <= 2:
                    # Two-stage bootstrap: Resample deliveries with replacement
                    drawn_balls = pres_sub.sample(n=len(pres_sub), replace=True, random_state=rng)
                    econ_sample = (drawn_balls["bowler_runs_conceded"].sum() / max(1, len(drawn_balls))) * 6.0
                else:
                    w = p_sub["m_weight"].values
                    pres_mask = (p_sub["pressure_score_bowl"] >= 55.0).values & (p_sub["is_legal"] == 1).values
                    pres_legal = np.sum(w * pres_mask)
                    if pres_legal < 10:
                        continue
                    pres_runs = np.sum(w * pres_mask * p_sub["bowler_runs_conceded"].values)
                    econ_sample = (pres_runs / max(1, pres_legal)) * 6.0
                bootstrap_scores[pid].append(econ_sample)

    ci_results = {}
    for pid, samples in bootstrap_scores.items():
        if len(samples) >= 20:
            ci_low = np.percentile(samples, 2.5)
            ci_high = np.percentile(samples, 97.5)
            se = np.std(samples)
            ci_results[pid] = {
                "ci_lower": round(ci_low, 2),
                "ci_upper": round(ci_high, 2),
                "std_error": round(se, 2),
                "bootstrap_samples_count": len(samples)
            }
        else:
            ci_results[pid] = {
                "ci_lower": 0.0,
                "ci_upper": 0.0,
                "std_error": 0.0,
                "bootstrap_samples_count": len(samples)
            }

    return ci_results

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

    top_batters = build_batter_reliability_model(bat_metrics)
    top_bowlers = build_bowler_reliability_model(bowl_metrics)

    print("=== TOP 10 BATTERS UNDER PRESSURE ===")
    print(top_batters[["rank", "player_id", "player_name", "reliability_score", "pres_runs", "pres_balls_faced", "norm_sr", "pres_sr", "delta_sr"]].head(10).to_string(index=False))

    print("\n=== TOP 10 BOWLERS UNDER PRESSURE ===")
    print(top_bowlers[["rank", "player_id", "player_name", "reliability_score", "pres_wickets", "pres_legal_balls", "norm_economy", "pres_economy", "delta_economy"]].head(10).to_string(index=False))

