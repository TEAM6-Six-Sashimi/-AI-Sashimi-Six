import json
import logging
import re
from json import JSONDecodeError

from pydantic import ValidationError

from app.core.exceptions import AiResponseParseException
from app.features.job_posting.prompts import build_job_posting_analysis_prompt
from app.features.job_posting.schemas import (
    JobPostingAnalyzeRequest,
    JobPostingAnalyzeResponse,
)
from app.shared.clients.gemini_client import GeminiClient
from app.shared.utils.response_cleaner import remove_markdown_fence


logger = logging.getLogger("uvicorn.error")

_MAX_CONTENT_LENGTH = 8000
_CHUNK_SIZE = 1200


class JobPostingService:
    def __init__(self):
        self.gemini_client = GeminiClient()

    async def analyze(
            self,
            request: JobPostingAnalyzeRequest,
    ) -> JobPostingAnalyzeResponse:
        normalized_content = self._prepare_content(
            request.content
        )

        prepared_request = request.model_copy(
            update={
                "content": normalized_content
            }
        )

        prompt = build_job_posting_analysis_prompt(
            prepared_request
        )

        generated_text = await self.gemini_client.generate(prompt)

        return self._parse_analysis_response(generated_text)

    def _parse_analysis_response(
            self,
            generated_text: str,
    ) -> JobPostingAnalyzeResponse:
        try:
            json_text = remove_markdown_fence(generated_text)
            data = json.loads(json_text)

            data.setdefault("certificates", [])
            data.setdefault("courseSearchCriteria", [])

            criteria = data["courseSearchCriteria"]

            if not isinstance(criteria, list):
                raise ValueError("courseSearchCriteria must be a list")

            data["courseSearchCriteria"] = [
                criterion
                for criterion in criteria
                if isinstance(criterion, dict)
                and criterion.get("recommendationType") == "CERTIFICATE"
            ]

            return JobPostingAnalyzeResponse.model_validate(data)

        except JSONDecodeError as exception:
            logger.warning(
                "Job posting AI response JSON decode failed: textSnippet=%s",
                self._truncate(generated_text),
            )
            raise AiResponseParseException() from exception

        except ValidationError as exception:
            logger.warning(
                "Job posting AI response validation failed: errors=%s",
                exception.errors(),
            )
            raise AiResponseParseException() from exception

        except ValueError as exception:
            logger.warning(
                "Job posting AI response shape invalid: message=%s",
                str(exception),
            )
            raise AiResponseParseException() from exception

        except Exception as exception:
            logger.exception(
                "Job posting AI response parse unexpected error"
            )
            raise AiResponseParseException() from exception

    def _prepare_content(
            self,
            content: str,
    ) -> str:
        normalized = self._normalize_content(content)

        if len(normalized) <= _MAX_CONTENT_LENGTH:
            return normalized

        compressed = self._compress_by_chunks(normalized)

        logger.info(
            "Job posting content compressed: originalLength=%s, compressedLength=%s",
            len(normalized),
            len(compressed),
        )

        return compressed

    def _normalize_content(
            self,
            content: str,
    ) -> str:
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in content.splitlines()
        ]

        deduplicated_lines = []
        seen = set()

        for line in lines:
            if not line:
                continue

            if line in seen:
                continue

            seen.add(line)
            deduplicated_lines.append(line)

        return "\n".join(deduplicated_lines).strip()

    def _compress_by_chunks(
            self,
            content: str,
    ) -> str:
        chunks = self._split_into_chunks(content)

        selected_indexes = []
        selected_length = 0

        for index in self._balanced_indexes(len(chunks)):
            chunk = chunks[index]
            next_length = selected_length + len(chunk) + 2

            if next_length > _MAX_CONTENT_LENGTH:
                continue

            selected_indexes.append(index)
            selected_length = next_length

        selected_indexes.sort()

        return "\n\n".join(
            chunks[index]
            for index in selected_indexes
        ).strip()

    def _split_into_chunks(
            self,
            content: str,
    ) -> list[str]:
        paragraphs = [
            paragraph.strip()
            for paragraph in content.split("\n")
            if paragraph.strip()
        ]

        chunks = []
        current = []

        current_length = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph)

            if current and current_length + paragraph_length + 1 > _CHUNK_SIZE:
                chunks.append("\n".join(current))
                current = []
                current_length = 0

            if paragraph_length > _CHUNK_SIZE:
                chunks.extend(
                    self._split_long_paragraph(paragraph)
                )
                continue

            current.append(paragraph)
            current_length += paragraph_length + 1

        if current:
            chunks.append("\n".join(current))

        return chunks

    def _split_long_paragraph(
            self,
            paragraph: str,
    ) -> list[str]:
        return [
            paragraph[index:index + _CHUNK_SIZE]
            for index in range(
                0,
                len(paragraph),
                _CHUNK_SIZE
            )
        ]

    def _balanced_indexes(
            self,
            size: int,
    ) -> list[int]:
        indexes = []
        left = 0
        right = size - 1

        while left <= right:
            indexes.append(left)

            if left != right:
                indexes.append(right)

            left += 1
            right -= 1

        return indexes

    def _truncate(
            self,
            value: str,
            limit: int = 300,
    ) -> str:
        if len(value) <= limit:
            return value

        return value[:limit] + "...(truncated)"