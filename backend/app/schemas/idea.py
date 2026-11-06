from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

# 프론트엔드 -> 백엔드 요청 스키마
class IdeaGenerateRequest(BaseModel):
    keyword: str = Field(..., description="브레인스토밍 주제 또는 핵심 키워드", example="AI 기반 웹 서비스")
    category: Optional[str] = Field(default="일반", description="아이디어 분야", example="IT/소프트웨어")
    count: int = Field(default=3, ge=1, le=10, description="생성할 아이디어 개수", example=3)

class IdeaCombineRequest(BaseModel):
    selected_idea_ids: List[str] = Field(..., min_length=2, description="조합할 아이디어 ID 리스트", example=["id-1", "id-2"])
    direction: Optional[str] = Field(default="두 아이디어의 장점 결합", description="조합 방향성")

# 핵심 엔티티 스키마
class IdeaItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="아이디어 고유 식별자")
    title: str = Field(..., description="아이디어 제목")
    description: str = Field(..., description="아이디어 상세 설명")
    tags: List[str] = Field(default_factory=list, description="관련 태그")
    parent_ids: List[str] = Field(default_factory=list, description="조합 원본 ID 리스트 (Excalidraw 관계도용)")

# 백엔드 -> 프론트엔드 응답 스키마
class IdeaResponse(BaseModel):
    status: str = Field(default="success", description="응답 상태")
    message: Optional[str] = Field(default=None, description="안내 메시지")
    ideas: List[IdeaItem] = Field(default_factory=list, description="아이디어 목록")
