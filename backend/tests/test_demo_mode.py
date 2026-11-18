import json
import os
import unittest
from functools import partial
from unittest.mock import patch

import httpx
from app.clients.ollama import OllamaClient
from main import create_app


class DemoModeTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_generates_three_and_combines_one_without_thinking(self):
        requests = []
        def handler(request):
            body = json.loads(request.content)
            requests.append(body)
            count = body["format"]["properties"]["ideas"]["minItems"]
            return httpx.Response(200, json={"response": json.dumps({"ideas": [
                {"title": f"아이디어 {i}", "description": "시간 관리를 돕습니다.", "tags": ["시간", "관리", "학습"]}
                for i in range(count)
            ]})})
        with patch.dict(os.environ, {"OLLAMA_DEMO_MODE": "true"}):
            with patch.dict(os.environ):
                os.environ.pop("OLLAMA_MODEL", None)
                async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as upstream:
                    with patch("app.services.ai_service.OllamaClient", side_effect=partial(OllamaClient, http_client=upstream)):
                        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url="http://test") as api:
                            generated = await api.post("/api/v1/generate", json={"keyword": "시간 관리", "count": 3})
                            self.assertEqual(generated.status_code, 200)
                            parents = generated.json()["ideas"][:2]
                            combined = await api.post("/api/v1/combine", json={"selected_ideas": parents, "count": 1})
        self.assertEqual(combined.status_code, 200)
        self.assertEqual(len(generated.json()["ideas"]), 3)
        self.assertEqual(len(combined.json()["ideas"]), 1)
        self.assertEqual(combined.json()["ideas"][0]["parent_ids"], [item["id"] for item in parents])
        for body, count in zip(requests, [3, 1]):
            self.assertIs(body["think"], False)
            self.assertEqual(body["model"], "qwen3:1.7b")
            self.assertEqual(body["format"]["properties"]["ideas"]["maxItems"], count)
            self.assertIn("tags", body["format"]["properties"]["ideas"]["items"]["required"])
            self.assertLess(len(body["system"]) + len(body["prompt"]), 600)

    async def test_client_only_sends_think_when_requested(self):
        bodies = []
        def handler(request):
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json={"response": "ok"})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = OllamaClient(http_client=http)
            await client.generate("qwen3:0.6b", "test", think=False)
            await client.generate("qwen2.5:7b", "test")
        self.assertIs(bodies[0]["think"], False)
        self.assertNotIn("think", bodies[1])
