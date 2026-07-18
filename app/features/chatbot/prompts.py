from pathlib import Path

_REGULATIONS_DIR = Path(__file__).parent / "regulations"

# 답변 생성 규정(V1) / 질문 분류 규정(V1)을 번들 파일에서 로드한다.
# 규정 문서 안의 {{USER_MESSAGE}} 등 placeholder를 실제 값으로 치환해 프롬프트를 만든다.
_ANSWER_REGULATION = (_REGULATIONS_DIR / "answer_regulation.txt").read_text(encoding="utf-8")
_CLASSIFICATION_REGULATION = (
    _REGULATIONS_DIR / "classification_regulation.txt"
).read_text(encoding="utf-8")

_NOT_PROVIDED = "제공되지 않음"


# 분류 규정도 길어(약 855줄) 입력이 문서 중간에 묻히므로, 규정 뒤에 실제 입력과
# "지금 분류하라"는 지시를 덧붙여 LLM의 마지막 지시가 "이 질문을 분류해 JSON만 출력"이 되게 한다.
_CLASSIFICATION_CLOSING_TEMPLATE = """

============================================================
[지금 분류할 실제 입력]

위 규정을 준수하여, 아래 사용자 질문을 분류한 결과를 지금 즉시 반환한다.

- 설명문, 인사말, 마크다운을 출력하지 않는다.
- 유효한 JSON 객체 하나만 출력한다.
- 위에서 정의한 intent, stage, questionType 외의 값을 새로 만들지 않는다.

[현재 사용자 질문]
{user_message}

[이전 대화 요약]
{conversation_context}
"""


def build_classification_prompt(
        user_message: str,
        conversation_context: str | None = None,
) -> str:
    """질문 분류 규정 + 실제 입력을 합쳐 분류용 프롬프트를 만든다.

    규정집 내용은 바꾸지 않고, 문서 뒤에 실제 입력을 덧붙여 LLM이 바로 분류 JSON을 내도록 한다.
    """
    conversation_context = conversation_context or _NOT_PROVIDED

    regulation = (
        _CLASSIFICATION_REGULATION
        .replace("{{USER_MESSAGE}}", user_message)
        .replace("{{CONVERSATION_CONTEXT}}", conversation_context)
    )

    closing = _CLASSIFICATION_CLOSING_TEMPLATE.format(
        user_message=user_message,
        conversation_context=conversation_context,
    )

    return regulation + closing

# 규정 문서가 길어(약 790줄) 실제 입력이 문서 중간(제4조)에 묻히면,
# LLM이 규정을 "설명서"로 인식해 답변 대신 입력을 다시 요청하는 문제가 있다.
# → 규정집 내용은 그대로 두고, 문서 뒤에 실제 입력과 "지금 답변하라"는 지시를 덧붙여,
#   LLM의 마지막 지시가 "이 질문에 답변만 출력"이 되도록 한다.
_CLOSING_TEMPLATE = """

============================================================
[지금 답변할 실제 입력]

위 「핏격 AI 진로상담 답변 생성 엔진 운영규정」의 모든 조항을 준수하여,
아래 사용자 질문에 대한 진로상담 답변을 지금 즉시 생성한다.

- 규정을 요약하거나 "규정을 숙지했습니다" 같은 메타 발화를 하지 않는다.
- 입력을 다시 요청하지 않는다. 아래에 이미 입력이 제공되어 있다.
- 내부 처리 정보나 형식 설명 없이, 사용자에게 하는 자연어 상담 답변만 출력한다.

[현재 사용자 질문]
{user_message}

[이전 대화 요약]
{conversation_context}

[질문 분류 결과 JSON]
{classification_json}

[RAG 참고 정보]
{rag_context}

[핏격 서비스 정보]
{service_context}
"""


def build_answer_prompt(
        user_message: str,
        conversation_context: str | None = None,
        classification_json: str | None = None,
        rag_context: str | None = None,
        service_context: str | None = None,
) -> str:
    """답변 생성 규정 + 실제 입력을 합쳐 최종 프롬프트를 만든다.

    규정집(_ANSWER_REGULATION) 내용은 바꾸지 않고, 문서 뒤에 실제 입력을 덧붙여
    LLM이 규정을 따르며 실제 질문에 바로 답하도록 한다.

    Phase 1(현재)에서는 분류 결과/RAG가 없어 '제공되지 않음'으로 채운다.
    (규정 제41조: RAG 정보가 비어 있으면 일반적인 상담 방향만 제공한다)
    Phase 2~3에서 classification_json, rag_context가 실제 값으로 채워진다.
    """
    conversation_context = conversation_context or _NOT_PROVIDED
    classification_json = classification_json or _NOT_PROVIDED
    rag_context = rag_context or _NOT_PROVIDED
    service_context = service_context or _NOT_PROVIDED

    regulation = (
        _ANSWER_REGULATION
        .replace("{{USER_MESSAGE}}", user_message)
        .replace("{{CONVERSATION_CONTEXT}}", conversation_context)
        .replace("{{CLASSIFICATION_JSON}}", classification_json)
        .replace("{{RAG_CONTEXT}}", rag_context)
        .replace("{{FITGYEOK_SERVICE_CONTEXT}}", service_context)
    )

    closing = _CLOSING_TEMPLATE.format(
        user_message=user_message,
        conversation_context=conversation_context,
        classification_json=classification_json,
        rag_context=rag_context,
        service_context=service_context,
    )

    return regulation + closing
