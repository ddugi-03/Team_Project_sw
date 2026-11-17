from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.exceptions import (
    AIResponseParseException, OllamaConnectionException,
    ai_parse_exception_handler, ollama_conn_exception_handler,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Team Project API",
        version="0.1.0",
    )
    application.add_exception_handler(AIResponseParseException, ai_parse_exception_handler)
    application.add_exception_handler(OllamaConnectionException, ollama_conn_exception_handler)
    application.include_router(api_v1_router)
    return application


app = create_app()

