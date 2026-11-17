import time
import logging
import os
import httpx
import uuid
from typing import List, Dict, Any, Optional
from app.clients.ollama import OllamaClient
from app.schemas.idea import IdeaItem
from app.core.exceptions import execute_with_retry, AIResponseParseException, OllamaConnectionException

logger = logging.getLogger(__name__)

# [AI-2 확정] 기본 모델명 및 추론 최적화 옵션
MODEL_NAME = "qwen2.5:7b"

# [AI-1 확정] 공통 System Prompt: JSON 규격 100% 강제 및 외국어(한자/중국어/영어) 혼용 완벽 차단
COMMON_SYSTEM_PROMPT = """당신은 한국의 IT 및 비즈니스 아이디어 브레인스토밍 전문가입니다.
사용자의 요청에 따라 독창적이고 실현 가능한 아이디어를 도출하며, 반드시 아래 규칙을 엄격히 준수하여 순수 JSON 객체로만 응답하세요.

[절대 규칙]
1. 언어 제한: 모든 텍스트는 오직 자연스러운 '순수 한국어'로만 작성하세요. 중국어(한자), 일본어, 불필요한 영단어를 절대 섞지 마세요.
2. 출력 형식: 인사말, 마크다운 코드 블록(```json 등), 부연 설명 없이 오직 중괄호({ })로 시작하고 끝나는 유효한 JSON만 출력하세요.
3. 스키마 고정: 최상위 키는 반드시 "ideas" 배열이어야 하며, 배열 안의 각 객체는 반드시 "title", "description", "tags" 3개의 키만 가져야 합니다. (임의로 다른 키를 추가하거나 누락하지 마세요.)
4. 태그 규칙: "tags"는 '#' 기호가 없는 핵심 한국어 명사 키워드 3개로 구성된 문자열 배열(["키워드1", "키워드2", "키워드3"])로 작성하세요."""

# [AI-2 확정] Qwen2.5 최적화 파라미터 (최대 10개 생성 시 JSON 잘림 방지를 위해 num_ctx, num_predict 확장)
OPTIMIZED_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "num_ctx": 2048,      # 다중 아이디어 조합 및 프롬프트 길이를 고려해 2048 확보
    "num_predict": 1536,  # 아이디어 최대 10개 생성 시 JSON이 중간에 잘리지 않도록 512 -> 1536으로 상향
}


async def _call_ollama(
    system_prompt: str, 
    user_prompt: str, 
    task_name: str,
    temperature: Optional[float] = None
) -> List[IdeaItem]:
    """
    Ollama API 공통 호출, 응답 속도(Latency) 측정 및 JSON 파싱 검증 헬퍼 함수
    """
    start_time = time.perf_counter()
    
    # 요청별 creativity_level(temperature)이 넘어오면 동적으로 반영
    request_options = dict(OPTIMIZED_OPTIONS)
    if temperature is not None:
        request_options["temperature"] = temperature

    try:
        async with OllamaClient(timeout=60.0) as client:
            async def request_ai_text() -> str:
                """Ollama에 한 번 요청하고 원문 응답 문자열을 반환한다."""
                try:
                    data = await client.generate(
                        model=os.getenv("OLLAMA_MODEL", MODEL_NAME),
                        prompt=user_prompt,
                        system=system_prompt,
                        format="json",
                        options=request_options,
                    )
                except ValueError as e:
                    raise AIResponseParseException("Ollama HTTP 응답 JSON 형식이 올바르지 않습니다.") from e
                raw_response = data.get("response")
                if not isinstance(raw_response, str):
                    raise AIResponseParseException("Ollama 응답의 response 필드가 문자열이 아닙니다.")
                return raw_response

            # 파싱 실패 시 최대 3회 재시도
            ideas = await execute_with_retry(request_ai_text, max_retries=3)

        elapsed = time.perf_counter() - start_time
        logger.info(f"[AI Latency] {task_name} 완료: {elapsed:.2f}초 소요")
        print(f"[AI Latency] {task_name} 완료: {elapsed:.2f}초 소요")
        return ideas

    except httpx.TimeoutException as e:
        logger.warning("[AI Timeout] %s (%.2fs)", task_name, time.perf_counter() - start_time)
        raise OllamaConnectionException("AI 응답 대기 시간을 초과했습니다. 잠시 후 다시 시도해 주세요.") from e
    except httpx.RequestError as e:
        logger.warning("[AI Connection Error] %s: %s", task_name, type(e).__name__)
        raise OllamaConnectionException() from e
    except httpx.HTTPStatusError as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"[AI Error] {task_name} 실패 ({elapsed:.2f}초): {str(e)}")
        raise OllamaConnectionException("AI 모델 서버가 요청을 처리하지 못했습니다.") from e
    except (ValueError, AttributeError, TypeError) as e:
        raise AIResponseParseException("Ollama 응답 형식이 올바르지 않습니다.") from e


async def generate_ideas_service(
    topic: str,
    count: int = 3,
    category: str = "일반",
    creativity_level: float = 0.7
) -> List[IdeaItem]:
    """
    [AI 1] 주제를 받아 Ollama AI를 통해 아이디어를 생성하고 Pydantic 객체 리스트로 반환
    """
    user_prompt = f"""다음 조건에 맞춰 서로 관점이 다른 독창적인 아이디어 {count}개를 생성하세요.

[입력 조건]
- 핵심 주제(키워드): {topic}
- 적용 분야(카테고리): {category}
- 필수 생성 개수: 정확히 {count}개 (부족하거나 초과하지 말 것)

[작성 가이드]
1. title: 직관적이고 호기심을 끄는 구체적인 아이디어 제목 (20자 이내 권장)
2. description: 누가(타겟), 어떤 문제를 해결하기 위해, 어떤 기능을 쓰는지와 기대 효과를 포함한 구체적인 설명 (공백 포함 80~120자 내외, 2~3문장)
3. tags: 아이디어의 핵심 특징을 나타내는 한국어 명사 키워드 정확히 3개

[출력 JSON 형식 및 작성 예시]
{{
  "ideas": [
    {{
      "title": "스마트 텀블러 자동 세척 구독함",
      "description": "캠퍼스 내 다회용 컵 사용을 늘리기 위해 사물함 형태의 무인 세척기를 설치하는 서비스입니다. 학생들은 사용한 텀블러를 넣고 앱으로 살균 세척을 요청해 위생과 편의성을 동시에 챙길 수 있습니다.",
      "tags": ["친환경", "무인세척", "구독서비스"]
    }}
  ]
}}"""

    return await _call_ollama(
        COMMON_SYSTEM_PROMPT, 
        user_prompt, 
        f"아이디어 생성({topic}, {count}개)",
        temperature=creativity_level
    )


async def combine_ideas_service(
    selected_ideas: List[IdeaItem],
    direction: str = "두 아이디어의 장점을 결합하여 새로운 서비스 구상",
    count: int = 2
) -> List[IdeaItem]:
    """
    [AI 2] 선택된 2개 이상의 아이디어를 결합해 시너지 아이디어를 생성
    """
    selected_ideas = [IdeaItem.model_validate(idea) for idea in selected_ideas]
    if len(selected_ideas) < 2 or len({idea.id for idea in selected_ideas}) != len(selected_ideas):
        raise ValueError("서로 다른 아이디어를 두 개 이상 선택해 주세요.")
    
    parent_ids = [idea.id for idea in selected_ideas]
    ideas_formatted = "\n".join(
        [
            f"- 아이디어 {idx + 1}: [{idea.title}] {idea.description} (키워드: {', '.join(idea.tags)})"
            for idx, idea in enumerate(selected_ideas)
        ]
    )

    user_prompt = f"""아래에 제시된 기존 아이디어들의 핵심 메커니즘과 장점을 유기적으로 융합하여, 새로운 시너지가 나는 제3의 아이디어 {count}개를 도출하세요.

[결합할 원본 아이디어 목록]
{ideas_formatted}

[융합 방향성 및 요구사항]
{direction}
- 필수 생성 개수: 정확히 {count}개

[시너지 도출 가이드]
1. 단순 나열 금지: 'A 기능과 B 기능을 함께 제공한다' 식의 1차원적인 합치기를 피하고, 두 아이디어가 만나 기존에 없던 새로운 가치를 만드는 화학적 결합을 제안하세요.
2. title: 융합된 시너지의 특징이 한눈에 드러나는 매력적인 제목 (20자 이내 권장)
3. description: 원본 아이디어들의 어떤 요소가 어떻게 결합되었는지, 그리고 이를 통해 사용자에게 어떤 새로운 혜택을 주는지 2~3문장(공백 포함 80~120자 내외)으로 명확히 설명하세요.
4. tags: 융합된 아이디어를 대표하는 핵심 한국어 명사 키워드 정확히 3개

[출력 JSON 형식]
{{
  "ideas": [
    {{
      "title": "융합된 시너지 아이디어 제목",
      "description": "첫 번째 아이디어의 핵심 기술과 두 번째 아이디어의 보상 체계를 결합한 새로운 서비스입니다. 사용자가 특정 행동을 완료하면 자동으로 맞춤형 혜택을 제공하여 참여율을 극대화합니다.",
      "tags": ["핵심키워드1", "핵심키워드2", "핵심키워드3"]
    }}
  ]
}}"""

    results = await _call_ollama(COMMON_SYSTEM_PROMPT, user_prompt, f"아이디어 조합({len(selected_ideas)}개 결합 -> {count}개 생성)")
    
    # 서버에서 직접 고유 ID와 부모 ID(parent_ids) 계보를 확정
    return [
        idea.model_copy(update={"id": str(uuid.uuid4()), "parent_ids": list(parent_ids)})
        for idea in results
    ]
