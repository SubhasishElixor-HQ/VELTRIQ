import { useEffect, useMemo, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const questions = [
  'What happened before this battery warning?',
  'When did the battery warning first occur?',
  'Which signals changed before this warning?',
  'Has this battery warning happened before?',
  'How did this trip compare with another trip?',
  "What happened immediately before this battery warning?",
    "When did the battery warning first occur?",
    "How long did the warning remain active?",
    "How many times has this warning occurred?",
    "When did this warning last occur?",
    "Did the warning disappear automatically or after a restart?",
    "Were any other warnings triggered at the same time?",
    "How much time passed between the first abnormal signal and the warning?",
    "Did voltage, current, and temperature change together?",
    "Was there a sudden spike or a gradual deterioration?",
    "Which sensor readings are most strongly associated with this warning?",
    "Did any sensor provide inconsistent or implausible readings?",
    "Could this warning be caused by a faulty sensor?",
    "What combination of signals best explains this warning?",

]

type Evidence = {
  evidence_id: string
  record_type: 'event' | 'signal' | 'log' | 'trip'
  timestamp_utc: string
  source: string
  label: string
  value?: number | string | null
  unit?: string | null
  quality?: string | null
  trip_id: string
}
type Result = {
  intent: string
  answer: string
  time_range: string
  evidence: Evidence[]
  limitations: string[]
  response_mode: 'deterministic' | 'local-model'
  simulated_data: boolean
}
type Stats = { counts: Record<string, number>; model_configured: boolean; mode: string }

function fmtTime(value: string) {
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function titleCase(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function App() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState<Result | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const refreshStats = async () => {
    try {
      const response = await fetch(`${API}/api/v1/settings`)
      if (!response.ok) throw new Error('API unavailable')
      setStats(await response.json())
      setError('')
    } catch {
      setError('The local API is not running. Start the backend using the README instructions.')
    }
  }
  useEffect(() => { void refreshStats() }, [])

  const ask = async (value = question) => {
    const text = value.trim()
    if (!text) return
    setQuestion(text)
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API}/api/v1/query`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || 'The query could not be completed.')
      setResult(payload)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected local API error.')
    } finally { setLoading(false) }
  }

  const importFile = async (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.jsonl')) {
      setError('Choose a JSONL file. See docs/data-format.md for the supported record schema.')
      return
    }
    setImporting(true); setError(''); setToast('')
    try {
      const response = await fetch(`${API}/api/v1/import`, { method: 'POST', headers: { 'Content-Type': 'text/plain; charset=utf-8' }, body: await file.text() })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || 'Import failed.')
      const inserted = Object.values(payload.inserted as Record<string, number>).reduce((total, count) => total + count, 0)
      setToast(`Imported ${inserted} records · ${payload.duplicates} duplicates · ${payload.rejected} rejected`)
      await refreshStats()
    } catch (e) { setError(e instanceof Error ? e.message : 'Import failed.') }
    finally { setImporting(false) }
  }

  const evidenceCounts = useMemo(() => {
    const evidence = result?.evidence || []
    return { events: evidence.filter((x) => x.record_type === 'event').length, signals: evidence.filter((x) => x.record_type === 'signal').length + evidence.filter((x) => x.record_type === 'log').length }
  }, [result])

  return (
    <div className="app-shell">
      <aside className="rail">
        <div className="brand-mark">V</div>
        <div className="rail-spacer" />
        <div className="rail-icon active" title="Diagnostic workbench">⌕</div>
        <div className="rail-icon" title="Vehicle data">▤</div>
        <div className="rail-spacer" />
        <div className="avatar">SE</div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="brand-lockup"><span>VELTRIQ</span><small>SERVICE ENGINEERING WORKSPACE</small></div>
          <div className="topbar-right">
            <span className="local-badge"><i /> LOCAL ONLY</span>
            <button className="import-button" onClick={() => document.getElementById('jsonl-input')?.click()} disabled={importing}>
              {importing ? 'Importing…' : '＋ Import JSONL'}
            </button>
            <input id="jsonl-input" type="file" accept=".jsonl,application/json" hidden onChange={(e) => { void importFile(e.target.files?.[0]); e.currentTarget.value = '' }} />
          </div>
        </header>

        <section className="welcome-row">
          <div>
            <div className="eyebrow">OFFLINE DIAGNOSTIC ASSISTANT <span className="dot-sep">/</span> DEMO DATA</div>
            <h1>Find the story behind a warning.</h1>
            <p className="lede">Ask a question. Review the timeline and the vehicle records behind the answer.</p>
          </div>
          <div className="vehicle-stamp"><span className="vehicle-glyph">▰</span><div><b>DEMO EV 01</b><small>SIMULATED VEHICLE</small></div><span className="live-dot" /></div>
        </section>

        <section className="metrics-row">
          <div className="metric"><span className="metric-label">TRIPS IN LOCAL HISTORY</span><b>{stats?.counts.trips ?? '—'}</b><small>Stored on this device</small></div>
          <div className="metric"><span className="metric-label">DIAGNOSTIC EVENTS</span><b>{stats?.counts.events ?? '—'}</b><small>Warnings and system events</small></div>
          <div className="metric"><span className="metric-label">ANSWER ENGINE</span><b className="metric-engine">{stats?.model_configured ? 'Local SLM' : 'Evidence rules'}</b><small>{stats?.model_configured ? 'Local endpoint configured' : 'Works without a model'}</small></div>
          <div className="metric target-metric"><span className="metric-label">EDGE LATENCY GOAL</span><b>&lt; 2 sec</b><small>Not benchmarked on vehicle hardware</small></div>
        </section>

        {error && <div className="notice error-notice"><span>!</span><div><b>Action needed</b><p>{error}</p></div><button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
        {toast && <div className="notice success-notice"><span>✓</span><div>{toast}</div><button onClick={() => setToast('')} aria-label="Dismiss message">×</button></div>}

        <section className="workbench">
          <div className="query-panel">
            <div className="section-heading"><div><span className="section-kicker">ASK THE VEHICLE HISTORY</span><h2>What would you like to investigate?</h2></div><span className="offline-chip">● OFFLINE</span></div>
            <div className="composer">
              <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void ask() } }} placeholder="Example: What happened before this battery warning?" rows={3} maxLength={500} />
              <div className="composer-footer"><span>Answers are grounded in imported records</span><button className="ask-button" onClick={() => void ask()} disabled={loading || !question.trim()}>{loading ? 'Searching…' : 'Ask VehicleGPT'} <span>→</span></button></div>
            </div>
            <div className="examples-heading">START WITH A QUESTION</div>
            <div className="question-list">{questions.map((q, i) => <button key={q} className="question-chip" onClick={() => { setQuestion(q); void ask(q) }}><span className="question-number">0{i + 1}</span>{q}<span className="chip-arrow">↗</span></button>)}</div>
            <div className="data-footnote"><span className="shield">◇</span><span>Read-only analysis. VehicleGPT does not control the vehicle or contact cloud services.</span></div>
          </div>

          <div className="results-panel">
            <div className="results-header"><div><span className="section-kicker">INVESTIGATION RESULT</span><h2>{result ? 'Evidence timeline' : 'Your evidence will appear here'}</h2></div>{result && <span className="result-count">{evidenceCounts.events} events · {evidenceCounts.signals} signals</span>}</div>
            {!result ? <div className="empty-state"><div className="empty-graphic"><span>⌁</span><i /><i /><i /></div><b>Start with a warning or a trip comparison</b><p>VehicleGPT will search the local history and show the records used to answer.</p><span className="empty-time">NO CLOUD REQUIRED</span></div> : <>
              <div className="answer-card"><div className="answer-label"><span className="answer-spark">✳</span> SUMMARY <span className="answer-mode">{result.response_mode === 'local-model' ? 'LOCAL MODEL' : 'DETERMINISTIC'}</span></div><p>{result.answer}</p><div className="time-window"><span>TIME WINDOW</span><b>{result.time_range}</b></div></div>
              {result.limitations.length > 0 && <div className="limitation"><span>!</span><div><b>Data limitation</b><p>{result.limitations.join(' ')}</p></div></div>}
              <div className="timeline-list">{result.evidence.map((item) => <article className="evidence-row" key={item.evidence_id}><div className={`timeline-marker ${item.record_type}`}><span>{item.record_type === 'event' ? '!' : item.record_type === 'signal' ? '⌁' : '▤'}</span></div><div className="evidence-content"><div className="evidence-meta"><span className={`type-tag ${item.record_type}`}>{item.record_type.toUpperCase()}</span><time>{fmtTime(item.timestamp_utc)}</time></div><b>{item.label}</b><div className="evidence-detail">{item.value !== null && item.value !== undefined ? <span>{typeof item.value === 'number' ? item.value.toFixed(1) : item.value}{item.unit ? ` ${item.unit}` : ''}</span> : null}<span>{item.source}</span><span>{item.trip_id}</span></div>{item.quality && item.quality !== 'valid' && <span className="quality-warning">{titleCase(item.quality)} sample</span>}</div></article>)}</div>
              {result.evidence.length === 0 && <div className="no-evidence">No records matched. Import the generated demo dataset or use a supported question.</div>}
              <div className="result-disclaimer">Evidence is shown from the local dataset. Correlation does not establish root cause.</div>
            </>}
          </div>
        </section>
        <footer className="page-footer"><span>VEHICLEGPT <i>·</i> SOFTWARE-ONLY PILOT</span><span>SIMULATED DATA <i>·</i> LOCAL STORAGE <i>·</i> NO CONTROL PATH</span></footer>
      </main>
    </div>
  )
}
