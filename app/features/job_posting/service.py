import json

from app.core.exceptions import AiResponseParseException
from app.features.job_posting.prompts import build_job_posting_analysis_prompt
from app.features.job_posting.schemas import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
)
from app.shared.clients.gemini_client import GeminiClient
from app.shared.utils.response_cleaner import remove_markdown_fence


class JobPostingService:
    def __init__(self):
        self.gemini_client = GeminiClient()

    async def analyze(
            self,
            request: JobPostingAnalyzeRequest,
    ) -> JobPostingAnalyzeResponse:
        prompt = build_job_posting_analysis_prompt(request)

        generated_text = await self.gemini_client.generate(prompt)

        return self._parse_analysis_response(generated_text)

    def _parse_analysis_response(
            self,
            generated_text: str,
    ) -> JobPostingAnalyzeResponse:
        try:
            json_text = remove_markdown_fence(generated_text)
            data = json.loads(json_text)

            data["courses"] = []

            return JobPostingAnalyzeResponse.model_validate(data)
        except Exception as exception:
            raise AiResponseParseException() from exception