import assert from 'node:assert/strict'
import axios from 'axios'
import { createServer } from 'vite'

const original = axios.defaults.adapter
let request
axios.defaults.adapter = async (config) => {
  request = JSON.parse(config.data)
  return { data: { ideas: [] }, status: 200, statusText: 'OK', headers: {}, config }
}
const server = await createServer({
  define: { 'import.meta.env.VITE_DEMO_MODE': JSON.stringify('true') },
  server: { middlewareMode: true, ws: false, watch: null }, appType: 'custom',
})
try {
  const { requestCombination } = await server.ssrLoadModule('/src/services/api.js')
  const cards = ['a', 'b'].map((id) => ({ id, title: id, description: '설명', tags: [] }))
  await requestCombination(cards)
  assert.equal(request.count, 1)
  assert.deepEqual(request.selected_ideas.map((idea) => idea.id), ['a', 'b'])
  console.log('PASS: 발표 모드에서 두 카드 전체 내용과 결합 결과 1개 요청')
} finally {
  axios.defaults.adapter = original
  await server.close()
}
