---
phase: 02-feature-engineering
plan: 01
subsystem: features
tags: [pandas, rolling, shift, epa, nfl, feature-engineering, pytest]

# Dependency graph
requires:
  - phase: 01-data-foundation
    provides: "Cached PBP/schedule parquet files, data loaders, team normalization, DB schema"
provides:
  - "features/definitions.py with ROLLING_FEATURES, SITUATIONAL_FEATURES, FORBIDDEN_FEATURES constants"
  - "features/build.py with 5-function pipeline: aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features, store_game_features"
  - "game_features DDL in sql/init.sql"
  - "Synthetic test fixtures for feature pipeline testing"
  - "18 unit tests verifying feature correctness"
affects: [03-model-training, 02-02-leakage-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-stage feature pipeline: aggregate -> roll -> pivot"
    - "shift(1).expanding().mean() grouped by (team, season) for all rolling features"
    - "Synthetic PBP/schedule fixtures for deterministic testing"

key-files:
  created:
    - features/__init__.py
    - features/definitions.py
    - features/build.py
    - features/tests/__init__.py
    - features/tests/conftest.py
    - features/tests/test_features.py
  modified:
    - sql/init.sql
    - pyproject.toml

key-decisions:
  - "Per-season rolling reset via groupby(['team', 'season']) -- NFL rosters change between seasons"
  - "Expanding window (not fixed-size) as primary rolling approach"
  - "Ties counted as 0.5 in win rate computation"
  - "EPA computed from pass/run plays only (EPA_PLAY_TYPES filter)"
  - "Turnover differential via self-merge on opponent turnovers committed"

patterns-established:
  - "Feature definitions locked in definitions.py -- never modify during autoresearch"
  - "Build pipeline locked in build.py -- never modify during autoresearch"
  - "build_game_features() accepts pre-loaded data for testing or loads from cache for production"
  - "Synthetic fixtures with known values for deterministic feature validation"

requirements-completed: [FEAT-01, FEAT-02, FEAT-03, FEAT-04]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 02 Plan 01: Feature Pipeline Summary

**Rolling EPA/play, point diff, turnover diff, and win rate features with shift(1) leakage prevention, computed per-team per-season from cached PBP/schedule data and pivoted to home-perspective rows**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-16T21:22:32Z
- **Completed:** 2026-03-16T21:28:38Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Feature definitions module with 7 rolling features, 5 situational features, forbidden features list, and EPA play type filter
- Complete 5-function build pipeline: aggregate game stats from PBP, compute rolling features with shift(1), pivot to home perspective, orchestrate full pipeline, store to PostgreSQL
- game_features table DDL with indexes appended to sql/init.sql
- 18 unit tests covering aggregation, rolling, home perspective, and end-to-end pipeline correctness

## Task Commits

Each task was committed atomically:

1. **Task 1: Feature definitions, DB schema, test scaffolds** - `435f76e` (feat)
2. **Task 2: Feature build pipeline** - `ba9fbf4` (feat, TDD)
3. **Task 3: Feature correctness unit tests** - `6be4315` (test, TDD)

_TDD tasks included RED/GREEN cycle: test(02-01) at 961c1ac, then feat at ba9fbf4, cleanup at 193fc80_

## Files Created/Modified
- `features/__init__.py` - Package init (empty)
- `features/definitions.py` - ROLLING_FEATURES, SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES, EPA_PLAY_TYPES constants
- `features/build.py` - 5-function pipeline: aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features, store_game_features
- `features/tests/__init__.py` - Test package init (empty)
- `features/tests/conftest.py` - 4 synthetic fixtures: synthetic_schedule, synthetic_pbp, synthetic_two_season_schedule, synthetic_two_season_pbp
- `features/tests/test_features.py` - 18 unit tests across 4 test classes
- `sql/init.sql` - Added game_features table DDL with 2 indexes
- `pyproject.toml` - Added "features/tests" to testpaths

## Decisions Made
- Per-season rolling reset via groupby(['team', 'season']) -- NFL rosters change dramatically between seasons, making cross-season rolling misleading
- Expanding window (not fixed-size) as primary rolling approach -- captures full season history; fixed-window variants can be added in Phase 3 experiments via models/train.py
- Ties counted as 0.5 in win rate -- standard NFL analytics convention for rare tie games
- EPA computed from pass/run plays only -- other play types (kickoff, punt) have EPA but are not meaningful for team quality
- Turnover differential via self-merge on opponent turnovers committed -- PBP records turnovers from offense perspective, so differential requires pairing both teams

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Feature pipeline is importable and tested with synthetic data
- Leakage tests (features/tests/test_leakage.py) still need to be created in plan 02-02
- Features/build.py is now LOCKED for Phase 3 autoresearch per CLAUDE.md
- All Phase 1 tests (45 total) still pass alongside new feature tests

## Self-Check: PASSED

All 8 created/modified files verified on disk. All 3 task commits (435f76e, ba9fbf4, 6be4315) verified in git history.

---
*Phase: 02-feature-engineering*
*Completed: 2026-03-16*
