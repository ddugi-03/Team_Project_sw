import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import IdeaCard from './ideacard'
import CardDragHandle from './carddraghandle'
import { useIdeaStore } from '../store/useideastore'
import { layoutIdeas, connection } from '../utils/canvasLayout'
import { clampZoom, fitZoom, zoomScroll, minZoom, maxZoom } from '../utils/canvasZoom'

function MindMap() {
  const ideas = useIdeaStore((state) => state.ideas)
  const topic = useIdeaStore((state) => state.topic)
  const selectedIds = useIdeaStore((state) => state.selectedIds)
  const combineIdeas = useIdeaStore((state) => state.combineIdeas)
  const clearSelection = useIdeaStore((state) => state.clearSelection)
  const isGenerating = useIdeaStore((state) => state.isGenerating)
  const isCombining = useIdeaStore((state) => state.isCombining)
  const busy = isGenerating || isCombining
  const positions = useIdeaStore((state) => state.positions)
  const moveCard = useIdeaStore((state) => state.moveCard)
  const resetPositions = useIdeaStore((state) => state.resetPositions)
  const viewport = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 })
  const pendingScroll = useRef(null)
  const previousIdeas = useRef(ideas)
  const { nodes, center, boardWidth, boardHeight } = layoutIdeas(ideas, positions)
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const edges = nodes.flatMap((node) => (node.parentIds || ['topic']).map((id) => ({
    source: id === 'topic' ? center : byId.get(id), target: node,
  }))).filter((edge) => edge.source)

  const changeZoom = (value, fit = false) => {
    const board = viewport.current
    const nextZoom = fit ? value : clampZoom(value)
    if (!board) return
    const position = fit ? { left: boardWidth * nextZoom / 2, top: boardHeight * nextZoom / 2 } : zoomScroll(board.scrollLeft, board.scrollTop, board.clientWidth, board.clientHeight, zoom, nextZoom, true)
    if (nextZoom === zoom) {
      board.scrollTo({ ...position, behavior: 'instant' })
      return
    }
    pendingScroll.current = position
    setZoom(nextZoom)
  }

  useLayoutEffect(() => {
    const board = viewport.current
    const observer = new ResizeObserver(() => {
      setViewportSize((previous) => previous.width === board.clientWidth && previous.height === board.clientHeight ? previous : { width: board.clientWidth, height: board.clientHeight })
    })
    observer.observe(board)
    return () => observer.disconnect()
  }, [])

  useLayoutEffect(() => {
    if (!pendingScroll.current || !viewport.current) return
    viewport.current.scrollTo({ ...pendingScroll.current, behavior: 'instant' })
    pendingScroll.current = null
  }, [zoom])

  useEffect(() => {
    if (isGenerating || ideas === previousIdeas.current || !viewport.current) return
    const board = viewport.current
    const last = ideas.at(-1)
    const element = Array.from(board.querySelectorAll('[data-idea-id]')).find((node) => node.dataset.ideaId === last?.id)
    if (last?.parentIds && element) {
      board.scrollTo({
        left: (element.offsetLeft + element.offsetWidth / 2) * zoom,
        top: (element.offsetTop + element.offsetHeight / 2) * zoom,
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
      })
    } else {
      board.scrollTo({ left: board.clientWidth / 2, top: board.clientHeight / 2, behavior: 'instant' })
    }
    previousIdeas.current = ideas
  }, [ideas, isGenerating, zoom])

  const handleCombine = async () => { await combineIdeas() }

  return (
    <section className="map-panel" aria-label="AI Brainstorming Canvas">
      <div className="map-heading">
        <div><h2>AI Brainstorming Canvas <span>{ideas.length}</span></h2></div>
        <p>아이디어 보드</p>
      </div>
      <div className="map-instructions"><span>카드를 선택해 결합하거나, ‘이동’을 드래그해 배치하세요.</span><span>선택 {selectedIds.length}개</span></div>
      <div className="zoom-controls" role="group" aria-label="캔버스 배율 조절">
        <button type="button" aria-label="캔버스 축소" disabled={busy || !ideas.length || zoom <= minZoom} onClick={() => changeZoom(zoom - 0.1)}>−</button>
        <output aria-live="polite" aria-label="현재 배율">{Math.round(zoom * 100)}%</output>
        <button type="button" aria-label="캔버스 확대" disabled={busy || !ideas.length || zoom >= maxZoom} onClick={() => changeZoom(zoom + 0.1)}>+</button>
        <button type="button" disabled={busy || !ideas.length} onClick={() => changeZoom(1)}>100%</button>
        <button type="button" disabled={busy || !ideas.length} onClick={() => {
          const board = viewport.current
          if (board) changeZoom(fitZoom(board.clientWidth, board.clientHeight, boardWidth, boardHeight), true)
        }}>전체 보기</button>
        <button type="button" disabled={busy || !Object.keys(positions).length} onClick={resetPositions}>자동 배치</button>
      </div>
      <div className="request-status" role="status" aria-live="polite">
        {busy && <><span className="spinner" aria-hidden="true" /><span>{isGenerating ? '아이디어를 생성하고 있습니다.' : '선택한 아이디어를 결합하고 있습니다.'} AI 응답에 시간이 걸릴 수 있습니다.</span></>}
      </div>
      <div className="map-viewport" ref={viewport} style={{ '--grid-spacing': `${24 * zoom}px` }} tabIndex={0} aria-busy={busy} aria-label="마인드맵 보드. 가로와 세로로 스크롤할 수 있습니다.">
        {isGenerating ? <div className="loading-board" aria-hidden="true">{Array.from({ length: 3 }, (_, index) => <div className="skeleton-card" key={index}><span /><span /><span /><span /></div>)}</div> : ideas.length === 0 ? <div className="empty-state">주제를 입력하면 아이디어가 여기에 표시됩니다.</div> : (
          <div className="map-scaled-area" style={{ width: boardWidth * zoom + viewportSize.width, height: boardHeight * zoom + viewportSize.height, backgroundPosition: `${viewportSize.width / 2}px ${viewportSize.height / 2}px` }}>
          <div className="map-canvas" style={{ left: viewportSize.width / 2, top: viewportSize.height / 2, width: boardWidth, height: boardHeight, transform: `scale(${zoom})` }}>
            <svg className="map-connections" width={boardWidth} height={boardHeight} aria-hidden="true">
              <defs>{['base', 'combined'].map((kind) => <marker key={kind} id={`arrow-${kind}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path className={`arrow-${kind}`} d="M 1 1 L 9 5 L 1 9" fill="none" strokeWidth="1.5" /></marker>)}</defs>
              {edges.map(({ source, target }) => <path key={`${source.id}-${target.id}`} d={connection(source, target, nodes)} className={target.parentIds ? 'combined-line' : ''} markerEnd={`url(#arrow-${target.parentIds ? 'combined' : 'base'})`} />)}
            </svg>
            <div className="topic-card" style={{ left: center.x, top: center.y }}><CardDragHandle node={center} zoom={zoom} viewport={viewport} moveCard={moveCard} disabled={busy} /><span>중심 주제</span><h3>{topic}</h3><div className="topic-rule" /></div>
            {nodes.map((idea, index) => <div className="map-node" key={idea.id} data-idea-id={idea.id} style={{ left: idea.x, top: idea.y }}><CardDragHandle node={idea} zoom={zoom} viewport={viewport} moveCard={moveCard} disabled={busy} /><IdeaCard idea={idea} index={index} /></div>)}
          </div>
          </div>
        )}
      </div>
      <div className="map-toolbar">
        <div className="selected-titles">{selectedIds.length ? selectedIds.map((id) => byId.get(id)?.title).join(' + ') : '선택한 카드가 없습니다.'}</div>
        <div className="map-actions"><button className="text-button" type="button" disabled={!selectedIds.length || busy} onClick={clearSelection}>선택 해제</button><button className="primary-button" type="button" disabled={selectedIds.length < 2 || busy} onClick={handleCombine}>{isCombining ? <><span className="spinner" aria-hidden="true" /> 결합 중...</> : '선택한 아이디어 결합'}</button></div>
      </div>
    </section>
  )
}

export default MindMap
