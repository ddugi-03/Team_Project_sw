# 아이디어 노트

주제별 아이디어를 생성하고 마인드맵에서 카드를 두 개 이상 선택해 결합합니다. 선택 개수에는 상한이 없으며, 결합한 카드도 다시 선택할 수 있습니다. 생성 개수는 양의 정수로 입력합니다. 새 주제를 생성하면 현재 보드를 교체하며 새로고침 시 보드는 초기화됩니다.

```sh
npm install
npm run dev
```

## 백엔드 연결

처음에는 빈 보드가 표시되며 모든 생성·결합 요청은 실제 API를 호출합니다. 더미데이터나 실패 시 예시 데이터를 표시하는 기능은 없습니다.

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
```

검증 스크립트는 테스트 안에서만 Axios 응답을 대체합니다. 실제 백엔드와의 통합 검증은 서버 실행 후 진행해야 합니다.
