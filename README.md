# LinkVault

A URL shortener API built with FastAPI. Create short links, track click analytics, and manage team workspaces.

---

## Features

- **Link shortening** — Generate short slugs automatically or provide a custom one
- **Link expiry** — Set an optional expiry date/time on any link
- **Click tracking** — Every redirect is recorded asynchronously with device type, browser, and referrer
- **Analytics** — Per-link stats (daily clicks, device breakdown, browser breakdown, top referrers) over a configurable time window
- **Top links** — Ranked list of your most-clicked active links
- **Workspaces** — Create team workspaces, invite members by email, assign roles, remove members
- **JWT authentication** — Short-lived access tokens (15 min) with rotating refresh tokens (7 days)
- **Redis caching** — Redirect hot path served from Redis cache with automatic TTL
- **Rate limiting** — Per-IP request rate limiting with graceful Redis-failure fallback
- **Prometheus metrics** — Instrumented via `prometheus-fastapi-instrumentator`, scraped at `/metrics`
- **Health check** — `/health` endpoint reporting database and cache status
- **Structured logging** — Request/response logging with request IDs and durations via Loguru

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (async) |
| Database | PostgreSQL 16 via asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Cache | Redis 7 |
| Background tasks | Celery (Redis broker) |
| Migrations | Alembic |
| Auth | JWT (HS256) — python-jose |
| Password hashing | bcrypt via passlib |
| Runtime | Python 3.14, Uvicorn |
| Package manager | uv |
| Monitoring | Prometheus + Grafana |
| Logging | Loguru |

---

## API Endpoints

### Auth — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login with email + password, returns access and refresh tokens |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new token pair |
| `GET` | `/auth/me` | Get the current authenticated user's profile |

### Links — `/api/v1/links`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/links/` | Create a shortened link (optional custom slug, optional expiry) |
| `GET` | `/links/` | List your links (paginated with `limit` and `offset`) |
| `DELETE` | `/links/{link_id}` | Soft-delete a link (deactivates it, preserves history) |

### Redirect

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/{slug}` | Redirect to the original URL; returns 410 if expired, 404 if not found |

### Analytics — `/api/v1/analytics`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/links/{link_id}/stats` | Daily click chart, device, browser, and referrer breakdown for a link |
| `GET` | `/analytics/top-links` | Your top links ranked by total click count |

Query parameters for `/stats`:
- `period` — Number of days to look back, 1–90 (default: 7)

Query parameters for `/top-links`:
- `limit` — Number of results, 1–50 (default: 10)

### Workspaces — `/api/v1/workspaces`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/workspaces/` | Create a new workspace |
| `GET` | `/workspaces/` | List workspaces you own or are a member of |
| `GET` | `/workspaces/{workspace_id}` | Get a single workspace |
| `POST` | `/workspaces/{workspace_id}/members` | Invite a user to the workspace by email |
| `DELETE` | `/workspaces/{workspace_id}/members/{user_id}` | Remove a member from the workspace |
| `GET` | `/workspaces/{workspace_id}/members` | List workspace members (paginated) |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns database and cache status |
| `GET` | `/metrics` | Prometheus metrics endpoint |
| `GET` | `/docs` | Interactive Swagger UI (when DEBUG=true) |
| `GET` | `/redoc` | ReDoc API documentation |

---

## Getting Started

### Prerequisites

- Python 3.14+
- PostgreSQL 16
- Redis 7
- [uv](https://docs.astral.sh/uv/) package manager

### Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Sudhanshukumar0007/Link_vault.git
   cd Link_vault
   ```

2. **Copy and configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your database URL, Redis URL, and a strong SECRET_KEY
   ```

   Required variables:

   | Variable | Example |
   |----------|---------|
   | `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/linkvault` |
   | `REDIS_URL` | `redis://localhost:6379` |
   | `SECRET_KEY` | 32+ character random string |
   | `ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
   | `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
   | `APP_ENV` | `development` |
   | `DEBUG` | `true` |

3. **Install dependencies**

   ```bash
   uv sync
   ```

4. **Run database migrations**

   ```bash
   uv run alembic upgrade head
   ```

5. **Start the API server**

   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. **Start the Celery worker** (required for click analytics)

   ```bash
   uv run celery -A app.tasks.celery_app worker --loglevel=info
   ```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

## Docker Compose

To start PostgreSQL, Redis, Prometheus, and Grafana locally:

```bash
docker compose up -d
```

Services:

| Service | Port |
|---------|------|
| PostgreSQL | 5432 |
| Redis | 6379 |
| Prometheus | 9090 |
| Grafana | 3000 (admin / admin) |

---

## Running Tests

```bash
uv run pytest tests/ -v
```

Tests use a dedicated test database and run with real PostgreSQL and Redis. Ensure both are running before executing the suite.

---

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── auth.py          # Auth routes
│       ├── links.py         # Link CRUD routes
│       ├── redirect.py      # Redirect handler
│       ├── analytics.py     # Analytics routes
│       └── workspaces.py    # Workspace routes
├── core/
│   ├── config.py            # Settings (pydantic-settings)
│   ├── redis.py             # Redis client
│   ├── security.py          # JWT and password hashing
│   └── utils.py             # Slug generation, reserved slugs
├── db/
│   └── session.py           # Async SQLAlchemy session
├── middleware/
│   ├── logging.py           # Request/response logging
│   └── rate_limit.py        # IP-based rate limiting
├── models/                  # SQLAlchemy ORM models
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic layer
├── tasks/
│   ├── celery_app.py        # Celery app config
│   └── analytics.py        # Click recording task
└── main.py                  # App factory and lifespan
alembic/
└── versions/                # Database migrations
monitoring/
└── prometheus.yml           # Prometheus scrape config
tests/                       # Pytest async test suite
```

---

## Deployment

The project includes a `render.yaml` for one-click deployment to [Render](https://render.com) and a `Dockerfile` for container-based deployments.

Environment variables `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY` must be set in the deployment environment. `APP_ENV` should be set to `production` and `DEBUG` to `false`.

---

## License

MIT
