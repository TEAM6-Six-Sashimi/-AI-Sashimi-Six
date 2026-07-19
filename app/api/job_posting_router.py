from fastapi import APIRouter

from app.features.job_posting.schemas import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
)
from app.features.job_posting.service import JobPostingService

router = APIRouter(
    prefix="/job-postings",
    tags=["Job Posting"],
)

job_posting_service = JobPostingService()


@router.post(
    "/analyze",
    response_model=JobPostingAnalyzeResponse,
    response_model_by_alias=True,
)
async def analyze_job_posting(
        request: JobPostingAnalyzeRequest,
):
    return await job_posting_service.analyze(request)