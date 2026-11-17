from fastapi import APIRouter

from app.schemas.idea import IdeaCombineRequest, IdeaResponse
from app.services.ai_service import combine_ideas_service

router = APIRouter(tags=["combine"])


@router.post("/combine", response_model=IdeaResponse)
async def combine(request: IdeaCombineRequest) -> IdeaResponse:
    """BE-B 공식 스키마로 검증한 아이디어를 조합해 반환한다."""
    ideas = await combine_ideas_service(
        selected_ideas=request.selected_ideas,
        direction=(
            request.direction
            if request.direction is not None
            else IdeaCombineRequest.model_fields["direction"].default
        ),
        count=request.count,
    )

    return IdeaResponse(
        status="success",
        message="아이디어 조합 완료",
        ideas=ideas,
    )