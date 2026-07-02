import pytest

async def test_create_link_unauthenticated(client):
    response = await client.post("/api/v1/links/",json={
        "original_url":"https://github.com/Sudhanshukumar0007",
        "custom_slug":None,
        "expires_at":None,
    })
    assert response.status_code==401

async def test_create_link_success(client,auth_headers):
    response = await client.post("/api/v1/links/",json={
        "original_url":"https://github.com/Sudhanshukumar0007",
        "custom_slug":None,
        "expires_at":None,
    },headers=auth_headers)
    assert response.status_code==200
    data = response.json()
    assert data["original_url"] == "https://github.com/Sudhanshukumar0007"
    assert data["click_count"]== 0
    assert data["is_active"] == True

async def create_link_custom_slug(client,auth_headers):
    response = client.post("/api/v1/links/",json={
        "original_url":"https://github.com",
        "custome_slug":"myslug",
        "expires_at":None
        },headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["slug"] == "myslug"
    
async def test_create_duplicate_slug(client,auth_headers):
    await client.post("/api/v1/links/",json={
        "original_url":"https://github.com",
        "custom_slug":"dupslug",
        "expires_at":None
    },headers=auth_headers)

    response = await client.post("/api/v1/links/",json={
        "original_url":"https://github.com",
        "custom_slug":"dupslug",
        "expires_at":None
    },headers=auth_headers)

    assert response.status_code == 400

async def test_get_links(client, auth_headers):
    await client.post("/api/v1/links/", json={
        "original_url": "https://github.com",
        "custom_slug": None,
        "expires_at": None
    }, headers=auth_headers)
    response = await client.get("/api/v1/links/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

async def test_delete_link(client,auth_headers):
    create = await client.post("/api/v1/links/",json={
        "original_url":"https://github.com",
        "custom_slug":"todelete",
        "expires_at":None
    },headers=auth_headers)
    link_id = create.json()["id"]
    response = await client.delete(f"/api/v1/links/{link_id}",headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Link deleted successfully"

async def test_delete_nonexistent_link(client, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/api/v1/links/{fake_id}", headers=auth_headers)
    assert response.status_code == 404
async def test_delete_other_users_link(client, auth_headers):
    # create link with auth_headers user
    create = await client.post("/api/v1/links/", json={
        "original_url": "https://github.com",
        "custom_slug": "otheruser",
        "expires_at": None
    }, headers=auth_headers)
    link_id = create.json()["id"]

    await client.post("/api/v1/auth/register", json={
        "name": "Hacker",
        "email": "hacker@test.com",
        "password": "testpass123"
    })
    login = await client.post("/api/v1/auth/login",
        data={"username": "hacker@test.com", "password": "testpass123"}
    )
    hacker_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.delete(f"/api/v1/links/{link_id}", headers=hacker_headers)
    assert response.status_code == 404  