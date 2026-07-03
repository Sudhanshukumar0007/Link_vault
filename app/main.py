from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.redirect import router as redirect_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logging import LoggingMiddleware  # add this
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import from_url
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.redis import get_redis
import app.core.redis as redis_module

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_module.redis_client = from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    await redis_module.redis_client.ping()
    yield
    await redis_module.redis_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    Instrumentator().instrument(app).expose(app)
    app.add_middleware(LoggingMiddleware)

    if settings.APP_ENV != "testing":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    app.include_router(api_router)

    @app.get("/health")
    async def health():
        health_status = {
            "status": "healthy",
            "version": settings.VERSION,
            "database": "healthy",
            "redis": "healthy",
        }
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
        except Exception:
            health_status["database"] = "unhealthy"
            health_status["status"] = "degraded"

        try:
            redis = await get_redis()
            await redis.ping()
        except Exception:
            health_status["redis"] = "unhealthy"
            health_status["status"] = "degraded"

        return health_status

    app.include_router(redirect_router)

    return app


app = create_app()