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

router = APIRouter(tags=["redirect"])

@router.get("/{slug}")
async def redirect(
    slug: str,
    db: AsyncSession = Depends(get_db),
    redis:Redis = Depends(get_redis)
):
    cached_url = await redis.get(f"slug:{slug}")
    if cached_url:
        logger.info(f"CACHE HIT | slug={slug}")
        return RedirectResponse(url=cached_url)
    # Cache miss query db

    result = await db.execute(
        select(Link).where(Link.slug == slug, Link.is_active == True)
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")
    
    await redis.set(f"slug:{slug}",str(link.original_url),ex=86400)

    link.click_count += 1
    await db.commit()

    logger.info(f"CACHE SET | slug={slug} | cached for 24hrs")
    return RedirectResponse(url=str(link.original_url))