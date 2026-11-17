from fastapi import APIRouter

from app.schemas.idea import IdeaCombineRequest, IdeaResponse
from app.services.ai_service import combine_ideas_service

router = APIRouter(tags=["combine"])


@router.post("/combine", response_model=IdeaResponse)
async def combine(request: IdeaCombineRequest) -> IdeaResponse:
    """선택된 아이디어의 내용과 원본 ID를 보존하여 결합합니다."""
    ideas = await combine_ideas_service(
        selected_ideas=request.selected_ideas,
        direction=request.direction or "두 아이디어의 장점 결합",
        count=request.count,
    )
    return IdeaResponse(message="아이디어 조합 완료", ideas=ideas)
