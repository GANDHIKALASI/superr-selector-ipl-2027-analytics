# Deployment & Data-Boundary Guide — SupeRR Selector Analytics

This document explains how the interactive **SupeRR Selector Players Dashboard** runs both locally and on **Vercel**, while keeping proprietary raw CSV datasets, internal eligibility/identity audits, and confidential reports restricted to the local workspace.

---

## 1. Public Cloud vs Local Workspace Separation

| Asset Category | Local Workspace (`localhost`) | GitHub & Vercel Production |
| :--- | :--- | :--- |
| **Interactive Players Dashboard (`/` & `/api/batters`, `/api/bowlers`, `/api/overall`, `/api/allrounders`, `/api/all-players`, `/api/reliability`, `/api/data-quality`)** | Enabled (reads 7 derived dashboard files from `outputs/`) | Enabled (bundles only the 7 derived dashboard files via `vercel.json`) |
| **Raw Ball-by-Ball & Match CSVs (`data/*.csv`)** | Local only | Excluded & `HTTP 403` blocked |
| **Internal Identity / Eligibility Audits (`outputs/player_*_audit.csv`, `outputs/candidate_*.csv`)** | Local only | Excluded & `HTTP 403` blocked |
| **Confidential PDF & PPTX Deliverables (`submission/`, `reports/`, `/download/*`)** | Enabled locally | Excluded & `HTTP 403` blocked (`reportsDownloadEnabled: false`) |
| **Private Screenshots (`assets/screenshot_*.png`)** | Local only | Excluded & `HTTP 404` blocked |

### Missing-File Guard
If any of the 7 required derived dashboard files in `outputs/` (`top_10_batters.csv`, `top_10_bowlers.csv`, `top_10_overall.csv`, `top_10_allrounders.csv`, `eligible_player_universe.csv`, `all_player_reliability_scores.csv`, `data_quality_summary.json`) is missing, the server returns `HTTP 500` and displays an explicit error banner instead of inventing substitute data.

---

## 2. Local Commands (`Node.js 22.x`)

```bash
# Run full interactive dashboard locally
npm start

# Preview public Vercel behavior locally (hides & blocks PDF/PPTX downloads)
npm run start:public

# Verify derived dashboard & privacy boundaries
npm run test:privacy
```

---

## 3. Vercel Deployment Settings

[`vercel.json`](./vercel.json) routes all requests through [`api/index.js`](./api/index.js) and bundles only the Node server, static frontend, allowed branding images, and the 7 derived dashboard JSON/CSV files.
In Vercel Project Settings:
- **Framework Preset:** `Other`
- **Build Command:** *(leave empty)*
- **Output Directory:** *(leave empty)*
- **Install Command:** *(leave empty)*
