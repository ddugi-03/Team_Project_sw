from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.idea import IdeaCombineRequest, IdeaResponse
from app.services.ai_service import combine_ideas_service

router = APIRouter(tags=["combine"])

# BE-A: FE의 {"idea_ids": [...]} 지원. 기존 Swagger/BE 요청 {"selected_ideas": [...]}도 유지.
class IdeaIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idea_ids: list[str] = Field(min_length=2)
    direction: str | None = None
    count: int = Field(default=2, ge=1, le=5)

    @field_validator("idea_ids")
    @classmethod
    def validate_ids(cls, ids: list[str]) -> list[str]:
        if any(not idea_id.strip() for idea_id in ids):
            raise ValueError("빈 아이디어 ID는 허용되지 않습니다.")

        if len(ids) != len(set(ids)):
            raise ValueError("중복된 아이디어를 선택할 수 없습니다.")

        return ids


@router.post("/combine", response_model=IdeaResponse)
async def combine(request: IdeaCombineRequest | IdeaIdsRequest, http_request: Request) -> IdeaResponse:
    """선택된 아이디어를 결합해 새로운 아이디어 생성"""

    # 두 요청 형식의 혼합 사용 방지
    raw_body = await http_request.json()
    if "idea_ids" in raw_body and "selected_ideas" in raw_body:
        raise HTTPException(
            status_code=422,
            detail="idea_ids와 selected_ideas를 동시에 전달할 수 없습니다."
        )

    if isinstance(request, IdeaIdsRequest):
        # FE: idea_ids -> 원본 아이디어 조회
        selected_ideas = http_request.app.state.idea_registry.resolve(
            request.idea_ids
        )

        if selected_ideas is None:
            raise HTTPException(
                status_code=404,
                detail="선택한 아이디어를 찾을 수 없습니다. 다시 생성해 주세요."
            )

        # BE-B 공식 스키마로 변환 및 검증
        payload = {
            "selected_ideas": selected_ideas,
            "count": request.count
        }

        if request.direction is not None:
            payload["direction"] = request.direction

        combine_request = IdeaCombineRequest.model_validate(payload)

    else:
        # BE-B 공식 스키마 요청은 그대로 사용
        combine_request = request

    # 검증 완료된 데이터만 AI 서비스로 전달
    ideas = await combine_ideas_service(
        selected_ideas=combine_request.selected_ideas,
        direction=combine_request.direction or "두 아이디어의 장점 결합",
        count=combine_request.count
    )

    # 생성된 아이디어를 재조합할 수 있도록 저장
    http_request.app.state.idea_registry.remember(ideas)

    return IdeaResponse(
        status="success",
        message="아이디어 조합 완료",
        ideas=ideas
    )