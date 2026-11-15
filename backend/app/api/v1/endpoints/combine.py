from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from app.schemas.idea import IdeaResponse
from app.services.ai_service import combine_ideas_service

router = APIRouter(tags=["combine"])


# BE-A: FE의 {"idea_ids": [...]} 지원. 기존 Swagger/BE 요청 {"selected_ideas": [...]}도 유지.
# TODO(BE-B): 최종 IdeaCombineRequest와 두 요청 형식의 통일 여부 협의.
class CombineTestRequest(BaseModel):
    selected_ideas: Optional[List[dict[str, Any]]] = Field(
        default=None,
        min_length=2,
        example=[
            {"title": "AI 스터디 플래너", "description": "시험 범위와 남은 일수를 분석해 매일 공부할 분량을 자동 배분해주는 앱"},
            {"title": "집중력 측정 타이머", "description": "웹캠으로 졸음이나 스마트폰 사용을 감지해 알림을 주는 뽀모도로 타이머"}
        ]
    )
    idea_ids: Optional[List[str]] = Field(
        default=None, min_length=2,
        description="프론트엔드가 선택한 아이디어 ID 목록 (2개 이상)",
    )
    direction: Optional[str] = Field(default="두 아이디어의 핵심 장점을 결합한 시너지 서비스")
    count: int = Field(default=2, ge=1, le=5)

    @model_validator(mode="after")
    def validate_source(self) -> "CombineTestRequest":
        if (self.idea_ids is None) == (self.selected_ideas is None):
            raise ValueError("idea_ids 또는 selected_ideas 중 하나만 전달해야 합니다.")
        if self.idea_ids is not None:
            if any(not idea_id.strip() for idea_id in self.idea_ids):
                raise ValueError("idea_ids에 빈 ID를 전달할 수 없습니다.")
            if len(set(self.idea_ids)) != len(self.idea_ids):
                raise ValueError("서로 다른 아이디어를 2개 이상 선택해야 합니다.")
        return self


@router.post("/combine", response_model=IdeaResponse)
async def combine(request: CombineTestRequest, http_request: Request) -> IdeaResponse:
    """선택된 아이디어를 결합해 시너지 아이디어 생성"""
    if request.idea_ids is not None:
        # BE-A: 프론트엔드가 ID만 전달하므로 이번 서버에서 생성한 원본을 조회.
        selected_ideas = http_request.app.state.idea_registry.resolve(request.idea_ids)
        if selected_ideas is None:
            raise HTTPException(
                status_code=404,
                detail="선택한 아이디어를 찾을 수 없습니다. 서버 재시작 후에는 아이디어를 다시 생성해 주세요.",
            )
    else:
        selected_ideas = request.selected_ideas

    ideas = await combine_ideas_service(
        selected_ideas=selected_ideas,
        direction=request.direction or "두 아이디어의 장점 결합",
        count=request.count
    )
    # BE-A: 결합된 아이디어도 다시 선택·조합할 수 있어야 하므로 보관.
    http_request.app.state.idea_registry.remember(ideas)
    return IdeaResponse(
        status="success",
        message="아이디어 조합 완료",
        ideas=ideas
    )
