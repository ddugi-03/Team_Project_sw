import './App.css'
import IdeaForm from './components/ideaform'
import MindMap from './components/mindmap'
import { useIdeaStore } from './store/useideastore'

function App() {
  const notice = useIdeaStore((state) => state.notice)
  const dismissNotice = useIdeaStore((state) => state.dismissNotice)

  return (
    <div className="app-shell">
      <header className="app-header"><h1>아이디어 노트<span className="header-divider" />마인드맵</h1></header>
      <main className="workspace">
        <aside className="input-panel">
          <IdeaForm />
          <div className="usage-note"><h3>사용 방법</h3><ol><li>주제를 입력해 아이디어를 생성합니다.</li><li>결합할 카드를 두 개 이상 선택합니다.</li><li>결합 버튼을 누르면 새 카드가 추가됩니다.</li></ol><p>새 카드도 다른 카드와 다시 결합할 수 있습니다.</p></div>
        </aside>
        <MindMap />
      </main>
      {notice && <div className={`toast ${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}><span>{notice.text}</span><button type="button" onClick={dismissNotice} aria-label="알림 닫기">×</button></div>}
    </div>
  )
}

export default App
