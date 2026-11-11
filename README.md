<div align="center">
  <img src="assets/superr_logo.png" alt="SupeRR Selector — IPL 2027 Analytics Logo" width="380" />

  <h1>SupeRR Selector — IPL 2027 Analytics</h1>

  <p>
    <strong>Auditable T20 Pressure Reliability Analytics Engine &amp; Interactive War Room Dashboard built for Rajasthan Royals' SupeRR Selector Season 2.</strong>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Competition-SupeRR%20Selector%20Season%202-E84D87?style=flat-square" alt="SupeRR Selector Season 2" />
    <img src="https://img.shields.io/badge/Python-3.12%20%7C%20SciPy%20%7C%20Pandas-141B38?style=flat-square" alt="Python Analytics Pipeline" />
    <img src="https://img.shields.io/badge/Node.js-22.x%20Zero--Dependency-D6B46A?style=flat-square" alt="Node.js 22.x Server" />
    <img src="https://img.shields.io/badge/Dashboard-Derived%20Player%20Rankings-24C58A?style=flat-square" alt="Derived Player Rankings Dashboard" />
    <img src="https://img.shields.io/badge/License-MIT-64748B?style=flat-square" alt="MIT License" />
  </p>
</div>

---

## Project Purpose & Competition Context

Built for **Rajasthan Royals' SupeRR Selector Season 2**, this project addresses the Round 1 analytical challenge:

> **"Identify the Most Reliable Players Under Pressure."**

Rather than relying on aggregate career averages, the system evaluates delivery-level T20 match context across domestic and international fixtures to measure how batters, bowlers, and dual-skill all-rounders execute when scoreboard urgency and match leverage peak—supporting data-driven player shortlisting for IPL 2027 auction planning.

---

## Key Capabilities & Analytical Methodology

### 1. Continuous Context-Aware Pressure Model (`src/pressure_model.py`)
Every delivery is scored pre-ball on a continuous $P \in [0, 100]$ scale derived from cumulative runs, balls remaining, wickets in hand, required run rate (second innings), phase rebuilding/death acceleration (first innings), and match closeness $C_{\text{match}} = 4 P_{\text{win}}(1 - P_{\text{win}})$.

### 2. Five-Pillar Reliability Indices (`src/batting_metrics.py`, `src/bowling_metrics.py`)
Constructs separate **Batting Reliability Score (BRS)** and **Bowling Reliability Score (PRS)** on a `0–100` cohort percentile scale using **Empirical Bayes shrinkage**:
- **Pressure Execution:** Shrunk pressure strike rate or pressure economy combined with boundary, dot-ball, and wicket efficiency.
- **Pressure Resilience ($\Delta$ Metrics):** Differential performance under pressure relative to each player's own normal-overs baseline, preventing inflated small-sample spikes.
- **Consistency, Leverage & Sample Confidence:** Match-level repeatability and effective pressure volume weighting.

### 3. Precision-Weighted Cross-Role Standardization & Honest Uncertainty (`src/reliability_model.py`)
Unifies specialist batters, specialist bowlers, and dual-skill all-rounders using precision-weighted cross-role $z$-scores ($Z_{\text{adj}}$) with role priors $\tau_{\text{role}} = 0.5 \cdot \text{median}(n_{\text{pres, role}})$ and **300-iteration two-stage match-cluster bootstrap 95% confidence intervals** to preserve intra-match correlation structure.

### 4. Out-of-Sample & Sensitivity Validation (`src/validation.py`)
Validates model behavior across chronological temporal splits, format comparisons (Spearman $\rho$ and Kendall $\tau$), alternative weight perturbations, and minimum sample threshold sensitivity checks.

### 5. Interactive Players Dashboard (`server.js`, `public/`)
Zero-dependency Node.js & Vercel web dashboard featuring sortable Top-10 Batters, Top-10 Bowlers, Final Top-10 Overall, Dual All-Rounders, Screened Candidate Pool search, interactive Chart.js visuals, player inspection dossiers, KaTeX equations, and Data Quality validation cards.

---

## Technical Architecture & Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Statistical Pipeline** | Python, Pandas, NumPy, SciPy | Delivery pressure scoring, Empirical Bayes shrinkage, cluster bootstrap CIs, cross-role standardization |
| **Visualization & UI** | Chart.js, KaTeX, Matplotlib | Interactive sortable leaderboards, pressure charts, mathematical notation |
| **Web & API Runtime** | Node.js `22.x` (`http`, `fs`, `path`), [`server.js`](server.js) | Serves interactive derived player dashboard locally & on Vercel with `HTTP 403` isolation on raw CSVs and private reports |
| **Cloud Deployment** | Vercel Serverless Functions ([`api/index.js`](api/index.js), [`vercel.json`](vercel.json)) | Live web hosting of derived leaderboards with raw data & confidential reports excluded |
| **Verification** | Pytest, Node `assert` ([`tests/test_public_privacy.js`](tests/test_public_privacy.js)) | Privacy-boundary verification & missing-file fail-closed checks |

---

## Project Structure

```text
├── api/
│   └── index.js                             # Vercel Serverless entrypoint wrapping server.js
├── assets/
│   ├── gandhi-kalasi.jpg                    # Developer profile photo
│   ├── superr_crest.png                     # Custom SupeRR Selector crest badge
│   └── superr_logo.png                      # Project logo displayed above
├── outputs/                                 # Derived dashboard feeds only (raw/audit CSVs excluded)
│   ├── all_player_reliability_scores.csv
│   ├── data_quality_summary.json
│   ├── eligible_player_universe.csv
│   ├── top_10_allrounders.csv
│   ├── top_10_batters.csv
│   ├── top_10_bowlers.csv
│   └── top_10_overall.csv
├── public/
│   ├── app.js                               # Client UI controller, sorting & Chart.js logic
│   ├── favicon.svg                          # Brand favicon
│   ├── index.html                           # Interactive Players Dashboard UI
│   ├── logo.svg                             # Vector header wordmark
│   └── style.css                            # Royale Obsidian & Gold responsive stylesheet
├── src/
│   ├── __init__.py
│   ├── batting_metrics.py                   # Empirical Bayes Batting Reliability Score (BRS)
│   ├── bowling_metrics.py                   # Empirical Bayes Bowling Reliability Score (PRS)
│   ├── generate_charts.py                   # Matplotlib figure generation
│   ├── pressure_model.py                    # Context-aware T20 delivery pressure model
│   ├── reliability_model.py                 # Match-cluster bootstrap & cross-role scoring
│   └── validation.py                        # Temporal, weight & threshold validation helpers
├── tests/
│   └── test_public_privacy.js               # Derived dashboard & boundary checks
├── .gitignore
├── .vercelignore
├── DEPLOYMENT.md                            # Runtime isolation & Vercel deployment guide
├── LICENSE
├── package.json
├── requirements.txt
├── server.js                                # Zero-dependency Node HTTP & Serverless handler
└── vercel.json                              # Vercel production routing configuration
```

---

## Local Installation & Setup

### Prerequisites
- **Node.js** `22.x`
- **Python** `3.10+` *(for running statistical modules locally)*

### Start the Dashboard
```bash
git clone https://github.com/GANDHIKALASI/superr-selector-ipl-2027-analytics.git
cd superr-selector-ipl-2027-analytics
npm start
```
Open `http://localhost:3000`.

### Preview Cloud Behavior & Run Verification Checks
```bash
npm run start:public    # Simulates Vercel mode (blocks PDF/PPTX download routes)
npm run test:privacy    # Runs derived dashboard & boundary checks
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Vercel deployment instructions.

---

## Privacy & Data-Handling Notice

- **Raw competition CSV datasets** (`data/*.csv` ball-by-ball, matches, lineups), **internal eligibility & identity audit tables** (`outputs/player_*_audit.csv`, `outputs/candidate_*.csv`), and **confidential competition PDF/PPTX deliverables** (`submission/`, `reports/`) are strictly excluded from GitHub and Vercel and return `HTTP 403` on cloud endpoints.
- **No mock or synthetic player data** is used anywhere in the repository or dashboard; every displayed ranking originates directly from verified statistical pipeline outputs.

---

## Developer Profile

<img src="assets/gandhi-kalasi.jpg" alt="Gandhi Kalasi" width="96" />

**Developed by Gandhi Kalasi**

- **GitHub:** https://github.com/GANDHIKALASI
- **LinkedIn:** https://www.linkedin.com/in/gandhi-kalasi/
- **Instagram:** https://instagram.com/bug_gandhi
