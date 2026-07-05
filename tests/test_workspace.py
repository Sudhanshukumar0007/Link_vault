import uuid

async def test_create_workspace(client, auth_headers):
    response = await client.post("/api/v1/workspaces/", json={
        "name": "Test Workspace"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Workspace"
    assert data["plan"] == "free"

async def test_create_workspace_unauthenticated(client):
    response = await client.post("/api/v1/workspaces/", json={
        "name": "Test Workspace"
    })
    assert response.status_code == 401

async def test_list_workspaces(client, auth_headers):
    await client.post("/api/v1/workspaces/", json={
        "name": "My Workspace"
    }, headers=auth_headers)
    response = await client.get("/api/v1/workspaces/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

async def test_get_workspace(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Get Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]
    response = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == workspace_id

async def test_get_workspace_not_member(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Private Workspace"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]

    unique_email = f"other_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "Other User",
        "email": unique_email,
        "password": "testpass123"
    })
    login = await client.post("/api/v1/auth/login",
        data={"username": unique_email, "password": "testpass123"}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=other_headers)
    assert response.status_code == 404

async def test_invite_member(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Invite Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]

    invited_email = f"invited_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "Invited User",
        "email": invited_email,
        "password": "testpass123"
    })
    response = await client.post(f"/api/v1/workspaces/{workspace_id}/members", json={
        "email": invited_email,
        "role": "editor"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "editor"
    assert response.json()["user_email"] == invited_email

async def test_invite_nonexistent_user(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Invite Fail Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]
    response = await client.post(f"/api/v1/workspaces/{workspace_id}/members", json={
        "email": "nobody@nowhere.com",
        "role": "viewer"
    }, headers=auth_headers)
    assert response.status_code == 404

async def test_list_members(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Members Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]
    response = await client.get(f"/api/v1/workspaces/{workspace_id}/members", headers=auth_headers)
    assert response.status_code == 200
    members = response.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"

async def test_remove_member(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Remove Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]

    remove_email = f"remove_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "To Remove",
        "email": remove_email,
        "password": "testpass123"
    })
    invite = await client.post(f"/api/v1/workspaces/{workspace_id}/members", json={
        "email": remove_email,
        "role": "viewer"
    }, headers=auth_headers)
    user_id = invite.json()["user_id"]
    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{user_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Member removed successfully"

async def test_non_owner_cannot_invite(client, auth_headers):
    create = await client.post("/api/v1/workspaces/", json={
        "name": "Permission Test"
    }, headers=auth_headers)
    workspace_id = create.json()["id"]

    editor_email = f"editor_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "Editor",
        "email": editor_email,
        "password": "testpass123"
    })
    await client.post(f"/api/v1/workspaces/{workspace_id}/members", json={
        "email": editor_email,
        "role": "editor"
    }, headers=auth_headers)
    login = await client.post("/api/v1/auth/login",
        data={"username": editor_email, "password": "testpass123"}
    )
    editor_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    third_email = f"third_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "Third",
        "email": third_email,
        "password": "testpass123"
    })
    response = await client.post(f"/api/v1/workspaces/{workspace_id}/members", json={
        "email": third_email,
        "role": "viewer"
    }, headers=editor_headers)
    assert response.status_code == 403