# Architecture: AI Mock Interview Platform

## Purpose

This document defines the technical architecture for a live mock interview platform that supports:

- LeetCode-style coding interviews
- Behavioral interviews with a voice AI interviewer
- Company-specific interview adaptation
- Post-interview transcript analysis and communication feedback
- Future system design interview support

This document is implementation-focused and intended to guide backend, frontend, infra, and data design decisions.

---

# 1. High-Level System Overview

The platform has five major layers:

1. **Frontend Client**
   - Interview room UI
   - LeetCode-style coding interface
   - Behavioral interview interface
   - Transcript + feedback dashboard

2. **Application Backend**
   - Session orchestration
   - Interview flow control
   - User/session APIs
   - Feedback/report generation
   - Company research integration

3. **Real-Time Voice Layer**
   - Audio streaming
   - Speech-to-text events
   - Text-to-speech interviewer playback
   - Turn-taking / interruption support

4. **Data Layer**
   - Persistent session storage
   - Transcript storage
   - Coding submissions
   - Feedback reports
   - Company pattern snapshots

5. **Infrastructure / Async Layer**
   - Queues / background jobs
   - caching / ephemeral state
   - storage
   - monitoring
   - deployment

---

# 2. Recommended Stack

## Frontend

- **React + TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **Monaco Editor** for coding interface
- **WebSocket client** for live interview state
- **Waveform / mic visualization components**

## Backend

Keep backend abstract for now since framework is undecided:

### Option A: FastAPI

Good fit if you want:

- Python ecosystem
- easier AI pipeline integration
- strong typing with Pydantic
- async support
- easier transcript/feedback processing with Python libraries

### Recommendation for now

Design the system so backend services are framework-agnostic:

- REST APIs
- WebSocket gateway
- background workers
- shared service boundaries

This makes it easy to start with either FastAPI or Express.

## Realtime / Voice

- **ElevenLabs** (Elevenlabs MCP server is installed if needed) for:
  - TTS interviewer voice
  - STT transcription
  - conversational turn-taking
  - interruption-aware interaction

## Company Research / Retrieval

- **Tavily**
  - public interview question/pattern gathering
  - company values / role context / hiring themes
  - external research enrichment

## Database

- **MongoDB**
  - flexible document model
  - good fit for transcripts, feedback JSON, research snapshots, sessions
  - active interview session state
  - timers
  - turn state
  - transient orchestration metadata

## Auth

- **Clerk**

## Deployment

- Frontend: **Vercel**
- Backend: **Railway**, 
- DB: **MongoDB**

---

# 3. Core Architectural Principles

## 3.1 Separate Real-Time from Standard API Work

Live interviews have different performance characteristics than normal CRUD APIs.

Split:

- **standard application API**
- **real-time session / voice orchestration**
- **background feedback jobs**

## 3.2 Store Flexible Interview Artifacts as Documents

Interview sessions produce nested, evolving data:

- transcript segments
- question trees
- dynamic feedback
- code submissions
- research snapshots

MongoDB is a good fit for this.

## 3.3 Keep Interview Logic Server-Controlled

The client should not decide:

- when to interrupt
- when to advance question
- follow-up selection
- scoring logic

The backend should own interview state and orchestration.

## 3.4 Make the System Event-Driven Internally

A live interview is naturally event-based:

- question asked
- user started speaking
- silence threshold reached
- transcript partial received
- follow-up triggered
- coding submission run
- feedback generated

Representing interview flow as internal events keeps the architecture clean.

---

# 4. Main System Components

## 4.1 Frontend Client

### Responsibilities

- authentication
- interview setup flow
- live interview room UI
- code editor UI
- transcript rendering
- feedback dashboard
- company mode selection
- progress history

### Main frontend modules

#### A. Setup Flow

- choose role
- choose company
- choose interview type
- choose difficulty
- choose duration
- choose interviewer tone

#### B. Technical Interview Room

- problem statement panel
- code editor
- language selector
- run / submit buttons
- test result panel
- timer
- transcript side panel
- interviewer speaking state
- user mic state

#### C. Behavioral Interview Room

- interviewer prompt panel
- speaking status UI
- timer
- transcript stream
- question history
- mute / pause / skip controls

#### D. Feedback Dashboard

- overall score
- per-question feedback
- coding correctness results
- communication metrics
- transcript evidence highlights
- replay of important clips

### Frontend communication patterns

- **REST** for setup, fetching data, saving preferences
- **WebSocket** for live interview events
- **direct media stream or voice session connection** depending on final ElevenLabs integration pattern

---

## 4.2 API Backend

This is the main application backend.

### Responsibilities

- user/session CRUD
- interview session creation
- question planning
- company research pipeline triggering
- transcript persistence
- feedback generation kickoff
- analytics endpoints
- session history endpoints

### Suggested service modules

#### Auth Service

- session validation
- user identity
- role/access checks

#### Interview Service

- create session
- load session
- advance session state
- persist question/answer timeline
- end session

#### Question Planning Service

- generate interview plan
- choose question sequence
- attach follow-up branches
- adapt based on mode:
  - technical
  - behavioral
  - mixed
  - future system design

#### Company Research Service

- call Tavily
- score sources
- synthesize themes
- cache company snapshots

#### Transcript Service

- store raw transcript segments
- normalize speaker turns
- merge segments into final transcript

#### Feedback Service

- run scoring pipelines
- generate evidence-based feedback
- create summary reports
- suggest drills

#### Coding Evaluation Service

- run code against test cases
- store results
- compute performance metadata
- pass results into feedback engine

---

## 4.3 Real-Time Session Orchestrator

This is the most important runtime component.

### Responsibilities

- manage active interview state
- receive live transcript events
- determine when interviewer should speak
- decide follow-up vs pushback vs next question
- manage interruption rules
- synchronize UI state

### Key state tracked per live session

- current question
- current mode
- timer state
- speaking state
- partial transcript buffer
- silence timer
- interruption counters
- interviewer mode/persona
- coding progress markers
- current follow-up depth

### Why this should be separate

Real-time interviews require:

- fast event handling
- low latency
- stateful orchestration
- robust reconnect behavior

This should not be tightly coupled to ordinary request/response routes.

---

## 4.4 Voice Integration Layer

### External provider

- ElevenLabs

### Responsibilities

- interviewer TTS playback
- user speech transcription
- turn-taking events
- silence / end-of-turn signaling
- support interruption-aware flows

### Internal responsibilities

- normalize provider events into app events
- buffer transcript partials
- mark speaker boundaries
- associate transcript with active question

### Example normalized internal events

- `interviewer.audio.started`
- `interviewer.audio.finished`
- `user.speech.started`
- `user.speech.partial`
- `user.speech.final`
- `user.silence.timeout`
- `turn.transition.ready`

---

## 4.5 Coding Evaluation Layer

Used only in technical LeetCode-style interview mode.

### Responsibilities

- load coding problem
- compile/execute code safely
- run public and hidden test cases
- return pass/fail metadata
- store complexity/execution metadata if available

### Important note

This must be isolated for security.

### Preferred architecture

- dedicated sandbox runner service
- containerized execution
- strict CPU / memory / timeout limits
- no unrestricted filesystem/network access

### Inputs

- language
- code
- problem id
- test case set

### Outputs

- passed count
- failed count
- stdout/stderr
- runtime metrics
- error type
- submission status

---

## 4.6 Feedback Engine

This can run partly synchronously and partly asynchronously.

### Responsibilities

- evaluate transcript
- evaluate communication quality
- evaluate coding explanation quality
- evaluate behavioral structure
- generate evidence-based feedback
- produce overall scorecard

### Inputs

- question asked
- transcript
- coding results if technical
- company context if applicable
- interview mode
- follow-up history

### Output types

- overall score
- category scores
- transcript evidence spans
- improvement notes
- better answer examples
- targeted drills

---

## 4.7 Company Research Pipeline

### Responsibilities

- retrieve public interview signals using Tavily
- gather company hiring themes / role themes
- score source quality
- generate structured pattern snapshot

### Output example

```json
{
  "company": "ExampleCo",
  "role": "Software Engineer Intern",
  "behavioral_themes": [
    { "theme": "ownership", "confidence": 0.82 },
    { "theme": "collaboration", "confidence": 0.76 }
  ],
  "technical_focus": [
    { "theme": "algorithms", "confidence": 0.74 },
    { "theme": "data structures", "confidence": 0.7 }
  ],
  "style_signals": [{ "theme": "deep follow-ups", "confidence": 0.67 }]
}
```

# 5. Runtime Flow

This section describes how the system behaves at runtime across different interview modes.

---

## 5.1 Interview Setup Flow

1. User opens setup page
2. User selects:
   - role
   - company (optional)
   - interview mode (technical, behavioral, mixed)
   - difficulty
   - duration
3. Frontend sends request to backend:
   - `POST /api/interviews`
4. Backend:
   - creates session document
   - retrieves or generates company interview questions (via Tavily)
   - generates interview plan:
     - question sequence
     - follow-up trees
     - interviewer persona
5. Session is stored in database
6. Frontend transitions to interview room
7. WebSocket connection is established for live session

---

## 5.2 Live Behavioral Interview Flow

1. Session starts
2. Real-time orchestrator loads first question
3. Backend sends prompt to voice layer (ElevenLabs)
4. Interviewer speaks question (TTS)
5. User responds via microphone
6. Voice layer streams:
   - partial transcripts
   - final transcript segments
7. Orchestrator evaluates:
   - silence duration
   - filler-heavy speech
   - incomplete answers
   - vagueness
8. Orchestrator decides next action:
   - continue listening
   - ask follow-up
   - interrupt
   - push back
   - move to next question
9. Transcript segments are persisted incrementally
10. Process repeats for all questions
11. Session ends
12. Feedback job is triggered
13. User is redirected to feedback dashboard

---

## 5.3 Live Technical Interview Flow (LeetCode-Style)

1. Session starts
2. Coding problem is loaded in UI
3. Interviewer introduces problem via voice
4. User:
   - explains approach (optional but encouraged)
   - begins coding in editor
5. System streams transcript while user speaks
6. Orchestrator monitors:
   - silence
   - coding without explanation
   - rambling explanations
7. Interviewer may intervene:
   - ask for approach clarification
   - ask time/space complexity
   - request optimization discussion
8. User runs or submits code:
   - frontend sends code to backend
   - backend forwards to coding sandbox
9. Sandbox executes:
   - runs test cases
   - returns results (pass/fail, runtime, errors)
10. Results are displayed in UI
11. Orchestrator may trigger:

- follow-up questions
- deeper probing

12. All data stored:

- transcript
- code submissions
- execution results

13. Session ends
14. Feedback engine combines:

- coding performance
- communication quality

15. User sees final report

---

## 5.4 Mixed Interview Flow

1. Session starts with predefined sequence:
   - behavioral → technical OR
   - technical → behavioral
2. Behavioral portion follows section 5.2
3. Technical portion follows section 5.3
4. Orchestrator handles transition:
   - resets timers
   - updates mode
5. Final report combines:
   - behavioral scores
   - technical scores
   - communication metrics across both

---

## 5.5 Post-Interview Feedback Flow

1. Session ends → backend triggers async job
2. Feedback engine processes:
   - transcript
   - question intent
   - coding results (if technical)
   - timing and interruption metadata
3. Pipeline:
   - segment transcript by question
   - evaluate against rubric
   - extract evidence spans
   - generate scores
   - generate improvement suggestions
4. Report is saved in database
5. Frontend polls or subscribes:
   - `feedback.ready` event
6. User sees:
   - overall score
   - per-question feedback
   - transcript highlights
   - suggested improvements

---

## 5.6 Company Research Flow (Background)

1. User selects company
2. Backend checks for existing snapshot
3. If stale or missing:
   - trigger Tavily research job
4. Tavily retrieves:
   - interview experiences
   - company values
   - role expectations
   - interview questions from specific user-selected companies (feed https://leetbot.org/ into tavily endpoint)
5. Backend:
   - scores sources
   - synthesizes patterns
   - generates structured themes
6. Snapshot stored in DB
7. Interview plan uses this snapshot for:
   - question selection
   - follow-up behavior
   - interviewer tone

---

## 5.7 Failure / Recovery Flow

### WebSocket Disconnect

- client reconnects automatically
- backend restores session state from MongoDB
- resume interview from last known state

### Voice Provider Failure

- fallback to text-based prompts
- continue interview in degraded mode

### Coding Sandbox Failure

- return structured error (timeout, runtime error)
- allow retry

### Tavily Failure

- fallback to generic interview mode
- mark company mode as degraded

---

## 5.8 Event-Driven Flow Summary

Core runtime is event-based:

- `question.asked`
- `user.speech.started`
- `transcript.partial`
- `transcript.final`
- `silence.detected`
- `interruption.triggered`
- `followup.triggered`
- `code.submitted`
- `coding.result`
- `feedback.generated`

These events drive the orchestrator and UI updates in real time.
