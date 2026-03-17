"""Tests for GET /api/health endpoint."""


def test_health(client):
    """GET /api/health returns 200 with {"status": "ok"}."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
