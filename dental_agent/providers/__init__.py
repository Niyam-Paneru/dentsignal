"""
providers/__init__.py - Provider Package

Export provider interfaces and implementations.
"""

from providers.base import (
    # Data classes
    VoiceConfig,
    TranscriptionResult,
    AudioChunk,
    CallInfo,
    LLMMessage,
    LLMResponse,
    
    # Abstract interfaces
    SpeechProvider,
    TelephonyProvider,
    LLMProvider,
    
    # Registry
    ProviderRegistry,
    get_registry,
)

# Import implementations to register them
from providers.deepgram_provider import DeepgramProvider
from providers.twilio_provider import TwilioProvider
from providers.llm_providers import OpenAIProvider, ClaudeProvider


def register_all_providers():
    """Register all built-in providers with the global registry."""
    from providers.deepgram_provider import register as reg_deepgram
    from providers.twilio_provider import register as reg_twilio
    from providers.llm_providers import register as reg_llm
    
    reg_deepgram()
    reg_twilio()
    reg_llm()


__all__ = [
    # Data classes
    "VoiceConfig",
    "TranscriptionResult", 
    "AudioChunk",
    "CallInfo",
    "LLMMessage",
    "LLMResponse",
    
    # Interfaces
    "SpeechProvider",
    "TelephonyProvider",
    "LLMProvider",
    
    # Implementations
    "DeepgramProvider",
    "TwilioProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    
    # Registry
    "ProviderRegistry",
    "get_registry",
    "register_all_providers",
]
