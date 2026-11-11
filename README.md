# SupeRR Selector — High-Pressure T20 Player Reliability Analytics (IPL 2027)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Methodology: Empirical Bayes & Cluster Bootstrap](https://img.shields.io/badge/Methodology-Empirical%20Bayes%20%26%20Cluster%20Bootstrap-101827.svg)](docs/pressure_model.md)

> **Sanitized Public Methodology Release:** This public repository contains the core quantitative Python modeling modules, delivery-level pressure specification, and validation framework developed for the **SupeRR Selector Season 2** high-pressure T20 scouting problem. Per proprietary competition data restrictions, original ball-by-ball CSVs, player-level statistics, derived rankings, eligibility audits, and full scouting reports are **withheld locally** and excluded from version control.

---

## Confidentiality & Scope Notice

Because this repository is public and the competition dataset is proprietary:
- **Included in Public GitHub:** Generalized delivery-level pressure equations ([`docs/pressure_model.md`](docs/pressure_model.md)), quantitative modeling modules (`src/`), schema documentation ([`data/README.md`](data/README.md)), project configuration (`requirements.txt`), and MIT license (`LICENSE`).
- **Withheld Locally (`.gitignore`d):** Raw competition CSV files (`data/*.csv`), derived player metrics and rankings (`outputs/`), identity/exclusion scripts holding competition player IDs, full analytical reports (`reports/`), and official submission packages (`submission/`).
- **Zero Synthetic Placeholders:** No fabricated or synthetic player datasets are included in place of private competition records.
- **Methodology Scope:** All statistical modeling evaluates historical on-field high-pressure execution only; player auction availability, franchise retention lists, salary caps, and medical/fitness status lie outside the analytical scope.

---

## Quantitative Architecture

The analytics pipeline separates repeatable high-pressure execution from small-sample noise across five modular stages:

1. **Delivery-Level Pre-Ball Pressure Index ($P \in [0, 100]$)** — Implemented in [`src/pressure_model.py`](src/pressure_model.py) and specified in [`docs/pressure_model.md`](docs/pressure_model.md). Computes match jeopardy strictly **prior to each delivery** using inning phase, balls remaining, wickets in hand, required run rate vs. par scoring expectation (2nd innings), expected target pressure (1st innings), and knockout/super-over leverage without lookahead leakage.
2. **Baseline vs. High-Pressure Role Metrics** — Implemented in [`src/batting_metrics.py`](src/batting_metrics.py) and [`src/bowling_metrics.py`](src/bowling_metrics.py). Separates high-pressure deliveries ($P_{\text{bat}} \ge 50.0$ for batters; $P_{\text{bowl}} \ge 55.0$ for bowlers) from each player's personal normal baseline while enforcing legal-delivery vs. wide/no-ball cricket accounting (`ball_total_runs` vs. `bowler_runs_conceded` excluding byes/leg-byes).
3. **Two-Tier Empirical Bayes Shrinkage & 5-Pillar Scoring (BRS / PRS)** — Implemented in [`src/reliability_model.py`](src/reliability_model.py). Applies conjugate Bayesian shrinkage ($k_{\text{bat}} = 60$, $k_{\text{bowl}} = 80$, death overs $k_{\text{death}} = 40$) to stabilize strike rate, boundary rate, dot-ball percentage, economy, and wicket-taking under pressure, combining shrunk execution, pressure-vs-normal retention ($\Delta$), match-level consistency, continuous pressure-weighted leverage, and sample confidence into composite Batting Reliability Score (**BRS**) and Bowling Reliability Score (**PRS**).
4. **Cross-Role Precision Weighting & Bootstrap Uncertainty** — Implemented in [`src/reliability_model.py`](src/reliability_model.py) and [`src/validation.py`](src/validation.py). Quantifies uncertainty with two-stage **match-cluster bootstrap** resampling ($B = 300$) to preserve within-match delivery dependence, and synthesizes batters and bowlers on a shared $z$-score scale penalized by bootstrap standard error ($\text{Overall}_i = 50 + 10 \cdot z_i \cdot \sqrt{n_{\text{eff}} / (n_{\text{eff}} + \tau)}$).
5. **Robustness, Sensitivity & Chart Generation** — Implemented in [`src/validation.py`](src/validation.py) and [`src/generate_charts.py`](src/generate_charts.py). Evaluates out-of-sample temporal correlation, Spearman rank stability ($\rho$) across alternative pressure thresholds ($P \ge 55, 65$) and shrinkage priors ($k \pm 20$), and generates publication-grade diagnostic charts.

---

## Repository Structure (Public Release)

```text
superr-selector-ipl-2027-analytics/
├── assets/                     # Project crest, logo, and author avatar
├── data/
│   └── README.md               # Expected schema for local competition CSV files
├── docs/
│   └── pressure_model.md       # Mathematical derivation of P_bat, P_bowl in [0, 100]
├── src/
│   ├── __init__.py
│   ├── pressure_model.py       # Pre-delivery continuous pressure & phase tagging
│   ├── batting_metrics.py      # Batting normal vs. high-pressure execution metrics
│   ├── bowling_metrics.py      # Legal-ball accounting & bowling pressure metrics
│   ├── reliability_model.py    # Empirical Bayes shrinkage, BRS/PRS & cluster CIs
│   ├── validation.py           # Out-of-sample split & sensitivity stability tests
│   └── generate_charts.py      # High-DPI analytical chart exporter
├── .gitignore                  # Protects local raw CSVs, outputs/, reports/, submission/
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Local Reproduction (With Authorized Competition Data)

In an authorized private competition workspace containing the 6 source CSV tables under `data/` and the full ingestion/ranking/test modules:

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Data Placement
Place the authorized competition CSV files inside `data/` as documented in [`data/README.md`](data/README.md):
- `ball_by_ball.csv`
- `matches.csv`
- `competitions.csv`
- `teams.csv`
- `playing_eleven.csv`
- `competition_team_player_mapping.csv`

### 3. Run Pipeline & Verification Suite (Authorized Local Workspace)
```bash
PYTHONPATH=src python src/rankings.py
PYTHONPATH=src python src/generate_charts.py
pytest -rs -v
```

---

## Author

**Gandhi Kalasi**  
Quantitative Cricket Analytics & Sports Data Engineering  
Repository: `GANDHIKALASI/superr-selector-ipl-2027-analytics`  
License: [MIT](LICENSE)
