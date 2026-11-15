import { useEffect, useRef } from 'react'
import IdeaCard from './ideacard'
import { useIdeaStore } from '../store/useideastore'

const width = 228
const height = 208
const center = { id: 'topic', x: 436, y: 326 }
const positions = [{ x: 64, y: 92 }, { x: 436, y: 36 }, { x: 808, y: 92 }, { x: 64, y: 526 }, { x: 808, y: 526 }]

function connection(source, target) {
  const dx = target.x - source.x
  const dy = target.y - source.y
  const ratio = Math.max(Math.abs(dx) / (width / 2 + 10), Math.abs(dy) / (height / 2 + 10))
  const offsetX = dx / ratio
  const offsetY = dy / ratio
  return `M ${source.x + width / 2 + offsetX} ${source.y + height / 2 + offsetY} L ${target.x + width / 2 - offsetX} ${target.y + height / 2 - offsetY}`
}

function MindMap() {
  const ideas = useIdeaStore((state) => state.ideas)
  const topic = useIdeaStore((state) => state.topic)
  const selectedIds = useIdeaStore((state) => state.selectedIds)
  const combineIdeas = useIdeaStore((state) => state.combineIdeas)
  const clearSelection = useIdeaStore((state) => state.clearSelection)
  const busy = useIdeaStore((state) => state.isGenerating || state.isCombining)
  const viewport = useRef(null)
  const previousCount = useRef(ideas.length)
  let baseIndex = 0
  let combinedIndex = 0
  const nodes = ideas.map((idea) => {
    const position = idea.parentIds || baseIndex >= positions.length
      ? { x: 64 + (combinedIndex % 3) * 372, y: 842 + Math.floor(combinedIndex++ / 3) * 330 }
      : positions[baseIndex++]
    return { ...idea, ...position }
  })
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const edges = nodes.flatMap((node) => (node.parentIds || ['topic']).map((id) => ({
    source: id === 'topic' ? center : byId.get(id), target: node,
  }))).filter((edge) => edge.source)
  const boardHeight = Math.max(800, ...nodes.map((node) => node.y + height + 60))

  useEffect(() => {
    if (ideas.length > previousCount.current) {
      const last = ideas[ideas.length - 1]
      if (last?.parentIds) {
        Array.from(viewport.current?.querySelectorAll('[data-idea-id]') || []).find((node) => node.dataset.ideaId === last.id)?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
      }
    }
    previousCount.current = ideas.length
  }, [ideas])

  const handleCombine = async () => { await combineIdeas() }

  return (
    <section className="map-panel" aria-label="아이디어 마인드맵">
      <div className="map-heading">
        <div><span className="document-label">아이디어 노트</span><h2>마인드맵 <span>{ideas.length}</span></h2></div>
        <p>아이디어 보드</p>
      </div>
      <div className="map-instructions"><span>결합할 카드를 두 개 이상 선택하세요.</span><span>선택 {selectedIds.length}개</span></div>
      <div className="map-viewport" ref={viewport} tabIndex={0} aria-label="마인드맵 보드. 가로와 세로로 스크롤할 수 있습니다.">
        {ideas.length === 0 ? <div className="empty-state">주제를 입력하면 아이디어가 여기에 표시됩니다.</div> : (
          <div className="map-canvas" style={{ height: boardHeight }}>
            <svg className="map-connections" width="1100" height={boardHeight} aria-hidden="true">
              <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="currentColor" strokeWidth="1.5" /></marker></defs>
              {edges.map(({ source, target }) => <path key={`${source.id}-${target.id}`} d={connection(source, target)} className={target.parentIds ? 'combined-line' : ''} markerEnd="url(#arrow)" />)}
            </svg>
            <div className="topic-card" style={{ left: center.x, top: center.y }}><span>중심 주제</span><h3>{topic}</h3><div className="topic-rule" /></div>
            {nodes.map((idea, index) => <div className="map-node" key={idea.id} data-idea-id={idea.id} style={{ left: idea.x, top: idea.y }}><IdeaCard idea={idea} index={index} /></div>)}
          </div>
        )}
      </div>
      <div className="map-toolbar">
        <div className="selected-titles">{selectedIds.length ? selectedIds.map((id) => byId.get(id)?.title).join(' + ') : '선택한 카드가 없습니다.'}</div>
        <div className="map-actions"><button className="text-button" type="button" disabled={!selectedIds.length || busy} onClick={clearSelection}>선택 해제</button><button className="primary-button" type="button" disabled={selectedIds.length < 2 || busy} onClick={handleCombine}>{busy ? '처리 중...' : '선택한 아이디어 결합'}</button></div>
      </div>
    </section>
  )
}

export default MindMap
