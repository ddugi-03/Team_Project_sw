# 백엔드 A 개발 현황 및 연동 안내

**담당 범위:** FastAPI API 기본 구조 및 Ollama HTTP 클라이언트 구축

**현재 상태:** 담당 모듈의 초기 구현 및 독립 테스트 완료, 실제 AI 통합 대기

**하단에 fastAPI 서버 테스트 방법 추가.**

### 1. 구현 완료 사항

**FastAPI 서버**
- FastAPI 서버 기본 구조 및 실행 환경 구축
- `/api/v1/generate`, `/api/v1/combine` 엔드포인트 구현
- 임의 JSON 객체 수신 및 Mock 응답 반환
- Swagger UI(`/docs`) 동작 확인

**Ollama HTTP 클라이언트**
- `httpx.AsyncClient` 기반 비동기 통신 구현
- Ollama `/api/generate`, `/api/chat` 엔드포인트 지원
- `stream: false` 방식의 JSON 요청 및 응답 수신
- `OLLAMA_BASE_URL` 환경변수를 통한 서버 주소 설정
- HTTP 오류 및 연결 실패 시 예외 전달
- 외부 HTTP 클라이언트 주입 및 비동기 자원 종료 지원

### 2. 검증 현황

Ollama 서버를 모방하는 `httpx.MockTransport`를 사용해 6개 단위 테스트 통과.

기존 FastAPI Mock 엔드포인트와 Swagger UI 정상 동작 확인.

실제 Ollama 모델 호출은 수행하지 않았음.

### 3. 현재 구현 상태

```text
React 프론트엔드
       │
       ▼
FastAPI 서버
 ├── /api/v1/generate ── Mock 응답
 └── /api/v1/combine  ── Mock 응답

OllamaClient (구현 완료)
 ├── /api/generate
 └── /api/chat
       │
       ▼
Ollama 서버 (실제 연동 대기)
```

현재 FastAPI API와 OllamaClient는 각각 구현되어 있으며, **실제 AI 호출 파이프라인은 아직 연결하지 않은 상태**입니다.

### 4. 이후 진행할 작업

1. 확정된 API 스키마 -> 서비스 계층에서 FastAPI 엔드포인트와 OllamaClient 연결
2. 전체 요청·응답 및 예외 처리 통합 검증

**FastAPI API 뼈대와 Ollama HTTP 클라이언트 구현은 완료되었습니다.**

오류 및 연동에 대해 언제든 말씀주세요.

##
## FastAPI 백엔드 로컬 실행 방법

**1. 프로젝트 Clone 후 백엔드 디렉터리로 이동**

```bash
cd backend
```

**2. Python 가상환경 생성 (최초 1회)**

```bash
python -m venv .venv
```

**3. 가상환경 활성화 (Windows)**

PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:
```cmd
.venv\Scripts\activate.bat
```

**4. 의존성 설치**

```bash
python -m pip install -r requirements.txt
```

**5. FastAPI 서버 실행**

```bash
python -m uvicorn main:app --reload
```

**6. Swagger UI 접속**

http://127.0.0.1:8000/docs

Swagger에서 다음 API를 직접 실행할 수 있습니다.

- `POST /api/v1/generate`
- `POST /api/v1/combine`

현재 두 API는 Mock 응답을 반환하므로, 실제 Ollama 서버 없이 테스트할 수 있습니다.

**7. Ollama 클라이언트 단위 테스트 (선택)**

```bash
python -m unittest discover -s tests -v
```

실제 모델 서버 없이 HTTP 통신 클라이언트의 동작을 검증할 수 있습니다.

서버 종료는 터미널에서 `Ctrl + C`를 누르면 됩니다.
