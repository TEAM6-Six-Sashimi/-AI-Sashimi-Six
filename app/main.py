from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import AiServerException
from app.health.router import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SASHIMI AI Server",
        description="FastAPI server for SASHIMI-SIX AI features",
        version="0.1.0",
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