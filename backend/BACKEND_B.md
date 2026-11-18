# 3주차 백엔드 B 구현 및 연동 안내

## 완료 범위

- 공통 IdeaCombineRequest로 선택한 IdeaItem 전체를 검증하고 프롬프트에 제목·설명 전달
- 중복 선택, 빈 ID·제목·설명, 최소 선택 개수 및 결과 개수 범위 검증
- 결과 ID와 parent_ids를 서버 UUID 및 직접 선택한 부모 ID로 확정
- 재결합 시 조상 전체가 아닌 직접 부모만 기록
- Excalidraw Skeleton 변환 스키마와 순수 어댑터 추가
- 실제 AI 서비스에서 타임아웃·연결 실패·HTTP 오류를 OllamaConnectionException으로 매핑 및 로깅
- FastAPI에 502 파싱 오류 / 503 연결 오류 핸들러 등록

## 프론트 연동 계약

POST /api/v1/combine

```json
{
  "selected_ideas": [
    {"id": "a", "title": "스터디 플래너", "description": "학습 일정을 배분합니다.", "tags": ["학습"]},
    {"id": "b", "title": "집중 타이머", "description": "집중 시간을 관리합니다.", "tags": ["집중"]}
  ],
  "direction": "대학생에게 유용한 서비스",
  "count": 2
}
```

응답은 기존 IdeaResponse이며 각 결과에 새로운 id와 parent_ids: ["a", "b"]가 들어갑니다.
selected_ideas에는 이전 생성/결합 API 응답의 원본 id를 포함하세요. DB 저장 없이 카드 내용으로 재결합합니다.

프론트 후속 작업:

- 현재 idea_ids 요청을 selected_ideas 전체 객체 요청으로 변경
- 서버 parent_ids를 사용하거나 기존 화면의 parentIds로 매핑
- 오류 토스트는 ErrorResponse.message를 우선 표시 (detail은 없을 수 있음)

## 캔버스 변환 (4주차 연결 준비)

```python
from app.services.canvas_service import ideas_to_canvas
data = ideas_to_canvas(all_board_ideas).model_dump(mode="json")
```

모든 부모가 포함된 보드의 IdeaItem 목록을 받습니다. 원본 노드와 결합 노드를 단계별로 배치하고,
직접 부모마다 화살표를 만듭니다. 입력 순서와 무관하게 관계를 계산합니다.
중복 ID, 부모 누락, 중복 부모, 자기 참조, 순환 관계는 ValueError로 거부합니다.
제목·설명은 label, 원본 데이터와 계보는 customData에 보존합니다.

출력은 완성된 .excalidraw 파일이 아닌 ExcalidrawElementSkeleton 목록입니다.
프론트에서 정식 요소로 변환한 후 initialData/updateScene에 전달하세요.

```js
import { convertToExcalidrawElements } from '@excalidraw/excalidraw'
const elements = convertToExcalidrawElements(data.elements, { regenerateIds: false })
```

공식 계약: https://github.com/excalidraw/excalidraw/blob/master/dev-docs/docs/%40excalidraw/excalidraw/api/excalidraw-element-skeleton.mdx

캔버스 HTTP 라우터·프론트 Excalidraw 설치는 이번 범위에 포함되지 않습니다.
실제 패키지 변환과 렌더링 검증은 4주차 프론트 연동 시 진행합니다.

## 다른 담당자 연동 사항

- 백엔드 A: CORS 개발 서버 허용, execute_with_retry 연결 및 OllamaClient 통합
- AI 담당: 결과 개수 준수, JSON 안정화 및 벤치마크
- ai_service의 Ollama 주소·모델·60초 타임아웃과 프롬프트는 유지
- 프론트 제한 시간은 백엔드 추론/재시도 시간보다 여유 있게 조정 필요

## 검증

backend 디렉터리에서:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

실제 Ollama 대신 MockTransport/AsyncMock으로 조합 API, 계보·재결합, 스키마 검증,
타임아웃·연결 장애, 오류 응답 및 캔버스 그래프를 검증합니다.
실제 모델 품질·지연과 브라우저 E2E는 발표 노트북에서 별도로 확인해야 합니다.
