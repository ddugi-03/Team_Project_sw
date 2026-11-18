# 노트북 중간발표 모드

설치된 Qwen3 작은 모델을 사용하고 thinking을 끕니다.
프롬프트와 설명을 짧게 줄이고 기본 시연 흐름은 3개 생성 → 2개 선택 → 결과 1개 결합입니다.
일반 모드의 기본 모델·프롬프트·결합 개수는 유지됩니다.

## 실행

Ollama 서버가 실행 중이어야 합니다. 먼저 아래 모델이 있는지 확인하세요.

```powershell
ollama list
```

백엔드 터미널 (backend 폴더, 가상환경 활성화 후):

```powershell
$env:OLLAMA_DEMO_MODE="true"
$env:OLLAMA_MODEL="qwen3:1.7b"
python -m uvicorn main:app --reload
```

프론트 터미널 (frontend 폴더):

```powershell
$env:VITE_DEMO_MODE="true"
npm run dev
```

모델을 비교하려면 백엔드 OLLAMA_MODEL을 qwen3:0.6b로 바꾸고 다시 실행하세요.
두 모드는 각각 백엔드 추론 설정과 프론트 결합 개수를 제어하므로 함께 켜야 합니다.
발표 전에 같은 주제로 한 번 생성해 모델을 미리 로드하세요.
준비 요청도 추론과 같은 num_ctx=1024를 사용해야 불필요한 재로딩을 줄일 수 있습니다.
다른 비교 모델을 동시에 로드하지 말고, 발표 전에는 선택한 모델 하나로 확인하세요.
작은 모델은 결과 품질이 달라질 수 있으며 실제 결과를 확인해야 합니다.

일반 모드로 복구하려면 해당 터미널의 환경변수를 제거하고 재실행하세요.

```powershell
Remove-Item Env:OLLAMA_DEMO_MODE -ErrorAction SilentlyContinue
Remove-Item Env:OLLAMA_MODEL -ErrorAction SilentlyContinue
Remove-Item Env:VITE_DEMO_MODE -ErrorAction SilentlyContinue
```

## 실제 노트북 측정 (2026-11-18, CPU)

주제: 대학생의 시간 관리. 최종 1.7b 설정에서 모델 준비 후 3개 생성 9.20초,
2개 선택 후 1개 결합 5.68초로 모두 성공했습니다. 준비 요청은 0.30초였습니다.
생성 예시는 시간표 생성 앱, 스케줄 공유 플랫폼, 자기 조절 앱이었고,
결합 결과는 일정 관리 협업 플랫폼으로 정상적인 부모 ID 두 개를 보존했습니다.
이는 한 주제의 측정값이며 모든 요청의 속도나 품질을 보장하지 않습니다.

0.6b도 비교했지만 짧은 프롬프트만 사용했을 때 개수 오류와 태그 누락이 있었고,
스키마를 적용한 후에도 어색한 문장과 내용 품질 문제가 있어 1.7b를 기본으로 선택했습니다.
모델 전환 중 로딩이 97초까지 늘어난 사례도 있어 발표 전에는 단일 모델로 예열하세요.

자동 검증: backend unittest 56개, 프론트 build/lint, check-mindmap 및 check-demo 통과.

think 파라미터 공식 문서:
https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx

발표 모드에서는 JSON Schema로 필드·개수·문자열 길이를 제한합니다.
https://ollama.com/blog/structured-outputs
