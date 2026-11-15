"""FastAPI -> AI service -> OllamaClient tests using mocked HTTP transport.

No test in this module contacts a real Ollama server or loads a model.
"""

import json
import os
import unittest
from functools import partial
from unittest.mock import patch
from uuid import UUID

import httpx

from app.clients.ollama import OllamaClient
from app.core.exceptions import AIResponseParseException
from app.schemas.idea import IdeaResponse
from app.services import ai_service
from main import create_app


class APIIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        for name in ("OLLAMA_BASE_URL", "OLLAMA_MODEL", "CORS_ALLOW_ORIGINS"):
            os.environ.pop(name, None)

        self.requests: list[httpx.Request] = []
        self.ideas = [
            {"title": "학습 도우미", "description": "매일 학습을 돕는 서비스", "tags": ["학습", "일정", "관리"]},
            {"title": "집중 타이머", "description": "집중 시간을 관리하는 서비스", "tags": ["집중", "시간", "관리"]},
        ]
        self.ollama_status = 200
        self.ollama_response = {"response": json.dumps({"ideas": self.ideas}, ensure_ascii=False)}
        self.ollama_error: type[httpx.RequestError] | None = None
        self.ollama_http = httpx.AsyncClient(transport=httpx.MockTransport(self.handle_ollama))
        self.addAsyncCleanup(self.ollama_http.aclose)
        client_patch = patch(
            "app.services.ai_service.OllamaClient",
            side_effect=partial(OllamaClient, http_client=self.ollama_http),
        )
        self.client_factory = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.api = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app()), base_url="http://api.test",
        )
        self.addAsyncCleanup(self.api.aclose)

    async def handle_ollama(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.ollama_error is not None:
            raise self.ollama_error("mock upstream failure", request=request)
        return httpx.Response(self.ollama_status, json=self.ollama_response)

    def assert_idea_response(self, response: httpx.Response, message: str) -> None:
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"status", "message", "ideas"})
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["message"], message)
        parsed = IdeaResponse.model_validate(body)
        self.assertEqual(len(parsed.ideas), len(self.ideas))
        for actual, expected in zip(body["ideas"], self.ideas):
            self.assertEqual(set(actual), {"id", "title", "description", "tags", "parent_ids"})
            UUID(actual["id"])
            self.assertEqual(actual["parent_ids"], [])
            for field, value in expected.items():
                self.assertEqual(actual[field], value)

    def assert_ollama_payload(self) -> dict:
        self.assertEqual(len(self.requests), 1)
        request = self.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(str(request.url), "http://localhost:11434/api/generate")
        self.assertEqual(request.extensions["timeout"]["read"], 60.0)
        payload = json.loads(request.content)
        self.assertEqual(set(payload), {"model", "prompt", "stream", "system", "format", "options"})
        self.assertEqual(payload["model"], "qwen2.5:7b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["system"], ai_service.COMMON_SYSTEM_PROMPT)
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["options"], {
            "temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.1,
            "num_ctx": 1024, "num_predict": 512,
        })
        self.client_factory.assert_called_once_with(timeout=60.0)
        return payload

    async def test_generate_response_and_async_client_flow(self) -> None:
        response = await self.api.post("/api/v1/generate", json={
            "keyword": "학습", "category": "교육", "count": 2, "creativity_level": 0.2,
        })
        self.assert_idea_response(response, "아이디어 생성 완료")
        payload = self.assert_ollama_payload()
        self.assertIn("- 주제 키워드: 학습", payload["prompt"])
        self.assertIn("- 분야(카테고리): 교육", payload["prompt"])
        self.assertIn("- 생성 개수: 정확히 2개", payload["prompt"])

    async def test_generate_defaults_and_null_category(self) -> None:
        for extra in ({}, {"category": None}):
            with self.subTest(extra=extra):
                self.requests.clear()
                response = await self.api.post("/api/v1/generate", json={"keyword": "학습", **extra})
                self.assert_idea_response(response, "아이디어 생성 완료")
                payload = json.loads(self.requests[0].content)
                self.assertIn("- 분야(카테고리): 일반", payload["prompt"])
                self.assertIn("- 생성 개수: 정확히 3개", payload["prompt"])

    async def test_combine_response_and_async_client_flow(self) -> None:
        response = await self.api.post("/api/v1/combine", json={
            "selected_ideas": self.ideas, "direction": "학습 효과 향상", "count": 2,
        })
        self.assert_idea_response(response, "아이디어 조합 완료")
        payload = self.assert_ollama_payload()
        self.assertIn("새로운 융합 아이디어 2개", payload["prompt"])
        self.assertIn("학습 효과 향상", payload["prompt"])
        for idea in self.ideas:
            self.assertIn(idea["title"], payload["prompt"])
            self.assertIn(idea["description"], payload["prompt"])

    async def test_combine_defaults_and_null_direction(self) -> None:
        cases = [
            ({}, "두 아이디어의 핵심 장점을 결합한 시너지 서비스"),
            ({"direction": None}, "두 아이디어의 장점 결합"),
        ]
        for extra, expected_direction in cases:
            with self.subTest(extra=extra):
                self.requests.clear()
                response = await self.api.post("/api/v1/combine", json={"selected_ideas": self.ideas, **extra})
                self.assert_idea_response(response, "아이디어 조합 완료")
                payload = json.loads(self.requests[0].content)
                self.assertIn(expected_direction, payload["prompt"])
                self.assertIn("새로운 융합 아이디어 2개", payload["prompt"])

    async def test_remote_url_and_model_are_configurable(self) -> None:
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "https://ollama.example.test:11434/",
            "OLLAMA_MODEL": "configured-model:latest",
        }):
            response = await self.api.post("/api/v1/generate", json={"keyword": "학습"})
        self.assert_idea_response(response, "아이디어 생성 완료")
        self.assertEqual(str(self.requests[0].url), "https://ollama.example.test:11434/api/generate")
        self.assertEqual(json.loads(self.requests[0].content)["model"], "configured-model:latest")

    async def test_existing_request_validation_rejects_invalid_payloads(self) -> None:
        cases = [
            ("generate", {}),
            ("generate", {"keyword": ""}),
            ("generate", {"keyword": "학습", "count": 0}),
            ("generate", {"keyword": "학습", "count": 11}),
            ("generate", {"keyword": "학습", "creativity_level": -0.1}),
            ("generate", {"keyword": "학습", "creativity_level": 1.1}),
            ("combine", {"idea_ids": ["one", "two"]}),
            ("combine", {"selected_ideas": self.ideas[:1]}),
            ("combine", {"selected_ideas": self.ideas, "count": 0}),
            ("combine", {"selected_ideas": self.ideas, "count": 6}),
        ]
        for endpoint, body in cases:
            with self.subTest(endpoint=endpoint, body=body):
                response = await self.api.post(f"/api/v1/{endpoint}", json=body)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.requests, [])

    async def test_existing_http_error_mapping_is_preserved(self) -> None:
        self.ollama_status = 503
        with self.assertRaisesRegex(AIResponseParseException, "Ollama API 통신 실패"):
            await self.api.post("/api/v1/generate", json={"keyword": "학습"})
        self.assertEqual(len(self.requests), 1)

    async def test_existing_connection_and_timeout_mapping_is_preserved(self) -> None:
        for error in (httpx.ConnectError, httpx.ReadTimeout):
            with self.subTest(error=error):
                self.ollama_error = error
                with self.assertRaisesRegex(AIResponseParseException, "Ollama API 통신 실패"):
                    await self.api.post("/api/v1/combine", json={"selected_ideas": self.ideas})

    async def test_existing_parser_accepts_markdown_json(self) -> None:
        self.ollama_response = {"response": f"```json\n{json.dumps({'ideas': self.ideas})}\n```"}
        response = await self.api.post("/api/v1/generate", json={"keyword": "학습"})
        self.assert_idea_response(response, "아이디어 생성 완료")

    async def test_existing_parser_failure_is_preserved(self) -> None:
        self.ollama_response = {"response": "invalid model output"}
        with self.assertRaises(AIResponseParseException):
            await self.api.post("/api/v1/generate", json={"keyword": "학습"})
        self.assertEqual(len(self.requests), 1)

    async def test_allowed_origin_is_returned_on_generate_response(self) -> None:
        response = await self.api.post(
            "/api/v1/generate", json={"keyword": "학습"},
            headers={"Origin": "http://localhost:5173"},
        )
        self.assert_idea_response(response, "아이디어 생성 완료")
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


class CORSTests(unittest.IsolatedAsyncioTestCase):
    async def preflight(
        self,
        origin: str,
        method: str = "POST",
        headers: str = "content-type",
        endpoint: str = "generate",
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app()), base_url="http://api.test",
        ) as client:
            return await client.options(f"/api/v1/{endpoint}", headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": headers,
            })

    async def asyncSetUp(self) -> None:
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("CORS_ALLOW_ORIGINS", None)

    async def test_default_development_origins_allow_json_post(self) -> None:
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"):
            for endpoint in ("generate", "combine"):
                with self.subTest(origin=origin, endpoint=endpoint):
                    response = await self.preflight(origin, endpoint=endpoint)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["access-control-allow-origin"], origin)
                    self.assertIn("POST", response.headers["access-control-allow-methods"])
                    self.assertIn("content-type", response.headers["access-control-allow-headers"].lower())
                    self.assertIn("Origin", response.headers["vary"])

    async def test_unconfigured_origins_are_rejected(self) -> None:
        for origin in ("https://untrusted.test", "http://localhost:5173.evil.test", "null"):
            with self.subTest(origin=origin):
                response = await self.preflight(origin)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn("access-control-allow-origin", response.headers)

    async def test_environment_overrides_defaults_and_trims_origins(self) -> None:
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": " https://ui.test, ,https://preview.test, "}):
            for origin in ("https://ui.test", "https://preview.test"):
                response = await self.preflight(origin)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], origin)
            response = await self.preflight("http://localhost:5173")
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("access-control-allow-origin", response.headers)

    async def test_empty_origin_setting_disables_cross_origin_access(self) -> None:
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": ""}):
            response = await self.preflight("http://localhost:5173")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    async def test_unconfigured_method_is_rejected(self) -> None:
        response = await self.preflight("http://localhost:5173", method="DELETE")
        self.assertEqual(response.status_code, 400)

    async def test_unconfigured_header_is_rejected(self) -> None:
        response = await self.preflight("http://localhost:5173", headers="x-unconfigured-header")
        self.assertEqual(response.status_code, 400)
