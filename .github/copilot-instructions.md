# Copilot Instructions for DentSignal

## Big picture
- **Product name**: DentSignal - AI Voice Agent for Dental Practices
- Two apps live here: a FastAPI voice backend in `dental_agent/` and a Next.js dashboard in `dashboard/`. Backend handles telephony (Twilio ↔ Deepgram), AI routing, CRM-style data; frontend renders the multi-tenant SaaS dashboard with Supabase auth.
- Inbound calls: Twilio webhook → `routes_inbound.py` builds TwiML, then media streams over WebSocket into the Deepgram bridge in `websocket_bridge.py` which converts mulaw↔linear16, buffers 200–400 ms chunks, tracks conversation state, and writes summary back to DB.
- Outbound calls and SMS: Celery tasks in `tasks.py` call Twilio via `twilio_service.py`; retry with exponential backoff; status webhooks handled by the legacy `routes_twilio` router.
- Prompts and voice configuration are per-clinic: `prompt_builder.py` loads research-based dental scripts and Deepgram Aura voice metadata, exposes `build_agent_config()` for the bridge.
- AI cost routing: `ai_providers.py` maps task types to OpenAI (real-time voice), Gemini (analysis/summaries), and Hugging Face (embeddings/search) with price-aware fallbacks.
- Practice-specific playbooks in `playbooks/` folder: `general-practice.md`, `pediatric-practice.md`, `solo-practice.md`, `specialty-practice.md`.

## Run and develop (backend)
- Quick start with env checks: `python run_server.py` (add `--ngrok` to auto-fill API_BASE_URL/WS_BASE_URL and print Twilio webhook steps). For pure Uvicorn: `uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload`.
- Copy `dental_agent/.env.example` to `.env`; required: DEEPGRAM_API_KEY, OPENAI_API_KEY, TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER, DATABASE_URL (defaults to sqlite). TELEPHONY_MODE controls consent enforcement (SIMULATED vs TWILIO).
- Startup seeds demo admin `admin@dental.local / admin123` and a sample clinic in `api_main.py`.
- Celery/Redis optional for outbound calling; start Redis, then `celery -A celery_config worker --loglevel=info`. API_BASE_URL must be reachable by Twilio for webhooks.
- Tests: `python test_voice_agent.py` for the main suite; targeted modes `python test_voice_agent.py prompt|api|audio`. Integration flow tests live in `tests/integration_simulated.py`.
- PowerShell dev script: `start_dev.ps1` for local development setup.

## Data and models
- Persistence uses SQLModel in `db.py`; `create_db()` runs at startup. Inbound and outbound calls are separate tables (`InboundCall` vs `Call`/`CallResult`). Enqueue outbound calls via `enqueue_calls_for_batch` on batches/leads.
- API schemas for clinics and inbound calls sit in `models.py`; FastAPI router files expect these shapes.
- Backend routers: `routes_inbound.py`, `routes_calls.py`, `routes_calendar.py`, `routes_analytics.py`, `routes_sms.py`, `routes_admin.py`, `routes_superadmin.py`, `routes_usage.py`, `routes_twilio.py`.

## Voice pipeline details
- Inbound websocket handler calls `handle_voice_websocket()` inside `websocket_bridge.py`: converts audio, handles barge-in, tracks `ConversationTracker`, sends Deepgram agent config from PromptBuilder, and writes transcript/analytics back via `update_inbound_call` in `routes_inbound.py`.
- Deepgram intents/STT/TTS helpers are in `deepgram_service.py`; Twilio call/SMS helpers are in `twilio_service.py`. Keep audio at 8 kHz; no resampling needed for Twilio streams.
- Agent config stored in `agent_config/dental_receptionist.json`.

## Logging and security
- Logging uses rotating files with PII masking in `utils.py`; prefer provided `setup_logger`/filters. JWT auth in `api_main.py` is demo-grade (plain password compare); do not ship as-is.
- Phone numbers must be normalized E.164; validators in `api_main.py` and helpers in utils enforce this. Consent is required for PSTN mode.
- Rate limiting middleware in `rate_limiter.py`.

## Frontend (dashboard)
- **Stack**: Next.js 16 App Router, React 19, Tailwind CSS 4, Radix UI, Zustand, Recharts for analytics, TanStack Table for data tables.
- Scripts: `npm run dev|build|start|lint` and `npm run test:e2e` (Playwright) in `dashboard/package.json`.
- Supabase auth SSR: middleware delegates to `src/lib/supabase/middleware.ts` to refresh sessions and gate protected routes (/dashboard, /live-calls, /calls, /calendar, /settings, /analytics, /superadmin). Auth routes redirect to /dashboard when logged in.
- Supabase clients: browser in `src/lib/supabase/client.ts`, server in `src/lib/supabase/server.ts`. Requires NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.

## Frontend structure
- **Landing page**: `src/app/page.tsx` with marketing components in `src/components/landing/` (marketing-header.tsx, marketing-footer.tsx, roi-calculator.tsx).
- **Auth pages**: `src/app/login/`, `src/app/signup/`, `src/app/logout/`.
- **Legal pages**: `src/app/pricing/`, `src/app/privacy/`, `src/app/terms/`.
- **Dashboard shell**: wraps pages with `src/app/(dashboard)/layout.tsx` and Sidebar component in `src/components/layout/sidebar.tsx`; global styles in `src/app/globals.css`.
- **Dashboard pages**: `/dashboard`, `/live-calls`, `/calls`, `/calendar`, `/analytics`, `/settings`, `/superadmin`.
- **Dashboard components**: `src/components/dashboard/` contains `calls-chart.tsx`, `recent-calls-table.tsx`, `onboarding-progress.tsx`, `call-forwarding-guide.tsx`.
- **UI components**: `src/components/ui/` for Radix-based primitives.
- **Cloudflare Turnstile**: Bot protection via `src/components/turnstile.tsx`.

## Multi-tenant data
- API functions in `src/lib/api/dental.ts` use `getUserClinicId()` to get the authenticated user's clinic from `dental_clinics.owner_id`. Never hardcode clinic IDs.
- Dashboard stats, calls, appointments all filter by clinic_id automatically.

## Super admin
- Super admin email: `founder@dentsignal.me`. Defined in `SUPER_ADMIN_EMAILS` array in:
  - `dashboard/src/components/layout/sidebar.tsx`
  - `dashboard/src/app/(dashboard)/superadmin/page.tsx`
  - `dental_agent/routes_superadmin.py` (reads from env var `SUPER_ADMIN_EMAILS`)
- Update all three locations when adding new platform admins.

## Database setup
- Supabase migrations in `dashboard/supabase/migrations/`:
  - `001_create_dental_tables.sql` - Core tables with RLS policies
  - `002_seed_demo_data.sql` - Demo data template (replace YOUR_USER_ID_HERE)
  - `003_add_clinic_onboarding_fields.sql` - Onboarding tracking
  - `003_quick_setup.sql` - Quick setup helper
  - `004_security_performance_fixes.sql` - Security and performance improvements
- Tables: `dental_clinics` (owner_id links to auth.users), `dental_clinic_settings`, `dental_calls`, `dental_appointments`, `dental_patients`. RLS ensures users only see their own clinic data.

## Public assets
- Logo files in `dashboard/public/`: `logo.png`, `logo.svg`, `favicon.ico`, `favicon.png`, `icon.svg`.
- Brand assets in `brand/logos/` folder.
- SEO files: `robots.txt`, `sitemap.xml`.

## Testing
- Backend: `pytest` with config in `dental_agent/pytest.ini`. Test files: `test_voice_agent.py`, `test_api.py`, `test_ai_providers.py`, `test_agent_responses.py`, `test_deepgram_connection.py`.
- Frontend: Playwright E2E tests in `dashboard/tests/e2e.spec.ts`. Run with `npm run test:e2e`.
- TestSprite config in `dashboard/testsprite_tests/` and `dental_agent/testsprite_tests/`.

## Documentation
- API docs: `dental_agent/API_DOCUMENTATION.md`
- Troubleshooting: `dental_agent/TROUBLESHOOTING.md`
- Research and planning docs in `docs/` folder: `copilot-context/`, `planning/`, `research/`, `technical/`.
- Sales materials in `sales/` folder.
- Site audit docs in `site-audit/` folder.
- Psychology research in `psychology/` folder.

## Patterns to follow
- Keep telephony URLs consistent with API_BASE_URL/WS_BASE_URL; Twilio Stream connects to /inbound/ws/{call_id} and posts status to /inbound/status/{call_id}.
- Reuse PromptBuilder instead of hardcoding prompts; per-clinic overrides should be stored on `Client` and passed through agent config.
- For new AI tasks, extend `TaskType` and `TASK_PROVIDER_MAP` in `ai_providers.py` so cost-aware routing stays centralized.
- When adding protected frontend routes, update the `protectedRoutes` list in `src/lib/supabase/middleware.ts` to keep redirects consistent.
- Use `date-fns` for date formatting in frontend.
- Use Lucide icons consistently across the app.

## Deep research guidance
- Before implementing complex features, **ask the user to do deep research** via web search or documentation review to understand best practices, edge cases, and common pitfalls.
- For third-party integrations (Twilio, Deepgram, Supabase, etc.), always consult official docs first; API signatures and rate limits change frequently.
- When unsure about architectural decisions (e.g., real-time audio pipelines, multi-tenant RLS), gather context from the existing codebase patterns before proposing changes.
- Document research findings in relevant MD files (like those in `docs/research/`) so future sessions have context.
