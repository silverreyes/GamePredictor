"""Unit tests for training pipeline (models/train.py).

Tests cover:
- Temporal split correctness and boundary enforcement
- Tie exclusion and NaN rolling feature dropping
- In-sample 2021/2022 remaining in training set
- Forbidden feature rejection
- Multi-season evaluation return format
- TreeSHAP top-5 format
- Compound keep/revert decision logic
"""

import numpy as np
import pandas as pd
import pytest

from tests.models.conftest import ROLLING_COLS
from models.train import load_and_split, train_and_evaluate, should_keep


def _make_multi_season_df(
    seasons: list[int],
    rows_per_season: int = 5,
    include_tie: bool = False,
    include_nan_week1: bool = True,
) -> pd.DataFrame:
    """Build a synthetic multi-season feature DataFrame for split tests.

    Args:
        seasons: List of seasons to include.
        rows_per_season: Games per season (default 5).
        include_tie: If True, last game of first season is a tie (home_win=NaN).
        include_nan_week1: If True, week 1 of each season has NaN rolling features.

    Returns:
        DataFrame mimicking build_game_features() output.
    """
    teams = ["KC", "BUF", "SF", "PHI", "DAL", "MIA", "BAL", "DET", "CIN", "JAX"]
    rows = []

    for season in seasons:
        for i in range(rows_per_season):
            week = i + 1
            home = teams[i % len(teams)]
            away = teams[(i + 1) % len(teams)]

            # Rolling features: NaN for week 1, known values otherwise
            if include_nan_week1 and week == 1:
                rolling_vals = {col: np.nan for col in ROLLING_COLS}
            else:
                rolling_vals = {col: 0.5 + (i * 0.01) for col in ROLLING_COLS}

            # Target: home wins most games
            if include_tie and season == seasons[0] and i == rows_per_season - 1:
                home_win = np.nan  # tie
            else:
                home_win = float(1 if i % 2 == 0 else 0)

            row = {
                "game_id": f"{season}_{week:02d}_{away}_{home}",
                "season": season,
                "week": week,
                "gameday": f"{season}-09-{10 + i:02d}",
                "home_team": home,
                "away_team": away,
                "home_win": home_win,
                "home_rest": 7,
                "away_rest": 7,
                "div_game": 0,
            }
            row.update(rolling_vals)
            rows.append(row)

    return pd.DataFrame(rows)


class TestTemporalSplit:
    """Tests for load_and_split temporal boundary enforcement."""

    def test_temporal_split(self):
        """load_and_split assigns seasons 2005-2022 to train and 2023 to val_2023."""
        df = _make_multi_season_df(
            seasons=[2005, 2010, 2021, 2022, 2023],
            rows_per_season=5,
            include_nan_week1=True,
        )
        train, val_2023, val_2022, val_2021, feature_cols = load_and_split(df)

        # Train should contain 2005, 2010, 2021, 2022
        assert set(train["season"].unique()) == {2005, 2010, 2021, 2022}

        # val_2023 should contain only 2023
        assert set(val_2023["season"].unique()) == {2023}

        # val_2022 and val_2021 are subsets
        assert set(val_2022["season"].unique()) == {2022}
        assert set(val_2021["season"].unique()) == {2021}

    def test_temporal_split_excludes_ties(self):
        """Rows with home_win=NaN (ties) are excluded from all splits."""
        df = _make_multi_season_df(
            seasons=[2021, 2022, 2023],
            rows_per_season=5,
            include_tie=True,
            include_nan_week1=False,
        )

        # Verify there IS a tie in the data
        assert df["home_win"].isna().sum() == 1

        train, val_2023, val_2022, val_2021, _ = load_and_split(df)

        # No NaN in any split's target column
        assert train["home_win"].isna().sum() == 0
        assert val_2023["home_win"].isna().sum() == 0
        assert val_2022["home_win"].isna().sum() == 0
        assert val_2021["home_win"].isna().sum() == 0

    def test_temporal_split_drops_nan_features(self):
        """Week-1 rows with NaN rolling features are dropped from all splits."""
        df = _make_multi_season_df(
            seasons=[2021, 2022, 2023],
            rows_per_season=5,
            include_nan_week1=True,
        )

        # Before split, there should be 3 week-1 NaN rows (one per season)
        week1_rows = df[df["week"] == 1]
        assert len(week1_rows) == 3
        assert week1_rows[ROLLING_COLS[0]].isna().all()

        train, val_2023, val_2022, val_2021, feature_cols = load_and_split(df)

        # After split, no NaN in feature columns for any split
        for split_name, split_df in [
            ("train", train),
            ("val_2023", val_2023),
            ("val_2022", val_2022),
            ("val_2021", val_2021),
        ]:
            for col in feature_cols:
                assert split_df[col].isna().sum() == 0, (
                    f"NaN found in {split_name}[{col}]"
                )

    def test_train_size_includes_2021_2022(self):
        """2021 and 2022 data remains in the training set (not removed).

        val_2021/val_2022 are in-sample evaluation subsets, NOT held-out.
        The training set should include them.
        """
        df = _make_multi_season_df(
            seasons=[2005, 2021, 2022, 2023],
            rows_per_season=5,
            include_nan_week1=False,
        )
        train, val_2023, val_2022, val_2021, _ = load_and_split(df)

        # Training set should include 2021 and 2022 seasons
        train_seasons = set(train["season"].unique())
        assert 2021 in train_seasons
        assert 2022 in train_seasons

        # val_2021 and val_2022 should be subsets of train (same data)
        assert len(val_2021) > 0
        assert len(val_2022) > 0

    def test_no_forbidden_features(self):
        """load_and_split raises AssertionError if forbidden features appear in columns."""
        df = _make_multi_season_df(
            seasons=[2022, 2023],
            rows_per_season=3,
            include_nan_week1=False,
        )

        # Add a forbidden feature column
        df["result"] = 10.0

        with pytest.raises(AssertionError, match="Forbidden feature"):
            load_and_split(df)


class TestTrainAndEvaluate:
    """Tests for train_and_evaluate function."""

    @pytest.fixture
    def training_data(self):
        """Prepare small synthetic training/evaluation data for XGBoost tests."""
        np.random.seed(42)
        n_train = 50
        n_val = 20
        n_features = 5  # Use fewer features for speed

        feature_names = [f"feat_{i}" for i in range(n_features)]

        def make_set(n):
            X = pd.DataFrame(
                np.random.randn(n, n_features),
                columns=feature_names,
            )
            y = pd.Series(np.random.randint(0, 2, size=n), dtype=float)
            return X, y

        X_train, y_train = make_set(n_train)
        X_val_2023, y_val_2023 = make_set(n_val)
        X_val_2022, y_val_2022 = make_set(n_val)
        X_val_2021, y_val_2021 = make_set(n_val)

        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val_2023": X_val_2023,
            "y_val_2023": y_val_2023,
            "X_val_2022": X_val_2022,
            "y_val_2022": y_val_2022,
            "X_val_2021": X_val_2021,
            "y_val_2021": y_val_2021,
        }

    def test_multi_season_eval(self, training_data):
        """train_and_evaluate returns val_accuracy_2023, val_accuracy_2022, val_accuracy_2021."""
        results, model = train_and_evaluate(
            **training_data,
            params={"n_estimators": 5, "max_depth": 2},
        )

        assert "val_accuracy_2023" in results
        assert "val_accuracy_2022" in results
        assert "val_accuracy_2021" in results
        assert "log_loss" in results
        assert "brier_score" in results

        # All accuracies should be between 0 and 1
        for key in ["val_accuracy_2023", "val_accuracy_2022", "val_accuracy_2021"]:
            assert 0.0 <= results[key] <= 1.0

    def test_shap_top5_format(self, training_data):
        """train_and_evaluate results['shap_top5'] is a list of 5 (str, float) tuples."""
        results, _ = train_and_evaluate(
            **training_data,
            params={"n_estimators": 5, "max_depth": 2},
        )

        shap_top5 = results["shap_top5"]
        assert isinstance(shap_top5, list)
        assert len(shap_top5) == 5

        for item in shap_top5:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)  # feature name
            assert isinstance(item[1], float)  # importance value
            assert item[1] >= 0  # SHAP importance is non-negative (mean absolute)


class TestShouldKeep:
    """Tests for compound keep/revert decision logic."""

    def test_keep_revert_large_improvement(self):
        """should_keep returns True when accuracy improves by >= 0.5%."""
        assert should_keep(
            new_acc=0.610,
            prev_best_acc=0.600,
            new_log_loss=0.690,  # log_loss worse
            prev_best_log_loss=0.680,
        ) is True

    def test_keep_revert_small_improvement_with_logloss(self):
        """should_keep returns True when accuracy improves by any amount AND log_loss improves."""
        assert should_keep(
            new_acc=0.602,
            prev_best_acc=0.600,
            new_log_loss=0.675,  # log_loss better
            prev_best_log_loss=0.680,
        ) is True

    def test_keep_revert_small_improvement_without_logloss(self):
        """should_keep returns False when accuracy improves < 0.5% but log_loss worsens."""
        assert should_keep(
            new_acc=0.602,
            prev_best_acc=0.600,
            new_log_loss=0.690,  # log_loss worse
            prev_best_log_loss=0.680,
        ) is False

    def test_keep_revert_no_improvement(self):
        """should_keep returns False when accuracy does not improve."""
        assert should_keep(
            new_acc=0.598,
            prev_best_acc=0.600,
            new_log_loss=0.670,  # even if log_loss improves
            prev_best_log_loss=0.680,
        ) is False
