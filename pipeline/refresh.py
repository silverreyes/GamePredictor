"""Weekly pipeline: ingest -> features -> retrain -> predict."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import pandas as pd

from data.db import get_engine, get_table
from data.ingest import upsert_dataframe
from data.loaders import load_pbp_cached, load_schedules_cached
from data.sources import TEAM_COLUMNS_PBP, TEAM_COLUMNS_SCHEDULE
from data.transforms import (
    filter_preseason,
    normalize_teams_in_df,
    select_pbp_columns,
    select_schedule_columns,
)
from data.validators import validate_game_count

logger = logging.getLogger(__name__)


def ingest_new_data(engine):
    """Step 1: Ingest new data for the current season.

    - Offseason guard: skips entirely if detect_current_week returns None
    - Cache invalidation: deletes parquet cache before re-downloading
    - Staleness check: verifies new results appeared after ingestion
    """
    from models.predict import detect_current_week

    # Determine current season
    season_result = pd.read_sql(
        "SELECT MAX(season) AS current_season FROM schedules WHERE game_type = 'REG'",
        engine,
    )
    current_season = season_result["current_season"].iloc[0]
    if current_season is None:
        logger.info("No seasons found in database -- skipping ingestion")
        return
    current_season = int(current_season)

    # Offseason guard
    if detect_current_week(engine) is None:
        logger.info("Offseason detected -- skipping ingestion")
        return

    # Record week before ingestion for staleness check
    week_before_result = pd.read_sql(
        "SELECT MAX(week) AS latest_week FROM schedules "
        "WHERE season = %(season)s AND game_type = 'REG' AND home_score IS NOT NULL",
        engine,
        params={"season": current_season},
    )
    week_before = week_before_result["latest_week"].iloc[0]
    logger.info("Current season: %d, latest completed week before ingestion: %s", current_season, week_before)

    # Cache invalidation
    pbp_cache = Path(f"data/cache/pbp_{current_season}.parquet")
    sched_cache = Path(f"data/cache/schedules_{current_season}.parquet")
    pbp_cache.unlink(missing_ok=True)
    sched_cache.unlink(missing_ok=True)
    logger.info("Cache invalidated for season %d", current_season)

    # Ingest PBP
    logger.info("Loading PBP data for season %d...", current_season)
    pbp_df = load_pbp_cached(current_season)
    pbp_df = filter_preseason(pbp_df, "season_type")
    pbp_df = select_pbp_columns(pbp_df)
    pbp_df = normalize_teams_in_df(pbp_df, TEAM_COLUMNS_PBP)

    raw_pbp_table = get_table("raw_pbp", engine)
    upsert_dataframe(engine, raw_pbp_table, pbp_df, ["game_id", "play_id"])
    logger.info("Upserted %d PBP rows", len(pbp_df))

    # Validate PBP game counts
    reg_pbp = pbp_df[pbp_df["season_type"] == "REG"]
    pbp_game_count = reg_pbp["game_id"].nunique()
    pbp_result = validate_game_count(current_season, pbp_game_count, "raw_pbp")
    logger.info("PBP validation: %s (expected %d, got %d)", pbp_result.status, pbp_result.expected_games, pbp_result.actual_games)

    # Ingest schedules
    logger.info("Loading schedule data for season %d...", current_season)
    sched_df = load_schedules_cached(current_season)
    sched_df = sched_df[sched_df["game_type"] != "PRE"].reset_index(drop=True)
    sched_df = select_schedule_columns(sched_df)
    sched_df = normalize_teams_in_df(sched_df, TEAM_COLUMNS_SCHEDULE)
    sched_df["games_in_season"] = 16 if current_season <= 2020 else 17

    schedules_table = get_table("schedules", engine)
    upsert_dataframe(engine, schedules_table, sched_df, ["game_id"])
    logger.info("Upserted %d schedule rows", len(sched_df))

    # Validate schedule game counts
    sched_reg_count = len(sched_df[sched_df["game_type"] == "REG"])
    sched_result = validate_game_count(current_season, sched_reg_count, "schedules")
    logger.info("Schedule validation: %s (expected %d, got %d)", sched_result.status, sched_result.expected_games, sched_result.actual_games)

    # Staleness check
    week_after_result = pd.read_sql(
        "SELECT MAX(week) AS latest_week FROM schedules "
        "WHERE season = %(season)s AND game_type = 'REG' AND home_score IS NOT NULL",
        engine,
        params={"season": current_season},
    )
    week_after = week_after_result["latest_week"].iloc[0]

    if week_after is not None and week_before is not None:
        if int(week_after) <= int(week_before):
            raise ValueError(
                f"Data stale: latest completed week is {week_after}, "
                f"expected new results (was {week_before} before ingestion)"
            )
    elif week_after is None and week_before is None:
        raise ValueError("Data stale: latest completed week is None, expected new results")

    logger.info("Ingestion complete. Latest completed week: %s", week_after)


def recompute_features(engine):
    """Step 2: Recompute features for all seasons."""
    from features.build import build_game_features, store_game_features

    logger.info("Building game features for all seasons...")
    df = build_game_features()
    n = store_game_features(df)
    logger.info("Stored %d feature rows", n)


def retrain_and_stage(engine, experiments_path, model_dir):
    """Step 3: Retrain model using existing training pipeline and stage it.

    This function trains a new model and stages it. The staged model does NOT
    go live until POST /model/reload is called (per must_haves).

    Non-fatal: if this step fails, run_pipeline continues to step 4.
    """
    from features.build import build_game_features
    from models.baselines import compute_baselines
    from models.train import (
        DEFAULT_PARAMS,
        load_and_split,
        log_experiment,
        save_best_model,
        setup_mlflow,
        should_keep,
        train_and_evaluate,
    )
    from features.definitions import TARGET

    # MLflow setup: respect MLFLOW_TRACKING_URI env var for Docker
    if os.environ.get("MLFLOW_TRACKING_URI"):
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
        mlflow.set_experiment("nfl-game-predictor")
    else:
        setup_mlflow()

    # Load feature matrix and split
    logger.info("Loading feature matrix for retraining...")
    df = build_game_features()
    train, val_2023, val_2022, val_2021, feature_cols = load_and_split(df)

    # Determine experiment ID from existing experiments
    experiment_id = 1
    prev_best_acc = 0.0
    prev_best_log_loss = float("inf")
    current_params = DEFAULT_PARAMS.copy()

    if os.path.exists(experiments_path):
        with open(experiments_path) as f:
            lines = [line.strip() for line in f if line.strip()]
            experiment_id = len(lines) + 1
            for line in lines:
                entry = json.loads(line)
                if entry.get("keep"):
                    if entry["val_accuracy_2023"] > prev_best_acc:
                        prev_best_acc = entry["val_accuracy_2023"]
                        prev_best_log_loss = entry["log_loss"]
                    # Use the last kept experiment's params
                    current_params = entry.get("params", DEFAULT_PARAMS.copy())

    logger.info("Training experiment %d with params from last kept experiment...", experiment_id)

    # Prepare X/y splits
    X_train = train[feature_cols]
    y_train = train[TARGET]
    X_val_2023 = val_2023[feature_cols]
    y_val_2023 = val_2023[TARGET]
    X_val_2022 = val_2022[feature_cols]
    y_val_2022 = val_2022[TARGET]
    X_val_2021 = val_2021[feature_cols]
    y_val_2021 = val_2021[TARGET]

    # Train and evaluate
    results, model = train_and_evaluate(
        X_train, y_train,
        X_val_2023, y_val_2023,
        X_val_2022, y_val_2022,
        X_val_2021, y_val_2021,
        current_params,
    )

    # Compute baselines
    baselines = compute_baselines(df, 2023)

    # Keep/revert decision
    keep = should_keep(
        results["val_accuracy_2023"], prev_best_acc,
        results["log_loss"], prev_best_log_loss,
    )

    # Experiment 1 always kept unconditionally (no prior best to compare)
    if experiment_id == 1:
        keep = True

    # Save model if keeping
    model_path = None
    if keep:
        model_path = save_best_model(model, artifacts_dir=model_dir)
        logger.info("Model staged at %s (call POST /model/reload to go live)", model_path)
    else:
        logger.info("Experiment %d reverted (accuracy: %.4f vs prev best: %.4f)",
                     experiment_id, results["val_accuracy_2023"], prev_best_acc)

    # Always log experiment
    log_experiment(
        experiment_id=experiment_id,
        params=current_params,
        features_used=feature_cols,
        val_acc_2023=results["val_accuracy_2023"],
        val_acc_2022=results["val_accuracy_2022"],
        val_acc_2021=results["val_accuracy_2021"],
        baseline_home=baselines["always_home_accuracy"],
        baseline_record=baselines["better_record_accuracy"],
        log_loss_val=results["log_loss"],
        brier_score_val=results["brier_score"],
        shap_top5=results["shap_top5"],
        keep=keep,
        hypothesis="Automated retrain via pipeline",
        prev_best_acc=prev_best_acc,
        model_path=model_path,
        jsonl_path=experiments_path,
    )

    logger.info("Experiment %d logged. Decision: %s", experiment_id, "KEEP" if keep else "REVERT")
    return keep


def generate_current_predictions(engine, model_path, experiments_path):
    """Step 4: Generate predictions for the current week.

    Uses the staged model (or existing best model) to generate predictions.
    """
    from api.config import get_confidence_tier
    from models.predict import (
        detect_current_week,
        generate_predictions,
        get_best_experiment,
        load_best_model,
    )

    # Load model
    model = load_best_model(model_path)

    # Get best experiment for model_id
    best_exp = get_best_experiment(experiments_path)
    model_id = best_exp["experiment_id"] if best_exp else None

    # Detect current week
    current = detect_current_week(engine)
    if current is None:
        logger.info("Offseason detected -- skipping prediction generation")
        return

    season, week = current
    logger.info("Generating predictions for season %d, week %d...", season, week)

    predictions = generate_predictions(
        model, season, week, engine, get_confidence_tier, model_id=model_id,
    )

    logger.info("Generated %d predictions", len(predictions))


def run_pipeline():
    """Orchestrate the weekly refresh pipeline.

    Steps:
    1. ingest_new_data -- FATAL: failure stops pipeline
    2. recompute_features -- FATAL: failure stops pipeline
    3. retrain_and_stage -- NON-FATAL: failure logged, continues to step 4
    4. generate_current_predictions -- failure logged
    """
    start = datetime.now(timezone.utc).isoformat()
    logger.info("Pipeline started at %s", start)

    # Read configuration from env vars
    engine = get_engine()
    model_path = os.environ.get("MODEL_PATH", "models/artifacts/best_model.json")
    experiments_path = os.environ.get("EXPERIMENTS_PATH", "models/experiments.jsonl")
    model_dir = os.path.dirname(model_path)

    # Step 1: Ingest (fatal)
    try:
        ingest_new_data(engine)
    except Exception:
        logger.exception("Step 1 FAILED (fatal): ingest_new_data")
        return

    # Step 2: Recompute features (fatal)
    try:
        recompute_features(engine)
    except Exception:
        logger.exception("Step 2 FAILED (fatal): recompute_features")
        return

    # Step 3: Retrain (non-fatal)
    try:
        retrain_and_stage(engine, experiments_path, model_dir)
    except Exception:
        logger.exception("Step 3 FAILED (non-fatal): retrain_and_stage -- continuing to predictions")

    # Step 4: Generate predictions
    try:
        generate_current_predictions(engine, model_path, experiments_path)
    except Exception:
        logger.exception("Step 4 FAILED: generate_current_predictions")

    end = datetime.now(timezone.utc).isoformat()
    logger.info("Pipeline finished at %s", end)
