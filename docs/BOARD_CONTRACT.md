# 4주차 백엔드 B: 보드 저장·복원 계약

## 구현 범위와 역할 연결

- 백엔드: 버전이 있는 JSON 스키마, 전체 보드 검증, 관계 보존, 선택적 평가 기록 형식.
- 프론트 담당자가 연결할 부분: 파일 선택·다운로드 버튼, 아래 직렬화/복원 변환, 검증 성공 후 한 번의 상태 교체.
- 서버 디스크·DB·전역 레지스트리에 보드를 저장하지 않습니다. 호출 간 보드 상태가 없으며 로그인·세션 기능도 추가하지 않습니다.
- 기존 `POST /api/v1/generate`, `/api/v1/combine`의 요청·응답 계약은 변경하지 않습니다.
- 원본 반영 판단·유사도 계산·모델 변경은 AI 파트 범위입니다. 아래 평가 필드는 합의·연결용이며 자동 평가 구현을 의미하지 않습니다.

## API

| 요청 | 성공 | 용도 |
|---|---|---|
| `POST /api/v1/board/export` | 200 + BoardDocument | 현재 보드의 저장 형식을 검증하고 반환 |
| `POST /api/v1/board/validate` | 200 + BoardDocument | 파일을 상태에 반영하기 전에 전체 문서를 검증 |

두 경로 모두 JSON 본문에 **BoardDocument 자체**를 받으며 `status` 래퍼 없이 검증된 문서를 반환합니다.
필수 형식·버전 필드는 생략할 수 없습니다. 오류는 기존 FastAPI 방식인 422 `detail` 배열이며, 기존 프론트의 요청 형식 오류 처리와 호환됩니다.
응답은 `parent_ids`와 ID·배열 순서·위치를 유지하며 null인 선택 필드만 생략합니다. 위치의 정수/실수 표기는 정규화될 수 있습니다.
검증 실패 시 부분 결과를 반환하거나 저장 상태를 바꾸지 않습니다. 문서를 실행하거나 외부 URL을 호출하지 않습니다.

```json
{
  "format": "idea-note-board",
  "schema_version": 1,
  "topic": "팀 일정",
  "ideas": [
    {"id": "a", "title": "시간표 도구", "description": "빈 시간을 찾습니다.", "tags": [], "parent_ids": []},
    {"id": "b", "title": "공동 일정", "description": "가능 시간을 모읍니다.", "tags": [], "parent_ids": []},
    {"id": "c", "title": "팀 모임", "description": "시간표의 빈 시간을 모아 모임을 제안합니다.", "tags": [], "parent_ids": ["a", "b"]}
  ],
  "positions": {"topic": {"x": 24, "y": 24}, "a": {"x": 340, "y": 120}}
}
```

위치가 없는 카드는 기존 자동 배치로 복원합니다. `positions.topic`은 중앙 주제 카드의 위치이며, 아이디어 ID로 `topic`을 사용할 수 없습니다.
현재 범위는 **카드·주제·위치·원본 관계**입니다. 화면의 zoom/scroll, 선택 상태, 생성 폼의 category/creativity는 저장하지 않습니다.

## 검증 규칙

- 보드 최대 500개 카드, 위치 최대 501개. ID 최대 128자, 제목 500자, 설명·주제 4,000자.
- 태그 최대 50개, 태그당 최대 100자. 빈 제목·설명·태그 및 앞뒤 공백/제어 문자가 있는 ID를 거부합니다.
- 알 수 없는 필드를 거부합니다. 파일에서는 `parentIds`가 아니라 `parent_ids`를 사용합니다.
- ID는 파일에 반드시 있어야 하며 누락 시 새 ID를 만들지 않습니다. 중복 ID를 거부합니다.
- 부모는 모두 같은 보드에 있어야 합니다. 자기 참조·중복 부모·순환을 거부합니다. 부모는 없거나 두 개 이상이어야 합니다.
- 카드 배열 순서는 자유입니다. 부모보다 자식이 먼저 있어도 유효하며 저장 순서 그대로 반환합니다.
- 위치는 유한한 숫자이고 0~1,000,000 범위입니다. 숫자 문자열·boolean·NaN·Infinity는 허용하지 않습니다.
- 지원하지 않는 format/version을 거부합니다. 향후 버전 변경 시 명시적 변환 절차를 추가해야 합니다.

개수·문자 길이 제한은 역직렬화 후의 데이터 제한입니다. 업로드 전체 바이트 제한·인증·호출 제한은 이 구현에 포함하지 않습니다.
프론트는 큰 파일을 읽기 전 용량을 확인하고, 공개 배포 시 백엔드 A와 요청 본문 크기·동시 요청 제한을 별도로 적용해야 합니다.

## 프론트 연결 예시

기존 `frontend/src/services/api.js`의 Axios 인스턴스로 `/api/v1/board/export`, `/api/v1/board/validate`를 호출합니다.
내보내기 전 busy 상태를 확인하고, 요청 시작 시점의 스냅샷을 생성합니다.

```js
const snapshot = {
  format: 'idea-note-board',
  schema_version: 1,
  topic: state.topic,
  ideas: state.ideas.map(idea => ({
    id: idea.id,
    title: idea.title,
    description: idea.description,
    tags: idea.tags || [],
    parent_ids: idea.parentIds ?? idea.parent_ids ?? [],
    ...(idea.combination_review ? { combination_review: idea.combination_review } : {}),
  })),
  positions: structuredClone(state.positions),
}
const { data: document } = await api.post('/api/v1/board/export', snapshot)
// document를 JSON.stringify 후 Blob으로 다운로드합니다. 생성한 object URL은 사용 후 해제합니다.
```

불러오기 전에는 생성·조합 중인지 확인하고, 파일 JSON 파싱 후 `/board/validate`에 전달합니다.
가져오기 진행 중에도 편집을 막거나 작업 버전 토큰을 확인해, 늦게 돌아온 응답이 새로운 편집을 덮지 않게 해야 합니다.
실패하면 `ideas`, `positions`, `topic`을 하나도 변경하지 않습니다. 성공 시에만 Zustand 상태를 한 번에 교체합니다.

```js
const { data: document } = await api.post('/api/v1/board/validate', parsedFile)
set({
  topic: document.topic,
  ideas: document.ideas.map(({ parent_ids, ...idea }) => ({
    ...idea,
    // 루트의 []를 undefined로 바꿔 기존 중앙 주제 연결 로직과 맞춥니다.
    parentIds: parent_ids.length ? parent_ids : undefined,
  })),
  positions: document.positions,
  selectedIds: [],
  notice: null,
})
```

서버는 최근 생성 ID 레지스트리를 이용해 복원하지 않습니다. 기존 combine은 선택된 **전체 카드 내용**을 받으므로 서버 재시작 후에도 저장 파일의 원본 ID로 재조합할 수 있습니다.
저장 파일의 ID·관계 검증은 참조 일관성 검사이며, 파일 작성자 인증이나 내용 진위 보증은 아닙니다.

## AI 2와 합의할 선택적 평가 필드

각 BoardIdea에 아래 `combination_review`를 선택적으로 추가할 수 있습니다. 기존 파일에는 없어도 됩니다.

```json
{
  "evaluated_by": "human",
  "source_usage": [
    {"source_id": "a", "used_element": "빈 시간 탐색", "evidence": "시간표에서 빈 시간을 찾음"},
    {"source_id": "b", "used_element": "참여자 일정 취합", "evidence": "각자의 가능 시간을 비교함"}
  ],
  "note": "평가자가 확인한 내용"
}
```

- `evaluated_by`: `human` 또는 `ai`. `source_usage`의 ID는 직접 부모 전체와 중복 없이 정확히 일치해야 합니다.
- `used_element`, `evidence`는 비어 있으면 안 됩니다. 백엔드는 참조와 형식만 검사하며 근거가 실제 맞는지 판단하지 않습니다.
- AI 파트가 원본 누락·중복 평가와 재생성 흐름을 완성한 뒤 생성 파이프라인 연결을 별도 변경으로 진행합니다.
- 기존 생성 응답에 이 필드를 자동으로 추가하거나, 이 기록만으로 '편향 해결'을 선언하지 않습니다.

## 실행·검증

```powershell
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m uvicorn main:app --reload
```

`http://localhost:8000/docs`에서 board 두 API를 확인할 수 있습니다. 예시 파일은 `docs/examples/board-v1.json`입니다.
통합 테스트는 Ollama HTTP 또는 AI 호출을 모의 처리합니다. 실제 모델의 속도·품질이나 프론트 파일 버튼 완성까지 검증한 것은 아닙니다.
