# 백엔드 A 실행·검증 가이드

> 대상: Windows 11 · VS Code · PowerShell · FastAPI 프로젝트  
> 기준 코드: 최근 검수·반영한 `backend/` (BE-B 공식 `IdeaGenerateRequest`, `IdeaCombineRequest`, `IdeaResponse` 우선)  
> 목표: **서버 실행 → Swagger 검증 → 로컬 대체 Ollama로 전체 경로 검증 → 실제 Ollama 연동**  
> 범위: 백엔드 A의 라우팅·CORS·OllamaClient·연결 지점 검증. BE-B 스키마·예외 처리, AI 프롬프트, FE 코드는 수정하지 않음.

## 0. 먼저 알아둘 결론

**현재 실제 API 라우터는 이미 Mock API가 아니다.**

```text
POST /api/v1/generate ─┐
                       ├→ ai_service.py → execute_with_retry()
POST /api/v1/combine ──┘                       │
                                             ▼
                                     clients/ollama.py
                                             │ HTTP POST /api/generate
                                             ▼
                                    Ollama 서버 또는 로컬 대체 서버
```

- `app/services/mock_service.py`는 옛날 임시 구현으로, **현재의 generate/combine 라우터에서 사용하지 않는다**. 따라서 실제 서버를 연결하기 위해 이 파일을 삭제하거나 라우터를 갈아 끼울 필요가 없다.
- `httpx.MockTransport`, `AsyncMock`, `TestClient`는 **테스트 과정에서만 사용하는 가짜 응답**이다. 일반적으로 Uvicorn으로 실행한 API에는 자동 적용되지 않는다.
- 실제 Ollama 서버가 없더라도 **서버 실행, `/docs`, 스키마의 422 검증, CORS, OllamaClient의 독립 테스트**는 가능하다.
- 실제 서버가 없는 상태에서 정상 요청으로 생성·조합을 시도하면, **접근 가능한 Ollama가 없는 한 HTTP 503**이 예상된다. 이것은 현재 설계에서 정상적인 연결 실패 응답이다.
- Swagger에서 AI 응답 200까지 경험해 보려면, 아래의 **선택 사항인 로컬 대체 Ollama HTTP 서버**를 실행할 수 있다. 이는 실제 Qwen2.5 검증을 대신하지 않는다.

## 1. 준비: Python 가상환경과 의존성

**VS Code에서 `Team_Project_sw` 프로젝트 루트**를 연 다음 터미널을 열고(`터미널 → 새 터미널`), `backend`로 이동한다.

```powershell
cd backend
```

터미널이 이미 `...\backend>`라면 `cd backend`를 다시 실행하지 않는다.

가상환경이 없다면 최초 한 번 생성한다.

```powershell
py -m venv .venv
```

PowerShell 활성화:

```powershell
.\.venv\Scripts\Activate.ps1
```

> 활성화가 실행 정책 문제로 차단되면, 활성화 없이 `\.venv\Scripts\python.exe`를 이후의 `python` 대신 사용해도 된다. 불필요하게 전역 실행 정책을 바꿀 필요는 없다.

의존성 설치:

```powershell
python -m pip install -r requirements.txt
```

Python과 패키지 확인:

```powershell
python --version
python -m pip show fastapi uvicorn httpx
```

현재 `requirements.txt`는 `fastapi`, `uvicorn[standard]`, `httpx`를 명시한다. Pydantic은 FastAPI의 의존성으로 설치된다.

## 2. FastAPI 서버 실행

**터미널 A** (`backend` 디렉터리):

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

다음 주소에서 확인한다.

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Swagger에 다음 두 항목이 보여야 한다.

- `POST /api/v1/generate`
- `POST /api/v1/combine`

서버 종료는 실행 중인 터미널에서 **Ctrl+C**. `--reload`는 로컬 개발용이며 운영 배포 옵션이 아니다.

> `http://127.0.0.1:8000/`로 접속했을 때 404가 나와도 이상이 아니다. 현재 `main.py`에는 루트(`/`) 엔드포인트가 없다.

## 3. Ollama 없이 Swagger에서 할 수 있는 검증

Swagger에서 해당 API 클릭 → **Try it out** → Request body 수정 → **Execute** 순서로 실행한다.

### 3-1. Generate — BE-B 공식 요청 스키마

정상 **형식** 예시:

```json
{
  "keyword": "IoT 기반 분리수거",
  "category": "IT/소프트웨어",
  "count": 2,
  "creativity_level": 0.7
}
```

- `keyword`: 필수 문자열, 빈 문자열 불가
- `category`: 선택, 기본값 `일반`
- `count`: 1~10
- `creativity_level`: 0.0~1.0

**실제 Ollama가 연결되지 않은 상태**에서는 위 요청이 스키마 검증을 통과하더라도 AI 호출 단계에서 **503**이 될 수 있다. 정상 형식의 요청이라는 사실과 추론 성공은 별개다.

스키마 거부 테스트:

```json
{
  "keyword": "테스트",
  "count": 0
}
```

**예상:** HTTP **422**. 모델 서버가 없어도 검증할 수 있다.

### 3-2. Combine — BE-B 공식 요청 스키마

정상 **형식** 예시:

```json
{
  "selected_ideas": [
    {
      "id": "idea-a",
      "title": "학습 플래너",
      "description": "학습 일정을 자동으로 계획합니다.",
      "tags": ["학습"]
    },
    {
      "id": "idea-b",
      "title": "집중 타이머",
      "description": "집중 시간과 휴식을 관리합니다.",
      "tags": ["시간관리"]
    }
  ],
  "direction": "대학생에게 유용한 하나의 서비스로 결합",
  "count": 2
}
```

- `selected_ideas`: **최소 2개**의 `IdeaItem` 전체 객체. 서로 다른 ID, 빈 제목·설명 금지
- `direction`: 선택, 기본값은 BE-B의 `IdeaCombineRequest` 정의를 따름
- `count`: 1~5
- 응답의 `parent_ids`: 조합에 사용한 **직접 부모의 ID** (위 예시에서는 `["idea-a", "idea-b"]`)

FE의 예전 형식은 이제 공식 규격이 아니다.

```json
{"idea_ids": ["idea-a", "idea-b"]}
```

**예상:** HTTP **422**. FE가 `selected_ideas` 객체 배열로 변경해야 한다. BE-A에서 FE 전용 변환·메모리 저장 기능을 다시 만들지 않는다.

중복 ID 검증:

```json
{
  "selected_ideas": [
    {"id": "a", "title": "A", "description": "설명 A"},
    {"id": "a", "title": "B", "description": "설명 B"}
  ]
}
```

**예상:** HTTP **422**.

> Swagger의 **422**는 FastAPI/Pydantic 입력 검증 성공을 의미한다. AI 호출 성공 테스트가 아니다.

## 4. CORS 확인: Swagger만으로는 충분하지 않음

Swagger는 백엔드 자체 출처에서 열리므로, **Swagger 성공만으로 브라우저의 교차 출처(CORS)를 검증했다고 볼 수 없다**.

서버가 실행된 상태에서 **새 PowerShell 터미널 B**를 열고 다음을 실행한다.

```powershell
$response = Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/api/v1/generate" `
  -Method Options `
  -Headers @{
    Origin = "http://localhost:5173"
    "Access-Control-Request-Method" = "POST"
    "Access-Control-Request-Headers" = "content-type"
  }
$response.StatusCode
$response.Headers["Access-Control-Allow-Origin"]
```

**예상:** 상태 코드 `200`, 허용 출처 `http://localhost:5173`.

현재 `main.py` 기본 허용 출처:

```text
http://localhost:5173
http://127.0.0.1:5173
http://localhost:3000
```

FE의 실제 개발 주소가 다르면 **서버 시작 전에** `CORS_ALLOW_ORIGINS` 환경변수에 등록해야 한다. 환경변수 변경 뒤에는 Uvicorn을 **재시작**한다.

## 5. 선택: 로컬 대체 Ollama로 전체 HTTP 연결 테스트 (실제 AI 불필요)

**목적:** `Swagger → FastAPI Router → AI Service → Retry → OllamaClient → HTTP 응답 → BE-B 파싱 → IdeaResponse`를 실제 네트워크 요청까지 포함해 확인. **진짜 Qwen2.5 추론은 하지 않는다.**

### 5-1. 임시 파일 만들기

`backend/manual_mock_ollama.py`를 생성하고 아래 코드를 붙여넣는다. 실험용 파일이므로 Git에 커밋하지 않고 확인 후 삭제해도 된다.

```python
import json
from fastapi import FastAPI, Request

app = FastAPI(title="Local Ollama Stub")

# success: 정상 응답 / retry_then_success: 2회 파싱 실패 후 성공
# always_invalid: 계속 비정상 응답 -> 백엔드에서 502
MODE = "success"
attempts = 0


@app.post("/api/generate")
async def generate(request: Request):
    global attempts
    attempts += 1
    payload = await request.json()
    print(f"[stub] attempt={attempts} model={payload.get('model')} "
          f"format={payload.get('format')} stream={payload.get('stream')}")

    if MODE == "always_invalid" or (
        MODE == "retry_then_success" and attempts <= 2
    ):
        return {"response": "이 문장은 JSON이 아닙니다"}

    ideas = [
        {
            "title": "환경 센서 플랫폼",
            "description": "센서로 환경 정보를 수집합니다.",
            "tags": ["센서", "환경", "자동화"],
        },
        {
            "title": "재활용 보상 플랫폼",
            "description": "재활용 참여에 보상을 제공합니다.",
            "tags": ["재활용", "참여", "보상"],
        },
    ]
    return {"response": json.dumps({"ideas": ideas}, ensure_ascii=False)}
```

### 5-2. 2개의 서버 실행

**터미널 A:** 대체 Ollama 서버 (`backend`에서 실행)

```powershell
python -m uvicorn manual_mock_ollama:app --host 127.0.0.1 --port 11435
```

**터미널 B:** FastAPI 서버 (`backend`에서 실행). 이미 켜 둔 8000번 서버는 Ctrl+C로 종료한 후 **이 터미널에서 재실행**한다.

```powershell
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
$env:OLLAMA_MODEL = "mock-model"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**브라우저:** <http://127.0.0.1:8000/docs>

3장의 Generate/Combine 정상 형식 JSON으로 각각 Execute를 누른다.

**예상:** 두 API 모두 200과 `status: "success"`, `ideas` 배열. Combine 결과의 각 `parent_ids`는 제출한 원본 두 ID와 일치해야 한다.

> 대체 서버는 입력된 주제·개수와 무관하게 **항상 정해 둔 아이디어 2개**를 반환한다. 이것은 파이프라인 작동 확인일 뿐 생성 품질·개수 준수 검증이 아니다.

### 5-3. Retry·오류 확인 (선택)

임시 파일의 `MODE` 값을 바꾸고 **대체 Ollama 서버를 재시작**한다.

| `MODE` | 예상 결과 | 확인할 점 |
|---|---|---|
| `"success"` | 200 | `[stub]` 요청 1회 |
| `"retry_then_success"` | 200 | 파싱 실패 후 3번째 호출에서 성공 |
| `"always_invalid"` | 502 / `AI_PARSE_ERROR` | 3번 호출해도 실패 |

대체 서버를 **종료**하고 FastAPI는 같은 `OLLAMA_BASE_URL`로 실행해 둔 뒤 정상 형식 요청을 보내면 **503 / `OLLAMA_CONNECTION_ERROR`**가 예상된다.

재시도 정책은 **파싱 오류에만 적용**된다. HTTP 연결 실패·타임아웃은 재시도 대상이 아니다.

## 6. 실제 Ollama 서버로 전환 (AI 담당자가 주소 제공한 뒤)

**핵심: 현재 실행 코드에서 Mock → 실서버로 바꾸려고 수정해야 하는 Python 파일은 기본적으로 없다.** 테스트용 대체 서버 대신 실제 Ollama 주소와 모델명을 지정하면 된다.

AI 담당자에게 아래 정보를 받는다.

- 네트워크상 접근 가능한 **서버 주소와 포트** (예: `http://192.168.x.x:11434`)
- 실제 로드된 **모델명** (`qwen2.5:7b` 등)
- 본인 PC에서 해당 서버에 접근 가능한지 (같은 LAN/VPN, 방화벽, 인증/접근 정책)
- 생성·조합 프롬프트와 JSON 출력 방식 확정 여부

**백엔드를 실행할 PowerShell 터미널**에서, 실제 제공받은 주소를 사용하여:

```powershell
$env:OLLAMA_BASE_URL = "http://실제서버주소:11434"
$env:OLLAMA_MODEL = "qwen2.5:7b"
Invoke-RestMethod -Uri "$env:OLLAMA_BASE_URL/api/tags"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

`/api/tags`에서 모델 목록이 보이면 **서버 API에 도달했다**는 뜻이다. 사용하려는 모델이 있는지도 확인한다. **모델 목록 조회 성공만으로 생성 API가 성공한다는 의미는 아니다.**

`localhost:11434`는 **현재 사용 중인 본인 PC**를 가리킨다. AI 팀원의 컴퓨터에서 Ollama를 실행한다면 상대 컴퓨터의 접근 가능한 주소를 사용해야 한다. Ollama 포트를 인터넷에 무방비로 공개하지 말고 팀 내 제한된 네트워크에서 접근하도록 협의한다.

이제 Swagger에서 3장의 정상 Generate·Combine 요청을 실행한다. **실제 생성 응답의 ID를 복사하여 조합 요청에 넣는 흐름**으로 확인하면 더 좋다.

### 실제 응답 판정 기준

| 응답 | 해석 | 우선 확인 대상 |
|---|---|---|
| 200 + `status: success` | API가 요청·추론·파싱·응답을 통과 | 제목·설명·태그·개수·`parent_ids` 검토 |
| 422 | BE-B 요청 스키마 위반 | JSON 키와 필수 필드 |
| 502 + `AI_PARSE_ERROR` | AI 출력 JSON을 파싱·검증하지 못함 (재시도 후 실패 가능) | AI 프롬프트/JSON 출력, BE-B 파서 |
| 503 + `OLLAMA_CONNECTION_ERROR` | 서버 연결·응답 지연·HTTP 상태 오류 | 서버 주소, 모델명, 방화벽, 모델 동작 |

현재 `ai_service.py`는 호출마다 60초 타임아웃을 사용하고 파싱 오류 시 최대 **총 3회 호출**한다. 실제 추론이 느리면 요청 전체가 길어질 수 있으므로 FE의 타임아웃과 함께 점검한다.

## 7. Mock을 없앴을 때 무엇이 작동하고, 무엇이 멈추나?

| 기능 / 코드 | Mock 없이 Ollama 서버도 없을 때 | 실서버로 바꿀 때 할 일 |
|---|---|---|
| `main.py` / FastAPI 서버 시작 | **작동** | 변경 불필요 |
| `/docs`, `/openapi.json` | **작동** | 변경 불필요 |
| Generate/Combine 잘못된 입력의 422 | **작동** | 변경 불필요 |
| CORS 사전 요청 | **작동** | FE 실제 출처 확인 |
| `clients/ollama.py` HTTP 클라이언트 | 코드는 동작하나 **외부 응답 없음** | `OLLAMA_BASE_URL` 설정 |
| 정상 Generate 요청 | Ollama 연결 실패로 **503 예상** | 서버 주소·모델 확인 후 재실행 |
| 정상 Combine 요청 | Ollama 연결 실패로 **503 예상** | FE는 `selected_ideas` 사용 |
| `ai_service.py` Retry | 코드 존재, 실제 파싱 재시도는 AI 응답 없으면 관찰 불가 | 실제 추론 또는 로컬 대체 서버로 검증 |
| `services/mock_service.py` | **라우터에서 참조하지 않아 영향 없음** | 굳이 수정·삭제하지 않아도 됨 |
| 과거 `manual_api_check.py`의 `AsyncMock` | 해당 테스트만 성공 | 실제 API 성공의 증거로 혼동하지 않기 |
| 과거 `manual_ollama_check.py`의 `MockTransport` | 해당 테스트만 성공 | 실제 모델 응답은 별도 검증 필요 |

**실서버 전환 때 기본적으로 수정할 곳은 환경변수뿐**이지만, 데이터 계약 변경이 발생하면 별도 조정이 필요하다.

- FE의 구형 `idea_ids` → BE-B 공식 `selected_ideas` 변경 (**FE 담당**) 
- `ErrorResponse.message` 우선 표시와 `parent_ids` 매핑 (**FE 담당**)
- `creativity_level`이 현재 `OPTIMIZED_OPTIONS["temperature"]`에 실제 반영되지 않는 점 (**AI-2와 협의 필요**)
- JSON 출력 품질, 모델 옵션, 추론 지연 (**AI 담당**)
- `IdeaRegistry` 및 과거 테스트 파일은 현재 API 호출 경로에서 사용하지 않음. **서버 실행을 위해 제거할 필요 없음**

## 8. 전체 React E2E 전에 확인할 항목

1. 백엔드 Swagger에서 정상 Generate·Combine 응답 200이 확인되었는가?
2. FE가 `POST /api/v1/combine`에 `idea_ids`가 아니라 **`selected_ideas`**를 보내도록 변경했는가?
3. FE의 실제 Origin이 CORS 허용 목록에 포함돼 있는가?
4. FE Axios의 Base URL이 이 FastAPI 주소(보통 `http://localhost:8000`)를 가리키는가?
5. FE 타임아웃이 실제 추론 및 Retry에 충분한가?
6. 프론트엔드에서 입력 → 카드 생성 → 다중 선택 → 조합 결과 추가 표시까지 확인했는가?

**Swagger의 API 성공은 백엔드–Ollama E2E이며, React까지 포함한 전체 E2E는 별도이다.**

## 9. 문제 발생 시 빠른 확인표

| 증상 | 주된 확인 지점 |
|---|---|
| `No module named ...` | 현재 `backend` 가상환경, `pip install -r requirements.txt` |
| `Could not import module "main"` | 터미널 위치가 `backend`인지 확인 |
| `Address already in use` / 포트 충돌 | 기존 Uvicorn 중복 실행 여부 |
| `/`에서 404 | 루트 라우트 없음. `/docs` 사용 |
| Swagger 정상 요청이 503 | Ollama 주소·포트·프로세스·모델명·접속 가능 여부 확인 |
| 정상 요청이 502 | AI가 반환한 JSON 텍스트 형식·BE-B 파싱 결과 확인 |
| Combine이 422 | `selected_ideas` 전체 객체, 2개 이상, 중복 ID 확인 |
| 브라우저 FE에서만 CORS 실패 | 실제 프론트 주소, `CORS_ALLOW_ORIGINS`, 서버 재시작 확인 |
| Starlette 관련 DeprecationWarning | 테스트 클라이언트 라이브러리 경고. **실제 API 실패와 구분** |

## 10. 직접 검증 결과 기록 (작성용)

| 테스트 | 결과 | 확인 날짜 / 비고 |
|---|---|---|
| FastAPI 실행 / `/docs` 접속 | [ ] 통과 [ ] 실패 | |
| Generate 잘못된 입력 422 | [ ] 통과 [ ] 실패 | |
| Combine 잘못된 입력 422 | [ ] 통과 [ ] 실패 | |
| CORS Preflight 200 | [ ] 통과 [ ] 실패 | |
| 로컬 대체 Ollama → Generate 200 | [ ] 통과 [ ] 실패 [ ] 생략 | |
| 로컬 대체 Ollama → Combine 200 / `parent_ids` | [ ] 통과 [ ] 실패 [ ] 생략 | |
| 로컬 대체 Ollama → Retry 3회 | [ ] 통과 [ ] 실패 [ ] 생략 | |
| 실제 Ollama `/api/tags` 연결 | [ ] 통과 [ ] 실패 [ ] 서버 미확보 | |
| 실제 Ollama → Generate 200 | [ ] 통과 [ ] 실패 [ ] 서버 미확보 | |
| 실제 Ollama → Combine 200 | [ ] 통과 [ ] 실패 [ ] 서버 미확보 | |
| React → FastAPI → Ollama → React | [ ] 통과 [ ] 실패 [ ] FE 수정 대기 | |

---

**완료 기준**: 백엔드 A의 코드 구현은 현재 거의 완료된 상태이며, 실제 AI 서버 주소·모델을 확보한 뒤 Swagger에서 **Generate와 Combine 모두 정상 200**을 확인하고, FE와 실제 E2E까지 마쳐야 3주차 통합 마일스톤을 최종 완료로 표시할 수 있다.
