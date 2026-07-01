from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select
from app.schemas.link import LinkCreate
from app.models.user import User
from app.models.link import Link
from app.core.utils import generate_slug
from uuid import UUID


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
        slug = data.custom_slug
    else:
        slug = generate_slug()
        while await check_slug_in_db(db, slug):
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


async def get_user_links(db: AsyncSession, user_id: UUID) -> list[Link]:
    result = await db.execute(
        select(Link).where(Link.user_id == user_id, Link.is_active == True)
    )
    return result.scalars().all()


async def delete_link(db: AsyncSession, link_id: UUID, user_id: UUID) -> dict:
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
    return {"message": "Link deleted successfully"}