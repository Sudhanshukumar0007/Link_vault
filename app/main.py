from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.redirect import router as redirect_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
    )

    app.include_router(api_router) 
    app.include_router(redirect_router) 
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.VERSION}

    return app


app = create_app()