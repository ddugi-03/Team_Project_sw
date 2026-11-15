from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import uuid

# ==========================================
# 1. 요청 스키마 (Request)
# ==========================================

class IdeaGenerateRequest(BaseModel):
    keyword: str = Field(..., min_length=1, description="브레인스토밍 주제 또는 핵심 키워드", example="AI 기반 브레인스토밍")
    category: Optional[str] = Field(default="일반", description="아이디어 분야", example="IT/소프트웨어")
    count: int = Field(default=3, ge=1, le=10, description="생성할 아이디어 개수", example=3)
    creativity_level: float = Field(default=0.7, ge=0.0, le=1.0, description="창의성 수치 (Temperature)")

class IdeaCombineRequest(BaseModel):
    selected_ideas: List["IdeaItem"] = Field(
        ..., 
        min_length=2, 
        description="조합할 기존 아이디어 객체 리스트 (최소 2개 이상 - ID뿐만 아니라 제목/설명을 AI에 넘기기 위함)"
    )
    direction: Optional[str] = Field(
        default="두 아이디어의 장점을 결합하여 새로운 서비스 구상", 
        description="조합 방향성 및 추가 요구조건"
    )

# ==========================================
# 2. 핵심 엔티티 스키마 (Core Entity)
# ==========================================

class IdeaItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="아이디어 고유 식별자")
    title: str = Field(..., description="아이디어 제목")
    description: str = Field(..., description="아이디어 상세 설명")
    tags: List[str] = Field(default_factory=list, description="관련 태그")
    parent_ids: List[str] = Field(default_factory=list, description="조합 원본 ID 리스트 (Excalidraw 엣지 연결용)")

# ==========================================
# 3. 응답 및 공통 에러 스키마 (Response)
# ==========================================

class IdeaResponse(BaseModel):
    status: Literal["success"] = "success"
    message: Optional[str] = Field(default=None, description="안내 메시지")
    ideas: List[IdeaItem] = Field(default_factory=list, description="아이디어 목록")

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str = Field(..., description="에러 식별 코드 (예: AI_PARSE_ERROR, OLLAMA_TIMEOUT)")
    message: str = Field(..., description="사용자에게 보여줄 에러 메시지")
    detail: Optional[str] = Field(default=None, description="디버깅용 상세 에러 내역")