---
phase: 08-database-and-api-integration
plan: 02
subsystem: api
tags: [fastapi, spread-predictions, lifespan, model-reload, xgbregressor, tdd]

# Dependency graph
requires:
  - phase: 08-database-and-api-integration
    plan: 01
    provides: spread prediction functions (load/select/generate), Pydantic schemas, config settings
provides:
  - GET /api/predictions/spreads/week/{season}/{week} endpoint with 503 degradation
  - Lifespan spread model loading with graceful FileNotFoundError handling
  - Extended GET /api/model/info with nested spread_model metadata
  - Extended POST /api/model/reload with spread model hot-swap
  - 7 new spread API tests plus updated fixtures for all existing tests
affects: [09-frontend-dashboard (frontend will call spread endpoints)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spread endpoint mirrors classifier predictions pattern (pd.read_sql, response construction)"
    - "Graceful degradation: spread model failures set state to None, API continues serving classifier"
    - "no_spread_client fixture pattern for testing degradation behavior"

key-files:
  created:
    - api/routes/spreads.py
    - tests/api/test_spreads.py
  modified:
    - api/main.py
    - api/routes/model.py
    - api/deps.py
    - tests/api/conftest.py
    - tests/api/test_model.py

key-decisions:
  - "Spread endpoint uses path params {season}/{week} rather than query params, matching URL hierarchy convention"
  - "Spread reload generates predictions only when both current week and spread info are available"

patterns-established:
  - "Graceful degradation pattern: try/except FileNotFoundError -> set state to None in lifespan"
  - "no_spread_client fixture for testing API behavior when optional models are missing"

requirements-completed: [API-02, API-03, API-04]

# Metrics
duration: 11min
completed: 2026-03-23
---

# Phase 8 Plan 02: Spread API Wiring Summary

**FastAPI spread predictions endpoint, lifespan model loading with graceful degradation, model info/reload extensions, and 22 passing API tests**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-23T19:45:45Z
- **Completed:** 2026-03-23T19:56:52Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- GET /api/predictions/spreads/week/{season}/{week} returns spread predictions or 503 when model unavailable
- Lifespan loads spread model alongside classifier with graceful FileNotFoundError degradation
- GET /api/model/info includes nested spread_model object (mae, rmse, derived_win_accuracy, training_date, experiment_id)
- POST /api/model/reload hot-swaps both classifier and spread model, returning spread metadata in response
- 22 total API tests pass (15 existing + 7 new spread tests) via TDD RED-GREEN cycle

## Task Commits

Each task was committed atomically:

1. **Task 1: Create spreads route, update lifespan/model routes, update deps docstring** - `89e1888` (feat)
2. **Task 2: Add failing tests for spread API endpoints (TDD RED)** - `01cc5cf` (test)
3. **Task 2: Update test fixtures and pass spread API tests (TDD GREEN)** - `990c127` (feat)

_Note: Task 2 used TDD cycle with separate RED and GREEN commits._

## Files Created/Modified
- `api/routes/spreads.py` - New spread predictions endpoint with 503 degradation when model missing
- `api/main.py` - Extended lifespan with spread model loading, added spreads router
- `api/routes/model.py` - Extended model_info with SpreadModelInfo, reload with spread model hot-swap
- `api/deps.py` - Updated docstring with spread_model and spread_model_info state keys
- `tests/api/conftest.py` - Added SAMPLE_SPREAD_EXPERIMENT, SAMPLE_SPREAD_PREDICTIONS, mock_spread_model, no_spread_client fixtures
- `tests/api/test_spreads.py` - 4 tests: spread week, prediction fields, 503 no model, startup without spread
- `tests/api/test_model.py` - 3 new tests: model info spread, spread null, reload spread fields

## Decisions Made
- Spread endpoint uses path params {season}/{week} rather than query params, matching URL hierarchy convention for the resource structure
- Spread reload generates predictions only when both current week and spread info are available, avoiding partial state

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All spread API endpoints complete and tested
- Phase 8 (Database and API Integration) fully complete
- Ready for Phase 9 (Frontend Dashboard) which will consume these endpoints
- Spread predictions accessible at GET /api/predictions/spreads/week/{season}/{week}
- Model info at GET /api/model/info includes spread metadata

## Self-Check: PASSED

All 7 files verified present. All 3 commits verified in git log.

---
*Phase: 08-database-and-api-integration*
*Completed: 2026-03-23*
