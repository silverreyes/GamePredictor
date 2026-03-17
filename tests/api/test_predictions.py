"""Tests for /api/predictions/* endpoints."""


def test_get_week_predictions(client):
    """GET /api/predictions/week/1?season=2024 returns 200 with predictions."""
    response = client.get("/api/predictions/week/1", params={"season": 2024})
    assert response.status_code == 200
    data = response.json()
    assert data["season"] == 2024
    assert data["week"] == 1
    assert data["status"] == "ok"
    assert isinstance(data["predictions"], list)


def test_week_default_season(client):
    """GET /api/predictions/week/1 without season defaults to max season (2024)."""
    response = client.get("/api/predictions/week/1")
    assert response.status_code == 200
    data = response.json()
    assert data["season"] == 2024


def test_current_week(client):
    """GET /api/predictions/current returns predictions for auto-detected week."""
    response = client.get("/api/predictions/current")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_offseason(offseason_client):
    """GET /api/predictions/current returns offseason status when no unplayed games."""
    response = offseason_client.get("/api/predictions/current")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "offseason"
    assert data["predictions"] == []


def test_history(client):
    """GET /api/predictions/history returns predictions with outcomes and summary."""
    response = client.get("/api/predictions/history")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "summary" in data
    assert isinstance(data["predictions"], list)


def test_history_summary(client):
    """Summary contains correct/total/accuracy fields with valid values."""
    response = client.get("/api/predictions/history")
    data = response.json()
    summary = data["summary"]
    assert "correct" in summary
    assert "total" in summary
    assert "accuracy" in summary
    # With our sample data: 1 correct out of 2 total
    assert summary["total"] == 2
    assert summary["correct"] == 1
    assert summary["accuracy"] == pytest.approx(0.5)


def test_history_filters(client):
    """History with ?team=BAL returns only games involving BAL."""
    response = client.get(
        "/api/predictions/history", params={"team": "BAL"}
    )
    assert response.status_code == 200
    data = response.json()
    for pred in data["predictions"]:
        assert "BAL" in (pred["home_team"], pred["away_team"])


# Import pytest for approx
import pytest
