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

# 규정(V2) 뒤에 실제 입력을 덧붙인다. 규정만 보내면 LLM이 이를 "설명서"로 읽고
# 답변 대신 입력을 다시 요청하는 문제가 있어, 마지막 지시가 "이 질문에 답하라"가 되게 한다.
# 항목 이름은 규정 2절(입력 기준)에 적힌 것과 맞춘다.
_CLOSING_TEMPLATE = """

============================================================
[지금 답변할 실제 입력]

위 「핏격 AI 진로상담 답변 생성 엔진 운영규정 V2」를 준수하여,
아래 사용자 질문에 대한 상담 답변을 지금 즉시 생성한다.

- 규정을 요약하거나 "규정을 숙지했습니다" 같은 메타 발화를 하지 않는다.
- 입력을 다시 요청하지 않는다. 아래에 이미 입력이 제공되어 있다.
- 내부 라벨과 상담 단계는 사용자에게 노출하지 않는다.

userMessage:
{user_message}

intentLabel:
{intent_label}

counselingStage:
{counseling_stage}

retrievedContext:
{rag_context}

conversationSummary:
{conversation_context}
"""


def build_answer_prompt(
        user_message: str,
        conversation_context: str | None = None,
        intent_label: str | None = None,
        counseling_stage: str | None = None,
        rag_context: str | None = None,
) -> str:
    """답변 생성 규정(V2) + 실제 입력을 합쳐 최종 프롬프트를 만든다.

    규정 V2는 intentLabel·counselingStage를 받아 상담 단계별 답변 방식을 정하므로,
    분류 결과 전체(JSON)가 아니라 이 두 값만 전달한다.
    RAG 결과가 없으면 '제공되지 않음'으로 두고, 규정에 따라 일반 상담 방향만 답한다.
    """
    return _ANSWER_REGULATION + _CLOSING_TEMPLATE.format(
        user_message=user_message,
        intent_label=intent_label or _NOT_PROVIDED,
        counseling_stage=counseling_stage or _NOT_PROVIDED,
        rag_context=rag_context or _NOT_PROVIDED,
        conversation_context=conversation_context or _NOT_PROVIDED,
    )
