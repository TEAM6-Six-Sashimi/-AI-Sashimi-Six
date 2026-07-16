class AiServerException(Exception):
    def __init__(
            self,
            error_code: str,
            message: str,
    ):
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class GeminiApiException(AiServerException):
    def __init__(self):
        super().__init__(
            "GEMINI_API_ERROR",
            "Gemini API 호출 중 오류가 발생했습니다.",
        )


class AiResponseParseException(AiServerException):
    def __init__(self):
        super().__init__(
            "AI_RESPONSE_PARSE_FAILED",
            "AI 응답을 파싱할 수 없습니다.",
        )