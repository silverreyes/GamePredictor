---
phase: 03-model-training-and-autoresearch
plan: 01
subsystem: model
tags: [xgboost, mlflow, shap, scikit-learn, baselines]

# Dependency graph
requires:
  - phase: 02-feature-engineering
    provides: "Feature matrix with rolling stats and home_win target via build_game_features()"
provides:
  - "models/ package with baselines.py (always_home_baseline, better_record_baseline, compute_baselines)"
  - "Prior-season tiebreaker logic for better-record baseline"
  - "ML dependencies installed (xgboost, mlflow, shap, scikit-learn)"
  - "Test scaffolds for models/ (conftest with sample_feature_df fixture)"
affects: [03-02-PLAN, 03-03-PLAN]

# Tech tracking
tech-stack:
  added: [xgboost 3.2.0, mlflow 3.10.1, shap 0.51.0, scikit-learn 1.8.0]
  patterns: [baseline-before-experiment, prior-season-tiebreaker]

key-files:
  created: [models/__init__.py, models/baselines.py, tests/models/__init__.py, tests/models/conftest.py, tests/models/test_baselines.py]
  modified: [pyproject.toml]

key-decisions:
  - "Upgraded pandas from 1.5.3 to 2.3.3 for numpy 2.x compatibility (numpy 2.4.3 required by ML deps)"
  - "Prior-season lookup uses home perspective first, fills from away perspective only if not already set"

patterns-established:
  - "Baselines module is read-only during autoresearch: only train.py is modified"
  - "Both baselines exclude ties; better-record additionally excludes NaN-record games with separate game counts"

requirements-completed: [MODL-03]

# Metrics
duration: 7min
completed: 2026-03-17
---

# Phase 3 Plan 01: ML Dependencies and Baselines Summary

**Baseline computation module with prior-season tiebreaker and 10 unit tests, plus XGBoost/MLflow/SHAP/scikit-learn dependencies**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-17T00:52:27Z
- **Completed:** 2026-03-17T00:59:14Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created models/ package with baselines.py implementing always_home_baseline, better_record_baseline, and compute_baselines
- Prior-season tiebreaker for better-record baseline uses final rolling_win from previous season, with home-team fallback only when no prior data exists
- Added xgboost, mlflow, shap, scikit-learn to project dependencies
- 10 unit tests covering all baseline logic including tied-record tiebreaker and NaN exclusion

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ML dependencies and create models package with baselines module** - `87e5a14` (feat)
2. **Task 2: Create test scaffolds and baseline unit tests** - `1f4410a` (test)

## Files Created/Modified
- `pyproject.toml` - Added xgboost, mlflow, shap, scikit-learn dependencies
- `models/__init__.py` - Empty package init for models module
- `models/baselines.py` - Baseline computation with _build_prior_season_records helper and three public functions
- `tests/models/__init__.py` - Empty package init for model tests
- `tests/models/conftest.py` - Synthetic feature DataFrame fixture (20 rows across 2 seasons)
- `tests/models/test_baselines.py` - 10 unit tests for all baseline functions

## Decisions Made
- Upgraded pandas from 1.5.3 to 2.3.3 for numpy 2.x compatibility (numpy 2.4.3 pulled in by ML deps broke pandas 1.5.3 binary interface)
- Prior-season lookup iterates home perspective first, fills gaps from away perspective (values should be consistent since rolling_win is per-team)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Upgraded pandas for numpy 2.x binary compatibility**
- **Found during:** Task 1 (dependency installation)
- **Issue:** Installing xgboost/mlflow pulled numpy 2.4.3, which broke pandas 1.5.3 (ValueError: numpy.dtype size changed)
- **Fix:** Upgraded pandas to 2.3.3 (compatible with numpy 2.x and mlflow's pandas<3 constraint)
- **Files modified:** None (runtime dependency, not in source)
- **Verification:** All imports succeed, full test suite passes (61 passed, 3 skipped)
- **Committed in:** Part of Task 1 verification

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for ML dependencies to coexist with existing pandas. No scope creep.

## Issues Encountered
- nfl-data-py 0.3.3 has strict numpy<2.0 and pandas<2.0 pins that conflict with ML dependencies. The package still works at runtime despite pip's warning because nfl-data-py doesn't use numpy/pandas C extensions that changed. This is a pre-existing constraint that does not affect functionality.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- models/baselines.py is ready to be called from compute_baselines(df, 2023) in the training pipeline
- Baseline accuracies will be stored in program.md as fixed reference numbers
- Test scaffolds (conftest.py, __init__.py) are ready for test_train.py and test_logging.py in subsequent plans

## Self-Check: PASSED

All 5 created files verified on disk. Both task commits (87e5a14, 1f4410a) verified in git log.

---
*Phase: 03-model-training-and-autoresearch*
*Completed: 2026-03-17*
