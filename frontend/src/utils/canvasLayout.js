import { routeConnection } from './routeConnection.js'
import { clearCurve } from './curveGeometry.js'

export const cardWidth = 228
export const cardHeight = 208
const padding = 48
const top = 96
const columnGap = 128
const rowGap = 64

export function layoutIdeas(ideas, positions = {}) {
  const byId = new Map(ideas.map((idea) => [idea.id, idea]))
  const depths = new Map()
  function depth(idea, visiting = new Set()) {
    if (depths.has(idea.id)) return depths.get(idea.id)
    if (visiting.has(idea.id)) return 1
    const next = new Set([...visiting, idea.id])
    const parents = (idea.parentIds || []).map((id) => byId.get(id)).filter(Boolean)
    const level = parents.length ? 1 + Math.max(...parents.map((parent) => depth(parent, next))) : 1
    depths.set(idea.id, level)
    return level
  }
  const columns = new Map()
  ideas.forEach((idea) => {
    const level = depth(idea)
    if (!columns.has(level)) columns.set(level, [])
    columns.get(level).push(idea)
  })
  const placed = new Map()
  for (const [level, column] of [...columns].sort(([a], [b]) => a - b)) {
    const desiredY = (idea) => {
      const parents = (idea.parentIds || []).map((id) => placed.get(id)).filter(Boolean)
      return parents.length ? parents.reduce((sum, parent) => sum + parent.y, 0) / parents.length : top
    }
    let nextY = top
    column.sort((a, b) => desiredY(a) - desiredY(b)).forEach((idea) => {
      const y = Math.max(nextY, desiredY(idea))
      placed.set(idea.id, { ...idea, level, x: padding + level * (cardWidth + columnGap), y })
      nextY = y + cardHeight + rowGap
    })
  }
  const nodes = ideas.map((idea) => ({ ...placed.get(idea.id), ...positions[idea.id], manualPosition: Boolean(positions[idea.id]) }))
  const initial = [...placed.values()].filter((node) => node.level === 1)
  const center = {
    id: 'topic', level: 0, x: padding,
    y: initial.length ? Math.min(top + cardHeight + rowGap, (initial[0].y + initial.at(-1).y) / 2) : top,
    ...positions.topic,
    manualPosition: Boolean(positions.topic),
  }
  return {
    nodes, center,
    boardWidth: Math.max(1100, ...[center, ...nodes].map((node) => node.x + cardWidth + padding)),
    boardHeight: Math.max(600, ...[center, ...nodes].map((node) => node.y + cardHeight + padding)),
  }
}

export function connectionPoints(source, target, nodes) {
  const start = { x: source.x + cardWidth + 6, y: source.y + cardHeight / 2 }
  const end = { x: target.x - 10, y: target.y + cardHeight / 2 }
  const columns = new Map()
  nodes.filter((node) => node.x > source.x && node.x < target.x).forEach((node) => {
    if (!columns.has(node.x)) columns.set(node.x, [])
    columns.get(node.x).push(node)
  })
  const ordered = [...columns].sort(([a], [b]) => a - b)
  const clearance = 20
  const lanes = [...new Set([start.y, end.y, ...ordered.flatMap(([, cards]) => cards.flatMap((card) => [card.y - clearance, card.y + cardHeight + clearance]))])]
  let previous = [{ y: start.y, cost: 0, parent: null }]
  for (const [, cards] of ordered) {
    previous = lanes.filter((y) => cards.every((card) => y <= card.y - clearance || y >= card.y + cardHeight + clearance)).map((y) => {
      const choices = previous.map((entry) => ({ entry, cost: entry.cost + Math.abs(entry.y - y) + (entry.y === y ? 0 : 16) }))
      const best = choices.reduce((a, b) => a.cost <= b.cost ? a : b)
      return { y, cost: best.cost, parent: best.entry }
    })
  }
  let best = previous.reduce((a, b) => a.cost + Math.abs(a.y - end.y) <= b.cost + Math.abs(b.y - end.y) ? a : b)
  const chosen = []
  while (best.parent) {
    chosen.unshift(best.y)
    best = best.parent
  }
  const points = [start]
  let currentY = start.y
  let previousRight = source.x + cardWidth
  ordered.forEach(([x], index) => {
    const gutter = (previousRight + x) / 2
    points.push({ x: gutter, y: currentY }, { x: gutter, y: chosen[index] })
    currentY = chosen[index]
    previousRight = x + cardWidth
  })
  const gutter = (previousRight + target.x) / 2
  points.push({ x: gutter, y: currentY }, { x: gutter, y: end.y }, end)
  return points
}

function roundedPath(points, nodes = []) {
  const clean = []
  for (const point of points) {
    if (clean.at(-1)?.x === point.x && clean.at(-1)?.y === point.y) continue
    while (clean.length > 1) {
      const a = clean.at(-2)
      const b = clean.at(-1)
      if ((a.x === b.x && b.x === point.x) || (a.y === b.y && b.y === point.y)) clean.pop()
      else break
    }
    if (clean.at(-1)?.x !== point.x || clean.at(-1)?.y !== point.y) clean.push(point)
  }
  let path = `M ${clean[0].x} ${clean[0].y}`
  for (let index = 1; index < clean.length - 1; index++) {
    const a = clean[index - 1]
    const b = clean[index]
    const c = clean[index + 1]
    const before = Math.hypot(b.x - a.x, b.y - a.y)
    const after = Math.hypot(c.x - b.x, c.y - b.y)
    let radius = Math.min(80, before / 2, after / 2)
    let entry
    let exit
    while (true) {
      entry = { x: b.x - (b.x - a.x) / before * radius, y: b.y - (b.y - a.y) / before * radius }
      exit = { x: b.x + (c.x - b.x) / after * radius, y: b.y + (c.y - b.y) / after * radius }
      // 각 모서리를 크게 둥글리되, 카드 가까이에서는 곡률을 줄입니다.
      const control1 = { x: entry.x + (b.x - entry.x) * 2 / 3, y: entry.y + (b.y - entry.y) * 2 / 3 }
      const control2 = { x: exit.x + (b.x - exit.x) * 2 / 3, y: exit.y + (b.y - exit.y) * 2 / 3 }
      if (radius <= 8 || clearCurve(entry, control1, control2, exit, nodes, cardWidth, cardHeight)) break
      radius /= 2
    }
    path += ` L ${entry.x} ${entry.y} Q ${b.x} ${b.y} ${exit.x} ${exit.y}`
  }
  return `${path} L ${clean.at(-1).x} ${clean.at(-1).y}`
}

export function connection(source, target, nodes = []) {
  const cards = [...new Map([source, target, ...nodes].map((node) => [node.id, node])).values()]
  const direction = target.x >= source.x ? 1 : -1
  const start = { x: source.x + (direction > 0 ? cardWidth + 6 : -6), y: source.y + cardHeight / 2 }
  const end = { x: target.x + (direction > 0 ? -10 : cardWidth + 10), y: target.y + cardHeight / 2 }
  const bend = Math.min(220, Math.max(48, Math.abs(end.x - start.x) / 2))
  const first = { x: start.x + direction * bend, y: start.y }
  const second = { x: end.x - direction * bend, y: end.y }
  if (clearCurve(start, first, second, end, cards, cardWidth, cardHeight)) {
    return `M ${start.x} ${start.y} C ${first.x} ${first.y}, ${second.x} ${second.y}, ${end.x} ${end.y}`
  }
  if (source.manualPosition || target.manualPosition || nodes.some((node) => node.manualPosition)) {
    return roundedPath(routeConnection(source, target, nodes, cardWidth, cardHeight), cards)
  }
  const startX = source.x + cardWidth + 6
  const endX = target.x - 10
  const startY = source.y + cardHeight / 2
  const endY = target.y + cardHeight / 2
  // 중간 열마다 가까운 카드 사이 여백을 찾아 짧게 우회.
  if (target.level - source.level > 1) {
    return roundedPath(connectionPoints(source, target, nodes), cards)
  }
  const middleX = (startX + endX) / 2
  return `M ${startX} ${startY} C ${middleX} ${startY}, ${middleX} ${endY}, ${endX} ${endY}`
}
