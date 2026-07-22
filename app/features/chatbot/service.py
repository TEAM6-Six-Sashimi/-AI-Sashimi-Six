import asyncio
import logging

from app.features.chatbot import intent_classifier
from app.features.chatbot.classifier import Classifier
from app.features.chatbot.prompts import build_answer_prompt
from app.features.chatbot.rag import format_rag_context, retrieve
from app.features.chatbot.schemas import ChatRequest, ChatResponse, Classification
from app.shared.clients.gemini_client import GeminiClient

logger = logging.getLogger("uvicorn.error")


class ChatbotService:
    """진로상담 챗봇 서비스.

    흐름: ① 질문 분류 → ② RAG 검색(needsRag일 때) → ③ 답변 생성

    ①은 임베딩 유사도로 먼저 판정하고(약 40ms), 확신이 낮을 때만 LLM 분류(6~9초)로 넘긴다.

    각 단계는 실패해도 답변이 나오도록 방어한다.
    - 분류 실패 → 분류 없이 답변
    - RAG 실패/결과 없음 → RAG 없이 답변 (규정에 따라 일반 상담 방향만)
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

        # ③ 답변 생성 (규정 V2는 의도 라벨과 상담 단계를 입력으로 받는다)
        prompt = build_answer_prompt(
            user_message=request.user_message,
            conversation_context=request.conversation_context,
            intent_label=classification.intent if classification else None,
            counseling_stage=classification.stage if classification else None,
            rag_context=rag_context,
        )

        reply = await self.gemini_client.generate(prompt)

        return ChatResponse(reply=reply.strip())

    async def _classify(
            self,
            user_message: str,
            conversation_context: str | None,
    ) -> Classification | None:
        """① 임베딩 분류(약 40ms) → ② 확신이 낮을 때만 LLM 분류(6~9초)."""
        try:
            classification = await asyncio.to_thread(
                intent_classifier.classify, user_message
            )
            if classification:
                logger.info(
                    "[Chatbot] 임베딩 분류 %s / %s (유사도 %.3f)",
                    classification.intent, classification.rag_source_type,
                    classification.confidence,
                )
                return classification
        except Exception as exception:
            logger.warning("임베딩 분류 실패, LLM 분류로 넘깁니다: %r", exception)

        try:
            logger.info("[Chatbot] LLM 분류로 폴백")
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
            # ragKeywords를 함께 넘겨, 자격증은 종목명으로 좁혀 검색되게 한다.
            chunks = await asyncio.to_thread(
                retrieve,
                classification.rag_source_type,
                user_message,
                3,
                classification.rag_keywords,
            )
            if not chunks:
                return None
            return format_rag_context(chunks)
        except Exception as exception:
            logger.warning("RAG 검색 실패, RAG 없이 답변합니다: %r", exception)
            return None
