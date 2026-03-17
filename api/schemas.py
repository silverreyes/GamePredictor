"""Pydantic response models for all API endpoints."""

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    """Single game prediction."""

    game_id: str
    season: int
    week: int
    game_date: str | None = None
    home_team: str
    away_team: str
    predicted_winner: str
    confidence: float
    confidence_tier: str
    actual_winner: str | None = None
    correct: bool | None = None


class HistorySummary(BaseModel):
    """Summary statistics for prediction history."""

    correct: int
    total: int
    accuracy: float | None = None


class PredictionHistoryResponse(BaseModel):
    """Response for GET /predictions/history."""

    predictions: list[PredictionResponse]
    summary: HistorySummary


class WeekPredictionsResponse(BaseModel):
    """Response for GET /predictions/week/{week} and /predictions/current."""

    season: int
    week: int
    status: str = "ok"  # "ok" or "offseason"
    predictions: list[PredictionResponse]


class ModelInfoResponse(BaseModel):
    """Response for GET /model/info."""

    experiment_id: int
    training_date: str
    val_accuracy_2023: float
    feature_count: int
    hypothesis: str
    baseline_always_home: float
    baseline_better_record: float


class ShapFeature(BaseModel):
    """Single SHAP feature importance entry."""

    feature: str
    importance: float


class ExperimentResponse(BaseModel):
    """Single experiment from experiments.jsonl."""

    experiment_id: int
    timestamp: str
    params: dict
    features: list[str]
    val_accuracy_2023: float
    val_accuracy_2022: float
    val_accuracy_2021: float
    baseline_always_home: float
    baseline_better_record: float
    log_loss: float
    brier_score: float
    shap_top5: list[ShapFeature]
    keep: bool
    hypothesis: str
    prev_best_acc: float
    model_path: str | None = None


class ReloadResponse(BaseModel):
    """Response for POST /model/reload."""

    status: str
    experiment_id: int
    val_accuracy_2023: float
    predictions_generated: int


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: str
