from typing import Any

from fastapi import APIRouter, Body

from app.services.mock_service import generate_mock_response


router = APIRouter(tags=["generate"])


@router.post("/generate")
def generate(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Accept a temporary request object and return a mock response."""
    return generate_mock_response(payload)
