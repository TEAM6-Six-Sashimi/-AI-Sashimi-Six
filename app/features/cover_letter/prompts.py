import json
from pathlib import Path

from app.features.cover_letter.schemas import CoverLetterReviewRequest


_PROMPTS_DIR = Path(__file__).parent / "prompt_templates"

_COVER_LETTER_REVIEW_REGULATION = (
    _PROMPTS_DIR / "cover_letter_review_regulation.txt"
).read_text(encoding="utf-8")

_NOT_PROVIDED = "제공되지 않음"


_CLOSING_TEMPLATE = """

============================================================
[지금 첨삭할 실제 입력]
============================================================

위 「핏격 AI 자기소개서 첨삭 엔진 운영규정」의 모든 조항을 준수하여,
아래 자기소개서 문항에 대한 첨삭 결과를 지금 즉시 반환한다.

- 점수, 백분율, 등급, 순위, 합격 가능성을 생성하지 않는다.
- 입력된 문항만 첨삭한다.
- EMPTY 상태를 반환하지 않는다.
- questionKey는 입력값을 그대로 사용한다.
- 입력 문항 순서와 응답 문항 순서를 동일하게 유지한다.
- 모든 필수 key를 포함한다.
- 응답 key는 반드시 camelCase를 사용한다.
- Markdown 코드블록, 설명문, 인사말, 주석을 출력하지 않는다.
- 유효한 JSON 객체 하나만 출력한다.
- JSON 앞뒤에 어떠한 문장도 추가하지 않는다.

[자기소개서 문항 배열]
{questions_json}

[이력서 요약 참고자료]
{resume_summary}

[채용공고 요약 참고자료]
{job_posting_summary}

[RAG 참고 정보]
{rag_context}

[최종 출력 명령]

지금 위 입력을 첨삭하고,
규정에서 정의한 JSON 스키마와 정확히 일치하는
유효한 JSON 객체 하나만 반환한다.
"""


def _normalize_optional_text(value: str | None) -> str:
    if value is None:
        return _NOT_PROVIDED

    normalized = value.strip()

    return normalized if normalized else _NOT_PROVIDED


def build_cover_letter_review_prompt(
    request: CoverLetterReviewRequest,
    rag_context: str | None = None,
) -> str:
    if not request.questions:
        raise ValueError(
            "자기소개서 첨삭을 위해 최소 1개 이상의 문항이 필요합니다."
        )

    questions_payload = [
        {
            "questionKey": question.question_key,
            "questionTitle": question.question_title,
            "content": question.content.strip(),
        }
        for question in request.questions
        if question.content and question.content.strip()
    ]

    if not questions_payload:
        raise ValueError(
            "자기소개서 첨삭을 위해 최소 1개 이상의 작성된 문항이 필요합니다."
        )

    questions_json = json.dumps(
        questions_payload,
        ensure_ascii=False,
        indent=2,
    )

    resume_summary = _normalize_optional_text(request.resume_summary)
    job_posting_summary = _normalize_optional_text(
        request.job_posting_summary
    )
    normalized_rag_context = _normalize_optional_text(rag_context)

    regulation = (
        _COVER_LETTER_REVIEW_REGULATION
        .replace("{{QUESTIONS_JSON}}", questions_json)
        .replace("{{RESUME_SUMMARY}}", resume_summary)
        .replace("{{JOB_POSTING_SUMMARY}}", job_posting_summary)
        .replace("{{RAG_CONTEXT}}", normalized_rag_context)
    )

    closing = _CLOSING_TEMPLATE.format(
        questions_json=questions_json,
        resume_summary=resume_summary,
        job_posting_summary=job_posting_summary,
        rag_context=normalized_rag_context,
    )

    return regulation + closing