# Copilot Instructions for DentSignal

## Architecture overview
- **DentSignal**: Multi-tenant AI Voice Agent SaaS for dental practices
- **Backend** (`dental_agent/`): FastAPI + Celery handling Twilio↔Deepgram telephony, AI routing, CRM data
- **Frontend** (`dashboard/`): Next.js 16 App Router + Supabase auth, React 19, Tailwind 4, Radix UI

### Voice call flow
1. Inbound: Twilio webhook → `routes_inbound.py` TwiML → WebSocket at `/inbound/ws/{call_id}`
2. `websocket_bridge.py` converts mulaw↔linear16 (8kHz, no resampling), buffers 200-400ms chunks
3. Deepgram Voice Agent handles STT+LLM+TTS via `wss://agent.deepgram.com/v1/agent/converse`
4. Outbound: Celery tasks in `tasks.py` → `twilio_service.py` with exponential backoff retry

### AI cost routing (`ai_providers.py`)
- OpenAI: real-time voice (latency-critical)
- Gemini: post-call analysis, sentiment, summaries (50% cheaper)
- Hugging Face: embeddings, search (free)
- Extend `TaskType` and `TASK_PROVIDER_MAP` for new AI tasks

## Development commands

### Backend
```bash
cd dental_agent
python run_server.py           # Quick start with env checks (--ngrok for tunnels)
uvicorn api_main:app --reload  # Pure Uvicorn
celery -A celery_config worker --loglevel=info  # Outbound calls (requires Redis)
python test_voice_agent.py     # Main test suite (modes: prompt|api|audio)
```

### Frontend
```bash
cd dashboard
npm run dev      # Development server at localhost:3000
npm run build    # Production build
npm run test:e2e # Playwright E2E tests
```

## Key patterns

### Multi-tenancy
- Frontend: `getUserClinicId()` in `src/lib/api/dental.ts` resolves clinic from `dental_clinics.owner_id`
- Backend: SQLModel in `db.py`, separate tables for `InboundCall` vs `Call`/`CallResult`
- **Never hardcode clinic IDs** - all queries filter by authenticated user's clinic

### Per-clinic configuration
- `prompt_builder.py` → `build_agent_config()` loads clinic-specific prompts and Deepgram voice settings
- Store overrides on `Client` model, not inline prompts
- Playbooks in `playbooks/` folder define practice-type scripts

### Protected routes (frontend)
- Update `protectedRoutes` array in `src/lib/supabase/middleware.ts` when adding dashboard pages
- Current: `/dashboard`, `/live-calls`, `/calls`, `/calendar`, `/settings`, `/analytics`, `/superadmin`

### Super admin sync
- `SUPER_ADMIN_EMAILS` defined in **3 places** - update all when adding admins:
  1. `dashboard/src/components/layout/sidebar.tsx`
  2. `dashboard/src/app/(dashboard)/superadmin/page.tsx`
  3. `dental_agent/routes_superadmin.py` (reads from env var)

### Phone number handling
- Normalize to E.164 format using validators in `utils.py`
- Consent required when `TELEPHONY_MODE=TWILIO`

## Database
- Backend: SQLModel + SQLite (dev) or PostgreSQL via `DATABASE_URL`
- Frontend: Supabase with RLS policies in `dashboard/supabase/migrations/`
- Tables: `dental_clinics`, `dental_calls`, `dental_appointments`, `dental_patients`

## Environment variables
Backend (`dental_agent/.env`): `DEEPGRAM_API_KEY`, `OPENAI_API_KEY`, `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_NUMBER`, `DATABASE_URL`, `TELEPHONY_MODE`
Frontend (`dashboard/.env.local`): `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Conventions
- Frontend icons: Lucide React exclusively
- Date formatting: `date-fns`
- Logging: Use `setup_logger()` from `utils.py` with PII masking
- Telephony URLs: Match `API_BASE_URL`/`WS_BASE_URL` for Twilio webhooks

## Key documentation
- [API_DOCUMENTATION.md](dental_agent/API_DOCUMENTATION.md) - Backend API reference
- [TROUBLESHOOTING.md](dental_agent/TROUBLESHOOTING.md) - Common issues
- `docs/research/` - Integration research findings
