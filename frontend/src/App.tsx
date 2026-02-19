import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API = 'http://localhost:8000'
const WS = 'ws://localhost:8000'

type Page = 'home' | 'interview' | 'history'
type Phase = 'start' | 'resume_done' | 'dsa' | 'dsa_eval' | 'system_design' | 'sd_eval' | 'behavioral' | 'beh_eval' | 'debate' | 'final'

interface AgentMsg { sender: string; content: string; confidence: number; message_type: string }
interface Evaluation { agent: string; content: string; metadata?: any }
interface HistoryItem {
  session_id: string
  candidate: string
  date: string
  recommendation: string
  overall_score: number
  difficulty: string
  hire_level: string
  score_breakdown?: Record<string, number>
}

export default function App() {
  const [page, setPage] = useState<Page>('home')
  const [phase, setPhase] = useState<Phase>('start')
  const [name, setName] = useState('')
  const [resume, setResume] = useState('')
  const [pdfFileName, setPdfFileName] = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [skillProfile, setSkillProfile] = useState<any>(null)
  const [difficulty, setDifficulty] = useState('MEDIUM')
  const [question, setQuestion] = useState<any>(null)
  const [code, setCode] = useState('')
  const [answer, setAnswer] = useState('')
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [scores, setScores] = useState<any>({})
  const [finalReport, setFinalReport] = useState<any>(null)
  const [hints, setHints] = useState<string[]>([])
  const [hintsLeft, setHintsLeft] = useState(2)
  const [loading, setLoading] = useState(false)
  const [liveMessages, setLiveMessages] = useState<AgentMsg[]>([])
  const [status, setStatus] = useState('')
  const [wsOk, setWsOk] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [pastSessions, setPastSessions] = useState(0)
  const codeRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const connect = useCallback((sid: string) => {
    const ws = new WebSocket(`${WS}/ws/${sid}`)
    ws.onopen = () => setWsOk(true)
    ws.onclose = () => setWsOk(false)
    ws.onmessage = e => {
      const d = JSON.parse(e.data)
      if (d.type === 'agent_message') {
        setLiveMessages(prev => [...prev.slice(-9), d.data])
      }
    }
  }, [])

  const api = async (path: string, params?: Record<string, string>) => {
    const url = new URL(`${API}${path}`)
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
    const res = await fetch(url.toString(), { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  }

  const loadHistory = async () => {
    try {
      const res = await fetch(`${API}/interview/history`)
      const data = await res.json()
      setHistory(data.interviews || [])
    } catch (e) {
      console.error('Error loading history:', e)
    }
  }

  useEffect(() => {
    if (page === 'history') loadHistory()
  }, [page])

  // PDF Upload handler
  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setStatus('Please upload a PDF file.')
      return
    }
    setPdfLoading(true)
    setStatus('Extracting text from PDF...')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API}/upload-resume`, { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'PDF extraction failed')
      }
      const data = await res.json()
      setResume(data.text)
      setPdfFileName(file.name)
      setStatus(`✅ PDF loaded: ${data.pages} page(s) extracted`)
    } catch (err: any) {
      setStatus(`PDF error: ${err.message}`)
    }
    setPdfLoading(false)
  }

  const startInterview = async () => {
    if (!name.trim()) { setStatus('Please enter your name.'); return }
    if (!resume.trim()) { setStatus('Please add your resume (text or PDF).'); return }
    setLoading(true); setStatus('Recruiter analyzing your resume...')
    try {
      const d = await api('/interview/start', { candidate_name: name, resume })
      setSessionId(d.session_id)
      setSkillProfile(d.skill_profile)
      setDifficulty(d.difficulty)
      setPastSessions(d.past_interviews_found || 0)
      setPhase('resume_done')
      setPage('interview')
      connect(d.session_id)
      setStatus('')
    } catch { setStatus('Backend error. Is it running on port 8000?') }
    setLoading(false)
  }

  const startDSA = async () => {
    setLoading(true); setStatus('Generating coding question...')
    try {
      const d = await api(`/interview/${sessionId}/dsa/start`)
      setQuestion(d.question)
      setCode('# Write your Python solution here\n\ndef solution():\n    pass\n')
      setHints([]); setHintsLeft(2)
      setPhase('dsa')
      setStatus('')
    } catch { setStatus('Error loading DSA question.') }
    setLoading(false)
  }

  const submitDSA = async () => {
    if (!code.trim()) { setStatus('Write some code first!'); return }
    setLoading(true); setPhase('dsa_eval'); setStatus('2 agents evaluating your code...')
    setEvaluations([])
    try {
      const d = await api(`/interview/${sessionId}/dsa/answer`, { answer: code })
      setEvaluations(d.evaluations || [])
      setScores(d.scores || {})
      setStatus('Evaluation complete!')
    } catch { setStatus('Error evaluating answer.') }
    setLoading(false)
  }

  const getHint = async () => {
    if (hintsLeft <= 0) return
    try {
      const d = await api(`/interview/${sessionId}/dsa/hint`)
      setHints(prev => [...prev, d.hint])
      setHintsLeft(d.hints_remaining)
    } catch {}
  }

  const startSD = async () => {
    setLoading(true); setStatus('Generating system design question...')
    setEvaluations([]); setAnswer('')
    try {
      const d = await api(`/interview/${sessionId}/system-design/start`)
      setQuestion(d.question)
      setPhase('system_design')
      setStatus('')
    } catch { setStatus('Error loading system design question.') }
    setLoading(false)
  }

  const submitSD = async () => {
    if (!answer.trim()) { setStatus('Write your design first!'); return }
    setLoading(true); setPhase('sd_eval'); setStatus('Staff Engineer evaluating your design...')
    try {
      const d = await api(`/interview/${sessionId}/system-design/answer`, { answer })
      setEvaluations([{ agent: 'SYSTEM_DESIGN', content: d.evaluation, metadata: d.metadata }])
      setScores(d.scores || {})
      setStatus('Design evaluated!')
    } catch { setStatus('Error evaluating design.') }
    setLoading(false)
  }

  const startBehavioral = async () => {
    setLoading(true); setStatus('Generating behavioral question...')
    setEvaluations([]); setAnswer('')
    try {
      const d = await api(`/interview/${sessionId}/behavioral/start`)
      setQuestion(d.question)
      setPhase('behavioral')
      setStatus('')
    } catch { setStatus('Error loading behavioral question.') }
    setLoading(false)
  }

  const submitBehavioral = async () => {
    if (!answer.trim()) { setStatus('Write your answer first!'); return }
    setLoading(true); setPhase('beh_eval'); setStatus('Behavioral interviewer analyzing...')
    try {
      const d = await api(`/interview/${sessionId}/behavioral/answer`, { answer })
      setEvaluations([{ agent: 'BEHAVIORAL', content: d.evaluation, metadata: d.metadata }])
      setScores(d.scores || {})
      setStatus('Behavioral done!')
    } catch { setStatus('Error evaluating behavioral.') }
    setLoading(false)
  }

  const runDebateAndFinal = async () => {
    setLoading(true); setPhase('debate'); setStatus('🥊 Agents debating your performance...')
    try {
      await api(`/interview/${sessionId}/debate`)
      setStatus('📋 Generating final report...')
      const d = await api(`/interview/${sessionId}/final`)
      setFinalReport(d)
      setScores(d.all_scores || {})
      setPhase('final')
      setStatus('')
    } catch { setStatus('Error generating final report.') }
    setLoading(false)
  }

  const handleTab = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Tab') return
    e.preventDefault()
    const s = e.currentTarget.selectionStart
    const newCode = code.substring(0, s) + '    ' + code.substring(e.currentTarget.selectionEnd)
    setCode(newCode)
    setTimeout(() => { if (codeRef.current) codeRef.current.selectionStart = codeRef.current.selectionEnd = s + 4 }, 0)
  }

  const diffColor = (d: string) => d === 'EASY' || d === 'Easy' ? '#00d4aa' : d === 'MEDIUM' || d === 'Medium' ? '#ffa500' : '#ff4757'

  const resetToHome = () => {
    setPage('home'); setPhase('start'); setSessionId(''); setFinalReport(null)
    setScores({}); setLiveMessages([]); setSkillProfile(null); setPastSessions(0)
    setQuestion(null); setCode(''); setAnswer(''); setEvaluations([])
    setStatus(''); setResume(''); setPdfFileName('')
  }

  const steps = [
    { id: 'resume_done', label: 'Resume' },
    { id: 'dsa_eval', label: 'Coding' },
    { id: 'sd_eval', label: 'Sys Design' },
    { id: 'beh_eval', label: 'Behavioral' },
    { id: 'final', label: 'Final' }
  ]
  const phaseOrder: Record<string, number> = { start: 0, resume_done: 1, dsa: 2, dsa_eval: 2, system_design: 3, sd_eval: 3, behavioral: 4, beh_eval: 4, debate: 5, final: 5 }
  const currentStep = phaseOrder[phase] || 0

  // ─── HOME PAGE ──────────────────────────────────────────────────────────────
  if (page === 'home') return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <span className="brand-icon">🚀</span>
          <h1>OrchestrAI <span className="brand-sub">Interview Lab</span></h1>
        </div>
        <nav className="nav-pills">
          <button className="pill active">Home</button>
          <button className="pill" onClick={() => setPage('history')}>📜 History</button>
        </nav>
      </header>

      <div className="home-layout">
        {/* Left: Form */}
        <div className="home-form-col">
          <div className="home-form-card">
            <h2 className="form-title">Start Your Interview</h2>
            <p className="form-sub">8 AI agents will evaluate you in real-time</p>

            <div className="fg">
              <label>Full Name</label>
              <input
                className="inp"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Nurzhan Sultanov"
              />
            </div>

            <div className="fg">
              <label>Resume</label>
              <div className="resume-options">
                {/* PDF Upload */}
                <div
                  className={`pdf-drop-zone ${pdfFileName ? 'pdf-loaded' : ''}`}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    style={{ display: 'none' }}
                    onChange={handlePdfUpload}
                  />
                  {pdfLoading ? (
                    <span className="pdf-state">⏳ Extracting PDF...</span>
                  ) : pdfFileName ? (
                    <span className="pdf-state pdf-ok">📄 {pdfFileName} <span className="pdf-change">click to change</span></span>
                  ) : (
                    <span className="pdf-state">📁 Upload PDF Resume <span className="pdf-hint">click to browse</span></span>
                  )}
                </div>

                <div className="or-divider"><span>or paste text</span></div>

                <textarea
                  className="ta"
                  rows={7}
                  value={resume}
                  onChange={e => { setResume(e.target.value); if (e.target.value) setPdfFileName('') }}
                  placeholder={"Describe your experience:\n- Languages: Python, TypeScript\n- Frameworks: FastAPI, React\n- Projects: RAG system, Agent builder\n- LeetCode: 600+ problems solved"}
                />
              </div>
            </div>

            {status && <p className={status.startsWith('✅') ? 'status-ok' : 'err'}>{status}</p>}

            <button className="btn-main" onClick={startInterview} disabled={loading || pdfLoading}>
              {loading ? '⏳ Analyzing Resume...' : '🎯 Start Interview'}
            </button>
          </div>
        </div>

        {/* Right: Info */}
        <div className="home-info-col">
          <div className="home-hero">
            <h2 className="hero-title">AI-Powered<br/>Technical Interview</h2>
            <p className="hero-sub">Get interviewed by a panel of 8 specialized AI agents — just like a real FAANG loop.</p>
          </div>

          <div className="agent-showcase">
            {[
              { icon: '🎯', name: 'Recruiter', desc: 'Analyzes your resume & sets difficulty' },
              { icon: '💻', name: 'DSA Interviewer', desc: 'LeetCode-style coding questions' },
              { icon: '🔍', name: 'Code Evaluator', desc: 'Judges code quality & complexity' },
              { icon: '🏗️', name: 'System Design', desc: 'Architecture & scalability' },
              { icon: '🧠', name: 'Behavioral', desc: 'STAR-method soft skills' },
              { icon: '🥊', name: 'Critic Agent', desc: 'Cross-agent debate & challenge' },
              { icon: '🔎', name: 'Hallucination Detector', desc: 'Validates AI evaluations' },
              { icon: '⚖️', name: 'Final Decision', desc: 'Hire / No-Hire with reasoning' },
            ].map(a => (
              <div key={a.name} className="agent-card">
                <span className="agent-icon">{a.icon}</span>
                <div>
                  <strong>{a.name}</strong>
                  <p>{a.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="feature-pills">
            <span className="fpill">🧠 RAG Memory</span>
            <span className="fpill">🔴 Live Updates</span>
            <span className="fpill">📊 Score Breakdown</span>
            <span className="fpill">📄 PDF Support</span>
          </div>
        </div>
      </div>
    </div>
  )

  // ─── HISTORY PAGE ────────────────────────────────────────────────────────────
  if (page === 'history') return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <span className="brand-icon">🚀</span>
          <h1>OrchestrAI <span className="brand-sub">Interview Lab</span></h1>
        </div>
        <nav className="nav-pills">
          <button className="pill" onClick={() => setPage('home')}>Home</button>
          <button className="pill active">📜 History</button>
        </nav>
      </header>

      <div className="history-page">
        <div className="history-page-header">
          <div>
            <h2>Interview History</h2>
            <p className="history-sub">All completed interview sessions</p>
          </div>
          <div className="history-stats">
            <div className="hstat">
              <span className="hstat-num">{history.length}</span>
              <span className="hstat-label">Total</span>
            </div>
            <div className="hstat">
              <span className="hstat-num green">{history.filter(h => h.recommendation === 'hire').length}</span>
              <span className="hstat-label">Hired</span>
            </div>
            <div className="hstat">
              <span className="hstat-num red">{history.filter(h => h.recommendation !== 'hire').length}</span>
              <span className="hstat-label">Rejected</span>
            </div>
            <div className="hstat">
              <span className="hstat-num accent">
                {history.length > 0 ? (history.reduce((s, h) => s + (h.overall_score || 0), 0) / history.length).toFixed(1) : '—'}
              </span>
              <span className="hstat-label">Avg Score</span>
            </div>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="empty-history">
            <div className="empty-icon">📋</div>
            <h3>No interviews yet</h3>
            <p>Start your first interview to see results here.</p>
            <button className="btn-main" style={{width:'auto', padding:'0.75rem 2rem'}} onClick={() => setPage('home')}>
              🎯 Start Interview
            </button>
          </div>
        ) : (
          <div className="history-grid">
            {history.map((h, idx) => (
              <div key={h.session_id} className={`hcard ${h.recommendation === 'hire' ? 'hcard-hire' : 'hcard-nohire'}`}>
                <div className="hcard-top">
                  <div className="hcard-rank">#{idx + 1}</div>
                  <div className={`hcard-verdict ${h.recommendation === 'hire' ? 'verdict-hire' : 'verdict-nohire'}`}>
                    {h.recommendation === 'hire' ? '✅ HIRE' : '❌ NO HIRE'}
                  </div>
                </div>

                <div className="hcard-name">{h.candidate}</div>
                {h.hire_level && <div className="hcard-level">{h.hire_level}</div>}

                <div className="hcard-score-row">
                  <div className="hcard-score-big">
                    <span className="score-number">{h.overall_score}</span>
                    <span className="score-denom">/10</span>
                  </div>
                  <div className="hcard-score-bar-wrap">
                    <div className="hcard-score-bar" style={{width: `${(h.overall_score || 0) * 10}%`, background: h.recommendation === 'hire' ? 'var(--green)' : 'var(--red)'}} />
                  </div>
                </div>

                {h.score_breakdown && Object.keys(h.score_breakdown).length > 0 && (
                  <div className="hcard-breakdown">
                    {Object.entries(h.score_breakdown).map(([k, v]) => (
                      <div key={k} className="hcard-bitem">
                        <span>{k.replace(/_/g,' ')}</span>
                        <span className="bitem-score">{v as number}/10</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="hcard-meta">
                  <span className={`hcard-diff diff-${h.difficulty.toLowerCase()}`}>{h.difficulty}</span>
                  <span className="hcard-date">{new Date(h.date).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'})}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  // ─── FINAL REPORT ────────────────────────────────────────────────────────────
  if (page === 'interview' && phase === 'final' && finalReport) return (
    <div className="app">
      <header className="header compact">
        <div className="header-brand">
          <span className="brand-icon">🚀</span>
          <h1>OrchestrAI</h1>
        </div>
        <nav className="nav-pills">
          <button className="pill" onClick={resetToHome}>Home</button>
          <button className="pill" onClick={() => setPage('history')}>History</button>
        </nav>
      </header>
      <div className="report-wrap">
        <div className="card final-card">
          <div className={`rec-banner ${finalReport.recommendation === 'hire' ? 'hire' : 'nohire'}`}>
            <div className="rec-emoji">{finalReport.recommendation === 'hire' ? '✅' : '❌'}</div>
            <div>
              <h2>{finalReport.recommendation === 'hire' ? 'HIRE' : 'NO HIRE'}</h2>
              <p>Overall Score: <strong>{finalReport.overall_score}/10</strong> · Confidence: {Math.round((finalReport.confidence||0)*100)}%</p>
              {finalReport.hire_level && <p className="hire-level">Level: {finalReport.hire_level}</p>}
              {pastSessions > 0 && <p className="past-sessions">🧠 {pastSessions} past interview(s) in memory</p>}
            </div>
          </div>

          <div className="score-grid">
            {Object.entries(finalReport.score_breakdown || {}).map(([k, v]) => (
              <div key={k} className="score-item">
                <span className="score-label">{k.replace(/_/g,' ')}</span>
                <div className="score-bar-wrap"><div className="score-bar" style={{width: `${(v as number)*10}%`}} /></div>
                <span className="score-num">{v as number}/10</span>
              </div>
            ))}
          </div>

          {finalReport.detailed_feedback && (
            <div className="feedback-section"><p>{finalReport.detailed_feedback}</p></div>
          )}

          <div className="two-col">
            <div>
              <h3>✅ Strengths</h3>
              {(finalReport.strengths||[]).map((s: string) => <div key={s} className="list-item green-dot">{s}</div>)}
            </div>
            <div>
              <h3>⚠️ Concerns</h3>
              {(finalReport.concerns||[]).map((c: string) => <div key={c} className="list-item red-dot">{c}</div>)}
            </div>
          </div>

          {finalReport.growth_areas?.length > 0 && (
            <div className="growth-section">
              <h3>🚀 Growth Areas</h3>
              {finalReport.growth_areas.map((g: string) => <div key={g} className="list-item blue-dot">{g}</div>)}
            </div>
          )}

          {finalReport.next_steps && (
            <div className="next-steps"><strong>Next Steps:</strong> {finalReport.next_steps}</div>
          )}

          <div className="final-actions">
            <button className="btn-main" onClick={resetToHome}>🔄 New Interview</button>
            <button className="btn-secondary-outline" onClick={() => setPage('history')}>📜 View History</button>
          </div>
        </div>
      </div>
    </div>
  )

  // ─── INTERVIEW IN PROGRESS ────────────────────────────────────────────────────
  return (
    <div className="app">
      <header className="header compact">
        <div className="header-brand">
          <span className="brand-icon">🚀</span>
          <h1>OrchestrAI</h1>
        </div>
        <div className="header-right">
          <div className="progress-steps">
            {steps.map((s, i) => (
              <div key={s.id} className={`step ${currentStep > i ? 'done' : currentStep === i+1 ? 'active' : ''}`}>
                <span className="step-dot">{currentStep > i ? '✓' : i+1}</span>
                <span className="step-label">{s.label}</span>
              </div>
            ))}
          </div>
          <span className={`badge ${wsOk ? 'green' : 'gray'}`}>{wsOk ? '🟢 Live' : '⚪'}</span>
        </div>
      </header>

      {/* RESUME DONE */}
      {phase === 'resume_done' && (
        <div className="center-wrap">
          <div className="card">
            <h2>✅ Resume Analyzed — {name}</h2>
            {pastSessions > 0 && (
              <div className="past-sessions-alert">
                🧠 Found {pastSessions} past interview session{pastSessions !== 1 ? 's' : ''} in RAG memory
              </div>
            )}
            <div className="profile-row">
              <div className="pitem">
                <span className="plabel">Difficulty</span>
                <span className="pval" style={{color: diffColor(difficulty)}}>{difficulty}</span>
              </div>
              <div className="pitem">
                <span className="plabel">DSA Level</span>
                <span className="pval">{skillProfile?.dsa_level || '—'}</span>
              </div>
              <div className="pitem">
                <span className="plabel">Experience</span>
                <span className="pval">
                  {skillProfile?.experience_years !== undefined && skillProfile?.experience_years !== null
                    ? `${skillProfile.experience_years}y`
                    : '—'}
                </span>
              </div>
              <div className="pitem">
                <span className="plabel">Sys Design</span>
                <span className="pval">{skillProfile?.system_design_level || '—'}</span>
              </div>
            </div>

            {/* Languages */}
            {skillProfile?.languages && Object.keys(skillProfile.languages).length > 0 && (
              <div className="profile-section">
                <span className="profile-section-label">Languages</span>
                <div className="tags-row">
                  {Object.entries(skillProfile.languages).map(([l,v]) =>
                    <span key={l} className="tag">{l} <span className="tag-level">({v as string})</span></span>
                  )}
                </div>
              </div>
            )}

            {/* Frameworks */}
            {skillProfile?.frameworks?.length > 0 && (
              <div className="profile-section">
                <span className="profile-section-label">Frameworks</span>
                <div className="tags-row">
                  {skillProfile.frameworks.map((f: string) => <span key={f} className="tag">{f}</span>)}
                </div>
              </div>
            )}

            {/* Strengths & Gaps */}
            {(skillProfile?.strengths?.length > 0 || skillProfile?.gaps?.length > 0) && (
              <div className="strengths-gaps-row">
                {skillProfile?.strengths?.length > 0 && (
                  <div>
                    <span className="profile-section-label">Strengths</span>
                    <div className="tags-row">
                      {skillProfile.strengths.map((s: string) => <span key={s} className="tag green">{s}</span>)}
                    </div>
                  </div>
                )}
                {skillProfile?.gaps?.length > 0 && (
                  <div>
                    <span className="profile-section-label">Areas to Probe</span>
                    <div className="tags-row">
                      {skillProfile.gaps.map((g: string) => <span key={g} className="tag red">{g}</span>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            <button className="btn-main" onClick={startDSA} disabled={loading}>
              {loading ? '⏳ Loading...' : '💻 Start Coding Round →'}
            </button>
          </div>
        </div>
      )}

      {/* DSA PHASE */}
      {(phase === 'dsa' || phase === 'dsa_eval') && (
        <div className="interview-split">
          <div className="question-panel">
            {question && (<>
              <h2>{question.title}</h2>
              <div className="qmeta">
                <span className="diff" style={{color:diffColor(question.difficulty||difficulty)}}>{question.difficulty||difficulty}</span>
                {question.category && <span className="qcat">{question.category}</span>}
              </div>
              <p className="prob-stmt">{question.problem_statement}</p>
              {question.examples?.map((ex: any, i: number) => (
                <div key={i} className="ex">
                  <div><strong>Input:</strong> {ex.input}</div>
                  <div><strong>Output:</strong> {ex.output}</div>
                  {ex.explanation && <div className="ex-explain"><strong>Explanation:</strong> {ex.explanation}</div>}
                </div>
              ))}
              {question.constraints?.length > 0 && (
                <div className="constraints">
                  <strong>Constraints:</strong>
                  <ul>{question.constraints.map((c: string, i: number) => <li key={i}>{c}</li>)}</ul>
                </div>
              )}
              {hints.length > 0 && (
                <div className="hints">
                  <strong>💡 Hints:</strong>
                  {hints.map((h, i) => <div key={i} className="hint">{h}</div>)}
                </div>
              )}
              <button className="btn-hint" onClick={getHint} disabled={hintsLeft <= 0}>
                💡 Hint ({hintsLeft} left)
              </button>
            </>)}
            {evaluations.length > 0 && (
              <div className="evals">
                <h3>🤖 Agent Evaluations</h3>
                {evaluations.map((e, i) => (
                  <div key={i} className={`eval ${e.agent.toLowerCase()}`}>
                    <strong>{e.agent.replace(/_/g,' ')}</strong>
                    <p>{e.content}</p>
                  </div>
                ))}
                <button className="btn-secondary" onClick={startSD}>Next: System Design →</button>
              </div>
            )}
          </div>
          <div className="editor-panel">
            <h3>💻 Code Editor</h3>
            <textarea
              ref={codeRef}
              className="code-ed"
              value={code}
              onChange={e => setCode(e.target.value)}
              onKeyDown={handleTab}
              spellCheck={false}
            />
            {status && <p className="status">{status}</p>}
            <button
              className="btn-submit"
              onClick={submitDSA}
              disabled={loading || phase === 'dsa_eval'}
            >
              {loading || phase === 'dsa_eval' ? '⏳ Evaluating...' : '🚀 Submit Code'}
            </button>
          </div>
        </div>
      )}

      {/* SYSTEM DESIGN PHASE */}
      {(phase === 'system_design' || phase === 'sd_eval') && (
        <div className="center-wrap">
          <div className="card">
            <h2>🏗️ {question?.title || 'System Design'}</h2>
            <p className="prob-stmt">{question?.problem_statement}</p>
            {question?.requirements?.length > 0 && (
              <div className="reqs">
                <strong>Requirements:</strong>
                <ul>{question.requirements.map((r: string, i: number) => <li key={i}>{r}</li>)}</ul>
              </div>
            )}
            <textarea
              className="ta"
              rows={15}
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              placeholder="Describe your architecture, components, data flow, scaling strategy..."
            />
            {status && <p className="status">{status}</p>}
            {evaluations.length === 0 ? (
              <button className="btn-main" onClick={submitSD} disabled={loading}>
                {loading ? '⏳ Evaluating...' : 'Submit Design'}
              </button>
            ) : (
              <>
                <div className="eval-card"><p>{evaluations[0].content}</p></div>
                <button className="btn-main" onClick={startBehavioral}>Next: Behavioral →</button>
              </>
            )}
          </div>
        </div>
      )}

      {/* BEHAVIORAL PHASE */}
      {(phase === 'behavioral' || phase === 'beh_eval') && (
        <div className="center-wrap">
          <div className="card">
            <h2>🧠 Behavioral Interview</h2>
            <div className="star-guide">
              {[['S','Situation'],['T','Task'],['A','Action'],['R','Result']].map(([l,d]) => (
                <div key={l} className="star-item">
                  <span className="star-letter">{l}</span>
                  <span className="star-desc">{d}</span>
                </div>
              ))}
            </div>
            <p className="bq">{question?.question}</p>
            <textarea
              className="ta"
              rows={14}
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              placeholder="Use the STAR format to structure your answer..."
            />
            {status && <p className="status">{status}</p>}
            {evaluations.length === 0 ? (
              <button className="btn-main" onClick={submitBehavioral} disabled={loading}>
                {loading ? '⏳ Evaluating...' : 'Submit Answer'}
              </button>
            ) : (
              <>
                <div className="eval-card"><p>{evaluations[0].content}</p></div>
                <button className="btn-main" onClick={runDebateAndFinal}>
                  🥊 Agent Debate & Final Report
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* DEBATE */}
      {phase === 'debate' && (
        <div className="center-wrap">
          <div className="card debate-card">
            <div className="debate-anim">🥊</div>
            <h2>Cross-Agent Debate in Progress</h2>
            <p className="sub">7 AI agents are challenging each other on your performance...</p>
            <div className="agent-list">
              {['RECRUITER','DSA INTERVIEWER','CODE EVALUATOR','SYSTEM DESIGN','BEHAVIORAL','CRITIC','FINAL DECISION'].map(a =>
                <div key={a} className="agent-pill">{a}</div>
              )}
            </div>
            {status && <p className="status">{status}</p>}
          </div>
        </div>
      )}

      {/* LIVE FEED */}
      {liveMessages.length > 0 && (
        <div className="live-feed">
          <h4>🔴 Live Agent Activity</h4>
          {liveMessages.slice(-3).map((m, i) => (
            <div key={i} className="msg">
              <span className="sender">{m.sender}</span>
              <span className="txt">{m.content.substring(0, 100)}{m.content.length > 100 ? '...' : ''}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}