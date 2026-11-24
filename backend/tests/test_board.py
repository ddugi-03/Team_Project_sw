"""Board contract and save -> restore -> recombine integration (no real AI calls)."""

import copy
import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.board import BoardDocument
from app.schemas.idea import IdeaItem
from main import create_app


def card(key, parents=None):
    return {"id": key, "title": f"아이디어 {key}", "description": "기능을 연결해 사용자의 문제를 해결합니다.",
            "tags": ["협업"], "parent_ids": parents or []}


def board():
    return {"format": "idea-note-board", "schema_version": 1, "topic": "팀 일정",
            "ideas": [card("a"), card("b"), card("c", ["a", "b"]), card("d", ["a", "c"])],
            "positions": {"topic": {"x": 24, "y": 30}, "a": {"x": 200.5, "y": 400}}}


class BoardContractTests(unittest.TestCase):
    def test_round_trip_preserves_content_order_ids_positions_and_direct_parents(self):
        original = board()
        restored = BoardDocument.model_validate_json(
            BoardDocument.model_validate(original).model_dump_json(exclude_none=True),
        ).model_dump(exclude_none=True)
        self.assertEqual(original, restored)
        self.assertEqual(restored["ideas"][-1]["parent_ids"], ["a", "c"])

    def test_empty_board_and_missing_positions_are_valid(self):
        value = board()
        value.update(topic="", ideas=[], positions={})
        self.assertEqual(BoardDocument.model_validate(value).ideas, [])
        value = board()
        del value["positions"]
        self.assertEqual(BoardDocument.model_validate(value).positions, {})

    def test_file_order_is_not_topological(self):
        value = board()
        value["ideas"].reverse()
        self.assertEqual(BoardDocument.model_validate(value).ideas[0].id, "d")

    def test_invalid_documents(self):
        cases = {}
        def invalid(name, mutate):
            value = board()
            mutate(value)
            cases[name] = value
        invalid("duplicate id", lambda b: b["ideas"].append(card("a")))
        invalid("missing id", lambda b: b["ideas"][0].pop("id"))
        invalid("reserved topic id", lambda b: b["ideas"].append(card("topic")))
        invalid("whitespace id", lambda b: b["ideas"][0].update(id=" a"))
        invalid("missing parent", lambda b: b["ideas"][-1].update(parent_ids=["a", "missing"]))
        invalid("self parent", lambda b: b["ideas"][-1].update(parent_ids=["a", "d"]))
        invalid("duplicate parent", lambda b: b["ideas"][-1].update(parent_ids=["a", "a"]))
        invalid("one parent", lambda b: b["ideas"][-1].update(parent_ids=["a"]))
        invalid("cycle", lambda b: b["ideas"][0].update(parent_ids=["b", "d"]))
        invalid("unknown position", lambda b: b["positions"].update(unknown={"x": 1, "y": 2}))
        invalid("missing position coordinate", lambda b: b["positions"]["a"].pop("y"))
        invalid("negative position", lambda b: b["positions"]["a"].update(x=-1))
        invalid("infinite position", lambda b: b["positions"]["a"].update(x=float("inf")))
        invalid("nan position", lambda b: b["positions"]["a"].update(x=float("nan")))
        invalid("boolean position", lambda b: b["positions"]["a"].update(x=True))
        invalid("string position", lambda b: b["positions"]["a"].update(x="123"))
        invalid("very large position", lambda b: b["positions"]["a"].update(x=1_000_001))
        invalid("unsupported version", lambda b: b.update(schema_version=2))
        invalid("boolean version", lambda b: b.update(schema_version=True))
        invalid("float version", lambda b: b.update(schema_version=1.0))
        invalid("wrong format", lambda b: b.update(format="excalidraw"))
        invalid("blank description", lambda b: b["ideas"][0].update(description="  "))
        invalid("long title", lambda b: b["ideas"][0].update(title="가" * 501))
        invalid("long topic", lambda b: b.update(topic="가" * 4001))
        invalid("blank tag", lambda b: b["ideas"][0].update(tags=[" "]))
        invalid("excessive tags", lambda b: b["ideas"][0].update(tags=["a"] * 51))
        invalid("unknown root field", lambda b: b.update(server_path="/tmp/board"))
        invalid("unknown card field", lambda b: b["ideas"][0].update(parentIds=[]))
        invalid("too many ideas", lambda b: b.update(ideas=[card(str(i)) for i in range(501)]))
        for name, value in cases.items():
            with self.subTest(name=name), self.assertRaises(ValidationError):
                BoardDocument.model_validate(value)

    def test_deep_graph_does_not_depend_on_python_recursion_limit(self):
        value = board()
        value["ideas"] = [card("0"), card("1")]
        value["ideas"] += [card(str(i), ["0", str(i - 1)]) for i in range(2, 500)]
        value["positions"] = {}
        self.assertEqual(len(BoardDocument.model_validate(value).ideas), 500)

    def test_review_contract_preserves_evidence_and_requires_exact_parent_coverage(self):
        value = board()
        review = {"evaluated_by": "human", "source_usage": [
            {"source_id": "a", "used_element": "빈 시간 탐색", "evidence": "시간표의 빈 시간을 찾음"},
            {"source_id": "b", "used_element": "일정 취합", "evidence": "팀원의 가능 시간을 비교함"},
        ], "note": "내용의 정확성은 사람이 확인한 기록"}
        value["ideas"][2]["combination_review"] = review
        self.assertEqual(BoardDocument.model_validate(value).ideas[2].combination_review.note, review["note"])
        for sources in [["a", "a"], ["a", "c"], ["a", "b", "d"]]:
            invalid = copy.deepcopy(value)
            invalid["ideas"][2]["combination_review"]["source_usage"] = [
                {"source_id": key, "used_element": "요소", "evidence": "근거"} for key in sources
            ]
            with self.subTest(sources=sources), self.assertRaises(ValidationError):
                BoardDocument.model_validate(invalid)


class BoardAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_validate_and_export_do_not_invoke_ai_or_mutate_document(self):
        original = board()
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock) as ai:
            for route in ("validate", "export"):
                response = self.client.post(f"/api/v1/board/{route}", json=original)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), original)
            ai.assert_not_awaited()

    def test_rejected_import_does_not_affect_valid_board(self):
        original = board()
        invalid = copy.deepcopy(original)
        invalid["ideas"][0]["id"] = "b"
        for route in ("validate", "export"):
            response = self.client.post(f"/api/v1/board/{route}", json=invalid)
            self.assertEqual(response.status_code, 422)
            self.assertIn("detail", response.json())
        self.assertEqual(self.client.post("/api/v1/board/validate", json=original).json(), original)

    def test_malformed_json_is_rejected(self):
        response = self.client.post("/api/v1/board/validate", content='{"ideas":',
                                    headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)

    def test_import_after_process_restart_then_recombine_uses_preserved_ids(self):
        exported = self.client.post("/api/v1/board/export", json=board()).json()
        with TestClient(create_app()) as restarted:
            restored = restarted.post("/api/v1/board/validate", json=exported).json()
            selected = [restored["ideas"][0], restored["ideas"][-1]]
            with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock,
                       return_value=[IdeaItem(**card("model-id", ["fake", "parent"]))]):
                response = restarted.post("/api/v1/combine", json={"selected_ideas": selected, "count": 1})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()["ideas"][0]
            self.assertEqual(result["parent_ids"], ["a", "d"])
            self.assertNotIn(result["id"], [item["id"] for item in restored["ideas"]] + ["model-id"])
            restored["ideas"].append(result)
            self.assertEqual(restarted.post("/api/v1/board/export", json=restored).status_code, 200)

    def test_review_metadata_is_optional_and_does_not_change_combine_contract(self):
        value = board()
        value["ideas"][2]["combination_review"] = {
            "evaluated_by": "ai", "source_usage": [
                {"source_id": key, "used_element": "요소", "evidence": "설명 속 근거"} for key in ["a", "b"]
            ],
        }
        restored = self.client.post("/api/v1/board/validate", json=value)
        self.assertEqual(restored.status_code, 200, restored.text)
        with patch("app.services.ai_service._call_ollama", new_callable=AsyncMock,
                   return_value=[IdeaItem(**card("new"))]):
            result = self.client.post("/api/v1/combine", json={
                "selected_ideas": [restored.json()["ideas"][0], restored.json()["ideas"][2]], "count": 1,
            })
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["ideas"][0]["parent_ids"], ["a", "c"])

    def test_new_routes_are_in_openapi_and_allow_existing_frontend_origin(self):
        spec = self.client.get("/openapi.json").json()
        self.assertIn("/api/v1/board/validate", spec["paths"])
        self.assertIn("/api/v1/board/export", spec["paths"])
        response = self.client.options("/api/v1/board/validate", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


if __name__ == "__main__":
    unittest.main()
