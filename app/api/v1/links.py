from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.schemas.link import LinkResponse, LinkCreate
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.link_service import create_link, get_user_links, delete_link
from app.core.redis import get_redis
from redis.asyncio import Redis

router = APIRouter(prefix="/links", tags=["links"])

@router.post("/", response_model=LinkResponse)
async def create_link_route(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_link(db, data, current_user.id)

@router.get("/", response_model=list[LinkResponse])
async def get_links_route(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_links(db, current_user.id, limit, offset)
@router.delete("/{link_id}")
async def delete_link_route(
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis:Redis=Depends(get_redis)
):
    return await delete_link(db, link_id, current_user.id,redis)