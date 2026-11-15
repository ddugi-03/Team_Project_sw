import { useIdeaStore } from '../store/useideastore'

function IdeaCard({ idea, index }) {
  const selectedIds = useIdeaStore((state) => state.selectedIds)
  const toggleIdea = useIdeaStore((state) => state.toggleIdea)
  const busy = useIdeaStore((state) => state.isGenerating || state.isCombining)
  const selected = selectedIds.includes(idea.id)

  return (
    <button
      type="button"
      className={`idea-card ${selected ? 'selected' : ''} ${idea.parentIds ? 'combined-card' : ''}`}
      aria-pressed={selected}
      onClick={() => toggleIdea(idea.id)}
      disabled={busy}
    >
      <span className="idea-card-top">
        <span>{idea.parentIds ? '결합' : `아이디어 ${String(index + 1).padStart(2, '0')}`}</span>
        <span className="card-check" aria-hidden="true">{selected ? '✓' : '+'}</span>
      </span>
      <strong className="card-title">{idea.title}</strong>
      <span className="card-description">{idea.description}</span>
      <span className="tags">{idea.tags.map((tag) => <span key={tag}>{tag}</span>)}</span>
    </button>
  )
}

export default IdeaCard
