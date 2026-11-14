import time
import logging
import httpx
from typing import List, Dict, Any
from app.schemas.idea import IdeaItem
from app.core.exceptions import parse_and_validate_ai_json, AIResponseParseException

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

# [AI 1] 공통 System Prompt: JSON 규격 강제 및 중국어/영어 혼용 방지
COMMON_SYSTEM_PROMPT = """당신은 창의적이고 실용적인 아이디어를 도출하는 브레인스토밍 전문가입니다.
반드시 아래 규칙을 엄격히 준수하여 순수 JSON 형식으로만 응답하세요.

[필수 규칙]
1. 모든 텍스트는 오직 자연스러운 순수 한국어로만 작성하세요. 한자, 중국어, 불필요한 영어 단어를 절대 섞지 마세요.
2. 인사말, 마크다운 기호(```json 등), 부연 설명 없이 오직 유효한 JSON 객체만 출력하세요.
3. 최상위 키는 반드시 "ideas"여야 하며, 각 요소는 "title", "description", "tags" 키만 가집니다.
4. "tags"는 '#' 기호 없는 핵심 한국어 키워드 3개의 문자열 리스트로 작성하세요."""

# [AI 2] Qwen2.5 최적화 파라미터 (창의성·정형성 균형 및 응답 속도 개선)
OPTIMIZED_OPTIONS = {
    "temperature": 0.7,      # 창의성과 JSON 규격 안정성의 균형점 (0.6~0.8 권장)
    "top_p": 0.9,            # 지나치게 엉뚱한 토큰 생성 억제
    "repeat_penalty": 1.1,   # 동일 단어/문장 반복 방지
    "num_ctx": 2048,         # 불필요한 컨텍스트 메모리 점유 축소로 속도 향상
    "num_predict": 1024      # 과도한 길이 생성 방지 (Latency 단축)
}


async def _call_ollama(system_prompt: str, user_prompt: str, task_name: str) -> List[IdeaItem]:
    """
    Ollama API 공통 호출, 응답 속도(Latency) 측정 및 JSON 파싱 검증 헬퍼 함수
    """
    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": user_prompt,
        "format": "json",
        "stream": False,
        "options": OPTIMIZED_OPTIONS
    }

    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()

            data = response.json()
            raw_response = data.get("response", "")

        elapsed = time.perf_counter() - start_time
        logger.info(f"[AI Latency] {task_name} 완료: {elapsed:.2f}초 소요")
        print(f"[AI Latency] {task_name} 완료: {elapsed:.2f}초 소요")

        return parse_and_validate_ai_json(raw_response)

    except httpx.HTTPError as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"[AI Error] {task_name} 실패 ({elapsed:.2f}초): {str(e)}")
        raise AIResponseParseException(f"Ollama API 통신 실패: {str(e)}")


async def generate_ideas_service(
    topic: str,
    count: int = 3,
    category: str = "일반"
) -> List[IdeaItem]:
    """
    [AI 1] 주제를 받아 Ollama AI를 통해 아이디어를 생성하고 Pydantic 객체 리스트로 반환
    """
    user_prompt = f"""다음 조건에 맞춰 서로 다른 독창적인 아이디어 {count}개를 생성하세요.

- 주제 키워드: {topic}
- 분야(카테고리): {category}
- 생성 개수: 정확히 {count}개

[작성 가이드]
1. title: 호기심을 끄는 구체적이고 명확한 서비스/아이디어 제목
2. description: 핵심 기능, 주요 타겟, 기대 효과를 포함한 2~3문장의 구체적인 설명
3. tags: 핵심 한국어 키워드 3개 (예: ["인공지능", "일정관리", "생산성"])

[출력 JSON 형식]
{{
  "ideas": [
    {{
      "title": "...",
      "description": "...",
      "tags": ["...", "...", "..."]
    }}
  ]
}}"""

    return await _call_ollama(COMMON_SYSTEM_PROMPT, user_prompt, f"아이디어 생성({topic})")


async def combine_ideas_service(
    selected_ideas: List[Dict[str, Any]],
    direction: str = "두 아이디어의 장점 결합",
    count: int = 2
) -> List[IdeaItem]:
    """
    [AI 1] 선택된 2개 이상의 아이디어를 결합해 시너지 아이디어를 생성
    """
    ideas_formatted = "\n".join(
        [
            f"{idx + 1}. 제목: {idea.get('title', '')} / 설명: {idea.get('description', '')}"
            for idx, idea in enumerate(selected_ideas)
        ]
    )

    user_prompt = f"""아래 선택된 기존 아이디어들의 핵심 장점을 결합하여 새로운 융합 아이디어 {count}개를 생성하세요.

[선택된 아이디어 목록]
{ideas_formatted}

[조합 방향성]
{direction}

[작성 가이드]
1. 단순 나열이 아닌, 기존 아이디어들이 결합되어 새로운 가치를 만드는 시너지 아이디어를 제안하세요.
2. title: 융합된 특징이 드러나는 새로운 아이디어 제목
3. description: 어떻게 기존 아이디어들이 결합되었는지와 핵심 가치를 2~3문장으로 설명
4. tags: 핵심 한국어 키워드 3개

[출력 JSON 형식]
{{
  "ideas": [
    {{
      "title": "...",
      "description": "...",
      "tags": ["...", "...", "..."]
    }}
  ]
}}"""

    return await _call_ollama(COMMON_SYSTEM_PROMPT, user_prompt, "아이디어 조합")
