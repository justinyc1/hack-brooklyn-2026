import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/cn'
import { companies } from '@/lib/mock/companies'
import { personas } from '@/lib/mock/personas'
import { apiFetch } from '@/lib/api'
import type { ApiSession } from '@/lib/apiTypes'
import type { InterviewMode, Difficulty, InterviewerPersona } from '@/lib/types'

interface SetupState {
  role: string
  company: string
  mode: InterviewMode | ''
  difficulty: Difficulty | ''
  durationMinutes: number
  persona: InterviewerPersona | ''
}

const ROLES = [
  { id: 'intern', label: 'SWE Intern', hint: 'Data structures, algorithms, behavioral' },
  { id: 'new-grad', label: 'New Grad SWE', hint: 'Core SWE loop, system design intro' },
  { id: 'mid', label: 'Mid-Level SWE', hint: 'System design, technical depth, ownership' },
  { id: 'senior', label: 'Senior SWE', hint: 'System design, leadership, execution' },
]

const MODES = [
  { id: 'technical' as InterviewMode, label: 'Technical', hint: 'LeetCode-style coding with voice interviewer' },
  { id: 'behavioral' as InterviewMode, label: 'Behavioral', hint: 'Voice-led STAR questions and follow-ups' },
  { id: 'mixed' as InterviewMode, label: 'Mixed', hint: 'Both: behavioral then technical' },
]

const DIFFICULTIES = [
  { id: 'easy' as Difficulty, label: 'Easy', hint: 'Fundamentals, warm-up' },
  { id: 'medium' as Difficulty, label: 'Medium', hint: 'Standard FAANG screen' },
  { id: 'hard' as Difficulty, label: 'Hard', hint: 'Senior/staff level depth' },
]

const DURATIONS = [
  { mins: 20, label: '20 min', hint: 'Quick warm-up' },
  { mins: 30, label: '30 min', hint: 'Short screen' },
  { mins: 45, label: '45 min', hint: 'Standard session' },
  { mins: 60, label: '60 min', hint: 'Full loop round' },
]

const STEPS = [
  { id: 1, label: '01', title: 'Your role', subtitle: "What level are you interviewing for?" },
  { id: 2, label: '02', title: 'Company', subtitle: "Which company should we tailor this for?" },
  { id: 3, label: '03', title: 'Interview type', subtitle: "What kind of session do you want?" },
  { id: 4, label: '04', title: 'Difficulty', subtitle: "How hard should we push you?" },
  { id: 5, label: '05', title: 'Duration', subtitle: "How much time do you have?" },
  { id: 6, label: '06', title: 'Interviewer', subtitle: "Choose your interviewer's persona." },
]

function OptionCard({
  selected,
  onClick,
  label,
  hint,
  tag,
}: {
  selected: boolean
  onClick: () => void
  label: string
  hint?: string
  tag?: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'group w-full rounded-md border p-5 text-left transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ember focus-visible:outline-offset-2',
        selected
          ? 'border-ember/60 bg-ember/8 shadow-ember-sm'
          : 'border-ink-700/70 bg-ink-900 hover:border-ink-600 hover:bg-ink-800/60'
      )}
    >
      {tag && (
        <p className={cn('mb-2 font-mono text-[10px] uppercase tracking-widest', selected ? 'text-ember' : 'text-paper-faint')}>
          {tag}
        </p>
      )}
      <p className={cn('font-display text-base font-semibold', selected ? 'text-paper' : 'text-paper-dim group-hover:text-paper')}>
        {label}
      </p>
      {hint && <p className="mt-1 text-sm text-paper-faint">{hint}</p>}
    </button>
  )
}

const slideVariants = {
  enter: { opacity: 0, x: 32 },
  center: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" } },
  exit: { opacity: 0, x: -24, transition: { duration: 0.2 } },
}

export function Setup() {
  const navigate = useNavigate()
  const { getToken } = useAuth()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [state, setState] = useState<SetupState>({
    role: '',
    company: '',
    mode: '',
    difficulty: '',
    durationMinutes: 45,
    persona: '',
  })

  const canAdvance = () => {
    if (step === 1) return !!state.role
    if (step === 2) return !!state.company
    if (step === 3) return !!state.mode
    if (step === 4) return !!state.difficulty
    if (step === 5) return !!state.durationMinutes
    if (step === 6) return !!state.persona
    return false
  }

  const handleStart = async () => {
    if (loading) return
    setLoading(true)
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')
      const roleLabel = ROLES.find((r) => r.id === state.role)?.label ?? state.role
      const companyName = companies.find((c) => c.id === state.company)?.name ?? state.company
      const session = await apiFetch<ApiSession>('/api/interviews', token, {
        method: 'POST',
        body: JSON.stringify({
          mode: state.mode,
          role: roleLabel,
          company: companyName,
          difficulty: state.difficulty,
          duration_minutes: state.durationMinutes,
          interviewer_tone: state.persona,
        }),
      })
      if (session.mode === 'technical' || session.mode === 'mixed') {
        navigate(`/interview/${session.id}/technical`)
      } else {
        navigate(`/interview/${session.id}/behavioral`)
      }
    } catch (err) {
      toast.error('Failed to create session. Is the backend running?')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const currentStepMeta = STEPS[step - 1]

  return (
    <div className="min-h-screen bg-ink-950 py-12 px-6">
      <div className="mx-auto max-w-5xl">
        {/* Progress bar */}
        <div className="mb-10 flex items-center gap-4">
          <span className="font-mono text-xs text-paper-faint">{currentStepMeta.label} / 06</span>
          <div className="flex-1 h-px bg-ink-700">
            <motion.div
              className="h-px bg-ember"
              animate={{ width: `${((step - 1) / 5) * 100}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
          <button
            onClick={() => navigate('/')}
            className="font-mono text-xs text-paper-faint hover:text-paper-dim transition-colors"
          >
            ✕ Cancel
          </button>
        </div>

        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[1fr_280px]">
          {/* Main step content */}
          <div>
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
              >
                <p className="mb-1 font-mono text-xs uppercase tracking-widest text-ember">{currentStepMeta.label}</p>
                <h2 className="mb-2 font-display text-3xl font-semibold text-paper">{currentStepMeta.title}</h2>
                <p className="mb-8 text-paper-dim">{currentStepMeta.subtitle}</p>

                {step === 1 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {ROLES.map((r) => (
                      <OptionCard
                        key={r.id}
                        selected={state.role === r.id}
                        onClick={() => setState((s) => ({ ...s, role: r.id }))}
                        label={r.label}
                        hint={r.hint}
                      />
                    ))}
                  </div>
                )}

                {step === 2 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {companies.map((c) => (
                      <OptionCard
                        key={c.id}
                        selected={state.company === c.id}
                        onClick={() => setState((s) => ({ ...s, company: c.id }))}
                        label={c.name}
                        hint={c.behavioralThemes.slice(0, 2).join(' · ')}
                      />
                    ))}
                  </div>
                )}

                {step === 3 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    {MODES.map((m) => (
                      <OptionCard
                        key={m.id}
                        selected={state.mode === m.id}
                        onClick={() => setState((s) => ({ ...s, mode: m.id }))}
                        label={m.label}
                        hint={m.hint}
                      />
                    ))}
                  </div>
                )}

                {step === 4 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    {DIFFICULTIES.map((d) => (
                      <OptionCard
                        key={d.id}
                        selected={state.difficulty === d.id}
                        onClick={() => setState((s) => ({ ...s, difficulty: d.id }))}
                        label={d.label}
                        hint={d.hint}
                      />
                    ))}
                  </div>
                )}

                {step === 5 && (
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {DURATIONS.map((d) => (
                      <OptionCard
                        key={d.mins}
                        selected={state.durationMinutes === d.mins}
                        onClick={() => setState((s) => ({ ...s, durationMinutes: d.mins }))}
                        label={d.label}
                        hint={d.hint}
                      />
                    ))}
                  </div>
                )}

                {step === 6 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {personas.map((p) => (
                      <OptionCard
                        key={p.id}
                        selected={state.persona === p.id}
                        onClick={() => setState((s) => ({ ...s, persona: p.id }))}
                        label={p.name}
                        hint={p.description}
                        tag={p.id}
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

            {/* Navigation */}
            <div className="mt-10 flex items-center gap-4">
              {step > 1 && (
                <button
                  onClick={() => setStep((s) => s - 1)}
                  className="font-mono text-xs uppercase tracking-widest text-paper-faint hover:text-paper-dim transition-colors border-b border-transparent hover:border-paper-faint/30 pb-px"
                >
                  ← Back
                </button>
              )}
              <div className="flex-1" />
              {step < 6 ? (
                <button
                  onClick={() => canAdvance() && setStep((s) => s + 1)}
                  disabled={!canAdvance()}
                  className={cn(
                    'flex items-center gap-3 rounded-sm px-6 py-3 font-mono text-sm uppercase tracking-widest transition-all duration-200',
                    canAdvance()
                      ? 'bg-ember text-ink-950 hover:bg-ember-soft active:scale-[0.97]'
                      : 'bg-ink-800 text-paper-faint cursor-not-allowed'
                  )}
                >
                  Continue →
                </button>
              ) : (
                <button
                  onClick={handleStart}
                  disabled={!canAdvance() || loading}
                  className={cn(
                    'flex items-center gap-3 rounded-sm px-8 py-3 font-mono text-sm uppercase tracking-widest transition-all duration-200',
                    canAdvance() && !loading
                      ? 'bg-ember text-ink-950 hover:bg-ember-soft active:scale-[0.97]'
                      : 'bg-ink-800 text-paper-faint cursor-not-allowed'
                  )}
                >
                  {loading ? 'Creating...' : 'Start interview →'}
                </button>
              )}
            </div>
          </div>

          {/* Summary rail */}
          <aside className="hidden lg:block">
            <div className="sticky top-24 rounded-md border border-ink-700/60 bg-ink-900 p-5">
              <p className="mb-4 font-mono text-[10px] uppercase tracking-widest text-paper-faint">Your session</p>
              <div className="space-y-3">
                {[
                  { label: 'Role', value: state.role ? ROLES.find((r) => r.id === state.role)?.label : null },
                  { label: 'Company', value: state.company ? companies.find((c) => c.id === state.company)?.name : null },
                  { label: 'Mode', value: state.mode ? state.mode.charAt(0).toUpperCase() + state.mode.slice(1) : null },
                  { label: 'Difficulty', value: state.difficulty ? state.difficulty.charAt(0).toUpperCase() + state.difficulty.slice(1) : null },
                  { label: 'Duration', value: state.durationMinutes ? `${state.durationMinutes} min` : null },
                  { label: 'Interviewer', value: state.persona ? personas.find((p) => p.id === state.persona)?.name : null },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-paper-faint">{label}</span>
                    <span className={cn('font-mono text-xs', value ? 'text-paper' : 'text-paper-faint/40')}>
                      {value ?? '—'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
