import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.exceptions import (
    AIResponseParseException,
    OllamaConnectionException,
    ai_parse_exception_handler,
    ollama_conn_exception_handler,
)
from app.services.idea_registry import IdeaRegistry


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

    # BE-A: ID만 보내는 FE의 combine 요청에 맞춰 최근 아이디어를 일시 저장.
    # TODO(BE-A/FE): 운영 시 세션별 영구 저장소로 교체하거나 FE가 아이디어 본문을 전달하도록 계약 확정.
    application.state.idea_registry = IdeaRegistry()

    # BE-A: BE-B가 이미 구현한 예외 핸들러를 앱에 등록(구현 자체는 변경하지 않음).
    application.add_exception_handler(AIResponseParseException, ai_parse_exception_handler)
    application.add_exception_handler(OllamaConnectionException, ollama_conn_exception_handler)
    # TODO(BE-B): 통신 실패를 OllamaConnectionException으로 변환하는 정책 및 Retry 적용 검토.

    application.include_router(api_v1_router)
    return application


app = create_app()
