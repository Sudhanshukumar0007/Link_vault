# LinkVault 🔗

A production-grade URL shortener and analytics API built with FastAPI. Built as a learning project to cover every layer of real backend engineering — from async database sessions to Redis caching, Celery background tasks, CI/CD pipelines, and observability dashboards.

**Live API:** https://link-vault-zbon.onrender.com/docs

---

## What it does

- Shorten any URL to a custom or auto-generated slug
- Redirect users via sub-100ms cached redirects
- Track every click with device, browser, and referrer analytics
- Manage links in personal or team workspaces
- Authenticate with JWT access + refresh token rotation

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Cache | Redis (cache-aside pattern) |
| Task Queue | Celery + Redis broker |
| Auth | JWT (HS256) + bcrypt + refresh token rotation |
| Observability | Prometheus + Grafana |
| Logging | Loguru (structured JSON with request IDs) |
| Testing | pytest + pytest-asyncio + httpx |
| CI/CD | GitHub Actions → Render (deploy after CI pass) |
| Containerization | Docker + Docker Compose |

---

## Architecture

```
Client
  │
  ▼
FastAPI (Uvicorn)
  │         │
  │         ▼
  │       Redis
  │       ├── Cache-aside for redirects (slug → URL)
  │       ├── Rate limiting (sliding window)
  │       └── Celery broker
  │
  ▼
PostgreSQL
  ├── users
  ├── links
  ├── clicks (analytics events)
  ├── workspaces + workspace_members
  └── refresh_tokens
  
Celery Worker
  └── record_click task (async analytics)
  
Prometheus + Grafana
  └── RED metrics dashboard (Rate, Errors, Duration)
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register with name, email, password |
| POST | `/api/v1/auth/login` | Login → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| GET | `/api/v1/auth/me` | Current user profile |

### Links
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/links/` | Create short link (optional custom slug, expiry) |
| GET | `/api/v1/links/` | List user's links (paginated) |
| DELETE | `/api/v1/links/{id}` | Soft delete + cache invalidation |

### Redirect
| Method | Endpoint | Description |
|---|---|---|
| GET | `/{slug}` | Redirect → fires async click tracking |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/links/{id}/stats` | Daily clicks, devices, browsers, referrers |
| GET | `/api/v1/analytics/top-links` | Most clicked links |

### Workspaces
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/workspaces/` | Create workspace |
| GET | `/api/v1/workspaces/` | List user's workspaces |
| GET | `/api/v1/workspaces/{id}` | Get workspace |
| POST | `/api/v1/workspaces/{id}/members` | Invite member (owner only) |
| GET | `/api/v1/workspaces/{id}/members` | List members with user info |
| DELETE | `/api/v1/workspaces/{id}/members/{user_id}` | Remove member |

---

## Key Engineering Decisions

### Cache-aside on redirects
Every redirect checks Redis first. On cache miss, DB is queried and result cached for 24h (or until link expiry). On cache hit, response is immediate with no DB query. Redis failure falls back to DB gracefully.

### Fire-and-forget click tracking
Redirects return immediately. Click recording (DB write + user-agent parse) happens in a Celery background task. Users never wait for analytics.

### Refresh token rotation
Every `/refresh` call atomically revokes the old token and issues a new pair. Concurrent refresh calls are handled safely — only one wins at the DB level.

### Sliding window rate limiting
Redis sorted sets track request timestamps per IP. Old entries are pruned atomically on each request. Fails open (allows request) if Redis is down.

### Soft deletes with cache invalidation
Links are never hard deleted. `is_active = False` is set first, then the Redis cache key is invalidated best-effort. DB is always the source of truth.

---

## Local Setup

**Prerequisites:** Docker, uv (Python package manager)

```bash
# Clone
git clone https://github.com/Sudhanshukumar0007/Link_vault
cd Link_vault

# Install dependencies
uv sync

# Start infrastructure
docker compose up -d

# Copy env
cp .env.example .env
# Fill in .env values

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
uv run celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

Open http://localhost:8000/docs for Swagger UI.

---

## Running Tests

```bash
# Create test DB
psql -U postgres -h localhost -c "CREATE DATABASE linkvault_test;"

# Run migrations on test DB
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/linkvault_test uv run alembic upgrade head

# Run tests
uv run pytest tests/ -v
```

**Test coverage:**
- Auth: register, login, duplicate email, wrong password, refresh token, /me
- Links: create, list, delete, slug collision, reserved slugs, unauthenticated
- Redirect: valid slug, invalid slug
- Workspaces: create, list, get, invite, remove, permission checks

---

## Observability

Start Prometheus + Grafana via Docker Compose:

```bash
docker compose up -d prometheus grafana
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

Dashboard panels:
- Requests per second
- p99 latency
- 4xx error rate

---

## CI/CD

Every push to `main`:
1. GitHub Actions spins up PostgreSQL + Redis
2. Runs full test suite (27 tests)
3. If tests pass → Render auto-deploys

---

**Implemented:**
- ✅ JWT auth with refresh token rotation
- ✅ Link CRUD with custom slugs, expiry, password protection
- ✅ Redis cache-aside on hot redirect path
- ✅ Celery click tracking (device, browser, referrer)
- ✅ Analytics endpoints (daily series, device/browser/referrer breakdown)
- ✅ Team workspaces with RBAC (owner/editor/viewer)
- ✅ Sliding window rate limiting
- ✅ Structured logging with request IDs
- ✅ Prometheus metrics + Grafana dashboard
- ✅ 27 passing tests
- ✅ GitHub Actions CI/CD

---

## Author

**Sudhanshu Kumar** — B.Tech CSE (AI/ML), KIET Group of Institutions

- GitHub: [@Sudhanshukumar0007](https://github.com/Sudhanshukumar0007)
- Blog: [Backprop Diaries](https://backpropdiaries.hashnode.dev)

> Built to learn production backend engineering — not just CRUD. Every decision in this codebase has a reason.