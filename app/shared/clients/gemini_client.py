import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import GeminiApiException


logger = logging.getLogger("uvicorn.error")


class GeminiClient:
    _client: httpx.AsyncClient | None = None
    _timeout_seconds: int | None = None

    async def generate(
            self,
            prompt: str,
    ) -> str:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise GeminiApiException()

        url = (
            f"{settings.gemini_base_url}/models/"
            f"{settings.gemini_model}:generateContent"
        )

        request_body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            client = await self._get_client(
                settings.gemini_timeout_seconds
            )

            response = await client.post(
                url,
                params={
                    "key": settings.gemini_api_key
                },
                json=request_body,
            )

            if response.status_code >= 400:
                logger.warning(
                    "Gemini API error status=%s bodySnippet=%s",
                    response.status_code,
                    self._truncate(response.text),
                )
                raise GeminiApiException()

            response_body = response.json()

            return self._extract_text(response_body)
        except GeminiApiException:
            raise
        except Exception as exception:
            logger.exception(
                "Gemini API unexpected error"
            )
            raise GeminiApiException() from exception

    def _extract_text(
            self,
            response_body: dict[str, Any],
    ) -> str:
        candidates = response_body.get("candidates")

        if not isinstance(candidates, list) or not candidates:
            logger.warning(
                "Gemini API response has no candidates: keys=%s",
                list(response_body.keys()),
            )
            raise GeminiApiException()

        first_candidate = candidates[0]

        if not isinstance(first_candidate, dict):
            logger.warning(
                "Gemini API candidate is invalid: type=%s",
                type(first_candidate).__name__,
            )
            raise GeminiApiException()

        content = first_candidate.get("content")

        if not isinstance(content, dict):
            logger.warning(
                "Gemini API response has no content: candidateKeys=%s",
                list(first_candidate.keys()),
            )
            raise GeminiApiException()

        parts = content.get("parts")

        if not isinstance(parts, list) or not parts:
            logger.warning(
                "Gemini API response has no parts: contentKeys=%s",
                list(content.keys()),
            )
            raise GeminiApiException()

        texts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict)
            and isinstance(part.get("text"), str)
            and part.get("text").strip()
        ]

        if not texts:
            logger.warning(
                "Gemini API response has no text parts: partsCount=%s",
                len(parts),
            )
            raise GeminiApiException()

        return "".join(texts).strip()

    def _truncate(
            self,
            value: str,
            limit: int = 200,
    ) -> str:
        if len(value) <= limit:
            return value

        return value[:limit] + "...(truncated)"

    @classmethod
    async def _get_client(
            cls,
            timeout_seconds: int,
    ) -> httpx.AsyncClient:
        if (
                cls._client is None
                or cls._client.is_closed
                or cls._timeout_seconds != timeout_seconds
        ):
            if cls._client is not None and not cls._client.is_closed:
                await cls._client.aclose()

            cls._client = httpx.AsyncClient(
                timeout=timeout_seconds
            )
            cls._timeout_seconds = timeout_seconds

        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()

        cls._client = None
        cls._timeout_seconds = None