# LinkVault Second Audit

Audit date: 2026-07-03

Scope: second-pass audit of the current FastAPI service after the first `audit.md` fixes. This pass reviewed auth, link CRUD, redirects, Redis/Celery behavior, analytics, migrations, tests, Docker/Render/CI config, and current guide alignment.

Note: workspace/team support is intentionally not audited as a defect here because it is deferred to a later term.

## Executive Summary

The project is materially improved since the first audit. Refresh tokens and `/auth/me` now exist, click analytics are modeled, redirect/Celery failures are partially guarded, pagination was added for link listing, custom slug validation exists, the Docker/Python version mismatch appears fixed, and CI now provisions Redis plus the test database.

The code is still not production-ready. The highest-risk remaining issues are: Redis is still a hard startup/runtime dependency despite the intended graceful fallback; redirect cache writes and delete cache invalidation can still break requests; several reserved root slugs are misspelled and can create unreachable links; the `users.name` migration is still unsafe for existing data; test verification is currently blocked by the local `.venv`; and the test suite still does not isolate Redis/Celery or validate the most important regressions.

## Fixed Or Improved Since Audit 1

- `POST /api/v1/auth/refresh` and `GET /api/v1/auth/me` were added in `app/api/v1/auth.py`.
- Refresh token storage was added with hashed tokens in `app/models/refresh_token.py`.
- Redirect click handling now writes a `clicks` row and uses an atomic `click_count = click_count + 1` update in `app/tasks/analytics.py`.
- Redirect path wraps cache reads and Celery enqueue in error handling in `app/api/v1/redirect.py`.
- Redis client is now centralized through `app/core/redis.py` and initialized in lifespan.
- Link listing now accepts `limit` and `offset`.
- Custom slug validation now enforces length and allowed characters in `app/schemas/link.py`.
- CI now points at `linkvault_test` and starts Redis.
- Docker now uses `python:3.14-slim`, matching `requires-python = ">=3.14"`.

## Critical Findings

1. Redis is still a hard dependency for app startup and many requests.
   - Evidence: `app/main.py:18-21` creates Redis in lifespan and immediately awaits `ping()`. If Redis is unavailable, the app does not start, so `/health` cannot report degraded status. `app/core/redis.py:7-10` raises if the global client is unset.
   - Impact: A Redis outage can take down the entire API, including health checks, even though redirect code was changed to fall back to the database.
   - Fix: Do not require Redis ping success for startup. Initialize the client best-effort, make cache/rate-limit/click paths tolerate Redis errors, and let `/health` report Redis as unhealthy without preventing boot.

2. Redirect fallback still crashes when Redis fails after the database lookup.
   - Evidence: cache read is inside a `try` in `app/api/v1/redirect.py:23-42`, but cache write at `app/api/v1/redirect.py:55` is outside a Redis error boundary.
   - Impact: If Redis is down, the handler can successfully find the link in PostgreSQL and then still return 500 while trying to populate cache.
   - Fix: Wrap `redis.set(...)` in its own `try/except` and continue redirecting. Add a regression test where `get` and `set` both raise.

3. Delete still depends on Redis availability.
   - Evidence: `app/api/v1/links.py:35` injects Redis into delete, and `app/services/link_service.py:73` awaits `redis.delete(...)` before marking the link inactive. There is no error handling.
   - Impact: If Redis is unavailable, users cannot delete links. Worse, the database update is skipped because cache invalidation runs first.
   - Fix: Mark the link inactive and commit as the source of truth. Invalidate cache best-effort afterward or in a small helper with logged failure.

4. Reserved slug protection has misspellings, allowing unreachable links.(Done)
   - Evidence: `app/core/utils.py` reserves `"metrcs"`, `"redocs"`, and `"fevicon.ico"` instead of `"metrics"`, `"redoc"`, and `"favicon.ico"`.
   - Impact: Users can create slugs that collide with root app routes or expected browser routes. A link with slug `metrics` or `redoc` may be stored successfully but will not behave as a normal public redirect because those paths are already claimed by the app.
   - Fix: Correct the reserved set and add tests for `health`, `metrics`, `docs`, `redoc`, `openapi.json`, `api`, and `favicon.ico`.

5. The `users.name` migration is still unsafe for existing production data.
   - Evidence: `alembic/versions/b3c8e600ea46_add_name_to_users.py:24` still adds `users.name` as `nullable=False` without a server default or data backfill.
   - Impact: Running migrations against an existing database with users can fail.
   - Fix: Change the migration to add the column nullable or with a temporary default, backfill existing rows, then alter to non-null.

## High Priority Findings

1. Tests still depend on real PostgreSQL, Redis, and Celery behavior.
   - Evidence: `tests/conftest.py:53` starts the FastAPI lifespan, which pings Redis. Tests override only `get_db` at `tests/conftest.py:50`; they do not override `get_redis` or mock `record_click.delay`.
   - Impact: Redirect/link tests are integration tests tied to local services. They do not prove graceful Redis/Celery failure behavior and can fail on a clean machine.
   - Fix: Add fake Redis fixtures and monkeypatch Celery enqueue for unit-level tests. Keep separate integration tests for real Redis/Postgres.

2. Test database setup bypasses Alembic migrations.
   - Evidence: `tests/conftest.py:25` uses `Base.metadata.create_all` and `tests/conftest.py:30` uses `drop_all`.
   - Impact: Migration bugs, including the unsafe `users.name` migration, are invisible to CI.
   - Fix: Add a migration smoke test using `alembic upgrade head` against the test database, or make CI run migrations before tests.

3. Test data is not isolated per test.
   - Evidence: `setup_db` creates all tables once per session and drops them only at the end. The `client` fixture creates sessions but does not rollback or truncate tables between tests.
   - Impact: Tests can pass or fail depending on execution order and reused emails/slugs. This gets worse as refresh token and analytics tests grow.
   - Fix: Use per-test transactions with rollback, or truncate all tables between tests.

4. Production docs are always enabled despite the earlier production-docs concern.
   - Evidence: `app/main.py:32-33` sets `docs_url="/docs"` and `redoc_url="/redoc"` unconditionally.
   - Impact: This may be acceptable for a demo, but it contradicts the previous production-hardening direction. README says it is enabled for demo purposes, so this is a conscious tradeoff, not a bug.
   - Fix: Gate docs on `DEBUG` or `APP_ENV`, or keep them enabled and explicitly document that production is a portfolio/demo deployment.

5. Rate limiting can become a global failure point.
   - Evidence: `app/middleware/rate_limit.py:22` calls `get_redis()`, and the Redis pipeline at `app/middleware/rate_limit.py:25-30` has no error handling.
   - Impact: When rate limiting is enabled, Redis failure can turn most non-skipped endpoints into 500 responses.
   - Fix: Decide fail-open or fail-closed. For this project, fail-open with warning logs is more consistent with redirect availability.

6. Refresh token rotation has no concurrency protection.
   - Evidence: `app/services/user_service.py:56-83` reads a valid token, sets `is_revoked = True`, creates a replacement, and commits without row locking or conditional update.
   - Impact: Two concurrent refresh requests using the same token can both see it as valid before either commit, issuing multiple valid replacement tokens.
   - Fix: Use a transaction with `SELECT ... FOR UPDATE`, or a conditional `UPDATE refresh_tokens SET is_revoked=true WHERE token_hash=:hash AND is_revoked=false` and require one affected row.

## Medium Priority Findings

1. Expired links are cached with a fixed 24-hour TTL when first resolved before expiry.
   - Evidence: `app/api/v1/redirect.py:55` always uses `ex=86400`.
   - Impact: A link that expires in 5 minutes can remain redirectable from cache for up to 24 hours.
   - Fix: Set cache TTL to `min(86400, seconds_until_expiry)` and avoid caching already-expired links.

2. Cached redirects do not re-check expiry or active status.
   - Evidence: on cache hit, `app/api/v1/redirect.py:25-39` redirects immediately from cached `link_id|original_url`.
   - Impact: Cache correctness relies entirely on perfect invalidation and expiry-aware TTL. Current delete invalidation is not resilient, and expiry-aware TTL is missing.
   - Fix: Implement expiry-aware TTL and make delete invalidation best-effort after DB commit. For stricter correctness, store expiry in cache and validate it on hit.

3. Analytics endpoint has no response schemas or parameter bounds.
   - Evidence: `app/api/v1/analytics.py` returns raw dictionaries; `period` and `limit` are unbounded query parameters.
   - Impact: Very large `period` or `limit` values can create slow queries or large responses. OpenAPI is less useful without schemas.
   - Fix: Add Pydantic response models and constrain `period` and `limit` with `Query(ge=..., le=...)`.

4. `APP_ENV` values are inconsistent.
   - Evidence: default is `"developement"` in `app/core/config.py:4`; CI sets `APP_ENV: test`; rate limiting is disabled only when `settings.APP_ENV != "testing"` in `app/main.py:39`.
   - Impact: Test/production behavior depends on exact string spelling. CI currently runs with rate limiting enabled because it uses `test`, not `testing`.
   - Fix: Standardize on `development`, `testing`, and `production`, or use an enum-style settings field.

5. Docker Compose still does not run the API or Celery worker.
   - Evidence: `docker-compose.yml` starts Postgres, Redis, Prometheus, and Grafana only.
   - Impact: A new developer cannot start the full app stack with one compose command, and click tasks require a separately started worker.
   - Fix: Add `api` and `worker` services with health checks and shared env configuration.

6. Click task does not guard malformed task input.
   - Evidence: `app/tasks/analytics.py:24` and `app/tasks/analytics.py:35` call `UUID(link_id)` without handling `ValueError`.
   - Impact: Bad queued input will fail the task noisily. This is not currently user-triggered through normal code, but it is easy to harden.
   - Fix: Parse the UUID once at the start, reject/log invalid IDs, and reuse the parsed value.

## Low Priority Findings

1. Typos and naming inconsistencies remain.
   - Examples: `APP_ENV="developement"` in `app/core/config.py`, Celery app name `"linkvalut"` in `app/tasks/celery_app.py`, log text `"unavialable"` and `"failing back"` in `app/api/v1/redirect.py`, and reserved slug typos in `app/core/utils.py`.
   - Impact: Mostly polish and maintainability, except the reserved slug typos are functionally serious and are listed as critical.

2. Unused imports remain.
   - Examples: `pytest` in tests, `select` and `User` in `app/tasks/analytics.py`, `text` in `app/api/v1/analytics.py`, `get_me` import in `app/api/v1/auth.py`, and UUID imports in `app/db/base.py`.
   - Impact: Lint noise and weaker code hygiene.
   - Fix: Run Ruff after the `.venv` issue is repaired.

3. README roadmap is partly stale.
   - Evidence: README still lists "Add refresh tokens and `/auth/me`" and "Real click analytics table" as short/long-term priorities even though these are partially implemented.
   - Impact: Readers may think completed work is missing or misunderstand the current maturity.
   - Fix: Update README to distinguish done, partial, and remaining work.

## Verification Results

Attempted inside sandbox:

```bash
uv run pytest tests/ -v
uv run ruff check .
uv run mypy app
```

Result: all three failed before running because `uv` could not access `C:\Users\vom69\AppData\Local\uv\cache\sdists-v9\.git` due to access denied.

Attempted outside sandbox with approval:

```bash
uv run pytest tests/ -v
uv run ruff check .
uv run mypy app
```

Result: all three failed before running project checks because `uv` tried to remove `C:\Users\vom69\Desktop\LinkVault\.venv\lib64` and received access denied. The workspace `.venv` currently contains only `pyvenv.cfg` and a broken `lib64` link; there is no `.venv\Scripts` directory.

No test, lint, or type-check results are available from this audit because the environment failed before executing them.

## Recommended Next Steps

1. Fix the broken `.venv` so verification can run: remove/recreate the virtualenv, then run `uv sync`, `uv run pytest tests/ -v`, `uv run ruff check .`, and `uv run mypy app`.
2. Make Redis non-fatal at startup and fail-open in redirect cache writes, delete invalidation, and rate limiting.
3. Correct `RESERVED_SLUGS` and add regression tests for all root-level reserved routes.
4. Repair the unsafe `users.name` migration before applying it to any database with existing users.
5. Add tests for Redis down, Celery down, delete after cached redirect, expired-link cache TTL, refresh-token reuse, and migration upgrade.
6. Tighten test isolation and stop relying on `Base.metadata.create_all` as a substitute for migration verification.

