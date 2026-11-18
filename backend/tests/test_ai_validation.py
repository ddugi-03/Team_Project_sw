import json
import unittest
from functools import partial
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx

from app.clients.ollama import OllamaClient
from app.core.exceptions import AIResponseParseException, execute_with_retry, parse_and_validate_ai_json
from main import create_app


def raw_ideas(count):
    return json.dumps({"ideas": [
        {"title": f"제목 {i}", "description": " 설명 ", "tags": ["학습"]}
        for i in range(count)
    ]})


class AIValidationTests(unittest.IsolatedAsyncioTestCase):
    def test_model_ids_and_parents_are_never_trusted(self):
        raw = json.dumps({"ideas": [
            {"id": "topic", "parent_ids": ["missing"], "title": "첫째", "description": "설명"},
            {"id": "topic", "parent_ids": "invalid", "title": "둘째", "description": "설명"},
        ]})
        items = parse_and_validate_ai_json(raw)
        self.assertEqual(len({item.id for item in items}), 2)
        for item in items:
            UUID(item.id)
            self.assertEqual(item.parent_ids, [])

    def test_blank_titles_and_descriptions_are_rejected(self):
        for field in ["title", "description"]:
            for blank in ["", " \n\t "]:
                with self.subTest(field=field, blank=blank):
                    data = {"title": "제목", "description": "설명", field: blank}
                    with self.assertRaises(AIResponseParseException):
                        parse_and_validate_ai_json(json.dumps({"ideas": [data]}))

    async def test_wrong_count_retries_and_recovers(self):
        call = AsyncMock(side_effect=[raw_ideas(1), raw_ideas(3)])
        items = await execute_with_retry(call, expected_count=3, delay=0)
        self.assertEqual(len(items), 3)
        self.assertEqual(call.await_count, 2)

    async def test_excess_count_is_also_rejected(self):
        call = AsyncMock(return_value=raw_ideas(3))
        with self.assertRaises(AIResponseParseException):
            await execute_with_retry(call, expected_count=2, delay=0)
        self.assertEqual(call.await_count, 3)

    async def test_blank_content_retries_and_recovers(self):
        call = AsyncMock(side_effect=[
            '{"ideas":[{"title":" ","description":"설명"}]}', raw_ideas(1)
        ])
        items = await execute_with_retry(call, expected_count=1, delay=0)
        self.assertEqual(items[0].description, "설명")
        self.assertEqual(call.await_count, 2)

    async def test_generation_and_combination_count_validation_reaches_api(self):
        for route, payload in [
            ("generate", {"keyword": "교육", "count": 3}),
            ("combine", {"count": 3, "selected_ideas": [
                {"id": id, "title": id, "description": "설명"} for id in ["a", "b"]
            ]}),
        ]:
            for recover in [True, False]:
                requests = []
                def handler(request):
                    requests.append(request)
                    count = 3 if recover and len(requests) > 1 else 1
                    return httpx.Response(200, json={"response": raw_ideas(count)})
                with self.subTest(route=route, recover=recover):
                    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as upstream:
                        with patch("app.services.ai_service.OllamaClient", side_effect=partial(OllamaClient, http_client=upstream)):
                            with patch("app.core.exceptions.asyncio.sleep", new_callable=AsyncMock):
                                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()), base_url="http://test") as api:
                                    response = await api.post("/api/v1/" + route, json=payload)
                    self.assertEqual(response.status_code, 200 if recover else 502)
                    self.assertEqual(len(requests), 2 if recover else 3)
                    if recover:
                        self.assertEqual(len(response.json()["ideas"]), 3)
                    else:
                        self.assertEqual(response.json()["error_code"], "AI_PARSE_ERROR")
