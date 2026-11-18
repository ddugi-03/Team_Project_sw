import assert from 'node:assert/strict'
import { clampZoom, fitZoom, zoomScroll } from '../src/utils/canvasZoom.js'

assert.equal(clampZoom(-1), 0.1)
assert.equal(clampZoom(2), 1.5)
assert.equal(clampZoom(0.7 - 0.1), 0.6)
for (const [width, height, boardWidth, boardHeight] of [[800, 600, 1800, 1400], [320, 400, 1100, 600], [1000, 700, 1100, 3000], [800, 600, 1100, 10000], [320, 400, 1000000, 1000000]]) {
  const zoom = fitZoom(width, height, boardWidth, boardHeight)
  assert.ok(boardWidth * zoom <= width)
  assert.ok(boardHeight * zoom <= height)
}
assert.ok(fitZoom(800, 600, 1100, 10000) < 0.1)
assert.equal(fitZoom(2000, 2000, 1100, 600), 1)
const position = zoomScroll(500, 400, 800, 600, 1, 0.8)
assert.equal((position.left + 400) / 0.8, 900)
assert.equal((position.top + 300) / 0.8, 700)
assert.deepEqual(zoomScroll(0, 0, 800, 600, 1, 0.1), { left: 0, top: 0 })
// 화면 절반 크기의 양쪽 여백을 두면 작은 배율에서도 중심 좌표가 유지됩니다.
const centered = zoomScroll(400, 300, 800, 600, 1, 0.3, true)
assert.equal(centered.left / 0.3, 400)
assert.equal(centered.top / 0.3, 300)
const restored = zoomScroll(centered.left, centered.top, 800, 600, 0.3, 1, true)
assert.deepEqual(restored, { left: 400, top: 300 })
console.log('PASS: 배율 제한, 단계 변경, 전체 보기 크기, 확대·축소 시 중심 유지')
