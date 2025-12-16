"""
providers/openai_provider.py - OpenAI LLM Provider Implementation

Implements LLMProvider for OpenAI:
- Chat completions (GPT-4, GPT-3.5-turbo)
- Streaming responses
- Token counting
"""

import os
import logging
from typing import Optional, AsyncIterator

from providers.base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider implementation.
    
    Uses OpenAI for:
    - Chat completions
    - Streaming responses
    """
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OpenAI API key required")
        
        self._default_model = default_model or self.DEFAULT_MODEL
        self._organization = organization
        
        # Lazy-load client
        self._client = None
        self._async_client = None
        
        # Usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_requests = 0
    
    @property
    def name(self) -> str:
        return "openai"
    
    def _get_client(self):
        """Get or create sync OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    organization=self._organization,
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._client
    
    def _get_async_client(self):
        """Get or create async OpenAI client."""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
                self._async_client = AsyncOpenAI(
                    api_key=self._api_key,
                    organization=self._organization,
                )
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._async_client
    
    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> LLMResponse:
        """
        Get a completion from OpenAI.
        """
        client = self._get_async_client()
        
        model_to_use = model or self._default_model
        
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = await client.chat.completions.create(
                model=model_to_use,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Track usage
            self._total_requests += 1
            if response.usage:
                self._total_prompt_tokens += response.usage.prompt_tokens
                self._total_completion_tokens += response.usage.completion_tokens
            
            choice = response.choices[0]
            
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                tokens_used=(response.usage.total_tokens if response.usage else 0),
                finish_reason=choice.finish_reason or "stop",
            )
            
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    async def stream_complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from OpenAI.
        """
        client = self._get_async_client()
        
        model_to_use = model or self._default_model
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            stream = await client.chat.completions.create(
                model=model_to_use,
                messages=openai_messages,
                stream=True,
                **kwargs
            )
            
            self._total_requests += 1
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI stream failed: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self._default_model)
            return len(encoding.encode(text))
        except ImportError:
            # Rough estimate: ~4 chars per token
            return len(text) // 4
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        # Approximate cost calculation (varies by model)
        prompt_cost = self._total_prompt_tokens * 0.00015 / 1000  # GPT-4o-mini input
        completion_cost = self._total_completion_tokens * 0.0006 / 1000  # GPT-4o-mini output
        
        return {
            "provider": self.name,
            "model": self._default_model,
            "total_requests": self._total_requests,
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "estimated_cost_usd": round(prompt_cost + completion_cost, 4),
        }


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude LLM provider implementation.
    """
    
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError("Anthropic API key required")
        
        self._default_model = default_model or self.DEFAULT_MODEL
        self._client = None
        
        # Usage tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError("anthropic package required: pip install anthropic")
        return self._client
    
    async def complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> LLMResponse:
        """Get a completion from Claude."""
        client = self._get_client()
        model_to_use = model or self._default_model
        
        # Separate system message
        system_msg = ""
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            response = await client.messages.create(
                model=model_to_use,
                max_tokens=max_tokens,
                system=system_msg if system_msg else None,
                messages=claude_messages,
                temperature=temperature,
            )
            
            self._total_requests += 1
            self._total_input_tokens += response.usage.input_tokens
            self._total_output_tokens += response.usage.output_tokens
            
            content = response.content[0].text if response.content else ""
            
            return LLMResponse(
                content=content,
                model=model_to_use,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason or "stop",
            )
            
        except Exception as e:
            logger.error(f"Claude completion failed: {e}")
            raise
    
    async def stream_complete(
        self,
        messages: list[LLMMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion tokens from Claude."""
        client = self._get_client()
        model_to_use = model or self._default_model
        
        system_msg = ""
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            async with client.messages.stream(
                model=model_to_use,
                max_tokens=kwargs.get("max_tokens", 500),
                system=system_msg if system_msg else None,
                messages=claude_messages,
            ) as stream:
                self._total_requests += 1
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Claude stream failed: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (Claude uses similar tokenization to GPT)."""
        # Rough estimate
        return len(text) // 4
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        # Sonnet pricing
        input_cost = self._total_input_tokens * 0.003 / 1000
        output_cost = self._total_output_tokens * 0.015 / 1000
        
        return {
            "provider": self.name,
            "model": self._default_model,
            "total_requests": self._total_requests,
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "estimated_cost_usd": round(input_cost + output_cost, 4),
        }


# Register with global registry
def register():
    """Register LLM providers with the global registry."""
    from providers.base import get_registry
    registry = get_registry()
    registry.register_llm("openai", OpenAIProvider)
    registry.register_llm("anthropic", ClaudeProvider)
