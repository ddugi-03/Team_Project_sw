import { useState } from 'react'
import { useIdeaStore } from '../store/useideastore'

function IdeaForm() {
  const generateIdeas = useIdeaStore((state) => state.generateIdeas)
  const isGenerating = useIdeaStore((state) => state.isGenerating)
  const isCombining = useIdeaStore((state) => state.isCombining)
  const busy = isGenerating || isCombining
  const [keyword, setKeyword] = useState('')
  const [count, setCount] = useState(3)
  const [category, setCategory] = useState('일반')

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!keyword.trim() || !Number.isInteger(count) || count < 1 || count > 10 || busy) return
    await generateIdeas({ keyword: keyword.trim(), category, count })
  }

  return (
    <section className="composer">
      <h2>새 주제</h2>
      <form onSubmit={handleSubmit}>
        <fieldset disabled={busy}>
        <label htmlFor="keyword" className="field-label">주제 또는 키워드</label>
        <textarea id="keyword" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="예: 대학생을 위한 친환경 캠퍼스 서비스" rows="3" maxLength={500} required />
        <div className="form-grid">
          <label>생성 개수
            <input type="number" min="1" max="10" step="1" required value={count} onChange={(event) => setCount(event.target.value === '' ? '' : Number(event.target.value))} />
          </label>
          <label>분야
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="일반">전체 분야</option><option value="기술">기술</option><option value="비즈니스">비즈니스</option><option value="교육">교육</option><option value="환경">환경</option>
            </select>
          </label>
        </div>
        <button className="primary-button generate-button" type="submit" disabled={busy || !keyword.trim()}>
          {isGenerating ? <><span className="spinner" aria-hidden="true" /> 생성 중...</> : '아이디어 생성'}
        </button>
        </fieldset>
      </form>
    </section>
  )
}
export default IdeaForm
