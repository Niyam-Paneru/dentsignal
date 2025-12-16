#I asked 2 Ai and below are the answers 

# 1st AI


Below is a Deepgram Voice Agent API × Twilio Media Streams guide tuned for production, with Python 3.13 + FastAPI + websockets in mind.

I’ll assume:

You’re using Deepgram Voice Agent API (single WS endpoint) as the core orchestrator.

Twilio Media Streams sends you mu-law 8kHz RTP audio over WebSocket.

You proxy audio between Twilio and Deepgram, and handle function-calling + business logic on your side.

1. BARGE-IN & INTERRUPTION HANDLING
Deepgram Voice Agent API has built-in barge-in & turn-taking. You still need to wire events into your control loop.​

1.1 Core Events to Watch
Typical event types (names may vary; adapt to actual docs):

UserStartedSpeaking – VAD detects start of user speech.

UtteranceEnd / UserStoppedSpeaking – end of segment; often comes with transcript + confidence.

ResponseStart / ResponseAudioStart – TTS starting/streaming.

ResponseEnd / ResponseAudioEnd – TTS finished.

FunctionCall / ToolCall – LLM decided to call a function.

FunctionResult – you sent result back; model continues.

1.2 When to Stop Speaking and Listen
Rule of thumb for full‑duplex:

If AI is speaking and you receive UserStartedSpeaking:

Immediately stop sending TTS audio to Twilio.

Optionally send a “stop/interrupt” control message to Deepgram if supported (e.g. {"type":"agent_interrupt"}).

Start buffering user audio again.

1.3 Example WS Handling Loop (Python, pseudo–event names)
python
import asyncio
import json
import websockets

class DGAgentSession:
    def __init__(self, dg_url, dg_token):
        self.dg_url = dg_url
        self.dg_token = dg_token
        self.ws = None
        self.agent_speaking = False
        self.user_speaking = False

    async def connect(self):
        self.ws = await websockets.connect(
            self.dg_url,
            extra_headers={"Authorization": f"Token {self.dg_token}"},
            ping_interval=20,
            ping_timeout=20,
        )

    async def send_audio(self, pcm_bytes: bytes):
        if self.ws:
            await self.ws.send(pcm_bytes)

    async def send_control(self, payload: dict):
        if self.ws:
            await self.ws.send(json.dumps(payload))

    async def run(self, on_tts_chunk, on_final_user_utterance):
        async for raw in self.ws:
            # distinguish binary (audio) vs text (events)
            if isinstance(raw, bytes):
                # TTS PCM from DG -> to Twilio
                if self.agent_speaking:
                    await on_tts_chunk(raw)
                continue

            evt = json.loads(raw)
            t = evt.get("type")

            if t == "agent_speech_start":
                self.agent_speaking = True

            elif t == "agent_speech_end":
                self.agent_speaking = False

            elif t == "user_started_speaking":
                self.user_speaking = True
                if self.agent_speaking:
                    # Hard barge-in: stop playback + tell DG to cut current response
                    self.agent_speaking = False
                    await on_tts_chunk(b"")  # stop Twilio stream if needed
                    await self.send_control({"type": "agent_interrupt"})

            elif t == "utterance_end":
                self.user_speaking = False
                transcript = evt["transcript"]["text"]
                await on_final_user_utterance(transcript, evt)
1.4 End-of-Turn Sensitivity
Deepgram handles EoU/EoT with model-driven VAD & turn-taking.​

Typical config JSON when you start the agent session (example):

json
{
  "agent": {
    "turn_detection": {
      "type": "server_vad",
      "params": {
        "silence_duration_ms": 500,
        "min_utterance_ms": 300,
        "max_utterance_ms": 8000,
        "energy_threshold": 0.3
      }
    },
    "barge_in": {
      "enabled": true,
      "mode": "hard",           // "soft" = let response finish phrase
      "min_user_speech_ms": 150
    }
  }
}
Tuning heuristics:

For telephone dental receptionist:

silence_duration_ms: 600–800 ms (patients pause a bit).

min_utterance_ms: 250–300 ms to ignore coughs.

max_utterance_ms: 8000–10000 ms to avoid insanely long single turns.

barge_in.enabled: true, mode: "hard" so callers can cut off long explanations.

2. LATENCY OPTIMIZATION
2.1 Latency Sources
End‑to‑end pipeline (PSTN → user hears AI):

PSTN → Twilio RTP → your backend (network & Twilio jitter buffer).

Your server → Deepgram STT (WebSocket).

LLM + function calls.

Deepgram TTS → your server.

Your server → Twilio Media Stream → PSTN.

2.2 Time-to-First-Byte (TTFB) for TTS
Aura‑2 is optimized for sub‑200 ms TTFB and ~0.11x Real-Time Factor.​

Your job is to avoid additional delays:

Use streaming playback: send chunks to Twilio as soon as you get TTS bytes, don’t buffer full sentences.

Use short LLM responses; long responses dominate perceived latency.

Use pre‑warm: keep a persistent Deepgram WS open per call; avoid creating a new session for each turn.

2.3 Optimal Audio Chunk Sizes
For Twilio Media Streams:

Twilio sends 20ms µ-law @ 8kHz frames (160 samples).

You can safely accumulate 40–60 ms before forwarding to Deepgram to reduce WS overhead.

Recommended:

python
CHUNK_MS = 40          # 2 Twilio frames
SAMPLES_PER_MS = 8     # 8000 Hz
BYTES_PER_SAMPLE = 1   # mu-law 8-bit
CHUNK_BYTES = CHUNK_MS * SAMPLES_PER_MS * BYTES_PER_SAMPLE  # 320 bytes
Forward ~every 40–60 ms; lower chunk = lower latency but more overhead.

2.4 WebSocket Keep-Alive & Connection Pooling
Twilio: one WS per call; you can't pool that.

Deepgram: keep one WS per call for the session; don’t re‑connect each utterance.

Python websockets.connect:

python
ws = await websockets.connect(
    dg_url,
    extra_headers={"Authorization": f"Token {DG_API_KEY}"},
    ping_interval=20,
    ping_timeout=20,
    max_queue=32,           # backpressure
    write_limit=2**16
)
Set read timeout (via outer task) to detect stuck connections.

Use backpressure: if Deepgram is slow, you may drop oldest audio frames (better than buffering unboundedly in real time).

2.5 Caching Common Responses
For fixed templates (“We’re closed”, “Let me check that”, disclaimers):

Maintain an in‑memory map text → pre‑encoded PCM (or at least TTS response chunks).

Or let Deepgram handle TTS each time but cache at your layer for phrases used in every call.

Pseudo:

python
from functools import lru_cache

@lru_cache(maxsize=64)
async def synthesize_static_phrase(text: str) -> bytes:
    # Call Deepgram TTS HTTP once; store full PCM in cache
    ...
    return pcm_bytes
Use this for:

Intro greeting

On-hold messages

“One moment while I check that…”

3. FUNCTION CALLING PATTERNS
Deepgram’s Voice Agent API supports function calling (aka tools) built-in.​

3.1 Function Schema Best Practices
Use JSON schema–like definitions:

Simple, strongly-typed args.

Clear descriptions.

Avoid huge nested objects; pass IDs and look up server-side.

Separate:

Function definition (sent to Deepgram).

Function handler (your Python mapping).

Business logic (actual DB/API work).​

Example tool schema JSON (appointment booking):

json
{
  "functions": [
    {
      "name": "book_appointment",
      "description": "Book a dental appointment for the caller",
      "parameters": {
        "type": "object",
        "properties": {
          "patient_name": {
            "type": "string",
            "description": "Full name of the patient"
          },
          "phone": {
            "type": "string",
            "description": "Contact phone number"
          },
          "reason": {
            "type": "string",
            "description": "Reason for visit or chief complaint"
          },
          "preferred_time_window": {
            "type": "string",
            "enum": ["morning", "afternoon", "evening"],
            "description": "Broad time window preference"
          }
        },
        "required": ["patient_name", "phone", "reason"]
      }
    },
    {
      "name": "lookup_appointment",
      "description": "Retrieve upcoming appointment for a given phone number",
      "parameters": {
        "type": "object",
        "properties": {
          "phone": { "type": "string" }
        },
        "required": ["phone"]
      }
    }
  ]
}
Send this once in your initial agent config.

3.2 Async Function Handling (Python)
Process FunctionCall events from Deepgram:

python
FUNCTION_MAP = {}

def register_function(name):
    def wrapper(fn):
        FUNCTION_MAP[name] = fn
        return fn
    return wrapper

@register_function("book_appointment")
async def book_appointment(args: dict) -> dict:
    # Async DB/API IO
    appt_id = await create_appointment_in_db(args)
    return {"status": "success", "appointment_id": appt_id}

@register_function("lookup_appointment")
async def lookup_appointment(args: dict) -> dict:
    appt = await get_next_appt_by_phone(args["phone"])
    if not appt:
        return {"status": "not_found"}
    return {"status": "found", "appointment": appt}


async def handle_function_call(evt, dg_session: DGAgentSession):
    fn_name = evt["function"]["name"]
    fn_args = evt["function"]["arguments"]  # already parsed dict
    call_id = evt["function"]["call_id"]

    handler = FUNCTION_MAP.get(fn_name)
    if not handler:
        result = {"error": f"Unknown function {fn_name}"}
    else:
        try:
            result = await asyncio.wait_for(handler(fn_args), timeout=2.5)
        except asyncio.TimeoutError:
            result = {"error": "timeout"}
        except Exception as e:
            result = {"error": "internal_error", "details": str(e)}

    # Send result back to DG
    await dg_session.send_control({
        "type": "function_result",
        "call_id": call_id,
        "name": fn_name,
        "result": result
    })
3.3 Chaining Multiple Calls
Pattern:

Let the LLM orchestrate multiple function calls within a turn.

Your side just:

Executes each call.

Sends function_result.

Deepgram continues the reasoning.

Don’t manually orchestrate multi‑call flows unless you have to. If business workflow is rigid (e.g., insurance → schedule), encode in function descriptions & system prompt.

3.4 Error & Timeout Handling
You must shield the user from raw errors:

If a function returns {"error": ...}, the LLM can be prompted to:

“If any tool result contains an error, apologize and ask for a different time/option instead of exposing internal details.”

Timeout strategy:

asyncio.wait_for(handler(...), timeout=2–3s).

If DB is slow, send filler speech via another function or by letting DG talk: “Let me just check that for you, this might take a moment…”

4. CONVERSATION STATE MANAGEMENT
4.1 Where to Store State
Per-call in-memory dict keyed by call_sid (Twilio) or DG session_id.

Includes:

patient_name

phone

last_intent

appointment_candidate

Flags: verified_insurance, is_new_patient etc.

python
class CallState:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.slots = {}
        self.history_tokens_estimate = 0
        self.summary = None
4.2 Token Limit Management
LLM context is finite. Strategy:

Maintain rolling window of recent utterances (e.g., last 10–15 turns).

Maintain compressed summary of earlier context.

Summarization trigger:

When history_tokens_estimate > 2_000 or turn_count > 15.

Your agent system prompt should say:

“You will receive a conversation summary plus the last few messages. Use both to continue the conversation naturally.”

Pseudo:

python
async def maybe_summarize(history: list[str], current_summary: str | None) -> str:
    if len(history) < 20:
        return current_summary or ""
    # Call a cheap LLM or DG tool to summarize
    text = "\n".join(history[-20:])
    summary = await summarize_with_llm(current_summary, text)
    history.clear()
    return summary
4.3 Handling Corrections
When user says “Actually, no, I meant…”:

Keep latest utterance authoritative.

State structure should store current values + previous values if needed.

Example:

python
if user says "Actually, make that Thursday instead of Tuesday":
    state.slots["appt_day"] = "Thursday"
LLM will handle narrative consistency; you only need the canonical slot values.

5. ERROR RECOVERY
5.1 Deepgram Connection Drops
You must tolerate DG WS close codes.

High-level:

python
async def run_agent_with_reconnect(dg_url, token, on_tts_chunk, on_user_utt):
    backoff = 1
    while True:
        session = DGAgentSession(dg_url, token)
        try:
            await session.connect()
            await session.run(on_tts_chunk, on_user_utt)
        except Exception:
            # log error
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 16)
            continue
        break
When DG is down mid-call:

Tell caller via TTS: “I’m having trouble accessing our system right now. Let me transfer you to a team member or please call back in a few minutes.”

Optionally bridge to human agent or voicemail.

5.2 Partial Audio
If Twilio WS drops:

Twilio fires call.status=completed webhook. Clean up state.

Don’t attempt to reconnect Twilio stream mid-call; PSTN call is gone.

If you miss some audio but call continues:

DG context might be partial, but conversation can recover.

You can prompt LLM: “If user response was unclear or missing, politely ask them to repeat.”

5.3 Graceful Degradation When LLM Slow
If LLM response > 1.5–2s, use filler speech:

“One moment while I check that for you…”

Implement as a tool play_filler_message or as a static cached TTS phrase triggered if no response after X ms.

Pseudo:

python
async def wait_for_llm_or_filler(task, timeout=2.0):
    try:
        return await asyncio.wait_for(task, timeout=timeout)
    except asyncio.TimeoutError:
        # play filler
        await play_filler_tts()
        # then wait longer
        return await task
6. AUDIO QUALITY
6.1 Encoding & Sample Rate
Twilio PSTN:

Media Streams: PCM µ-law, 8kHz, mono.

Deepgram Voice Agent:

Supports 8k/16k; use 8k to avoid resampling when using Twilio.

If DG expects linear16 16kHz, do:

µ-law → linear16 (ffmpeg or pure Python).

Upsample 8k→16k (e.g., soxr or simple linear interpolation).

But if Voice Agent accepts 8k µ-law, choose that to eliminate resampling.

6.2 Handling Noisy Phone Lines
Use DG’s telephony-optimized STT (Nova‑3 “phone call” / telephony domain).

Configure:

json
{
  "stt": {
    "model": "nova-3-phonecall",
    "language": "en",
    "disable_disfluencies": false,
    "punctuate": true
  }
}
Encourage user to move to quiet area if confidence low.

6.3 Echo & Double Audio
Avoid echo:

Ensure only one audio path from DG TTS → Twilio at any time.

Don’t simultaneously:

Play Twilio <Say> and

Send DG TTS into Media Stream.

Use pure Media Streams for audio once the call is connected.

6.4 Volume Normalization
If Deepgram’s TTS is already normalized (Aura‑2 has consistent loudness), you usually don’t need additional AGC.​

If you must adjust:

Apply simple gain on PCM (careful with clipping).

Better: configure TTS output level via DG parameter if available (e.g., loudness_dbfs).

7. VOICE SELECTION & TUNING (Aura‑2)
7.1 Aura‑2 Voice Catalog
See DG docs. Examples (names can change; check docs):​

json
{
  "tts": {
    "model": "aura-2-aurora-en",      // bright, energetic female[web:197]
    "voice": "aurora"
  }
}
Aurora (Aura‑2) characteristics:​

Young adult female, bright, clear.

~195 WPM, high pitch (~213 Hz), high energy.

Great for modern assistants and IVR, but may be fast for older callers. Slow via shorter outputs + potential rate control (see below).

For dental receptionist:

Prefer neutral, warm voices (slightly lower energy than Aurora) if available: e.g. aura-2-callcenter-en-female-1 (fictional example; check catalog).

7.2 SSML & Prosody Controls
Deepgram Aura‑2 is designed to not require SSML; it learns pauses and emphasis from data.​

If SSML is available (check tts-models docs):​

Example:

xml
<speak>
  <prosody rate="90%" pitch="-2st">
    Good morning, thank you for calling Bright Smiles Dental.
  </prosody>
  <break time="300ms"/>
  <prosody rate="95%">
    This is Emma. How can I help you today?
  </prosody>
</speak>
In JSON config:

json
{
  "tts": {
    "model": "aura-2-aurora-en",
    "format": "linear16",
    "ssml": true,
    "voice": "aurora"
  }
}
If no SSML:

Control perceived speed by:

Shorter sentences.

Injecting commas & periods where you want pauses.

Avoiding huge lists in one utterance.

8. PRODUCTION MONITORING
8.1 Core Metrics
Track at per-call and aggregate level:

STT latency:

user_audio_end_ts → final_transcript_ts.

LLM latency:

final_transcript_ts → response_text_ready_ts.

TTS latency:

response_text_ready_ts → first_tts_byte_ts.

End-to-end latency:

user_last_speech_ts → user_hears_first_ai_audio_ts.

Function call metrics:

Count, error rate, p95 latency per function.

Call outcome:

Appointment booked? (1/0)

Call duration, turns count.

Technical:

WS disconnects, reconnection attempts.

Audio buffer overflows/drops.

8.2 Logging Conversations for Debugging
At minimum:

json
{
  "call_id": "twilio_call_sid",
  "session_id": "dg_session_id",
  "events": [
    {
      "ts": "2025-12-08T16:30:00Z",
      "type": "user_utterance",
      "text": "I have a toothache"
    },
    {
      "ts": "2025-12-08T16:30:01Z",
      "type": "agent_response",
      "text": "I'm sorry to hear that, let's get you scheduled..."
    },
    {
      "ts": "...",
      "type": "function_call",
      "name": "book_appointment",
      "args": { "patient_name": "John Doe" }
    }
  ]
}
Store full transcripts and tool events.

For debugging audio:

Optionally store raw PCM or compressed Opus for a subset of calls (consider privacy/PHI).

8.3 A/B Testing Prompts & Voices
Implement config‑driven agent profiles:

python
AGENT_VARIANTS = {
    "A": {
        "system_prompt": "... shorter, transactional",
        "tts_model": "aura-2-aurora-en"
    },
    "B": {
        "system_prompt": "... more empathetic language + dental-anxiety focus",
        "tts_model": "aura-2-some-other-en"
    }
}
Randomly assign A or B per call (or segment by clinic).

Measure:

Appointment conversion rate.

Average call duration.

Hangup rate before booking.

8.4 Cost Tracking & Optimization
Deepgram Voice Agent pricing ~$4.50/hr of audio (check latest). Strategies:​

Keep calls focused (reduce rambling).

Use short system prompts (token cost).

Pre-calc cost per call:

python
cost_per_sec = 4.50 / 3600
estimated_cost = cost_per_sec * call_duration_seconds
Track cost per appointment booked vs. patient LTV.

9. END-TO-END ARCHITECTURE (TEXT DIAGRAM)
9.1 High-Level
text
Caller (PSTN)
   │
   ▼
Twilio Voice (SIP/PSTN)
   │
   ▼
Twilio Media Streams (WS, µ-law 8kHz)
   │
   │  (audio frames)
   ▼
Your FastAPI Backend (Python 3.13)
   ├─ WS Client → Deepgram Voice Agent API (full-duplex audio + JSON events)
   │     ├─ STT (Nova-3) + LLM + TTS (Aura-2) orchestrated by DG
   │     ├─ DG sends function_call events
   │     └─ Your app sends function_result events
   ├─ Business logic (DB, scheduling, CRM, etc.)
   ├─ Monitoring, logging, A/B routing
   └─ Streams TTS audio chunks back to Twilio WS
   │
   ▼
Twilio → PSTN
   │
   ▼
Caller hears AI receptionist
10. Minimal FastAPI Skeleton (Twilio + Deepgram)
python
from fastapi import FastAPI, WebSocket
import asyncio
import json

app = FastAPI()

DG_URL = "wss://api.deepgram.com/v1/agents/voice"
DG_TOKEN = "dg_your_api_key"

@app.websocket("/twilio-media-stream")
async def twilio_media_stream(ws: WebSocket):
    await ws.accept()
    call_sid = None
    dg_session = DGAgentSession(DG_URL, DG_TOKEN)
    await dg_session.connect()

    async def send_to_twilio(pcm: bytes):
        # Wrap in Twilio Media Stream JSON if needed
        await ws.send_text(json.dumps({
            "event": "media",
            "media": {
                "payload": pcm.hex()  # or base64, depending on your format
            }
        }))

    async def on_user_utt(transcript: str, evt: dict):
        # Optionally log or update state here
        pass

    # Run DG receive loop
    dg_task = asyncio.create_task(
        dg_session.run(send_to_twilio, on_user_utt)
    )

    # Receive Twilio media and send to DG
    try:
        async for msg in ws.iter_text():
            data = json.loads(msg)
            event = data.get("event")

            if event == "start":
                call_sid = data["start"]["callSid"]
                # Optionally send DG agent config here
                await dg_session.send_control({
                    "type": "agent_config",
                    "config": {
                        "agent": {
                            "turn_detection": {...},
                            "barge_in": {...}
                        },
                        "functions": [...],
                    }
                })

            elif event == "media":
                payload = data["media"]["payload"]  # base64 PCM µ-law
                pcm = base64.b64decode(payload)
                await dg_session.send_audio(pcm)

            elif event == "stop":
                break

    finally:
        dg_task.cancel()
        await dg_session.ws.close()
        await ws.close()
(You’ll adjust payload formats to match Twilio and DG exactly, but this is the high‑level wiring.)

If you tell me your exact Deepgram agent JSON and Twilio Media Stream payload format you’re using today, I can turn this into a drop‑in FastAPI service with tuned params for dental receptionist calls (including function schemas for booking, rescheduling, insurance checks).









# second Ai 


DEEPGRAM VOICE AGENT API: ADVANCED IMPLEMENTATION GUIDE (December 2025)
Executive Summary
Deepgram's Voice Agent API (Nova-3 STT + Aura-2 TTS + unified orchestration) is production-ready at $4.50/hour. It outperforms OpenAI Realtime (6.4% better VAQI) and ElevenLabs (29.3%) through native barge-in handling, sub-300ms latency, and integrated function calling. This guide covers actual production patterns, not theory.

1. BARGE-IN & INTERRUPTION HANDLING
How It Works
Deepgram's runtime detects speaker overlap during TTS synthesis

Transcription resumes immediately without restarting streams

No manual cancellation logic needed - system handles state

Key Events to Track
python
# Event types you'll receive over WebSocket
EVENT_HANDLERS = {
    "UserStartedSpeaking": "User began speaking (latency metric)",
    "TranscriptUpdate": "interim_results=true for real-time feedback",
    "speech_final": "User finished utterance (endpointing fired)",
    "UtteranceEnd": "Fallback end-of-speech (1000+ ms of silence)",
    "AgentStartedSpeaking": "AI began TTS response",
    "AgentFinishedSpeaking": "TTS synthesis complete",
}
Configuration for Barge-In
json
{
  "model": "nova-3-general",
  "encoding": "linear16",
  "sample_rate": 16000,
  "channels": 1,
  "interim_results": true,
  "vad_events": true,
  "endpointing": 800,
  "utterance_end_ms": 2000,
  "detect_language": false,
  "smart_format": true,
  "filler_words": false,
  "profanity_filter": false
}
Critical Parameters:

endpointing: 800 → Deepgram detects speech end at 800ms silence (speech_final event)

utterance_end_ms: 2000 → Fallback: if speech_final misses (noisy lines), UtteranceEnd fires at 2000ms

vad_events: true → Enable UserStartedSpeaking events for interruption detection

Production Implementation Pattern
python
import asyncio
import json
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
from twilio.rest import Client

class VoiceAgentOrchestrator:
    def __init__(self, deepgram_key: str):
        self.dg_client = DeepgramClient(api_key=deepgram_key)
        self.conversation_state = {
            "user_speaking": False,
            "agent_speaking": False,
            "current_transcript": "",
            "speech_final_received": False,
        }
    
    async def handle_voice_event(self, event_type: str, event_data: dict):
        """Handle Deepgram runtime events"""
        
        if event_type == "UserStartedSpeaking":
            # Interrupt agent if it's mid-response
            if self.conversation_state["agent_speaking"]:
                print("🔴 BARGE-IN DETECTED - User interrupted agent")
                await self.interrupt_agent_response()
            self.conversation_state["user_speaking"] = True
            
        elif event_type == "TranscriptUpdate":
            # Interim results - update UI/logging
            is_final = event_data.get("speech_final", False)
            transcript = event_data.get("transcript", "")
            self.conversation_state["current_transcript"] = transcript
            
            if is_final:
                self.conversation_state["speech_final_received"] = True
                print(f"✅ SPEECH FINAL: {transcript}")
                
        elif event_type == "UtteranceEnd":
            # Fallback end-of-speech (if speech_final missed)
            if not self.conversation_state["speech_final_received"]:
                print(f"⚠️ UTTERANCE END (no speech_final): {self.conversation_state['current_transcript']}")
            
            # Process the full utterance now
            await self.process_user_input(self.conversation_state["current_transcript"])
            self.conversation_state["user_speaking"] = False
            self.conversation_state["speech_final_received"] = False
            
        elif event_type == "AgentStartedSpeaking":
            self.conversation_state["agent_speaking"] = True
            print("🎙️ Agent speaking...")
            
        elif event_type == "AgentFinishedSpeaking":
            self.conversation_state["agent_speaking"] = False
            print("🎙️ Agent finished")
    
    async def interrupt_agent_response(self):
        """Stop current agent response and resume listening"""
        # Voice Agent API handles this natively - just send UserStartedSpeaking
        # No manual cancellation of TTS needed
        print("Resuming transcription...")
    
    async def process_user_input(self, user_text: str):
        """Send to LLM, get response, stream back"""
        if not user_text.strip():
            return
        
        # Your LLM call here (OpenAI, Claude, etc)
        response = await self.llm_query(user_text)
        
        # Stream response back - API handles interruption natively
        await self.stream_agent_response(response)
    
    async def stream_agent_response(self, text: str):
        """Send response to Aura-2 TTS"""
        # Voice Agent API streams this back over WebSocket
        # If user speaks during TTS, barge-in is handled automatically
        await self.send_to_agent({"type": "speak", "content": text})
Common Pitfalls
Pitfall	Why It Fails	Solution
Waiting for speech_final in noisy environments	Background noise breaks detection	Implement UtteranceEnd fallback with state tracking
Restarting transcription on barge-in	Creates gaps, loses context	Let Deepgram handle it - just listen for UserStartedSpeaking
Ignoring UtteranceEnd events	Misses user input on phone lines	Track: if speech_final, ignore next UtteranceEnd. If no speech_final, use UtteranceEnd
Not removing filler_words	"um," "uh" in transcript creates LLM confusion	Set filler_words: false for cleaner processing
2. LATENCY OPTIMIZATION
Latency Breakdown
text
Total E2E Latency = Audio Capture (20ms) 
                  + Network TX (10-30ms)
                  + STT Inference (50-150ms)
                  + LLM Processing (100-500ms)
                  + TTS Synthesis (200-500ms)
                  + Network RX (10-30ms)
TARGET: <1000ms for natural conversation
IDEAL: <500ms
Audio Chunk Sizing (Critical!)
python
# WebSocket connection configuration
AUDIO_CHUNK_SIZE_MS = 100  # Send 100ms chunks = 1600 bytes @ 16kHz linear16
SAMPLE_RATE = 16000
CHANNELS = 1
ENCODING = "linear16"  # 2 bytes per sample

bytes_per_chunk = (SAMPLE_RATE * CHANNELS * (ENCODING_BITS / 8)) * (AUDIO_CHUNK_SIZE_MS / 1000)
# = 16000 * 1 * 2 * 0.1 = 3200 bytes per chunk

# Twilio media stream default: 160 byte frames @ 8kHz (20ms each)
# Group into 100ms chunks:
TWILIO_FRAMES_PER_CHUNK = 5  # 5 * 20ms = 100ms chunks
Optimal Parameters by Use Case:

json
{
  "standard_phone_calls": {
    "audio_chunk_ms": 100,
    "sample_rate": 16000,
    "encoding": "linear16",
    "rationale": "Balanced latency + network efficiency"
  },
  "noisy_environments": {
    "audio_chunk_ms": 200,
    "sample_rate": 16000,
    "encoding": "linear16",
    "rationale": "Reduces retransmissions, less network overhead"
  },
  "ultra_low_latency": {
    "audio_chunk_ms": 50,
    "sample_rate": 16000,
    "encoding": "linear16",
    "rationale": "Faster feedback, higher network overhead - only if guaranteed bandwidth"
  }
}
WebSocket Keep-Alive Configuration
python
import websockets
import json
from typing import AsyncGenerator

class LatencyOptimizedVoiceAgent:
    def __init__(self, deepgram_key: str):
        self.ws = None
        self.keep_alive_interval = 5  # seconds
        self.latency_metrics = {
            "audio_sent_ts": {},
            "transcript_received_ts": {},
        }
    
    async def connect_optimized(self) -> None:
        """Connect with latency optimizations"""
        url = f"wss://agent.deepgram.com/agent?key={self.deepgram_key}"
        
        self.ws = await websockets.connect(
            url,
            # Connection pooling + keep-alive
            ping_interval=5,  # Send ping every 5s to keep socket warm
            ping_timeout=10,
            # Buffer settings for streaming
            read_limit=2**16,  # 64KB read buffer
            write_limit=2**16,  # 64KB write buffer
        )
        
        # Send configuration IMMEDIATELY (before audio)
        config = {
            "type": "Configure",
            "config": {
                "model": "nova-3-general",
                "encoding": "linear16",
                "sample_rate": 16000,
                "interim_results": True,
                "vad_events": True,
                "endpointing": 800,
                "utterance_end_ms": 2000,
            }
        }
        await self.ws.send(json.dumps(config))
        print(f"✅ Connected - latency should be <500ms from first audio chunk")
    
    async def send_audio_chunk(self, audio_bytes: bytes, chunk_id: int) -> None:
        """Send audio with latency tracking"""
        # Record when we send
        self.latency_metrics["audio_sent_ts"][chunk_id] = time.time_ns()
        
        message = {
            "type": "StreamAudio",
            "stream_audio": audio_bytes.hex(),  # Deepgram expects hex
            "chunk_id": chunk_id,  # For tracking
        }
        await self.ws.send(json.dumps(message))
    
    async def receive_with_latency_tracking(self) -> dict:
        """Receive transcript and calculate latency"""
        message = json.loads(await self.ws.recv())
        
        if message.get("type") == "TranscriptUpdate":
            chunk_id = message.get("chunk_id")
            if chunk_id in self.latency_metrics["audio_sent_ts"]:
                latency_ms = (time.time_ns() - self.latency_metrics["audio_sent_ts"][chunk_id]) / 1_000_000
                print(f"📊 Latency: {latency_ms:.1f}ms (chunk {chunk_id})")
        
        return message
    
    async def keep_alive(self) -> None:
        """Keep WebSocket alive during silences"""
        while True:
            await asyncio.sleep(self.keep_alive_interval)
            try:
                await self.ws.send(json.dumps({"type": "KeepAlive"}))
            except:
                break
TTS Pre-Buffering (Reduce TTFB)
python
async def stream_agent_response_optimized(self, text: str) -> None:
    """Stream TTS with pre-buffering for <200ms TTFB"""
    
    # Split long responses into chunks for progressive delivery
    sentences = text.split(". ")
    
    for i, sentence in enumerate(sentences):
        if not sentence.endswith((".", "!", "?")):
            sentence += "."
        
        # Start TTS synthesis immediately (don't wait for full response)
        tts_message = {
            "type": "Speak",
            "content": sentence,
            "flush": False if i < len(sentences) - 1 else True,  # Flush on last
            "buffer_ms": 0,  # No buffering - stream immediately
        }
        
        await self.ws.send(json.dumps(tts_message))
        print(f"📤 Queued TTS: {sentence[:50]}...")
        
        # Don't wait - next sentence can be prepared while this one plays
        await asyncio.sleep(0.1)  # Minimal delay between chunks
Caching Strategy for Common Responses
python
import hashlib
from typing import Dict, Optional

class ResponseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple] = {}  # {prompt_hash: (response, timestamp)}
        self.ttl = ttl_seconds
        self.hit_rate = {"hits": 0, "misses": 0}
    
    def get_cache_key(self, user_input: str, context: str = "") -> str:
        """Generate cache key from user input + context"""
        combined = f"{user_input}|{context}".lower().strip()
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, user_input: str, context: str = "") -> Optional[str]:
        """Retrieve cached response (if fresh)"""
        key = self.get_cache_key(user_input, context)
        
        if key in self.cache:
            response, timestamp = self.cache[key]
            age = time.time() - timestamp
            
            if age < self.ttl:
                self.hit_rate["hits"] += 1
                print(f"💾 CACHE HIT ({self.hit_rate['hits']} total)")
                return response
            else:
                del self.cache[key]
        
        self.hit_rate["misses"] += 1
        return None
    
    def set(self, user_input: str, response: str, context: str = "") -> None:
        """Cache response"""
        key = self.get_cache_key(user_input, context)
        self.cache[key] = (response, time.time())
        print(f"💾 Cached response (hit rate: {self.hit_rate['hits'] / (self.hit_rate['hits'] + self.hit_rate['misses']) * 100:.1f}%)")

# Usage in production
cache = ResponseCache(ttl_seconds=600)  # 10 minute TTL

async def get_agent_response(user_input: str, context: str) -> str:
    # Check cache first
    cached = cache.get(user_input, context)
    if cached:
        return cached
    
    # If miss, call LLM
    response = await llm_call(user_input, context)
    cache.set(user_input, response, context)
    return response
3. FUNCTION CALLING PATTERNS
Schema Definition
python
from typing import Any, Callable, Dict, List

FUNCTION_SCHEMA = {
    "name": "lookup_appointment",
    "description": "Look up patient appointment details and availability",
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "10-digit patient identifier"
            },
            "appointment_type": {
                "type": "string",
                "enum": ["cleaning", "checkup", "root_canal", "crown"],
                "description": "Type of appointment to search for"
            },
            "date_range_days": {
                "type": "integer",
                "description": "Search within N days from today (1-90)"
            }
        },
        "required": ["patient_id"]
    }
}

FUNCTION_REGISTRY: Dict[str, Callable] = {
    "lookup_appointment": lookup_appointment_handler,
    "schedule_appointment": schedule_appointment_handler,
    "update_notes": update_patient_notes_handler,
}
Async Function Execution (Non-Blocking)
python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

class AsyncFunctionExecutor:
    def __init__(self, timeout_seconds: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.timeout = timeout_seconds
        self.pending_calls = {}
    
    async def execute_function(
        self, 
        function_name: str, 
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function asynchronously without blocking agent"""
        
        if function_name not in FUNCTION_REGISTRY:
            return {
                "success": False,
                "error": f"Function '{function_name}' not found"
            }
        
        func = FUNCTION_REGISTRY[function_name]
        call_id = f"{function_name}_{int(time.time() * 1000)}"
        
        try:
            # Execute in thread pool (non-blocking to agent)
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    func,
                    function_args
                ),
                timeout=self.timeout
            )
            
            return {
                "success": True,
                "data": result,
                "call_id": call_id,
            }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Function call exceeded {self.timeout}s timeout",
                "call_id": call_id,
                "should_retry": True,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "call_id": call_id,
            }

# Actual database lookup functions
def lookup_appointment_handler(args: Dict) -> Dict:
    """Synchronous handler (runs in executor)"""
    patient_id = args.get("patient_id")
    appointment_type = args.get("appointment_type")
    date_range = args.get("date_range_days", 30)
    
    # Simulate DB query (replace with real DB)
    import random
    if random.random() > 0.1:  # 90% success rate
        return {
            "patient_id": patient_id,
            "appointments": [
                {
                    "date": (datetime.now() + timedelta(days=d)).isoformat(),
                    "time": f"{9 + d % 8}:00 AM",
                    "type": appointment_type,
                    "provider": f"Dr. Smith",
                }
                for d in range(1, 4)
            ]
        }
    else:
        raise Exception("Database connection timeout")

def schedule_appointment_handler(args: Dict) -> Dict:
    """Schedule new appointment"""
    return {
        "success": True,
        "appointment_id": "APT_" + str(int(time.time())),
        "confirmed_date": args.get("preferred_date"),
    }

def update_patient_notes_handler(args: Dict) -> Dict:
    """Update patient notes"""
    return {
        "success": True,
        "notes_updated": True,
        "timestamp": datetime.now().isoformat(),
    }
Function Chaining (Multi-Step Operations)
python
class FunctionCallChain:
    def __init__(self, executor: AsyncFunctionExecutor):
        self.executor = executor
        self.chain_history = []
    
    async def execute_chain(self, chain_def: List[Dict]) -> Dict:
        """
        Execute multiple function calls in sequence.
        chain_def: [
            {"function": "lookup_appointment", "args": {...}},
            {"function": "check_insurance", "args": {...}, "depends_on": 0},
            {"function": "schedule_appointment", "args": {...}, "depends_on": [0, 1]},
        ]
        """
        results = {}
        
        for i, step in enumerate(chain_def):
            func_name = step["function"]
            args = step["args"].copy()
            
            # Substitute previous results into args
            if "depends_on" in step:
                deps = step["depends_on"] if isinstance(step["depends_on"], list) else [step["depends_on"]]
                for dep_idx in deps:
                    dep_result = results[dep_idx]
                    if dep_result["success"]:
                        # Merge first result's data into args
                        args.update(dep_result.get("data", {}))
            
            # Execute function
            print(f"⚙️ Chain Step {i+1}: {func_name} with {args}")
            result = await self.executor.execute_function(func_name, args)
            results[i] = result
            
            # Fail fast if critical step fails
            if not result["success"] and step.get("critical", False):
                print(f"❌ Critical step {i} failed: {result['error']}")
                return {
                    "success": False,
                    "error": f"Chain failed at step {i}: {result['error']}",
                    "partial_results": results,
                }
            
            self.chain_history.append(result)
        
        return {
            "success": True,
            "results": results,
            "chain_length": len(results),
        }

# Usage
executor = AsyncFunctionExecutor(timeout_seconds=5)
chain = FunctionCallChain(executor)

chain_def = [
    {
        "function": "lookup_appointment",
        "args": {"patient_id": "1234567890", "appointment_type": "cleaning"},
        "critical": True,
    },
    {
        "function": "check_insurance",
        "args": {"patient_id": "1234567890"},
        "depends_on": 0,
    },
    {
        "function": "schedule_appointment",
        "args": {"appointment_type": "cleaning", "provider_id": "DR_001"},
        "depends_on": [0, 1],
        "critical": True,
    },
]

result = await chain.execute_chain(chain_def)
Error Handling & Timeouts
python
class RobustFunctionCaller:
    def __init__(self, max_retries: int = 2, timeout_seconds: int = 5):
        self.max_retries = max_retries
        self.timeout = timeout_seconds
        self.retry_delays = [0.5, 2.0]  # Exponential backoff
    
    async def call_with_retry(
        self,
        function_name: str,
        args: Dict,
        fallback_response: str = None,
    ) -> Dict:
        """Call function with retry logic and fallback"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute_function(function_name, args),
                    timeout=self.timeout,
                )
                
                if result["success"]:
                    return result
                
                # If function returned error but didn't timeout, don't retry
                if attempt == self.max_retries:
                    return result
                
            except asyncio.TimeoutError:
                print(f"⏱️ Attempt {attempt + 1}: Timeout after {self.timeout}s")
                
                if attempt < self.max_retries:
                    delay = self.retry_delays[attempt]
                    print(f"   Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    if fallback_response:
                        return {
                            "success": True,
                            "fallback": True,
                            "message": fallback_response,
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Function timeout after {self.max_retries + 1} attempts",
                        }
            
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                }
        
        return {
            "success": False,
            "error": "Unknown error in function execution",
        }
    
    async def _execute_function(self, function_name: str, args: Dict) -> Dict:
        """Actual execution (can be mocked)"""
        if function_name not in FUNCTION_REGISTRY:
            raise ValueError(f"Function {function_name} not found")
        
        func = FUNCTION_REGISTRY[function_name]
        result = await asyncio.get_event_loop().run_in_executor(
            None, func, args
        )
        return result

# Usage with fallback
caller = RobustFunctionCaller(max_retries=2, timeout_seconds=3)

result = await caller.call_with_retry(
    "lookup_appointment",
    {"patient_id": "1234567890"},
    fallback_response="I'm having trouble accessing the schedule. Would you like me to check again or take a message?"
)
4. CONVERSATION STATE MANAGEMENT
Context Window Management
python
from collections import deque
import tiktoken

class ConversationMemory:
    def __init__(
        self,
        max_tokens: int = 4000,
        max_turns: int = 50,
        model: str = "gpt-4o"
    ):
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)
        
        self.messages = deque(maxlen=max_turns)
        self.token_count = 0
        self.conversation_summary = None
    
    def add_message(self, role: str, content: str) -> bool:
        """Add message and handle token overflow"""
        tokens = len(self.encoding.encode(content))
        
        # Check if adding this message exceeds limit
        if self.token_count + tokens > self.max_tokens:
            # Strategy: Remove oldest message and try again
            if len(self.messages) > 2:  # Keep at least system + user
                old_msg = self.messages.popleft()
                old_tokens = len(self.encoding.encode(old_msg["content"]))
                self.token_count -= old_tokens
                print(f"⚠️ Removed oldest message (-{old_tokens} tokens)")
                return self.add_message(role, content)
            else:
                print(f"❌ Message too large even when alone: {tokens} tokens")
                return False
        
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        self.token_count += tokens
        
        return True
    
    def get_messages(self) -> List[Dict]:
        """Get conversation history for LLM"""
        return list(self.messages)
    
    def get_token_usage(self) -> Dict:
        """Get current token metrics"""
        return {
            "used": self.token_count,
            "max": self.max_tokens,
            "usage_percent": (self.token_count / self.max_tokens) * 100,
            "message_count": len(self.messages),
        }
    
    async def summarize_if_needed(self) -> None:
        """Summarize old messages when approaching limit"""
        usage = self.get_token_usage()
        
        if usage["usage_percent"] > 85:  # 85% full
            print(f"⚠️ Token usage at {usage['usage_percent']:.1f}% - summarizing...")
            
            # Keep last 5 messages, summarize the rest
            recent = list(self.messages)[-5:]
            old = list(self.messages)[:-5]
            
            if old:
                # Summarize old conversation
                summary_prompt = f"""Summarize this conversation excerpt in 2-3 sentences:
{json.dumps([m['content'] for m in old], indent=2)}"""
                
                summary = await self.llm_summarize(summary_prompt)
                self.conversation_summary = summary
                
                # Clear old messages
                self.messages.clear()
                for msg in recent:
                    self.messages.append(msg)
                
                # Recalculate tokens
                self.token_count = sum(
                    len(self.encoding.encode(m["content"])) 
                    for m in self.messages
                )
                print(f"✅ Summarized (new token count: {self.token_count})")

class SmartContextStrategy:
    """Choose between full history vs. summary based on conversation"""
    
    def __init__(self, memory: ConversationMemory):
        self.memory = memory
    
    def get_context(self) -> Dict:
        """Build context for LLM with summary if needed"""
        messages = self.memory.get_messages()
        summary = self.memory.conversation_summary
        
        context = {}
        
        # Include summary if available
        if summary:
            context["conversation_summary"] = summary
        
        # Include recent messages
        context["recent_messages"] = messages
        
        # Include metrics for logging
        context["metrics"] = self.memory.get_token_usage()
        
        return context
Conversation Branching (Corrections & Restarts)
python
class ConversationBranchManager:
    """Handle mid-conversation corrections and restarts"""
    
    def __init__(self):
        self.main_branch = []
        self.branches = {}  # {branch_id: conversation_history}
        self.current_branch = "main"
    
    def save_state(self, turn_number: int) -> str:
        """Save current state as a branch point"""
        branch_id = f"branch_{turn_number}_{int(time.time())}"
        self.branches[branch_id] = self.main_branch.copy()
        print(f"💾 Saved branch: {branch_id}")
        return branch_id
    
    def restore_branch(self, branch_id: str) -> bool:
        """Restore conversation to previous branch"""
        if branch_id in self.branches:
            self.main_branch = self.branches[branch_id].copy()
            print(f"↩️  Restored branch: {branch_id}")
            return True
        return False
    
    def handle_correction(self, original_turn: int, corrected_input: str) -> None:
        """User corrects themselves - handle gracefully"""
        # Keep everything up to the error
        if original_turn < len(self.main_branch):
            self.main_branch = self.main_branch[:original_turn]
            self.main_branch.append({
                "role": "user",
                "content": corrected_input,
                "correction": True,
            })
            print(f"✏️ Correction applied at turn {original_turn}")

# Usage
memory = ConversationMemory(max_tokens=4000)
branch_mgr = ConversationBranchManager()

# Normal conversation flow
memory.add_message("user", "I need an appointment")
memory.add_message("assistant", "What type of appointment?")

# User makes a correction
memory.add_message("user", "Actually, I meant a cleaning")

# If that's wrong, restore to save point
save_point = branch_mgr.save_state(turn_number=1)
# ... continue ...
# If needed: branch_mgr.restore_branch(save_point)
5. ERROR RECOVERY & CONNECTION MANAGEMENT
Reconnection Strategy
python
import asyncio
from typing import Optional

class ResilientVoiceAgent:
    def __init__(self, deepgram_key: str, max_reconnect_attempts: int = 5):
        self.deepgram_key = deepgram_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        
        self.audio_buffer = deque(maxlen=5)  # Buffer last 5 chunks
        self.connection_state = "disconnected"
    
    async def connect_with_recovery(self) -> bool:
        """Connect with automatic recovery"""
        for attempt in range(self.max_reconnect_attempts):
            try:
                self.connection_state = "connecting"
                await self._establish_connection()
                self.connection_state = "connected"
                print(f"✅ Connected (attempt {attempt + 1})")
                
                # Start keep-alive and receive loop
                await asyncio.gather(
                    self._keep_alive_loop(),
                    self._receive_loop(),
                )
                
            except asyncio.CancelledError:
                print("Connection cancelled")
                break
            
            except Exception as e:
                self.connection_state = "reconnecting"
                print(f"❌ Connection error (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_reconnect_attempts - 1:
                    delay = self.reconnect_delays[attempt]
                    print(f"⏳ Reconnecting in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    self.connection_state = "failed"
                    print(f"❌ Max reconnect attempts ({self.max_reconnect_attempts}) reached")
                    return False
        
        return False
    
    async def _establish_connection(self) -> None:
        """Establish WebSocket connection"""
        url = f"wss://agent.deepgram.com/agent?key={self.deepgram_key}"
        
        self.ws = await websockets.connect(
            url,
            ping_interval=5,
            ping_timeout=10,
            close_timeout=10,
        )
        
        # Send configuration
        config = {
            "type": "Configure",
            "config": {
                "model": "nova-3-general",
                "encoding": "linear16",
                "sample_rate": 16000,
                "interim_results": True,
                "vad_events": True,
            }
        }
        await self.ws.send(json.dumps(config))
    
    async def send_audio_with_recovery(self, audio_chunk: bytes, chunk_id: int) -> bool:
        """Send audio with fallback to buffer if disconnected"""
        
        # Buffer the chunk for potential retransmission
        self.audio_buffer.append((audio_chunk, chunk_id))
        
        try:
            if self.ws and self.connection_state == "connected":
                await self.ws.send(json.dumps({
                    "type": "StreamAudio",
                    "stream_audio": audio_chunk.hex(),
                    "chunk_id": chunk_id,
                }))
                return True
            else:
                print(f"⚠️ Not connected - buffering chunk {chunk_id}")
                return False
        
        except websockets.exceptions.ConnectionClosed:
            print(f"⚠️ Connection lost - buffering chunk {chunk_id}")
            self.connection_state = "disconnected"
            return False
    
    async def flush_buffered_audio(self) -> None:
        """Retransmit buffered audio after reconnect"""
        print(f"📤 Retransmitting {len(self.audio_buffer)} buffered chunks...")
        
        for audio_chunk, chunk_id in self.audio_buffer:
            try:
                await self.ws.send(json.dumps({
                    "type": "StreamAudio",
                    "stream_audio": audio_chunk.hex(),
                    "chunk_id": chunk_id,
                }))
                await asyncio.sleep(0.05)  # Prevent overwhelming
            except Exception as e:
                print(f"❌ Failed to retransmit chunk {chunk_id}: {e}")
    
    async def _keep_alive_loop(self) -> None:
        """Send keep-alive messages to prevent timeout"""
        while self.connection_state in ["connected", "connecting"]:
            try:
                await asyncio.sleep(5)
                if self.ws:
                    await self.ws.send(json.dumps({"type": "KeepAlive"}))
            except Exception as e:
                print(f"Keep-alive failed: {e}")
                break
    
    async def _receive_loop(self) -> None:
        """Receive messages from Deepgram"""
        try:
            async for message in self.ws:
                event = json.loads(message)
                await self._handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket closed - will attempt reconnect")
Graceful Degradation
python
class GracefulDegradation:
    """Fallback responses when systems fail"""
    
    FALLBACK_RESPONSES = {
        "database_timeout": "I'm having trouble accessing the information right now. Could you try again in a moment?",
        "llm_timeout": "Let me think about that... I'm processing a bit slowly. Could you repeat that?",
        "tts_timeout": "I'm having trouble speaking right now. Let me try again.",
        "general_error": "I apologize, but I'm experiencing technical difficulties. Please hold while I recover.",
    }
    
    def __init__(self):
        self.degradation_level = "full_service"  # full_service, limited, minimal
    
    async def handle_cascade_failure(self, error_type: str) -> str:
        """Get appropriate fallback response"""
        response = self.FALLBACK_RESPONSES.get(
            error_type,
            self.FALLBACK_RESPONSES["general_error"]
        )
        
        # Log for monitoring
        print(f"🚨 Degradation: {error_type} → {response[:50]}...")
        
        return response
    
    async def determine_degradation_level(self, failures: List[str]) -> None:
        """Adjust service level based on failures"""
        failed_systems = set(failures)
        
        if "database" in failed_systems and "llm" in failed_systems:
            self.degradation_level = "minimal"
            print("🔴 MINIMAL SERVICE: Only basic speech passthrough")
        elif len(failed_systems) > 1:
            self.degradation_level = "limited"
            print("🟡 LIMITED SERVICE: Some features unavailable")
        else:
            self.degradation_level = "full_service"
            print("🟢 FULL SERVICE: All systems operational")
6. AUDIO QUALITY OPTIMIZATION
Encoding Selection
json
{
  "linear16_vs_mulaw": {
    "linear16": {
      "bitrate": "256 kbps (16 bits * 16,000 samples/sec)",
      "best_for": "Clean phone lines, low noise environments",
      "latency_impact": "Minimal",
      "accuracy": "Highest (baseline)"
    },
    "mulaw": {
      "bitrate": "64 kbps (8 bits * 16,000 samples/sec)",
      "best_for": "Extremely bandwidth-limited networks",
      "latency_impact": "Slight compression delay (~10ms)",
      "accuracy": "-2-3% WER (word error rate)",
      "use_case": "Legacy PSTN where bandwidth < 100 kbps"
    }
  },
  "sample_rate_selection": {
    "8khz": {
      "bandwidth": "64 kbps (mulaw) / 128 kbps (linear16)",
      "accuracy": "Adequate for voice (misses >4kHz)",
      "best_for": "Phone calls via PSTN",
      "latency": "Lowest"
    },
    "16khz": {
      "bandwidth": "128 kbps (mulaw) / 256 kbps (linear16)",
      "accuracy": "Highest quality (industry standard)",
      "best_for": "Twilio Media Streams, modern VoIP",
      "latency": "Standard (~50ms buffering)"
    }
  }
}
Configuration by Channel
python
# Twilio Media Streams (RECOMMENDED)
TWILIO_CONFIG = {
    "encoding": "linear16",  # Twilio sends linear16
    "sample_rate": 8000,  # Twilio sends 8kHz (PSTN standard)
    "channels": 1,  # Mono
    "codec": "PCMU",  # Twilio's underlying codec, but it's already decoded
}

# WebRTC (Web/App)
WEBRTC_CONFIG = {
    "encoding": "linear16",
    "sample_rate": 48000,  # WebRTC uses 48kHz
    "channels": 2,  # Stereo common
    "downsample_to_16khz": True,  # Downsample for STT efficiency
}

# Direct SIP
SIP_CONFIG = {
    "encoding": "linear16",
    "sample_rate": 16000,
    "channels": 1,
    "vad_enabled": True,  # Reduce transmission during silence
}
Echo Cancellation & Noise Handling
python
import numpy as np
from scipy import signal

class AudioQualityFilter:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        # Noise gate threshold (-40 dB)
        self.noise_threshold = 10 ** (-40 / 20)
    
    def detect_echo(self, audio_chunk: np.ndarray) -> float:
        """Detect presence of echo (0.0-1.0)"""
        # Simple echo detection: compute autocorrelation
        autocorr = np.correlate(audio_chunk, audio_chunk, mode='full')
        
        # Peak at center (correlation with self) vs peaks at edges (echo)
        center_idx = len(autocorr) // 2
        center_energy = autocorr[center_idx]
        
        # Check for strong correlation at echo delays (200-500ms)
        echo_window = center_idx + np.arange(
            int(0.2 * self.sample_rate / len(audio_chunk)),
            int(0.5 * self.sample_rate / len(audio_chunk))
        )
        
        max_echo_energy = np.max(autocorr[echo_window]) if len(echo_window) > 0 else 0
        
        echo_ratio = max_echo_energy / center_energy if center_energy > 0 else 0
        
        return float(np.clip(echo_ratio, 0, 1))
    
    def apply_noise_gate(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Suppress audio below noise threshold"""
        # Compute RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        if rms < self.noise_threshold:
            # Below noise floor - silence it
            return np.zeros_like(audio_chunk)
        
        # Above threshold - pass through
        return audio_chunk
    
    def detect_clipping(self, audio_chunk: np.ndarray) -> float:
        """Detect clipping (0.0-1.0 where 1.0 = severe clipping)"""
        # Check for samples at or near ±1.0 (max amplitude)
        clipped = np.abs(audio_chunk) > 0.95
        clipping_ratio = np.sum(clipped) / len(audio_chunk)
        return float(clipping_ratio)

# Usage
audio_filter = AudioQualityFilter(sample_rate=16000)

def process_audio_chunk(chunk: np.ndarray) -> np.ndarray:
    """Process audio chunk before sending to Deepgram"""
    
    # Check quality
    echo_level = audio_filter.detect_echo(chunk)
    clipping_level = audio_filter.detect_clipping(chunk)
    
    if echo_level > 0.3:
        print(f"⚠️ Echo detected ({echo_level:.1%})")
    if clipping_level > 0.05:
        print(f"⚠️ Clipping detected ({clipping_level:.1%})")
    
    # Apply noise gate
    chunk = audio_filter.apply_noise_gate(chunk)
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(chunk))
    if max_val > 0:
        chunk = chunk / (max_val * 1.05)  # Leave 5% headroom
    
    return chunk
Volume Normalization
python
class VolumeNormalizer:
    def __init__(self, target_rms: float = 0.1):
        self.target_rms = target_rms
        self.smoothing_factor = 0.7
        self.current_gain = 1.0
    
    def normalize(self, audio_chunk: np.ndarray) -> np.ndarray:
        """Normalize volume with adaptive smoothing"""
        
        # Compute RMS of chunk
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        if rms < 1e-6:
            return audio_chunk  # Silent chunk
        
        # Calculate required gain
        required_gain = self.target_rms / rms
        
        # Smooth gain changes to avoid artifacts
        self.current_gain = (
            self.smoothing_factor * self.current_gain +
            (1 - self.smoothing_factor) * required_gain
        )
        
        # Limit gain to prevent clipping (0.5 to 2.0x)
        self.current_gain = np.clip(self.current_gain, 0.5, 2.0)
        
        # Apply gain
        normalized = audio_chunk * self.current_gain
        
        # Soft clip to prevent hard clipping
        normalized = np.tanh(normalized)  # Soft limiting
        
        return normalized
7. VOICE SELECTION & AURA-2 TUNING
Voice Characteristics
json
{
  "aura_2_voices": {
    "apollo": {
      "gender": "male",
      "pitch_hz": 135.59,
      "speaking_rate_wpm": 163,
      "energy": "medium",
      "use_case": "Professional, measured, reliable",
      "accent": "US English - neutral",
      "tone": "Authoritative but friendly"
    },
    "asteria": {
      "gender": "female",
      "pitch_hz": "~200-220",
      "speaking_rate_wpm": "~170",
      "energy": "medium-high",
      "use_case": "Customer service, engagement",
      "accent": "US English - neutral",
      "tone": "Warm, approachable"
    },
    "hades": {
      "gender": "male",
      "pitch_hz": "~120",
      "speaking_rate_wpm": "~155",
      "energy": "low",
      "use_case": "Serious, formal, executive",
      "accent": "US English - neutral",
      "tone": "Deep, authoritative"
    }
  }
}
Voice Selection Strategy
python
class VoiceSelector:
    VOICE_MAP = {
        "dental_clinic": {
            "greeting": "asteria",  # Warm, welcoming
            "information": "apollo",  # Clear, professional
            "appointment_confirmation": "asteria",  # Friendly confirmation
        },
        "it_support": {
            "default": "apollo",  # Professional, technical
            "error_messages": "hades",  # Serious issues
        },
        "sales": {
            "default": "asteria",  # Engaging, positive energy
            "price_discussion": "apollo",  # Serious, professional
        }
    }
    
    @staticmethod
    def select_voice(context: str, message_type: str = "default") -> str:
        """Select voice based on context and message type"""
        
        context_voices = VoiceSelector.VOICE_MAP.get(context, {})
        voice = context_voices.get(message_type, "apollo")
        
        return voice
    
    async def change_voice_mid_session(
        self,
        ws,
        new_voice: str,
        reason: str = ""
    ) -> None:
        """Dynamically change voice mid-conversation"""
        
        message = {
            "type": "UpdateSpeak",
            "speak_config": {
                "voice": new_voice,
            }
        }
        
        await ws.send(json.dumps(message))
        print(f"🎙️ Voice changed to {new_voice}" + (f" ({reason})" if reason else ""))
SSML & Advanced TTS Control
python
class AdvancedTTS:
    """Advanced text-to-speech control (Aura-2 supports via UpdateSpeak)"""
    
    @staticmethod
    def add_natural_pauses(text: str) -> str:
        """Add SSML pause directives for natural rhythm"""
        # Deepgram doesn't require SSML - it's built-in
        # But you can control pauses via text formatting
        
        replacements = {
            ". ": ".<break>  ",  # Slight pause after periods
            ", ": ",<break> ",   # Micro pause after commas
            " - ": " <break> -<break> ",  # Pause around dashes
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    @staticmethod
    def control_speech_rate(text: str, multiplier: float = 1.0) -> str:
        """
        Adjust apparent speech rate by:
        - Adding/removing pauses
        - Breaking into shorter phrases
        multiplier: 0.5 = half speed, 1.5 = 1.5x speed
        """
        if multiplier < 1.0:
            # Slower: add pauses and breaks
            text = text.replace(", ", ",<break> ")
            text = text.replace(". ", ".<break><break> ")
        elif multiplier > 1.0:
            # Faster: remove unnecessary pauses, join phrases
            text = text.replace("\n", " ")
            text = " ".join(text.split())  # Normalize whitespace
        
        return text
    
    @staticmethod
    def emphasize_important_terms(text: str, important_terms: List[str]) -> str:
        """Emphasize specific terms (implicit via Deepgram's training)"""
        # Deepgram learns emphasis from context
        # Approach: repeat important term, or structure sentence
        
        for term in important_terms:
            # Capitalize for emphasis (Aura-2 handles this)
            text = text.replace(term, term.upper())
        
        return text

# Usage
tts = AdvancedTTS()

# Natural pacing
text = "The appointment is scheduled for 3:00 PM. Please arrive early."
text = tts.add_natural_pauses(text)

# Emphasis on important terms
text = tts.emphasize_important_terms(
    text,
    important_terms=["3:00 PM", "arrive early"]
)
8. PRODUCTION MONITORING & METRICS
Latency & Performance Tracking
python
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class LatencyMetrics:
    audio_to_speech_final_ms: float  # User speaks → speech_final event
    speech_final_to_llm_response_ms: float  # speech_final → LLM response
    llm_response_to_tts_start_ms: float  # LLM response → Aura-2 starts
    tts_start_to_playback_ms: float  # Aura-2 starts → audio reaches client
    
    @property
    def total_latency_ms(self) -> float:
        return (
            self.audio_to_speech_final_ms +
            self.speech_final_to_llm_response_ms +
            self.llm_response_to_tts_start_ms +
            self.tts_start_to_playback_ms
        )

class LatencyTracker:
    def __init__(self, percentiles: List[int] = [50, 75, 95, 99]):
        self.percentiles = percentiles
        self.latencies = {
            "audio_to_speech_final": [],
            "speech_final_to_llm": [],
            "llm_to_tts": [],
            "tts_to_playback": [],
            "total": [],
        }
    
    def record_latency(self, metric_name: str, latency_ms: float) -> None:
        """Record a latency measurement"""
        if metric_name in self.latencies:
            self.latencies[metric_name].append(latency_ms)
    
    def get_stats(self, metric_name: str = "total") -> Dict:
        """Get latency statistics"""
        values = self.latencies.get(metric_name, [])
        
        if not values:
            return {"error": "No data"}
        
        values = sorted(values)
        
        stats = {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "median": values[len(values) // 2],
        }
        
        # Percentiles
        for p in self.percentiles:
            idx = int(len(values) * (p / 100))
            stats[f"p{p}"] = values[idx]
        
        return stats
    
    def print_report(self) -> None:
        """Print latency report"""
        print("\n" + "="*60)
        print("LATENCY REPORT")
        print("="*60)
        
        for metric in self.latencies:
            stats = self.get_stats(metric)
            if "error" not in stats:
                print(f"\n{metric}:")
                print(f"  Mean: {stats['mean']:.1f}ms")
                print(f"  Median (p50): {stats['median']:.1f}ms")
                print(f"  p95: {stats.get('p95', 'N/A')}")
                print(f"  p99: {stats.get('p99', 'N/A')}")
                print(f"  Max: {stats['max']:.1f}ms")

# Usage
tracker = LatencyTracker()

# During conversation
event_start = time.time()
# ... audio received ...
tracker.record_latency("audio_to_speech_final", (time.time() - event_start) * 1000)

# ... later ...
tracker.print_report()
Success Rate & Conversation Quality
python
@dataclass
class ConversationMetrics:
    call_id: str
    start_time: float
    duration_seconds: float
    
    # Quality metrics
    success: bool
    user_interruptions: int
    agent_interruptions: int  # Agent spoke over user
    speech_recognition_failures: int
    function_call_success_rate: float  # (successful calls / total calls)
    
    # Business metrics
    issue_resolved: bool
    escalation_needed: bool
    next_steps_provided: bool
    
    def get_quality_score(self) -> float:
        """Calculate conversation quality (0-100)"""
        score = 100.0
        
        # Deduct for issues
        score -= self.agent_interruptions * 5  # Heavy penalty
        score -= self.speech_recognition_failures * 3
        score -= (1 - self.function_call_success_rate) * 10
        
        # Bonus for resolution
        if self.issue_resolved:
            score += 20
        if not self.escalation_needed:
            score += 10
        
        return max(0, score)

class ConversationAnalyzer:
    def __init__(self):
        self.conversations = []
    
    def analyze_batch(self, metrics_list: List[ConversationMetrics]) -> Dict:
        """Analyze a batch of conversations"""
        
        quality_scores = [m.get_quality_score() for m in metrics_list]
        success_rate = sum(m.success for m in metrics_list) / len(metrics_list)
        resolution_rate = sum(m.issue_resolved for m in metrics_list) / len(metrics_list)
        
        return {
            "conversations_analyzed": len(metrics_list),
            "success_rate_percent": success_rate * 100,
            "resolution_rate_percent": resolution_rate * 100,
            "avg_quality_score": sum(quality_scores) / len(quality_scores),
            "total_duration_hours": sum(m.duration_seconds for m in metrics_list) / 3600,
            "avg_interruptions_per_call": sum(m.agent_interruptions for m in metrics_list) / len(metrics_list),
        }
Cost Tracking
python
class CostTracker:
    # Pricing (Dec 2025)
    PRICING = {
        "voice_agent_api": 4.50,  # per hour
        "nova_3_solo": 1.40,  # per hour STT only
        "aura_2_solo": 1.30,  # per hour TTS only
    }
    
    def __init__(self):
        self.sessions = {}  # {session_id: {start_time, duration_seconds, model_used}}
    
    def calculate_session_cost(self, session_id: str, model: str = "voice_agent_api") -> float:
        """Calculate cost for a session"""
        if session_id not in self.sessions:
            return 0
        
        duration_hours = self.sessions[session_id]["duration_seconds"] / 3600
        hourly_rate = self.PRICING.get(model, 4.50)
        
        return duration_hours * hourly_rate
    
    def calculate_batch_cost(self, sessions: List[str], model: str = "voice_agent_api") -> Dict:
        """Calculate cost for batch of sessions"""
        
        total_duration_seconds = sum(
            self.sessions[sid]["duration_seconds"]
            for sid in sessions
            if sid in self.sessions
        )
        
        hourly_rate = self.PRICING[model]
        total_cost = (total_duration_seconds / 3600) * hourly_rate
        cost_per_session = total_cost / len(sessions) if sessions else 0
        
        return {
            "model": model,
            "sessions": len(sessions),
            "total_duration_hours": total_duration_seconds / 3600,
            "hourly_rate": hourly_rate,
            "total_cost_usd": total_cost,
            "avg_cost_per_session": cost_per_session,
        }

# Usage
tracker = CostTracker()

# At session end
cost = tracker.calculate_session_cost("call_12345", model="voice_agent_api")
print(f"💰 Session cost: ${cost:.2f}")
Logging for Debugging
python
import logging
from datetime import datetime

class ProductionLogger:
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Conversation-specific logger
        self.conversation_log = logging.getLogger("conversations")
        handler = logging.FileHandler(
            f"{log_dir}/conversations_{datetime.now().strftime('%Y%m%d')}.log"
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.conversation_log.addHandler(handler)
    
    def log_transcript(
        self,
        call_id: str,
        speaker: str,
        text: str,
        confidence: float = 1.0,
    ) -> None:
        """Log transcript with confidence score"""
        self.conversation_log.info(
            f"{call_id} | {speaker}: {text} (confidence: {confidence:.2%})"
        )
    
    def log_function_call(
        self,
        call_id: str,
        function_name: str,
        args: Dict,
        result: Dict,
        latency_ms: float,
    ) -> None:
        """Log function calls for debugging"""
        status = "✅" if result.get("success") else "❌"
        self.conversation_log.info(
            f"{call_id} | {status} {function_name}({json.dumps(args)[:100]}) → {latency_ms:.1f}ms"
        )
    
    def log_error(
        self,
        call_id: str,
        error_type: str,
        error_message: str,
        stacktrace: Optional[str] = None,
    ) -> None:
        """Log errors for post-mortem analysis"""
        self.conversation_log.error(
            f"{call_id} | {error_type}: {error_message}\n{stacktrace or ''}"
        )
9. REFERENCE ARCHITECTURE DIAGRAM
text
┌─────────────────────────────────────────────────────────────────┐
│                      PHONE USER (PSTN/VoIP)                     │
└────────────────┬────────────────────────────────────────────────┘
                 │ Audio Stream (8-16kHz)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              TWILIO MEDIA STREAMS (FastAPI WebSocket)           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Audio Chunking (100ms), Buffering (5 chunks),            │   │
│  │ Volume Normalization, Echo Detection                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────────┘
                 │ 100ms chunks, linear16
                 ▼
         ┌───────────────────────────────────┐
         │   DEEPGRAM VOICE AGENT API         │
         │  ┌─────────────────────────────┐   │
         │  │ Nova-3 STT (Streaming)      │   │  UserStartedSpeaking
         │  │ • Endpointing: 800ms        │   │  TranscriptUpdate
         │  │ • UtteranceEnd: 2000ms      │   │  speech_final
         │  │ • VAD Events: Enabled       │   │  UtteranceEnd
         │  └─────────────────────────────┘   │
         │  ┌─────────────────────────────┐   │
         │  │ Runtime Orchestration       │   │
         │  │ • Turn-Taking Detection     │   │
         │  │ • Barge-In Handling         │   │
         │  │ • Function Call Routing     │   │
         │  │ • Context Management        │   │
         │  └─────────────────────────────┘   │
         │  ┌─────────────────────────────┐   │
         │  │ Aura-2 TTS (Streaming)      │   │
         │  │ • TTFB: <200ms              │   │
         │  │ • Voice Switching           │   │
         │  │ • Interruptible Output      │   │
         │  └─────────────────────────────┘   │
         └────┬──────────────────────────────┘
              │ UserStartedSpeaking,
              │ TranscriptUpdate, speech_final
              ▼
┌──────────────────────────────┐
│   YOUR APPLICATION LOGIC      │
│  ┌────────────────────────┐   │
│  │ Conversation State Mgr │◄──┼── Context Window (max 4000 tokens)
│  └────────────────────────┘   │
│  ┌────────────────────────┐   │
│  │ Function Call Executor │   │
│  │ • Async execution      │   │
│  │ • Timeout handling     │   │
│  │ • Retry logic          │   │
│  └────────────────────────┘   │
└──────────┬───────────────────┘
           │
       ┌───┴───┬──────────────┐
       ▼       ▼              ▼
    ┌─────┐ ┌────────┐   ┌────────┐
    │ LLM │ │Database│   │Analytics│
    └─────┘ └────────┘   └────────┘
10. COMMON PITFALLS & SOLUTIONS
Pitfall	Root Cause	Solution
High latency (>1 second)	Audio chunks too large (250ms+) or LLM processing slow	Use 100ms chunks; implement LLM response caching
Frequent barge-in failures	Ignoring UserStartedSpeaking events	Track state and interrupt TTS immediately on event
Conversation context grows unbounded	Not managing token count	Implement ConversationMemory with summarization at 85% cap
Function calls block TTS	Synchronous function execution	Use AsyncFunctionExecutor with thread pool
Connection drops lose audio	No buffering strategy	Implement circular audio buffer + flush on reconnect
Poor audio quality on PSTN	Not normalizing volume or detecting clipping	Add VolumeNormalizer + ClippingDetector in pipeline
Agent interrupts user mid-thought	Endpointing threshold too aggressive	Use endpointing:800ms + UtteranceEnd:2000ms fallback
Expensive token usage on long calls	Token-based LLM pricing	Use Deepgram's fixed $4.50/hr instead; cache responses
Transcription misses background noise	Using default VAD	Fine-tune endpointing for your environment; test locally
TTS sounds robotic	Using old voice models	Use Aura-2 (2025+) with natural pause/emphasis handling
11. PRODUCTION CHECKLIST
text
## Pre-Launch Checklist

- [ ] **Barge-in Testing**: Verify agent stops mid-sentence when user interrupts
- [ ] **Latency Testing**: P95 latency < 500ms in production network
- [ ] **Connection Resilience**: WebSocket drops/reconnects handled gracefully
- [ ] **Audio Quality**: Test on noisy phone lines (add noise in testing)
- [ ] **Function Timeouts**: All external calls have timeouts (3-5s max)
- [ ] **Token Limits**: Conversation memory has max_tokens cap with summarization
- [ ] **Error Messages**: All failures have graceful fallback responses
- [ ] **Cost Tracking**: Monitoring session costs; alerts if >$X/minute
- [ ] **Logging**: All transcripts, function calls, errors logged for debugging
- [ ] **A/B Testing**: Prompt variations compared; winning version tracked
- [ ] **Rate Limiting**: Respect Deepgram limits (15 concurrent Voice Agent connections)
- [ ] **Compliance**: HIPAA audit logging if handling health data

## Monitoring Setup

- [ ] **Latency Dashboard**: P50, P95, P99 latencies tracked real-time
- [ ] **Success Rate**: % calls where issue resolved tracked
- [ ] **Error Rates**: Function failures, timeouts, disconnects monitored
- [ ] **Cost Dashboard**: Real-time per-call cost visible
- [ ] **Audio Quality**: Echo, clipping, SNR metrics visible
- [ ] **Alerting**: Pagerduty/Slack alerts for latency >800ms or error rate >5%
CONCLUSION
Deepgram's Voice Agent API is production-ready for high-volume deployment. The key differentiators:

Unified stack = lower latency (sub-300ms achievable)

Native barge-in = no custom interruption logic needed

Fixed pricing = $4.50/hr vs token-based competitors (75% cheaper than OpenAI)

Built-in orchestration = streaming function calls without pausing speech

Your next move: Start with the latency optimization section (audio chunks, keep-alive, TTS buffering), then add robust function calling with timeout handling. Deploy with monitoring from day 1.
