import json

from app.features.chatbot.prompts import build_classification_prompt
from app.features.chatbot.schemas import Classification
from app.shared.clients.gemini_client import GeminiClient
from app.shared.utils.response_cleaner import remove_markdown_fence


class Classifier:
    """질문 분류 엔진. LLM에 분류 규정 프롬프트를 보내 분류 결과(JSON)를 받아 파싱한다."""

    def __init__(self):
        self.gemini_client = GeminiClient()

    async def classify(
            self,
            user_message: str,
            conversation_context: str | None = None,
    ) -> Classification:
        prompt = build_classification_prompt(
            user_message=user_message,
            conversation_context=conversation_context,
        )

        generated_text = await self.gemini_client.generate(prompt)

        json_text = remove_markdown_fence(generated_text)
        data = json.loads(json_text)

        return Classification.model_validate(data)
