# Research Notes - Dental AI Voice Agent

> **Last Updated**: December 6, 2025
> **Status**: Research COMPLETE - Ready to implement!

---

## 📌 KEY DECISIONS MADE

| Decision | Answer |
|----------|--------|
| **Build custom or use platform?** | BUILD CUSTOM (Twilio + Deepgram) |
| **Deepgram has Voice Agent?** | ✅ YES - Full package (STT + LLM + TTS) |
| **Need Gemini/HF for calls?** | ❌ NO - Only for post-call analytics (later) |
| **One codebase or per-clinic?** | ONE codebase, multi-tenant |
| **Dashboard now or later?** | LATER - Get paying customers first |

---

## 🔬 DEEPGRAM VOICE AGENT (Confirmed June 2025)

### What It Includes
| Component | What It Does | Your Role |
|-----------|-------------|-----------|
| **STT** (Nova-3) | Transcribes caller speech | Automatic |
| **LLM Orchestration** | Decides responses | You provide system prompt |
| **TTS** (Aura-2) | Speaks naturally | Pick voice |
| **Turn-taking** | Knows when caller done | Automatic |
| **Barge-in** | Handles interruptions | Automatic |
| **Function Calling** | Triggers actions | You define functions |

**Key Insight**: One WebSocket connection handles EVERYTHING.

### How to "Train" Per Clinic
**NOT machine learning** - just prompt engineering!

Each clinic gets their own prompt stored in DB:
```python
class Clinic(SQLModel):
    agent_name: str        # "Sarah"
    agent_voice: str       # "aura-asteria-en"
    custom_instructions: str
    # ... clinic info fields
```

Dynamic prompt built from DB fields at call time.

---

## 🔧 TWILIO + DEEPGRAM ARCHITECTURE

```
Caller → Twilio → WebSocket (mulaw/8000) → FastAPI → Deepgram Voice Agent
                                              ↓
                                   (process + TTS back)
                                              ↓
                                          Twilio → Caller
```

### Audio Format Conversion Required
| From | To | Code |
|------|----|----- |
| Twilio (mulaw) | Deepgram (linear16) | `audioop.ulaw2lin(audio, 2)` |
| Deepgram (linear16) | Twilio (mulaw) | `audioop.lin2ulaw(audio, 2)` |

### Twilio Media Stream Specs
| Property | Value |
|----------|-------|
| Encoding | mulaw (µ-law, PCMU) |
| Sample Rate | 8000 Hz |
| Channels | 1 (mono) |
| Payload | Base64-encoded |

---

## 💰 COST BREAKDOWN

### Per Call (3 min average)
| Service | Cost/min | Per Call |
|---------|----------|----------|
| Deepgram STT | $0.0043 | $0.013 |
| Deepgram TTS | $0.0079 | $0.024 |
| Twilio PSTN | $0.025 | $0.075 |
| **Total** | | **~$0.11** |

### Per Clinic (100 calls/month × 3 min)
- Deepgram: ~$4/month
- Twilio: ~$7.50/month
- **Total: ~$12/month** per clinic

### Your Pricing
- Charge: $99-199/month
- Profit margin: **85-94%**

---

## ⏱️ LATENCY BREAKDOWN

| Step | Time |
|------|------|
| Twilio → WebSocket | ~50ms |
| Deepgram STT | ~100ms |
| LLM response | ~200-300ms |
| Deepgram TTS | ~50-100ms |
| Back to Twilio | ~50ms |
| **Total** | **300-600ms** |

---

## 🏢 MULTI-TENANT ARCHITECTURE

### ONE Codebase for ALL Clinics
```
/dental-agent/
├── app/
│   ├── main.py
│   ├── models.py          ← Clinic model with prompt fields
│   ├── prompt_builder.py  ← Builds prompt from clinic data
│   ├── websocket_bridge.py← Twilio ↔ Deepgram bridge
│   └── routes_twilio.py
├── .env                   ← API keys only (no clinic data)
└── database               ← All clinic data lives here
```

### Call Routing Flow
```
1. Call comes to +1-303-555-0123
2. Server queries: "Which clinic owns this number?"
3. Returns: Clinic ID 7 (Sunshine Dental)
4. Builds prompt with Sunshine's info
5. Deepgram answers: "Hi, thanks for calling Sunshine Dental!"
```

---

## 📊 PLATFORM COMPARISON (For Reference)

| Platform | Free Test Calls? | Cost/min | Verdict |
|----------|-----------------|----------|---------|
| **Deepgram** | $200 credits | $0.075 | ✅ USE THIS |
| Retell AI | $10 credits | $0.07 | Good backup |
| Vapi.ai | $10 credits | $0.05+ | Blocked outbound on free |
| Synthflow | 14-day trial | $0.08+ | $375/mo minimum |
| Bland.ai | Enterprise only | Custom | Not for startups |

**Decision**: Build custom with Deepgram (you already have account + credits)

---

## 🚀 7-DAY REVENUE ROADMAP

| Day | Action | Revenue | Cost |
|-----|--------|---------|------|
| 1-2 | Deploy Deepgram + test | $0 | $2 |
| 3 | Close Clinic #1 | $99 | $0 |
| 4-5 | Close Clinic #2-5 | $396 | $0 |
| 6-7 | Build basic dashboard | $0 | $0 |
| **WEEK 1** | **5 customers** | **$495/mo MRR** | **$2** |

---

## 📝 FUTURE FEATURES (After MVP)

### Post-Call Analysis Pipeline (Week 2+)
Only AFTER you have paying customers:

```
Call Ends → Transcript Saved → Async Analysis:
├── Gemini: Summarize (2-3 sentences)
├── HF: Sentiment (happy/neutral/frustrated)
├── HF: Intent (booked/reschedule/callback)
├── Gemini: Suggested action
└── Save to DB → Show in Dashboard
```

### Dashboard Features (Week 3+)
- Recent calls table
- Transcript viewer
- Sentiment badges
- Analytics (calls/day, booking rate)

---

## ✅ PRODUCTION CHECKLIST

- [ ] Use Deepgram Voice Agent API (not manual STT+TTS)
- [ ] Store streamSid in Redis if multi-server
- [ ] Implement timeout handling (30s silence = hangup)
- [ ] Use mark messages to sequence audio
- [ ] Set interim_results=True
- [ ] Implement VAD (voice activity detection)
- [ ] Cache LLM responses for common questions
- [ ] Monitor API costs

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Implement models.py** - Add Clinic model
2. **Create prompt_builder.py** - Dynamic prompt per clinic
3. **Create websocket_bridge.py** - Twilio ↔ Deepgram
4. **Update routes_twilio.py** - /twilio/incoming webhook
5. **Set up ngrok** - Expose localhost for testing
6. **Make first test call!**

---

*Research Status: ✅ COMPLETE*
*Ready to: START CODING*
