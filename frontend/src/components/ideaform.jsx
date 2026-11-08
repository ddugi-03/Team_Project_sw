
import { useState } from 'react'
import { useIdeaStore } from '../store/useideastore'

function IdeaForm() {
  const generateIdeas = useIdeaStore((state) => state.generateIdeas)

  const [keyword, setKeyword] = useState('')
  const [count, setCount] = useState(3)
  const [category, setCategory] = useState('전체')
  const [creativity, setCreativity] = useState(70)

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!keyword.trim()) return

    // 입력한 조건 확인
    console.log({
      keyword,
      count,
      category,
      creativity,
    })

    // Dummy 데이터 생성
    generateIdeas(count)
  }

  return (
    <div className="rounded-sm border border-[#ECE8EE] bg-white p-6 shadow-sm sm:p-8">
      <form onSubmit={handleSubmit} className="space-y-6">

        {/* 키워드 입력 */}
        <div>

          <textarea
            id="keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="여기입력"
            rows={3}
            required
            className="w-full resize-none rounded-md border border-[#EAE5EF] bg-[#FAF9FB] p-4 text-sm outline-none focus:border-[#8B76BE]"
          />
        </div>

        {/* 아이디어 개수 및 분야 */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="count"
              className="mb-2 block text-sm font-semibold text-[#50475B]"
            >
              아이디어 개수
            </label>

            <select
              id="count"
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-full rounded-md border border-[#EAE5EF] bg-[#FAF9FB] p-3"
            >
              <option value={1}>1개</option>
              <option value={3}>3개</option>
              <option value={5}>5개</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="category"
              className="mb-2 block text-sm font-semibold text-[#50475B]"
            >
              분야
            </label>

            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-md border border-[#EAE5EF] bg-[#FAF9FB] p-3"
            >
              <option value="전체">전체</option>
              <option value="기술">기술</option>
              <option value="비즈니스">비즈니스</option>
              <option value="교육">교육</option>
              <option value="환경">환경</option>
            </select>
          </div>
        </div>

        {/* 창의성 수준 */}
        <div>
          <div className="mb-3 flex justify-between text-sm">
            <label
              htmlFor="creativity"
              className="font-semibold text-[#50475B]"
            >
              창의성 수준
            </label>

            <span className="font-medium text-[#8B76BE]">
              {creativity}%
            </span>
          </div>

          <input
            id="creativity"
            type="range"
            min="0"
            max="100"
            step="10"
            value={creativity}
            onChange={(e) => setCreativity(Number(e.target.value))}
            className="w-full accent-[#8B76BE]"
          />
        </div>

        {/* 생성 버튼 */}
        <button
          type="submit"
          className="w-full cursor-pointer rounded-2xl bg-[#8B76BE] py-4 font-semibold text-white transition hover:bg-[#7560AA]"
        >
          ✦ 아이디어 생성하기
        </button>

      </form>
    </div>
  )
}

export default IdeaForm
