from fastapi import APIRouter

from app.features.chatbot.schemas import ChatRequest, ChatResponse
from app.features.chatbot.service import ChatbotService

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)

chatbot_service = ChatbotService()


@router.post(
    "/messages",
    response_model=ChatResponse,
    response_model_by_alias=True,
)
async def chat(
        request: ChatRequest,
):
    return await chatbot_service.chat(request)
