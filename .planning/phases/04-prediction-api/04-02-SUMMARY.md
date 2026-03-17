---
phase: 04-prediction-api
plan: 02
subsystem: api
tags: [fastapi, cors, dependency-injection, httpx, testclient, pydantic]

# Dependency graph
requires:
  - phase: 04-prediction-api
    provides: "models/predict.py pipeline, api/config.py settings, api/schemas.py response models"
  - phase: 03-model-training-and-autoresearch
    provides: "Trained XGBoost model, experiments.jsonl log"
  - phase: 01-data-foundation
    provides: "PostgreSQL schema, data/db.py engine access"
provides:
  - "FastAPI application with lifespan model loading, CORS, and 6 endpoints"
  - "api/deps.py dependency injection for testable app state"
  - "api/routes/ with predictions, model, experiments, health routers"
  - "Comprehensive test suite (23 tests) covering all endpoints and predict.py"
affects: [05-dashboard, 06-pipeline-and-deployment]

# Tech tracking
tech-stack:
  added: [fastapi, uvicorn, httpx]
  patterns: ["Lifespan context manager for model loading", "Dependency injection via get_app_state", "TestClient with patched lifespan for isolated API tests", "Token-protected reload with X-Reload-Token header"]

key-files:
  created: [api/main.py, api/deps.py, api/routes/__init__.py, api/routes/predictions.py, api/routes/model.py, api/routes/experiments.py, api/routes/health.py, tests/api/__init__.py, tests/api/conftest.py, tests/api/test_health.py, tests/api/test_experiments.py, tests/api/test_predictions.py, tests/api/test_model.py, tests/models/test_predict.py]
  modified: [pyproject.toml]

key-decisions:
  - "Patch lifespan dependencies (get_engine, load_best_model, get_best_experiment) in tests rather than bypassing lifespan entirely"
  - "Separate offseason_client fixture for isolated offseason behavior testing"
  - "FastAPI and uvicorn added to main dependencies (not dev), httpx added to dev dependencies"

patterns-established:
  - "API test pattern: patch lifespan + route-level dependencies, use TestClient context manager"
  - "All routes under /api/ prefix for clean reverse proxy config"
  - "Predictions read from DB via pd.read_sql with parameterized queries"

requirements-completed: [API-01, API-02, API-03, API-04]

# Metrics
duration: 8min
completed: 2026-03-17
---

# Phase 4 Plan 2: FastAPI Endpoints and Test Suite Summary

**Complete FastAPI prediction API with 6 endpoints (predictions week/current/history, model info/reload, experiments, health) and 23-test suite using mocked dependencies**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-17T05:47:28Z
- **Completed:** 2026-03-17T05:55:28Z
- **Tasks:** 2 (Task 3 is checkpoint:human-verify)
- **Files modified:** 15

## Accomplishments
- Implemented all 6 FastAPI endpoints with dependency injection, CORS middleware, and lifespan model loading
- Built comprehensive test suite (23 tests) covering all endpoints, offseason behavior, token auth, and predict.py logic
- Verified prefix flip correctness in _get_team_rolling_features (critical for prediction accuracy)
- Full test suite (102 tests) passes with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: FastAPI application and all route implementations** - `e6413e3` (feat)
2. **Task 2: Comprehensive test suite for all endpoints and predict.py** - `79c311f` (test)

## Files Created/Modified
- `pyproject.toml` - Added fastapi, uvicorn to dependencies; httpx to dev dependencies
- `api/deps.py` - Dependency injection with app_state dict and get_app_state()
- `api/main.py` - FastAPI app with lifespan model loading, CORS, router includes
- `api/routes/__init__.py` - Package marker
- `api/routes/predictions.py` - GET /api/predictions/week/{week}, /current, /history endpoints
- `api/routes/model.py` - GET /api/model/info and POST /api/model/reload endpoints
- `api/routes/experiments.py` - GET /api/experiments endpoint reading experiments.jsonl
- `api/routes/health.py` - GET /api/health endpoint
- `tests/api/__init__.py` - Test package marker
- `tests/api/conftest.py` - Test fixtures with mocked model, DB, and experiments file
- `tests/api/test_health.py` - Health endpoint test
- `tests/api/test_experiments.py` - Experiments endpoint tests (list, structure)
- `tests/api/test_predictions.py` - Prediction endpoint tests (week, default season, current, offseason, history, summary, filters)
- `tests/api/test_model.py` - Model endpoint tests (info, baselines, reload, auth, bad token)
- `tests/models/test_predict.py` - Predict.py unit tests (best experiment, model loading, confidence, rolling features, path normalization)

## Decisions Made
- Added fastapi and uvicorn to main dependencies (not dev-only) since they are runtime requirements for the API server
- Test fixtures patch both lifespan-level and route-level dependencies to prevent real DB/model access during tests
- Created separate offseason_client fixture rather than parameterizing the main client fixture, for clearer test intent

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test fixture to patch lifespan dependencies**
- **Found during:** Task 2 (test creation)
- **Issue:** Plan's conftest populated app_state directly but TestClient runs lifespan which overwrote the state with real get_engine/load_best_model calls
- **Fix:** Added patches for api.main.get_engine, api.main.load_best_model, api.main.get_best_experiment, and api.main.settings to prevent lifespan from calling real functions
- **Files modified:** tests/api/conftest.py
- **Verification:** All 23 tests pass with mocked dependencies
- **Committed in:** 79c311f (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for test isolation. No scope creep.

## Issues Encountered
- httpx initial install via `pip install httpx -q` silently failed; resolved by using `python -m pip install httpx`

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All API endpoints implemented and tested with mocked dependencies
- Ready for Phase 5 (React dashboard) to consume the API
- Server can be started with `uvicorn api.main:app --reload` when PostgreSQL and model artifacts are available
- Phase 6 will add Docker deployment and pipeline orchestration

## Self-Check: PASSED

All 15 created/modified files verified on disk. Both task commits (e6413e3, 79c311f) verified in git log.

---
*Phase: 04-prediction-api*
*Completed: 2026-03-17*
