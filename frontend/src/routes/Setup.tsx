import { useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/cn'
import { companies } from '@/lib/mock/companies'
import { personas, behavioralPersonas } from '@/lib/mock/personas'
import { apiFetch, API_BASE } from '@/lib/api'
import type { ApiSession } from '@/lib/apiTypes'
import type { Difficulty, InterviewerPersona, BehavioralPersona } from '@/lib/types'

type InterviewType = 'behavioral' | 'technical' | 'resume' | ''

interface SetupState {
  interviewType: InterviewType
  // Behavioral / Resume path
  behavioralPersona: BehavioralPersona | ''
  // Technical path
  role: string
  company: string
  difficulty: Difficulty | ''
  technicalPersona: InterviewerPersona | ''
  // Shared
  durationMinutes: number | undefined
  // Resume specific
  resumeFile: File | null
  resumeText: string
  resumeS3Url: string
  // Deep-link preset
  problemId: string | undefined
}

const ROLES = [
  { id: 'intern', label: 'Software Engineer Intern', hint: 'Data structures, algorithms, behavioral' },
  { id: 'new-grad', label: 'New Grad SWE', hint: 'Core SWE loop, system design intro' },
  { id: 'mid', label: 'Mid-Level SWE', hint: 'System design, technical depth, ownership' },
  { id: 'senior', label: 'Senior SWE', hint: 'System design, leadership, execution' },
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

const INTERVIEW_TYPES = [
  { id: 'behavioral' as InterviewType, label: 'Behavioral', hint: 'Voice-led STAR questions and follow-ups' },
  { id: 'technical' as InterviewType, label: 'Technical', hint: 'LeetCode-style coding with voice interviewer' },
  { id: 'resume' as InterviewType, label: 'Resume Deep Dive', hint: 'Questions based on your resume' },
]

function totalSteps(interviewType: InterviewType): number {
  if (interviewType === 'behavioral') return 3
  if (interviewType === 'technical') return 6
  if (interviewType === 'resume') return 4
  return 1
}

function stepLabel(step: number, interviewType: InterviewType): { title: string; subtitle: string } {
  if (step === 1) return { title: 'Interview type', subtitle: 'What kind of session do you want?' }
  
  if (interviewType === 'behavioral') {
    if (step === 2) return { title: 'Duration', subtitle: 'How much time do you have?' }
    if (step === 3) return { title: 'Interviewer', subtitle: "Choose your interviewer's style." }
  }
  
  if (interviewType === 'resume') {
    if (step === 2) return { title: 'Upload Resume', subtitle: 'Upload your resume PDF so we can tailor the questions.' }
    if (step === 3) return { title: 'Duration', subtitle: 'How much time do you have?' }
    if (step === 4) return { title: 'Interviewer', subtitle: "Choose your interviewer's style." }
  }

  if (interviewType === 'technical') {
    if (step === 2) return { title: 'Your role', subtitle: "What level are you interviewing for?" }
    if (step === 3) return { title: 'Company', subtitle: "Which company should we tailor this for?" }
    if (step === 4) return { title: 'Difficulty', subtitle: "How hard should we push you?" }
    if (step === 5) return { title: 'Duration', subtitle: "How much time do you have?" }
    if (step === 6) return { title: 'Interviewer', subtitle: "Choose your interviewer's persona." }
  }
  
  return { title: '', subtitle: '' }
}

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
  center: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
  exit: { opacity: 0, x: -24, transition: { duration: 0.2 } },
}

export function Setup() {
  const navigate = useNavigate()
  const { getToken } = useAuth()
  const [searchParams] = useSearchParams()

  const presetType = (searchParams.get('type') ?? '') as InterviewType
  const presetRole = searchParams.get('role') ?? ''
  const presetCompany = searchParams.get('company') ?? ''
  const presetDifficulty = (searchParams.get('difficulty') ?? '') as Difficulty | ''
  const presetProblemId = searchParams.get('problem_id') ?? ''
  const hasPreset = presetType === 'technical' && !!presetRole && !!presetCompany && !!presetDifficulty && !!presetProblemId

  const [step, setStep] = useState(hasPreset ? 5 : 1)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)

  const [state, setState] = useState<SetupState>({
    interviewType: presetType,
    behavioralPersona: '',
    role: presetRole,
    company: presetCompany,
    difficulty: presetDifficulty,
    technicalPersona: '',
    durationMinutes: hasPreset ? 45 : undefined,
    resumeFile: null,
    resumeText: '',
    resumeS3Url: '',
    problemId: presetProblemId || undefined,
  })

  const total = totalSteps(state.interviewType)
  const isFinalStep = step === total

  const canAdvance = (): boolean => {
    if (step === 1) return !!state.interviewType
    
    if (state.interviewType === 'behavioral') {
      if (step === 2) return !!state.durationMinutes
      if (step === 3) return !!state.behavioralPersona
    }
    
    if (state.interviewType === 'resume') {
      if (step === 2) return !!state.resumeFile && !!state.resumeText // Wait for upload to complete
      if (step === 3) return !!state.durationMinutes
      if (step === 4) return !!state.behavioralPersona
    }
    
    if (state.interviewType === 'technical') {
      if (step === 2) return !!state.role
      if (step === 3) return !!state.company
      if (step === 4) return !!state.difficulty
      if (step === 5) return !!state.durationMinutes
      if (step === 6) return !!state.technicalPersona
    }
    return false
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      toast.error('Only PDF files are supported.')
      return
    }
    
    setIsUploading(true)
    setState(s => ({ ...s, resumeFile: file }))
    
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')
      
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${API_BASE}/api/upload/resume`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
      
      if (!response.ok) throw new Error('Upload failed')
      
      const data = await response.json()
      
      setState(s => ({ 
        ...s, 
        resumeText: data.text,
        resumeS3Url: data.s3_url
      }))
      toast.success('Resume parsed successfully!')
      
    } catch (err) {
      console.error(err)
      toast.error('Failed to parse resume.')
      setState(s => ({ ...s, resumeFile: null, resumeText: '', resumeS3Url: '' }))
    } finally {
      setIsUploading(false)
    }
  }

  const handleStart = async () => {
    if (loading) return
    setLoading(true)
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated')

      let session: ApiSession

      if (state.interviewType === 'behavioral') {
        session = await apiFetch<ApiSession>('/api/interviews/behavioral', token, {
          method: 'POST',
          body: JSON.stringify({
            duration_minutes: state.durationMinutes,
            behavioral_persona: state.behavioralPersona,
          }),
        })
      } else if (state.interviewType === 'resume') {
        session = await apiFetch<ApiSession>('/api/interviews', token, {
          method: 'POST',
          body: JSON.stringify({
            mode: 'resume',
            duration_minutes: state.durationMinutes,
            behavioral_persona: state.behavioralPersona,
            role: 'Software Engineer', // default fallback
            resume_text: state.resumeText,
            resume_s3_url: state.resumeS3Url,
          }),
        })
      } else {
        const roleLabel = ROLES.find((r) => r.id === state.role)?.label ?? state.role
        const companyName = companies.find((c) => c.id === state.company)?.name ?? state.company
        session = await apiFetch<ApiSession>('/api/interviews', token, {
          method: 'POST',
          body: JSON.stringify({
            mode: 'technical',
            role: roleLabel,
            company: companyName,
            difficulty: state.difficulty,
            duration_minutes: state.durationMinutes,
            interviewer_tone: state.technicalPersona,
            ...(state.problemId ? { problem_id: state.problemId } : {}),
          }),
        })
      }

      navigate(`/interview/${session.id}/${session.mode === 'behavioral' || session.mode === 'resume' ? 'behavioral' : 'technical'}`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      if (msg.includes('generate-tests') || msg.includes('no test cases')) {
        toast.error('Problem not ready — test cases still generating. Try again in a moment.')
      } else {
        toast.error('Failed to create session')
      }
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const { title, subtitle } = stepLabel(step, state.interviewType)
  const stepNumLabel = String(step).padStart(2, '0')
  const totalLabel = String(total).padStart(2, '0')
  const progressPct = total > 1 ? ((step - 1) / (total - 1)) * 100 : 0

  let summaryRows: { label: string, value: string | null | undefined }[] = []
  
  if (state.interviewType === 'behavioral') {
    summaryRows = [
      { label: 'Type', value: 'Behavioral' },
      { label: 'Duration', value: state.durationMinutes ? `${state.durationMinutes} min` : null },
      { label: 'Interviewer', value: state.behavioralPersona ? behavioralPersonas.find((p) => p.id === state.behavioralPersona)?.name : null },
    ]
  } else if (state.interviewType === 'resume') {
    summaryRows = [
      { label: 'Type', value: 'Resume Deep Dive' },
      { label: 'Resume', value: state.resumeFile ? state.resumeFile.name : null },
      { label: 'Duration', value: state.durationMinutes ? `${state.durationMinutes} min` : null },
      { label: 'Interviewer', value: state.behavioralPersona ? behavioralPersonas.find((p) => p.id === state.behavioralPersona)?.name : null },
    ]
  } else {
    summaryRows = [
      { label: 'Type', value: state.interviewType ? 'Technical' : null },
      { label: 'Role', value: state.role ? ROLES.find((r) => r.id === state.role)?.label : null },
      { label: 'Company', value: state.company ? companies.find((c) => c.id === state.company)?.name : null },
      { label: 'Difficulty', value: state.difficulty ? state.difficulty.charAt(0).toUpperCase() + state.difficulty.slice(1) : null },
      { label: 'Duration', value: state.durationMinutes ? `${state.durationMinutes} min` : null },
      { label: 'Interviewer', value: state.technicalPersona ? personas.find((p) => p.id === state.technicalPersona)?.name : null },
    ]
  }

  return (
    <div className="min-h-screen bg-ink-950 py-12 px-6">
      <div className="mx-auto max-w-5xl">
        {/* Progress bar */}
        <div className="mb-10 flex items-center gap-4">
          <span className="font-mono text-xs text-paper-faint">{stepNumLabel} / {totalLabel}</span>
          <div className="flex-1 h-px bg-ink-700">
            <motion.div
              className="h-px bg-ember"
              animate={{ width: `${progressPct}%` }}
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
                <p className="mb-1 font-mono text-xs uppercase tracking-widest text-ember">{stepNumLabel}</p>
                <h2 className="mb-2 font-display text-3xl font-semibold text-paper">{title}</h2>
                <p className="mb-8 text-paper-dim">{subtitle}</p>

                {/* Step 1: Interview type */}
                {step === 1 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {INTERVIEW_TYPES.map((t) => (
                      <OptionCard
                        key={t.id}
                        selected={state.interviewType === t.id}
                        onClick={() => setState((s) => ({ ...s, interviewType: t.id }))}
                        label={t.label}
                        hint={t.hint}
                      />
                    ))}
                  </div>
                )}

                {/* Behavioral & Resume Shared Steps */}
                {/* Resume: Step 2 = Upload Resume */}
                {state.interviewType === 'resume' && step === 2 && (
                  <div className="flex flex-col items-center justify-center rounded-md border-2 border-dashed border-ink-700/70 bg-ink-900/50 p-12 text-center transition-colors hover:border-ink-600 hover:bg-ink-800/50">
                    <input 
                      type="file" 
                      accept=".pdf" 
                      className="hidden" 
                      ref={fileInputRef} 
                      onChange={handleFileUpload} 
                    />
                    <div className="mb-4 rounded-full bg-ink-800 p-4 text-paper-dim">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2v4a2 2 0 0 0 2 2h4"></path><path d="M10.4 12.6a2 2 0 1 1 3 3L8 21l-4 1 1-4Z"></path><path d="m18 16 3-3-3-3"></path><path d="m6 8-3 3 3 3"></path><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path></svg>
                    </div>
                    {state.resumeFile ? (
                      <div className="flex flex-col items-center gap-2">
                        <p className="font-medium text-paper">{state.resumeFile.name}</p>
                        {isUploading ? (
                          <p className="text-sm text-ember animate-pulse">Parsing and uploading...</p>
                        ) : (
                          <p className="text-sm text-green-400">Ready!</p>
                        )}
                        <button 
                          onClick={() => fileInputRef.current?.click()}
                          className="mt-4 text-sm text-paper-dim underline hover:text-paper"
                        >
                          Choose a different file
                        </button>
                      </div>
                    ) : (
                      <>
                        <h3 className="mb-2 font-medium text-paper">Upload Resume PDF</h3>
                        <p className="mb-6 text-sm text-paper-dim">Only PDF format is supported.</p>
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="rounded-sm bg-ember px-5 py-2 font-mono text-sm uppercase tracking-widest text-ink-950 transition-colors hover:bg-ember-soft"
                        >
                          Browse Files
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Behavioral: Step 2, Resume: Step 3 = Duration */}
                {(state.interviewType === 'behavioral' && step === 2) || (state.interviewType === 'resume' && step === 3) ? (
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
                ) : null}

                {/* Behavioral: Step 3, Resume: Step 4 = Persona */}
                {(state.interviewType === 'behavioral' && step === 3) || (state.interviewType === 'resume' && step === 4) ? (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {behavioralPersonas.map((p) => (
                      <OptionCard
                        key={p.id}
                        selected={state.behavioralPersona === p.id}
                        onClick={() => setState((s) => ({ ...s, behavioralPersona: p.id }))}
                        label={p.name}
                        hint={p.description}
                        tag={p.id}
                      />
                    ))}
                  </div>
                ) : null}

                {/* Technical: Step 2 = Role */}
                {state.interviewType === 'technical' && step === 2 && (
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

                {/* Technical: Step 3 = Company */}
                {state.interviewType === 'technical' && step === 3 && (
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

                {/* Technical: Step 4 = Difficulty */}
                {state.interviewType === 'technical' && step === 4 && (
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

                {/* Technical: Step 5 = Duration */}
                {state.interviewType === 'technical' && step === 5 && (
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

                {/* Technical: Step 6 = Persona */}
                {state.interviewType === 'technical' && step === 6 && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {personas.map((p) => (
                      <OptionCard
                        key={p.id}
                        selected={state.technicalPersona === p.id}
                        onClick={() => setState((s) => ({ ...s, technicalPersona: p.id }))}
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
              {!isFinalStep ? (
                <button
                  onClick={() => canAdvance() && setStep((s) => s + 1)}
                  disabled={!canAdvance() || isUploading}
                  className={cn(
                    'flex items-center gap-3 rounded-sm px-6 py-3 font-mono text-sm uppercase tracking-widest transition-all duration-200',
                    canAdvance() && !isUploading
                      ? 'bg-ember text-ink-950 hover:bg-ember-soft active:scale-[0.97]'
                      : 'bg-ink-800 text-paper-faint cursor-not-allowed'
                  )}
                >
                  Continue →
                </button>
              ) : (
                <button
                  onClick={handleStart}
                  disabled={!canAdvance() || loading || isUploading}
                  className={cn(
                    'flex items-center gap-3 rounded-sm px-8 py-3 font-mono text-sm uppercase tracking-widest transition-all duration-200',
                    canAdvance() && !loading && !isUploading
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
                {summaryRows.map(({ label, value }) => (
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
