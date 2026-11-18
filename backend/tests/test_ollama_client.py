import json
import os
import unittest
from unittest.mock import patch

import httpx

from app.clients.ollama import OllamaClient


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    """HTTP transport mocks only. These tests require no Ollama server."""

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

    async def test_generate_forwards_extended_parameters(self) -> None:
        options = {"temperature": 0.7, "num_ctx": 1024, "num_predict": 512}

        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                json.loads(request.content),
                {
                    "model": "demo-model",
                    "prompt": "demo prompt",
                    "stream": False,
                    "system": "system instructions",
                    "format": "json",
                    "options": options,
                },
            )
            self.assertEqual(request.extensions["timeout"]["read"], 60.0)
            return httpx.Response(200, json={"response": "generated"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            async with OllamaClient(timeout=60.0, http_client=http_client) as client:
                await client.generate(
                    "demo-model", "demo prompt",
                    system="system instructions", format="json", options=options,
                )
            self.assertFalse(http_client.is_closed)

    async def test_generate_preserves_empty_parameters_and_schema_format(self) -> None:
        schema = {"type": "object", "properties": {"ideas": {"type": "array"}}}

        async def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            self.assertEqual(payload["system"], "")
            self.assertEqual(payload["format"], schema)
            self.assertEqual(payload["options"], {})
            return httpx.Response(200, json={"response": "generated"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = OllamaClient(http_client=http_client)
            await client.generate("demo-model", "demo prompt", system="", format=schema, options={})

    async def test_generate_omits_explicit_none_parameters(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                json.loads(request.content),
                {"model": "demo-model", "prompt": "demo prompt", "stream": False},
            )
            return httpx.Response(200, json={"response": "generated"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = OllamaClient(http_client=http_client)
            await client.generate("demo-model", "demo prompt", system=None, format=None, options=None)

    async def test_owned_http_client_is_closed_by_context_manager(self) -> None:
        async with OllamaClient() as client:
            http_client = client._get_http_client()
            self.assertFalse(http_client.is_closed)

        self.assertTrue(http_client.is_closed)
        await client.aclose()

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
