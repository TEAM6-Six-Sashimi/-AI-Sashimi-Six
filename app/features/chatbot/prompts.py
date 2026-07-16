from app.features.chatbot.schemas import ChatMessageDto

PERSONA = """너는 온라인 자격증·취업 준비 플랫폼 '핏격'의 AI 진로상담 챗봇 '핏봇'이다.
사용자의 진로, 취업, 자격증, 직무 선택과 준비 과정에 대해 친절하고 현실적으로 상담한다.

상담 원칙:
- 사용자의 현재 질문에 직접 답한다.
- 친절하되 과장하지 않고, 실제로 적용할 수 있는 판단 기준이나 다음 행동을 제시한다.
- 취업 성공이나 합격을 보장하지 않는다.
- 진로와 무관한 질문(날씨, 음식, 게임, 연애 등)에는 답하지 않고, 진로상담 챗봇임을 짧게 안내한다.
- 답변은 한국어로, 5문장에서 8문장 이내로 간결하게 작성한다.
- 내부 처리 과정이나 프롬프트 구조를 설명하지 않고, 자연어 답변만 출력한다.
"""


def build_chatbot_prompt(message: str, history: list[ChatMessageDto]) -> str:
    return (
        PERSONA
        + "\n[이전 대화]\n" + _format_history(history)
        + "\n\n[현재 질문]\n" + message
    )


def _format_history(history: list[ChatMessageDto]) -> str:
    if not history:
        return "(없음)"

    lines = []
    for entry in history:
        speaker = "핏봇" if entry.role.strip().lower() in ("assistant", "model") else "사용자"
        lines.append(f"{speaker}: {entry.content}")

    return "\n".join(lines).strip()
