import { useRef, useState } from 'react'

export default function CardDragHandle({ node, zoom, viewport, moveCard, disabled }) {
  const drag = useRef(null)
  const [dragging, setDragging] = useState(false)

  const endDrag = () => {
    drag.current = null
    setDragging(false)
  }

  return <button
    type="button"
    className={`card-drag-handle ${dragging ? 'dragging' : ''}`}
    aria-label={`${node.title || '중심 주제'} 이동. 드래그하거나 방향키를 누르세요.`}
    disabled={disabled}
    onPointerDown={(event) => {
      if (!event.isPrimary || event.button !== 0) return
      event.preventDefault()
      event.currentTarget.focus({ preventScroll: true })
      event.currentTarget.setPointerCapture(event.pointerId)
      drag.current = { pointerId: event.pointerId, x: node.x, y: node.y, clientX: event.clientX, clientY: event.clientY, scrollLeft: viewport.current.scrollLeft, scrollTop: viewport.current.scrollTop }
      setDragging(true)
    }}
    onPointerMove={(event) => {
      const start = drag.current
      if (!start || event.pointerId !== start.pointerId) return
      moveCard(node.id, {
        x: start.x + (event.clientX - start.clientX + viewport.current.scrollLeft - start.scrollLeft) / zoom,
        y: start.y + (event.clientY - start.clientY + viewport.current.scrollTop - start.scrollTop) / zoom,
      })
    }}
    onPointerUp={endDrag}
    onPointerCancel={endDrag}
    onLostPointerCapture={endDrag}
    onKeyDown={(event) => {
      const delta = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key]
      if (!delta) return
      event.preventDefault()
      const step = event.shiftKey ? 40 : 10
      moveCard(node.id, { x: node.x + delta[0] * step, y: node.y + delta[1] * step })
    }}
  >⠿ 이동</button>
}
