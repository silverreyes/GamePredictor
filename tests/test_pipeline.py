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
# Test: recompute_features calls build and store
# ---------------------------------------------------------------------------
def test_recompute_features_calls_build_and_store():
    """Mocks build_game_features and store_game_features. Verifies both called."""
    from pipeline.refresh import recompute_features

    engine = MagicMock()
    mock_df = pd.DataFrame({"a": [1, 2]})

    with patch("features.build.build_game_features", return_value=mock_df) as mock_build:
        with patch("features.build.store_game_features", return_value=2) as mock_store:
            recompute_features(engine)

            mock_build.assert_called_once()
            mock_store.assert_called_once_with(mock_df)


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


