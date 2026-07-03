# LinkVault

LinkVault is a FastAPI URL shortener API built as a production-readiness learning project. It covers the core backend pieces of a modern short-link service: JWT auth, refresh tokens, link management, public redirects, Redis caching, Celery-based click tracking, PostgreSQL persistence, Alembic migrations, Prometheus metrics, Docker support, CI, and Render deployment configuration.

This project is currently a portfolio/demo backend, not a finished production service. The codebase intentionally keeps known limitations visible while they are being fixed.

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

### Auth

- `POST /api/v1/auth/register` - create a user
- `POST /api/v1/auth/login` - login with email/password
- `POST /api/v1/auth/refresh` - rotate a refresh token and issue a new access token
- `GET /api/v1/auth/me` - return the authenticated user profile

### Links

- `POST /api/v1/links/` - create a short link
- `GET /api/v1/links/?limit=10&offset=0` - list the current user's active links
- `DELETE /api/v1/links/{link_id}` - soft-delete a link owned by the current user
- Custom slug validation with length and character checks
- Reserved slug protection for application routes

### Redirects And Analytics

- `GET /{slug}` - redirect to the original URL
- Redis cache-aside lookup for redirects
- Celery task for click recording
- Atomic click-count increments
- Click analytics table with device, browser, referrer, and timestamp data
- `GET /api/v1/analytics/links/{link_id}/stats` - per-link analytics
- `GET /api/v1/analytics/top-links` - top links for the authenticated user

### Operations

- `GET /health` - app, database, and Redis health response
- `/metrics` - Prometheus metrics endpoint
- Alembic migrations
- Dockerfile for deployment
- Docker Compose for local dependencies
- GitHub Actions CI skeleton
- Render deployment config

## Project Status

Implemented:

- Core auth with access and refresh tokens
- Authenticated link CRUD
- Public redirects
- Redis redirect caching
- Celery click tracking
- Basic analytics API
- PostgreSQL models and Alembic migrations
- Prometheus metrics
- Docker/Render deployment setup
- Basic automated tests

Still in progress:

- Redis/Celery outage hardening
- Expiry-aware redirect cache TTL
- Migration safety for existing production data
- Stronger test isolation
- Password-protected links
- API keys
- Workspaces and RBAC
- Structured JSON logging with request IDs

Swagger UI is enabled for demo purposes. In a stricter production deployment, `/docs` and `/redoc` should usually be disabled or protected.

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

## Testing And Quality Checks

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

If developing from WSL, run `uv` and the test commands from WSL. Do not share the same `.venv` between Windows PowerShell and WSL.

## Docker

The current `docker-compose.yml` starts supporting services:

- PostgreSQL on `5432`
- Redis on `6379`
- Prometheus on `9090`
- Grafana on `3000`

The API is started manually with:

```bash
uv run uvicorn app.main:app --reload
```

A future improvement is to add API and Celery worker services to Compose.

## Deployment

`render.yaml` configures a Docker-based Render web service. Required Render environment variables:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `APP_ENV=production`
- `DEBUG=false`

The Docker command runs Alembic migrations before starting Uvicorn.

## Known Limitations

- Redis is still too tightly coupled to startup and some request paths.
- Redirect cache writes and delete cache invalidation need stronger failure handling.
- Expired links need cache TTLs based on their actual expiration time.
- Refresh-token rotation needs stronger concurrency protection.
- Test setup still depends on real PostgreSQL and Redis.
- Tests currently use `Base.metadata.create_all`, so migration correctness needs separate verification.
- Compose does not yet run the API or Celery worker.
- Workspace/team support is intentionally deferred.

## Roadmap

Short-term priorities:

- Make Redis non-fatal for startup, redirects, deletes, and rate limiting.
- Add expiry-aware Redis TTL for redirects.
- Repair unsafe migrations before using them on existing production data.
- Improve test isolation and add Redis/Celery failure tests.
- Add password-protected links.
- Add API request/response examples to the README.

Long-term priorities:

- Workspaces and RBAC.
- API keys.
- Structured JSON logging with request IDs.
- Full Docker Compose stack with API and worker services.
- Stronger analytics aggregation.
- Complete CI/CD pipeline.
