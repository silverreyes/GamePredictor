"""Unit tests for feature pipeline correctness.

Tests verify: aggregation produces correct per-team stats, rolling uses
shift(1) with NaN for week 1, rolling resets at season boundaries,
home perspective has one row per game with both teams' rolling features
and situational features, no forbidden columns in output.
"""
import pandas as pd
import numpy as np
import pytest

from features.build import (
    aggregate_game_stats,
    compute_rolling_features,
    build_home_perspective,
    build_game_features,
)
from features.definitions import FORBIDDEN_FEATURES


# =============================================================================
# Aggregation Tests
# =============================================================================


class TestAggregateGameStats:
    """Tests for the aggregate_game_stats function."""

    def test_aggregate_game_stats_row_count(self, synthetic_pbp, synthetic_schedule):
        """4 games x 2 teams per game = 8 rows in team log."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        assert len(team_log) == 8

    def test_aggregate_game_stats_epa_values(self, synthetic_pbp, synthetic_schedule):
        """KC game 1 off_epa = 0.2, def_epa = -0.1 (DET's offense EPA)."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        kc_game1 = team_log[
            (team_log["team"] == "KC") & (team_log["game_id"] == "2023_01_KC_DET")
        ]
        assert len(kc_game1) == 1
        assert kc_game1["off_epa_per_play"].iloc[0] == pytest.approx(0.2, abs=1e-6)
        assert kc_game1["def_epa_per_play"].iloc[0] == pytest.approx(-0.1, abs=1e-6)

    def test_aggregate_game_stats_turnovers(self, synthetic_pbp, synthetic_schedule):
        """KC game 1: turnovers_committed = 1 (1 INT), turnovers_forced = 0."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        kc_game1 = team_log[
            (team_log["team"] == "KC") & (team_log["game_id"] == "2023_01_KC_DET")
        ]
        assert kc_game1["turnovers_committed"].iloc[0] == 1
        assert kc_game1["turnovers_forced"].iloc[0] == 0

    def test_aggregate_game_stats_turnover_diff(self, synthetic_pbp, synthetic_schedule):
        """KC game 1: turnover_diff = forced - committed = 0 - 1 = -1."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        kc_game1 = team_log[
            (team_log["team"] == "KC") & (team_log["game_id"] == "2023_01_KC_DET")
        ]
        assert kc_game1["turnover_diff"].iloc[0] == -1

    def test_aggregate_game_stats_win_column(self, synthetic_pbp, synthetic_schedule):
        """KC wins games 1,2 (home), game 3 (away at CHI, result=-7 means
        home CHI lost so away KC won), loses game 4 (home)."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        kc = team_log[team_log["team"] == "KC"].sort_values("week")
        wins = kc["win"].tolist()
        # Game 1: KC home, result=7 > 0 => win=1.0
        # Game 2: KC home, result=10 > 0 => win=1.0
        # Game 3: KC away at CHI, result=-7 => away team won => win=1.0
        # Game 4: KC home, result=-17 < 0 => win=0.0
        assert wins == [1.0, 1.0, 1.0, 0.0]

    def test_aggregate_game_stats_point_diff(self, synthetic_pbp, synthetic_schedule):
        """KC game 1 (home, result=7) point_diff = 7.0."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        kc_game1 = team_log[
            (team_log["team"] == "KC") & (team_log["game_id"] == "2023_01_KC_DET")
        ]
        assert kc_game1["point_diff"].iloc[0] == pytest.approx(7.0)


# =============================================================================
# Rolling Feature Tests
# =============================================================================


class TestComputeRollingFeatures:
    """Tests for the compute_rolling_features function."""

    def test_rolling_shift1_excludes_current(self, synthetic_pbp, synthetic_schedule):
        """KC game 1 rolling_off_epa is NaN (first game),
        KC game 2 rolling_off_epa = 0.2 (only game 1 data)."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        kc = rolling[rolling["team"] == "KC"].sort_values("week")

        # Game 1: first game => NaN
        assert pd.isna(kc.iloc[0]["rolling_off_epa_per_play"])

        # Game 2: only game 1 data => 0.2
        assert kc.iloc[1]["rolling_off_epa_per_play"] == pytest.approx(0.2, abs=1e-6)

    def test_rolling_week1_nan(self, synthetic_pbp, synthetic_schedule):
        """All rolling columns are NaN for week 1 games."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)

        week1 = rolling[rolling["week"] == 1]
        rolling_cols = [c for c in rolling.columns if c.startswith("rolling_")]

        for _, row in week1.iterrows():
            for col in rolling_cols:
                assert pd.isna(row[col]), (
                    f"Week 1 {row['team']} {col} should be NaN, got {row[col]}"
                )

    def test_rolling_expanding_mean(self, synthetic_pbp, synthetic_schedule):
        """KC game 3 rolling_off_epa = mean(0.2, 0.3) = 0.25."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        kc = rolling[rolling["team"] == "KC"].sort_values("week")

        # Game 3 (index 2): expanding mean of games 1 and 2
        assert kc.iloc[2]["rolling_off_epa_per_play"] == pytest.approx(0.25, abs=1e-6)

    def test_rolling_resets_at_season_boundary(
        self, synthetic_two_season_pbp, synthetic_two_season_schedule
    ):
        """With 2-season fixture, 2023 week 1 rolling features are NaN
        despite 2022 data existing."""
        team_log = aggregate_game_stats(
            synthetic_two_season_pbp, synthetic_two_season_schedule
        )
        rolling = compute_rolling_features(team_log)

        # KC in 2023 week 1 should have NaN rolling (season reset)
        kc_2023_w1 = rolling[
            (rolling["team"] == "KC")
            & (rolling["season"] == 2023)
            & (rolling["week"] == 1)
        ]
        assert len(kc_2023_w1) == 1
        rolling_cols = [c for c in rolling.columns if c.startswith("rolling_")]
        for col in rolling_cols:
            assert pd.isna(kc_2023_w1.iloc[0][col]), (
                f"2023 week 1 KC {col} should be NaN (season reset), got {kc_2023_w1.iloc[0][col]}"
            )

    def test_rolling_win_rate_values(self, synthetic_pbp, synthetic_schedule):
        """KC game 4 rolling_win = mean(1.0, 1.0, 1.0) = 1.0 (won first 3)."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        kc = rolling[rolling["team"] == "KC"].sort_values("week")

        # Game 4 (index 3): expanding mean of wins [1.0, 1.0, 1.0]
        assert kc.iloc[3]["rolling_win"] == pytest.approx(1.0, abs=1e-6)


# =============================================================================
# Home Perspective Tests
# =============================================================================


class TestBuildHomePerspective:
    """Tests for the build_home_perspective function."""

    def test_home_perspective_one_row_per_game(self, synthetic_pbp, synthetic_schedule):
        """Output has exactly as many rows as regular-season games in schedule."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        result = build_home_perspective(synthetic_schedule, rolling)

        n_reg = len(synthetic_schedule[synthetic_schedule["game_type"] == "REG"])
        assert len(result) == n_reg

    def test_home_perspective_has_both_teams(self, synthetic_pbp, synthetic_schedule):
        """Output has home_rolling_* and away_rolling_* columns."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        result = build_home_perspective(synthetic_schedule, rolling)

        home_rolling_cols = [c for c in result.columns if c.startswith("home_rolling_")]
        away_rolling_cols = [c for c in result.columns if c.startswith("away_rolling_")]

        assert len(home_rolling_cols) > 0, "No home_rolling_* columns found"
        assert len(away_rolling_cols) > 0, "No away_rolling_* columns found"
        assert len(home_rolling_cols) == len(away_rolling_cols), (
            "Mismatched home/away rolling column counts"
        )

    def test_home_perspective_situational_features(self, synthetic_pbp, synthetic_schedule):
        """Output has home_rest, away_rest, div_game, week columns."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        result = build_home_perspective(synthetic_schedule, rolling)

        for col in ["home_rest", "away_rest", "div_game", "week"]:
            assert col in result.columns, f"Missing situational column: {col}"

    def test_home_perspective_no_forbidden_columns(self, synthetic_pbp, synthetic_schedule):
        """result, home_score, away_score not in output columns."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        result = build_home_perspective(synthetic_schedule, rolling)

        for col in FORBIDDEN_FEATURES:
            assert col not in result.columns, f"Forbidden column '{col}' found in output"

    def test_home_win_target(self, synthetic_pbp, synthetic_schedule):
        """home_win = 1 when result > 0, 0 when result < 0, None for ties."""
        team_log = aggregate_game_stats(synthetic_pbp, synthetic_schedule)
        rolling = compute_rolling_features(team_log)
        result = build_home_perspective(synthetic_schedule, rolling)

        result_sorted = result.sort_values("week")
        # Game 1: KC home, result=7 => home_win=1
        assert result_sorted.iloc[0]["home_win"] == 1
        # Game 2: KC home, result=10 => home_win=1
        assert result_sorted.iloc[1]["home_win"] == 1
        # Game 3: CHI home, result=-7 => home_win=0
        assert result_sorted.iloc[2]["home_win"] == 0
        # Game 4: KC home, result=-17 => home_win=0
        assert result_sorted.iloc[3]["home_win"] == 0


# =============================================================================
# End-to-End Test
# =============================================================================


class TestBuildGameFeatures:
    """Tests for the full build_game_features pipeline."""

    def test_build_game_features_end_to_end(self, synthetic_pbp, synthetic_schedule):
        """Full pipeline with synthetic data produces correct shape
        and no NaN in situational columns."""
        result = build_game_features(
            pbp=synthetic_pbp, schedule=synthetic_schedule
        )

        # Correct number of rows (4 regular season games)
        assert len(result) == 4

        # Has required column groups
        assert "game_id" in result.columns
        assert "season" in result.columns
        assert "home_win" in result.columns
        assert "home_team" in result.columns
        assert "away_team" in result.columns

        # Situational features are not NaN
        for col in ["week", "home_rest", "away_rest", "div_game"]:
            assert result[col].notna().all(), f"NaN found in situational column: {col}"

        # No forbidden features
        for col in FORBIDDEN_FEATURES:
            assert col not in result.columns, f"Forbidden column '{col}' in output"

        # Has both home and away rolling columns
        home_rolling = [c for c in result.columns if c.startswith("home_rolling_")]
        away_rolling = [c for c in result.columns if c.startswith("away_rolling_")]
        assert len(home_rolling) == 7  # 7 rolling features
        assert len(away_rolling) == 7

    def test_build_game_features_two_seasons(
        self, synthetic_two_season_pbp, synthetic_two_season_schedule
    ):
        """Two-season data produces correct row count and season reset."""
        result = build_game_features(
            pbp=synthetic_two_season_pbp, schedule=synthetic_two_season_schedule
        )

        # 3 regular season games
        assert len(result) == 3

        # Week 1 2023 game should have NaN rolling features
        w1_2023 = result[(result["season"] == 2023) & (result["week"] == 1)]
        assert len(w1_2023) == 1
        home_rolling_cols = [c for c in result.columns if c.startswith("home_rolling_")]
        for col in home_rolling_cols:
            assert pd.isna(w1_2023.iloc[0][col]), (
                f"2023 week 1 home {col} should be NaN, got {w1_2023.iloc[0][col]}"
            )
