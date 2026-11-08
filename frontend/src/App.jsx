
import IdeaForm from './components/ideaform'
import IdeaCard from './components/ideacard'
import { useIdeaStore } from './store/useideastore'

function App() {
  const ideas = useIdeaStore((state) => state.ideas)
  const selectedIds = useIdeaStore((state) => state.selectedIds)

  return (
    <div className="min-h-screen bg-[#F8F7F4]">

      {/* 헤더 */}
      <header className="border-b border-[#E6E0E9] bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">

          <h1 className="text-xl font-extrabold text-[#302C39]">
            <span className="mr-2 text-[#8B76BE]">✳</span>
            서비스 이름
          </h1>

          {/*<span className="hidden text-sm text-[#9C93A9] sm:block">
            Creative Space ✦
          </span>*/}

        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">

        {/* 조건 입력 폼 */}
        <div className="mx-auto max-w-2xl">
          <IdeaForm />
        </div>

        {/* 생성된 아이디어 영역 */}
        <section className="mt-14">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-bold text-[#35303F]">
              생성된 아이디어
            </h2>

            <span className="rounded-full bg-[#EEE8F8] px-4 py-2 text-xs font-semibold text-[#8B76BE]">
              {ideas.length} Ideas
            </span>
          </div>

          {ideas.length === 0 ? (
            <div className="rounded-2xl border-2 border-dashed border-[#DDD6E4] bg-white/60 p-12 text-center">
              
              <p className="mt-3 text-sm text-[#938B9A]">
                키워드를 입력하고 아이디어를 생성해 보세요.
              </p>
            </div>
          ) : (
            <>
              {/* 아이디어 카드 출력 */}
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {ideas.map((idea, index) => (
                  <IdeaCard
                    key={idea.id}
                    idea={idea}
                    index={index}
                  />
                ))}
              </div>

              {/* 선택한 아이디어 개수 */}
              <p className="mt-6 text-right text-sm text-[#837C8A]">
                선택한 아이디어: {selectedIds.length}개
              </p>
            </>
          )}
        </section>

      </main>
    </div>
  )
}

export default App
