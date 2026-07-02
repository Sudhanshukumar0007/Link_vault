from redis.asyncio import from_url, Redis
from app.core.config import settings

async def get_redis() -> Redis:
    redis = from_url(
        settings.REDIS_URL,
        decode_responses=True,
        ssl_cert_reqs=None  
    )
    return redis