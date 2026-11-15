"""Temporary per-process idea lookup for the frontend's ID-only combine request.

This intentionally avoids changing the frontend or the BE-B data schemas.
It is suitable for a single-process local demo, not persistent multi-worker storage.
"""

from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import Iterable

from app.schemas.idea import IdeaItem


class IdeaRegistry:
    """Remember recent generated ideas so /combine can resolve selected IDs."""

    def __init__(self, ttl_seconds: float = 3600, max_items: int = 1000) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_items = max_items
        self._items: OrderedDict[str, tuple[float, IdeaItem]] = OrderedDict()
        self._lock = Lock()

    def remember(self, ideas: Iterable[IdeaItem]) -> None:
        """Store generated or combined ideas, using their existing UUIDs."""
        now = monotonic()
        with self._lock:
            self._remove_expired(now)
            for idea in ideas:
                self._items[idea.id] = (now + self._ttl_seconds, idea.model_copy(deep=True))
                self._items.move_to_end(idea.id)
            while len(self._items) > self._max_items:
                self._items.popitem(last=False)

    def resolve(self, idea_ids: list[str]) -> list[dict[str, str]] | None:
        """Return prompt inputs in frontend selection order; None if any ID is missing."""
        with self._lock:
            self._remove_expired(monotonic())
            if any(idea_id not in self._items for idea_id in idea_ids):
                return None
            return [
                {
                    "id": idea_id,
                    "title": self._items[idea_id][1].title,
                    "description": self._items[idea_id][1].description,
                }
                for idea_id in idea_ids
            ]

    def _remove_expired(self, now: float) -> None:
        for idea_id in list(self._items):
            if self._items[idea_id][0] <= now:
                del self._items[idea_id]
