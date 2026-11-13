import os
from typing import Any

import httpx


class OllamaClient:
    """Small async HTTP client for Ollama's non-streaming endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        configured_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self.base_url = configured_url.rstrip("/")
        self.timeout = timeout
        self._http_client = http_client
        self._owns_http_client = http_client is None

    async def generate(self, model: str, prompt: str) -> dict[str, Any]:
        """Call Ollama's /api/generate endpoint without streaming."""
        return await self._post(
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Call Ollama's /api/chat endpoint without streaming."""
        return await self._post(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
            },
        )

    async def aclose(self) -> None:
        """Close the internally created HTTP client, if there is one."""
        if self._http_client is not None and self._owns_http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.aclose()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._get_http_client().post(
            f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        response_json = response.json()
        if not isinstance(response_json, dict):
            raise ValueError("Ollama response must be a JSON object")
        return response_json

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient()
        return self._http_client
