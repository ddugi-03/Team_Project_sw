import json
import re
import asyncio
from typing import List, Callable, Awaitable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.schemas.idea import IdeaItem, ErrorResponse

# ==========================================
# 1. 커스텀 예외 클래스 정의
# ==========================================

class AIResponseParseException(Exception):
    """Ollama 응답에서 JSON 추출 또는 스키마 검증 실패 시 발생"""
    def __init__(self, message: str, raw_response: str = ""):
        self.message = message
        self.raw_response = raw_response
        super().__init__(self.message)

class OllamaConnectionException(Exception):
    """로컬 Ollama 서버 연결 실패 또는 타임아웃 시 발생"""
    def __init__(self, message: str = "AI 모델 서버와 통신할 수 없습니다."):
        self.message = message
        super().__init__(self.message)

# ==========================================
# 2. JSON 추출/검증 및 자동 재시도(Retry) 로직
# ==========================================

def parse_and_validate_ai_json(raw_response: str) -> List[IdeaItem]:
    """
    Ollama 텍스트 응답에서 마크다운 코드블록(```json) 등을 제거하고 
    순수 JSON만 추출하여 IdeaItem 리스트로 검증/변환
    """
    try:
        # 마크다운 코드 블록 제거 및 JSON 배열/객체 추출
        cleaned_text = re.sub(r'```(?:json)?|```', '', raw_response).strip()
        json_match = re.search(r'\[.*\]|\{.*\}', cleaned_text, re.DOTALL)
        
        if not json_match:
            raise AIResponseParseException("AI 응답에서 JSON 형식을 찾을 수 없습니다.", raw_response)
        
        parsed_data = json.loads(json_match.group(0))

        # 단일 객체 또는 {"ideas": [...]} 형태로 올 경우 리스트로 정규화
        if isinstance(parsed_data, dict):
            parsed_data = parsed_data.get("ideas", [parsed_data])

        if not isinstance(parsed_data, list) or len(parsed_data) == 0:
            raise AIResponseParseException("추출된 아이디어 데이터가 비어 있거나 리스트가 아닙니다.", raw_response)

        ideas = []
        for item in parsed_data:
            if not isinstance(item, dict):
                raise TypeError("아이디어는 JSON 객체여야 합니다.")
            # 모델은 내용만 제공합니다. ID와 계보는 서버가 관리합니다.
            ideas.append(IdeaItem.model_validate({
                key: item[key] for key in ("title", "description", "tags") if key in item
            }))
        return ideas

    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise AIResponseParseException(f"JSON 파싱 또는 스키마 검증 실패: {str(e)}", raw_response)

async def execute_with_retry(
    ai_call_func: Callable[[], Awaitable[str]], 
    max_retries: int = 3, 
    delay: float = 0.5,
    expected_count: int | None = None,
) -> List[IdeaItem]:
    """
    [백엔드 A 연동용 헬퍼 함수]
    Ollama 호출 함수를 받아 실행하고, 파싱 실패 시 최대 max_retries번 재요청을 수행함
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            raw_text = await ai_call_func()
            ideas = parse_and_validate_ai_json(raw_text)
            if expected_count is not None and len(ideas) != expected_count:
                raise AIResponseParseException(
                    f"아이디어 개수 불일치: 요청 {expected_count}개, 응답 {len(ideas)}개", raw_text
                )
            return ideas
        except AIResponseParseException as e:
            last_exception = e
            if attempt < max_retries:
                await asyncio.sleep(delay)
                continue
    raise last_exception

# ==========================================
# 3. FastAPI 전역 예외 핸들러 (main.py 등록용)
# ==========================================

async def ai_parse_exception_handler(request: Request, exc: AIResponseParseException):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=ErrorResponse(
            error_code="AI_PARSE_ERROR",
            message="AI가 올바른 형식의 아이디어를 생성하지 못했습니다. 다시 시도해 주세요.",
            detail=exc.message
        ).model_dump()
    )

async def ollama_conn_exception_handler(request: Request, exc: OllamaConnectionException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error_code="OLLAMA_CONNECTION_ERROR",
            message=exc.message
        ).model_dump()
    )