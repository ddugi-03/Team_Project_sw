import json
import re
from typing import Dict, Any, List
from pydantic import ValidationError
from app.schemas.idea import IdeaItem

class AIResponseParseException(Exception):
    """AI 응답 파싱 실패 시 발생하는 커스텀 예외"""
    pass

def parse_and_validate_ai_json(raw_response: str) -> List[IdeaItem]:
    """
    Ollama 텍스트 응답에서 JSON 구문을 추출하고 Pydantic 객체 리스트로 검증 및 변환
    """
    try:
        # 1. 정규식을 통해 JSON 배열/객체 형태 문자열만 추출
        json_match = re.search(r'\[.*\]|\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            raise AIResponseParseException("AI 응답에서 JSON 포맷을 찾을 수 없습니다.")
        
        json_str = json_match.group(0)
        parsed_data = json.loads(json_str)

        # 2. 단일 객체로 넘어올 경우 리스트 형태로 변환
        if isinstance(parsed_data, dict):
            if "ideas" in parsed_data:
                parsed_data = parsed_data["ideas"]
            else:
                parsed_data = [parsed_data]

        # 3. Pydantic 스키마 검증 및 IdeaItem 객체로 변환
        validated_ideas = []
        for item in parsed_data:
            validated_ideas.append(IdeaItem(**item))

        return validated_ideas

    except (json.JSONDecodeError, ValidationError) as e:
        raise AIResponseParseException(f"JSON 파싱 또는 스키마 검증 실패: {str(e)}")
