# Dental AI Voice Agent - Next Steps & Research

## 📋 Current Status
- ✅ FastAPI backend set up
- ✅ Twilio account with US number (+19048679643)
- ✅ Deepgram account with API key
- ✅ Basic SQLModel ORM configured
- ✅ Research completed - Deepgram Voice Agent API confirmed!
- ⏳ Ready to implement real voice agent

---

## 🔬 Research Results (COMPLETED)

### ✅ Deepgram Voice Agent API - CONFIRMED!
**Launched June 2025** - This is exactly what we need!

| Product | What It Does | Use Case |
|---------|-------------|----------|
| **Nova-3** (STT) | Speech-to-text only | Manual orchestration |
| **Aura-2** (TTS) | Text-to-speech only | Manual orchestration |
| **Voice Agent API** | STT + LLM + TTS + turn-taking + barge-in | **USE THIS!** |

**Key Features:**
- ✅ One WebSocket connection handles everything
- ✅ Built-in turn-taking & barge-in detection
- ✅ Bring your own LLM (GPT-4, Claude) OR use Deepgram's
- ✅ ~300-600ms latency per turn
- ❗ You still need: intent routing, appointment booking logic

### ✅ Twilio Media Streams - CONFIRMED!

**Architecture:**
```
Caller → Twilio → WebSocket (mulaw/8000) → FastAPI → Deepgram Voice Agent
                                              ↓
                                   (process + TTS back)
                                              ↓
                                          Twilio → Caller
```

**Audio Format Specs:**
| Property | Twilio Format | Deepgram Format |
|----------|--------------|-----------------|
| Encoding | mulaw (µ-law) | linear16 (PCM) |
| Sample Rate | 8000 Hz | 8000 or 16000 Hz |
| Channels | 1 (mono) | 1 (mono) |
| Payload | Base64-encoded | Base64-encoded |

**You must convert:** `mulaw ↔ linear16` using `audioop`

### ✅ Cost Estimates (Per Dental Clinic)
Assuming 20 calls/day × 3 min average = 60 min/day:

| Service | Cost/min | Daily | Monthly |
|---------|----------|-------|---------|
| Deepgram STT | $0.0043 | $0.26 | ~$8 |
| Deepgram TTS | $0.0079 | $0.47 | ~$14 |
| Twilio PSTN | $0.025 | $1.50 | ~$45 |
| **Total** | | | **~$67/month** |

**You charge:** $199-299/month → **$130-230 profit per clinic**

### ✅ Latency Breakdown
| Step | Time |
|------|------|
| Twilio → WebSocket | ~50ms |
| Deepgram STT | ~100ms |
| LLM response | ~200-300ms |
| Deepgram TTS | ~50-100ms |
| Back to Twilio | ~50ms |
| **Total** | **300-600ms** |

---

## 🏗️ Implementation Plan (UPDATED)

### Phase 1: Data Models (Multi-Tenant)
```python
# models.py additions needed:

class Clinic(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    twilio_number: str           # assigned Twilio number
    address: str
    hours: str
    services: str                # JSON string
    insurance_accepted: str
    agent_name: str              # e.g., "Sarah"
    agent_voice: str             # Deepgram voice ID e.g., "aura-asteria-en"
    custom_instructions: str
    owner_email: str
    monthly_price: int
    is_active: bool = True

class Call(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    clinic_id: int = Field(foreign_key="clinic.id")
    from_number: str             # patient number
    to_number: str               # clinic Twilio number
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    status: str                  # "in_progress", "completed", "failed"
    outcome: str | None          # "booked", "no_answer", "hangup", etc.
    transcript: str | None
```

### Phase 2: Prompt Builder
```python
# prompt_builder.py - builds per-clinic system prompt
def build_clinic_prompt(clinic: Clinic) -> str:
    """
    Build a customized system prompt for Deepgram Voice Agent.
    Includes: clinic name, address, hours, services, agent personality.
    """
    pass
```

### Phase 3: WebSocket Bridge (Twilio ↔ Deepgram)
```python
# websocket_bridge.py - THE CORE OF THE SYSTEM

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    1. Receive mulaw audio from Twilio (base64)
    2. Convert mulaw → linear16 (for Deepgram)
    3. Send to Deepgram Voice Agent
    4. Receive TTS response from Deepgram
    5. Convert linear16 → mulaw (for Twilio)
    6. Send back to Twilio
    """
    pass
```

### Phase 4: Twilio Inbound Webhook
```python
# routes_twilio.py
@app.post("/twilio/incoming")
async def incoming_call(request: Request):
    """
    1. Parse To/From from Twilio
    2. Look up Clinic by twilio_number
    3. Create Call record in DB
    4. Return TwiML with <Connect><Stream>
    """
    response = VoiceResponse()
    connect = response.connect()
    connect.stream(url="wss://your-ngrok-url/ws")
    return HTMLResponse(str(response), media_type="application/xml")
```

### Phase 5: Admin API Endpoints
```python
# routes_admin.py
POST /api/clinics              # Create clinic
GET  /api/clinics/{id}         # Get clinic details
GET  /api/clinics/{id}/calls   # List calls for clinic
GET  /api/calls/{id}           # Get call with transcript
```

---

## 🔧 Key Code: Audio Format Conversion

```python
import audioop
import base64

# Twilio sends mulaw → convert to linear16 (for Deepgram)
mulaw_audio = base64.b64decode(payload)
linear16_audio = audioop.ulaw2lin(mulaw_audio, 2)

# Deepgram TTS returns linear16 → convert back to mulaw (for Twilio)
tts_linear16 = deepgram_response["audio"]
tts_mulaw = audioop.lin2ulaw(tts_linear16, 2)
base64_payload = base64.b64encode(tts_mulaw).decode()
```

---

## 🔧 Key Code: TwiML for Media Streaming

```python
from twilio.twiml.voice_response import VoiceResponse

response = VoiceResponse()
connect = response.connect()
connect.stream(url="wss://your-domain.com/ws")  # Bidirectional
return str(response)

# Output:
# <Response>
#   <Connect>
#     <Stream url="wss://your-domain.com/ws"/>
#   </Connect>
# </Response>
```

---

## ✅ Production Checklist

- [ ] Use Deepgram Voice Agent API (not manual STT+TTS)
- [ ] Store streamSid in Redis if multi-server
- [ ] Implement timeout handling (Twilio hangs up after 30s silence)
- [ ] Use mark messages to sequence audio without overlaps
- [ ] Set interim_results=True for responsive feedback
- [ ] Implement VAD (voice activity detection)
- [ ] Cache LLM responses for common questions
- [ ] Monitor Deepgram API costs

---

## 🎯 Decision: BUILD CUSTOM with Deepgram Voice Agent

**Why NOT use Retell/Vapi:**
- Vapi blocks outbound on free tier
- Retell/Vapi cost more ($0.11-0.15/min vs $0.01/min)
- Less control over the conversation
- You already have Twilio + Deepgram accounts

**Why BUILD CUSTOM:**
- ✅ Full control over conversation logic
- ✅ Much cheaper (~$0.02/min total)
- ✅ Use your existing Twilio number
- ✅ Use your existing Deepgram credits
- ✅ Multi-tenant architecture built-in
- ✅ Own the IP, no vendor lock-in

---

## 📝 Files to Create/Modify

| File | Purpose | Status |
|------|---------|--------|
| `models.py` | Add Clinic, update Call model | ⏳ Pending |
| `prompt_builder.py` | Per-clinic prompt generation | ⏳ Pending |
| `websocket_bridge.py` | Twilio ↔ Deepgram audio bridge | ⏳ Pending |
| `routes_twilio.py` | /twilio/incoming webhook | ⏳ Pending |
| `routes_admin.py` | Clinic management APIs | ⏳ Pending |
| `intent_router.py` | Intent detection + function calling | ⏳ Pending |

---

## 📌 Action Items (UPDATED)

- [x] ~~Research Deepgram Voice Agent API~~ ✅ CONFIRMED EXISTS
- [x] ~~Research Twilio Media Streams~~ ✅ GOT SPECS
- [x] ~~Decide: Platform vs Custom~~ ✅ BUILD CUSTOM
- [ ] **NEXT: Implement Phase 1** - Update models.py with Clinic model
- [ ] **NEXT: Implement Phase 2** - Create prompt_builder.py
- [ ] **NEXT: Implement Phase 3** - Create websocket_bridge.py
- [ ] **NEXT: Implement Phase 4** - Update routes_twilio.py
- [ ] **NEXT: Set up ngrok** for testing
- [ ] **NEXT: Make first test call!**

---

## 🚀 To Test a Call (After Implementation)

1. Start FastAPI server:
   ```bash
   uvicorn api_main:app --host 0.0.0.0 --port 8000
   ```

2. Start ngrok tunnel:
   ```bash
   ngrok http 8000
   ```

3. Configure Twilio webhook:
   - Go to Twilio Console → Phone Numbers → +19048679643
   - Set Voice webhook to: `https://your-ngrok-url/twilio/incoming`

4. Call your Twilio number from any phone!

---

## 🔬 Still Need Research? (OPTIONAL)

### Research Prompt: Voice AI Platform Free Tier Comparison
If you want to compare platform options for future reference:
```
Compare free tier calling limits for:
1. Retell AI - can you make real outbound calls?
2. Vapi.ai - what's minimum payment to unlock calls?
3. Bland.ai - any developer trial?
4. Synthflow - 14-day trial includes real calls?
Which platform allows FREE test calls to my own phone?
```

---

*Last updated: December 6, 2025*
*Research Status: ✅ COMPLETED - Ready to implement!*
