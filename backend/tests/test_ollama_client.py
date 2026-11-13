import os
import unittest
from unittest.mock import patch

import httpx

from app.clients.ollama import OllamaClient


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_posts_expected_payload_and_returns_json(self) -> None:
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json={"response": "generated"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = OllamaClient(
                base_url="http://ollama.test",
                http_client=http_client,
            )
            result = await client.generate("demo-model", "demo prompt")

        self.assertEqual(result, {"response": "generated"})
        self.assertEqual(str(requests[0].url), "http://ollama.test/api/generate")
        self.assertEqual(
            httpx.Request.read(requests[0]),
            b'{"model":"demo-model","prompt":"demo prompt","stream":false}',
        )

    async def test_chat_posts_expected_payload_and_returns_json(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(str(request.url), "http://ollama.test/api/chat")
            return httpx.Response(200, json={"message": {"content": "ok"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = OllamaClient(
                base_url="http://ollama.test/",
                http_client=http_client,
            )
            result = await client.chat(
                "demo-model",
                [{"role": "user", "content": "hello"}],
            )

        self.assertEqual(result, {"message": {"content": "ok"}})

    async def test_environment_variable_configures_base_url(self) -> None:
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://configured.test/"}):
            client = OllamaClient()

        self.assertEqual(client.base_url, "http://configured.test")

    async def test_http_error_is_raised(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "unavailable"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = OllamaClient(http_client=http_client)
            with self.assertRaises(httpx.HTTPStatusError):
                await client.generate("demo-model", "demo prompt")

    async def test_non_object_json_response_is_rejected(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=["not", "an", "object"])

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = OllamaClient(http_client=http_client)
            with self.assertRaisesRegex(ValueError, "JSON object"):
                await client.generate("demo-model", "demo prompt")

    async def test_connection_error_is_propagated(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = OllamaClient(http_client=http_client)
            with self.assertRaises(httpx.ConnectError):
                await client.generate("demo-model", "demo prompt")


if __name__ == "__main__":
    unittest.main()
