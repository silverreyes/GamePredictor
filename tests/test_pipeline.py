"""Unit tests for pipeline steps, failure modes, and worker schedule."""
import os
from unittest.mock import MagicMock, patch, call

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Test: ingest_new_data calls loaders and upserts
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.validate_game_count")
@patch("pipeline.refresh.upsert_dataframe")
@patch("pipeline.refresh.get_table")
@patch("pipeline.refresh.normalize_teams_in_df", side_effect=lambda df, cols: df)
@patch("pipeline.refresh.select_schedule_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.select_pbp_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.filter_preseason", side_effect=lambda df, col: df)
@patch("pipeline.refresh.load_schedules_cached")
@patch("pipeline.refresh.load_pbp_cached")
@patch("pipeline.refresh.pd.read_sql")
def test_ingest_new_data_calls_loaders_and_upserts(
    mock_read_sql,
    mock_load_pbp,
    mock_load_sched,
    mock_filter,
    mock_select_pbp,
    mock_select_sched,
    mock_normalize,
    mock_get_table,
    mock_upsert,
    mock_validate,
):
    """Verify ingest_new_data calls cache deletion, loaders, and upserts."""
    from pipeline.refresh import ingest_new_data

    engine = MagicMock()

    # Mock DB queries:
    # 1. current season query -> 2024
    # 2. week_before query -> week 10
    # 3. week_after query (staleness check) -> week 11
    mock_read_sql.side_effect = [
        pd.DataFrame({"current_season": [2024]}),
        pd.DataFrame({"latest_week": [10]}),
        pd.DataFrame({"latest_week": [11]}),
    ]

    # Mock detect_current_week to return (2024, 11) -- not offseason
    with patch("pipeline.refresh.Path.unlink") as mock_unlink:
        with patch("models.predict.detect_current_week", return_value=(2024, 11)):
            # Mock loaders
            pbp_df = pd.DataFrame({
                "game_id": ["g1"], "season_type": ["REG"], "play_id": [1],
            })
            sched_df = pd.DataFrame({
                "game_id": ["g1"], "game_type": ["REG"],
            })
            mock_load_pbp.return_value = pbp_df
            mock_load_sched.return_value = sched_df
            mock_validate.return_value = MagicMock(status="OK", expected_games=272, actual_games=1)

            ingest_new_data(engine)

    # Verify loaders were called with current season
    mock_load_pbp.assert_called_once_with(2024)
    mock_load_sched.assert_called_once_with(2024)

    # Verify upsert was called twice (PBP + schedules)
    assert mock_upsert.call_count == 2

    # Verify cache invalidation (unlink called twice)
    assert mock_unlink.call_count == 2


# ---------------------------------------------------------------------------
# Test: staleness check raises ValueError
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.validate_game_count")
@patch("pipeline.refresh.upsert_dataframe")
@patch("pipeline.refresh.get_table")
@patch("pipeline.refresh.normalize_teams_in_df", side_effect=lambda df, cols: df)
@patch("pipeline.refresh.select_schedule_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.select_pbp_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.filter_preseason", side_effect=lambda df, col: df)
@patch("pipeline.refresh.load_schedules_cached")
@patch("pipeline.refresh.load_pbp_cached")
@patch("pipeline.refresh.pd.read_sql")
def test_ingest_new_data_staleness_raises(
    mock_read_sql,
    mock_load_pbp,
    mock_load_sched,
    mock_filter,
    mock_select_pbp,
    mock_select_sched,
    mock_normalize,
    mock_get_table,
    mock_upsert,
    mock_validate,
):
    """Mocks DB to return same max week before and after. Verifies ValueError raised."""
    from pipeline.refresh import ingest_new_data

    engine = MagicMock()

    # Same week before and after -> stale
    mock_read_sql.side_effect = [
        pd.DataFrame({"current_season": [2024]}),
        pd.DataFrame({"latest_week": [10]}),  # week_before
        pd.DataFrame({"latest_week": [10]}),  # week_after (same = stale)
    ]

    with patch("pipeline.refresh.Path.unlink"):
        with patch("models.predict.detect_current_week", return_value=(2024, 11)):
            pbp_df = pd.DataFrame({
                "game_id": ["g1"], "season_type": ["REG"], "play_id": [1],
            })
            sched_df = pd.DataFrame({
                "game_id": ["g1"], "game_type": ["REG"],
            })
            mock_load_pbp.return_value = pbp_df
            mock_load_sched.return_value = sched_df
            mock_validate.return_value = MagicMock(status="OK", expected_games=272, actual_games=1)

            with pytest.raises(ValueError, match="stale"):
                ingest_new_data(engine)


# ---------------------------------------------------------------------------
# Test: offseason guard skips ingestion entirely
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.pd.read_sql")
def test_ingest_offseason_skips(mock_read_sql):
    """Mocks detect_current_week to return None. Verifies early return without loaders."""
    from pipeline.refresh import ingest_new_data

    engine = MagicMock()

    # First query returns a season, but detect_current_week returns None
    mock_read_sql.return_value = pd.DataFrame({"current_season": [2024]})

    with patch("models.predict.detect_current_week", return_value=None):
        with patch("pipeline.refresh.load_pbp_cached") as mock_pbp:
            with patch("pipeline.refresh.Path.unlink") as mock_unlink:
                ingest_new_data(engine)

                # Should NOT have called loaders or cache invalidation
                mock_pbp.assert_not_called()
                mock_unlink.assert_not_called()


# ---------------------------------------------------------------------------
# Test: recompute_features chunks by season (BUG-001)
# ---------------------------------------------------------------------------
def test_recompute_features_chunks_by_season():
    """Verifies recompute_features processes each season independently.

    Regression test for BUG-001: the old implementation loaded all 20 seasons
    of raw PBP at once and OOM-killed the worker. The new implementation
    queries distinct seasons and calls build/store once per season.
    """
    from pipeline.refresh import recompute_features

    engine = MagicMock()
    seasons_df = pd.DataFrame({"season": [2022, 2023, 2024]})
    mock_df = pd.DataFrame({"a": [1, 2]})

    with patch("pipeline.refresh.pd.read_sql", return_value=seasons_df):
        with patch("features.build.build_game_features", return_value=mock_df) as mock_build:
            with patch("features.build.store_game_features", return_value=2) as mock_store:
                recompute_features(engine)

    # One build + store call per season, with that season in the seasons kwarg
    assert mock_build.call_count == 3
    assert mock_store.call_count == 3
    called_seasons = [c.kwargs["seasons"] for c in mock_build.call_args_list]
    assert called_seasons == [[2022], [2023], [2024]]


def test_recompute_features_empty_seasons():
    """If schedules is empty, recompute_features should no-op, not crash."""
    from pipeline.refresh import recompute_features

    engine = MagicMock()
    with patch("pipeline.refresh.pd.read_sql", return_value=pd.DataFrame({"season": []})):
        with patch("features.build.build_game_features") as mock_build:
            recompute_features(engine)
            mock_build.assert_not_called()


# ---------------------------------------------------------------------------
# Test: retrain_and_stage loads features from DB (BUG-001)
# ---------------------------------------------------------------------------
def test_retrain_loads_features_from_db(tmp_path):
    """retrain_and_stage must load from game_features table, not rebuild from PBP.

    Regression for BUG-001: rebuilding from PBP cache duplicates the OOM risk.
    The stored feature matrix is what training should consume.
    """
    from pipeline.refresh import retrain_and_stage

    engine = MagicMock()
    feature_df = pd.DataFrame({
        "game_id": ["g1"], "season": [2023], "week": [1],
        "home_team": ["KC"], "away_team": ["BUF"], "home_win": [1],
        "home_rest": [7],
    })

    with patch("pipeline.refresh._load_features_from_db", return_value=feature_df) as mock_load:
        with patch("models.train.load_and_split", return_value=(
            feature_df, feature_df, feature_df, feature_df, ["home_rest"],
        )):
            with patch("models.train.train_and_evaluate", return_value=(
                {"val_accuracy_2023": 0.6, "val_accuracy_2022": 0.6,
                 "val_accuracy_2021": 0.6, "log_loss": 0.5, "brier_score": 0.2,
                 "shap_top5": []},
                MagicMock(),
            )):
                with patch("models.baselines.compute_baselines", return_value={
                    "always_home_accuracy": 0.55, "better_record_accuracy": 0.58,
                }):
                    with patch("models.train.save_best_model", return_value="/m.json"):
                        with patch("models.train.log_experiment"):
                            retrain_and_stage(engine, str(tmp_path / "exp.jsonl"), str(tmp_path))

    mock_load.assert_called_once_with(engine)


# ---------------------------------------------------------------------------
# Test: retrain failure is non-fatal in run_pipeline
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.get_engine")
@patch("pipeline.refresh.ingest_new_data")
@patch("pipeline.refresh.recompute_features")
@patch("pipeline.refresh.retrain_and_stage", side_effect=RuntimeError("training failed"))
@patch("pipeline.refresh.generate_current_predictions")
def test_retrain_nonfatal_in_run_pipeline(
    mock_predict,
    mock_retrain,
    mock_features,
    mock_ingest,
    mock_engine,
):
    """Step 3 failure should NOT prevent step 4 from running."""
    from pipeline.refresh import run_pipeline

    mock_engine.return_value = MagicMock()
    run_pipeline()

    # Step 4 should still be called despite step 3 failure
    mock_predict.assert_called_once()


# ---------------------------------------------------------------------------
# Test: step 1 failure stops pipeline
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.get_engine")
@patch("pipeline.refresh.ingest_new_data", side_effect=RuntimeError("ingest failed"))
@patch("pipeline.refresh.recompute_features")
def test_step1_failure_stops_pipeline(mock_features, mock_ingest, mock_engine):
    """Step 1 failure should prevent step 2 from running."""
    from pipeline.refresh import run_pipeline

    mock_engine.return_value = MagicMock()
    run_pipeline()

    # Step 2 should NOT be called
    mock_features.assert_not_called()


# ---------------------------------------------------------------------------
# Test: step 2 failure stops pipeline
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.get_engine")
@patch("pipeline.refresh.ingest_new_data")
@patch("pipeline.refresh.recompute_features", side_effect=RuntimeError("features failed"))
@patch("pipeline.refresh.retrain_and_stage")
def test_step2_failure_stops_pipeline(mock_retrain, mock_features, mock_ingest, mock_engine):
    """Step 2 failure should prevent step 3 from running."""
    from pipeline.refresh import run_pipeline

    mock_engine.return_value = MagicMock()
    run_pipeline()

    # Step 3 should NOT be called
    mock_retrain.assert_not_called()


# ---------------------------------------------------------------------------
# Test: cache invalidation
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.validate_game_count")
@patch("pipeline.refresh.upsert_dataframe")
@patch("pipeline.refresh.get_table")
@patch("pipeline.refresh.normalize_teams_in_df", side_effect=lambda df, cols: df)
@patch("pipeline.refresh.select_schedule_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.select_pbp_columns", side_effect=lambda df: df)
@patch("pipeline.refresh.filter_preseason", side_effect=lambda df, col: df)
@patch("pipeline.refresh.load_schedules_cached")
@patch("pipeline.refresh.load_pbp_cached")
@patch("pipeline.refresh.pd.read_sql")
def test_cache_invalidation(
    mock_read_sql,
    mock_load_pbp,
    mock_load_sched,
    mock_filter,
    mock_select_pbp,
    mock_select_sched,
    mock_normalize,
    mock_get_table,
    mock_upsert,
    mock_validate,
):
    """Verifies ingest_new_data calls unlink for pbp and schedules cache files."""
    from pipeline.refresh import ingest_new_data

    engine = MagicMock()

    mock_read_sql.side_effect = [
        pd.DataFrame({"current_season": [2024]}),
        pd.DataFrame({"latest_week": [10]}),
        pd.DataFrame({"latest_week": [11]}),
    ]

    with patch("pipeline.refresh.Path.unlink") as mock_unlink:
        with patch("models.predict.detect_current_week", return_value=(2024, 11)):
            pbp_df = pd.DataFrame({
                "game_id": ["g1"], "season_type": ["REG"], "play_id": [1],
            })
            sched_df = pd.DataFrame({
                "game_id": ["g1"], "game_type": ["REG"],
            })
            mock_load_pbp.return_value = pbp_df
            mock_load_sched.return_value = sched_df
            mock_validate.return_value = MagicMock(status="OK", expected_games=272, actual_games=1)

            ingest_new_data(engine)

    # Should have called unlink twice (pbp + schedules cache) with missing_ok=True
    assert mock_unlink.call_count == 2
    for c in mock_unlink.call_args_list:
        assert c == call(missing_ok=True)


# ---------------------------------------------------------------------------
# Test: worker schedule configuration
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Test: step 5 generates spread predictions
# ---------------------------------------------------------------------------
@patch("models.predict.generate_spread_predictions", return_value=[{"game_id": "g1"}])
@patch("models.predict.detect_current_week", return_value=(2024, 5))
@patch("models.predict.get_best_spread_experiment", return_value={"experiment_id": 42})
@patch("models.predict.load_best_spread_model")
def test_step5_generates_spread_predictions(
    mock_load_spread,
    mock_get_exp,
    mock_detect,
    mock_generate,
):
    """Step 5 should call all 4 spread functions with correct args."""
    from pipeline.refresh import generate_current_spread_predictions

    engine = MagicMock()
    spread_model_path = "/path/spread.json"
    spread_experiments_path = "/path/spread_exp.jsonl"

    generate_current_spread_predictions(engine, spread_model_path, spread_experiments_path)

    mock_load_spread.assert_called_once_with(spread_model_path)
    mock_get_exp.assert_called_once_with(spread_experiments_path)
    mock_detect.assert_called_once_with(engine)
    mock_generate.assert_called_once_with(
        mock_load_spread.return_value, 2024, 5, engine, model_id=42,
    )


# ---------------------------------------------------------------------------
# Test: step 5 failure is non-fatal in run_pipeline
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.get_engine")
@patch("pipeline.refresh.ingest_new_data")
@patch("pipeline.refresh.recompute_features")
@patch("pipeline.refresh.retrain_and_stage")
@patch("pipeline.refresh.generate_current_predictions")
@patch("pipeline.refresh.generate_current_spread_predictions", side_effect=RuntimeError("spread failed"))
def test_step5_nonfatal_in_run_pipeline(
    mock_spread,
    mock_predict,
    mock_retrain,
    mock_features,
    mock_ingest,
    mock_engine,
):
    """Step 5 failure should NOT prevent pipeline from completing."""
    from pipeline.refresh import run_pipeline

    mock_engine.return_value = MagicMock()
    run_pipeline()  # Should NOT raise

    # Earlier steps should still have been called
    mock_ingest.assert_called_once()
    mock_predict.assert_called_once()


# ---------------------------------------------------------------------------
# Test: step 5 offseason skips spread generation
# ---------------------------------------------------------------------------
@patch("models.predict.generate_spread_predictions")
@patch("models.predict.detect_current_week", return_value=None)
@patch("models.predict.get_best_spread_experiment", return_value={"experiment_id": 1})
@patch("models.predict.load_best_spread_model")
def test_step5_offseason_skips(
    mock_load_spread,
    mock_get_exp,
    mock_detect,
    mock_generate,
):
    """Offseason (detect_current_week returns None) should skip spread predictions."""
    from pipeline.refresh import generate_current_spread_predictions

    engine = MagicMock()
    generate_current_spread_predictions(engine, "p", "e")

    mock_generate.assert_not_called()


# ---------------------------------------------------------------------------
# Test: run_pipeline reads spread env vars
# ---------------------------------------------------------------------------
@patch("pipeline.refresh.get_engine")
@patch("pipeline.refresh.ingest_new_data")
@patch("pipeline.refresh.recompute_features")
@patch("pipeline.refresh.retrain_and_stage")
@patch("pipeline.refresh.generate_current_predictions")
@patch("pipeline.refresh.generate_current_spread_predictions")
def test_run_pipeline_reads_spread_env_vars(
    mock_spread,
    mock_predict,
    mock_retrain,
    mock_features,
    mock_ingest,
    mock_engine,
    monkeypatch,
):
    """run_pipeline should pass SPREAD_MODEL_PATH and SPREAD_EXPERIMENTS_PATH env vars to step 5."""
    monkeypatch.setenv("SPREAD_MODEL_PATH", "/vol/spread.json")
    monkeypatch.setenv("SPREAD_EXPERIMENTS_PATH", "/vol/spread_exp.jsonl")

    from pipeline.refresh import run_pipeline

    mock_engine.return_value = MagicMock()
    run_pipeline()

    mock_spread.assert_called_once()
    call_args = mock_spread.call_args
    # positional args: (engine, spread_model_path, spread_experiments_path)
    assert call_args[0][1] == "/vol/spread.json"
    assert call_args[0][2] == "/vol/spread_exp.jsonl"


# ---------------------------------------------------------------------------
# Test: worker schedule configuration
# ---------------------------------------------------------------------------
def test_worker_schedule_config(monkeypatch):
    """Verifies CronTrigger with day_of_week='tue' and configurable hour from env."""
    monkeypatch.setenv("REFRESH_CRON_HOUR", "10")

    import pipeline.worker

    mock_sched_instance = MagicMock()
    original_scheduler = pipeline.worker.scheduler
    pipeline.worker.scheduler = mock_sched_instance

    try:
        with patch("pipeline.worker.signal.signal"):
            pipeline.worker.main()

        # Verify add_job was called
        mock_sched_instance.add_job.assert_called_once()
        job_call = mock_sched_instance.add_job.call_args

        # The CronTrigger is passed as the second positional arg
        trigger = job_call[0][1]
        from apscheduler.triggers.cron import CronTrigger
        assert isinstance(trigger, CronTrigger)

        # Verify day_of_week="tue" and hour=10
        # CronTrigger.fields is ordered: year, month, day, week, day_of_week, hour, minute, second
        assert str(trigger.fields[4]) == "tue"   # day_of_week
        assert str(trigger.fields[5]) == "10"    # hour
    finally:
        pipeline.worker.scheduler = original_scheduler


