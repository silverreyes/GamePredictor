---
phase: 08-database-and-api-integration
plan: 01
subsystem: database, api, models
tags: [xgboost, xgbregressor, postgresql, pydantic, spread-predictions, ddl]

# Dependency graph
requires:
  - phase: 07-spread-model-training
    provides: spread_experiments.jsonl, best_spread_model.json artifacts, XGBRegressor training pipeline
provides:
  - spread_predictions table DDL with indexes in init.sql
  - load_best_spread_model(), get_best_spread_experiment(), generate_spread_predictions() in predict.py
  - SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo Pydantic schemas
  - SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH config settings
  - 9 unit tests covering spread prediction functions and winner derivation logic
affects: [08-02-PLAN (API wiring consumes all artifacts from this plan)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spread prediction functions mirror classifier patterns (load, experiment select, generate)"
    - "XGBRegressor model.predict() for spread inference (not predict_proba)"
    - "MAE-based experiment selection (lowest wins, opposite of classifier accuracy)"
    - "Spread-sign winner derivation: predicted_spread >= 0 -> home_team wins"

key-files:
  created: []
  modified:
    - sql/init.sql
    - models/predict.py
    - api/schemas.py
    - api/config.py
    - tests/models/test_predict.py

key-decisions:
  - "Mirrored existing classifier function patterns for consistency"
  - "Home-team convention for zero spread (predicted_spread == 0.0 -> home wins)"

patterns-established:
  - "Spread functions follow same load/select/generate pattern as classifier"
  - "MAE selection uses < comparison (lower is better) vs classifier > (higher is better)"

requirements-completed: [API-01]

# Metrics
duration: 5min
completed: 2026-03-23
---

# Phase 8 Plan 01: Spread Prediction Foundation Summary

**Spread prediction DDL, XGBRegressor pipeline functions (load/select/generate), Pydantic schemas, and config settings with 9 passing TDD tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-23T19:37:41Z
- **Completed:** 2026-03-23T19:42:20Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- spread_predictions table DDL appended to init.sql with game_id PK, predicted_spread, predicted_winner, and season/week indexes
- Three spread functions in predict.py: load_best_spread_model (XGBRegressor), get_best_spread_experiment (lowest MAE), generate_spread_predictions (spread-sign winner)
- SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo schemas plus ModelInfoResponse.spread_model and ReloadResponse spread fields
- SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH config settings with environment variable overrides
- 17 total tests pass (8 existing + 9 new spread tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add spread_predictions DDL, config settings, and Pydantic schemas** - `150bda9` (feat)
2. **Task 2: Add spread prediction functions (TDD RED)** - `140b5d3` (test)
3. **Task 2: Add spread prediction functions (TDD GREEN)** - `e9169b9` (feat)

_Note: Task 2 used TDD cycle with separate RED and GREEN commits._

## Files Created/Modified
- `sql/init.sql` - Added spread_predictions table DDL with predicted_spread, predicted_winner columns and indexes
- `api/config.py` - Added SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH settings
- `api/schemas.py` - Added SpreadPredictionResponse, SpreadWeekResponse, SpreadModelInfo; extended ModelInfoResponse and ReloadResponse
- `models/predict.py` - Added load_best_spread_model, get_best_spread_experiment, generate_spread_predictions functions
- `tests/models/test_predict.py` - Added 9 spread tests: model load/missing, experiment selection/lowest MAE/no file/path normalization, winner home/away/zero

## Decisions Made
- Mirrored existing classifier function patterns for consistency (same structure, different model type and metric)
- Home-team convention for zero spread: predicted_spread == 0.0 means home team is predicted winner (consistent with home-advantage convention)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All data layer artifacts ready for Plan 02 (API wiring)
- predict.py exports all three spread functions Plan 02 needs for lifespan loading and route handlers
- Pydantic schemas ready for FastAPI response models
- Config settings ready for environment-based spread model path configuration

## Self-Check: PASSED

All 6 files verified present. All 3 commits verified in git log.

---
*Phase: 08-database-and-api-integration*
*Completed: 2026-03-23*
