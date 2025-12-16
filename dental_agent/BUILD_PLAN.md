# AI Voice Agent for Dental Clinics - Build Plan

## Project Overview
AI Voice Agent system for dental clinics with FastAPI backend and AI Voice Agent Worker.

## Architecture

### 1. FastAPI Backend (`main.py`)
- JWT Authentication
- Lead uploads (CSV/JSON)
- n8n webhook integration
- Call logs, transcripts, results in SQLite
- Dashboard API endpoints

### 2. Database Layer (`db.py`)
- SQLModel ORM (Pydantic + SQLAlchemy)
- Models: User, Client, UploadBatch, Lead, Call, CallResult
- Session management
- Helper functions for enqueueing calls

### 3. Telephony Adapter (`telephony.py`)
- SIMULATED mode (for MVP)
- TWILIO_STUB mode (for later PSTN)
- Phone formatting helpers

### 4. AI Voice Agent Worker (`agent_server.py`)
- Deepgram Voice Agent WebSocket integration
- FSM: GREETING → QUALIFY → OFFER_SLOT → CONFIRM → END
- Simulated conversation for testing
- Posts results back to API

### 5. Agent Configuration (`agent_config/dental_receptionist.json`)
- Persona definition
- Greeting variations
- Qualifying questions
- Booking logic
- Fallbacks

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | JWT login |
| POST | /api/clients/{client_id}/uploads | Upload leads (CSV/JSON) |
| POST | /webhook/n8n/start-call | n8n webhook to start call |
| POST | /api/calls/{call_id}/status | Update call status/result |
| GET | /api/clients/{client_id}/batches/{batch_id}/calls | Get call logs |
| POST | /api/twilio/webhook | Twilio event handler |

## Database Schema

```
User: id, email (unique), password_hash, is_admin
Client: id, name, email, timezone
UploadBatch: id, client_id (FK), created_at, source
Lead: id, batch_id (FK), name, phone, email, source_url, notes, created_at
Call: id, lead_id (FK), batch_id (FK), client_id (FK), status, attempt, created_at, updated_at
CallResult: id, call_id (FK), result, transcript, booked_slot, notes, created_at
```

## Call Status Values
- queued
- in-progress
- completed
- failed

## Call Result Values
- booked
- no-answer
- failed
- reschedule
- voicemail

## Environment Variables
- DATABASE_URL
- JWT_SECRET
- DEEPGRAM_API_KEY
- TELEPHONY_MODE (SIMULATED | TWILIO)
- TWILIO_SID
- TWILIO_TOKEN
- TWILIO_NUMBER

## Build Order
1. ✅ BUILD_PLAN.md (this file)
2. ✅ db.py - Database models and helpers
3. ✅ api_main.py - FastAPI application
4. ✅ telephony.py - Telephony adapter
5. ✅ agent_server.py - Voice agent worker
6. ✅ agent_config/dental_receptionist.json
7. ✅ tests/test_call_flow.py
8. ✅ tests/integration_simulated.py
9. ✅ n8n_workflow_scraper_to_agent.json
10. ✅ .env.example
11. ✅ README.md (updated with quick start)

## Testing Strategy
- Unit tests for FSM logic
- Integration tests with TestClient
- Simulated calls (deterministic, seeded random)
- No external network calls in tests

## Notes
- MVP runs locally with simulated calls first
- Real Twilio PSTN integration added later
- TCPA compliance: only use client-provided leads
