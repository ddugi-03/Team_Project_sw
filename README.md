# 💡 AI 기반 아이디어 브레인스토밍 플랫폼

> 키워드와 조건을 바탕으로 AI가 아이디어를 생성·조합하고, Excalidraw 캔버스 위에서 시각적으로 발전시키는 웹 서비스입니다.

---

## 🚀 프로젝트 개요
* **서비스명:** AI 아이디어 브레인스토밍 플랫폼 (가제)
* **주요 기능:**
  * 조건별(키워드, 분야 등) 아이디어 생성
  * 기존 아이디어 간 결합 및 고도화
  * 카드 기반 아이디어 시각화 및 무한 캔버스 연동
  * 아이디어 간 관계도 표현 및 저장/불러오기
* **차별점:** 단순 AI 챗봇 형태를 벗어나 아이디어의 생성·결합·발전 과정을 시각적으로 구조화 및 관리

---

## 🛠️ 기술 스택 (Tech Stack)

### Frontend
- **Framework:** React
- **Canvas / Visualization:** Excalidraw (`@excalidraw/excalidraw`)
- **State Management:** Zustand / React Query

### Backend & AI
- **Framework:** Python, FastAPI
- **Local AI Engine:** Ollama
- **LLM Model:** Qwen (Qwen2.5)
- **Data Processing:** JSON / Pydantic

---

## 📂 프로젝트 구조 (Directory Structure)

```text
.
├── backend/            # FastAPI 백엔드
│   ├── app/
│   │   ├── api/        # API 라우터 (generate, combine 등)
│   │   ├── core/       # Ollama 및 프롬프트 로직
│   │   └── schemas/    # Pydantic 데이터 모델
│   ├── main.py
│   └── requirements.txt
└── frontend/           # React 프론트엔드
    ├── src/
    │   ├── components/ # UI 및 Excalidraw 컴포넌트
    │   ├── store/      # 상태 관리
    │   └── services/   # 백엔드 API 연동
    └── package.json