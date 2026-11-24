"""Stateless board import/export validation, independent of AI model availability."""

from fastapi import APIRouter

from app.schemas.board import BoardDocument

router = APIRouter(prefix="/board", tags=["board"])


@router.post("/validate", response_model=BoardDocument, response_model_exclude_none=True)
async def validate_board(document: BoardDocument) -> BoardDocument:
    """불러오기 전 전체 문서를 검증합니다. 실패 시 422이며 어떤 상태도 변경하지 않습니다."""
    return document


@router.post("/export", response_model=BoardDocument, response_model_exclude_none=True)
async def export_board(document: BoardDocument) -> BoardDocument:
    """현재 보드의 저장 형식을 검증해 반환합니다. 파일 다운로드는 프론트에서 처리합니다."""
    return document
