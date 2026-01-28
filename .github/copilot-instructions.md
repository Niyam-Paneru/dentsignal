# Copilot Instructions for DentSignal

## 🎯 Special Commands

### `{divide}` Command
When user says **`{divide}`** followed by any task:
1. **Break the task into small, focused prompts** (each completable in one session)
2. **List them with clear labels** (e.g., `TASK-1`, `TASK-2`, `RW-1`, `DOC-1`)
3. **Wait for user to specify which prompt(s) to execute**
4. **Focus 100% on only the selected task(s)**

Example usage:
- User: `{divide} research RevenueWell competitor`
- Copilot: Lists prompts like `RW-1: Product Overview`, `RW-2: Pricing`, etc.
- User: `Do RW-1`
- Copilot: Executes only that specific task

This allows the user to:
- Choose task priority order
- Work in focused sessions
- Pause and resume easily
- Have clear visibility into work breakdown

---

## � OpenSpec (Auto-Triggered for Large Features)

**OpenSpec is installed for spec-driven development. Use it AUTOMATICALLY when appropriate.**

### When to USE OpenSpec (without being asked):
- User requests a **new feature** with 3+ files or components
- User asks for something **complex** (e.g., "add call transfer", "implement analytics dashboard")
- Task requires **planning** before coding (architecture decisions, multi-step workflows)
- User says keywords: "feature", "implement", "build", "add [major thing]", "refactor [system]"

### When NOT to use OpenSpec:
- Quick fixes, bug fixes, typos
- Single-file changes
- Config updates
- Questions/research (no code changes)
- User explicitly says "quick" or "just do it"

### Auto-Trigger Workflow:
1. **Detect** large feature request
2. **Announce**: "This looks like a multi-step feature. I'll use OpenSpec to plan it first."
3. **Run**: `/opsx:new <feature-name>`
4. **Generate**: `/opsx:ff` (fast-forward to create proposal, specs, design, tasks)
5. **Show user** the generated plan
6. **Ask**: "Ready to implement?" 
7. **If yes**: `/opsx:apply` to implement tasks
8. **Archive**: `/opsx:archive` when complete

### Quick Reference:
| Command | What it does |
|---------|--------------|
| `/opsx:new <name>` | Start a new change folder |
| `/opsx:ff` | Fast-forward: generate all planning docs |
| `/opsx:apply` | Implement the tasks |
| `/opsx:archive` | Archive completed change |
| `/opsx:status` | Check current change status |

---

## �🔧 MCP Server Usage (MANDATORY)

**Always use MCP servers for every task. Open necessary servers FIRST before doing any work.**

### Available MCP Servers & When to Use

| Server | Use For | Activate When |
|--------|---------|---------------|
| **Serena** | Code navigation, refactoring, understanding codebase structure | Always - reduces token usage by 40-60% |
| **Supabase** | Query database, check tables, manage data | Database questions, debugging data issues |
| **GitHub** | Create issues, PRs, manage repo | Version control tasks |
| **Postgres** | Direct SQL queries on production DB | Data analysis, migrations |
| **Fetch** | Make HTTP requests, test APIs | Testing endpoints, external API calls |
| **Memory** | Remember user preferences across sessions | Long-term context |
| **Playwright** | Browser automation, E2E testing | Testing UI, screenshots |
| **Chrome DevTools** | Inspect pages, debug frontend | UI debugging, performance |
| **Pylance** | Python code execution, syntax checking, imports | Python development |

### Serena Benefits (Primary MCP)
- **Semantic code search** - finds code by meaning, not just text
- **Smart refactoring** - understands code relationships
- **Reduced token usage** - caches codebase understanding
- **Cross-file navigation** - follows imports and references automatically

### MCP Usage Rules
1. Before ANY task, identify which MCP servers are needed
2. Activate them without being asked
3. Prefer MCP tools over manual file reading when available
4. Use Serena for code navigation instead of multiple `read_file` calls
5. Use Supabase/Postgres for database queries instead of suggesting SQL
6. Use Fetch for API testing instead of suggesting curl commands

---

## Architecture overview
- **DentSignal**: Multi-tenant AI Voice Agent SaaS for dental practices
- **Backend** (`dental_agent/`): FastAPI + Celery handling Twilio↔Deepgram telephony, AI routing, CRM data
- **Frontend** (`dashboard/`): Next.js 16 App Router + Supabase auth, React 19, Tailwind 4, Radix UI
- **Pricing**: $199/month flat (all-inclusive)

### ROI Assumptions (Defensible)
| Metric | Value | Notes |
|--------|-------|-------|
| Total missed calls/month | 300 | All types (clinical, reschedules, etc.) |
| New-patient missed calls | 25/month | ≈8% of total (conservative) |
| New patient Year 1 value | $850 | Conservative (LTV is $3k-$7k+) |
| Monthly loss | $21,250 | 25 × $850 |
| Annual loss | $255,000 | $21,250 × 12 |
| DentSignal cost | $2,388/year | $199 × 12 |
| ROI | 107× | $255k ÷ $2,388 |

> **Sales talking point:** "We're only counting 25 missed new-patient calls a month at $850 each and ignoring all the hygiene/reschedule calls. Most practices miss more than that, so this model is conservative."

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

> **📁 All docs are organized under `docs/` - see [docs/INDEX.md](docs/INDEX.md) for navigation**

| Category | Path | Key Files |
|----------|------|-----------|
| **Planning** | `docs/planning/` | ROADMAP.md, TODO_MASTER.md, PRODUCTION_ROADMAP.md |
| **Research** | `docs/research/` | COMPETITOR_RESEARCH.md, PSYCHOLOGY_DEEP_DIVE.md |
| **Technical** | `docs/technical/` | DEEPGRAM_RESEARCH.md, Twilio Media Streams Optimization.md |
| **Marketing** | `docs/marketing/` | ROI_CALCULATOR_PROMPT.md, case_study_real_math.md |
| **Backend API** | `dental_agent/` | API_DOCUMENTATION.md, TROUBLESHOOTING.md, TWILIO_SETUP.md |

## AI Skills (Auto-loaded)

### Domain-Specific Skills
- **deepgram-twilio-voice** - Real-time voice AI with Deepgram Voice Agent and Twilio. See `.github/skills/deepgram-twilio-voice/SKILL.md`
- **dental-voice-deployment** - Setup guide for new clinic instances. See `.github/skills/dental-voice-deployment/SKILL.md`
- **fastapi-celery-automation** - Background task automation patterns. See `.github/skills/fastapi-celery-automation/SKILL.md`
- **postgres-best-practices** - Supabase Postgres optimization rules for queries, indexes, RLS, and schema design. See `.github/skills/postgres-best-practices/SKILL.md`

### Frontend Optimization Skills (Vercel)
- **react-best-practices** - 40+ React/Next.js performance optimization rules from Vercel Engineering. Auto-applied when writing components, data fetching, or optimizing bundle size. See `~/.agents/skills/vercel-react-best-practices/SKILL.md`
- **web-design-guidelines** - 100+ accessibility, UX, and performance rules. Auto-applied when reviewing UI code or implementing forms/animations. See `~/.agents/skills/web-design-guidelines/SKILL.md`
