
import { useIdeaStore } from '../store/useideastore'

// 카드 배경색
const colors = {
  yellow: 'bg-[#FFF0C7]',
  purple: 'bg-[#E9E2FF]',
  green: 'bg-[#DFF2E6]',
  pink: 'bg-[#FBE2E9]',
  blue: 'bg-[#DFECFF]',
}

function IdeaCard({ idea, index }) {
  const selectedIds = useIdeaStore((state) => state.selectedIds)
  const toggleIdea = useIdeaStore((state) => state.toggleIdea)

  const isSelected = selectedIds.includes(idea.id)

  return (
    <label
      className={`
        block cursor-pointer rounded-2xl p-6
        transition duration-200 hover:-translate-y-1 hover:shadow-lg
        ${colors[idea.color] || colors.yellow}
        ${isSelected ? 'ring-2 ring-[#8B76BE]' : ''}
      `}
    >
      <div className="mb-5 flex items-center justify-between">
        <span className="text-xs font-semibold tracking-wider text-[#80768B]">
          IDEA {String(index + 1).padStart(2, '0')}
        </span>

        {/* 선택 체크박스 */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleIdea(idea.id)}
          aria-label={`${idea.title} 선택`}
          className="h-5 w-5 accent-[#8B76BE]"
        />
      </div>

      {/* 아이디어 제목 */}
      <h3 className="mb-3 text-lg font-bold text-[#37313D]">
        {idea.title}
      </h3>

      {/* 아이디어 설명 */}
      <p className="mb-5 text-sm leading-relaxed text-[#77717A]">
        {idea.description}
      </p>

      {/* 아이디어 태그 */}
      <div className="flex flex-wrap gap-2">
        {idea.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-white/60 px-3 py-1 text-xs text-[#80768B]"
          >
            #{tag}
          </span>
        ))}
      </div>
    </label>
  )
}

export default IdeaCard
