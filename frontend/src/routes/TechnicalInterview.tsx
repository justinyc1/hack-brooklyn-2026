import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import Editor from '@monaco-editor/react'
import { Conversation } from '@11labs/client'
import type { Status } from '@11labs/client'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { cn } from '@/lib/cn'
import { apiFetch } from '@/lib/api'
import type { ApiSession, ApiQuestion, ApiCodeRunResult, ApiAgentUrl } from '@/lib/apiTypes'
import type { Language } from '@/lib/types'

const LANGUAGES: { id: Language; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'javascript', label: 'JS' },
  { id: 'java', label: 'Java' },
  { id: 'cpp', label: 'C++' },
  { id: 'go', label: 'Go' },
]

function useCountdown(initialSeconds: number) {
  const [seconds, setSeconds] = useState(initialSeconds)
  useEffect(() => {
    if (seconds <= 0) return
    const id = setInterval(() => setSeconds((s) => s - 1), 1000)
    return () => clearInterval(id)
  }, [seconds])
  const mm = String(Math.floor(seconds / 60)).padStart(2, '0')
  const ss = String(seconds % 60).padStart(2, '0')
  return { timeStr: `${mm}:${ss}`, seconds }
}

function TimerRing({ timeStr, totalSecs, remainSecs }: { timeStr: string; totalSecs: number; remainSecs: number }) {
  const pct = remainSecs / totalSecs
  const r = 28
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct)
  const color = pct > 0.4 ? '#FF6B35' : '#B23A3A'
  return (
    <div className="relative flex h-20 w-20 items-center justify-center">
      <svg className="absolute inset-0 -rotate-90" width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="rgba(250,247,242,0.06)" strokeWidth="3" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="3"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.5s' }} />
      </svg>
      <span className="font-mono text-xs text-paper">{timeStr}</span>
    </div>
  )
}

interface TestResultUI {
  id: string
  input: string
  expected: string
  actual?: string
  passed?: boolean
}

interface TranscriptLine { speaker: 'ai' | 'user'; text: string }

export function TechnicalInterview() {
  const { id: sessionId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { getToken } = useAuth()

  const [session, setSession] = useState<ApiSession | null>(null)
  const [question, setQuestion] = useState<ApiQuestion | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [language, setLanguage] = useState<Language>('python')
  const [code, setCode] = useState('')
  const [showTests, setShowTests] = useState(false)
  const [testResults, setTestResults] = useState<TestResultUI[]>([])
  const [running, setRunning] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [connecting, setConnecting] = useState(true)
  const [interviewerSpeaking, setInterviewerSpeaking] = useState(false)
  const [muted, setMuted] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptLine[]>([])

  const convRef = useRef<Awaited<ReturnType<typeof Conversation.startSession>> | null>(null)
  const transcriptRef = useRef<HTMLDivElement>(null)

  const totalSecs = (session?.duration_minutes ?? 45) * 60
  const { timeStr, seconds: remainSecs } = useCountdown(totalSecs)

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [transcript])

  // Load session + questions + start ElevenLabs on mount
  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    async function load() {
      try {
        const token = await getToken()
        if (!token) return
        const [sess, questions, agentUrl] = await Promise.all([
          apiFetch<ApiSession>(`/api/interviews/${sessionId}`, token),
          apiFetch<ApiQuestion[]>(`/api/interviews/${sessionId}/questions`, token),
          apiFetch<ApiAgentUrl>(`/api/interviews/${sessionId}/agent-url`, token),
        ])
        if (cancelled) return
        setSession(sess)

        const techQ = questions.find((q) => q.type === 'technical') ?? null
        setQuestion(techQ)
        if (techQ?.problem?.starter_code?.['python']) {
          setCode(techQ.problem.starter_code['python'])
        }

        // Mark session active
        if (sess.status === 'pending') {
          await apiFetch(`/api/interviews/${sessionId}`, token, {
            method: 'PATCH',
            body: JSON.stringify({ status: 'active' }),
          })
        }

        const conversation = await Conversation.startSession({
          signedUrl: agentUrl.signed_url,
          onMessage: ({ message, source }: { message: string; source: 'ai' | 'user' }) => {
            setTranscript((t) => [...t, { speaker: source, text: message }])
          },
          onModeChange: ({ mode }: { mode: 'speaking' | 'listening' }) => {
            setInterviewerSpeaking(mode === 'speaking')
          },
          onStatusChange: ({ status }: { status: Status }) => {
            if (status === 'connected') setConnecting(false)
          },
          onError: (message: string, context?: unknown) => {
            console.error('ElevenLabs error', message, context)
          },
        })

        if (cancelled) {
          await conversation.endSession()
          return
        }

        convRef.current = conversation
        const convId = conversation.getId()

        if (convId) {
          const t = await getToken()
          if (t) {
            await apiFetch(`/api/interviews/${sessionId}`, t, {
              method: 'PATCH',
              body: JSON.stringify({ elevenlabs_conversation_id: convId }),
            })
          }
        }

        setConnecting(false)
      } catch (err) {
        if (!cancelled) {
          setLoadError('Failed to load session.')
          setConnecting(false)
        }
        console.error(err)
      }
    }
    load()
    return () => {
      cancelled = true
      convRef.current?.endSession().catch(() => {})
    }
  }, [sessionId, getToken])

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang)
    const starter = question?.problem?.starter_code?.[lang] ?? ''
    setCode(starter)
  }

  const handleRun = async () => {
    if (!sessionId || !question?.coding_problem_id || running) return
    setRunning(true)
    setShowTests(true)
    try {
      const token = await getToken()
      if (!token) return
      const result = await apiFetch<ApiCodeRunResult>(
        `/api/interviews/${sessionId}/code/run`,
        token,
        {
          method: 'POST',
          body: JSON.stringify({ language, code, question_id: question.id }),
        }
      )
      setTestResults(
        result.test_results.map((tr) => ({
          id: tr.test_case_id,
          input: '',
          expected: '',
          actual: tr.stdout ?? tr.stderr ?? '',
          passed: tr.passed,
        }))
      )
    } catch (err) {
      console.error('Run failed', err)
    } finally {
      setRunning(false)
    }
  }

  const handleSubmit = async () => {
    if (!sessionId || !question?.coding_problem_id || submitting) return
    setSubmitting(true)
    setShowTests(true)
    try {
      const token = await getToken()
      if (!token) return
      const result = await apiFetch<ApiCodeRunResult>(
        `/api/interviews/${sessionId}/code/submit`,
        token,
        {
          method: 'POST',
          body: JSON.stringify({ language, code, question_id: question.id }),
        }
      )
      setTestResults(
        result.test_results.map((tr) => ({
          id: tr.test_case_id,
          input: '',
          expected: '',
          actual: tr.stdout ?? tr.stderr ?? '',
          passed: tr.passed,
        }))
      )
      await endSession(token)
    } catch (err) {
      console.error('Submit failed', err)
    } finally {
      setSubmitting(false)
    }
  }

  const endSession = async (tokenArg?: string) => {
    if (!sessionId) return
    try {
      await convRef.current?.endSession()
      const token = tokenArg ?? (await getToken())
      if (!token) return
      await apiFetch(`/api/interviews/${sessionId}`, token, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'completed' }),
      })
    } catch (err) {
      console.error('PATCH completed failed', err)
      toast.error('Session may not have saved. Feedback generation could be delayed.')
    }
    navigate(`/feedback/${sessionId}`)
  }

  if (loadError) {
    return (
      <div className="flex h-screen items-center justify-center bg-ink-950">
        <p className="font-mono text-xs text-crimson">{loadError}</p>
      </div>
    )
  }

  const problem = question?.problem
  const persona = session?.interviewer_tone ?? 'neutral'
  const personaInitial = persona.charAt(0).toUpperCase()

  return (
    <div className="flex h-screen flex-col bg-ink-950 overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-ink-700/60 bg-ink-900 px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-ember">◆</span>
          <span className="font-display text-sm font-semibold text-paper">Intervue</span>
          <span className="font-mono text-xs text-paper-faint ml-2">
            Technical{session?.company ? ` · ${session.company}` : ''}
          </span>
        </div>
        <button
          onClick={() => endSession()}
          className="font-mono text-xs uppercase tracking-widest text-paper-faint hover:text-crimson transition-colors border border-ink-700/60 px-3 py-1 rounded-sm hover:border-crimson/40"
        >
          End session
        </button>
      </div>

      {/* Three-pane layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Pane 1: Problem */}
        <div className="flex w-[320px] shrink-0 flex-col overflow-y-auto border-r border-ink-700/60 bg-ink-900 p-5">
          {!problem ? (
            <p className="font-mono text-xs text-paper-faint animate-pulse">Loading problem...</p>
          ) : (
            <>
              <div className="mb-1 flex items-center gap-2">
                <span className={cn(
                  'rounded-sm px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest',
                  problem.difficulty === 'easy' ? 'bg-moss/15 text-moss' :
                  problem.difficulty === 'medium' ? 'bg-ember/15 text-ember' :
                  'bg-crimson/15 text-crimson'
                )}>
                  {problem.difficulty}
                </span>
              </div>
              <h2 className="mb-4 font-display text-xl font-semibold text-paper">{problem.title}</h2>
              <div className="prose-sm text-sm leading-relaxed text-paper-dim space-y-4">
                <p className="text-paper-dim whitespace-pre-line">{problem.description}</p>
                <div className="space-y-3">
                  {problem.examples.map((ex, i) => (
                    <div key={i} className="rounded-sm border border-ink-700/50 bg-ink-800 p-3">
                      <p className="font-mono text-[10px] uppercase tracking-widest text-paper-faint mb-2">Example {i + 1}</p>
                      <p className="font-mono text-xs text-paper-dim"><span className="text-paper-faint">Input:</span> {ex.input}</p>
                      <p className="font-mono text-xs text-paper-dim"><span className="text-paper-faint">Output:</span> {ex.output}</p>
                      {ex.explanation && <p className="mt-1 text-xs text-paper-faint">{ex.explanation}</p>}
                    </div>
                  ))}
                </div>
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-widest text-paper-faint mb-2">Constraints</p>
                  <ul className="space-y-1">
                    {problem.constraints.map((c, i) => (
                      <li key={i} className="font-mono text-xs text-paper-dim flex gap-2"><span className="text-paper-faint">·</span>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Pane 2: Editor */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex items-center gap-2 border-b border-ink-700/60 bg-ink-900 px-3 py-2">
            <div className="flex items-center gap-1">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.id}
                  onClick={() => handleLanguageChange(lang.id)}
                  className={cn(
                    'rounded-sm px-2.5 py-1 font-mono text-xs transition-all duration-150',
                    language === lang.id
                      ? 'bg-ember/15 text-ember border border-ember/30'
                      : 'text-paper-faint hover:text-paper-dim border border-transparent'
                  )}
                >
                  {lang.label}
                </button>
              ))}
            </div>
            <div className="ml-auto flex items-center gap-2">
              <button
                onClick={handleRun}
                disabled={running}
                className="flex items-center gap-1.5 rounded-sm border border-ink-700/60 bg-ink-800 px-3 py-1.5 font-mono text-xs text-paper-dim hover:border-paper-faint/30 hover:text-paper transition-all disabled:opacity-50"
              >
                {running ? '...' : '▶ Run'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex items-center gap-1.5 rounded-sm bg-ember px-3 py-1.5 font-mono text-xs text-ink-950 hover:bg-ember-soft transition-all disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit →'}
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              language={language === 'cpp' ? 'cpp' : language}
              value={code}
              onChange={(val) => setCode(val ?? '')}
              theme="vs-dark"
              options={{
                fontSize: 13,
                fontFamily: '"JetBrains Mono", monospace',
                fontLigatures: true,
                lineHeight: 1.7,
                padding: { top: 16, bottom: 16 },
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                renderLineHighlight: 'all',
                cursorBlinking: 'smooth',
                smoothScrolling: true,
                tabSize: 4,
              }}
            />
          </div>

          <AnimatePresence>
            {showTests && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden border-t border-ink-700/60 bg-ink-900"
              >
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-mono text-xs uppercase tracking-widest text-paper-faint">Test Results</p>
                    <button onClick={() => setShowTests(false)} className="font-mono text-xs text-paper-faint hover:text-paper-dim">✕</button>
                  </div>
                  {testResults.length === 0 ? (
                    <p className="font-mono text-xs text-paper-faint animate-pulse">Running...</p>
                  ) : (
                    <div className="space-y-2">
                      {testResults.map((tc) => (
                        <div key={tc.id} className={cn(
                          'flex items-center gap-3 rounded-sm border p-3',
                          tc.passed ? 'border-moss/30 bg-moss/8' : 'border-crimson/30 bg-crimson/8'
                        )}>
                          <span className={cn('font-mono text-xs', tc.passed ? 'text-moss' : 'text-crimson')}>
                            {tc.passed ? '✓ PASS' : '✗ FAIL'}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="font-mono text-xs text-paper-faint">Test case {tc.id}</p>
                            {tc.actual && <p className="font-mono text-xs text-paper-dim truncate">Output: {tc.actual}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Pane 3: Interviewer + Transcript */}
        <div className="flex w-[280px] shrink-0 flex-col border-l border-ink-700/60 bg-ink-900">
          <div className="border-b border-ink-700/60 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-full border border-ink-700/80 bg-ink-800 font-display text-sm font-semibold text-paper">
                {personaInitial}
                {interviewerSpeaking && (
                  <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-ember animate-pulse border border-ink-900" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-paper">AI Interviewer</p>
                <p className="font-mono text-[10px] text-paper-faint capitalize">
                  {connecting ? 'Connecting...' : interviewerSpeaking ? 'Speaking' : persona}
                </p>
              </div>
              {interviewerSpeaking && (
                <div className="ml-auto flex items-center gap-1">
                  {[1, 2, 3].map((i) => (
                    <motion.div
                      key={i}
                      animate={{ scaleY: [1, 2.5, 1] }}
                      transition={{ repeat: Infinity, duration: 0.6, delay: i * 0.15 }}
                      className="h-3 w-0.5 rounded-full bg-ember origin-bottom"
                    />
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={() => {
                const newMuted = !muted
                setMuted(newMuted)
                try { convRef.current?.setVolume?.({ volume: newMuted ? 0 : 1 }) } catch {}
              }}
              className={cn(
                'w-full rounded-sm border px-3 py-1.5 font-mono text-xs uppercase tracking-widest transition-all duration-200',
                muted
                  ? 'border-crimson/40 bg-crimson/10 text-crimson'
                  : 'border-ink-700/60 text-paper-faint hover:border-paper-faint/30 hover:text-paper-dim'
              )}
            >
              {muted ? '⊘ Muted' : '⊙ Mute'}
            </button>
          </div>

          <div ref={transcriptRef} className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth">
            {connecting ? (
              <p className="font-mono text-[10px] text-paper-faint/50 animate-pulse">Connecting to interviewer...</p>
            ) : transcript.length === 0 ? (
              <p className="font-mono text-[10px] text-paper-faint/50">Transcript will appear here...</p>
            ) : (
              transcript.map((seg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.25 }}
                  className="flex gap-2"
                >
                  <span className={cn(
                    'mt-0.5 shrink-0 font-mono text-[9px] font-medium uppercase',
                    seg.speaker === 'ai' ? 'text-paper-faint' : 'text-ember'
                  )}>
                    {seg.speaker === 'ai' ? 'INT' : 'YOU'}
                  </span>
                  <p className="text-xs leading-relaxed text-paper-dim">{seg.text}</p>
                </motion.div>
              ))
            )}
          </div>

          <div className="flex items-center justify-end border-t border-ink-700/60 p-4">
            <TimerRing timeStr={timeStr} totalSecs={totalSecs} remainSecs={remainSecs} />
          </div>
        </div>
      </div>
    </div>
  )
}
