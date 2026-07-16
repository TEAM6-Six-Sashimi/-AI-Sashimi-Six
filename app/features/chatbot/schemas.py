from pydantic import BaseModel, ConfigDict, Field


class UserContext(BaseModel):
    """분류 결과에서 추출한 최소 상담 정보."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    major_field: str | None = Field(default=None, alias="majorField")
    current_status: str | None = Field(default=None, alias="currentStatus")
    target_job: str | None = Field(default=None, alias="targetJob")
    industry: str | None = None
    certificates: list[str] = Field(default_factory=list)
    concern: str | None = None
    has_specific_goal: bool = Field(default=False, alias="hasSpecificGoal")


class Classification(BaseModel):
    """질문 분류 엔진(LLM)이 반환하는 분류 결과.

    LLM 출력이 일부 어긋나도 견디도록 기본값을 넉넉히 두고 extra 필드는 무시한다.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    intent: str = "UNKNOWN"
    secondary_intents: list[str] = Field(default_factory=list, alias="secondaryIntents")
    stage: str = "REDIRECT"
    question_type: str = Field(default="UNKNOWN", alias="questionType")
    confidence: float = 0.0
    user_context: UserContext = Field(default_factory=UserContext, alias="userContext")
    needs_clarification: bool = Field(default=False, alias="needsClarification")
    clarification_question: str | None = Field(default=None, alias="clarificationQuestion")
    needs_rag: bool = Field(default=False, alias="needsRag")
    rag_source_type: str = Field(default="NONE", alias="ragSourceType")
    rag_keywords: list[str] = Field(default_factory=list, alias="ragKeywords")
    site_guide_type: str = Field(default="NONE", alias="siteGuideType")
    reason: str = ""


class ChatRequest(BaseModel):
    """Spring이 보내는 챗봇 요청.

    userMessage: 현재 사용자 질문
    conversationContext: 이전 대화 요약(없으면 None). Spring이 history를 문자열로 합쳐 전달한다.
    """

    model_config = ConfigDict(populate_by_name=True)

    user_message: str = Field(..., alias="userMessage", min_length=1)
    conversation_context: str | None = Field(default=None, alias="conversationContext")


class ChatResponse(BaseModel):
    """챗봇 응답. AI가 생성한 자연어 답변."""

    model_config = ConfigDict(populate_by_name=True)

    reply: str
