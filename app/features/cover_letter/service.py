import json

from app.core.exceptions import AiResponseParseException
from app.features.cover_letter.analyzer import (
    calculate_average_sentence_length,
    calculate_repeated_expression_count,
)
from app.features.cover_letter.prompts import build_cover_letter_review_prompt
from app.features.cover_letter.schemas import (
    CoverLetterQuestionReview,
    CoverLetterReviewRequest,
    CoverLetterReviewResponse,
)
from app.shared.clients.gemini_client import GeminiClient
from app.shared.utils.response_cleaner import remove_markdown_fence


class CoverLetterService:
    def __init__(self):
        self.gemini_client = GeminiClient()

    async def review(
            self,
            request: CoverLetterReviewRequest,
    ) -> CoverLetterReviewResponse:
        prompt = build_cover_letter_review_prompt(request)

        generated_text = await self.gemini_client.generate(prompt)

        return self._parse_review_response(
            generated_text,
            request,
        )

    def _parse_review_response(
            self,
            generated_text: str,
            request: CoverLetterReviewRequest,
    ) -> CoverLetterReviewResponse:
        try:
            json_text = remove_markdown_fence(generated_text)
            data = json.loads(json_text)

            question_reviews = [
                CoverLetterQuestionReview.model_validate(question)
                for question in data["questions"]
            ]

            return CoverLetterReviewResponse(
                overall_comment=data["overallComment"],
                repeated_expression_count=calculate_repeated_expression_count(
                    question_reviews
                ),
                average_sentence_length=calculate_average_sentence_length(
                    [question.content for question in request.questions]
                ),
                questions=question_reviews,
            )
        except Exception as exception:
            raise AiResponseParseException() from exception