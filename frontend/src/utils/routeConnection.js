// 자유롭게 이동한 카드 사이에서 카드 가장자리의 여백을 따라 경로를 찾음.
export function routeConnection(source, target, nodes, width, height) {
  const direction = target.x + width / 2 >= source.x + width / 2 ? 1 : -1
  const start = { x: source.x + (direction > 0 ? width + 6 : -6), y: source.y + height / 2 }
  const end = { x: target.x + (direction > 0 ? -10 : width + 10), y: target.y + height / 2 }
  const entry = { x: start.x + direction * 18, y: start.y }
  const exit = { x: end.x - direction * 14, y: end.y }
  const cards = [...new Map([source, target, ...nodes].map((node) => [node.id, node])).values()]
  const boxes = cards.map((node) => ({ left: node.x - 16, right: node.x + width + 16, top: node.y - 16, bottom: node.y + height + 16 }))
  const xs = [...new Set([entry.x, exit.x, ...boxes.flatMap((box) => [box.left, box.right])])].sort((a, b) => a - b)
  const ys = [...new Set([entry.y, exit.y, ...boxes.flatMap((box) => [box.top, box.bottom])])].sort((a, b) => a - b)
  const free = (a, b) => boxes.every((box) => a.y === b.y
    ? !(a.y > box.top && a.y < box.bottom && Math.max(a.x, b.x) > box.left && Math.min(a.x, b.x) < box.right)
    : !(a.x > box.left && a.x < box.right && Math.max(a.y, b.y) > box.top && Math.min(a.y, b.y) < box.bottom))
  const first = { ix: xs.indexOf(entry.x), iy: ys.indexOf(entry.y), axis: 0, cost: 0, parent: null }
  const goalX = xs.indexOf(exit.x)
  const goalY = ys.indexOf(exit.y)
  const key = (point) => `${point.ix}:${point.iy}:${point.axis}`
  const heuristic = (point) => Math.abs(xs[point.ix] - exit.x) + Math.abs(ys[point.iy] - exit.y)
  first.priority = heuristic(first)
  const queue = [first]
  const costs = new Map([[key(first), 0]])
  while (queue.length) {
    queue.sort((a, b) => b.priority - a.priority)
    const current = queue.pop()
    if (current.cost !== costs.get(key(current))) continue
    if (current.ix === goalX && current.iy === goalY) {
      const result = [end]
      for (let step = current; step; step = step.parent) result.unshift({ x: xs[step.ix], y: ys[step.iy] })
      return [start, ...result]
    }
    const a = { x: xs[current.ix], y: ys[current.iy] }
    for (const [dx, dy, axis] of [[1, 0, 1], [-1, 0, 1], [0, 1, 2], [0, -1, 2]]) {
      const ix = current.ix + dx
      const iy = current.iy + dy
      if (ix < 0 || iy < 0 || ix >= xs.length || iy >= ys.length) continue
      const b = { x: xs[ix], y: ys[iy] }
      if (!free(a, b)) continue
      const cost = current.cost + Math.abs(b.x - a.x) + Math.abs(b.y - a.y) + (current.axis && current.axis !== axis ? 12 : 0)
      const next = { ix, iy, axis, cost, parent: current }
      if (cost >= (costs.get(key(next)) ?? Infinity)) continue
      costs.set(key(next), cost)
      next.priority = cost + heuristic(next)
      queue.push(next)
    }
  }
  // 사용자가 카드를 포개 놓아 우회할 수 없는 경우에도 연결은 유지.
  return [start, entry, { x: entry.x, y: exit.y }, exit, end]
}
