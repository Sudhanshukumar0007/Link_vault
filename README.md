# LinkVault

LinkVault is a FastAPI URL shortener API built as a production-readiness learning project. The current codebase supports user registration/login, authenticated short-link creation/listing/deletion, public redirects, Redis redirect caching, Celery click-count updates, Alembic migrations, Docker-based services, GitHub Actions, and Prometheus instrumentation.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy async
- Alembic
- Redis
- Celery
- Pydantic v2
- Prometheus FastAPI Instrumentator
- Docker / Docker Compose
- GitHub Actions
- Render deployment config

## Current Features

- `POST /api/v1/auth/register` - create a user
- `POST /api/v1/auth/login` - login with email/password and receive a JWT access token
- `POST /api/v1/links/` - create a short link
- `GET /api/v1/links/` - list the current user's active links
- `DELETE /api/v1/links/{link_id}` - soft-delete a link owned by the current user
- `GET /{slug}` - redirect to the original URL
- `GET /health` - basic app health response
- `/metrics` - Prometheus metrics endpoint

## Project Status

Implemented: core auth, link CRUD, redirects, Redis cache-aside, Celery click counter, migrations, tests, Docker support, CI skeleton.
>  Swagger UI is enabled for demo purposes. In a real production deployment this would be disabled.
Demo: https://link-vault-zbon.onrender.com/docs


## Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

Start required services:

```bash
docker compose up -d postgres redis
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

## Environment Variables

Required variables:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/linkvault
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_ENV=development
DEBUG=true
```

## Testing and Quality Checks

Expected local checks:

```bash
uv run ruff check .
uv run mypy app
uv run pytest tests/ -v
```

The current tests expect PostgreSQL and Redis to be available locally. The test database URL in `tests/conftest.py` is:

```text
postgresql+asyncpg://postgres:password@localhost:5432/linkvault_test
```

## Docker

The current `docker-compose.yml` starts supporting services:

- PostgreSQL on `5432`
- Redis on `6379`
- Prometheus on `9090`
- Grafana on `3000`

The API is started manually with `uv run uvicorn app.main:app --reload`. A future improvement is to add API and Celery worker services to Compose.

## Deployment

`render.yaml` configures a Docker-based Render web service. Required Render environment variables:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `APP_ENV=production`
- `DEBUG=false`

The Docker command runs Alembic migrations before starting Uvicorn.

## Roadmap

Short-term priorities:

- Fix Redis cache invalidation after link delete.
- Make redirects degrade gracefully when Redis/Celery are unavailable.
- Fix Python version mismatch between `pyproject.toml` and Docker.
- Fix CI database URL and test isolation.
- Add refresh tokens and `/auth/me`.
- Add password-protected links and expiry-aware cache TTL.

Long-term priorities:

- Real click analytics table and aggregation.
- Team workspaces and RBAC.
- API keys.
- Structured JSON logging with request IDs.
- DB/Redis/Celery health checks.
- Complete CI/CD pipeline.
