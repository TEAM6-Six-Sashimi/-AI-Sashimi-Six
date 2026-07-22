"""의도 분류(임베딩) — LLM을 부르지 않고 유사도로 질문 의도를 판정한다.

기존 LLM 분류는 규정집 약 15,000자를 매 요청마다 보내 6~9초가 걸렸다.
여기서는 미리 색인해 둔 예시 질문과의 유사도로 판정해 약 40ms에 끝낸다.
확신이 낮으면(SIMILARITY_THRESHOLD 미만) None을 돌려주고, 호출부가 LLM 분류로 넘긴다.

임베딩 모델은 rag 모듈의 것을 그대로 쓴다(약 440MB를 두 번 올리지 않기 위함).
"""
import logging
from functools import lru_cache

from app.features.chatbot.rag import INTENTS_COLLECTION, certificate_names, get_collection
from app.features.chatbot.schemas import Classification

logger = logging.getLogger("uvicorn.error")

# 이 값 미만이면 확신이 없다고 보고 LLM 분류로 넘긴다.
# 측정 결과 0.55에서 약 90%가 임베딩으로 처리되고 그중 정확도 약 88%였다.
SIMILARITY_THRESHOLD = 0.55

# 의도 라벨 → (RAG 사용 여부, 검색할 자료). 라벨은 data/intents.csv 기준.
_FITGYEOK_LABELS = frozenset({
    "JOB_POSTING_ANALYSIS", "COURSE_RECOMMENDATION",
    "RESUME_REVIEW", "COVER_LETTER_REVIEW", "AI_FEATURE_QUESTION",
})
# NCS 직무 자료는 102건뿐이라 적중률이 낮아 검색 대상에서 제외한다.
# 자격증 자료는 라벨이 아니라 종목명 매칭으로 판단한다(아래 _certificate_keywords 참고).


def _routing(label: str) -> tuple[bool, str]:
    if label in _FITGYEOK_LABELS:
        return True, "FITGYEOK_AI"
    return False, "NONE"


def _stage_of(label: str, stage_name: str) -> str:
    """규정 V2가 참조하는 상담 단계 이름."""
    return stage_name or "범위 외 질문"


def _certificate_keywords(user_message: str) -> list[str]:
    """질문에 포함된 자격증 종목명을 찾는다(사전 매칭, 1ms 내외).

    LLM 없이 ragKeywords를 만들기 위한 것으로, 긴 이름을 우선한다.
    (예: '정보처리산업기사'가 '정보처리기사'보다 먼저 오도록)
    """
    names = certificate_names()
    found = [name for name in names if name and name in user_message]
    return sorted(found, key=len, reverse=True)


@lru_cache(maxsize=1)
def _collection():
    return get_collection(INTENTS_COLLECTION)


def classify(user_message: str) -> Classification | None:
    """의도를 분류한다. 확신이 낮으면 None(→ 호출부에서 LLM 분류로 폴백)."""
    try:
        result = _collection().query(query_texts=[user_message], n_results=1)
    except Exception as exception:
        logger.warning("[Chatbot] 임베딩 분류 실패, LLM 분류로 넘깁니다: %r", exception)
        return None

    if not result["ids"][0]:
        return None

    metadata = result["metadatas"][0][0] or {}
    similarity = 1 - result["distances"][0][0]
    label = metadata.get("label", "UNKNOWN")

    if similarity < SIMILARITY_THRESHOLD:
        logger.info("[Chatbot] 임베딩 분류 확신 부족(%.3f) → LLM 분류", similarity)
        return None

    needs_rag, rag_source_type = _routing(label)
    keywords = _certificate_keywords(user_message)

    # 질문에 자격증 종목명이 들어 있으면 라벨과 무관하게 자격증 자료를 본다.
    # (예: "정보처리기사 시험 과목" → 라벨은 학습계획이어도 자격증 정보가 필요하다)
    if keywords:
        needs_rag, rag_source_type = True, "CERTIFICATE"

    return Classification(
        intent=label,
        stage=_stage_of(label, metadata.get("stage_name", "")),
        confidence=similarity,
        needs_rag=needs_rag,
        rag_source_type=rag_source_type,
        rag_keywords=keywords,
        reason=f"임베딩 유사도 {similarity:.3f} (예시: {metadata.get('example', '')[:30]})",
    )
