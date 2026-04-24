// Matches FastAPI response schemas exactly (snake_case)

export type SessionStatus = 'pending' | 'active' | 'completed' | 'abandoned'
export type SessionMode = 'technical' | 'behavioral' | 'mixed' | 'resume'
export type BehavioralPersona = 'supportive' | 'corporate' | 'pressure' | 'probing'

export interface ApiSession {
  id: string
  clerk_user_id: string
  mode: SessionMode
  role: string | null
  company: string | null
  difficulty: 'easy' | 'medium' | 'hard' | null
  duration_minutes: number
  interviewer_tone: 'friendly' | 'neutral' | 'intense' | 'skeptical' | null
  behavioral_persona: BehavioralPersona | null
  status: SessionStatus
  question_ids: string[]
  elevenlabs_agent_id: string | null
  elevenlabs_conversation_id: string | null
  audio_s3_url: string | null
  created_at: string
  started_at: string | null
  ended_at: string | null
}

export interface ApiSessionList {
  sessions: ApiSession[]
  total: number
}

export interface ApiAgentUrl {
  agent_id: string
  signed_url: string
}

export interface ApiProblem {
  id: string
  title: string
  difficulty: 'easy' | 'medium' | 'hard'
  description: string
  examples: { input: string; output: string; explanation?: string }[]
  constraints: string[]
  starter_code: Record<string, string>
}

export interface ApiQuestion {
  id: string
  type: 'technical' | 'behavioral'
  prompt: string
  order: number
  coding_problem_id: string | null
  problem: ApiProblem | null
}

export interface ApiTestResult {
  test_case_id: string
  passed: boolean
  stdout: string | null
  stderr: string | null
  runtime_ms: number | null
  status: string
}

export interface ApiCodeRunResult {
  test_results: ApiTestResult[]
  passed_count: number
  total_count: number
  status: string
}

export interface ApiCategoryScores {
  clarity: number | null
  confidence: number | null
  conciseness: number | null
  structure: number | null
  specificity: number | null
  pace: number | null
  problem_solving: number | null
  code_correctness: number | null
  optimization_awareness: number | null
  star_structure: number | null
  impact_articulation: number | null
  ownership: number | null
}

export interface ApiEvidenceSpan {
  transcript_segment_id: string
  quote: string
  note: string
}

export interface ApiQuestionFeedback {
  question_id: string
  question_text: string | null
  score: number
  strengths: string[]
  improvements: string[]
  better_answer_example: string | null
  evidence: ApiEvidenceSpan[]
}

export interface ApiFeedbackReport {
  session_id: string
  overall_score: number
  category_scores: ApiCategoryScores
  per_question_feedback: ApiQuestionFeedback[]
  top_strengths: string[]
  top_weaknesses: string[]
  targeted_drills: string[]
  generated_at: string
}
