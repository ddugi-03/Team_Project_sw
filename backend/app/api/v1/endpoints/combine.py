from typing import Any

from fastapi import APIRouter, Body

from app.services.mock_service import combine_mock_response


router = APIRouter(tags=["combine"])


@router.post("/combine")
def combine(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Accept a temporary request object and return a mock response."""
    return combine_mock_response(payload)
