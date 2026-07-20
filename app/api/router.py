from fastapi import APIRouter

from app.api.chatbot_router import router as chatbot_router
from app.api.cover_letter_router import router as cover_letter_router
from app.api.job_posting_router import router as job_posting_router

api_router = APIRouter(
    prefix="/api",
)

api_router.include_router(cover_letter_router)
api_router.include_router(chatbot_router)
api_router.include_router(job_posting_router)