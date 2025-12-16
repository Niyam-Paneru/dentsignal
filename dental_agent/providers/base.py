"""
providers/base.py - Abstract Provider Interfaces

Defines abstract base classes for:
- SpeechProvider (STT/TTS - Deepgram, Whisper, etc.)
- TelephonyProvider (Twilio, Vonage, etc.)
- LLMProvider (OpenAI, Claude, etc.)

This allows swapping providers without changing business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, AsyncIterator, Callable
from enum import Enum


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class VoiceConfig:
    """Configuration for text-to-speech voice."""
    voice_id: str
    name: str = ""
    language: str = "en-US"
    speed: float = 1.0
    pitch: float = 1.0


@dataclass
class TranscriptionResult:
    """Result from speech-to-text."""
    text: str
    confidence: float = 1.0
    is_final: bool = True
    language: str = "en"
    words: list = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class AudioChunk:
    """Audio data chunk for streaming."""
    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    format: str = "linear16"  # linear16, mulaw, alaw


@dataclass
class CallInfo:
    """Information about a phone call."""
    call_sid: str
    from_number: str
    to_number: str
    direction: str  # inbound, outbound
    status: str
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None


@dataclass
class LLMMessage:
    """A message in an LLM conversation."""
    role: str  # system, user, assistant
    content: str


@dataclass 
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"


# =============================================================================
# SPEECH PROVIDER (STT/TTS)
# =============================================================================

class SpeechProvider(ABC):
    """
    Abstract speech provider interface.
    
    Implementations: DeepgramProvider, WhisperProvider, GoogleSpeechProvider
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'deepgram', 'whisper')."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to provider."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        on_transcript: Callable[[TranscriptionResult], None],
    ) -> None:
        """
        Stream audio and receive transcriptions.
        
        Args:
            audio_stream: Async iterator of audio chunks
            on_transcript: Callback for each transcription result
        """
        pass
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: VoiceConfig,
    ) -> AsyncIterator[AudioChunk]:
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            voice: Voice configuration
            
        Yields:
            Audio chunks
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> list[VoiceConfig]:
        """List available voices."""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> dict:
        """Get usage statistics (minutes, characters, etc.)."""
        pass


# =============================================================================
# TELEPHONY PROVIDER
# =============================================================================

class TelephonyProvider(ABC):
    """
    Abstract telephony provider interface.
    
    Implementations: TwilioProvider, VonageProvider
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'twilio', 'vonage')."""
        pass
    
    @abstractmethod
    async def make_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs
    ) -> CallInfo:
        """
        Initiate an outbound call.
        
        Args:
            to_number: Number to call (E.164)
            from_number: Caller ID (E.164)
            webhook_url: URL for call events
            
        Returns:
            CallInfo with call SID and status
        """
        pass
    
    @abstractmethod
    async def end_call(self, call_sid: str) -> bool:
        """End an active call."""
        pass
    
    @abstractmethod
    async def get_call(self, call_sid: str) -> Optional[CallInfo]:
        """Get call details."""
        pass
    
    @abstractmethod
    async def send_sms(
        self,
        to_number: str,
        from_number: str,
        body: str,
    ) -> dict:
        """
        Send an SMS message.
        
        Returns:
            Message details including SID
        """
        pass
    
    @abstractmethod
    def generate_twiml(self, instructions: dict) -> str:
        """
        Generate TwiML/equivalent for call control.
        
        Args:
            instructions: Dict with keys like 'say', 'stream', 'record'
            
        Returns:
            TwiML/NCCO string
        """
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> dict:
        """Get usage statistics (calls, minutes, cost)."""
        pass


# =============================================================================
# LLM PROVIDER
# =============================================================================

class LLMProvider(ABC):
    """
    Abstract LLM provider interface.
    
    Implementations: OpenAIProvider, ClaudeProvider, GeminiProvider
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'anthropic')."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> LLMResponse:
        """
        Get a completion from the LLM.
        
        Args:
            messages: Conversation history
            model: Model to use (provider default if None)
            temperature: Creativity (0-1)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content and metadata
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens.
        
        Yields:
            Text chunks as they arrive
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> dict:
        """Get usage statistics (tokens, cost)."""
        pass


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

class ProviderRegistry:
    """
    Registry for provider implementations.
    
    Usage:
        registry = ProviderRegistry()
        registry.register_speech("deepgram", DeepgramProvider)
        provider = registry.get_speech("deepgram")
    """
    
    def __init__(self):
        self._speech_providers: Dict[str, type] = {}
        self._telephony_providers: Dict[str, type] = {}
        self._llm_providers: Dict[str, type] = {}
        
        # Active instances
        self._active_speech: Dict[str, SpeechProvider] = {}
        self._active_telephony: Dict[str, TelephonyProvider] = {}
        self._active_llm: Dict[str, LLMProvider] = {}
    
    # Registration methods
    def register_speech(self, name: str, provider_class: type):
        """Register a speech provider class."""
        self._speech_providers[name] = provider_class
    
    def register_telephony(self, name: str, provider_class: type):
        """Register a telephony provider class."""
        self._telephony_providers[name] = provider_class
    
    def register_llm(self, name: str, provider_class: type):
        """Register an LLM provider class."""
        self._llm_providers[name] = provider_class
    
    # Factory methods
    def get_speech(self, name: str, **config) -> SpeechProvider:
        """Get or create a speech provider instance."""
        if name not in self._active_speech:
            if name not in self._speech_providers:
                raise ValueError(f"Unknown speech provider: {name}")
            self._active_speech[name] = self._speech_providers[name](**config)
        return self._active_speech[name]
    
    def get_telephony(self, name: str, **config) -> TelephonyProvider:
        """Get or create a telephony provider instance."""
        if name not in self._active_telephony:
            if name not in self._telephony_providers:
                raise ValueError(f"Unknown telephony provider: {name}")
            self._active_telephony[name] = self._telephony_providers[name](**config)
        return self._active_telephony[name]
    
    def get_llm(self, name: str, **config) -> LLMProvider:
        """Get or create an LLM provider instance."""
        if name not in self._active_llm:
            if name not in self._llm_providers:
                raise ValueError(f"Unknown LLM provider: {name}")
            self._active_llm[name] = self._llm_providers[name](**config)
        return self._active_llm[name]
    
    def list_providers(self) -> dict:
        """List all registered providers."""
        return {
            "speech": list(self._speech_providers.keys()),
            "telephony": list(self._telephony_providers.keys()),
            "llm": list(self._llm_providers.keys()),
        }


# Global registry instance
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _registry
