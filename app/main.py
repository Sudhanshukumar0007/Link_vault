from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.redirect import router as redirect_router
from app.middleware.rate_limit import RateLimitMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import from_url,Redis
from contextlib import asynccontextmanager

redis_client:Redis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = from_url(settings.REDIS_URL,decode_response=True)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
    )

    Instrumentator().instrument(app).expose(app)

    app.add_middleware(RateLimitMiddleware,requests_per_minute=60)
    app.include_router(api_router) 
    app.include_router(redirect_router) 
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.VERSION}

    return app


app = create_app()