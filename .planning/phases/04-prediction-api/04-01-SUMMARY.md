---
phase: 04-prediction-api
plan: 01
subsystem: api
tags: [fastapi, pydantic, xgboost, postgresql, predictions]

# Dependency graph
requires:
  - phase: 03-model-training-and-autoresearch
    provides: "Trained XGBoost model (best_model.json), experiments.jsonl log"
  - phase: 02-feature-engineering
    provides: "build_game_features() pipeline, rolling feature definitions"
  - phase: 01-data-foundation
    provides: "PostgreSQL schema (schedules table), data/db.py engine access"
provides:
  - "predictions table DDL in sql/init.sql"
  - "models/predict.py with load_best_model, get_best_experiment, detect_current_week, generate_predictions"
  - "_get_team_rolling_features helper for extracting team stats from feature matrix"
  - "api/config.py with Settings class and get_confidence_tier function"
  - "api/schemas.py with Pydantic v2 response models for all API endpoints"
affects: [04-02-PLAN, 05-dashboard, 06-pipeline-and-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Prediction pipeline separated from API layer", "Confidence = max(home_prob, 1-home_prob)", "Configurable confidence tier thresholds via environment", "PostgreSQL upsert via on_conflict_do_update"]

key-files:
  created: [models/predict.py, api/__init__.py, api/config.py, api/schemas.py]
  modified: [sql/init.sql]

key-decisions:
  - "Confidence tier thresholds default to 0.65 (high) and 0.55 (medium), configurable via env vars"
  - "predictions table uses game_id as sole PK (no model versioning per CONTEXT.md)"
  - "model_path backslash normalization in get_best_experiment to handle Windows paths on Linux"
  - "_get_team_rolling_features extracts unprefixed rolling stats then caller re-prefixes for home/away slot"

patterns-established:
  - "Prediction logic in models/predict.py, not in api/ -- keeps prediction code with model code"
  - "confidence_tier_fn passed as parameter to avoid circular api/ dependency"
  - "Pydantic v2 response models using Python 3.11+ union syntax (str | None)"

requirements-completed: [API-01, API-02, API-03, API-04]

# Metrics
duration: 3min
completed: 2026-03-17
---

# Phase 4 Plan 1: Prediction Pipeline and API Contracts Summary

**Prediction generation pipeline with team rolling feature extraction, PostgreSQL upsert, and Pydantic v2 response schemas for all API endpoints**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-17T05:40:44Z
- **Completed:** 2026-03-17T05:44:02Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created predictions table DDL with game_id PK, confidence tier, model_id audit column, and indexes
- Built models/predict.py with 4 exported functions (load_best_model, get_best_experiment, detect_current_week, generate_predictions) plus _get_team_rolling_features helper
- Established API contract layer with Pydantic v2 schemas for all 7 response types and configurable confidence tier thresholds

## Task Commits

Each task was committed atomically:

1. **Task 1: predictions table DDL and models/predict.py** - `be23bee` (feat)
2. **Task 2: API contract layer (config.py, schemas.py, __init__.py)** - `a3c7721` (feat)

## Files Created/Modified
- `sql/init.sql` - Added predictions table DDL and indexes
- `models/predict.py` - Prediction generation pipeline with 4 exported functions + helper
- `api/__init__.py` - Package marker
- `api/config.py` - Settings class with RELOAD_TOKEN, confidence thresholds, CORS origins
- `api/schemas.py` - All Pydantic v2 response models (PredictionResponse, WeekPredictionsResponse, PredictionHistoryResponse, ModelInfoResponse, ExperimentResponse, ReloadResponse, HealthResponse)

## Decisions Made
- Confidence tier thresholds default to 0.65/0.55, configurable via CONFIDENCE_HIGH/CONFIDENCE_MEDIUM env vars
- _get_team_rolling_features returns unprefixed keys (e.g., "rolling_off_epa_per_play") so caller re-prefixes for home/away context
- model_path normalized with .replace("\\", "/") in get_best_experiment to handle Windows backslashes in experiments.jsonl
- predictions table stores model_id (experiment_id) for debugging but this is not exposed in API response schemas

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- predictions table DDL ready to be applied to PostgreSQL
- models/predict.py ready for use by API endpoints (generate_predictions, detect_current_week, etc.)
- api/config.py and api/schemas.py provide the contract layer for 04-02-PLAN.md (FastAPI endpoints)
- All imports verified working

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (be23bee, a3c7721) verified in git log.

---
*Phase: 04-prediction-api*
*Completed: 2026-03-17*
