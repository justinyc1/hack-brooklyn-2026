import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import Editor from '@monaco-editor/react'
import { cn } from '@/lib/cn'
import { apiFetch } from '@/lib/api'
import type { ApiFeedbackReport, ApiSession, ApiCodeSnapshot } from '@/lib/apiTypes'

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const fadeUp = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } } }

interface MetricScore { label: string; score: number; max: number }
interface QuestionFeedbackUI {
  questionId: string
  questionText: string
  score: number
  evidenceSpans: { text: string; context: string }[]
  strengths: string[]
  improvements: string[]
  betterAnswer?: string
}
interface DrillUI { title: string; description: string; type: string }

function categoryLabel(key: string): string {
  const map: Record<string, string> = {
    clarity: 'Clarity', confidence: 'Confidence', conciseness: 'Conciseness',
    structure: 'Structure', specificity: 'Specificity', pace: 'Pace',
    problem_solving: 'Problem Solving', code_correctness: 'Correctness',
    optimization_awareness: 'Optimization', star_structure: 'STAR',
    impact_articulation: 'Impact', ownership: 'Ownership',
  }
  return map[key] ?? key.replace(/_/g, ' ')
}

function metricsFromCategories(cats: ApiFeedbackReport['category_scores']): MetricScore[] {
  return (Object.entries(cats) as [string, number | null][])
    .filter(([, v]) => v != null)
    .map(([k, v]) => ({ label: categoryLabel(k), score: Math.round((v ?? 0) * 10), max: 100 }))
}

function drillsFromStrings(raw: string[]): DrillUI[] {
  return raw.map((d) => {
    const text = d.replace(/^Practice:\s*/i, '')
    return { title: text, description: `Work on: ${text}`, type: 'Communication' }
  })
}

function MetricRing({ label, score, max }: MetricScore) {
  const pct = score / max
  const r = 32
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct)
  const color = pct >= 0.75 ? '#7E9E5C' : pct >= 0.55 ? '#FF6B35' : '#B23A3A'
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-20 w-20">
        <svg className="-rotate-90" width="80" height="80" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r={r} fill="none" stroke="rgba(250,247,242,0.06)" strokeWidth="4" />
          <motion.circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="4"
            strokeDasharray={circ} initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }} transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
            strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-mono text-sm font-medium text-paper">{score}</span>
        </div>
      </div>
      <p className="font-mono text-[10px] uppercase tracking-widest text-paper-faint">{label}</p>
    </div>
  )
}

function QuestionAccordion({ qf, idx }: { qf: QuestionFeedbackUI; idx: number }) {
  const [open, setOpen] = useState(idx === 0)
  return (
    <div className={cn('rounded-md border transition-all duration-200', open ? 'border-ember/20 bg-ink-900' : 'border-ink-700/60 bg-ink-900 hover:border-ink-600')}>
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between p-5 text-left">
        <div className="flex items-center gap-4">
          <span className="font-mono text-xs text-paper-faint">Q{String(idx + 1).padStart(2, '0')}</span>
          <p className="text-sm font-medium text-paper line-clamp-1">{qf.questionText}</p>
        </div>
        <div className="flex items-center gap-3 ml-4 shrink-0">
          <span className={cn('font-mono text-sm font-semibold', qf.score >= 75 ? 'text-moss' : qf.score >= 55 ? 'text-ember' : 'text-crimson')}>{qf.score}</span>
          <span className={cn('font-mono text-xs text-paper-faint transition-transform duration-200', open && 'rotate-180')}>▾</span>
        </div>
      </button>
      {open && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}
          className="border-t border-ink-700/50 p-5 space-y-5">
          {qf.evidenceSpans.length > 0 && (
            <div>
              <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-paper-faint">Evidence from your answer</p>
              <div className="space-y-2">
                {qf.evidenceSpans.map((span, i) => (
                  <div key={i} className="rounded-sm border-l-2 border-ember/50 bg-ember/5 px-4 py-3">
                    <p className="mb-1 text-sm text-paper italic">"{span.text}"</p>
                    {span.context && <p className="font-mono text-[10px] text-paper-faint">{span.context}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-moss">Strengths</p>
              <ul className="space-y-1.5">
                {qf.strengths.map((s, i) => <li key={i} className="flex gap-2 text-sm text-paper-dim"><span className="text-moss shrink-0">+</span>{s}</li>)}
              </ul>
            </div>
            <div>
              <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-crimson">Improve</p>
              <ul className="space-y-1.5">
                {qf.improvements.map((s, i) => <li key={i} className="flex gap-2 text-sm text-paper-dim"><span className="text-crimson shrink-0">△</span>{s}</li>)}
              </ul>
            </div>
          </div>
          {qf.betterAnswer && (
            <div>
              <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-paper-faint">Stronger answer</p>
              <p className="rounded-sm border border-ink-700/50 bg-ink-800 px-4 py-3 text-sm leading-relaxed text-paper-dim italic">"{qf.betterAnswer}"</p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}

function CodeTimeline({ snapshots, idx, onIdxChange }: {
  snapshots: ApiCodeSnapshot[]
  idx: number
  onIdxChange: (i: number) => void
}) {
  const snap = snapshots[idx]
  if (!snap) return null

  const ts = new Date(snap.timestamp)
  const timeLabel = ts.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  return (
    <div className="rounded-md border border-ink-700/60 bg-ink-900 overflow-hidden">
      <div className="flex items-center justify-between border-b border-ink-700/60 px-5 py-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-paper-faint">Code Timeline</p>
          <p className="mt-0.5 font-mono text-xs text-paper-dim">
            Snapshot {idx + 1} of {snapshots.length} · {snap.language} · {timeLabel}
          </p>
        </div>
        <span className="font-mono text-[10px] text-paper-faint/60">{snapshots.length} snapshots</span>
      </div>

      <div className="px-5 py-3 border-b border-ink-700/60">
        <input
          type="range"
          min={0}
          max={snapshots.length - 1}
          value={idx}
          onChange={(e) => onIdxChange(Number(e.target.value))}
          className="w-full accent-ember cursor-pointer"
        />
        <div className="mt-1 flex justify-between font-mono text-[9px] text-paper-faint/50">
          <span>Start</span>
          <span>End</span>
        </div>
      </div>

      <div style={{ height: 320 }}>
        <Editor
          height="100%"
          language={snap.language === 'cpp' ? 'cpp' : snap.language}
          value={snap.code}
          theme="vs-dark"
          options={{
            readOnly: true,
            fontSize: 12,
            fontFamily: '"JetBrains Mono", monospace',
            lineHeight: 1.6,
            padding: { top: 12, bottom: 12 },
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: 'none',
            cursorWidth: 0,
          }}
        />
      </div>
    </div>
  )
}

export function Feedback() {
  const { id: sessionId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { getToken } = useAuth()
  const [report, setReport] = useState<ApiFeedbackReport | null>(null)
  const [session, setSession] = useState<ApiSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [pollCount, setPollCount] = useState(0)
  const [snapshots, setSnapshots] = useState<ApiCodeSnapshot[]>([])
  const [snapshotIdx, setSnapshotIdx] = useState(0)
  const [loadingSnapshots, setLoadingSnapshots] = useState(false)

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false

    async function fetchFeedback() {
      try {
        const token = await getToken()
        if (!token || cancelled) return
        const [feedbackData, sessionData] = await Promise.all([
          apiFetch<ApiFeedbackReport>(`/api/feedback/${sessionId}`, token),
          apiFetch<ApiSession>(`/api/interviews/${sessionId}`, token).catch(() => null)
        ])
        if (!cancelled) {
          setReport(feedbackData)
          setSession(sessionData)
          setLoading(false)

          if (sessionData?.mode === 'technical') {
            setLoadingSnapshots(true)
            try {
              const snaps = await apiFetch<ApiCodeSnapshot[]>(
                `/api/interviews/${sessionId}/code/snapshots`,
                token
              )
              setSnapshots(snaps ?? [])
              setSnapshotIdx(Math.max(0, (snaps?.length ?? 1) - 1))
            } catch {
              // snapshots optional
            } finally {
              setLoadingSnapshots(false)
            }
          }
        }
      } catch {
        // 404 means not ready yet — retry is scheduled by the timeout effect
      }
    }

    fetchFeedback()
    return () => { cancelled = true }
  }, [sessionId, getToken, pollCount])

  useEffect(() => {
    if (!loading) return
    if (pollCount >= 40) {
      setTimeout(() => setLoading(false), 0)
      return
    }
    const id = setTimeout(() => setPollCount((n) => n + 1), 3000)
    return () => clearTimeout(id)
  }, [pollCount, loading])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-paper-faint mb-2">Generating feedback</p>
          <p className="font-mono text-[10px] text-paper-faint/60">This takes a few seconds...</p>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="font-mono text-xs text-crimson">Feedback unavailable.</p>
          <button onClick={() => navigate('/history')} className="mt-4 font-mono text-xs text-ember">← Back to history</button>
        </div>
      </div>
    )
  }

  const overallScore = Math.round(report.overall_score * 10)
  const scoreColor = overallScore >= 75 ? 'text-moss' : overallScore >= 55 ? 'text-ember' : 'text-crimson'
  const metrics = metricsFromCategories(report.category_scores)
  const drills = drillsFromStrings(report.targeted_drills)

  const perQuestion: QuestionFeedbackUI[] = report.per_question_feedback.map((qf, idx) => ({
    questionId: qf.question_id,
    questionText: qf.question_text ?? `Question ${idx + 1}`,
    score: Math.round(qf.score * 10),
    evidenceSpans: qf.evidence.map((e) => ({ text: e.quote, context: e.note })),
    strengths: qf.strengths,
    improvements: qf.improvements,
    betterAnswer: qf.better_answer_example ?? undefined,
  }))

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <motion.div variants={stagger} initial="hidden" animate="show">
        <motion.div variants={fadeUp} className="mb-10">
          <p className="mb-2 font-mono text-xs uppercase tracking-widest text-paper-faint">
            Session · {new Date(report.generated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </p>
          <h1 className="font-display text-4xl font-semibold text-paper md:text-5xl">Interview Feedback</h1>
        </motion.div>

        <motion.div variants={fadeUp} className="mb-8 rounded-md border border-ink-700/60 bg-ink-900 p-8">
          <div className="flex flex-col items-start gap-8 sm:flex-row sm:items-center">
            <div>
              <p className="mb-1 font-mono text-xs uppercase tracking-widest text-paper-faint">Overall score</p>
              <p className={cn('font-display text-7xl font-semibold leading-none', scoreColor)}>{overallScore}</p>
              <p className="mt-1 font-mono text-xs text-paper-faint">/ 100</p>
            </div>
            <div className="h-px w-full bg-ink-700/60 sm:h-20 sm:w-px" />
            <div className="flex flex-wrap gap-8">
              {metrics.map((m) => <MetricRing key={m.label} {...m} />)}
            </div>
          </div>
        </motion.div>

        <motion.div variants={fadeUp} className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-md border border-moss/20 bg-moss/5 p-5">
            <p className="mb-4 font-mono text-[10px] uppercase tracking-widest text-moss">Top strengths</p>
            <ul className="space-y-2">
              {report.top_strengths.map((s, i) => <li key={i} className="flex gap-2 text-sm text-paper-dim"><span className="text-moss shrink-0">✓</span>{s}</li>)}
            </ul>
          </div>
          <div className="rounded-md border border-crimson/20 bg-crimson/5 p-5">
            <p className="mb-4 font-mono text-[10px] uppercase tracking-widest text-crimson">Areas to improve</p>
            <ul className="space-y-2">
              {report.top_weaknesses.map((w, i) => <li key={i} className="flex gap-2 text-sm text-paper-dim"><span className="text-crimson shrink-0">△</span>{w}</li>)}
            </ul>
          </div>
        </motion.div>

        {perQuestion.length > 0 && (
          <motion.div variants={fadeUp} className="mb-8">
            <p className="mb-4 font-mono text-xs uppercase tracking-widest text-paper-faint">Question breakdown</p>
            <div className="space-y-3">
              {perQuestion.map((qf, i) => <QuestionAccordion key={qf.questionId} qf={qf} idx={i} />)}
            </div>
          </motion.div>
        )}

        {drills.length > 0 && (
          <motion.div variants={fadeUp} className="mb-10">
            <p className="mb-4 font-mono text-xs uppercase tracking-widest text-paper-faint">AREAS TO IMPROVE</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {drills.map((d, i) => (
                <div key={i} className="rounded-md border border-ink-700/60 bg-ink-900 p-5">
                  <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-ember">{d.type}</p>
                  <p className="mb-2 font-display text-sm font-semibold text-paper">{d.title}</p>
                  <p className="text-xs leading-relaxed text-paper-dim">{d.description}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {snapshots.length > 0 && (
          <motion.div variants={fadeUp} className="mb-8">
            <p className="mb-4 font-mono text-xs uppercase tracking-widest text-paper-faint">Code Evolution</p>
            {loadingSnapshots ? (
              <p className="font-mono text-xs text-paper-faint/60 animate-pulse">Loading snapshots...</p>
            ) : (
              <CodeTimeline snapshots={snapshots} idx={snapshotIdx} onIdxChange={setSnapshotIdx} />
            )}
          </motion.div>
        )}

        <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-4">
          {session?.audio_s3_url ? (
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-widest text-paper-faint">Session Audio</span>
              <audio controls src={session.audio_s3_url} className="h-10 rounded-sm" />
            </div>
          ) : (
            <button
              onClick={() => toast.info('Audio replay not available for this session')}
              className="flex items-center gap-2 rounded-sm border border-ink-700/60 px-4 py-2 font-mono text-xs text-paper-faint hover:border-paper-faint/30 hover:text-paper-dim transition-all duration-200"
            >
              ▶ Replay session audio
            </button>
          )}
          <button onClick={() => navigate('/setup')} className="flex items-center gap-2 rounded-sm bg-ember px-5 py-2 font-mono text-xs text-ink-950 hover:bg-ember-soft transition-all duration-200">
            Practice again →
          </button>
          <button onClick={() => navigate('/history')} className="font-mono text-xs text-paper-faint hover:text-paper-dim transition-colors border-b border-transparent hover:border-paper-faint/30 pb-px">
            View all sessions →
          </button>
        </motion.div>
      </motion.div>
    </div>
  )
}
