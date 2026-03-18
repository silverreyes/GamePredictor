---
phase: 06-pipeline-and-deployment
plan: 01
subsystem: pipeline
tags: [apscheduler, cron, pipeline, orchestration, mlflow, ingestion]

# Dependency graph
requires:
  - phase: 01-data-foundation
    provides: data ingestion functions (loaders, transforms, upsert)
  - phase: 02-feature-engineering
    provides: build_game_features, store_game_features
  - phase: 03-model-training-and-autoresearch
    provides: training pipeline (train_and_evaluate, should_keep, save_best_model)
  - phase: 04-prediction-api
    provides: predict pipeline (generate_predictions, detect_current_week, load_best_model)
provides:
  - pipeline/refresh.py with 4-step orchestration (ingest, features, retrain, predict)
  - pipeline/worker.py with APScheduler CronTrigger for Tuesday 6 AM UTC
  - Mixed failure modes (steps 1-2 fatal, step 3 non-fatal)
  - Offseason guard and staleness check in ingestion
  - Cache invalidation before re-downloading season data
affects: [06-pipeline-and-deployment]

# Tech tracking
tech-stack:
  added: [APScheduler 3.11]
  patterns: [four-step pipeline with mixed failure modes, lazy imports in pipeline functions, cache invalidation before re-download]

key-files:
  created: [pipeline/__init__.py, pipeline/refresh.py, pipeline/worker.py, tests/test_pipeline.py]
  modified: [pyproject.toml]

key-decisions:
  - "Lazy imports in pipeline step functions to avoid circular imports and heavy module loading"
  - "Cache invalidation deletes parquet files before re-downloading -- acceptable risk since DB is source of truth"
  - "Step 3 (retrain) non-fatal: failure logged but pipeline continues to step 4 (predictions)"
  - "MLflow tracking URI configurable via MLFLOW_TRACKING_URI env var for Docker; falls back to file:./mlruns"

patterns-established:
  - "Pipeline steps are standalone functions accepting engine + config, callable independently"
  - "run_pipeline reads all config from env vars with sensible defaults"
  - "Worker uses module-level BlockingScheduler with SIGTERM handler for Docker graceful shutdown"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03]

# Metrics
duration: 7min
completed: 2026-03-18
---

# Phase 6 Plan 1: Pipeline Refresh Summary

**Four-step weekly pipeline (ingest, features, retrain, predict) with APScheduler worker, mixed failure modes, and offseason guard**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-18T04:11:28Z
- **Completed:** 2026-03-18T04:18:32Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created pipeline/refresh.py with 4 step functions + run_pipeline orchestrator with correct failure modes
- Created pipeline/worker.py with APScheduler BlockingScheduler using Tuesday 6 AM UTC CronTrigger
- 10 unit tests covering step execution, failure modes, offseason guard, cache invalidation, staleness check, worker config, and MLflow URI override
- APScheduler>=3.10,<4.0 added to pyproject.toml

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pipeline package with four-step refresh and worker entrypoint** - `d06e697` (feat)
2. **Task 2: Unit tests for pipeline steps and failure modes** - `4057fd8` (test)

## Files Created/Modified
- `pipeline/__init__.py` - Package init (empty)
- `pipeline/refresh.py` - Four-step pipeline orchestration with mixed failure modes
- `pipeline/worker.py` - APScheduler entrypoint with SIGTERM handler and configurable cron hour
- `tests/test_pipeline.py` - 10 unit tests for all pipeline steps and failure modes
- `pyproject.toml` - Added APScheduler dependency

## Decisions Made
- Lazy imports in pipeline step functions to avoid circular imports and heavy module loading at import time
- Cache invalidation deletes parquet files before re-downloading; acceptable because DB is source of truth and nfl-data-py has retry logic
- MLflow tracking URI configurable via MLFLOW_TRACKING_URI env var for Docker deployment; defaults to file:./mlruns for local development
- Step 3 (retrain_and_stage) is non-fatal: failure is logged as warning and pipeline continues to step 4 (generate_current_predictions)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- APScheduler not installable via `pip install` due to shell PATH; resolved using `python -m pip install apscheduler`
- Test patches for lazy imports (functions imported inside function bodies) required patching at source module rather than pipeline.refresh module level
- CronTrigger field index for hour was off by one in initial test (index 5, not 2)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Pipeline module complete and ready for Docker containerization in plan 02
- Worker entrypoint callable via `python -m pipeline.worker` in container
- All pipeline functions importable and tested in isolation

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (d06e697, 4057fd8) verified in git log.

---
*Phase: 06-pipeline-and-deployment*
*Completed: 2026-03-18*
