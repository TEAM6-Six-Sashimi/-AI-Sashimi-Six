import httpx

from app.core.config import get_settings
from app.core.exceptions import GeminiApiException


class GeminiClient:
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
            async with httpx.AsyncClient(
                    timeout=settings.gemini_timeout_seconds
            ) as client:
                response = await client.post(
                    url,
                    params={
                        "key": settings.gemini_api_key
                    },
                    json=request_body,
                )

            if response.status_code >= 400:
                print("Gemini API error status:", response.status_code)
                print("Gemini API error body:", response.text)
                raise GeminiApiException()

            response_body = response.json()

            return response_body["candidates"][0]["content"]["parts"][0]["text"]
        except GeminiApiException:
            raise
        except Exception as exception:
            print("Gemini API unexpected error:", repr(exception))
            raise GeminiApiException() from exception