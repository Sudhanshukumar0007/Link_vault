from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.links import router as links_router
from app.api.v1.redirect import router as redirect_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(links_router)