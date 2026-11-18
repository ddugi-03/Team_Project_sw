import assert from 'node:assert/strict'
import { layoutIdeas, connection, connectionPoints, cardWidth, cardHeight } from '../src/utils/canvasLayout.js'
import { routeConnection } from '../src/utils/routeConnection.js'
import { bezierPoint } from '../src/utils/curveGeometry.js'

function checkRenderedPath(path, cards) {
  const tokens = path.match(/[MLQC]|-?\d*\.?\d+(?:e[-+]?\d+)?/gi)
  let index = 0
  let current
  const point = () => ({ x: Number(tokens[index++]), y: Number(tokens[index++]) })
  while (index < tokens.length) {
    const command = tokens[index++]
    if (command === 'M') { current = point(); continue }
    const start = current
    let first
    let second
    if (command === 'C') { first = point(); second = point() }
    if (command === 'Q') {
      const control = point()
      first = { x: start.x + (control.x - start.x) * 2 / 3, y: start.y + (control.y - start.y) * 2 / 3 }
      second = control
    }
    const end = point()
    if (command === 'Q') second = { x: end.x + (second.x - end.x) * 2 / 3, y: end.y + (second.y - end.y) * 2 / 3 }
    for (let step = 0; step <= 120; step++) {
      const t = step / 120
      const sample = command === 'L' ? { x: start.x + (end.x - start.x) * t, y: start.y + (end.y - start.y) * t } : bezierPoint(start, first, second, end, t)
      for (const card of cards) {
        assert.ok(!(sample.x > card.x && sample.x < card.x + cardWidth && sample.y > card.y && sample.y < card.y + cardHeight), `곡선이 ${card.id} 카드를 관통함`)
      }
    }
    current = end
  }
}

const initial = Array.from({ length: 7 }, (_, index) => ({ id: `idea-${index}` }))
const ideas = [
  ...initial,
  { id: 'ab', parentIds: ['idea-0', 'idea-1'] },
  { id: 'cd', parentIds: ['idea-2', 'idea-3'] },
  { id: 'again', parentIds: ['ab', 'idea-6'] },
  { id: 'final', parentIds: ['again', 'cd', 'idea-0'] },
]
for (const input of [[], initial.slice(0, 1), initial, ideas, [...ideas].reverse()]) {
  const layout = layoutIdeas(input)
  const nodes = [layout.center, ...layout.nodes]
  const byId = new Map(nodes.map((node) => [node.id, node]))
  for (const [index, node] of nodes.entries()) {
    assert.ok(node.x >= 0 && node.y >= 0)
    assert.ok(node.x + cardWidth <= layout.boardWidth)
    assert.ok(node.y + cardHeight <= layout.boardHeight)
    for (const other of nodes.slice(index + 1)) {
      assert.ok(node.x + cardWidth <= other.x || other.x + cardWidth <= node.x || node.y + cardHeight <= other.y || other.y + cardHeight <= node.y, `${node.id} / ${other.id}: 카드 겹침`)
    }
    if (node.id === 'topic') continue
    for (const id of node.parentIds || ['topic']) {
      const parent = byId.get(id)
      assert.ok(parent.x + cardWidth < node.x, '자식은 부모 오른쪽에 배치')
      const path = connection(parent, node, layout.nodes)
      assert.ok(!/NaN|Infinity/.test(path))
      checkRenderedPath(path, nodes)
      if (node.level - parent.level > 1) {
        assert.ok(path.includes(' C ') || path.includes(' Q '))
        const points = connectionPoints(parent, node, layout.nodes)
        for (let index = 1; index < points.length; index++) {
          const a = points[index - 1]
          const b = points[index]
          assert.ok(a.x === b.x || a.y === b.y)
          assert.ok(a.x >= 0 && a.y >= 0 && b.x <= layout.boardWidth && b.y <= layout.boardHeight)
          for (const card of nodes) {
            const crosses = a.y === b.y
              ? a.y > card.y && a.y < card.y + cardHeight && Math.max(a.x, b.x) > card.x && Math.min(a.x, b.x) < card.x + cardWidth
              : a.x > card.x && a.x < card.x + cardWidth && Math.max(a.y, b.y) > card.y && Math.min(a.y, b.y) < card.y + cardHeight
            assert.equal(crosses, false, `${parent.id} → ${node.id}: ${card.id} 관통`)
          }
        }
      } else {
        assert.ok(path.includes(' C '))
      }
    }
  }
}
assert.deepEqual(ideas.slice(0, 7), initial)
const source = { id: 'source', x: 48, y: 400, level: 1 }
const obstacle = { id: 'obstacle', x: 404, y: 400, level: 2 }
const target = { id: 'target', x: 760, y: 400, level: 3 }
const route = connectionPoints(source, target, [source, obstacle, target])
assert.ok(Math.min(...route.map((point) => point.y)) >= obstacle.y - 20)
assert.ok(Math.max(...route.map((point) => point.y)) <= obstacle.y + cardHeight + 20)
assert.ok(connection(source, target, [source, obstacle, target]).includes(' Q '))
checkRenderedPath(connection(source, target, [source, obstacle, target]), [source, obstacle, target])
const automatic = layoutIdeas(ideas)
const moved = layoutIdeas(ideas, { 'idea-0': { x: 1900, y: 1400 }, topic: { x: 80, y: 160 } })
assert.equal(moved.nodes[0].x, 1900)
assert.equal(moved.nodes[0].y, 1400)
assert.equal(moved.center.x, 80)
assert.ok(moved.boardWidth >= 1900 + cardWidth)
for (let index = 1; index < moved.nodes.length; index++) {
  assert.equal(moved.nodes[index].x, automatic.nodes[index].x)
  assert.equal(moved.nodes[index].y, automatic.nodes[index].y)
}
for (const [from, to] of [[source, target], [target, source], [{ ...source, y: 60 }, { ...target, x: 48, y: 900 }]]) {
  const cards = [from, to, obstacle]
  const route = routeConnection(from, to, cards, cardWidth, cardHeight)
  const rendered = connection({ ...from, manualPosition: true }, to, cards)
  assert.ok(!/NaN|Infinity/.test(rendered))
  checkRenderedPath(rendered, cards)
  for (let index = 1; index < route.length; index++) {
    const a = route[index - 1]
    const b = route[index]
    assert.ok(a.x === b.x || a.y === b.y)
    for (const card of cards) {
      const crosses = a.y === b.y
        ? a.y > card.y && a.y < card.y + cardHeight && Math.max(a.x, b.x) > card.x && Math.min(a.x, b.x) < card.x + cardWidth
        : a.x > card.x && a.x < card.x + cardWidth && Math.max(a.y, b.y) > card.y && Math.min(a.y, b.y) < card.y + cardHeight
      assert.equal(crosses, false, '드래그 후 연결이 카드를 관통하지 않아야 함')
    }
  }
}
console.log('PASS: 단계 배치, 카드 겹침 없음, 경계, 역순 입력, 가까운 여백 우회, 카드 관통 없음, 둥근 모서리')
