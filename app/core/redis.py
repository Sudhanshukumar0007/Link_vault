from redis.asyncio import from_url, Redis
from app.core.config import settings
from app.main import redis_client

async def get_redis() -> Redis:
    return redis_client