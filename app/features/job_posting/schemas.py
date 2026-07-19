from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


FitStatus = Literal[
    "SATISFIED",
    "PARTIALLY_SATISFIED",
    "NOT_SATISFIED",
    "UNKNOWN",
]


class JobPostingAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(..., min_length=50)
    resume_based: bool = Field(default=False, alias="resumeBased")
    resume_content: str | None = Field(default=None, alias="resumeContent")


class JobPostingSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_role: str = Field(..., alias="jobRole")
    required_qualifications: list[str] = Field(
        default_factory=list,
        alias="requiredQualifications",
    )
    preferred_qualifications: list[str] = Field(
        default_factory=list,
        alias="preferredQualifications",
    )
    experience_requirement: str | None = Field(
        default=None,
        alias="experienceRequirement",
    )
    main_task_summary: str = Field(..., alias="mainTaskSummary")


class FitAnalysisItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: FitStatus
    required: str | None = None
    user: str | None = None
    comment: str
    missing_items: list[str] = Field(
        default_factory=list,
        alias="missingItems",
    )


class JobFitAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    education: FitAnalysisItemResponse
    career: FitAnalysisItemResponse
    certification: FitAnalysisItemResponse
    overall_comments: list[str] = Field(
        default_factory=list,
        alias="overallComments",
    )


class CertificateRecommendationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    reason: str
    related_skills: list[str] = Field(
        default_factory=list,
        alias="relatedSkills",
    )
    difficulty: str | None = None


class JobPostingAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: JobPostingSummaryResponse
    fit_analysis: JobFitAnalysisResponse | None = Field(
        default=None,
        alias="fitAnalysis",
    )
    certificates: list[CertificateRecommendationResponse] = Field(
        default_factory=list,
    )
    courses: list = Field(default_factory=list)