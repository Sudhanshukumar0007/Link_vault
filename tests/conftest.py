import pytest_asyncio
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from asgi_lifespan import LifespanManager
import os
os.environ["APP_ENV"] = "test"
from app.main import app
from app.db.base import Base
from app.db.session import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/linkvault_test"

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE clicks, links, workspace_members, workspaces, refresh_tokens, users RESTART IDENTITY CASCADE"))

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
@pytest_asyncio.fixture
async def auth_headers(client):
    import uuid
    unique_email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
    
    register_resp = await client.post("/api/v1/auth/register", json={
        "name": "Auth User",
        "email": unique_email,
        "password": "testpass123"
    })
    assert register_resp.status_code == 200, f"Register failed: {register_resp.text}"

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": "testpass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}