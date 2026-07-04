from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.click import Click
from app.models.link import Link
from sqlalchemy import text

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/links/{link_id}/stats")
async def link_stats(
    link_id: UUID,
    period: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.now(timezone.utc) - timedelta(days=period)

    # verify link belongs to user
    link_result = await db.execute(
        select(Link).where(Link.id == link_id, Link.user_id == current_user.id)
    )
    link = link_result.scalar_one_or_none()
    if not link:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Link not found")

    # clicks per day
    day_trunc = func.date_trunc("day", Click.clicked_at)

    result = await db.execute(
        select(
            day_trunc.label("date"),
            func.count(Click.id).label("clicks")
        )
        .where(Click.link_id == link_id, Click.clicked_at >= since)
        .group_by(day_trunc)
        .order_by(day_trunc)
    )
    daily_clicks = [{"date": str(row.date.date()), "clicks": row.clicks} for row in result]

    # device breakdown
    device_result = await db.execute(
        select(Click.device_type, func.count(Click.id).label("count"))
        .where(Click.link_id == link_id, Click.clicked_at >= since)
        .group_by(Click.device_type)
    )
    devices = [{"device": row.device_type, "count": row.count} for row in device_result]

    # browser breakdown
    browser_result = await db.execute(
        select(Click.browser, func.count(Click.id).label("count"))
        .where(Click.link_id == link_id, Click.clicked_at >= since)
        .group_by(Click.browser)
    )
    browsers = [{"browser": row.browser, "count": row.count} for row in browser_result]

    # add this after browser_result
    referrer_result = await db.execute(
        select(Click.referrer, func.count(Click.id).label("count"))
        .where(
            Click.link_id == link_id,
            Click.clicked_at >= since,
            Click.referrer.isnot(None)
        )
        .group_by(Click.referrer)
        .order_by(desc(func.count(Click.id)))
        .limit(10)
    )
    referrers = [{"referrer": row.referrer, "count": row.count} for row in referrer_result]

    return {
        "link_id": str(link_id),
        "slug": link.slug,
        "total_clicks": link.click_count,
        "period_days": period,
        "daily_clicks": daily_clicks,
        "devices": devices,
        "browsers": browsers,
        "referrers":referrers,
    }


@router.get("/top-links")
async def top_links(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Link)
        .where(Link.user_id == current_user.id, Link.is_active == True)
        .order_by(desc(Link.click_count))
        .limit(limit)
    )
    links = result.scalars().all()
    return [
        {
            "slug": link.slug,
            "original_url": link.original_url,
            "click_count": link.click_count,
            "created_at": str(link.created_at)
        }
        for link in links
    ]