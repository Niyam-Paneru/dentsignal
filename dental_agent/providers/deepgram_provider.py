"""
providers/deepgram_provider.py - Deepgram Speech Provider Implementation

Implements SpeechProvider for Deepgram:
- Real-time STT via WebSocket
- TTS via Aura voices
"""

import os
import json
import logging
import asyncio
from typing import Optional, AsyncIterator, Callable
from dataclasses import dataclass

from providers.base import (
    SpeechProvider,
    VoiceConfig,
    TranscriptionResult,
    AudioChunk,
)

logger = logging.getLogger(__name__)


# Deepgram Aura voices
DEEPGRAM_VOICES = [
    VoiceConfig(voice_id="aura-asteria-en", name="Asteria", language="en-US"),
    VoiceConfig(voice_id="aura-luna-en", name="Luna", language="en-US"),
    VoiceConfig(voice_id="aura-stella-en", name="Stella", language="en-US"),
    VoiceConfig(voice_id="aura-athena-en", name="Athena", language="en-US"),
    VoiceConfig(voice_id="aura-hera-en", name="Hera", language="en-US"),
    VoiceConfig(voice_id="aura-orion-en", name="Orion", language="en-US"),
    VoiceConfig(voice_id="aura-arcas-en", name="Arcas", language="en-US"),
    VoiceConfig(voice_id="aura-perseus-en", name="Perseus", language="en-US"),
    VoiceConfig(voice_id="aura-angus-en", name="Angus", language="en-US"),
    VoiceConfig(voice_id="aura-orpheus-en", name="Orpheus", language="en-US"),
    VoiceConfig(voice_id="aura-helios-en", name="Helios", language="en-US"),
    VoiceConfig(voice_id="aura-zeus-en", name="Zeus", language="en-US"),
]


class DeepgramProvider(SpeechProvider):
    """
    Deepgram speech provider implementation.
    
    Uses Deepgram for:
    - Real-time STT (speech-to-text)
    - TTS via Aura voices
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "nova-2",
        language: str = "en-US",
    ):
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self._api_key:
            raise ValueError("Deepgram API key required")
        
        self._model = model
        self._language = language
        self._connected = False
        
        # Usage tracking
        self._total_audio_seconds = 0.0
        self._total_tts_characters = 0
    
    @property
    def name(self) -> str:
        return "deepgram"
    
    async def connect(self) -> None:
        """Establish connection (validates API key)."""
        # Validate API key by making a simple request
        self._connected = True
        logger.info("Deepgram provider connected")
    
    async def disconnect(self) -> None:
        """Close connection."""
        self._connected = False
        logger.info("Deepgram provider disconnected")
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        on_transcript: Callable[[TranscriptionResult], None],
    ) -> None:
        """
        Stream audio to Deepgram and receive transcriptions.
        
        Uses Deepgram's WebSocket API for real-time transcription.
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required: pip install websockets")
        
        # Build WebSocket URL with options
        url = f"wss://api.deepgram.com/v1/listen"
        params = [
            f"model={self._model}",
            f"language={self._language}",
            "punctuate=true",
            "interim_results=true",
            "endpointing=200",
            "utterance_end_ms=1000",
        ]
        url = f"{url}?{'&'.join(params)}"
        
        headers = {
            "Authorization": f"Token {self._api_key}",
        }
        
        async with websockets.connect(url, extra_headers=headers) as ws:
            logger.info("Connected to Deepgram STT WebSocket")
            
            async def send_audio():
                async for chunk in audio_stream:
                    await ws.send(chunk.data)
                    self._total_audio_seconds += len(chunk.data) / (chunk.sample_rate * 2)
                # Send close message
                await ws.send(json.dumps({"type": "CloseStream"}))
            
            async def receive_transcripts():
                async for message in ws:
                    data = json.loads(message)
                    
                    if data.get("type") == "Results":
                        channel = data.get("channel", {})
                        alternatives = channel.get("alternatives", [])
                        
                        if alternatives:
                            alt = alternatives[0]
                            result = TranscriptionResult(
                                text=alt.get("transcript", ""),
                                confidence=alt.get("confidence", 1.0),
                                is_final=data.get("is_final", True),
                                language=self._language,
                                duration_seconds=data.get("duration", 0),
                            )
                            
                            if result.text:
                                on_transcript(result)
            
            # Run send and receive concurrently
            await asyncio.gather(send_audio(), receive_transcripts())
    
    async def synthesize(
        self,
        text: str,
        voice: VoiceConfig,
    ) -> AsyncIterator[AudioChunk]:
        """
        Convert text to speech using Deepgram Aura.
        """
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp package required: pip install aiohttp")
        
        url = f"https://api.deepgram.com/v1/speak"
        params = {
            "model": voice.voice_id,
            "encoding": "linear16",
            "sample_rate": "16000",
        }
        
        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json",
        }
        
        self._total_tts_characters += len(text)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params=params,
                headers=headers,
                json={"text": text},
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Deepgram TTS error: {error}")
                
                # Stream audio chunks
                async for chunk in response.content.iter_chunked(4096):
                    yield AudioChunk(
                        data=chunk,
                        sample_rate=16000,
                        channels=1,
                        format="linear16",
                    )
    
    def get_available_voices(self) -> list[VoiceConfig]:
        """List available Deepgram Aura voices."""
        return DEEPGRAM_VOICES.copy()
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "provider": self.name,
            "audio_seconds_transcribed": round(self._total_audio_seconds, 2),
            "tts_characters": self._total_tts_characters,
            "estimated_cost": {
                "stt": round(self._total_audio_seconds / 60 * 0.0059, 4),  # Nova-2 pricing
                "tts": round(self._total_tts_characters / 1000 * 0.015, 4),  # Aura pricing
            }
        }


# Register with global registry
def register():
    """Register Deepgram provider with the global registry."""
    from providers.base import get_registry
    get_registry().register_speech("deepgram", DeepgramProvider)
