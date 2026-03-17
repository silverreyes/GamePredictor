"""Tests for GET /api/experiments endpoint."""


def test_list_experiments(client):
    """GET /api/experiments returns 200 with list of experiment dicts."""
    response = client.get("/api/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["experiment_id"] == 1


def test_experiments_structure(client):
    """Response entries have all required fields."""
    response = client.get("/api/experiments")
    data = response.json()
    entry = data[0]
    required_fields = [
        "experiment_id",
        "timestamp",
        "params",
        "features",
        "val_accuracy_2023",
        "keep",
        "hypothesis",
    ]
    for field in required_fields:
        assert field in entry, f"Missing field: {field}"
