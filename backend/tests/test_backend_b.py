import json
import unittest
from unittest.mock import AsyncMock, patch
from functools import partial
from app.clients.ollama import OllamaClient

import httpx
from fastapi.testclient import TestClient

from main import create_app
from app.core.exceptions import AIResponseParseException, OllamaConnectionException
from app.schemas.idea import IdeaItem
from app.services.ai_service import _call_ollama, combine_ideas_service
from app.services.canvas_service import ideas_to_canvas


def idea(id, parents=None):
    return IdeaItem(id=id, title="제목 " + id, description="설명 " + id, parent_ids=parents or [])


class CombinationTests(unittest.IsolatedAsyncioTestCase):
    async def test_prompt_and_authoritative_parent_mapping(self):
        selected = [idea("a"), idea("b")]
        generated = idea("a", ["invented"])
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, return_value=[generated]) as call:
            results = await combine_ideas_service(selected, direction="교육", count=1)
        prompt = call.call_args.args[1]
        self.assertIn("제목 a", prompt)
        self.assertIn("설명 b", prompt)
        self.assertIn("교육", prompt)
        self.assertEqual(results[0].parent_ids, ["a", "b"])
        self.assertNotEqual(results[0].id, "a")
        self.assertEqual(generated.parent_ids, ["invented"])

    async def test_recombination_tracks_direct_parents_only(self):
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, return_value=[idea("model")]):
            results = await combine_ideas_service([idea("combined", ["a", "b"]), idea("c")])
        self.assertEqual(results[0].parent_ids, ["combined", "c"])

    async def test_multiple_results_have_unique_ids(self):
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, return_value=[idea("same"), idea("same")]):
            results = await combine_ideas_service([idea("a"), idea("b")])
        self.assertEqual(len({x.id for x in results}), 2)
        self.assertTrue(all(x.parent_ids == ["a", "b"] for x in results))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.payload = {"selected_ideas": [idea("a").model_dump(), idea("b").model_dump()]}

    def tearDown(self):
        self.client.close()

    def test_combination_response_preserves_parents(self):
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, return_value=[idea("model")]):
            response = self.client.post("/api/v1/combine", json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ideas"][0]["parent_ids"], ["a", "b"])

    def test_invalid_selections_do_not_call_ai(self):
        invalid = [
            {"selected_ideas": [{"title": "제목", "description": "설명"}, idea("b").model_dump()]},
            {"idea_ids": ["a", "b"]},
            {"selected_ideas": [idea("a").model_dump()]},
            {"selected_ideas": [idea("a").model_dump()] * 2},
            {"selected_ideas": [{"id": "a", "title": "제목"}, idea("b").model_dump()]},
            {"selected_ideas": [idea(" ").model_dump(), idea("b").model_dump()]},
            {**self.payload, "count": 6},
        ]
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock) as call:
            for payload in invalid:
                with self.subTest(payload=payload):
                    self.assertEqual(self.client.post("/api/v1/combine", json=payload).status_code, 422)
            call.assert_not_awaited()

    def test_registered_error_handlers_on_both_routes(self):
        errors = [(OllamaConnectionException(), 503, "OLLAMA_CONNECTION_ERROR"),
                  (AIResponseParseException("invalid JSON"), 502, "AI_PARSE_ERROR")]
        for path, payload in [("/api/v1/generate", {"keyword": "교육"}), ("/api/v1/combine", self.payload)]:
            for error, status, code in errors:
                with self.subTest(path=path, error=code):
                    with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock, side_effect=error):
                        response = self.client.post(path, json=payload)
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(response.json()["error_code"], code)
                    self.assertEqual(response.json()["status"], "error")


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, handler):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with patch("app.services.ai_service.OllamaClient", side_effect=partial(OllamaClient, http_client=client)):
                with patch("app.core.exceptions.asyncio.sleep", new_callable=AsyncMock):
                    return await _call_ollama("system", "prompt", "test")

    async def test_timeout_and_connection_failures_are_mapped(self):
        for exception in [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError]:
            async def handler(request):
                raise exception("failed", request=request)
            with self.subTest(exception=exception):
                with self.assertRaises(OllamaConnectionException) as caught:
                    await self.invoke(handler)
                self.assertIsInstance(caught.exception.__cause__, exception)

    async def test_http_status_error_is_mapped(self):
        with self.assertRaises(OllamaConnectionException):
            await self.invoke(lambda request: httpx.Response(503, json={"error": "unavailable"}))

    async def test_invalid_response_is_parse_error(self):
        for body in [[], {"response": None}, {"response": "not JSON"}]:
            with self.subTest(body=body):
                with self.assertRaises(AIResponseParseException):
                    await self.invoke(lambda request: httpx.Response(200, json=body))

    async def test_valid_ollama_response(self):
        body = {"response": json.dumps({"ideas": [{"title": "교육", "description": "설명"}]})}
        results = await self.invoke(lambda request: httpx.Response(200, json=body))
        self.assertEqual(results[0].title, "교육")


class CanvasTests(unittest.TestCase):
    def test_empty_board(self):
        self.assertEqual(ideas_to_canvas([]).elements, [])

    def test_nodes_edges_labels_and_bindings(self):
        canvas = ideas_to_canvas([idea("a"), idea("b"), idea("c", ["a", "b"])])
        data = canvas.model_dump(mode="json")
        nodes = [x for x in data["elements"] if x["type"] == "rectangle"]
        edges = [x for x in data["elements"] if x["type"] == "arrow"]
        self.assertEqual(len(nodes), 3)
        self.assertEqual(len(edges), 2)
        self.assertIn("설명 a", nodes[0]["label"]["text"])
        self.assertEqual(nodes[2]["customData"]["parent_ids"], ["a", "b"])
        self.assertEqual(edges[0]["start"]["id"], nodes[0]["id"])
        self.assertEqual(edges[0]["end"]["id"], nodes[2]["id"])
        self.assertEqual(data["format"], "excalidraw-skeleton")

    def test_child_before_parents_and_recombination_layout(self):
        canvas = ideas_to_canvas([idea("d", ["c", "a"]), idea("c", ["a", "b"]), idea("a"), idea("b")])
        nodes = {x.customData["id"]: x for x in canvas.elements if x.type == "rectangle"}
        self.assertGreater(nodes["d"].x, nodes["c"].x)
        self.assertGreater(nodes["c"].x, nodes["a"].x)

    def test_invalid_graphs_are_rejected(self):
        for items in [[idea("a"), idea("a")], [idea("a", ["missing"])],
                      [idea("a", ["a"])], [idea("a", ["b"]), idea("b", ["a"])],
                      [idea("a"), idea("b", ["a", "a"])]]:
            with self.subTest(items=items):
                with self.assertRaises(ValueError):
                    ideas_to_canvas(items)
