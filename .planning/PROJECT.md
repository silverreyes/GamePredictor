# NFL Game Predictor

## What This Is

An end-to-end NFL game outcome prediction system. Ingests 20 seasons of play-by-play data, engineers leakage-safe features, trains an XGBoost classifier that beats trivial baselines at 62.89% on the 2023 validation season. Predictions are served via FastAPI and displayed in a React dashboard with weekly picks, season accuracy tracking, experiment comparison, and prediction history. Automated weekly refresh pipeline with human approval gate, deployed via Docker Compose.

## Core Value

Pre-game win/loss predictions with calibrated confidence scores that beat trivial baselines on the 2023 validation season.

## Requirements

### Validated

- Ingest and store 20 seasons of NFL data in PostgreSQL with normalized team abbreviations -- v1.0
- Engineer leakage-safe game-level features with automated temporal validation -- v1.0
- XGBoost classifier via autoresearch experiment loop, beating both trivial baselines -- v1.0 (62.89% vs 55.51% always-home, 58.20% better-record)
- FastAPI prediction and model management endpoints with token-protected hot-reload -- v1.0
- React dashboard with 4 views: picks, accuracy, experiments, history -- v1.0
- Docker Compose deployment with automated weekly refresh and human approval gate -- v1.0

### Active

- [ ] Probability calibration (Platt scaling or isotonic regression) on validation set
- [ ] Advanced engineered features: CPOE, success rate, weighted rolling averages, opponent adjustments
- [ ] QB consistency features (EPA standard deviation across games)
- [ ] SHAP-based feature importance display per prediction in the dashboard
- [ ] Calibration plot: predicted win probability vs actual win rate by bucket
- [ ] Model performance over time chart (rolling accuracy by week)
- [ ] Weekly recap view with correct/incorrect game highlights

### Out of Scope

- Live in-game predictions -- pre-game only, no real-time scoring data
- Vegas spread/over-under ingestion -- confidence from model probability, not odds comparison
- Player-level injury/availability data -- team-level aggregate features only for v1
- Mobile app -- web dashboard only, PWA not yet explored
- User accounts / authentication -- single-user or open read access
- Neural network models -- gradient boosting outperforms deep learning on ~5K structured rows
- Betting advice framing -- predictions only, no wagering guidance

## Context

Shipped v1.0 with ~8,200 LOC (6,110 Python + 1,935 TypeScript + 146 SQL).
Tech stack: Python 3.11, PostgreSQL, nflreadpy, pandas, XGBoost, FastAPI, React + Vite + Tailwind v4 + shadcn/ui, Docker Compose, MLflow, APScheduler.
Data source: nflreadpy (was nfl-data-py, switched during Phase 1 for compatibility).
Best model: Experiment 5 -- lower learning rate (0.1) + early stopping, 62.89% on 2023 validation.
Full 17-feature set proved near-optimal; all ablation experiments degraded accuracy.

## Constraints

- **Data leakage**: All rolling features must use only data prior to the game being predicted -- strictly enforced via shift(1) + 6 automated leakage tests
- **Temporal split**: Train 2005-2022, validate 2023, holdout 2024 -- no shuffling across time boundaries
- **Stack**: Python 3.11, PostgreSQL, nflreadpy, pandas, XGBoost, FastAPI, React, Docker Compose, MLflow
- **Benchmark**: Must beat always-home (~57%) and better-record (~60%) baselines on the 2023 validation season specifically
- **Feature schema**: One row per game (home team perspective)
- **Team normalization**: Applied at ingestion via TEAM_ABBREV_MAP constant in data/sources.py
- **Deployment**: Docker Compose on Linux VPS -- 5 services (postgres, api, mlflow, worker, caddy)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| nflreadpy as data source | Free, comprehensive, covers 2005+ play-by-play | Good -- reliable across all 20 seasons |
| XGBoost as primary classifier | Strong tabular performance, interpretable feature importance | Good -- 62.89% val accuracy, TreeSHAP works well |
| experiments.jsonl + MLflow dual logging | Portable flat file for scripting + visual UI for comparison | Good -- JSONL parsed directly by API for experiment scoreboard |
| Semi-automated pipeline | Automatic fetch/retrain but manual approval prevents bad models from auto-deploying | Good -- approval gate verified in Phase 6 |
| Temporal train/val/test split | Prevents data leakage across seasons, mirrors real-world deployment | Good -- 2024 holdout untouched for future evaluation |
| Per-season rolling reset | NFL rosters change between seasons; expanding window resets per team/season | Good -- prevents cross-season contamination |
| Full 17-feature set | All ablation experiments degraded accuracy | Good -- near-optimal; no feature pruning needed |
| Lower learning rate + early stopping | Biggest improvement lever for generalization (Exp 5) | Good -- +1.68pp over baseline config |
| Caddy as edge proxy | Static file serving + API reverse proxy + automatic HTTPS | Good -- simple config, same-origin relative URLs |
| Models volume read-only for API | Worker writes, API reads -- prevents API from corrupting model artifacts | Good -- clean separation of concerns |

---
*Last updated: 2026-03-18 after v1.0 milestone*
