from app.tasks.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.link import Link
from app.models.click import Click
from sqlalchemy import select, update
from loguru import logger
from uuid import UUID
from datetime import datetime, timezone
import hashlib
from app.models.user import User 
from user_agents import parse as parse_ua

@celery_app.task
def record_click(link_id: str, ip: str, user_agent: str, referrer: str):
    try:
        link_uuid = UUID(link_id)
    except ValueError:
        logger.error(f"Invalid link_id in record_click task: {link_id}")
        return

    with SyncSessionLocal() as db:
        ua = parse_ua(user_agent)
        device_type = "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
        browser = ua.browser.family

        click = Click(
            link_id=link_uuid,
            clicked_at=datetime.now(timezone.utc),
            ip_hash=hashlib.sha256(ip.encode()).hexdigest()[:16],
            referrer=referrer[:500] if referrer else None,
            device_type=device_type,
            browser=browser,
        )
        db.add(click)
        db.execute(
            update(Link)
            .where(Link.id == link_uuid)
            .values(click_count=Link.click_count + 1)
        )
        db.commit()
        logger.info(f"Click recorded | link_id={link_id} | device={device_type} | browser={browser}")