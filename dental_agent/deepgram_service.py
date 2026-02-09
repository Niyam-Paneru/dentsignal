"""
deepgram_service.py - Deepgram Voice AI Integration

Handles:
- Speech-to-Text (STT) for understanding caller responses
- Text-to-Speech (TTS) for generating AI voice responses
- Intent detection from speech

Deepgram Pricing (as of 2024):
- $200 FREE credits on signup
- Pay-as-you-go after that
- STT: ~$0.0043/min
- TTS: ~$0.015/1000 chars
"""

import os
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Deepgram Configuration
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_STT_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

# Intent keywords for classification
POSITIVE_KEYWORDS = [
    "yes", "yeah", "yep", "sure", "okay", "ok", "correct", "right",
    "speaking", "this is", "that's me", "i am", "good", "fine",
    "perfect", "sounds good", "works for me", "absolutely"
]

NEGATIVE_KEYWORDS = [
    "no", "nope", "not", "wrong", "busy", "can't", "cannot",
    "don't", "later", "another time", "not interested", "stop"
]

NEW_PATIENT_KEYWORDS = [
    "new", "first time", "never been", "haven't visited"
]

RETURNING_PATIENT_KEYWORDS = [
    "returning", "been there", "visited before", "existing", "regular"
]


def transcribe_audio(
    audio_data: bytes,
    sample_rate: int = 8000,
    encoding: str = "mulaw",
    channels: int = 1,
) -> dict:
    """
    Transcribe audio using Deepgram Speech-to-Text.
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Audio sample rate (Twilio uses 8000Hz)
        encoding: Audio encoding (Twilio uses mulaw)
        channels: Number of audio channels
        
    Returns:
        dict with transcript and confidence
    """
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY not configured")
        return {"error": "Deepgram not configured", "transcript": ""}
    
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": f"audio/basic",
    }
    
    params = {
        "model": "nova-2",  # Latest model
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "false",
        "sample_rate": sample_rate,
        "encoding": encoding,
        "channels": channels,
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                DEEPGRAM_STT_URL,
                headers=headers,
                params=params,
                content=audio_data,
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract transcript from response
            alternatives = (
                result.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])
            )
            
            if alternatives:
                transcript = alternatives[0].get("transcript", "")
                confidence = alternatives[0].get("confidence", 0)
                
                logger.info(f"Transcribed: '{transcript}' (confidence: {confidence:.2f})")
                
                return {
                    "success": True,
                    "transcript": transcript,
                    "confidence": confidence,
                }
            
            return {
                "success": True,
                "transcript": "",
                "confidence": 0,
            }
            
    except Exception as e:
        logger.error(f"Deepgram STT error: {e}")
        return {
            "success": False,
            "error": "Speech-to-text processing failed",
            "transcript": "",
        }


def text_to_speech(
    text: str,
    voice: str = "aura-asteria-en",
    output_format: str = "mp3",
) -> Optional[bytes]:
    """
    Convert text to speech using Deepgram TTS.
    
    Args:
        text: Text to convert to speech
        voice: Deepgram voice model
        output_format: Output audio format (mp3, wav, etc.)
        
    Returns:
        Audio bytes or None on error
    """
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY not configured")
        return None
    
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    params = {
        "model": voice,
        "encoding": output_format,
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                DEEPGRAM_TTS_URL,
                headers=headers,
                params=params,
                json={"text": text},
            )
            response.raise_for_status()
            
            logger.info(f"Generated TTS for: '{text[:50]}...'")
            return response.content
            
    except Exception as e:
        logger.error(f"Deepgram TTS error: {e}")
        return None


def detect_intent(transcript: str) -> dict:
    """
    Detect intent from transcribed speech.
    
    Uses keyword matching for simplicity. Can be enhanced with
    LLM-based intent detection for more accuracy.
    
    Args:
        transcript: Transcribed speech text
        
    Returns:
        dict with intent, confidence, and entities
    """
    if not transcript:
        return {
            "intent": "no_input",
            "confidence": 0,
            "entities": {},
        }
    
    text = transcript.lower().strip()
    
    # Check for affirmative response
    if any(keyword in text for keyword in POSITIVE_KEYWORDS):
        return {
            "intent": "affirmative",
            "confidence": 0.9,
            "entities": {"response": "yes"},
        }
    
    # Check for negative response
    if any(keyword in text for keyword in NEGATIVE_KEYWORDS):
        return {
            "intent": "negative",
            "confidence": 0.9,
            "entities": {"response": "no"},
        }
    
    # Check for new patient
    if any(keyword in text for keyword in NEW_PATIENT_KEYWORDS):
        return {
            "intent": "patient_type",
            "confidence": 0.85,
            "entities": {"patient_type": "new"},
        }
    
    # Check for returning patient
    if any(keyword in text for keyword in RETURNING_PATIENT_KEYWORDS):
        return {
            "intent": "patient_type",
            "confidence": 0.85,
            "entities": {"patient_type": "returning"},
        }
    
    # Default: unclear
    return {
        "intent": "unclear",
        "confidence": 0.3,
        "entities": {},
        "raw_text": text,
    }


def process_caller_response(transcript: str, current_state: str) -> dict:
    """
    Process caller response based on current conversation state.
    
    Args:
        transcript: What the caller said
        current_state: Current FSM state (greeting, qualify, offer, etc.)
        
    Returns:
        dict with next_state, response_text, and metadata
    """
    intent = detect_intent(transcript)
    
    if current_state == "greeting":
        if intent["intent"] == "affirmative":
            return {
                "next_state": "qualify",
                "intent": intent,
                "continue_call": True,
            }
        elif intent["intent"] == "negative":
            return {
                "next_state": "end",
                "intent": intent,
                "end_reason": "wrong_person",
                "continue_call": False,
            }
        else:
            return {
                "next_state": "greeting",  # Retry
                "intent": intent,
                "continue_call": True,
            }
    
    elif current_state == "qualify":
        if intent["intent"] == "patient_type":
            return {
                "next_state": "offer_slot",
                "intent": intent,
                "patient_type": intent["entities"].get("patient_type", "unknown"),
                "continue_call": True,
            }
        else:
            return {
                "next_state": "offer_slot",  # Assume and continue
                "intent": intent,
                "patient_type": "unknown",
                "continue_call": True,
            }
    
    elif current_state == "offer_slot":
        if intent["intent"] == "affirmative":
            return {
                "next_state": "confirm",
                "intent": intent,
                "booked": True,
                "continue_call": True,
            }
        elif intent["intent"] == "negative":
            return {
                "next_state": "end",
                "intent": intent,
                "end_reason": "not_interested",
                "continue_call": False,
            }
        else:
            return {
                "next_state": "offer_slot",  # Retry with different slot
                "intent": intent,
                "continue_call": True,
            }
    
    elif current_state == "confirm":
        return {
            "next_state": "end",
            "intent": intent,
            "end_reason": "booked",
            "continue_call": False,
        }
    
    return {
        "next_state": "end",
        "intent": intent,
        "continue_call": False,
    }


def verify_deepgram_credentials() -> dict:
    """
    Verify Deepgram API key is working.
    
    Returns:
        dict with status
    """
    if not DEEPGRAM_API_KEY:
        return {
            "success": False,
            "error": "DEEPGRAM_API_KEY not configured",
        }
    
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Use the projects endpoint to verify key
            response = client.get(
                "https://api.deepgram.com/v1/projects",
                headers=headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                
                return {
                    "success": True,
                    "message": "Deepgram API key is valid",
                    "projects": len(projects),
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                }
                
    except Exception as e:
        logger.error(f"Deepgram API verification failed: {e}")
        return {
            "success": False,
            "error": "Deepgram API verification failed",
        }
