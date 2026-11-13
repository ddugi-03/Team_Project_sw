from typing import Any


def generate_mock_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a placeholder response until the AI client is connected."""
    return {
        "status": "mock",
        "operation": "generate",
        "data": payload,
    }


def combine_mock_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a placeholder response until the AI client is connected."""
    return {
        "status": "mock",
        "operation": "combine",
        "data": payload,
    }
