import { useState, useEffect, useRef, useCallback } from 'react'
import type { AgentMessage, InterviewSession } from './types/interview'
import './App.css'

const API_BASE = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'

type Phase = 'start' | 'resume_analysis' | 'dsa' | 'evaluating' | 'completed'

interface Question {
  title: string
  difficulty: string
  category: string
  problem_statement: string
  examples: Array<{ input: string; output: string; explanation: string }>
  constraints: string[]
  hints: string[]
  time_complexity: string
  space_complexity: string
}

export default function App() {
  const [phase, setPhase] = useState<Phase>('start')
  const [candidateName, setCandidateName] = useState('')
  const [resume, setResume] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [skillProfile, setSkillProfile] = useState<any>(null)
  const [difficulty, setDifficulty] = useState<string>('MEDIUM')
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [code, setCode] = useState('')
  const [scores, setScores] = useState<any>({})
  const [hints, setHints] = useState<string[]>([])
  const [hintsRemaining, setHintsRemaining] = useState(2)
  const [isLoading, setIsLoading] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [evaluations, setEvaluations] = useState<Array<{agent: string, content: string}>>([])
  
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const codeRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, evaluations])

  const connectWebSocket = useCallback((sid: string) => {
    const ws = new WebSocket(`${WS_BASE}/ws/${sid}`)
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => setWsConnected(false)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'agent_message') {
        setMessages(prev => [...prev, data.data])
      }
    }
    wsRef.current = ws
    return ws
  }, [])

  const startInterview = async () => {
    if (!candidateName.trim() || !resume.trim()) {
      setStatusMsg('Please fill in your name and resume!')
      return
    }
    setIsLoading(true)
    setStatusMsg('Analyzing your resume...')
    try {
      const res = await fetch(
        `${API_BASE}/interview/start?candidate_name=${encodeURIComponent(candidateName)}&resume=${encodeURIComponent(resume)}`,
        { method: 'POST' }
      )
      const data = await res.json()
      setSessionId(data.session_id)
      setSkillProfile(data.skill_profile)
      setDifficulty(data.difficulty || 'MEDIUM')
      setPhase('resume_analysis')
      setStatusMsg('Resume analyzed! Ready to start coding interview.')
      connectWebSocket(data.session_id)
    } catch (e) {
      setStatusMsg('Error connecting to backend. Is it running?')
    }
    setIsLoading(false)
  }

  const startDSAPhase = async () => {
    if (!sessionId) return
    setIsLoading(true)
    setStatusMsg('Generating your question...')
    setPhase('dsa')
    try {
      const res = await fetch(`${API_BASE}/interview/${sessionId}/next`, { method: 'POST' })
      const data = await res.json()
      setCurrentQuestion(data.question)
      setCode('# Write your solution here\n\n')
      setStatusMsg('')
    } catch (e) {
      setStatusMsg('Error loading question.')
    }
    setIsLoading(false)
  }

  const submitAnswer = async () => {
    if (!sessionId || !code.trim()) {
      setStatusMsg('Please write some code first!')
      return
    }
    setIsLoading(true)
    setPhase('evaluating')
    setStatusMsg('Two AI agents are evaluating your code...')
    setEvaluations([])
    try {
      const res = await fetch(
        `${API_BASE}/interview/${sessionId}/answer?answer=${encodeURIComponent(code)}`,
        { method: 'POST' }
      )
      const data = await res.json()
      setEvaluations(data.evaluations || [])
      setScores(data.scores || {})
      setStatusMsg('Evaluation complete!')
    } catch (e) {
      setStatusMsg('Error submitting answer.')
    }
    setIsLoading(false)
  }

  const getHint = async () => {
    if (!sessionId || hintsRemaining <= 0) return
    try {
      const res = await fetch(`${API_BASE}/interview/${sessionId}/hint`, { method: 'POST' })
      const data = await res.json()
      setHints(prev => [...prev, data.hint])
      setHintsRemaining(data.hints_remaining)
    } catch (e) {
      setStatusMsg('Error getting hint.')
    }
  }

  const tryAnotherQuestion = async () => {
    setEvaluations([])
    setCode('')
    setHints([])
    setHintsRemaining(2)
    setPhase('dsa')
    await startDSAPhase()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const start = e.currentTarget.selectionStart
      const end = e.currentTarget.selectionEnd
      const newCode = code.substring(0, start) + '    ' + code.substring(end)
      setCode(newCode)
      setTimeout(() => {
        if (codeRef.current) {
          codeRef.current.selectionStart = codeRef.current.selectionEnd = start + 4
        }
      }, 0)
    }
  }

  const getDifficultyColor = (d: string) => {
    if (d === 'EASY' || d === 'Easy') return '#00d4aa'
    if (d === 'MEDIUM' || d === 'Medium') return '#ffa500'
    return '#ff4757'
  }

  // START SCREEN
  if (phase === 'start') {
    return (
      <div className="app">
        <header className="header">
          <h1>🚀 OrchestrAI Interview Lab</h1>
          <div className={`status-badge ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '🟢 Connected' : '⚪ Not Connected'}
          </div>
        </header>

        <div className="start-container">
          <div className="start-card">
            <h2>Technical Interview Simulator</h2>
            <p className="subtitle">Multi-agent AI system powered by Groq • LLaMA 3.3 70B</p>

            <div className="form-group">
              <label>Your Name</label>
              <input
                type="text"
                placeholder="e.g. Nurzhan Sultanov"
                value={candidateName}
                onChange={e => setCandidateName(e.target.value)}
                className="input"
              />
            </div>

            <div className="form-group">
              <label>Your Resume / Experience</label>
              <textarea
                placeholder="Paste your resume or describe your experience:&#10;- Programming languages&#10;- Frameworks&#10;- Projects&#10;- LeetCode experience..."
                value={resume}
                onChange={e => setResume(e.target.value)}
                className="textarea"
                rows={8}
              />
            </div>

            {statusMsg && <p className="status-msg error">{statusMsg}</p>}

            <button
              className="btn-primary"
              onClick={startInterview}
              disabled={isLoading}
            >
              {isLoading ? '⏳ Analyzing Resume...' : '🎯 Start Interview'}
            </button>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <span className="feature-icon">🤖</span>
              <h3>Multi-Agent System</h3>
              <p>Recruiter, DSA Interviewer & Code Evaluator work together</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">⚡</span>
              <h3>Adaptive Difficulty</h3>
              <p>Questions tailored to your skill level</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">💡</span>
              <h3>Instant Feedback</h3>
              <p>Detailed code review with complexity analysis</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🧠</span>
              <h3>RAG Memory</h3>
              <p>Vector store remembers your interview history</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // RESUME ANALYSIS SCREEN
  if (phase === 'resume_analysis') {
    return (
      <div className="app">
        <header className="header">
          <h1>🚀 OrchestrAI Interview Lab</h1>
          <div className="status-badge connected">🟢 Connected</div>
        </header>

        <div className="analysis-container">
          <div className="analysis-card">
            <h2>✅ Resume Analyzed!</h2>
            <p className="candidate-name">Candidate: <strong>{candidateName}</strong></p>

            <div className="profile-grid">
              <div className="profile-item">
                <span className="profile-label">Difficulty</span>
                <span className="profile-value" style={{color: getDifficultyColor(difficulty)}}>
                  {difficulty}
                </span>
              </div>
              <div className="profile-item">
                <span className="profile-label">DSA Level</span>
                <span className="profile-value">{skillProfile?.dsa_level || 'N/A'}</span>
              </div>
              <div className="profile-item">
                <span className="profile-label">Experience</span>
                <span className="profile-value">{skillProfile?.experience_years || 0} years</span>
              </div>
              <div className="profile-item">
                <span className="profile-label">System Design</span>
                <span className="profile-value">{skillProfile?.system_design_level || 'N/A'}</span>
              </div>
            </div>

            {skillProfile?.languages && (
              <div className="skills-section">
                <h3>Languages Detected</h3>
                <div className="tags">
                  {Object.entries(skillProfile.languages).map(([lang, level]) => (
                    <span key={lang} className="tag">
                      {lang} <span className="tag-level">({level as string})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {skillProfile?.strengths && (
              <div className="skills-section">
                <h3>Strengths</h3>
                <div className="tags">
                  {skillProfile.strengths.map((s: string) => (
                    <span key={s} className="tag strength">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {skillProfile?.gaps && (
              <div className="skills-section">
                <h3>Areas to Probe</h3>
                <div className="tags">
                  {skillProfile.gaps.map((g: string) => (
                    <span key={g} className="tag gap">{g}</span>
                  ))}
                </div>
              </div>
            )}

            <button className="btn-primary large" onClick={startDSAPhase} disabled={isLoading}>
              {isLoading ? '⏳ Loading Question...' : '💻 Start Coding Interview →'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // DSA INTERVIEW SCREEN
  return (
    <div className="app interview-layout">
      <header className="header compact">
        <h1>🚀 OrchestrAI Interview Lab</h1>
        <div className="header-right">
          {Object.keys(scores).length > 0 && (
            <span className="score-badge">
              Score: {scores.dsa ? `DSA: ${scores.dsa}/10` : ''}
              {scores.code_quality ? ` | Code: ${scores.code_quality}/10` : ''}
            </span>
          )}
          <div className={`status-badge ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '🟢 Live' : '⚪ Offline'}
          </div>
        </div>
      </header>

      <div className="interview-container">
        {/* LEFT PANEL - Question */}
        <div className="question-panel">
          {isLoading && !currentQuestion ? (
            <div className="loading-card">
              <div className="spinner"></div>
              <p>{statusMsg || 'Loading question...'}</p>
            </div>
          ) : currentQuestion ? (
            <>
              <div className="question-header">
                <h2>{currentQuestion.title}</h2>
                <div className="question-meta">
                  <span className="difficulty-badge" style={{color: getDifficultyColor(currentQuestion.difficulty)}}>
                    {currentQuestion.difficulty}
                  </span>
                  <span className="category-badge">{currentQuestion.category}</span>
                </div>
              </div>

              <div className="question-body">
                <p className="problem-statement">{currentQuestion.problem_statement}</p>

                {currentQuestion.examples?.length > 0 && (
                  <div className="examples-section">
                    <h3>Examples</h3>
                    {currentQuestion.examples.map((ex, i) => (
                      <div key={i} className="example-card">
                        <div><strong>Input:</strong> <code>{ex.input}</code></div>
                        <div><strong>Output:</strong> <code>{ex.output}</code></div>
                        {ex.explanation && <div><strong>Explanation:</strong> {ex.explanation}</div>}
                      </div>
                    ))}
                  </div>
                )}

                {currentQuestion.constraints?.length > 0 && (
                  <div className="constraints-section">
                    <h3>Constraints</h3>
                    <ul>
                      {currentQuestion.constraints.map((c, i) => (
                        <li key={i}><code>{c}</code></li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="complexity-section">
                  <span>🎯 Target: <strong>{currentQuestion.time_complexity}</strong> time, <strong>{currentQuestion.space_complexity}</strong> space</span>
                </div>
              </div>

              {/* Hints */}
              {hints.length > 0 && (
                <div className="hints-section">
                  <h3>💡 Hints Used</h3>
                  {hints.map((hint, i) => (
                    <div key={i} className="hint-card">{hint}</div>
                  ))}
                </div>
              )}

              <button
                className="btn-hint"
                onClick={getHint}
                disabled={hintsRemaining <= 0}
              >
                💡 Get Hint ({hintsRemaining} remaining)
              </button>

              {/* Evaluations */}
              {evaluations.length > 0 && (
                <div className="evaluations-section">
                  <h3>🤖 Agent Evaluations</h3>
                  {evaluations.map((ev, i) => (
                    <div key={i} className={`eval-card ${ev.agent.toLowerCase()}`}>
                      <div className="eval-agent-badge">{ev.agent.replace('_', ' ')}</div>
                      <p>{ev.content}</p>
                    </div>
                  ))}
                  <div className="next-actions">
                    <button className="btn-secondary" onClick={tryAnotherQuestion}>
                      🔄 Next Question
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="loading-card">
              <div className="spinner"></div>
              <p>Preparing your question...</p>
            </div>
          )}
        </div>

        {/* RIGHT PANEL - Code Editor */}
        <div className="editor-panel">
          <div className="editor-header">
            <span className="editor-title">💻 Code Editor</span>
            <span className="language-badge">Python</span>
          </div>

          <textarea
            ref={codeRef}
            className="code-editor"
            value={code}
            onChange={e => setCode(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="# Write your solution here&#10;&#10;def solution():&#10;    pass"
            spellCheck={false}
          />

          <div className="editor-footer">
            {statusMsg && (
              <p className={`status-msg ${phase === 'evaluating' ? 'loading' : ''}`}>
                {phase === 'evaluating' && <span className="mini-spinner"></span>}
                {statusMsg}
              </p>
            )}
            <button
              className="btn-submit"
              onClick={submitAnswer}
              disabled={isLoading || phase === 'evaluating' || !code.trim()}
            >
              {phase === 'evaluating' ? '⏳ Evaluating...' : '🚀 Submit Solution'}
            </button>
          </div>
        </div>
      </div>

      {/* Live Messages Feed */}
      {messages.length > 0 && (
        <div className="messages-feed">
          <h3>🔴 Live Agent Activity</h3>
          <div className="messages-list">
            {messages.slice(-3).map((msg, i) => (
              <div key={i} className="message-item">
                <span className="msg-agent">{msg.sender}</span>
                <span className="msg-content">{msg.content.substring(0, 100)}...</span>
                <span className="msg-confidence">{Math.round((msg.confidence || 0) * 100)}%</span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}
    </div>
  )
}