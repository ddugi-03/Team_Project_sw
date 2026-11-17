"""IdeaItem DAG를 순서와 무관하게 배치하는 순수 변환 어댑터."""
import json

from app.schemas.canvas import CanvasBinding, CanvasData, CanvasEdge, CanvasLabel, CanvasNode
from app.schemas.idea import IdeaItem


def ideas_to_canvas(ideas: list[IdeaItem]) -> CanvasData:
    """모든 원본을 포함한 보드를 받습니다. 중복·누락·순환 관계는 거부합니다."""
    by_id = {idea.id: idea for idea in ideas}
    if len(by_id) != len(ideas) or any(not idea.id.strip() for idea in ideas):
        raise ValueError("아이디어 ID는 비어 있지 않고 고유해야 합니다.")
    levels: dict[str, int] = {}
    remaining = dict(by_id)
    for idea in ideas:
        if len(idea.parent_ids) != len(set(idea.parent_ids)):
            raise ValueError("중복된 부모 ID가 있습니다.")
        if any(parent not in by_id for parent in idea.parent_ids):
            raise ValueError("보드에 없는 부모 ID가 있습니다.")
    while remaining:
        ready = [idea for idea in remaining.values() if all(p in levels for p in idea.parent_ids)]
        if not ready:
            raise ValueError("아이디어 관계에 순환 또는 자기 참조가 있습니다.")
        for idea in ready:
            levels[idea.id] = max((levels[p] + 1 for p in idea.parent_ids), default=0)
            del remaining[idea.id]

    rows: dict[int, int] = {}
    nodes: dict[str, CanvasNode] = {}
    for idea in ideas:
        level = levels[idea.id]
        row = rows.get(level, 0)
        rows[level] = row + 1
        nodes[idea.id] = CanvasNode(
            id="idea:" + idea.id, x=level * 440, y=row * 260,
            label=CanvasLabel(text=idea.title + "\n\n" + idea.description),
            customData=idea.model_dump(),
        )
    edges = []
    for idea in ideas:
        target = nodes[idea.id]
        for parent_id in idea.parent_ids:
            source = nodes[parent_id]
            x, y = source.x + source.width, source.y + source.height / 2
            dx, dy = target.x - x, target.y + target.height / 2 - y
            edges.append(CanvasEdge(
                id="edge:" + json.dumps([parent_id, idea.id], ensure_ascii=False),
                x=x, y=y, width=abs(dx), height=abs(dy), points=[(0, 0), (dx, dy)],
                start=CanvasBinding(id=source.id), end=CanvasBinding(id=target.id),
            ))
    return CanvasData(elements=[*nodes.values(), *edges])
