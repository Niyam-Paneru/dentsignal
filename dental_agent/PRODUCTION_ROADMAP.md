# 🦷 Dental AI Voice Agent - Production Roadmap

## Current Status: ✅ MVP Complete
- AI Voice Agent working with Deepgram + OpenAI
- Twilio integration ready
- Professional dental scripts (CARES Framework)
- Local testing passed

---

## Phase 1: Full Testing (Week 1)
**After Twilio $20 upgrade**

- [ ] Test real inbound calls
- [ ] Test call transfers
- [ ] Measure latency/response time
- [ ] Record sample calls for review
- [ ] Fine-tune prompts based on real conversations

---

## Phase 2: Web Dashboard (Week 2-3)

### Tech Stack Recommendation
```
Frontend: Next.js + Tailwind CSS + shadcn/ui
Backend:  FastAPI (existing) + PostgreSQL
Auth:     Clerk or NextAuth
Hosting:  Vercel (frontend) + Railway (backend)
```

### Dashboard Pages

#### 1. **Login/Signup**
- Clinic owner authentication
- Multi-tenant (each clinic sees only their data)

#### 2. **Dashboard Home**
```
┌─────────────────────────────────────────────────────┐
│  📊 Today's Overview                                │
├─────────────────┬─────────────────┬─────────────────┤
│  Calls: 23      │  Booked: 8      │  Missed: 2      │
├─────────────────┴─────────────────┴─────────────────┤
│  📈 This Week                                        │
│  [=========== 85% ============]  Booking Rate       │
├─────────────────────────────────────────────────────┤
│  🕐 Recent Calls                                     │
│  • 2:30 PM - John Smith - Cleaning booked ✅        │
│  • 2:15 PM - Mary Jones - Insurance question        │
│  • 1:45 PM - New Patient - Toothache - URGENT 🔴   │
└─────────────────────────────────────────────────────┘
```

#### 3. **Call History**
- List all calls with:
  - Date/time
  - Caller phone number
  - Duration
  - Outcome (booked, transferred, info only)
  - Full transcript
  - Audio playback (optional)

#### 4. **Calendar/Appointments**
```
┌─────────────────────────────────────────────────────┐
│  December 2025                    < Today >          │
├─────┬─────┬─────┬─────┬─────┬─────┬─────────────────┤
│ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │                 │
├─────┼─────┼─────┼─────┼─────┼─────┤   9:00 AM       │
│  8  │  9  │ 10  │ 11  │ 12  │ 13  │   John - Clean  │
│     │ ●●  │  ●  │ ●●● │  ●  │     │                 │
├─────┴─────┴─────┴─────┴─────┴─────┤   10:30 AM      │
│                                    │   Mary - Exam   │
│  ● = Appointments booked by AI     │                 │
└────────────────────────────────────┴─────────────────┘
```

#### 5. **Settings**
- Clinic Information
  - Name, address, phone
  - Business hours
  - Holiday schedule
  
- AI Agent Settings
  - Agent name (Sarah, Jessica, etc.)
  - Voice selection
  - Greeting customization
  - Services offered
  - Dentist names
  
- Integrations
  - Google Calendar sync
  - SMS notifications
  - Email confirmations

#### 6. **Analytics**
- Call volume by day/week/month
- Peak calling hours
- Booking conversion rate
- Common call reasons
- Average call duration
- Cost per call

---

## Phase 3: Calendar Integration (Week 3-4)

### Option A: Google Calendar (Recommended to Start)
**Pros:** Free, easy to set up, most clinics use it
**Implementation:**
```python
# Example: Book appointment to Google Calendar
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def book_to_google_calendar(
    patient_name: str,
    date: str,
    time: str,
    service: str,
    clinic_calendar_id: str
):
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': f'{patient_name} - {service}',
        'start': {'dateTime': f'{date}T{time}:00'},
        'end': {'dateTime': f'{date}T{end_time}:00'},
    }
    service.events().insert(calendarId=clinic_calendar_id, body=event).execute()
```

### Option B: Calendly Integration
**Pros:** Professional scheduling, automated reminders
**Use case:** Send caller a booking link via SMS

### Option C: Custom Calendar (Built-in)
**Pros:** Full control, no external dependencies
**Cons:** More work to build

### Option D: Dental Practice Management Software
- **Dentrix** - Most popular, has API
- **Open Dental** - Open source, good API
- **Eaglesoft** - Common in US
- **Curve Dental** - Cloud-based

---

## Phase 4: Production Deployment (Week 4-5)

### Infrastructure
```
┌─────────────────────────────────────────────────────┐
│                    PRODUCTION                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐     ┌─────────────┐                │
│  │   Vercel    │     │  Railway    │                │
│  │  (Frontend) │────▶│  (Backend)  │                │
│  │   Next.js   │     │   FastAPI   │                │
│  └─────────────┘     └──────┬──────┘                │
│                              │                       │
│         ┌────────────────────┼────────────────┐     │
│         ▼                    ▼                ▼     │
│  ┌─────────────┐     ┌─────────────┐  ┌───────────┐│
│  │   Twilio    │     │  Deepgram   │  │ PostgreSQL││
│  │  (Phone)    │     │  (Voice AI) │  │ (Database)││
│  └─────────────┘     └─────────────┘  └───────────┘│
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Domain Setup
- Buy domain: `dentalvoiceai.com` or similar
- Point to Vercel (frontend)
- API subdomain: `api.dentalvoiceai.com` → Railway

### Monthly Costs (Per Clinic)
| Service | Cost |
|---------|------|
| Twilio (number + calls) | ~$3-5 |
| Deepgram (voice) | ~$5-10 |
| OpenAI (LLM) | ~$2-5 |
| Railway (hosting) | ~$5 |
| Vercel (frontend) | Free tier |
| PostgreSQL | Included in Railway |
| **Total** | **~$15-25/month** |

### Pricing Strategy
| Plan | Price | Target |
|------|-------|--------|
| Starter | $49/mo | Solo dentist |
| Professional | $99/mo | Small practice |
| Enterprise | $199/mo | Multi-location |

---

## Phase 5: Advanced Features (Month 2+)

### SMS Features
- [ ] Appointment confirmations
- [ ] Reminder texts (24h before)
- [ ] Reschedule links
- [ ] Review requests after visit

### Voice Features
- [ ] Outbound reminder calls
- [ ] Recall/reactivation calls
- [ ] Post-visit follow-ups

### Analytics Dashboard
- [ ] Call recordings playback
- [ ] Sentiment analysis
- [ ] Missed opportunity alerts
- [ ] ROI calculator

### Multi-Language
- [ ] Spanish support
- [ ] Other languages as needed

---

## Immediate Next Steps

### This Week
1. ⬜ Wait for Twilio upgrade
2. ⬜ Test real calls thoroughly
3. ⬜ Set up PostgreSQL database
4. ⬜ Create database schema for multi-clinic

### Next Week
1. ⬜ Start Next.js frontend project
2. ⬜ Build login/authentication
3. ⬜ Create dashboard home page
4. ⬜ Build call history page

### Week 3
1. ⬜ Google Calendar integration
2. ⬜ Settings page
3. ⬜ Deploy to production
4. ⬜ Get first beta clinic

---

## Database Schema (Multi-Tenant)

```sql
-- Clinics (tenants)
CREATE TABLE clinics (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(20),
    twilio_number VARCHAR(20),
    address TEXT,
    business_hours JSONB,
    created_at TIMESTAMP
);

-- Clinic Settings
CREATE TABLE clinic_settings (
    clinic_id UUID REFERENCES clinics(id),
    agent_name VARCHAR(100),
    agent_voice VARCHAR(100),
    greeting_template TEXT,
    services JSONB,
    dentist_names JSONB,
    PRIMARY KEY (clinic_id)
);

-- Calls
CREATE TABLE calls (
    id UUID PRIMARY KEY,
    clinic_id UUID REFERENCES clinics(id),
    caller_phone VARCHAR(20),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    outcome VARCHAR(50),
    transcript TEXT,
    recording_url TEXT,
    patient_id UUID REFERENCES patients(id)
);

-- Appointments (booked by AI)
CREATE TABLE appointments (
    id UUID PRIMARY KEY,
    clinic_id UUID REFERENCES clinics(id),
    patient_id UUID REFERENCES patients(id),
    call_id UUID REFERENCES calls(id),
    scheduled_date DATE,
    scheduled_time TIME,
    service_type VARCHAR(100),
    status VARCHAR(50),
    google_event_id VARCHAR(255),
    created_at TIMESTAMP
);

-- Patients
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    clinic_id UUID REFERENCES clinics(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    date_of_birth DATE,
    insurance_provider VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP
);
```

---

## Questions to Decide

1. **Calendar System**: Google Calendar vs custom-built?
2. **Frontend Framework**: Next.js vs React + Vite?
3. **First Beta Clinic**: Do you have a dental clinic to test with?
4. **Branding**: Product name? (DentalVoiceAI, ToothTalk, etc.)
5. **Target Market**: US only? International?

---

## Resources

### Tutorials Needed
- [ ] Next.js + Tailwind dashboard tutorial
- [ ] Google Calendar API integration
- [ ] Twilio webhook best practices
- [ ] PostgreSQL with FastAPI

### Tools to Set Up
- [ ] GitHub repo (version control)
- [ ] Railway account (backend hosting)
- [ ] Vercel account (frontend hosting)
- [ ] Clerk account (authentication)

---

**Ready to start on the web dashboard?** Let me know and I'll create the Next.js project structure! 🚀
