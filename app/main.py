from fastapi import FastAPI
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.VERSION}

    return app


app = create_app()