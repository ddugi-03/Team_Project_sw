import httpx
from typing import List
from app.schemas.idea import IdeaItem
from app.core.exceptions import parse_and_validate_ai_json, AIResponseParseException

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

async def generate_ideas_service(topic: str, count: int = 3) -> List[IdeaItem]:
    """
    주제를 받아 Ollama AI를 통해 아이디어를 생성하고 Pydantic 객체 리스트로 반환
    """
    system_prompt = (
        "너는 창의적인 브레인스토밍 전문가야. 모든 답변은 오직 한국어로만 작성해야 하며, "
        "절대 중국어나 다른 외국어를 혼용해서는 안 돼. 오직 규격화된 JSON 형식으로만 답해."
    )
    
    user_prompt = f"""주제: {topic}
개수: {count}개

조건:
1. 제목(title)은 신선하고 독창적이어야 함.
2. 설명(description)은 서비스의 특징과 이점을 2~3문장으로 상세히 작성할 것.
3. 태그(tags)는 한글 키워드 3개의 배열 형태로 작성할 것.

출력 예시:
{{
  "ideas": [
    {{
      "title": "예시 제목",
      "description": "예시 설명입니다. 2문장 이상 작성합니다.",
      "tags": ["태그1", "태그2", "태그3"]
    }}
  ]
}}"""

    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": user_prompt,
        "format": "json",
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            raw_response = data.get("response", "")

        return parse_and_validate_ai_json(raw_response)

    except httpx.HTTPError as e:
        raise AIResponseParseException(f"Ollama API 통신 실패: {str(e)}")
