from app.features.chatbot.prompts import build_chatbot_prompt
from app.features.chatbot.schemas import ChatMessageRequest, ChatReplyResponse
from app.shared.clients.gemini_client import GeminiClient

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY = 20


class ChatbotService:
    def __init__(self):
        self.gemini_client = GeminiClient()

    async def send_message(
            self,
            request: ChatMessageRequest,
    ) -> ChatReplyResponse:
        message = request.message[:MAX_MESSAGE_LENGTH]
        history = request.history[-MAX_HISTORY:] if request.history else []

        prompt = build_chatbot_prompt(message, history)
        reply = await self.gemini_client.generate(prompt)

        return ChatReplyResponse(reply=reply)
