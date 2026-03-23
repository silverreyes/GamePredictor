"""Spread prediction endpoints."""

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_app_state
from api.schemas import SpreadPredictionResponse, SpreadWeekResponse, SpreadHistoryResponse

router = APIRouter()


@router.get(
    "/api/predictions/spreads/week/{season}/{week}",
    response_model=SpreadWeekResponse,
)
async def get_spread_predictions(
    season: int,
    week: int,
    state: dict = Depends(get_app_state),
):
    """Return spread predictions for a specific week.

    API-02: GET /api/predictions/spreads/week/{season}/{week} returns
    spread predictions per game for a given week.
    Returns 503 if spread model is not loaded.
    """
    if state.get("spread_model") is None:
        raise HTTPException(status_code=503, detail="Spread model not loaded")

    engine = state["engine"]
    query = """
        SELECT game_id, season, week, game_date, home_team, away_team,
               predicted_spread, predicted_winner,
               actual_spread, actual_winner, correct
        FROM spread_predictions
        WHERE season = %(season)s AND week = %(week)s
        ORDER BY game_date, game_id
    """
    df = pd.read_sql(query, engine, params={"season": season, "week": week})

    predictions = []
    for _, row in df.iterrows():
        predictions.append(
            SpreadPredictionResponse(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                game_date=(
                    str(row["game_date"]) if pd.notna(row["game_date"]) else None
                ),
                home_team=row["home_team"],
                away_team=row["away_team"],
                predicted_spread=float(row["predicted_spread"]),
                predicted_winner=row["predicted_winner"],
                actual_spread=(
                    float(row["actual_spread"])
                    if pd.notna(row.get("actual_spread"))
                    else None
                ),
                actual_winner=(
                    row["actual_winner"]
                    if pd.notna(row.get("actual_winner"))
                    else None
                ),
                correct=(
                    bool(row["correct"])
                    if pd.notna(row.get("correct"))
                    else None
                ),
            )
        )

    return SpreadWeekResponse(
        season=season,
        week=week,
        status="ok",
        predictions=predictions,
    )


@router.get(
    "/api/predictions/spreads/history",
    response_model=SpreadHistoryResponse,
)
async def get_spread_history(
    season: int | None = Query(
        default=None, description="Filter by season. Defaults to current season."
    ),
    state: dict = Depends(get_app_state),
):
    """Return all completed spread predictions for a season.

    DASH-04: Provides per-game spread correct/incorrect data for
    computing agreement breakdown with classifier predictions.
    Returns 503 if spread model is not loaded.
    """
    if state.get("spread_model") is None:
        raise HTTPException(status_code=503, detail="Spread model not loaded")

    engine = state["engine"]

    # Default season = most recent season with spread predictions
    if season is None:
        result = pd.read_sql(
            "SELECT MAX(season) as max_season FROM spread_predictions",
            engine,
        )
        if result["max_season"].iloc[0] is None:
            return SpreadHistoryResponse(season=0, predictions=[])
        season = int(result["max_season"].iloc[0])

    query = """
        SELECT game_id, season, week, game_date, home_team, away_team,
               predicted_spread, predicted_winner,
               actual_spread, actual_winner, correct
        FROM spread_predictions
        WHERE season = %(season)s AND actual_winner IS NOT NULL
        ORDER BY week, game_date, game_id
    """
    df = pd.read_sql(query, engine, params={"season": season})

    predictions = []
    for _, row in df.iterrows():
        predictions.append(
            SpreadPredictionResponse(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                game_date=(
                    str(row["game_date"]) if pd.notna(row["game_date"]) else None
                ),
                home_team=row["home_team"],
                away_team=row["away_team"],
                predicted_spread=float(row["predicted_spread"]),
                predicted_winner=row["predicted_winner"],
                actual_spread=(
                    float(row["actual_spread"])
                    if pd.notna(row.get("actual_spread"))
                    else None
                ),
                actual_winner=(
                    row["actual_winner"]
                    if pd.notna(row.get("actual_winner"))
                    else None
                ),
                correct=(
                    bool(row["correct"])
                    if pd.notna(row.get("correct"))
                    else None
                ),
            )
        )

    return SpreadHistoryResponse(season=season, predictions=predictions)
