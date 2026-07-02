from app.tasks.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.user import User  # import User so SQLAlchemy knows about users table
from app.models.link import Link
from sqlalchemy import select
from loguru import logger
from uuid import UUID
from sqlalchemy import update


@celery_app.task
def increment_click_count(link_id: str):
    with SyncSessionLocal() as db:
        db.execute(
            update(Link)
            .where(Link.id==UUID(link_id))
            .values(click_count=Link.click_count+1)
        )
        db.commit()
        logger.info(f"click counted | link_id={link_id}")