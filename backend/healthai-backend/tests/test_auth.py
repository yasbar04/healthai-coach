"""Tests for /auth endpoints."""

import pytest
from fastapi.testclient import TestClient


VALID_USER = {"email": "auth_test@example.com", "password": "Secure1!", "plan": "freemium"}


def test_register_success(client: TestClient):
    resp = client.post("/auth/register", json=VALID_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "plan" in data


def test_register_duplicate_email(client: TestClient):
    client.post("/auth/register", json=VALID_USER)
    resp = client.post("/auth/register", json=VALID_USER)
    assert resp.status_code == 409


def test_login_success(client: TestClient):
    client.post("/auth/register", json={**VALID_USER, "email": "login_test@example.com"})
    resp = client.post("/auth/login", json={"email": "login_test@example.com", "password": "Secure1!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient):
    client.post("/auth/register", json={**VALID_USER, "email": "badpw@example.com"})
    resp = client.post("/auth/login", json={"email": "badpw@example.com", "password": "WrongPassword!"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "Test123!"})
    assert resp.status_code == 401


def test_register_invalid_email(client: TestClient):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "Test123!", "plan": "freemium"})
    assert resp.status_code == 422


def test_me_unauthenticated(client: TestClient):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_me_authenticated(client: TestClient, auth_headers: dict):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert "plan" in data
