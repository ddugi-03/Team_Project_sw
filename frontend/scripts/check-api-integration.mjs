import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import axios from 'axios'
import { createServer } from 'vite'

// Axios 직렬화 결과를 실제 FastAPI 요청 검증/라우터에 전달합니다. AI 추론만 대체합니다.
const originalAdapter = axios.defaults.adapter
const bridge = fileURLToPath(new URL('../../backend/tests/frontend_bridge.py', import.meta.url))
axios.defaults.adapter = async (config) => {
  const response = JSON.parse(execFileSync(process.env.PYTHON || 'python', ['-X', 'utf8', bridge], {
    input: JSON.stringify({ url: config.url, body: JSON.parse(config.data) }),
    encoding: 'utf8',
  }))
  assert.equal(response.status, 200, JSON.stringify(response.data))
  return { ...response, statusText: 'OK', headers: {}, config }
}
const server = await createServer({ server: { middlewareMode: true, ws: false, watch: null }, appType: 'custom' })
try {
  const { useIdeaStore: store } = await server.ssrLoadModule('/src/store/useideastore.js')
  await store.getState().generateIdeas({ keyword: '학습', count: 2 })
  assert.equal(store.getState().ideas.length, 2)
  assert.ok(store.getState().ideas.every((idea) => idea.parentIds === undefined))
  const [first, second] = store.getState().ideas
  store.getState().toggleIdea(first.id)
  store.getState().toggleIdea(second.id)
  await store.getState().combineIdeas()
  assert.equal(store.getState().ideas.length, 4)
  const combined = store.getState().ideas.at(-1)
  assert.deepEqual(combined.parentIds, [first.id, second.id])
  store.getState().toggleIdea(first.id)
  store.getState().toggleIdea(combined.id)
  await store.getState().combineIdeas()
  assert.equal(store.getState().ideas.length, 6)
  assert.deepEqual(store.getState().ideas.at(-1).parentIds, [first.id, combined.id])
  assert.equal(store.getState().notice.type, 'success')
  console.log('PASS: 실제 FastAPI 계약으로 프론트 생성 → 결합 → 재결합 및 부모 관계 검증 (AI만 모킹)')
} finally {
  axios.defaults.adapter = originalAdapter
  await server.close()
}
