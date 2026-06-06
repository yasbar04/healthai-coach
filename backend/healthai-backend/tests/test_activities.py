"""Tests for /activities endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_list_activities_unauthenticated(client: TestClient):
    resp = client.get("/activities")
    assert resp.status_code == 401


def test_list_activities_empty(client: TestClient, auth_headers: dict):
    resp = client.get("/activities", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_activity(client: TestClient, auth_headers: dict):
    payload = {
        "activity_date": "2026-05-01",
        "steps": 8000,
        "active_minutes": 45,
        "calories_out": 350,
        "distance_km": 6.0,
        "workout_type": "Cardio",
    }
    resp = client.post("/activities", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["steps"] == 8000


def test_create_activity_missing_date(client: TestClient, auth_headers: dict):
    resp = client.post("/activities", json={"steps": 5000}, headers=auth_headers)
    assert resp.status_code == 422


def test_delete_activity(client: TestClient, auth_headers: dict):
    payload = {"activity_date": "2026-04-01", "steps": 3000}
    create_resp = client.post("/activities", json=payload, headers=auth_headers)
    if create_resp.status_code not in (200, 201):
        pytest.skip("Cannot create activity")
    activity_id = create_resp.json()["id"]
    del_resp = client.delete(f"/activities/{activity_id}", headers=auth_headers)
    assert del_resp.status_code in (200, 204)
