"""Local-demo idea registry tests, without any real AI server."""

import unittest
from unittest.mock import patch

from app.schemas.idea import IdeaItem
from app.services.idea_registry import IdeaRegistry


class IdeaRegistryTests(unittest.TestCase):
    def test_remember_and_resolve_ideas_in_requested_order(self) -> None:
        registry = IdeaRegistry()
        first = IdeaItem(id="first", title="A", description="A description")
        second = IdeaItem(id="second", title="B", description="B description")
        registry.remember([first, second])
        self.assertEqual(registry.resolve(["second", "first"]), [
            {"id": "second", "title": "B", "description": "B description"},
            {"id": "first", "title": "A", "description": "A description"},
        ])

    def test_expired_ideas_are_not_resolved(self) -> None:
        registry = IdeaRegistry(ttl_seconds=10)
        item = IdeaItem(id="a", title="A", description="A description")
        with patch("app.services.idea_registry.monotonic", return_value=100):
            registry.remember([item])
        with patch("app.services.idea_registry.monotonic", return_value=111):
            self.assertIsNone(registry.resolve(["a"]))

    def test_oldest_ideas_are_evicted_when_capacity_is_reached(self) -> None:
        registry = IdeaRegistry(max_items=2)
        registry.remember([
            IdeaItem(id="a", title="A", description="A description"),
            IdeaItem(id="b", title="B", description="B description"),
            IdeaItem(id="c", title="C", description="C description"),
        ])
        self.assertIsNone(registry.resolve(["a"]))
        self.assertIsNotNone(registry.resolve(["b", "c"]))


if __name__ == "__main__":
    unittest.main()
