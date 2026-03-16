---
phase: 02-feature-engineering
verified: 2026-03-16T22:00:00Z
status: gaps_found
score: 11/12 must-haves verified
re_verification: false
gaps:
  - truth: "Feature matrix covers all seasons 2005-2024 with no gaps in coverage (store path works)"
    status: failed
    reason: "DDL column names in sql/init.sql do not match pipeline output column names. store_game_features() would produce SQL column-not-found errors at runtime."
    artifacts:
      - path: "sql/init.sql"
        issue: "DDL declares home_rolling_off_epa, home_rolling_def_epa, home_rolling_win_rate (and away equivalents) but pipeline outputs home_rolling_off_epa_per_play, home_rolling_def_epa_per_play, home_rolling_win. DDL also missing home/away_rolling_turnovers_committed and home/away_rolling_turnovers_forced (4 columns present in pipeline output but absent from DDL)."
    missing:
      - "Fix sql/init.sql game_features DDL: rename home_rolling_off_epa -> home_rolling_off_epa_per_play, home_rolling_def_epa -> home_rolling_def_epa_per_play, home_rolling_win_rate -> home_rolling_win (and away_ equivalents)"
      - "Add missing columns to DDL: home_rolling_turnovers_committed REAL, home_rolling_turnovers_forced REAL, away_rolling_turnovers_committed REAL, away_rolling_turnovers_forced REAL"
human_verification:
  - test: "Run python -m features --seasons 2023 against a live PostgreSQL instance"
    expected: "Features build and store without SQL errors; game_features table has 285 rows (2023 REG season games) with correct column values"
    why_human: "store_game_features() requires a live DB; the DDL mismatch gap above must be fixed first, then this test confirms end-to-end storage works"
---

# Phase 2: Feature Engineering Verification Report

**Phase Goal:** A game_features table exists with one row per game (home perspective) containing rolling offensive, defensive, and situational features computed with zero data leakage
**Verified:** 2026-03-16T22:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|---------|
| 1  | Rolling EPA/play features use only games prior to each row's game date | VERIFIED | `compute_rolling_features` applies `x.shift(1).expanding().mean()` grouped by `(team, season)`; `test_shift1_excludes_current_game` and `test_spike_only_visible_after_game` pass |
| 2  | Rolling point diff, turnover diff, and win rate use only prior-game data | VERIFIED | Same shift(1) mechanism; all 7 rolling features share the same loop in `compute_rolling_features` |
| 3  | Situational features (home_rest, away_rest, div_game, week) are populated for every row | VERIFIED | `build_home_perspective` joins these directly from schedule; confirmed present in pipeline output columns |
| 4  | Feature matrix has exactly one row per regular-season game from home team perspective | VERIFIED | `build_home_perspective` filters `game_type == "REG"` then merges home and away rolling; `test_home_perspective_one_row_per_game` passes |
| 5  | Week 1 games have NaN for all rolling features (no prior data within season) | VERIFIED | `test_week1_rolling_features_are_nan` passes (leakage test); shift(1) pushes first row out with no fill |
| 6  | No feature column contains result, home_score, or away_score directly | VERIFIED | `build_game_features` asserts FORBIDDEN_FEATURES not in output; `test_no_forbidden_features_in_output` passes |
| 7  | Leakage tests structurally verify no rolling feature for game G includes data from game G or later | VERIFIED | `features/tests/test_leakage.py` has 6 tests; all pass; CLAUDE.md gate is in place |
| 8  | Removing the last game of the season does not change any prior game's features | VERIFIED | `test_removing_future_game_does_not_change_past_features` passes |
| 9  | Rolling resets at season boundaries (per-season groupby) | VERIFIED | `groupby(["team", "season"])` in `compute_rolling_features`; `test_rolling_resets_at_season_boundary` passes |
| 10 | Feature pipeline is runnable via CLI command `python -m features` | VERIFIED | `features/__main__.py` exists with Click command; `--help` flag works |
| 11 | Pipeline in-memory computation is substantive and non-stub | VERIFIED | `features/build.py` is 286 lines with 5 complete functions; no TODO/placeholder/pass stubs found |
| 12 | sql/init.sql DDL column names match the pipeline output column names for store_game_features() | FAILED | DDL declares 6 wrong column names and is missing 4 columns that the pipeline outputs (see Gaps) |

**Score:** 11/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `features/definitions.py` | Feature column lists and rolling config | VERIFIED | Contains ROLLING_FEATURES (7 items), SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES, EPA_PLAY_TYPES; importable |
| `features/build.py` | Full feature pipeline | VERIFIED | 286 lines; exports all 5 functions: aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features, store_game_features; uses shift(1) + groupby(team, season) |
| `features/tests/test_features.py` | Unit tests for feature correctness | VERIFIED | 18 tests across 4 classes; all pass |
| `features/tests/conftest.py` | Synthetic test fixtures | VERIFIED | Contains synthetic_pbp, synthetic_schedule, synthetic_two_season_schedule, synthetic_two_season_pbp |
| `features/tests/test_leakage.py` | Leakage validation tests (FEAT-05 gate) | VERIFIED | 6 tests in TestLeakagePrevention class; all pass; CLAUDE.md mandated gate satisfied |
| `features/__main__.py` | CLI entry point for feature build | VERIFIED | Click command with --seasons and --store/--no-store; builds and reports feature matrix |
| `sql/init.sql` | game_features DDL | PARTIAL | CREATE TABLE IF NOT EXISTS game_features exists with indexes; however 6 column names are wrong and 4 columns are missing relative to pipeline output |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `features/build.py` | `features/definitions.py` | `from features.definitions import` | WIRED | Line 8: imports ROLLING_FEATURES, SITUATIONAL_FEATURES, TARGET, FORBIDDEN_FEATURES, EPA_PLAY_TYPES |
| `features/build.py` | `data/loaders.py` | `load_pbp_cached, load_schedules_cached` | WIRED | Lines 207-208 inside conditional load path; called when pbp/schedule args are None |
| `features/build.py` | `data/sources.py` | `TEAM_COLUMNS_PBP, TEAM_COLUMNS_SCHEDULE` | WIRED | Lines 209 imports constants; `play_type.isin(EPA_PLAY_TYPES)` filter at line 30 |
| `features/tests/test_features.py` | `features/build.py` | `from features.build import` | WIRED | Line 1 imports aggregate_game_stats, compute_rolling_features, build_home_perspective, build_game_features |
| `features/tests/test_leakage.py` | `features/build.py` | `from features.build import` | WIRED | Lines 9-13 import aggregate_game_stats, compute_rolling_features, build_game_features |
| `features/__main__.py` | `features/build.py` | `from features.build import build_game_features, store_game_features` | WIRED | Line 5 |
| `store_game_features()` | `sql/init.sql` DDL | column names must match at runtime | NOT_WIRED | DDL column names diverge from pipeline output: `home_rolling_off_epa` vs `home_rolling_off_epa_per_play`, `home_rolling_win_rate` vs `home_rolling_win`, etc. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| FEAT-01 | 02-01-PLAN.md | Rolling EPA/play features (offensive and defensive) using only data prior to each game — strictly no leakage | SATISFIED | compute_rolling_features uses shift(1).expanding().mean() grouped by (team, season); leakage tests pass |
| FEAT-02 | 02-01-PLAN.md | Rolling basic game stats (point differential, turnover differential, win rate) using only prior-game data | SATISFIED | All computed in same shift(1) loop; 18 unit tests verify correctness |
| FEAT-03 | 02-01-PLAN.md | Situational features per game: home/away flag, rest days, week of season, divisional game flag | SATISFIED | home_rest, away_rest, div_game, week all present in pipeline output; test_home_perspective_situational_features passes |
| FEAT-04 | 02-01-PLAN.md | Feature matrix structured as one row per game from the home team perspective | SATISFIED | build_home_perspective produces one row per REG game; test_home_perspective_one_row_per_game passes |
| FEAT-05 | 02-02-PLAN.md | Automated leakage validation tests run against the feature pipeline and must pass before any model training | SATISFIED | 6 tests in features/tests/test_leakage.py; all pass; CLAUDE.md mandated gate documented and active |

No orphaned requirements found. All 5 Phase 2 requirement IDs (FEAT-01 through FEAT-05) are claimed by plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `sql/init.sql` | 108-119 | DDL column names do not match pipeline output | Blocker | `store_game_features()` will fail at runtime with SQL column errors when attempting to insert the feature matrix into PostgreSQL |

No TODO/FIXME/PLACEHOLDER comments found in any feature file. No empty function bodies or stub return values found.

### Human Verification Required

#### 1. End-to-end DB storage after DDL fix

**Test:** After correcting sql/init.sql column names, run `python -m features --seasons 2023 --store` against a live PostgreSQL instance (Docker container from Phase 1).
**Expected:** Command completes without errors; `SELECT COUNT(*) FROM game_features WHERE season = 2023` returns ~285 rows; a sample SELECT shows rolling columns with NaN for week 1 games and plausible EPA values for later weeks.
**Why human:** store_game_features() requires a live DB. The DDL mismatch gap must be resolved first, then a human must confirm the DB write succeeds and the data looks sane.

### Gaps Summary

One gap blocks complete goal achievement: the DDL schema in `sql/init.sql` was written with abbreviated column names (`home_rolling_off_epa`, `home_rolling_win_rate`) that differ from what the pipeline actually produces (`home_rolling_off_epa_per_play`, `home_rolling_win`). Four additional columns present in the pipeline output (`home/away_rolling_turnovers_committed`, `home/away_rolling_turnovers_forced`) are entirely absent from the DDL.

The in-memory pipeline is fully correct — all 24 tests pass (18 correctness + 6 leakage). The phase goal is achieved for computational correctness and zero-leakage guarantees. However, the persistence layer (`store_game_features()` + `sql/init.sql`) is misaligned, meaning the feature data cannot be stored to PostgreSQL without SQL errors. Success criterion #4 ("Feature matrix covers all seasons 2005-2024") implies the data is actually accessible in the DB, which requires the storage path to work.

The fix is surgical: update 6 column names in the DDL and add 4 missing columns. No changes to `features/build.py` or `features/definitions.py` are needed (CLAUDE.md locks those files anyway — the fix is only in `sql/init.sql`).

---

_Verified: 2026-03-16T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
