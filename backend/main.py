import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Team Project API",
        version="0.1.0",
    )
    configured_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ],
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )
    # TODO(BE-B): 전역 AI 파싱/연결 예외 핸들러 적용 여부 확인.
    application.include_router(api_v1_router)
    return application


app = create_app()
