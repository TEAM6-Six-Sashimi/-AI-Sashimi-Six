from fastapi import APIRouter

from app.api.cover_letter_router import router as cover_letter_router

api_router = APIRouter(
    prefix="/api",
)

api_router.include_router(cover_letter_router)