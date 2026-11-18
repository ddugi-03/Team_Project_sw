export const minZoom = 0.1
export const maxZoom = 1.5

export const clampZoom = (value) => Math.min(maxZoom, Math.max(minZoom, Math.round(value * 1000) / 1000))

// 전체 보기는 수동 배율 하한과 반올림을 적용하지 않아 큰 보드도 화면 안에 들어갑니다.
export const fitZoom = (width, height, boardWidth, boardHeight) => Math.min(
  Math.max(1, width - 24) / boardWidth,
  Math.max(1, height - 24) / boardHeight,
  1,
)

export function zoomScroll(scrollLeft, scrollTop, width, height, oldZoom, newZoom, centered = false) {
  const offsetX = centered ? 0 : width / 2
  const offsetY = centered ? 0 : height / 2
  return {
    left: Math.max(0, (scrollLeft + offsetX) / oldZoom * newZoom - offsetX),
    top: Math.max(0, (scrollTop + offsetY) / oldZoom * newZoom - offsetY),
  }
}
