# Architecture: AI Mock Interview Platform

## Purpose

This document defines the technical architecture for a live mock interview platform that supports:

- LeetCode-style coding interviews  
- Behavioral voice interviews  
- Company-specific interview adaptation  
- Real-time AI interviewer (voice)  
- Post-interview feedback + scoring  

---

# 1. High-Level System Overview

The system is composed of **4 main layers**:

## 1. Frontend
- React + TypeScript + Tailwind  
- Interview UI (coding + voice)  
- WebSocket client for real-time interaction  
- Auth via Clerk  

## 2. Backend & Business Logic (FastAPI)
- Central API gateway  
- Session orchestration  
- Service-based architecture  
- Handles all core logic  

## 3. External AI + Data Services
- Tavily → research & retrieval  
- ElevenLabs → voice + transcription  
- Featherless → LLM feedback + reasoning  

## 4. Database
- MongoDB → persistent storage  

---

# 2. System Architecture (Based on Diagram)

## Core Backend Entry Point

### FastAPI

Acts as the **central orchestrator**:

### Responsibilities:
- Handles all HTTP requests  
- Creates interview sessions  
- Initializes WebSocket sessions  
- Routes requests to internal services  
- Enforces auth (via Clerk)  

---

# 3. Backend Service Layer

The backend is structured into **independent services**:

---

## 3.1 Session Service (CORE)

This is the **central coordinator of the system**.

### Responsibilities
- Create interview session  
- Manage session lifecycle  
- Track current question  
- Coordinate between services  
- Store session data in MongoDB  

### Interactions
- Calls Retrieval Service → to fetch questions  
- Calls Voice Service → to start interviewer  
- Calls Feedback Service → after session ends  

---

## 3.2 Retrieval Service

Handles **question + company research**

### Responsibilities
- Fetch interview questions  
- Retrieve company-specific patterns  
- Call Tavily for external research  
- Normalize and structure results  

### External dependency
- Tavily API  

### Output
- Structured interview questions  
- Company insights  

---

## 3.3 Voice Service

Handles **real-time conversation**

### Responsibilities
- Create ElevenLabs agent  
- Stream interviewer speech (TTS)  
- Receive user speech (STT)  
- Manage conversation + transcription  
- Send transcript events to backend  

### External dependency
- ElevenLabs  

### Key outputs
- Transcript segments  
- Speaking events  
- Conversation IDs  

---

## 3.4 Feedback Service

Handles **post-interview evaluation**

### Responsibilities
- Analyze transcript  
- Evaluate communication quality  
- Evaluate technical explanation  
- Generate structured feedback  
- Produce scorecard  

### External dependency
- Featherless AI (LLMs like Qwen / DeepSeek)  

### Output
- Scores  
- Strengths / weaknesses  
- Improvement suggestions  

---

## 3.5 Analytics Service

Handles **user-level insights**

### Responsibilities
- Aggregate past interview performance  
- Track improvement trends  
- Compute metrics over time  

### Data source
- MongoDB  

---

# 4. External Services Integration

---

## 4.1 Tavily (Retrieval Layer)

### Used by:
- Retrieval Service  

### Purpose
- Fetch real-world interview questions  
- Gather company-specific patterns  
- Enrich interview realism  

---

## 4.2 ElevenLabs (Voice Layer)

### Used by:
- Voice Service  

### Purpose
- Interviewer speech (TTS)  
- User speech transcription (STT)  
- Real-time conversation handling  

---

## 4.3 Featherless AI (LLM Layer)

### Used by:
- Feedback Service  

### Purpose
- Transcript analysis  
- Scoring + reasoning  
- Structured feedback generation  

### Example models
- Qwen2.5  
- DeepSeek R1  

---

# 5. Database Layer (MongoDB)

### Stores:
- Users  
- Interview sessions  
- Questions  
- Transcripts  
- Code submissions  
- Feedback reports  

### Why MongoDB
- Flexible schema  
- Fits nested interview data  
- Good for transcripts + JSON feedback  

---

# 6. Data Flow (End-to-End)

---

## 6.1 Session Creation

1. Frontend → FastAPI  
2. FastAPI → Session Service  
3. Session Service → Retrieval Service  
4. Retrieval Service → Tavily  
5. Questions returned  
6. Session stored in MongoDB  

---

## 6.2 Start Interview

1. Frontend connects (WebSocket / session init)  
2. FastAPI → Session Service  
3. Session Service → Voice Service  
4. Voice Service → ElevenLabs agent created  
5. Agent starts conversation  

---

## 6.3 Live Interview (Real-Time)

**Flow:**

- User speaks → ElevenLabs  
- ElevenLabs → transcript  
- Voice Service → Session Service  

### Session Service decides:
- Follow-up  
- Interruption  
- Next question  

---

## 6.4 Coding Flow (Technical Mode)

1. User writes code (frontend)  
2. Frontend → FastAPI (`/run` or `/submit`)  
3. FastAPI → Code execution layer (Piston/Judge0)  
4. Results returned  
5. Stored in MongoDB  

---

## 6.5 End Interview

1. Session ends  
2. Session Service → Feedback Service  
3. Feedback Service → Featherless AI  
4. Feedback generated  
5. Stored in MongoDB  

---

## 6.6 Feedback Display

1. Frontend requests results  
2. FastAPI → MongoDB  
3. Feedback returned  

### UI renders:
- Score  
- Transcript  
- Suggestions  

---

# 7. Core Architectural Principles

---

## 7.1 Service-Based Design

Each service has a **single responsibility**:

- Session control  
- Retrieval  
- Voice  
- Feedback  

---

## 7.2 Backend Owns Logic

Frontend is **UI only**

All decisions happen in backend:
- Interview flow  
- Follow-ups  
- Scoring  

---

## 7.3 External APIs are Isolated

Each provider is wrapped:

- `tavily.py`  
- `elevenlabs.py`  
- `featherless.py`  

👉 Makes swapping providers easy  

---

## 7.4 Real-Time + REST Separation

- REST → setup, data fetch  
- WebSocket / streaming → live interview  
