from fastapi import APIRouter

from app.api.v1.endpoints import languages, translate

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(translate.router, tags=["traduction"])
api_router.include_router(languages.router, tags=["langues"])
