"""Prediction generation pipeline.

Generates pre-computed predictions from the trained model and stores them
in the predictions table. Prediction logic lives here (not in api/) per
CONTEXT.md decision: keeping prediction code with model code.

Functions:
    load_best_model: Load XGBoost model from best_model.json artifact.
    get_best_experiment: Parse experiments.jsonl for the best kept experiment.
    detect_current_week: Data-driven current week detection from schedule.
    generate_predictions: Build features, run inference, store predictions.
"""

import json
import os

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from data.db import get_engine, get_table
from features.build import build_game_features


def load_best_model(path: str = "models/artifacts/best_model.json") -> XGBClassifier:
    """Load XGBoost model from the best model artifact.

    Args:
        path: Path to the saved XGBoost JSON model file.

    Returns:
        Loaded XGBClassifier ready for inference.

    Raises:
        FileNotFoundError: If the model file does not exist at the given path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model file not found at '{path}'. "
            "Run the training pipeline first to generate a model artifact."
        )
    model = XGBClassifier()
    model.load_model(path)
    return model


def get_best_experiment(jsonl_path: str = "models/experiments.jsonl") -> dict | None:
    """Parse experiments.jsonl for the best kept experiment.

    Finds the experiment entry with keep=True and the highest val_accuracy_2023.

    Args:
        jsonl_path: Path to the experiments JSONL log file.

    Returns:
        The full experiment dict (experiment_id, timestamp, params, features,
        val_accuracy_2023, baselines, hypothesis, etc.), or None if no kept
        experiments exist.

    Raises:
        FileNotFoundError: If the JSONL file does not exist.
    """
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(
            f"Experiments file not found at '{jsonl_path}'. "
            "Run at least one experiment first."
        )

    best = None
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("keep"):
                if best is None or entry["val_accuracy_2023"] > best["val_accuracy_2023"]:
                    best = entry

    if best is not None:
        # Normalize model_path: experiments.jsonl may contain Windows backslashes
        # (e.g., "models/artifacts\\model_exp005.json") which break on Linux.
        best["model_path"] = best.get("model_path", "").replace("\\", "/")

    return best


def detect_current_week(engine) -> tuple[int, int] | None:
    """Data-driven current week detection from schedule.

    Queries the schedules table for the earliest regular-season week in the
    latest season where home_score IS NULL (unplayed game).

    Args:
        engine: SQLAlchemy engine connected to the database.

    Returns:
        Tuple of (current_season, current_week) as Python ints, or None
        if all games have been played (offseason).
    """
    season_query = "SELECT MAX(season) as current_season FROM schedules WHERE game_type = 'REG'"
    season_result = pd.read_sql(season_query, engine)
    current_season = season_result["current_season"].iloc[0]

    if current_season is None:
        return None

    current_season = int(current_season)

    week_query = """
    SELECT MIN(week) as current_week
    FROM schedules
    WHERE season = %(season)s
      AND game_type = 'REG'
      AND home_score IS NULL
    """
    week_result = pd.read_sql(week_query, engine, params={"season": current_season})
    current_week = week_result["current_week"].iloc[0]

    if current_week is None:
        return None  # Offseason: all games played

    return (current_season, int(current_week))


def _get_team_rolling_features(features_df: pd.DataFrame, team: str) -> dict:
    """Extract a team's most recent rolling features from the feature matrix.

    Looks up the team in the home-perspective feature DataFrame (where the team
    may appear as either home_team or away_team) and returns the rolling stats
    from their most recent completed game.

    CRITICAL PREFIX FLIP: If the team appeared as home_team in the most recent
    row, their stats are in home_rolling_* columns. If the team appeared as
    away_team, their stats are in away_rolling_* columns. Both sets contain
    THAT team's stats -- the prefix indicates the team's role in that game.

    Args:
        features_df: Feature DataFrame from build_game_features() with completed
            games only (no NaN rolling features).
        team: Three-letter team abbreviation (e.g., "KC", "BUF").

    Returns:
        Dict with unprefixed keys (e.g., "rolling_off_epa_per_play") so the
        caller can re-prefix as home_rolling_* or away_rolling_* for the
        target game.

    Raises:
        ValueError: If no rows are found for the team (team hasn't played
            any games yet this season).
    """
    # Find all rows where this team appears as home or away
    team_rows = features_df[
        (features_df["home_team"] == team) | (features_df["away_team"] == team)
    ]

    if team_rows.empty:
        raise ValueError(
            f"No completed games found for team '{team}' in the feature matrix. "
            "The team may not have played any games yet this season."
        )

    # Take the most recent game (highest week)
    latest = team_rows.loc[team_rows["week"].idxmax()]

    # Determine which prefix has this team's stats
    rolling_cols = [c for c in features_df.columns if c.startswith("home_rolling_")]
    unprefixed = {}

    if latest["home_team"] == team:
        # Team was home -- their stats are in home_rolling_* columns
        for col in rolling_cols:
            key = col.replace("home_", "")  # "home_rolling_X" -> "rolling_X"
            unprefixed[key] = latest[col]
    else:
        # Team was away -- their stats are in away_rolling_* columns
        for col in rolling_cols:
            away_col = col.replace("home_rolling_", "away_rolling_")
            key = col.replace("home_", "")  # "home_rolling_X" -> "rolling_X"
            unprefixed[key] = latest[away_col]

    return unprefixed


def generate_predictions(
    model: XGBClassifier,
    season: int,
    week: int,
    engine,
    confidence_tier_fn,
    model_id: int | None = None,
) -> list[dict]:
    """Generate predictions for a specific week and store in the predictions table.

    Builds features from all completed games in the season to get rolling stats,
    then constructs feature vectors for unplayed games in the target week by
    looking up each team's most recent rolling features.

    Args:
        model: Loaded XGBClassifier for inference.
        season: Season year (e.g., 2024).
        week: Week number to predict (e.g., 5).
        engine: SQLAlchemy engine connected to the database.
        confidence_tier_fn: Callable that maps a confidence float (0.5-1.0)
            to a tier label ("high", "medium", "low"). Passed in from
            api/config.py to avoid circular imports.
        model_id: Optional experiment_id for auditing (stored in predictions
            table but not exposed in API response).

    Returns:
        List of prediction dicts (one per game) that were upserted into the
        predictions table.
    """
    # Step 1: Build features for all completed games in the season
    features_df = build_game_features(seasons=[season])

    # Filter to only completed games (have rolling features, not NaN)
    rolling_cols = [c for c in features_df.columns if c.startswith("home_rolling_")]
    completed = features_df.dropna(subset=rolling_cols)

    # Step 2: Get schedule info for unplayed games in the target week
    schedule_query = """
    SELECT game_id, season, week, gameday, home_team, away_team,
           home_rest, away_rest, div_game
    FROM schedules
    WHERE season = %(season)s AND week = %(week)s
      AND game_type = 'REG' AND home_score IS NULL
    """
    unplayed = pd.read_sql(schedule_query, engine, params={"season": season, "week": week})

    if unplayed.empty:
        return []

    # Step 3: Build feature vectors for each unplayed game
    feature_names = model.get_booster().feature_names
    rows = []

    for _, game in unplayed.iterrows():
        home_team = game["home_team"]
        away_team = game["away_team"]

        # Get each team's latest rolling features
        home_feats = _get_team_rolling_features(completed, home_team)
        away_feats = _get_team_rolling_features(completed, away_team)

        # Re-prefix: rolling_X -> home_rolling_X / away_rolling_X
        game_features = {}
        for key, val in home_feats.items():
            game_features[f"home_{key}"] = val
        for key, val in away_feats.items():
            game_features[f"away_{key}"] = val

        # Add situational features from schedule
        game_features["home_rest"] = game["home_rest"]
        game_features["away_rest"] = game["away_rest"]
        game_features["div_game"] = game["div_game"]

        rows.append(game_features)

    # Step 4: Build DataFrame with correct column ordering from model
    X = pd.DataFrame(rows)[feature_names]

    # Step 5: Run inference
    proba = model.predict_proba(X)[:, 1]  # P(home_win)

    # Step 6: Compute predicted winner, confidence, and tier
    records = []
    for i, (_, game) in enumerate(unplayed.iterrows()):
        home_prob = float(proba[i])

        if home_prob >= 0.5:
            predicted_winner = game["home_team"]
            confidence = home_prob
        else:
            predicted_winner = game["away_team"]
            confidence = 1.0 - home_prob

        # Convert numpy/pandas types to Python native
        game_date = game["gameday"]
        if pd.notna(game_date):
            game_date = str(game_date)
        else:
            game_date = None

        record = {
            "game_id": str(game["game_id"]),
            "season": int(game["season"]),
            "week": int(game["week"]),
            "game_date": game_date,
            "home_team": str(game["home_team"]),
            "away_team": str(game["away_team"]),
            "predicted_winner": str(predicted_winner),
            "confidence": float(confidence),
            "confidence_tier": confidence_tier_fn(confidence),
            "model_id": model_id,
            "actual_winner": None,
            "correct": None,
        }
        records.append(record)

    # Step 7: Upsert into predictions table
    if records:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        predictions_table = get_table("predictions", engine)
        stmt = pg_insert(predictions_table).values(records)
        update_columns = {
            col: stmt.excluded[col]
            for col in [
                "season", "week", "game_date", "home_team", "away_team",
                "predicted_winner", "confidence", "confidence_tier",
                "model_id", "actual_winner", "correct",
            ]
        }
        upsert = stmt.on_conflict_do_update(
            index_elements=["game_id"],
            set_=update_columns,
        )
        with engine.begin() as conn:
            conn.execute(upsert)

    return records
