export function bezierPoint(a, b, c, d, t) {
  const u = 1 - t
  return {
    x: u ** 3 * a.x + 3 * u ** 2 * t * b.x + 3 * u * t ** 2 * c.x + t ** 3 * d.x,
    y: u ** 3 * a.y + 3 * u ** 2 * t * b.y + 3 * u * t ** 2 * c.y + t ** 3 * d.y,
  }
}

function segmentHitsCard(a, b, node, width, height) {
  const box = { left: node.x - 3, right: node.x + width + 3, top: node.y - 3, bottom: node.y + height + 3 }
  let low = 0
  let high = 1
  for (const [origin, delta, minimum, maximum] of [[a.x, b.x - a.x, box.left, box.right], [a.y, b.y - a.y, box.top, box.bottom]]) {
    if (Math.abs(delta) < 0.000001) {
      if (origin <= minimum || origin >= maximum) return false
      continue
    }
    const first = (minimum - origin) / delta
    const last = (maximum - origin) / delta
    low = Math.max(low, Math.min(first, last))
    high = Math.min(high, Math.max(first, last))
    if (low >= high) return false
  }
  return low < high
}

export function clearCurve(a, b, c, d, nodes, width, height) {
  let previous = a
  for (let index = 1; index <= 64; index++) {
    const next = bezierPoint(a, b, c, d, index / 64)
    if (nodes.some((node) => segmentHitsCard(previous, next, node, width, height))) return false
    previous = next
  }
  return true
}
