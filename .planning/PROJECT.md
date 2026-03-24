# NFL Game Predictor

## What This Is

An end-to-end NFL game outcome prediction system. Ingests 20 seasons of play-by-play data, engineers leakage-safe features, and runs two models: an XGBoost classifier (Pick-Em, 63.7% on 2024) and a Ridge regression spread model (MAE 10.68). Predictions are served via FastAPI and displayed in a React dashboard with weekly picks, season accuracy tracking, experiment comparison, and prediction history. Automated weekly refresh pipeline deployed via Docker Compose at nostradamus.silverreyes.net.

## Core Value

Pre-game win/loss and point spread predictions that beat trivial baselines, with a polished dashboard for tracking accuracy over time.

## Requirements

### Validated

- Ingest and store 20 seasons of NFL data in PostgreSQL with normalized team abbreviations -- v1.0
- Engineer leakage-safe game-level features with automated temporal validation -- v1.0
- XGBoost classifier via autoresearch experiment loop, beating both trivial baselines -- v1.0 (62.89% vs 55.51% always-home, 58.20% better-record)
- FastAPI prediction and model management endpoints with token-protected hot-reload -- v1.0
- React dashboard with 4 views: picks, accuracy, experiments, history -- v1.0
- Docker Compose deployment with automated weekly refresh and human approval gate -- v1.0
- Ridge regression spread model predicting margin of victory (MAE 10.68, 60.2% derived winner accuracy) -- v1.1
- Spread predictions table and API endpoint `/api/spreads/{season}/{week}` -- v1.1
- Dashboard showing spread predictions on PickCards with sportsbook sign convention and color-coded error -- v1.1
- Spread model performance tracking: MAE, derived win accuracy, Pick-Em vs Spread comparison -- v1.1
- Weekly pipeline spread inference (non-fatal step 5) with historical seed script -- v1.1
- Spread experiment logging to spread_experiments.jsonl (append-only) -- v1.1
- Season selector on Accuracy page with info tooltips on all cards -- v1.1

### Active

(No active requirements -- awaiting next milestone)

### Out of Scope

- Live in-game predictions -- pre-game only, no real-time scoring data
- Vegas spread/over-under ingestion -- model generates its own spreads
- Player-level injury/availability data -- team-level aggregate features only
- Mobile app -- web dashboard only
- User accounts / authentication -- single-user or open read access
- Neural network models -- gradient boosting outperforms deep learning on ~5K structured rows
- Betting advice framing -- predictions only, no wagering guidance
- Spread model auto-retraining in pipeline -- inference only, manual retrain via train_spread.py

## Context

Shipped v1.1 with ~15,000 LOC (Python + TypeScript + SQL).
Tech stack: Python 3.11, PostgreSQL, nflreadpy, pandas, XGBoost, scikit-learn (Ridge), FastAPI, React + Vite + Tailwind v4 + shadcn/ui, Docker Compose, APScheduler.
Two models: Pick-Em classifier (Exp 5, XGBoost) and Spread model (Exp 1, Ridge regression).
Dashboard branding uses "Pick-Em" (hyphenated) and sportsbook sign convention for spreads.
Production: nostradamus.silverreyes.net via Caddy reverse proxy with automatic HTTPS.

## Constraints

- **Data leakage**: All rolling features must use only data prior to the game being predicted -- strictly enforced via shift(1) + 6 automated leakage tests
- **Temporal split**: Train 2005-2022, validate 2023, holdout 2024 -- no shuffling across time boundaries
- **Stack**: Python 3.11, PostgreSQL, nflreadpy, pandas, XGBoost, scikit-learn, FastAPI, React, Docker Compose
- **Benchmark**: Must beat always-home and better-record baselines on the 2023 validation season
- **Feature schema**: One row per game (home team perspective)
- **Team normalization**: Applied at ingestion via TEAM_ABBREV_MAP constant in data/sources.py
- **Deployment**: Docker Compose on Linux VPS -- services: postgres, api, worker, caddy

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| nflreadpy as data source | Free, comprehensive, covers 2005+ play-by-play | Good |
| XGBoost as primary classifier | Strong tabular performance, interpretable feature importance | Good -- 62.89% val accuracy |
| experiments.jsonl logging | Portable flat file parsed directly by API for experiment scoreboard | Good |
| Semi-automated pipeline | Automatic fetch/retrain but manual approval prevents bad models | Good |
| Temporal train/val/test split | Prevents data leakage across seasons | Good |
| Per-season rolling reset | NFL rosters change between seasons | Good |
| Full 17-feature set | All ablation experiments degraded accuracy | Good |
| Lower learning rate + early stopping | Biggest improvement lever (Exp 5) | Good -- +1.68pp |
| Caddy as edge proxy | Static files + API reverse proxy + automatic HTTPS | Good |
| Models volume read-only for API | Worker writes, API reads | Good |
| Ridge regression for spreads | Simpler than XGBoost, comparable MAE after 5-experiment sweep | Good -- shipped Exp 1 baseline |
| Inference-only spread pipeline | Keeps weekly pipeline simple | Good -- non-fatal step 5 |
| Integrated dashboard (not separate page) | Users see both predictions in context | Good -- unified PickCard view |
| Sportsbook sign convention | Users expect negative=favorite, positive=underdog | Good -- corrected mid-v1.1 |
| "Pick-Em" branding (hyphenated) | Avoids apostrophe encoding issues, clear to visitors | Good |
| Over/under deferred to v1.2 | Keeps v1.1 scope focused | -- Pending |

---
*Last updated: 2026-03-24 after v1.1 milestone*
