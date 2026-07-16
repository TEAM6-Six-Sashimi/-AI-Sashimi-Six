from fastapi import APIRouter

from app.features.chatbot.schemas import ChatMessageRequest, ChatReplyResponse
from app.features.chatbot.service import ChatbotService

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)

chatbot_service = ChatbotService()


@router.post(
    "/messages",
    response_model=ChatReplyResponse,
    response_model_by_alias=True,
)
async def send_message(
        request: ChatMessageRequest,
):
    return await chatbot_service.send_message(request)
