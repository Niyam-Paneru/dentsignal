# Copilot Instructions for this repo

## Big picture
- Two apps live here: a FastAPI voice backend in `dental_agent/` and a Next.js dashboard in `dashboard/`. Backend handles telephony (Twilio ↔ Deepgram), AI routing, CRM-style data; frontend renders the multi-tenant dashboard with Supabase auth.
- Inbound calls: Twilio webhook → `routes_inbound.py` builds TwiML, then media streams over WebSocket into the Deepgram bridge in `websocket_bridge.py` which converts mulaw↔linear16, buffers 200–400 ms chunks, tracks conversation state, and writes summary back to DB.
- Outbound calls and SMS: Celery tasks in `tasks.py` call Twilio via `twilio_service.py`; retry with exponential backoff; status webhooks handled by the legacy `routes_twilio` router.
- Prompts and voice configuration are per-clinic: `prompt_builder.py` loads research-based dental scripts and Deepgram Aura voice metadata, exposes `build_agent_config()` for the bridge.
- AI cost routing: `ai_providers.py` maps task types to OpenAI (real-time voice), Gemini (analysis/summaries), and Hugging Face (embeddings/search) with price-aware fallbacks.

## Run and develop (backend)
- Quick start with env checks: `python run_server.py` (add `--ngrok` to auto-fill API_BASE_URL/WS_BASE_URL and print Twilio webhook steps). For pure Uvicorn: `uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload`.
- Copy `dental_agent/.env.example` to `.env`; required: DEEPGRAM_API_KEY, OPENAI_API_KEY, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, DATABASE_URL (defaults to sqlite). TELEPHONY_MODE controls consent enforcement (SIMULATED vs TWILIO).
- Startup seeds demo admin `admin@dental.local / admin123` and a sample clinic in `api_main.py`.
- Celery/Redis optional for outbound calling; start Redis, then `celery -A celery_config worker --loglevel=info`. API_BASE_URL must be reachable by Twilio for webhooks.
- Tests: `python test_voice_agent.py` for the main suite; targeted modes `python test_voice_agent.py prompt|api|audio`. Integration flow tests live in `tests/integration_simulated.py`.

## Data and models
- Persistence uses SQLModel in `db.py`; `create_db()` runs at startup. Inbound and outbound calls are separate tables (`InboundCall` vs `Call`/`CallResult`). Enqueue outbound calls via `enqueue_calls_for_batch` on batches/leads.
- API schemas for clinics and inbound calls sit in `models.py`; FastAPI router files expect these shapes.

## Voice pipeline details
- Inbound websocket handler calls `handle_voice_websocket()` inside `websocket_bridge.py`: converts audio, handles barge-in, tracks `ConversationTracker`, sends Deepgram agent config from PromptBuilder, and writes transcript/analytics back via `update_inbound_call` in `routes_inbound.py`.
- Deepgram intents/STT/TTS helpers are in `deepgram_service.py`; Twilio call/SMS helpers are in `twilio_service.py`. Keep audio at 8 kHz; no resampling needed for Twilio streams.

## Logging and security
- Logging uses rotating files with PII masking in `utils.py`; prefer provided `setup_logger`/filters. JWT auth in `api_main.py` is demo-grade (plain password compare); do not ship as-is.
- Phone numbers must be normalized E.164; validators in `api_main.py` and helpers in utils enforce this. Consent is required for PSTN mode.

## Frontend (dashboard)
- Next.js App Router, Tailwind 4, Radix UI, Zustand. Scripts: `npm run dev|build|start|lint` in `dashboard/package.json`.
- Supabase auth SSR: middleware delegates to `src/lib/supabase/middleware.ts` to refresh sessions and gate protected routes (/dashboard, /live-calls, /calls, /calendar, /settings, /analytics, /superadmin). Auth routes redirect to /dashboard when logged in.
- Supabase clients: browser in `src/lib/supabase/client.ts`, server in `src/lib/supabase/server.ts`. Requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
- Dashboard shell wraps pages with `src/app/(dashboard)/layout.tsx` and Sidebar component; global styles in `src/app/globals.css`. Adjust navigation there when adding screens.
- **Multi-tenant data**: API functions in `src/lib/api/dental.ts` use `getUserClinicId()` to get the authenticated user's clinic from `dental_clinics.owner_id`. Never hardcode clinic IDs.
- **Super admin**: Only `niyampaneru79@gmail.com` has access. Hardcoded in `SUPER_ADMIN_EMAILS` array in `sidebar.tsx` and `superadmin/page.tsx`. Update both when adding admins.

## Database setup
- Supabase tables defined in `dashboard/supabase/migrations/001_create_dental_tables.sql`. Run in Supabase SQL Editor to create tables with RLS policies.
- Demo data template in `dashboard/supabase/migrations/002_seed_demo_data.sql`. Replace `YOUR_USER_ID_HERE` with user UUID from Supabase Auth > Users.
- Tables: `dental_clinics` (owner_id links to auth.users), `dental_clinic_settings`, `dental_calls`, `dental_appointments`, `dental_patients`. RLS ensures users only see their own clinic data.

## Patterns to follow
- Keep telephony URLs consistent with API_BASE_URL/WS_BASE_URL; Twilio Stream connects to /inbound/ws/{call_id} and posts status to /inbound/status/{call_id}.
- Reuse PromptBuilder instead of hardcoding prompts; per-clinic overrides should be stored on `Client` and passed through agent config.
- For new AI tasks, extend `TaskType` and `TASK_PROVIDER_MAP` in `ai_providers.py` so cost-aware routing stays centralized.
- When adding protected frontend routes, update the `protectedRoutes` list in `src/lib/supabase/middleware.ts` to keep redirects consistent.

## Deep research guidance
- Before implementing complex features, **ask the user to do deep research** via web search or documentation review to understand best practices, edge cases, and common pitfalls.
- For third-party integrations (Twilio, Deepgram, Supabase, etc.), always consult official docs first; API signatures and rate limits change frequently.
- When unsure about architectural decisions (e.g., real-time audio pipelines, multi-tenant RLS), gather context from the existing codebase patterns before proposing changes.
- Document research findings in relevant MD files (like RESEARCH_NOTES.md, DEEPGRAM_RESEARCH.md) so future sessions have context.
