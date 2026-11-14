from typing import Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter
from app.schemas.idea import IdeaResponse
from app.services.ai_service import combine_ideas_service

router = APIRouter(tags=["combine"])


class CombineTestRequest(BaseModel):
    selected_ideas: List[dict[str, Any]] = Field(
        ...,
        min_length=2,
        example=[
            {"title": "AI 스터디 플래너", "description": "시험 범위와 남은 일수를 분석해 매일 공부할 분량을 자동 배분해주는 앱"},
            {"title": "집중력 측정 타이머", "description": "웹캠으로 졸음이나 스마트폰 사용을 감지해 알림을 주는 뽀모도로 타이머"}
        ]
    )
    direction: Optional[str] = Field(default="두 아이디어의 핵심 장점을 결합한 시너지 서비스")
    count: int = Field(default=2, ge=1, le=5)


@router.post("/combine", response_model=IdeaResponse)
async def combine(request: CombineTestRequest) -> IdeaResponse:
    """선택된 2개 이상의 아이디어를 결합해 시너지 아이디어 생성"""
    ideas = await combine_ideas_service(
        selected_ideas=request.selected_ideas,
        direction=request.direction or "두 아이디어의 장점 결합",
        count=request.count
    )
    return IdeaResponse(
        status="success",
        message="아이디어 조합 완료",
        ideas=ideas
    )