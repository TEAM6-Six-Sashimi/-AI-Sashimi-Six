from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CoverLetterQuestionStatus = Literal[
    "GOOD",
    "RECOMMENDED",
    "NEEDS_REVISION",
]


class CoverLetterQuestionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_key: str = Field(..., alias="questionKey")
    question_title: str = Field(..., alias="questionTitle")
    content: str = Field(..., min_length=1)


class CoverLetterReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    questions: list[CoverLetterQuestionRequest] = Field(..., min_length=1)
    resume_summary: str | None = Field(default=None, alias="resumeSummary")
    job_posting_summary: str | None = Field(
        default=None,
        alias="jobPostingSummary",
    )


class SpellingCorrection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    original: str
    corrected: str


class CoverLetterQuestionReview(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_key: str = Field(..., alias="questionKey")
    status: CoverLetterQuestionStatus
    summary_feedback: str = Field(..., alias="summaryFeedback")
    spelling_corrections: list[SpellingCorrection] = Field(
        default_factory=list,
        alias="spellingCorrections",
    )
    repeated_expressions: list[str] = Field(
        default_factory=list,
        alias="repeatedExpressions",
    )
    expression_improvement_count: int = Field(
        ...,
        ge=0,
        alias="expressionImprovementCount",
    )
    flow_improvement_count: int = Field(
        ...,
        ge=0,
        alias="flowImprovementCount",
    )
    feedback: str
    improved_example: str | None = Field(
        default=None,
        alias="improvedExample",
    )


class CoverLetterReviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    overall_comment: str = Field(..., alias="overallComment")
    repeated_expression_count: int = Field(
        ...,
        ge=0,
        alias="repeatedExpressionCount",
    )
    average_sentence_length: int = Field(
        ...,
        ge=0,
        alias="averageSentenceLength",
    )
    questions: list[CoverLetterQuestionReview]