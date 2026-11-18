export const minZoom = 0.1
export const maxZoom = 1.5

export const clampZoom = (value) => Math.min(maxZoom, Math.max(minZoom, Math.round(value * 1000) / 1000))

export const fitZoom = (width, height, boardWidth, boardHeight) => clampZoom(Math.min(
  Math.max(1, width - 24) / boardWidth,
  Math.max(1, height - 24) / boardHeight,
  1,
))

export function zoomScroll(scrollLeft, scrollTop, width, height, oldZoom, newZoom, centered = false) {
  const offsetX = centered ? 0 : width / 2
  const offsetY = centered ? 0 : height / 2
  return {
    left: Math.max(0, (scrollLeft + offsetX) / oldZoom * newZoom - offsetX),
    top: Math.max(0, (scrollTop + offsetY) / oldZoom * newZoom - offsetY),
  }
}
