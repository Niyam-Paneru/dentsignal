"""
ai_providers.py - Multi-Provider AI Architecture

Optimized AI provider selection:
- OpenAI: Real-time voice conversations (lowest latency)
- Gemini: Post-call analysis, sentiment, summaries (best cost/performance)
- Hugging Face: Embeddings, semantic search (FREE)

This architecture cuts AI costs by 50%+ while maintaining quality.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# API Endpoints
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
HF_INFERENCE_URL = "https://api-inference.huggingface.co/models"

# Default models
OPENAI_MODEL = "gpt-4o-mini"  # Best for real-time voice
GEMINI_MODEL = "gemini-2.0-flash"  # Best for batch analysis
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # FREE embeddings


class AIProvider(str, Enum):
    """Available AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"


class TaskType(str, Enum):
    """Types of AI tasks."""
    VOICE_CONVERSATION = "voice_conversation"  # Real-time, needs lowest latency
    SENTIMENT_ANALYSIS = "sentiment_analysis"  # Batch, cost-sensitive
    CALL_SUMMARY = "call_summary"  # Batch, cost-sensitive
    QUALITY_SCORING = "quality_scoring"  # Batch, cost-sensitive
    INTENT_EXTRACTION = "intent_extraction"  # Batch, cost-sensitive
    EMBEDDING = "embedding"  # Semantic search, should be FREE
    TRANSCRIPT_SEARCH = "transcript_search"  # Uses embeddings


# Task to provider mapping (optimized for cost + performance)
TASK_PROVIDER_MAP = {
    TaskType.VOICE_CONVERSATION: AIProvider.OPENAI,  # Latency critical
    TaskType.SENTIMENT_ANALYSIS: AIProvider.GEMINI,  # 50% cheaper
    TaskType.CALL_SUMMARY: AIProvider.GEMINI,  # 50% cheaper
    TaskType.QUALITY_SCORING: AIProvider.GEMINI,  # 50% cheaper
    TaskType.INTENT_EXTRACTION: AIProvider.GEMINI,  # 50% cheaper
    TaskType.EMBEDDING: AIProvider.HUGGINGFACE,  # FREE
    TaskType.TRANSCRIPT_SEARCH: AIProvider.HUGGINGFACE,  # FREE
}


@dataclass
class AIResponse:
    """Standardized AI response."""
    success: bool
    content: Any
    provider: AIProvider
    model: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    error: Optional[str] = None


# =============================================================================
# OpenAI Provider (Real-time Voice)
# =============================================================================

def openai_chat(
    messages: List[Dict[str, str]],
    model: str = OPENAI_MODEL,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> AIResponse:
    """
    OpenAI chat completion - use for real-time voice conversations.
    
    Best for: Voice agent responses (lowest latency)
    """
    if not OPENAI_API_KEY:
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.OPENAI,
            model=model,
            error="OPENAI_API_KEY not configured"
        )
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            
            # Estimate cost (gpt-4o-mini pricing)
            cost = (tokens / 1_000_000) * 0.375  # Avg of input/output
            
            return AIResponse(
                success=True,
                content=json.loads(content) if json_mode else content,
                provider=AIProvider.OPENAI,
                model=model,
                tokens_used=tokens,
                cost_estimate=cost,
            )
            
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.OPENAI,
            model=model,
            error=str(e)
        )


# =============================================================================
# Gemini Provider (Cost-Effective Analysis)
# =============================================================================

def gemini_generate(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = GEMINI_MODEL,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> AIResponse:
    """
    Gemini text generation - use for batch analysis tasks.
    
    Best for: Sentiment analysis, summaries, quality scoring
    50% cheaper than OpenAI for these tasks!
    """
    if not GEMINI_API_KEY:
        # Fallback to OpenAI if Gemini not configured
        logger.warning("GEMINI_API_KEY not configured, falling back to OpenAI")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return openai_chat(messages, json_mode=json_mode)
    
    try:
        url = f"{GEMINI_API_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
        
        contents = [{"parts": [{"text": prompt}]}]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from Gemini response
            candidates = data.get("candidates", [])
            if not candidates:
                return AIResponse(
                    success=False,
                    content=None,
                    provider=AIProvider.GEMINI,
                    model=model,
                    error="No response candidates"
                )
            
            content = candidates[0]["content"]["parts"][0]["text"]
            
            # Token counting from usage metadata
            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", 0)
            
            # Estimate cost (Gemini 1.5 Flash pricing - 50% of OpenAI)
            cost = (tokens / 1_000_000) * 0.1875
            
            return AIResponse(
                success=True,
                content=json.loads(content) if json_mode else content,
                provider=AIProvider.GEMINI,
                model=model,
                tokens_used=tokens,
                cost_estimate=cost,
            )
            
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return raw content
        logger.warning(f"Gemini JSON parse failed: {e}")
        return AIResponse(
            success=True,
            content=content,
            provider=AIProvider.GEMINI,
            model=model,
            error="JSON parse failed, returning raw content"
        )
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.GEMINI,
            model=model,
            error=str(e)
        )


# =============================================================================
# Hugging Face Provider (FREE Embeddings)
# =============================================================================

def hf_embed(
    texts: List[str],
    model: str = HF_EMBEDDING_MODEL,
) -> AIResponse:
    """
    Hugging Face embeddings - FREE for semantic search.
    
    Best for: Transcript search, finding similar calls
    """
    if not HF_API_KEY:
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.HUGGINGFACE,
            model=model,
            error="HF_API_KEY not configured"
        )
    
    try:
        url = f"{HF_INFERENCE_URL}/{model}"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        
        payload = {"inputs": texts, "options": {"wait_for_model": True}}
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            embeddings = response.json()
            
            return AIResponse(
                success=True,
                content=embeddings,
                provider=AIProvider.HUGGINGFACE,
                model=model,
                tokens_used=0,
                cost_estimate=0.0,  # FREE!
            )
            
    except Exception as e:
        logger.error(f"Hugging Face error: {e}")
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.HUGGINGFACE,
            model=model,
            error=str(e)
        )


def hf_similarity_search(
    query: str,
    documents: List[str],
    top_k: int = 5,
) -> AIResponse:
    """
    Semantic search using HF embeddings - FREE!
    
    Finds most similar transcripts/documents to a query.
    """
    import numpy as np
    
    # Get embeddings for query and documents
    all_texts = [query] + documents
    embed_response = hf_embed(all_texts)
    
    if not embed_response.success:
        return embed_response
    
    embeddings = embed_response.content
    query_embedding = np.array(embeddings[0])
    doc_embeddings = np.array(embeddings[1:])
    
    # Calculate cosine similarity
    similarities = np.dot(doc_embeddings, query_embedding) / (
        np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = [
        {"index": int(idx), "document": documents[idx], "score": float(similarities[idx])}
        for idx in top_indices
    ]
    
    return AIResponse(
        success=True,
        content=results,
        provider=AIProvider.HUGGINGFACE,
        model=HF_EMBEDDING_MODEL,
        cost_estimate=0.0,  # FREE!
    )


# =============================================================================
# Unified Interface
# =============================================================================

def ai_complete(
    task: TaskType,
    prompt: str,
    system_instruction: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.3,
) -> AIResponse:
    """
    Unified AI completion interface.
    
    Automatically routes to the optimal provider based on task type.
    
    Args:
        task: Type of task (determines provider)
        prompt: The prompt/query
        system_instruction: System message (optional)
        json_mode: Whether to return JSON
        temperature: Creativity (0.0-1.0)
    
    Returns:
        AIResponse with result from optimal provider
    """
    provider = TASK_PROVIDER_MAP.get(task, AIProvider.GEMINI)
    
    if provider == AIProvider.OPENAI:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return openai_chat(messages, json_mode=json_mode, temperature=temperature)
    
    elif provider == AIProvider.GEMINI:
        return gemini_generate(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=json_mode,
            temperature=temperature,
        )
    
    elif provider == AIProvider.HUGGINGFACE:
        # HF is only for embeddings, not chat
        return hf_embed([prompt])
    
    return AIResponse(
        success=False,
        content=None,
        provider=provider,
        model="unknown",
        error=f"Unknown provider: {provider}"
    )


# =============================================================================
# Provider Health Check
# =============================================================================

def check_all_providers() -> Dict[str, Any]:
    """
    Check health of all AI providers.
    
    Useful for dashboard status display.
    """
    results = {}
    
    # Check OpenAI
    if OPENAI_API_KEY:
        try:
            response = openai_chat([{"role": "user", "content": "Hi"}], temperature=0)
            results["openai"] = {
                "status": "ok" if response.success else "error",
                "model": OPENAI_MODEL,
                "error": response.error,
            }
        except Exception as e:
            results["openai"] = {"status": "error", "error": str(e)}
    else:
        results["openai"] = {"status": "not_configured"}
    
    # Check Gemini
    if GEMINI_API_KEY:
        try:
            response = gemini_generate("Hi", temperature=0)
            results["gemini"] = {
                "status": "ok" if response.success else "error",
                "model": GEMINI_MODEL,
                "error": response.error,
            }
        except Exception as e:
            results["gemini"] = {"status": "error", "error": str(e)}
    else:
        results["gemini"] = {"status": "not_configured"}
    
    # Check Hugging Face
    if HF_API_KEY:
        try:
            response = hf_embed(["test"])
            results["huggingface"] = {
                "status": "ok" if response.success else "error",
                "model": HF_EMBEDDING_MODEL,
                "error": response.error,
            }
        except Exception as e:
            results["huggingface"] = {"status": "error", "error": str(e)}
    else:
        results["huggingface"] = {"status": "not_configured"}
    
    return results


def get_provider_stats() -> Dict[str, Any]:
    """
    Get usage statistics and cost estimates.
    """
    return {
        "providers": {
            "openai": {
                "configured": bool(OPENAI_API_KEY),
                "use_cases": ["Voice Agent (real-time)"],
                "cost_per_1k_tokens": "$0.000375",
            },
            "gemini": {
                "configured": bool(GEMINI_API_KEY),
                "use_cases": ["Sentiment", "Summaries", "Quality Scoring"],
                "cost_per_1k_tokens": "$0.0001875",
                "savings_vs_openai": "50%",
            },
            "huggingface": {
                "configured": bool(HF_API_KEY),
                "use_cases": ["Embeddings", "Semantic Search"],
                "cost_per_1k_tokens": "$0.00 (FREE)",
                "savings_vs_openai": "100%",
            },
        },
        "optimization_tips": [
            "Voice calls use OpenAI for lowest latency",
            "Post-call analysis uses Gemini (50% cheaper)",
            "Transcript search uses HuggingFace (FREE)",
        ]
    }
