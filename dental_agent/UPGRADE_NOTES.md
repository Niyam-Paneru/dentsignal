# Dental AI Voice Agent - Research-Based Upgrade Documentation

## Overview

This document summarizes the major upgrades made to the Dental AI Voice Agent based on comprehensive research into:
1. Real dental receptionist communication patterns
2. Deepgram Voice Agent advanced features
3. Twilio Media Streams optimization

**Date**: December 2025  
**Version**: 2.0 (Research-Based Upgrade)

---

## Key Changes

### 1. New File: `dental_scripts.py`

A comprehensive module containing research-based conversation patterns:

#### CARES Framework Implementation
Every interaction follows the CARES communication model:
- **C - Connect**: First 10 seconds are critical, warm greeting
- **A - Acknowledge**: Active listening, verbal acknowledgments
- **R - Respond**: Address needs directly with solutions
- **E - Empathize**: Genuine understanding, handle dental anxiety
- **S - Summarize**: Recap decisions, confirm twice

#### Time-Based Greetings
```python
"Good morning, thank you for calling {clinic}, this is {agent}, how may I help you?"
"Good afternoon, thank you for calling {clinic}, this is {agent}, how may I help you?"
"Good evening, thank you for calling {clinic}, this is {agent}, how may I help you?"
```

#### Scenario-Specific Scripts
- **Toothache/Pain**: Empathy-first approach, urgency assessment (1-10 scale)
- **Routine Cleaning**: Ask about last visit, appropriate time estimation
- **Emergency**: Express urgency, check emergency slots
- **Insurance**: Collect info professionally, handle in/out of network
- **Cost Questions**: Defer to in-office consultation, explain payment options

#### Objection Handling Scripts
- "Too expensive" → Payment plans, value explanation
- "Dental fear" → Gentle approach, sedation options, patient control
- "No time" → Early/evening/Saturday hours
- "Want to think" → Offer to hold spot tentatively

#### Key Phrases (Research-Based)
```
❌ "When would you like to come in?"
✅ "I have openings on Tuesday at 2:00 PM and Thursday at 10:00 AM. Which works better for you?"

❌ "I'll try to help"
✅ "I'd be happy to help"

❌ "Please hold"
✅ "Let me look that up for you..."
```

---

### 2. Updated `prompt_builder.py`

Completely rewritten to use research-based prompts:

#### Changes:
- **Imports** `dental_scripts.py` for comprehensive system prompts
- **Time-based greetings** via `get_time_of_day()` function
- **Enhanced voice info** with warmth ratings
- **10,697 character system prompt** (vs ~2,500 before)

#### Enhanced Function Schemas
```python
# NEW functions added:
- lookup_patient      # Access patient history
- cancel_appointment  # Handle cancellations/reschedules
- verify_insurance    # Insurance verification
```

---

### 3. Updated `websocket_bridge.py`

Research-based Deepgram and Twilio optimizations:

#### Deepgram Advanced Features

**Barge-in Handling**:
```python
elif event_type == "UserStartedSpeaking":
    self.user_is_speaking = True
    if self.tracker.agent_is_speaking:
        logger.info("Barge-in detected - clearing audio queue")
        self.should_clear_audio = True
        await self._clear_twilio_audio()  # Stop current speech
```

**Audio Buffering (200-400ms chunks)**:
```python
class AudioBuffer:
    """Buffer audio for optimal chunk sizes - research shows 200-400ms optimal."""
    AUDIO_BUFFER_SIZE = 3200  # 200ms at 8kHz 16-bit
    AUDIO_BUFFER_MAX_MS = 400  # Max delay before flush
```

**Turn-Endpointing**:
```python
elif event_type == "AgentAudioDone":
    if self.tracker:
        self.tracker.mark_agent_speaking(False)
    await self._send_mark_to_twilio("audio_done")
```

#### Twilio Optimizations

**Clear Audio on Barge-in**:
```python
async def _clear_twilio_audio(self) -> None:
    message = {"event": "clear", "streamSid": self.stream_sid}
    await self.twilio_ws.send_json(message)
```

**Audio Mark Tracking**:
```python
async def _send_mark_to_twilio(self, mark_name: str = None) -> None:
    # Track audio playback completion
```

#### Enhanced Analytics
```python
def get_analytics(self) -> dict:
    return {
        "total_turns": len(self.turns),
        "user_turns": len(user_turns),
        "agent_turns": len(agent_turns),
        "barge_in_count": self.barge_in_count,
        "duration_seconds": self.get_duration_seconds(),
        "appointment_booked": self.booked_appointment is not None,
    }
```

---

## Configuration

### Deepgram Settings
```python
DEEPGRAM_AGENT_URL = "wss://agent.deepgram.com/v1/agent/converse"
DEEPGRAM_SAMPLE_RATE = 8000  # Direct passthrough, no upsampling

# Agent settings
settings = {
    "type": "SettingsConfiguration",
    "audio": {"encoding": "linear16", "sample_rate": 8000},
    "agent": {
        "listen": {"model": "nova-3"},           # Best STT
        "think": {"provider": {"type": "openai", "model": "gpt-4o-mini"}},
        "speak": {"model": "aura-asteria-en"}    # Warm female voice
    },
    "context": {
        "messages": [{"role": "assistant", "content": greeting}],
        "replay": True  # Speak greeting immediately
    }
}
```

### Recommended Voices for Dental
| Voice | Gender | Accent | Warmth | Notes |
|-------|--------|--------|--------|-------|
| aura-asteria-en | Female | American | High | **Recommended** - warm, professional |
| aura-athena-en | Female | British | High | Sophisticated alternative |
| aura-luna-en | Female | American | Medium | More neutral |

---

## File Structure After Upgrade

```
dental_agent/
├── dental_scripts.py       # NEW - Research-based conversation scripts
├── prompt_builder.py       # UPDATED - Uses dental_scripts
├── websocket_bridge.py     # UPDATED - Deepgram/Twilio optimizations
├── prompt_builder_old.py   # BACKUP - Previous version
├── websocket_bridge_old.py # BACKUP - Previous version
├── routes_inbound.py       # Existing - Twilio webhooks
├── db.py                   # Existing - Database models
├── api_main.py             # Existing - FastAPI app
└── ...
```

---

## Testing the Upgrade

### 1. Verify Imports
```powershell
cd dental_agent
python -c "from prompt_builder import PromptBuilder; print('OK')"
python -c "from websocket_bridge import VoiceAgentBridge; print('OK')"
python -c "from dental_scripts import build_dental_system_prompt; print('OK')"
```

### 2. View Generated Prompt
```powershell
python prompt_builder.py
```

### 3. Start Server and Test Call
```powershell
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Start server
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload

# Update Twilio webhook to ngrok URL
# Make test call
```

---

## Research Sources Applied

### Dental Receptionist Patterns
- CARES Framework (Connect, Acknowledge, Respond, Empathize, Summarize)
- Time-based greetings
- Assumptive scheduling language
- Dental anxiety handling
- Objection handling scripts

### Deepgram Voice Agent
- UserStartedSpeaking for barge-in detection
- 8kHz direct audio (no upsampling)
- SettingsConfiguration message format
- FunctionCallResponse format
- AgentAudioDone for turn tracking

### Twilio Media Streams
- Clear event for barge-in handling
- Mark events for audio sync
- Efficient mulaw ↔ linear16 conversion
- Action URL for stream failure fallback

---

## Next Steps

1. **Add real scheduling integration** - Connect to clinic's appointment system
2. **Add patient database lookup** - Implement `lookup_patient` function
3. **Add call recording** - Store audio for quality review
4. **Add analytics dashboard** - Track barge-in rates, booking rates
5. **Production deployment** - Move from ngrok to permanent hosting

---

## Support

For issues or questions about this upgrade, refer to:
- `RESEARCH_NOTES.md` - Original research documentation
- `BUILD_PLAN.md` - Overall project plan
- Deepgram Voice Agent API docs
- Twilio Media Streams docs
