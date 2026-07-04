from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select
from app.schemas.link import LinkCreate
from app.models.link import Link
from app.core.utils import generate_slug
from uuid import UUID
import redis
from app.core.utils import RESERVED_SLUGS
from loguru import logger

async def check_slug_in_db(db: AsyncSession, slug: str) -> Link | None:
    result = await db.execute(select(Link).where(Link.slug == slug))
    return result.scalar_one_or_none()


async def create_link(db: AsyncSession, data: LinkCreate, user_id: UUID) -> Link:
    if data.custom_slug:
        existing = await check_slug_in_db(db, data.custom_slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already taken, choose a different one"
            )
        if data.custom_slug in RESERVED_SLUGS:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="this slug is Reserved, choose a different one"
            )
        slug = data.custom_slug
    else:
        slug = generate_slug()
        while slug in RESERVED_SLUGS or await check_slug_in_db(db, slug):
            slug = generate_slug()

    link = Link(
        slug=slug,
        original_url=str(data.original_url),
        user_id=user_id,
        expires_at=data.expires_at
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def get_user_links(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 10,
    offset: int = 0
) -> list[Link]:
    result = await db.execute(
        select(Link)
        .where(Link.user_id == user_id, Link.is_active == True)
        .order_by(Link.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def delete_link(db: AsyncSession, link_id: UUID, user_id: UUID,redis) -> dict:
    result = await db.execute(
        select(Link).where(Link.id == link_id, Link.user_id == user_id)
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    link.is_active = False
    await db.commit()
    
    try:
        await redis.delete(f"slug:{link.slug}")
    except Exception:
        logger.warning(f"Cache invalidation failed | slug={link.slug}")
    return {"message": "Link deleted successfully"}