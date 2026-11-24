from fastapi import APIRouter

from app.api.v1.endpoints.combine import router as combine_router
from app.api.v1.endpoints.generate import router as generate_router
from app.api.v1.endpoints.board import router as board_router


router = APIRouter(prefix="/api/v1")
router.include_router(generate_router)
router.include_router(combine_router)
router.include_router(board_router)
