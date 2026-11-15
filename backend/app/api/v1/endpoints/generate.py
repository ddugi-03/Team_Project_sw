from fastapi import APIRouter, Request
from app.schemas.idea import IdeaGenerateRequest, IdeaResponse
from app.services.ai_service import generate_ideas_service

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=IdeaResponse)
async def generate(request: IdeaGenerateRequest, http_request: Request) -> IdeaResponse:
    """키워드와 카테고리를 받아 Ollama AI로 아이디어 생성"""
    # TODO(AI-2): creativity_level과 실제 OPTIMIZED_OPTIONS temperature 연계 여부 확인.
    ideas = await generate_ideas_service(
        topic=request.keyword,
        count=request.count,
        category=request.category or "일반"
    )
    # BE-A: FE는 조합 시 idea_ids만 보내므로 결과를 ID로 찾을 수 있게 보관.
    http_request.app.state.idea_registry.remember(ideas)
    return IdeaResponse(
        status="success",
        message="아이디어 생성 완료",
        ideas=ideas
    )
