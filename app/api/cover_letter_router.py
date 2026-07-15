from fastapi import APIRouter

from app.features.cover_letter.schemas import (
    CoverLetterReviewRequest,
    CoverLetterReviewResponse,
)
from app.features.cover_letter.service import CoverLetterService

router = APIRouter(
    prefix="/cover-letters",
    tags=["Cover Letter"],
)

cover_letter_service = CoverLetterService()


@router.post(
    "/review",
    response_model=CoverLetterReviewResponse,
    response_model_by_alias=True,
)
async def review_cover_letter(
        request: CoverLetterReviewRequest,
):
    return await cover_letter_service.review(request)