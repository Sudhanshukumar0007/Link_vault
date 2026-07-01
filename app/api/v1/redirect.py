from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.link import Link

router = APIRouter(tags=["redirect"])

@router.get("/{slug}")
async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Link).where(Link.slug == slug, Link.is_active == True)
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

    link.click_count += 1
    await db.commit()

    return RedirectResponse(url=str(link.original_url))