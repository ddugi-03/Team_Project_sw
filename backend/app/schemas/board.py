"""Versioned portable board contract; validation never changes server state."""

from collections import deque
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_IDEAS = 500
Identifier = Annotated[str, Field(min_length=1, max_length=128)]
Text = Annotated[str, Field(min_length=1, max_length=4000)]
Coordinate = Annotated[float, Field(ge=0, le=1_000_000, allow_inf_nan=False)]


class BoardModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def check_identifier(value: str) -> str:
    if value != value.strip() or not value or any(ord(c) < 32 for c in value):
        raise ValueError("ID는 비어 있거나 앞뒤 공백·제어 문자를 포함할 수 없습니다.")
    return value


class BoardPosition(BoardModel):
    x: Coordinate
    y: Coordinate


class SourceUsage(BoardModel):
    source_id: Identifier
    used_element: Text
    evidence: Text = Field(description="결과 설명에서 실제 반영된 부분. 내용의 진위는 별도 평가합니다.")

    _source_id = field_validator("source_id")(check_identifier)

    @field_validator("used_element", "evidence")
    @classmethod
    def require_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("평가 내용은 비어 있을 수 없습니다.")
        return value


class CombinationReview(BoardModel):
    """Optional interchange contract, not an implemented AI quality evaluator."""

    evaluated_by: Literal["ai", "human"]
    source_usage: list[SourceUsage] = Field(min_length=2, max_length=MAX_IDEAS)
    note: str = Field(default="", max_length=4000)


class BoardIdea(BoardModel):
    # Unlike generation, importing must never invent missing IDs or relationships.
    id: Identifier
    title: Annotated[str, Field(min_length=1, max_length=500)]
    description: Text
    tags: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=50,
    )
    parent_ids: list[Identifier] = Field(default_factory=list, max_length=MAX_IDEAS)
    combination_review: CombinationReview | None = None

    _id = field_validator("id")(check_identifier)

    @field_validator("title", "description")
    @classmethod
    def require_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("제목과 설명은 비어 있을 수 없습니다.")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("빈 태그는 허용하지 않습니다.")
        return values

    @field_validator("parent_ids")
    @classmethod
    def validate_parents(cls, values: list[str]) -> list[str]:
        for value in values:
            check_identifier(value)
        if len(values) != len(set(values)):
            raise ValueError("부모 ID는 중복될 수 없습니다.")
        return values

    @model_validator(mode="after")
    def validate_review(self) -> "BoardIdea":
        if len(self.parent_ids) == 1:
            raise ValueError("조합 카드는 서로 다른 원본을 두 개 이상 가져야 합니다.")
        if self.combination_review is not None:
            sources = [item.source_id for item in self.combination_review.source_usage]
            if len(sources) != len(set(sources)) or set(sources) != set(self.parent_ids):
                raise ValueError("평가의 source_id는 카드의 직접 부모 전체와 정확히 일치해야 합니다.")
        return self


class BoardDocument(BoardModel):
    format: Literal["idea-note-board"]
    schema_version: Literal[1]
    topic: str = Field(max_length=4000)
    ideas: list[BoardIdea] = Field(max_length=MAX_IDEAS)
    positions: dict[Identifier, BoardPosition] = Field(default_factory=dict, max_length=MAX_IDEAS + 1)

    @field_validator("schema_version", mode="before")
    @classmethod
    def version_is_integer(cls, value):
        if type(value) is not int:
            raise ValueError("schema_version은 정수여야 합니다.")
        return value

    @model_validator(mode="after")
    def validate_graph(self) -> "BoardDocument":
        ids = [idea.id for idea in self.ideas]
        if len(ids) != len(set(ids)):
            raise ValueError("중복된 카드 ID가 있습니다.")
        if "topic" in ids:
            raise ValueError("topic은 주제 카드에 예약된 ID입니다.")
        id_set = set(ids)
        for key in self.positions:
            check_identifier(key)
        if set(self.positions) - id_set - {"topic"}:
            raise ValueError("위치 데이터가 존재하지 않는 카드를 참조합니다.")
        # Kahn's algorithm avoids recursion limits and accepts arbitrary file order.
        children = {key: [] for key in ids}
        degrees = {idea.id: len(idea.parent_ids) for idea in self.ideas}
        for idea in self.ideas:
            for parent in idea.parent_ids:
                if parent not in id_set:
                    raise ValueError("존재하지 않는 부모 카드를 참조합니다.")
                if parent == idea.id:
                    raise ValueError("자기 자신을 부모로 지정할 수 없습니다.")
                children[parent].append(idea.id)
        pending = deque(key for key in ids if degrees[key] == 0)
        visited = 0
        while pending:
            key = pending.popleft()
            visited += 1
            for child in children[key]:
                degrees[child] -= 1
                if degrees[child] == 0:
                    pending.append(child)
        if visited != len(ids):
            raise ValueError("부모 관계에 순환이 있습니다.")
        return self
