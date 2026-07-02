import pytest

async def test_redirect_valid_slug(client,auth_headers):
    await client.post("/api/v1/links/",json={
        "original_url":"https://github.com",
        "custom_slug":"testdirect",
        "expires_at":None
    },headers = auth_headers)

    response = await client.get("/testdirect", follow_redirects=False)
    assert response.status_code==307
    assert response.headers["location"] == "https://github.com/"

async def test_redirect_invalid_slug(client):
    response = await client.get("/nonexistentslug123", follow_redirects=False)
    assert response.status_code == 404