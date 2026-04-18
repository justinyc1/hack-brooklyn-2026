# Backend TODO

Status legend: `[x]` done · `[ ]` not started · `[~]` partial

---

## Infrastructure & Setup

- [x] FastAPI app bootstrapped (`app/main.py`)
- [x] MongoDB connection (`app/db.py`)
- [x] Config/settings management (`app/config.py`, `.env`)
- [x] Health check endpoint (`GET /health`)
- [x] DB connectivity test endpoint (`GET /db-test`)
- [x] Tavily API integration test (`GET /tavily-test`)
- [x] ElevenLabs API integration test (`GET /eleven-test`)
- [x] Dependencies installed (`requirements.txt`: fastapi, uvicorn, pymongo, httpx, pydantic-settings)
- [ ] Redis client setup (ephemeral session state, timers)
- [x] Clerk JWT middleware (verify auth tokens on protected routes) (`app/auth/clerk.py`)

---

## Data Models (MongoDB Schemas)

- [x] `User` — clerk_user_id, email, created_at, preferences (`app/models/user.py`)
- [x] `InterviewSession` — clerk_user_id, mode, company, role, difficulty, duration, status, created_at (`app/models/interview_session.py`)
- [x] `Question` — session_id, type, prompt, follow_up_tree, order (`app/models/question.py`)
- [x] `TranscriptSegment` — session_id, question_id, speaker (interviewer/user), text, is_partial, timestamp (`app/models/transcript.py`)
- [x] `CodeSubmission` — session_id, question_id, language, code, test_results, submitted_at (`app/models/code_submission.py`)
- [x] `FeedbackReport` — session_id, overall_score, category_scores, per_question_feedback, evidence_spans, drills (`app/models/feedback.py`)
- [x] `CompanySnapshot` — company, role, behavioral_themes, technical_focus, style_signals, retrieved_at (`app/models/company_snapshot.py`)
- [x] `MongoBase` — shared base with PyObjectId coercion, `from_mongo`, `to_mongo` (`app/models/base.py`)

---

## API Routes

### Interview Sessions

- [x] `POST /api/interviews` — create session, generate question plan, return session (`app/routes/interviews.py`)
- [x] `GET /api/interviews/:id` — load session state (owner-scoped)
- [x] `PATCH /api/interviews/:id` — advance status, auto-set started_at/ended_at
- [x] `GET /api/interviews` — list sessions for authenticated user (history, newest first)

### Question Planning

- [x] Generate question sequence on session creation (technical, behavioral, mixed) (`app/services/question_planner.py`)
- [~] Attach follow-up branches to each question (tree structure ready; LLM generation pending)
- [x] Support interviewer persona/tone selection (friendly, neutral, intense, skeptical)

### Transcript

- [ ] `POST /api/interviews/:id/transcript` — persist transcript segment
- [ ] `GET /api/interviews/:id/transcript` — retrieve full transcript
- [ ] Normalize speaker turns (interviewer vs user)
- [ ] Segment transcript by question

### Code Execution (Technical Mode)

- [ ] `POST /api/interviews/:id/code/run` — forward code to sandbox, return test results
- [ ] `POST /api/interviews/:id/code/submit` — final submission, store results
- [ ] Sandboxed code execution (containerized runner, CPU/memory/timeout limits)
- [ ] Load coding problems (store problems in DB or static config)

### Feedback

- [ ] `GET /api/feedback/:id` — get feedback report (poll or subscribe)
- [ ] Async feedback job triggered on session end
- [ ] Score communication dimensions: clarity, confidence, conciseness, structure, specificity, pace
- [ ] Score technical dimensions: approach, correctness, optimization awareness
- [ ] Score behavioral dimensions: STAR structure, impact, ownership, reflection
- [ ] Generate evidence-based feedback with transcript spans
- [ ] Generate improved answer examples and targeted drills

### Company Research

- [ ] `GET /api/companies/:company/snapshot` — return cached snapshot or trigger Tavily job
- [ ] Call Tavily for interview patterns/questions (feed https://leetbot.org/ into Tavily API endpoint for company specific interview questions), company values, role themes
- [ ] Score and synthesize sources into structured snapshot
- [ ] Cache snapshots in DB (invalidate after N days)
- [ ] Graceful fallback to generic mode if Tavily fails

---

## Real-Time / WebSocket

- [ ] WebSocket gateway (`/ws/interviews/:id`)
- [ ] Session state sync to connected clients
- [ ] Events: `question.asked`, `transcript.partial`, `transcript.final`, `silence.detected`, `followup.triggered`, `code.submitted`, `feedback.generated`
- [ ] Reconnect handling (restore state from Redis on reconnect)
- [ ] Interviewer speaking state broadcast

---

## Voice Integration (ElevenLabs)

- [ ] TTS: send interviewer prompt text → receive audio stream
- [ ] STT: stream user microphone audio → receive partial + final transcripts
- [ ] Turn-taking events (end-of-turn detection)
- [ ] Silence detection / timeout signaling
- [ ] Interruption-aware flow
- [ ] Normalize provider events into internal app events
- [ ] Fallback to text-only mode if ElevenLabs fails

---

## Auth (Clerk)

- [x] Verify Clerk JWT on all protected routes (`require_auth` dependency)
- [x] Extract `clerk_user_id` from token and attach to request context (via `sub` claim)
- [ ] Upsert user record in DB on first verified request

---

## Session Orchestrator

- [ ] Per-session state stored in Redis (current question, timer, speaking state, silence counter, follow-up depth)
- [ ] Decision engine: continue listening / ask follow-up / interrupt / move to next question
- [ ] Timer-based constraints per question
- [ ] Interruption counter and rules
- [ ] Transition handling between behavioral and technical portions (mixed mode)

---

## Future / Post-MVP

- [ ] System design interview mode (whiteboard/canvas)
- [ ] Resume-based question generation
- [ ] Audio clip storage in S3 for replay
- [ ] Peer benchmarking analytics
- [ ] Semantic search over past interviews
