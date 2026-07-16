from pydantic import BaseModel, ConfigDict, Field


class ChatMessageDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str
    content: str


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(..., min_length=1)
    history: list[ChatMessageDto] = Field(default_factory=list)


class ChatReplyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reply: str
