from fastapi import APIRouter
from app.schemas.idea import IdeaGenerateRequest, IdeaResponse
from app.services.ai_service import generate_ideas_service

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=IdeaResponse)
async def generate(request: IdeaGenerateRequest) -> IdeaResponse:
    """키워드와 카테고리를 받아 Ollama AI로 아이디어 생성"""
    # TODO(AI-2): creativity_level과 실제 OPTIMIZED_OPTIONS temperature 연계 여부 확인.
    ideas = await generate_ideas_service(
        topic=request.keyword,
        count=request.count,
        category=request.category or "일반"
    )
    return IdeaResponse(
        status="success",
        message="아이디어 생성 완료",
        ideas=ideas
    )
