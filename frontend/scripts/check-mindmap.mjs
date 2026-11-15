import assert from 'node:assert/strict'
import axios from 'axios'
import { createElement } from 'react'
import { renderToString } from 'react-dom/server'
import { createServer } from 'vite'

// 앱에는 더미 모드가 없으며 테스트에서만 HTTP 응답을 대체합니다.
const originalAdapter = axios.defaults.adapter
const requests = []
let respond
axios.defaults.adapter = async (config) => {
  requests.push({ url: config.url, body: JSON.parse(config.data) })
  return { data: await respond(), status: 200, statusText: 'OK', headers: {}, config }
}
const server = await createServer({ server: { middlewareMode: true, ws: false, watch: null }, appType: 'custom' })
try {
  const { useIdeaStore: store } = await server.ssrLoadModule('/src/store/useideastore.js')
  const { default: App } = await server.ssrLoadModule('/src/App.jsx')
  assert.deepEqual(store.getState().ideas, [])
  assert.ok(renderToString(createElement(App)).includes('주제를 입력하면'))
  const items = Array.from({ length: 7 }, (_, i) => ({ id: `server-${i}`, title: `테스트 ${i}`, tags: [] }))
  let release
  respond = () => new Promise((resolve) => { release = resolve })
  const pending = store.getState().generateIdeas({ keyword: '교육', category: '교육', count: 7 })
  assert.equal(store.getState().isGenerating, true)
  await store.getState().generateIdeas({ keyword: '중복', count: 7 })
  assert.equal(requests.length, 1)
  release({ ideas: items })
  await pending
  assert.equal(store.getState().isGenerating, false)
  assert.deepEqual(requests[0], { url: '/api/v1/generate', body: { keyword: '교육', category: '교육', count: 7 } })
  store.getState().toggleIdea(items[0].id)
  await store.getState().combineIdeas()
  assert.equal(requests.length, 1)
  for (const item of items.slice(1)) store.getState().toggleIdea(item.id)
  assert.equal(store.getState().selectedIds.length, 7)
  store.getState().toggleIdea(items[6].id)
  assert.equal(store.getState().selectedIds.length, 6)
  store.getState().toggleIdea(items[6].id)
  respond = () => new Promise((resolve) => { release = resolve })
  const combining = store.getState().combineIdeas()
  assert.equal(store.getState().isCombining, true)
  store.getState().clearSelection()
  assert.equal(store.getState().selectedIds.length, 7)
  await store.getState().combineIdeas()
  assert.equal(requests.length, 2)
  release({ ideas: [{ id: 'server-combined', title: '결합 결과' }] })
  await combining
  assert.deepEqual(requests[1], { url: '/api/v1/combine', body: { idea_ids: items.map((item) => item.id) } })
  assert.equal(store.getState().ideas.length, 8)
  assert.deepEqual(store.getState().ideas.at(-1).parentIds, items.map((item) => item.id))
  assert.equal(store.getState().ideas.at(-1).id, 'server-combined')
  assert.deepEqual(store.getState().selectedIds, [])
  assert.equal(store.getState().isCombining, false)
  store.getState().toggleIdea('server-combined')
  store.getState().toggleIdea(items[0].id)
  respond = async () => ({ ideas: [{ id: 'server-recombined', title: '재결합 결과' }] })
  await store.getState().combineIdeas()
  assert.deepEqual(requests.at(-1).body.idea_ids, ['server-combined', items[0].id])
  const previousIdeas = store.getState().ideas
  respond = async () => { throw Object.assign(new Error('Network error'), { code: 'ERR_NETWORK' }) }
  await store.getState().generateIdeas({ keyword: '실패', count: 3 })
  assert.equal(store.getState().notice.type, 'error')
  assert.equal(store.getState().ideas, previousIdeas)
  assert.equal(store.getState().isGenerating, false)
  respond = async () => ({ status: 'mock' })
  await store.getState().generateIdeas({ keyword: '잘못된 응답', count: 3 })
  assert.equal(store.getState().notice.type, 'error')
  assert.equal(store.getState().ideas, previousIdeas)
  respond = async () => ({ ideas: items.slice(0, 2) })
  await store.getState().generateIdeas({ keyword: '새 주제', count: 2 })
  assert.equal(store.getState().topic, '새 주제')
  assert.equal(store.getState().ideas.length, 2)
  assert.deepEqual(store.getState().selectedIds, [])
  console.log('PASS: API 경로·요청 본문, 7개 다중 선택·결합, 재결합, 중복 요청 차단, 오류 처리, 더미 대체 없음')
} finally {
  axios.defaults.adapter = originalAdapter
  await server.close()
}
