# Dataset Documentation & Setup Guide

This directory holds the historical cricket datasets supplied for **SupeRR Selector Season 2** (2022 to 2026).

## Required CSV Files
1. `ball_by_ball.csv` (200,999 records): Delivery-level tracking for 867 matches.
2. `matches.csv` (883 records): Match metadata, dates, venues, targets, and revised overs.
3. `competitions.csv`: Tournament identifiers (IPL, T20I, T20).
4. `teams.csv`: Team names, franchises, and nation codes.
5. `playing_eleven.csv`: Lineup participation per match.
6. `competition_team_player_mapping.csv`: Canonical player mappings, team rosters, and IDs.

## Data Setup Instructions
If cloning from GitHub without large data files:
1. Download the official `6af3166e7b922_data_pack.zip` from Unstop.
2. Unzip all 6 CSV files into this `data/` directory:
   ```bash
   unzip data_pack.zip -d data/
   ```
3. Run `PYTHONPATH=src python src/rankings.py` to regenerate all analytics and rankings.

