import pytest

async def test_register_success(client):
    response = await client.post("/api/v1/auth/register", json={
        "name": "Sudhanshu",
        "email": "sudhanshu@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "sudhanshu@test.com"
    assert data["name"] == "Sudhanshu"
    assert "hashed_password" not in data  

async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json={
        "name": "User One",
        "email": "duplicate@test.com",
        "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/register", json={
        "name": "User Two",
        "email": "duplicate@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "name": "Login User",
        "email": "login@test.com",
        "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login",
        data={"username": "login@test.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data  # add this
    assert data["token_type"] == "bearer"

async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "name": "Wrong Pass User",
        "email": "wrongpass@test.com",
        "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login",
        data={"username": "wrongpass@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

async def test_login_nonexistent_user(client):
    response = await client.post("/api/v1/auth/login",
        data={"username": "nobody@test.com", "password": "testpass123"}
    )
    assert response.status_code == 401
async def test_refresh_token(client):
    await client.post("/api/v1/auth/register", json={
        "name": "Refresh User",
        "email": "refresh@test.com",
        "password": "testpass123"
    })
    login = await client.post("/api/v1/auth/login",
        data={"username": "refresh@test.com", "password": "testpass123"}
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

async def test_me_endpoint(client, auth_headers):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "auth@example.com"
    assert "hashed_password" not in data