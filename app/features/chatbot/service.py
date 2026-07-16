import asyncio
import logging

from app.features.chatbot.classifier import Classifier
from app.features.chatbot.prompts import build_answer_prompt
from app.features.chatbot.rag import format_rag_context, retrieve
from app.features.chatbot.schemas import ChatRequest, ChatResponse, Classification
from app.shared.clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ChatbotService:
    """진로상담 챗봇 서비스.

    흐름: ① 질문 분류(classifier) → ② RAG 검색(needsRag일 때) → ③ 답변 생성(answer)

    각 단계는 실패해도 답변이 나오도록 방어한다.
    - 분류 실패 → 분류 없이 답변
    - RAG 실패/결과 없음 → RAG 없이 답변 (규정 제41조: 일반 상담 방향만)
    """

    def __init__(self):
        self.gemini_client = GeminiClient()
        self.classifier = Classifier()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # ① 분류
        classification = await self._classify(
            request.user_message,
            request.conversation_context,
        )

        # ② RAG 검색 (분류 결과가 needsRag일 때만)
        rag_context = await self._retrieve_rag(classification, request.user_message)

        # ③ 답변 생성
        classification_json = (
            classification.model_dump_json(by_alias=True, indent=2)
            if classification
            else None
        )

        prompt = build_answer_prompt(
            user_message=request.user_message,
            conversation_context=request.conversation_context,
            classification_json=classification_json,
            rag_context=rag_context,
        )

        reply = await self.gemini_client.generate(prompt)

        return ChatResponse(reply=reply.strip())

    async def _classify(
            self,
            user_message: str,
            conversation_context: str | None,
    ) -> Classification | None:
        try:
            return await self.classifier.classify(user_message, conversation_context)
        except Exception as exception:
            logger.warning("질문 분류 실패, 분류 없이 답변합니다: %r", exception)
            return None

    async def _retrieve_rag(
            self,
            classification: Classification | None,
            user_message: str,
    ) -> str | None:
        if not classification or not classification.needs_rag:
            return None
        try:
            # chromadb 검색은 동기 함수라 이벤트 루프를 막지 않도록 스레드로 실행
            chunks = await asyncio.to_thread(
                retrieve,
                classification.rag_source_type,
                user_message,
            )
            if not chunks:
                return None
            return format_rag_context(chunks)
        except Exception as exception:
            logger.warning("RAG 검색 실패, RAG 없이 답변합니다: %r", exception)
            return None
