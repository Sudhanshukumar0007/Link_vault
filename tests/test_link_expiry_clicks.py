# import asyncio
# import pytest
# from datetime import datetime, timedelta, timezone

# # Based on the actual redirect.py:
# #   if seconds_until_expiry <= 0: raise HTTPException(status_code=410, detail="Link has expired")
# # -> expired links return 410, NOT 404. 404 is reserved for "slug never existed / inactive".


# async def test_redirect_expired_link_returns_410(client, auth_headers):
#     past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

#     create = await client.post(
#         "/api/v1/links/",
#         json={
#             "original_url": "https://github.com",
#             "custom_slug": "expiredslug",
#             "expires_at": past_time,
#         },
#         headers=auth_headers,
#     )
#     assert create.status_code == 200

#     response = await client.get("/expiredslug", follow_redirects=False)
#     assert response.status_code == 410


# async def test_redirect_future_expiry_still_works(client, auth_headers):
#     """Sanity check: a link expiring in the future should still redirect."""
#     future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

#     create = await client.post(
#         "/api/v1/links/",
#         json={
#             "original_url": "https://github.com",
#             "custom_slug": "futureslug",
#             "expires_at": future_time,
#         },
#         headers=auth_headers,
#     )
#     assert create.status_code == 200

#     response = await client.get("/futureslug", follow_redirects=False)
#     assert response.status_code == 307
#     assert response.headers["location"] == "https://github.com/"


# async def test_expired_link_not_served_from_cache_after_ttl():
#     """
#     NOTE - not runnable as-is, documenting a real gap instead of faking a pass:

#     redirect.py only checks `expires_at` on a cache MISS (the DB query path).
#     On a cache HIT it trusts the cached value unconditionally. Correctness
#     currently depends entirely on `ttl = min(86400, seconds_until_expiry)`
#     lining up with the real expiry. There is no test proving a link cached
#     just before expiry actually stops redirecting once expired - doing so
#     would require manipulating Redis TTL/time directly (e.g. via freezegun
#     or a real Redis connection with a short-lived key), which needs a fixture
#     exposing the Redis client, not just the HTTP client. Flagging this instead
#     of writing a test that doesn't actually exercise the cache path.
#     """
#     pytest.skip("Requires direct Redis access fixture - see docstring")


# async def test_click_recorded_in_db_after_redirect(client, auth_headers):
#     """
#     IMPORTANT ASSUMPTION: click_count / Click rows are updated by the
#     `record_click` Celery task via `.delay(...)`, which is fire-and-forget
#     and async by default. In a normal test run (no Celery worker, no
#     CELERY_TASK_ALWAYS_EAGER), this will NOT have completed by the time the
#     HTTP response returns - asserting click_count == N immediately after
#     the request will be flaky at best, and silently wrong at worst since
#     the `.delay()` call is wrapped in a bare `except: logger.warning(...)`.

#     To make click-count genuinely testable, set in your test settings:
#         CELERY_TASK_ALWAYS_EAGER = True
#         CELERY_TASK_EAGER_PROPAGATES = True
#     so `.delay()` runs synchronously in-process during tests. Until then,
#     this test polls with a short retry loop as a pragmatic workaround.
#     """
#     create = await client.post(
#         "/api/v1/links/",
#         json={
#             "original_url": "https://github.com",
#             "custom_slug": "clicktrack",
#             "expires_at": None,
#         },
#         headers=auth_headers,
#     )
#     assert create.status_code == 200
#     link_id = create.json()["id"]
#     assert create.json()["click_count"] == 0

#     await client.get("/clicktrack", follow_redirects=False)

#     # Poll briefly in case the Celery task is eager-but-not-instant.
#     # If your test config runs Celery eagerly and synchronously, this should
#     # pass on the first iteration; if it never passes, click_count updates
#     # are not wired to run during tests at all - that itself is the finding.
#     updated = None
#     for _ in range(5):
#         links = await client.get("/api/v1/links/", headers=auth_headers)
#         matching = [l for l in links.json() if l["id"] == link_id]
#         if matching and matching[0]["click_count"] > 0:
#             updated = matching[0]
#             break
#         await asyncio.sleep(0.2)

#     assert updated is not None, (
#         "click_count never incremented - either Celery isn't running eagerly "
#         "in tests, or click tracking is broken. See docstring."
#     )
#     assert updated["click_count"] == 1


# async def test_redirect_invalid_slug_returns_404(client):
#     """Nonexistent slug should 404, distinct from the 410 expired case."""
#     response = await client.get("/definitely-not-a-real-slug", follow_redirects=False)
#     assert response.status_code == 404


# async def test_deleted_link_no_longer_redirects(client, auth_headers):
#     """
#     Covers bug #2 from review: soft-deleted links should stop redirecting.
#     This will pass when Redis is healthy (delete_link's cache invalidation
#     succeeds) but is NOT proof the invalidation is reliable - if Redis is
#     unavailable at delete time, the except-swallow in link_service.delete_link
#     means the cached slug keeps serving until its TTL naturally expires.
#     """
#     create = await client.post(
#         "/api/v1/links/",
#         json={
#             "original_url": "https://github.com",
#             "custom_slug": "willdelete",
#             "expires_at": None,
#         },
#         headers=auth_headers,
#     )
#     assert create.status_code == 200
#     link_id = create.json()["id"]

#     # warm the cache
#     first = await client.get("/willdelete", follow_redirects=False)
#     assert first.status_code == 307

#     delete_resp = await client.delete(f"/api/v1/links/{link_id}", headers=auth_headers)
#     assert delete_resp.status_code == 200

#     second = await client.get("/willdelete", follow_redirects=False)
#     assert second.status_code == 404