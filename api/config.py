"""API configuration and settings."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""

    RELOAD_TOKEN: str = os.environ.get("RELOAD_TOKEN", "")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    MODEL_PATH: str = os.environ.get("MODEL_PATH", "models/artifacts/best_model.json")
    EXPERIMENTS_PATH: str = os.environ.get("EXPERIMENTS_PATH", "models/experiments.jsonl")

    # Confidence tier thresholds (configurable, not hardcoded per CONTEXT.md)
    CONFIDENCE_HIGH: float = float(os.environ.get("CONFIDENCE_HIGH", "0.65"))
    CONFIDENCE_MEDIUM: float = float(os.environ.get("CONFIDENCE_MEDIUM", "0.55"))

    # CORS origins for React dashboard (Phase 5)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


settings = Settings()


def get_confidence_tier(confidence: float) -> str:
    """Map raw confidence score to tier label.

    Thresholds are configurable via Settings. Default:
    - high: >= 0.65
    - medium: >= 0.55
    - low: < 0.55

    Args:
        confidence: Raw confidence value (0.5 to 1.0).

    Returns:
        One of "high", "medium", "low".
    """
    if confidence >= settings.CONFIDENCE_HIGH:
        return "high"
    elif confidence >= settings.CONFIDENCE_MEDIUM:
        return "medium"
    else:
        return "low"
