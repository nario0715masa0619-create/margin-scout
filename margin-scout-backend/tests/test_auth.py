import pytest

def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepassword"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user_id" in data
    assert data["email"] == "new@example.com"

def test_register_duplicate_email(client, user_a):
    res = client.post("/api/v1/auth/register", json={
        "email": "user_a@example.com",
        "username": "othername",
        "password": "securepassword"
    })
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]

def test_login_success(client, user_a):
    res = client.post("/api/v1/auth/login", json={
        "email": "user_a@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_invalid_password(client, user_a):
    res = client.post("/api/v1/auth/login", json={
        "email": "user_a@example.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_login_user_not_found(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "notfound@example.com",
        "password": "password123"
    })
    assert res.status_code == 401

def test_refresh_token_success(client, user_a):
    from app.security.jwt import JWTHandler
    refresh = JWTHandler.create_refresh_token(user_a.id)
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_refresh_invalid_token(client):
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
    assert res.status_code == 401

def test_me_endpoint_with_token(client, auth_headers_a):
    res = client.get("/api/v1/auth/me", headers=auth_headers_a)
    assert res.status_code == 200
    assert res.json()["email"] == "user_a@example.com"

def test_me_endpoint_without_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
