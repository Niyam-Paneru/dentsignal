# Dental Clinic AI Voice Agent

> **Stop losing $21,000/month to missed calls.** AI Voice Agent that answers every call, books appointments 24/7, and costs less than your coffee budget.

AI Voice Agent system for dental clinics - handles both **inbound** calls (patients calling in) and **outbound** calls (calling leads to book appointments).

## 💰 The Problem We Solve

| The Reality | The Cost |
|-------------|----------|
| 35% of dental calls go unanswered | $255,000/year lost |
| 62% won't leave a voicemail | They call your competitor |
| Peak call times = patient checkout | Your receptionist can't be everywhere |
| After-hours = 100% missed | 25% of calls come after 5pm |

**Our solution:** AI receptionist that never sleeps, never gets sick, and costs $0.11/call.

## 🚀 Features

### 📞 Voice Agent
- **Inbound Voice Agent**: AI answers calls to your clinic's Twilio number using Deepgram Voice Agent
- **Automated Outbound Calls**: AI calls leads and books dental appointments
- **Natural Conversation**: Uses Deepgram Voice Agent (STT + LLM + TTS in one WebSocket)
- **Multi-Tenant**: One codebase serves multiple dental clinics, each with custom prompts
- **Smart Retries**: Exponential backoff (15min → 2h → 24h) for missed outbound calls
- **Per-Clinic Customization**: Each clinic has its own AI agent name, voice, and custom instructions

### 📱 SMS Automation
- **Instant Confirmations**: SMS sent immediately when appointment booked
- **Smart Reminders**: 24h and 2h before appointment (reduces no-shows by 40%)
- **Post-Call Follow-up**: Thank you SMS with next steps
- **Patient Recall**: Automated 6-month checkup reminders
- **Review Requests**: Ask for Google reviews after positive visits
- **Bulk Campaigns**: Send recall reminders to hundreds of patients

### 📊 Analytics & Insights
- **Sentiment Analysis**: Was the caller happy? Frustrated? 
- **Quality Scoring**: AI grades each call 0-100
- **Conversion Funnel**: Track calls → intent → booked
- **Peak Hours Analysis**: Know when you're busiest
- **Common Questions**: What patients ask most (improve your AI!)
- **Daily/Weekly Reports**: Automated email summaries

### 🔒 Enterprise Ready
- **HIPAA Compliant**: End-to-end encryption, BAA included
- **Multi-Tenant**: One platform, unlimited clinics
- **Real-Time Dashboard**: Track everything in beautiful Next.js UI
- **Call Recording**: All calls recorded and transcribed for QA

## Architecture

```
                           INBOUND CALLS
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Patient     │────▶│     Twilio      │────▶│   FastAPI       │
│  Calls       │     │   (PSTN→WS)     │     │   /inbound/ws   │
└──────────────┘     └─────────────────┘     └─────────────────┘
                                                     │
                                                     ▼
                                              ┌─────────────────┐
                                              │   Deepgram      │
                                              │   Voice Agent   │
                                              │   (STT+LLM+TTS) │
                                              └─────────────────┘

                           OUTBOUND CALLS
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   Celery        │────▶│   Twilio        │
│   Backend       │     │   Workers       │     │   Phone Calls   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `api_main.py` | FastAPI REST API (leads, calls, webhooks) |
| `routes_inbound.py` | Inbound call handling + WebSocket |
| `routes_admin.py` | Clinic management API |
| `routes_sms.py` | SMS automation API |
| `routes_analytics.py` | Call analytics API |
| `routes_calendar.py` | **NEW** - Calendar & appointment scheduling API |
| `calendar_service.py` | **NEW** - Google Calendar + Calendly integration |
| `websocket_bridge.py` | Twilio ↔ Deepgram audio bridge |
| `prompt_builder.py` | Per-clinic prompt generation |
| `ai_providers.py` | Multi-provider AI (50% cost savings!) |
| `call_analytics.py` | Sentiment analysis & quality scoring |
| `post_call_workflow.py` | Automated post-call actions |
| `models.py` | Pydantic models for API |
| `twilio_service.py` | Twilio call management, TwiML, and SMS |
| `deepgram_service.py` | Speech-to-text and intent detection |
| `tasks.py` | Celery background tasks (calls, retries) |
| `db.py` | SQLModel database (SQLite/PostgreSQL) |

## 🧠 Multi-Provider AI Architecture

**50%+ cost savings** by routing tasks to the optimal AI provider:

| Task | Provider | Why |
|------|----------|-----|
| Voice Conversations | OpenAI (gpt-4o-mini) | Lowest latency for real-time |
| Sentiment Analysis | Gemini (2.0-flash) | 50% cheaper than OpenAI |
| Call Summaries | Gemini (2.0-flash) | 50% cheaper than OpenAI |
| Quality Scoring | Gemini (2.0-flash) | 50% cheaper than OpenAI |
| Transcript Search | HuggingFace | **FREE!** |
| Embeddings | HuggingFace | **FREE!** |

```python
# Usage example - automatic provider routing
from ai_providers import ai_complete, TaskType

# Routes to Gemini (cheaper for analysis)
sentiment = ai_complete(
    task=TaskType.SENTIMENT_ANALYSIS,
    prompt="Analyze: 'I love this dental office!'"
)

# Routes to OpenAI (faster for voice)
response = ai_complete(
    task=TaskType.VOICE_CONVERSATION,
    prompt="Patient said: 'I need to book a cleaning'"
)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your credentials:
```env
# Core Services
TWILIO_SID=ACxxxxx
TWILIO_TOKEN=xxxxx
TWILIO_NUMBER=+19048679643
DEEPGRAM_API_KEY=xxxxx
REDIS_URL=redis://localhost:6379/0

# AI Providers (Multi-provider architecture)
OPENAI_API_KEY=sk-xxxxx          # For voice (real-time)
GEMINI_API_KEY=AIzaSy-xxxxx      # For analysis (50% cheaper!)
HF_API_KEY=hf_xxxxx              # For embeddings (FREE!)
```

### 3. Start the Server

**Quick start (with environment check):**
```bash
python run_server.py
```

**With ngrok (for Twilio webhooks):**
```bash
python run_server.py --ngrok
```

**Manual start:**
```bash
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Configure Twilio Webhook

1. Start ngrok: `ngrok http 8000`
2. Copy your ngrok URL (e.g., `https://abc123.ngrok.io`)
3. Go to [Twilio Console](https://console.twilio.com/) → Phone Numbers → Your Number
4. Set Voice webhook to: `https://your-ngrok-url/inbound/voice`
5. Method: POST
6. Save

### 5. Test It!

Call your Twilio number from any phone. The AI receptionist will answer!

API available at:
- Swagger docs: `http://localhost:8000/docs`
- Demo login: `admin@dental.local` / `admin123`

## Testing

Run the test suite:
```bash
python test_voice_agent.py
```

Run specific tests:
```bash
python test_voice_agent.py prompt   # Test prompt builder
python test_voice_agent.py api      # Test API endpoints
python test_voice_agent.py audio    # Test audio conversion
```

## API Endpoints

### Inbound Voice (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/inbound/voice` | Twilio webhook for incoming calls |
| WS | `/inbound/ws/{call_id}` | WebSocket for audio streaming |
| POST | `/inbound/status/{call_id}` | Call status callback |
| GET | `/inbound/calls` | List inbound calls |
| GET | `/inbound/calls/{id}` | Get call details with transcript |

### Clinic Management (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/clinics` | Create new clinic |
| GET | `/api/clinics` | List all clinics |
| GET | `/api/clinics/{id}` | Get clinic details |
| PATCH | `/api/clinics/{id}` | Update clinic config |
| DELETE | `/api/clinics/{id}` | Deactivate clinic |
| GET | `/api/clinics/{id}/calls` | List calls for clinic |
| POST | `/api/clinics/{id}/assign-number` | Assign Twilio number |
| POST | `/api/clinics/{id}/test-prompt` | Preview AI prompt |
| GET | `/api/voices` | List available AI voices |
| GET | `/api/dashboard/stats` | Dashboard statistics |

### Outbound Calls (Existing)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login, returns JWT token |
| POST | `/api/clients/{id}/uploads` | Upload leads (CSV/JSON) |
| POST | `/batches` | Create batch and enqueue calls |
| GET | `/api/clients/{id}/batches/{id}/calls` | List calls for batch |

### SMS & Patient Engagement (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sms/send` | Send custom SMS |
| POST | `/api/sms/confirmation` | Send appointment confirmation |
| POST | `/api/sms/reminder` | Send appointment reminder |
| POST | `/api/sms/followup` | Send post-call follow-up |
| POST | `/api/sms/recall` | Send 6-month checkup reminder |
| POST | `/api/sms/review-request` | Request Google review |
| POST | `/api/sms/bulk/recall` | Send bulk recall reminders |
| GET | `/api/sms/templates` | List SMS templates |

### Analytics & Insights (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analytics/analyze` | Analyze call transcript |
| GET | `/api/analytics/quality-report` | Aggregate quality report |
| GET | `/api/analytics/dashboard-stats` | Dashboard overview |
| GET | `/api/analytics/common-questions` | Most asked questions |
| GET | `/api/analytics/sentiment-trends` | Sentiment over time |
| GET | `/api/analytics/conversion-funnel` | Call-to-booking funnel |
| GET | `/api/analytics/peak-hours` | Peak calling hours |
| POST | `/api/analytics/generate-report-email` | Generate summary email |

## Cost Breakdown

Per call (3 min average):
| Service | Cost |
|---------|------|
| Deepgram STT | $0.013 |
| Deepgram TTS | $0.024 |
| Twilio PSTN | $0.075 |
| **Total** | **~$0.11/call** |

Monthly estimate (100 calls × 3 min):
- Total: ~$12/month per clinic
- You charge: $199/month
- **Profit margin: ~94%**

## Optional: Start Celery (for outbound calls)

If you're also using outbound calling:

**Start Redis:**
```bash
docker run -d -p 6379:6379 redis
```

**Start Celery Worker:**
```bash
celery -A celery_config worker --loglevel=info
```

## Demo: Upload Leads via CSV

Create a CSV file `test_leads.csv`:

```csv
name,phone,email,source_url,notes
John Doe,+15551234567,john@example.com,http://example.com,New patient
Jane Smith,+15559876543,jane@example.com,,Returning patient
```

Upload via cURL:

```bash
curl -X POST "http://localhost:8000/api/clients/1/uploads" \
  -F "file=@test_leads.csv"
```

Or via JSON:

```bash
curl -X POST "http://localhost:8000/api/clients/1/uploads" \
  -H "Content-Type: application/json" \
  -d '{"leads": [{"name": "Test Patient", "phone": "+15551234567"}]}'
```

## Project Structure

```
dental_agent/
├── api_main.py              # FastAPI application (main entry point)
├── run_server.py            # Quick start script with ngrok support
├── test_voice_agent.py      # Test suite
├── 
├── # Inbound Voice Agent (NEW)
├── routes_inbound.py        # Inbound call webhooks + WebSocket
├── websocket_bridge.py      # Twilio ↔ Deepgram audio bridge
├── prompt_builder.py        # Per-clinic prompt generation
├── models.py                # Pydantic API models
├── 
├── # Clinic Management (NEW)
├── routes_admin.py          # Clinic CRUD API
├── 
├── # Core
├── db.py                    # SQLModel database layer
├── deepgram_service.py      # Deepgram integration
├── twilio_service.py        # Twilio call management
├── utils.py                 # Utility functions
├── 
├── # Outbound Calls (Celery-based)
├── agent_server.py          # Voice agent worker
├── tasks.py                 # Celery background tasks
├── routes_calls.py          # Call management routes
├── routes_twilio.py         # Twilio webhooks (outbound)
├── celery_config.py         # Celery configuration
├── 
├── # Configuration
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── agent_config/
│   └── dental_receptionist.json  # Agent persona config
├── 
├── # Tests
├── tests/
│   ├── test_call_flow.py    # Unit tests
│   └── integration_simulated.py  # Integration tests
└── 
```

## Development Roadmap

### ✅ Phase 1: Core Infrastructure (COMPLETE)
- [x] Database layer (SQLModel)
- [x] FastAPI backend with all endpoints
- [x] Telephony adapter (simulated + Twilio)
- [x] Agent worker with FSM conversation
- [x] Agent persona configuration
- [x] Unit and integration tests
- [x] **Deepgram Voice Agent WebSocket bridge**
- [x] **Inbound call handling**
- [x] **Per-clinic prompt customization**
- [x] **Clinic management API**
- [x] **Dashboard UI** (Next.js + Tailwind)

### ✅ Phase 2: Intelligence & Analytics (COMPLETE)
- [x] **Post-call analytics** (sentiment analysis, call summary)
- [x] **Call quality scoring** (AI grades each call 0-100)
- [x] **Conversion tracking** (calls → booked appointments funnel)
- [x] **Peak hours analysis** (when do most calls come in?)
- [x] **Common questions report** (what do patients ask most?)
- [x] **Daily/weekly email summaries** for clinic owners

### ✅ Phase 3: SMS & Patient Engagement (COMPLETE)
- [x] **Appointment confirmation SMS** (instant after booking)
- [x] **Appointment reminder SMS** (24h & 2h before)
- [x] **Post-call follow-up SMS** (thank you + next steps)
- [x] **Patient recall reminders** (6-month checkup)
- [x] **Review request SMS** (post-visit Google review ask)
- [x] **Bulk SMS campaigns** (recall reminders to multiple patients)

### ✅ Phase 4: Calendar & Booking (COMPLETE)
- [x] **Google Calendar integration** - Service account auth, busy times, create/cancel events
- [x] **Calendly integration** - API key auth, list events, get availability
- [x] **Real-time availability checking during calls** - Voice agent can check slots and speak them naturally
- [x] **No-show tracking and follow-up** - Mark no-shows, auto-SMS follow-up, reschedule tracking

**Files added:**
- `calendar_service.py` - Unified calendar service (Google Calendar + Calendly)
- `routes_calendar.py` - API endpoints for availability, appointments, no-shows

### 🎯 Phase 5: Advanced Patient Engagement (NEXT)
- [ ] Treatment plan follow-ups ("Time for your crown fitting!")
- [ ] Birthday/holiday greetings (patient retention)
- [ ] Insurance verification pre-call

### 🌍 Phase 5: Accessibility & Scale
- [ ] Multi-language support (Spanish, Vietnamese, Mandarin)
- [ ] After-hours emergency routing (urgent vs can wait)
- [ ] Wait time estimation during busy periods
- [ ] Multi-location support (clinic chains)
- [ ] White-label option for dental groups

### 🔌 Phase 6: Integrations (ENTERPRISE)
- [ ] Dentrix integration
- [ ] Eaglesoft integration
- [ ] Open Dental integration
- [ ] Curve Dental integration
- [ ] Custom PMS webhook support

### 💡 Future Vision
- [ ] AI-powered treatment recommendations
- [ ] Predictive no-show alerts
- [ ] Voice-based patient intake forms
- [ ] Automated insurance eligibility checks
- [ ] Patient portal with call history

## TCPA Compliance Notice

⚠️ **Important**: For outbound calls, only call leads who have provided consent or have an existing business relationship with your clinic. Do not use purchased lead lists. Ensure compliance with TCPA, state telemarketing laws, and the National Do Not Call Registry.

## License

MIT
