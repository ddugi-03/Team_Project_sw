# 아이디어 노트

캔버스 위의 `−` / `+` 버튼으로 10~150% 범위에서 배율을 조절합니다. `100%`는 기본 크기로 복구하고, `전체 보기`는 현재 보드를 화면에 맞춰 축소합니다. 배율을 바꿔도 카드 선택·결합을 사용할 수 있습니다.

확대·축소는 현재 화면 중심을 유지합니다. 카드와 중심 주제의 `이동` 손잡이를 드래그하면 위치와 연결선이 함께 갱신됩니다. 손잡이에 키보드 초점을 두고 방향키로 10px씩, Shift+방향키로 40px씩 이동할 수 있습니다. `자동 배치`로 원래 정렬을 복구합니다. 새 주제를 생성하거나 새로고침하면 수동 배치는 초기화됩니다.

주제별 아이디어를 생성하고 마인드맵에서 카드를 두 개 이상 선택해 결합합니다. 선택 개수에는 상한이 없으며, 결합한 카드도 다시 선택할 수 있습니다. 생성 개수는 양의 정수로 입력합니다. 새 주제를 생성하면 현재 보드를 교체하며 새로고침 시 보드는 초기화됩니다.

```sh
npm install
npm run dev
```

## 백엔드 연결

`npm run dev`로 실행하면 빈 보드로 시작하며 생성·결합 요청은 실제 API를 호출합니다. 아이디어 생성·결합에는 실행 중인 백엔드가 필요합니다.

## API 설정

서버 주소를 변경하려면 `.env.example`을 `.env.local`로 복사하고 값을 설정한 뒤 개발 서버를 다시 실행합니다.

```env
VITE_API_BASE_URL=http://localhost:8000
```

프론트엔드가 사용하는 API 계약입니다. 백엔드 구현과 요청·응답 형식을 맞춰야 합니다.

- `POST /api/v1/generate`: `{ keyword, category, count }` → `{ ideas: [{ id, title, description, tags }] }`
- `POST /api/v1/combine`: `{ idea_ids: [id1, id2, ...] }` → `{ ideas: [{ id, title, description, tags }] }`

응답의 `id`는 재결합 요청에도 사용합니다. 백엔드는 결과에 고유한 `id`를 반환하고 아이디어를 보관해야 합니다. 프론트엔드는 결합 카드에 `parentIds`를 붙여 연결선을 관리합니다.

백엔드 CORS에는 개발 서버가 출력한 프론트엔드 주소를 허용해야 합니다. Vite 기본 주소는 `http://localhost:5173`입니다. 계획서의 `localhost:3000`에 맞추려면 `npm run dev -- --port 3000`으로 실행합니다.

검증:

```sh
npm run build
npm run lint
node scripts/check-mindmap.mjs
node scripts/check-layout.mjs
node scripts/check-zoom.mjs
```

API 검증 스크립트는 테스트 안에서만 Axios 응답을 대체합니다. 배치·연결 경로·배율 계산도 별도로 검증합니다. 실제 백엔드와의 통합 검증은 서버 실행 후 진행해야 합니다.
