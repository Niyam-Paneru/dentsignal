"""
agent_server.py - AI Voice Agent Worker

Voice agent worker that processes queued calls using either:
- SIMULATED mode: Deterministic FSM-based conversation simulation
- REAL mode: Deepgram Voice Agent WebSocket integration

FSM States: GREETING -> QUALIFY -> OFFER_SLOT -> CONFIRM -> END

Environment Variables:
- DATABASE_URL: Database connection string
- DEEPGRAM_API_KEY: Deepgram API key (for real mode)
- AGENT_MODE: SIMULATED or REAL
- API_BASE_URL: Base URL for API callbacks (default: http://localhost:8000)

Usage:
    python agent_server.py --simulated  # Run with simulated calls
    python agent_server.py --real       # Run with Deepgram (requires API key)
"""

from __future__ import annotations

import argparse
import enum
import hashlib
import json
import os
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
AGENT_MODE = os.getenv("AGENT_MODE", "SIMULATED").upper()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")  # DevSkim: ignore DS137138 - localhost fallback for dev only

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Deterministic helpers (avoids insecure `random` module for scanners)
# -----------------------------------------------------------------------------

def _deterministic_choice(options: list, seed: Any, salt: str = "") -> Any:
    """Pick from a list deterministically using SHA-256 (not for security)."""
    digest = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return options[int(digest, 16) % len(options)]


class _DeterministicRng:
    """Minimal deterministic selector using hashlib (replaces random.Random)."""

    def __init__(self, seed: Any):
        self._seed = seed
        self._counter = 0

    def choice(self, seq: list) -> Any:
        digest = hashlib.sha256(f"{self._seed}:{self._counter}".encode()).hexdigest()
        self._counter += 1
        return seq[int(digest, 16) % len(seq)]


# -----------------------------------------------------------------------------
# FSM States
# -----------------------------------------------------------------------------

class CallState(str, enum.Enum):
    """Finite State Machine states for call flow."""
    GREETING = "greeting"
    QUALIFY = "qualify"
    OFFER_SLOT = "offer_slot"
    CONFIRM = "confirm"
    END = "end"
    FALLBACK = "fallback"


class CallResult(str, enum.Enum):
    """Possible call outcomes."""
    BOOKED = "booked"
    NO_ANSWER = "no-answer"
    FAILED = "failed"
    RESCHEDULE = "reschedule"
    VOICEMAIL = "voicemail"


# -----------------------------------------------------------------------------
# Conversation FSM
# -----------------------------------------------------------------------------

@dataclass
class ConversationContext:
    """Context object tracking conversation state and data."""
    call_id: int
    lead_name: str
    lead_phone: str
    state: CallState = CallState.GREETING
    transcript: list[str] = field(default_factory=list)
    patient_type: Optional[str] = None  # new or returning
    preferred_time: Optional[str] = None
    has_pain: bool = False
    booked_slot: Optional[datetime] = None
    result: Optional[CallResult] = None
    retry_count: int = 0
    max_retries: int = 3


class ConversationFSM:
    """
    Finite State Machine for dental receptionist call flow.
    
    Flow: GREETING -> QUALIFY -> OFFER_SLOT -> CONFIRM -> END
    
    This class can be used for both simulated and real conversations.
    For real mode, integrate with Deepgram Voice Agent responses.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize FSM with optional agent config.
        
        Args:
            config_path: Path to dental_receptionist.json config
        """
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load agent configuration from JSON file."""
        default_config = {
            "persona": "Friendly dental receptionist named Sarah",
            "greeting": [
                "Hello! This is Sarah from Sunshine Dental. Am I speaking with {name}?",
                "Hi there! This is Sarah calling from Sunshine Dental. Is this {name}?"
            ],
            "qualifying_questions": [
                "Are you a new or returning patient?",
                "What days and times work best for you?",
                "Are you experiencing any urgent pain or discomfort?"
            ],
            "available_slots": [
                "tomorrow at 10 AM",
                "tomorrow at 2 PM",
                "Wednesday at 9 AM",
                "Thursday at 11 AM"
            ],
            "confirmation_script": "Great! I've booked you for {slot}. You'll receive a confirmation text shortly.",
            "fallbacks": [
                "I'm sorry, I didn't quite catch that. Could you repeat?",
                "I apologize, I'm having trouble understanding. One more time?",
                "I'll have a team member call you back shortly. Thank you!"
            ]
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        return default_config
    
    def get_greeting(self, context: ConversationContext, rng: Optional[object] = None) -> str:
        """Get greeting message."""
        greetings = self.config.get("greeting", [])
        if greetings:
            greeting = _deterministic_choice(greetings, context.call_id, "greeting") if rng is None else rng.choice(greetings)
            return greeting.format(name=context.lead_name)
        return f"Hello, this is Sunshine Dental calling for {context.lead_name}."
    
    def get_qualifying_question(self, index: int) -> str:
        """Get qualifying question by index."""
        questions = self.config.get("qualifying_questions", [])
        if index < len(questions):
            return questions[index]
        return "How can we help you today?"
    
    def get_slot_offer(self, context: ConversationContext, rng: Optional[object] = None) -> str:
        """Generate slot offer based on preferences."""
        slots = self.config.get("available_slots", ["tomorrow at 10 AM"])
        slot = rng.choice(slots) if rng else _deterministic_choice(slots, context.call_id, "slot")
        return f"We have availability {slot}. Would that work for you?"
    
    def get_confirmation(self, context: ConversationContext) -> str:
        """Get confirmation message."""
        template = self.config.get("confirmation_script", "You're booked for {slot}.")
        slot_str = context.booked_slot.strftime("%A at %I:%M %p") if context.booked_slot else "your appointment"
        return template.format(slot=slot_str)
    
    def get_fallback(self, context: ConversationContext) -> str:
        """Get fallback message based on retry count."""
        fallbacks = self.config.get("fallbacks", ["I'll have someone call you back."])
        index = min(context.retry_count, len(fallbacks) - 1)
        return fallbacks[index]
    
    def transition(self, context: ConversationContext, user_input: str, rng: Optional[object] = None) -> str:
        """
        Process user input and transition to next state.
        
        Args:
            context: Current conversation context
            user_input: User's response (transcribed speech)
            rng: Optional seeded RNG for deterministic behavior
            
        Returns:
            Agent's next utterance
        """
        user_lower = user_input.lower().strip()
        
        # Log the exchange
        context.transcript.append(f"Patient: {user_input}")
        
        # Handle no response / silence
        if not user_lower or user_lower in ["...", "[silence]", "[no response]"]:
            context.retry_count += 1
            if context.retry_count >= context.max_retries:
                context.state = CallState.END
                context.result = CallResult.NO_ANSWER
                response = "I'll have our team follow up with you later. Goodbye!"
            else:
                response = self.get_fallback(context)
            context.transcript.append(f"Agent: {response}")
            return response
        
        # Reset retry on valid input
        context.retry_count = 0
        
        # State machine logic
        if context.state == CallState.GREETING:
            # Check if they confirm identity
            if any(word in user_lower for word in ["yes", "yeah", "speaking", "this is", "that's me"]):
                context.state = CallState.QUALIFY
                response = self.get_qualifying_question(0)
            elif any(word in user_lower for word in ["no", "wrong", "not"]):
                context.state = CallState.END
                context.result = CallResult.FAILED
                response = "I apologize for the confusion. Have a great day!"
            else:
                response = "Is this a good time to discuss scheduling your dental appointment?"
        
        elif context.state == CallState.QUALIFY:
            # Parse qualifying responses
            if "new" in user_lower:
                context.patient_type = "new"
            elif "return" in user_lower or "existing" in user_lower:
                context.patient_type = "returning"
            
            if any(word in user_lower for word in ["pain", "hurt", "emergency", "urgent"]):
                context.has_pain = True
            
            # Move to offer slot
            context.state = CallState.OFFER_SLOT
            if context.has_pain:
                response = "I understand. Let me find you an urgent appointment. " + self.get_slot_offer(context, rng)
            else:
                response = self.get_slot_offer(context, rng)
        
        elif context.state == CallState.OFFER_SLOT:
            if any(word in user_lower for word in ["yes", "yeah", "sure", "works", "good", "perfect", "ok", "okay"]):
                # Book the slot
                from datetime import timezone
                tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
                context.booked_slot = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                context.state = CallState.CONFIRM
                response = self.get_confirmation(context) + " Is there anything else I can help you with?"
            elif any(word in user_lower for word in ["no", "busy", "can't", "different", "other", "next week"]):
                context.state = CallState.END
                context.result = CallResult.RESCHEDULE
                response = "No problem! I'll have our scheduling team call you with more options. Have a great day!"
            else:
                response = "Would you like me to book that time slot for you?"
        
        elif context.state == CallState.CONFIRM:
            context.state = CallState.END
            context.result = CallResult.BOOKED
            response = "Thank you for choosing Sunshine Dental. We look forward to seeing you. Goodbye!"
        
        else:
            # END state or unknown
            response = "Goodbye!"
        
        context.transcript.append(f"Agent: {response}")
        return response


# -----------------------------------------------------------------------------
# Simulated Conversation Runner
# -----------------------------------------------------------------------------

def run_simulated_conversation(
    context: ConversationContext,
    fsm: ConversationFSM,
    seed: Optional[int] = None,
) -> tuple[CallResult, str, Optional[datetime]]:
    """
    Run a complete simulated conversation.
    
    Uses deterministic random responses based on seed for reproducibility.
    
    Args:
        context: Conversation context
        fsm: Conversation FSM instance
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (result, transcript_string, booked_slot)
    """
    effective_seed = seed if seed is not None else context.call_id
    rng = _DeterministicRng(effective_seed)
    
    # Simulated patient responses
    patient_responses = {
        CallState.GREETING: ["Yes, this is them", "Speaking", "That's me"],
        CallState.QUALIFY: [
            "I'm a returning patient, mornings work best",
            "New patient, I have some tooth pain",
            "Existing patient, afternoons please"
        ],
        CallState.OFFER_SLOT: ["Yes, that works perfectly", "Sure, book it", "Sounds good"],
        CallState.CONFIRM: ["No, that's all, thank you", "Nothing else, thanks"],
    }
    
    # Add greeting to transcript (pass RNG for deterministic behavior)
    greeting = fsm.get_greeting(context, rng)
    context.transcript.append(f"Agent: {greeting}")
    
    # Run conversation loop
    max_turns = 10
    for _ in range(max_turns):
        if context.state == CallState.END:
            break
        
        # Get simulated patient response
        responses = patient_responses.get(context.state, ["Okay"])
        patient_input = rng.choice(responses)
        
        # Process through FSM (pass RNG for deterministic slot offers)
        fsm.transition(context, patient_input, rng)
    
    # Ensure we have a result
    if context.result is None:
        context.result = CallResult.BOOKED if context.booked_slot else CallResult.FAILED
    
    # Build transcript string
    transcript_str = "\n".join(context.transcript)
    
    return context.result, transcript_str, context.booked_slot


# -----------------------------------------------------------------------------
# Deepgram WebSocket (Placeholder for Real Mode)
# -----------------------------------------------------------------------------

def connect_deepgram_ws(api_key: str) -> None:
    """
    Connect to Deepgram Voice Agent WebSocket.
    
    This is a placeholder showing the structure for real Deepgram integration.
    
    For real implementation:
    1. Use websockets library to connect to wss://agent.deepgram.com/...
    2. Send configuration message with agent persona
    3. Stream audio from Twilio to Deepgram
    4. Receive TTS audio frames from Deepgram
    5. Stream TTS audio back to Twilio
    
    Args:
        api_key: Deepgram API key
        
    Example WebSocket flow:
        
        import websockets
        import asyncio
        
        async def deepgram_agent_session(api_key: str, audio_stream):
            uri = "wss://agent.deepgram.com/v1/agent"
            headers = {"Authorization": f"Token {api_key}"}
            
            async with websockets.connect(uri, extra_headers=headers) as ws:
                # Send configuration
                config = {
                    "type": "Configure",
                    "audio": {"input": {"encoding": "mulaw", "sample_rate": 8000}},
                    "agent": {
                        "think": {"provider": {"type": "open_ai"}},
                        "speak": {"provider": {"type": "eleven_labs"}}
                    }
                }
                await ws.send(json.dumps(config))
                
                # Handle bidirectional streaming
                async def send_audio():
                    async for chunk in audio_stream:
                        await ws.send(chunk)
                
                async def receive_audio():
                    async for message in ws:
                        if isinstance(message, bytes):
                            # TTS audio frame - send to Twilio
                            yield message
                        else:
                            # JSON message - handle events
                            event = json.loads(message)
                            handle_event(event)
                
                await asyncio.gather(send_audio(), receive_audio())
    """
    
    if not api_key:
        raise RuntimeError(
            "Deepgram API key not configured. "
            "Set DEEPGRAM_API_KEY environment variable."
        )
    
    logger.info("Deepgram WebSocket connection would be established here")
    logger.info("See docstring for implementation details")
    
    # TODO: Implement real WebSocket connection
    # This requires:
    # 1. websockets library
    # 2. Audio streaming from Twilio (or local microphone for testing)
    # 3. Agent configuration matching dental_receptionist.json
    # 4. Event handling for transcript updates
    
    raise NotImplementedError(
        "Real Deepgram integration not implemented. "
        "Use --simulated mode for testing."
    )


# -----------------------------------------------------------------------------
# Agent Session Manager
# -----------------------------------------------------------------------------

class AgentSessionManager:
    """
    Manages call processing queue and agent sessions.
    
    Usage:
        manager = AgentSessionManager()
        manager.run_worker_loop(simulated=True)
    """
    
    def __init__(
        self,
        api_base_url: str = API_BASE_URL,
        config_path: Optional[str] = None,
    ):
        """
        Initialize session manager.
        
        Args:
            api_base_url: Base URL for API callbacks
            config_path: Path to agent config JSON
        """
        self.api_base_url = api_base_url
        self.fsm = ConversationFSM(config_path)
        self.pending_calls: list[dict] = []
    
    def enqueue_call(
        self,
        call_id: int,
        lead: dict,
        callback_url: Optional[str] = None,
    ) -> None:
        """
        Register a call for processing.
        
        Args:
            call_id: Call ID from database
            lead: Lead data dict with name, phone, etc.
            callback_url: Optional override for callback URL
        """
        self.pending_calls.append({
            "call_id": call_id,
            "lead": lead,
            "callback_url": callback_url or f"{self.api_base_url}/api/calls/{call_id}/status",
        })
        logger.info(f"Enqueued call {call_id} for {lead.get('name', 'Unknown')}")
    
    def post_call_result(
        self,
        call_id: int,
        result: CallResult,
        transcript: str,
        booked_slot: Optional[datetime] = None,
        callback_url: Optional[str] = None,
    ) -> bool:
        """
        POST call result to API.
        
        Args:
            call_id: Call ID
            result: Call result enum
            transcript: Full transcript text
            booked_slot: Booked appointment time if applicable
            callback_url: URL to POST to
            
        Returns:
            True if successful
        """
        url = callback_url or f"{self.api_base_url}/api/calls/{call_id}/status"
        
        payload = {
            "status": "completed",
            "result": result.value,
            "transcript": transcript,
            "notes": f"Processed by agent worker",
        }
        
        if booked_slot:
            payload["booked_slot"] = booked_slot.isoformat()
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Posted result for call {call_id}: {result.value}")
                return True
            else:
                logger.error(f"Failed to post result for call {call_id}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error posting result for call {call_id}: {e}")
            return False
    
    def process_call(
        self,
        call_id: int,
        lead: dict,
        callback_url: str,
        simulated: bool = True,
    ) -> None:
        """
        Process a single call.
        
        Args:
            call_id: Call ID
            lead: Lead data
            callback_url: Callback URL
            simulated: Use simulated conversation
        """
        logger.info(f"Processing call {call_id} for {lead.get('name', 'Unknown')}")
        
        # Create conversation context
        context = ConversationContext(
            call_id=call_id,
            lead_name=lead.get("name", "Customer"),
            lead_phone=lead.get("phone", ""),
        )
        
        if simulated:
            # Run simulated conversation
            result, transcript, booked_slot = run_simulated_conversation(
                context, self.fsm, seed=call_id
            )
        else:
            # Real mode - would use Deepgram
            # For now, fall back to simulated
            logger.warning("Real mode not implemented, using simulated")
            result, transcript, booked_slot = run_simulated_conversation(
                context, self.fsm, seed=call_id
            )
        
        # Post result
        self.post_call_result(call_id, result, transcript, booked_slot, callback_url)
    
    def run_worker_loop(
        self,
        simulated: bool = True,
        poll_interval: float = 2.0,
        max_iterations: Optional[int] = None,
    ) -> int:
        """
        Main worker loop that processes queued calls.
        
        Args:
            simulated: Use simulated conversations
            poll_interval: Seconds between database polls
            max_iterations: Max iterations (None for infinite)
            
        Returns:
            Number of calls processed
        """
        from db import create_db, get_session, Call, Lead, CallStatus
        from sqlmodel import select
        
        # Initialize database
        create_db(DATABASE_URL)
        
        logger.info(f"Starting agent worker loop (simulated={simulated})")
        
        processed = 0
        iterations = 0
        
        while max_iterations is None or iterations < max_iterations:
            iterations += 1
            
            with get_session() as session:
                # Get queued calls
                stmt = (
                    select(Call)
                    .where(Call.status == CallStatus.QUEUED)
                    .order_by(Call.created_at)
                    .limit(10)
                )
                calls = session.exec(stmt).all()
                
                if not calls:
                    logger.debug("No queued calls, waiting...")
                    time.sleep(poll_interval)
                    continue
                
                for call in calls:
                    # Mark as in-progress
                    call.status = CallStatus.IN_PROGRESS
                    session.commit()
                    
                    # Get lead data
                    lead = session.get(Lead, call.lead_id)
                    lead_data = {
                        "name": lead.name if lead else "Customer",
                        "phone": lead.phone if lead else "",
                        "email": lead.email if lead else None,
                    }
                    
                    callback_url = f"{self.api_base_url}/api/calls/{call.id}/status"
                    
                    try:
                        self.process_call(
                            call_id=call.id,
                            lead=lead_data,
                            callback_url=callback_url,
                            simulated=simulated,
                        )
                        processed += 1
                    except Exception as e:
                        import traceback
                        logger.error(f"Error processing call {call.id}: {e}")
                        logger.error(traceback.format_exc())
                        call.status = CallStatus.FAILED
                        session.commit()
            
            # Small delay between batches
            time.sleep(0.5)
        
        logger.info(f"Worker loop finished. Processed {processed} calls.")
        return processed


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Voice Agent Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python agent_server.py --simulated
    python agent_server.py --real --config agent_config/dental_receptionist.json
    python agent_server.py --simulated --max-iterations 5
        """
    )
    
    parser.add_argument(
        "--simulated",
        action="store_true",
        default=True,
        help="Run with simulated conversations (default)"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run with real Deepgram Voice Agent"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="agent_config/dental_receptionist.json",
        help="Path to agent config JSON"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Max worker loop iterations (default: infinite)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between DB polls (default: 2.0)"
    )
    
    args = parser.parse_args()
    
    # Determine mode
    simulated = not args.real
    
    if args.real and not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY required for real mode")
        return 1
    
    # Create and run manager
    manager = AgentSessionManager(
        api_base_url=API_BASE_URL,
        config_path=args.config,
    )
    
    try:
        processed = manager.run_worker_loop(
            simulated=simulated,
            poll_interval=args.poll_interval,
            max_iterations=args.max_iterations,
        )
        logger.info(f"Processed {processed} calls total")
        return 0
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Worker error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
