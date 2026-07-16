from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

# 답변 생성 규정(V1) / 질문 분류 규정(V1)을 번들 파일에서 로드한다.
# 규정 문서 안의 {{USER_MESSAGE}} 등 placeholder를 실제 값으로 치환해 프롬프트를 만든다.
_ANSWER_REGULATION = (_PROMPTS_DIR / "answer_regulation.txt").read_text(encoding="utf-8")
_CLASSIFICATION_REGULATION = (
    _PROMPTS_DIR / "classification_regulation.txt"
).read_text(encoding="utf-8")

_NOT_PROVIDED = "제공되지 않음"


# 분류 규정도 길어(약 855줄) 입력이 문서 중간에 묻히므로, 규정 뒤에 실제 입력과
# "지금 분류하라"는 지시를 덧붙여 LLM의 마지막 지시가 "이 질문을 분류해 JSON만 출력"이 되게 한다.
_CLASSIFICATION_CLOSING_TEMPLATE = """

