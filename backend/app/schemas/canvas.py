"""Excalidraw Skeleton 계약. 프론트에서 convertToExcalidrawElements로 완성합니다."""
from typing import Literal

from pydantic import BaseModel, Field


class CanvasLabel(BaseModel):
    text: str
    fontSize: int = 16


class CanvasBinding(BaseModel):
    id: str


class CanvasNode(BaseModel):
    id: str
    type: Literal["rectangle"] = "rectangle"
    x: float
    y: float
    width: float = 280
    height: float = 180
    label: CanvasLabel
    customData: dict = Field(default_factory=dict)


class CanvasEdge(BaseModel):
    id: str
    type: Literal["arrow"] = "arrow"
    x: float
    y: float
    width: float
    height: float
    points: list[tuple[float, float]]
    start: CanvasBinding
    end: CanvasBinding
    endArrowhead: Literal["arrow"] = "arrow"


class CanvasData(BaseModel):
    format: Literal["excalidraw-skeleton"] = "excalidraw-skeleton"
    schema_version: Literal[1] = 1
    elements: list[CanvasNode | CanvasEdge] = Field(default_factory=list)
