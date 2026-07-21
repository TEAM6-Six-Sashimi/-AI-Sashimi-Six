from pathlib import Path

from app.features.job_posting.schemas import JobPostingAnalyzeRequest


_PROMPTS_DIR = Path(__file__).parent / "prompt_templates"

_JOB_POSTING_ANALYSIS_REGULATION = (
    _PROMPTS_DIR / "job_posting_analysis_regulation.txt"
).read_text(encoding="utf-8")

_NOT_PROVIDED = "제공되지 않음"


_CLOSING_TEMPLATE = """

============================================================
[지금 분석할 실제 입력]
============================================================

위 「핏격 AI 채용공고 분석 엔진 운영규정」의 모든 조항을 준수하여,
아래 채용공고 본문을 분석한 결과를 지금 즉시 반환한다.

- 설명문, 인사말, 마크다운을 출력하지 않는다.
- Markdown 코드블록을 출력하지 않는다.
- 유효한 JSON 객체 하나만 출력한다.
- JSON 앞뒤에 어떠한 문장도 추가하지 않는다.
- 응답 key는 반드시 camelCase를 사용한다.
- 공고에 명시되지 않은 조건은 추론하지 않는다.
- 이력서 정보가 제공되지 않은 경우 fitAnalysis는 null로 반환한다.
- 실제 LMS 강의명, courseId, 강사명, 썸네일, 가격, 평점은 생성하지 않는다.
- Spring이 LMS DB에서 강의를 검색할 수 있도록 courseSearchCriteria를 반환한다.
- recommendationType은 반드시 CERTIFICATE만 사용한다.
- JOB_POSTING은 사용하지 않는다.
- 추천 가능한 자격증이 없으면 courseSearchCriteria는 빈 배열로 반환한다.

[채용공고 본문]
{content}

[이력서 기반 분석 여부]
{resume_based}

[이력서 요약]
{resume_content}

[최종 출력 명령]

지금 위 입력을 분석하고,
규정에서 정의한 JSON 스키마와 정확히 일치하는
유효한 JSON 객체 하나만 반환한다.
"""


def _normalize_optional_text(value: str | None) -> str:
    if value is None:
        return _NOT_PROVIDED

    normalized = value.strip()

    return normalized if normalized else _NOT_PROVIDED


def build_job_posting_analysis_prompt(
        request: JobPostingAnalyzeRequest,
) -> str:
    resume_content = _normalize_optional_text(request.resume_content)

    regulation = (
        _JOB_POSTING_ANALYSIS_REGULATION
        .replace("{{CONTENT}}", request.content)
        .replace("{{RESUME_BASED}}", str(request.resume_based).lower())
        .replace("{{RESUME_CONTENT}}", resume_content)
    )

    closing = _CLOSING_TEMPLATE.format(
        content=request.content,
        resume_based=str(request.resume_based).lower(),
        resume_content=resume_content,
    )

    return regulation + closing