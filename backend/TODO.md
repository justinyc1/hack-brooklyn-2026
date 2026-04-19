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


- [x] `POST /api/interviews/:id/transcript` — persist transcript segment
- [x] `GET /api/interviews/:id/transcript` — retrieve full transcript
- [x] Normalize speaker turns (interviewer vs user)
- [x] Segment transcript by question


### Code Execution (Technical Mode)


- [x] `POST /api/interviews/:id/code/run` — forward code to sandbox, return test results (`app/routes/code.py`)
- [x] `POST /api/interviews/:id/code/submit` — final submission, store results (`app/routes/code.py`)
- [x] Sandboxed code execution (Judge0 CE via RapidAPI) (`app/services/judge0.py`)
- [x] Load coding problems (static JSON config) (`problems/problems.json`)


### Feedback
- [x] `GET /api/feedback/:id` — get feedback report (`app/routes/feedback.py`)
- [x] Async feedback job triggered on session end (`services/feedback.py`, `generate_feedback`)
- [x] Score communication dimensions: clarity, confidence, conciseness, structure, specificity, pace
- [x] Score technical dimensions: approach, correctness, optimization awareness
- [x] Score behavioral dimensions: STAR structure, impact, ownership, reflection
- [x] Generate evidence-based feedback with transcript spans
- [x] Generate improved answer examples and targeted drills
- [x] LLM scoring via meta-llama/Meta-Llama-3.1-8B-Instruct (Featherless.ai) (`services/llm.py`)


### Company Research


- [x] `GET /api/companies/:company/snapshot` — return cached snapshot or trigger Tavily job (`app/routes/companies.py`)
- [x] Call Tavily for interview patterns/questions (feed https://leetbot.org/ into Tavily API endpoint for company specific interview questions), company values, role themes (`app/services/company_research.py`)
- [x] Score and synthesize sources into structured snapshot (LLM synthesis via Featherless)
- [x] Cache snapshots in DB (invalidate after 7 days) (`db.company_snapshots`)
- [x] Graceful fallback to generic mode if Tavily fails (returns empty theme lists)


---


## Real-Time / WebSocket


- [x] WebSocket gateway (`/ws/interviews/:id`)
- [x] Session state sync to connected clients
- [x] Events: `conversation.linked`, `question.advanced`, `transcript.synced`
- [~] Events: `silence.detected`, `followup.triggered`, `code.submitted`, `feedback.generated` (`feedback.generated` done)
- [ ] Reconnect handling (restore state from Redis on reconnect)
- [ ] Interviewer speaking state broadcast


---


## Voice Integration (ElevenLabs)


- [x] Conversational AI agent creation per session (TTS + STT + turn-taking bundled)
- [x] Signed URL endpoint for frontend WebSocket connection to ElevenLabs
- [x] Transcript sync from ElevenLabs on session completion
- [ ] Silence detection / timeout signaling
- [ ] Interruption-aware flow
- [ ] Fallback to text-only mode if ElevenLabs fails


---


## Auth (Clerk)


- [x] Verify Clerk JWT on all protected routes (`require_auth` dependency)
- [x] Extract `clerk_user_id` from token and attach to request context (via `sub` claim)
- [x] Upsert user record in DB on first verified request


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
