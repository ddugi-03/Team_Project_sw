from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Team Project API",
        version="0.1.0",
    )
    application.include_router(api_v1_router)
    return application


app = create_app()
