# DentSignal Troubleshooting Guide

> Quick solutions for common issues with the AI Voice Agent

---

## 🔴 Voice Agent Not Answering Calls

### Symptoms
- Calls go straight to voicemail
- "All circuits are busy" message
- Long silence when call connects

### Solutions

**1. Check Deepgram API Key**
```bash
# Verify key is set
echo $DEEPGRAM_API_KEY

# Test Deepgram connection
python -c "
import os
from deepgram import Deepgram
dg = Deepgram(os.getenv('DEEPGRAM_API_KEY'))
print('Deepgram connection OK')
"
```

**2. Check Twilio Webhook Configuration**
```bash
# Your Twilio number should point to:
# Voice URL: https://api.dentsignal.me/inbound/incoming/{clinic_id}
# Method: POST

# Run the update script
python update_twilio.py
```

**3. Check Server is Running**
```bash
# Health check
curl https://api.dentsignal.me/health

# Expected: {"status": "healthy", "version": "1.0.0"}
```

**4. Check WebSocket URL**
- Ensure `WS_BASE_URL` uses `wss://` not `ws://` in production
- The WebSocket endpoint is: `/inbound/ws/{call_id}`

---

## 🔴 AI Gives Wrong Responses

### Symptoms
- Agent says incorrect clinic name
- Wrong business hours mentioned
- Doesn't follow custom instructions

### Solutions

**1. Check Clinic Settings**
```sql
-- In your database
SELECT name, agent_name, custom_greeting, custom_instructions 
FROM client WHERE id = YOUR_CLINIC_ID;
```

**2. Update Clinic Configuration**
```python
# Via API
PATCH /api/clinics/{clinic_id}
{
  "agent_name": "Sophie",
  "custom_greeting": "Thank you for calling Sunny Smiles Dental!",
  "custom_instructions": "Always mention our $99 new patient special"
}
```

**3. Clear Prompt Cache**
```bash
# Restart the server to rebuild prompts
uvicorn api_main:app --reload
```

---

## 🔴 Appointments Not Syncing to Calendar

### Symptoms
- Appointments booked but don't appear in Google Calendar
- "Calendar sync failed" errors in logs

### Solutions

**1. Verify Calendar Integration**
```bash
# Check integration status
curl /api/calendar/integration/{clinic_id}

# Should show:
# {"has_integration": true, "provider": "google", "is_active": true}
```

**2. Check Google Credentials**
```bash
# Ensure service account JSON is valid
python -c "
import json
with open('google-credentials.json') as f:
    creds = json.load(f)
    print(f'Service account: {creds.get(\"client_email\")}')
"
```

**3. Share Calendar with Service Account**
- Open Google Calendar
- Click gear icon → Settings
- Select your calendar
- Share with: `service-account@project.iam.gserviceaccount.com`
- Permission: "Make changes to events"

---

## 🔴 SMS Not Sending

### Symptoms
- Appointment confirmations not received
- Reminder SMS never arrives
- "SMS failed" in logs

### Solutions

**1. Check Twilio Balance**
```bash
# Login to Twilio Console
# Check Account → Billing → Current Balance
```

**2. Verify Phone Number Format**
```python
# Phone numbers must be E.164 format
# ✅ Correct: +15551234567
# ❌ Wrong: 555-123-4567, (555) 123-4567

# Test normalization
from utils import normalize_phone
print(normalize_phone("555-123-4567"))  # +15551234567
```

**3. Check Twilio Number Capabilities**
```bash
# Your Twilio number must have SMS capability
# Check: Twilio Console → Phone Numbers → Your Number → Capabilities
```

**4. Test SMS Manually**
```python
from twilio_service import send_sms
result = send_sms("+15551234567", "Test message from DentSignal")
print(result)
```

---

## 🔴 Dashboard Won't Load

### Symptoms
- Blank page after login
- "Failed to fetch" errors
- Infinite loading spinner

### Solutions

**1. Check API Connection**
```bash
# Frontend must reach backend
curl https://api.dentsignal.me/health

# Check CORS settings in api_main.py
# Make sure your dashboard URL is in allowed_origins
```

**2. Verify Environment Variables (Dashboard)**
```bash
# .env.local in dashboard/
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
NEXT_PUBLIC_API_URL=https://api.dentsignal.me
```

**3. Clear Browser Cache**
- Open DevTools (F12)
- Right-click Refresh → "Empty Cache and Hard Reload"

**4. Check Supabase Connection**
```bash
# Test Supabase
curl "https://YOUR_PROJECT.supabase.co/rest/v1/dental_clinics" \
  -H "apikey: YOUR_ANON_KEY"
```

---

## 🔴 Audio Quality Issues

### Symptoms
- Choppy audio during calls
- Echo or feedback
- Long delays between speech

### Solutions

**1. Check Audio Buffer Settings**
```python
# In websocket_bridge.py
AUDIO_BUFFER_SIZE = 3200    # 200ms (increase for stability)
AUDIO_BUFFER_MAX_MS = 400   # Max buffer (increase to 600 if choppy)
```

**2. Check Server Location**
- Server should be geographically close to most callers
- Recommended: US East (Virginia) for US callers

**3. Monitor WebSocket Latency**
```bash
# Check ping times to Deepgram
ping agent.deepgram.com
```

**4. Review Barge-in Settings**
- If users frequently interrupt: increase endpointing timeout
- If AI talks over users: decrease endpointing timeout

---

## 🔴 Database Errors

### Symptoms
- "Table not found" errors
- "Connection refused"
- Data not persisting

### Solutions

**1. Initialize Database**
```bash
# Run from dental_agent folder
python -c "from db import create_db; create_db()"
```

**2. Check DATABASE_URL**
```bash
# SQLite (development)
DATABASE_URL=sqlite:///./dev.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:pass@host:5432/dentsignal
```

**3. Run Migrations (if using PostgreSQL)**
```bash
# Apply migrations
alembic upgrade head
```

---

## 🔴 Authentication Failures

### Symptoms
- "Invalid token" after login
- Session expires immediately
- "Unauthorized" on all requests

### Solutions

**1. Check JWT_SECRET**
```bash
# Must be the same across restarts
echo $JWT_SECRET

# Generate a secure one
python -c "import secrets; print(secrets.token_hex(32))"
```

**2. Check Token Expiry**
```python
# In api_main.py
JWT_EXPIRY_HOURS = 24  # Increase if sessions expire too fast
```

**3. Verify Clock Sync**
```bash
# JWT validation is time-sensitive
timedatectl status
# Ensure NTP is synchronized
```

---

## 🔴 High API Costs

### Symptoms
- Unexpectedly high OpenAI bills
- Deepgram charges more than expected

### Solutions

**1. Check AI Provider Routing**
```python
# In ai_providers.py
# Verify cost-effective routing:
# - Use Gemini for analysis (50% cheaper)
# - Use OpenAI only for real-time voice
```

**2. Review Call Duration**
```bash
# Long calls = higher costs
# Check average call duration
curl /api/analytics/calls/{clinic_id}
```

**3. Enable Cost Tracking**
```bash
# Check usage endpoints
curl /api/usage/{clinic_id}
```

**4. Set Budget Alerts**
- Deepgram: Settings → Usage → Alerts
- OpenAI: Settings → Limits → Usage Limits
- Twilio: Account → Billing → Usage Triggers

---

## 📞 Getting Support

### Log Collection
```bash
# Collect logs for support
tail -500 logs/api.log > support_logs.txt

# Include in your support request:
# - Error messages
# - Call ID (if applicable)
# - Timestamp of issue
# - Steps to reproduce
```

### Contact
- Email: support@dentsignal.me
- Dashboard: Settings → Help & Support

---

## 🛠️ Quick Diagnostics Script

Run this to check system health:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

checks = [
    ('DEEPGRAM_API_KEY', os.getenv('DEEPGRAM_API_KEY', '')[:10] + '...' if os.getenv('DEEPGRAM_API_KEY') else 'MISSING'),
    ('TWILIO_SID', os.getenv('TWILIO_SID', '')[:10] + '...' if os.getenv('TWILIO_SID') else 'MISSING'),
    ('TWILIO_TOKEN', 'SET' if os.getenv('TWILIO_TOKEN') else 'MISSING'),
    ('DATABASE_URL', os.getenv('DATABASE_URL', 'NOT SET')),
    ('JWT_SECRET', 'SET' if os.getenv('JWT_SECRET') else 'MISSING (using default!)'),
]

print('=== DentSignal Diagnostics ===')
for name, value in checks:
    status = '✅' if 'MISSING' not in value else '❌'
    print(f'{status} {name}: {value}')
"
```
