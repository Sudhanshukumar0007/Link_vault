from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.link import Link
from app.core.redis import get_redis
from redis.asyncio import Redis
from loguru import logger
from app.tasks.analytics import increment_click_count
from app.core.utils import RESERVED_SLUGS
router = APIRouter(tags=["redirect"])

@router.get("/{slug}")
async def redirect(
    slug: str,
    db: AsyncSession = Depends(get_db),
    redis:Redis = Depends(get_redis)
):
    if slug in RESERVED_SLUGS:
            raise HTTPException(status_code=404, detail="Not found")
    try:
        cached = await redis.get(f"slug:{slug}")
        if cached:
            logger.info(f"CACHE HIT | slug={slug}")
            link_id, original_url = cached.split("|", 1)
            try:
                increment_click_count.delay(link_id)
            except:
                logger.warning(f"Celery unavailable | slug={slug}")
            return RedirectResponse(url=original_url)
        # Cache miss query db
    except Exception:
        logger.warning(f"Redis unavialable | slug={slug} | failing back to DB")

    result = await db.execute(
        select(Link).where(Link.slug == slug, Link.is_active == True)
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")
    
    await redis.set(f"slug:{slug}",f"{link.id}|{str(link.original_url)}",ex=86400)

    try:
        increment_click_count.delay(str(link.id))
    except Exception:
        logger.warning("Celery unavailable")

    logger.info(f"CACHE MISS | slug={slug} | querying DB")
    return RedirectResponse(url=str(link.original_url))