import './App.css'
import IdeaForm from './components/ideaform'
import MindMap from './components/mindmap'
import { useIdeaStore } from './store/useideastore'
import { useEffect } from 'react'

function App() {
  const notice = useIdeaStore((state) => state.notice)
  const dismissNotice = useIdeaStore((state) => state.dismissNotice)

  useEffect(() => {
    if (!notice) return
    const timer = setTimeout(dismissNotice, 5000)
    return () => clearTimeout(timer)
  }, [notice, dismissNotice])

  return (
    <div className="app-shell">
      <header className="app-header"><h1>IDEA NOTE</h1></header>
      <main className="workspace">
        <aside className="input-panel">
          <IdeaForm />
        </aside>
        <MindMap />
      </main>
      {notice && <div className={`toast ${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}><span>{notice.text}</span><button type="button" onClick={dismissNotice} aria-label="알림 닫기">×</button></div>}
    </div>
  )
}

export default App
