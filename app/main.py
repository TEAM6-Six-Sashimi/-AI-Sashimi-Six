import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import AiServerException
from app.health.router import router as health_router

# uvicorn이 설정해 둔 로거를 쓴다(앱 자체 로거는 기본 설정에서 출력되지 않는다).
logger = logging.getLogger("uvicorn.error")


def _warmup_chatbot_rag() -> None:
    """챗봇 RAG 임베딩 모델을 미리 로드한다.

    실패해도 서버는 정상 기동한다(첫 요청이 느려질 뿐이며, 다른 기능과는 무관하다).
    """
    try:
        from app.features.chatbot.rag import warmup

        warmup()
        logger.info("[Chatbot] RAG 워밍업 완료")
    except Exception as exception:
        logger.warning(
            "[Chatbot] RAG 워밍업 실패 - 첫 요청이 느려질 수 있습니다: %r", exception
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 모델 로딩은 수십 초가 걸리므로 백그라운드로 돌린다.
    # 기동을 막으면 배포 헬스체크(150초 제한)가 지연될 수 있다.
    threading.Thread(target=_warmup_chatbot_rag, daemon=True).start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SASHIMI AI Server",
        description="FastAPI server for SASHIMI-SIX AI features",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.exception_handler(AiServerException)
    async def ai_server_exception_handler(
            request: Request,
            exception: AiServerException,
    ):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "errorCode": exception.error_code,
                "message": exception.message,
                "path": request.url.path,
            },
        )

    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_app()