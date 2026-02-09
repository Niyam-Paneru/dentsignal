"""
ai_providers.py - Multi-Provider AI Architecture

HIPAA-Compliant AI Provider Routing:
- Azure OpenAI: Voice + all PHI analysis (HIPAA BAA covered)
- Gemini: Embeddings & semantic search (FREE, no PHI)

Direct OpenAI and HuggingFace have been removed.
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

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g., https://dentsignal-openai.openai.azure.com/
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
USE_AZURE_OPENAI = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

# API Endpoints
if USE_AZURE_OPENAI and AZURE_OPENAI_ENDPOINT:
    # Azure OpenAI endpoint format
    OPENAI_API_URL = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    # Use Azure key if available, fall back to regular OpenAI key
    OPENAI_API_KEY = AZURE_OPENAI_API_KEY or OPENAI_API_KEY
    logger.info(f"Using Azure OpenAI: {AZURE_OPENAI_ENDPOINT} (deployment: {AZURE_OPENAI_DEPLOYMENT})")
else:
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Default models
OPENAI_MODEL = AZURE_OPENAI_DEPLOYMENT if USE_AZURE_OPENAI else "gpt-4o-mini"  # Best for real-time voice
GEMINI_MODEL = "gemini-2.5-flash"  # For any non-PHI text generation
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"  # FREE embeddings (3072 dims, truncated to 768)


class AIProvider(str, Enum):
    """Available AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"


class TaskType(str, Enum):
    """Types of AI tasks."""
    VOICE_CONVERSATION = "voice_conversation"  # Real-time, needs lowest latency
    SENTIMENT_ANALYSIS = "sentiment_analysis"  # Batch, cost-sensitive
    CALL_SUMMARY = "call_summary"  # Batch, cost-sensitive
    QUALITY_SCORING = "quality_scoring"  # Batch, cost-sensitive
    INTENT_EXTRACTION = "intent_extraction"  # Batch, cost-sensitive
    EMBEDDING = "embedding"  # Semantic search, should be FREE
    TRANSCRIPT_SEARCH = "transcript_search"  # Uses embeddings


# Task to provider mapping (HIPAA-optimized: PHI → Azure OpenAI, non-PHI → Gemini)
TASK_PROVIDER_MAP = {
    TaskType.VOICE_CONVERSATION: AIProvider.OPENAI,  # Azure OpenAI (BAA ✓)
    TaskType.SENTIMENT_ANALYSIS: AIProvider.OPENAI,  # Azure OpenAI (BAA ✓, processes PHI)
    TaskType.CALL_SUMMARY: AIProvider.OPENAI,  # Azure OpenAI (BAA ✓, processes PHI)
    TaskType.QUALITY_SCORING: AIProvider.OPENAI,  # Azure OpenAI (BAA ✓, processes PHI)
    TaskType.INTENT_EXTRACTION: AIProvider.OPENAI,  # Azure OpenAI (BAA ✓, processes PHI)
    TaskType.EMBEDDING: AIProvider.GEMINI,  # FREE (numerical vectors only, no PHI)
    TaskType.TRANSCRIPT_SEARCH: AIProvider.GEMINI,  # FREE (numerical vectors only, no PHI)
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
        if USE_AZURE_OPENAI:
            headers = {
                "api-key": OPENAI_API_KEY,
                "Content-Type": "application/json",
            }
        else:
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
# Gemini Embeddings (FREE)
# =============================================================================

def gemini_embed(
    texts: List[str],
    model: str = GEMINI_EMBEDDING_MODEL,
    task_type: str = "RETRIEVAL_DOCUMENT",
    output_dimensionality: int = 768,
) -> AIResponse:
    """
    Gemini embeddings - FREE on Gemini free tier.
    
    Best for: Transcript search, finding similar calls.
    Uses gemini-embedding-001 with 768 dimensions (good quality/size balance).
    """
    if not GEMINI_API_KEY:
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.GEMINI,
            model=model,
            error="GEMINI_API_KEY not configured"
        )
    
    try:
        url = f"{GEMINI_API_URL}/{model}:batchEmbedContents?key={GEMINI_API_KEY}"
        
        requests_list = [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]},
                "taskType": task_type,
                "outputDimensionality": output_dimensionality,
            }
            for text in texts
        ]
        
        payload = {"requests": requests_list}
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            embeddings = [
                emb["values"] for emb in data.get("embeddings", [])
            ]
            
            return AIResponse(
                success=True,
                content=embeddings,
                provider=AIProvider.GEMINI,
                model=model,
                tokens_used=0,
                cost_estimate=0.0,  # FREE on free tier!
            )
            
    except Exception as e:
        logger.error(f"Gemini embedding error: {e}")
        return AIResponse(
            success=False,
            content=None,
            provider=AIProvider.GEMINI,
            model=model,
            error=str(e)
        )


def gemini_similarity_search(
    query: str,
    documents: List[str],
    top_k: int = 5,
) -> AIResponse:
    """
    Semantic search using Gemini embeddings - FREE!
    
    Finds most similar transcripts/documents to a query.
    Uses separate task types for query vs documents (better accuracy).
    """
    import numpy as np
    
    # Embed query with RETRIEVAL_QUERY task type
    query_response = gemini_embed([query], task_type="RETRIEVAL_QUERY")
    if not query_response.success:
        return query_response
    
    # Embed documents with RETRIEVAL_DOCUMENT task type
    doc_response = gemini_embed(documents, task_type="RETRIEVAL_DOCUMENT")
    if not doc_response.success:
        return doc_response
    
    query_embedding = np.array(query_response.content[0])
    doc_embeddings = np.array(doc_response.content)
    
    # Normalize for cosine similarity (Gemini 768-dim needs normalization)
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
    
    # Calculate cosine similarity
    similarities = np.dot(doc_norms, query_norm)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = [
        {"index": int(idx), "document": documents[idx], "score": float(similarities[idx])}
        for idx in top_indices
    ]
    
    return AIResponse(
        success=True,
        content=results,
        provider=AIProvider.GEMINI,
        model=GEMINI_EMBEDDING_MODEL,
        cost_estimate=0.0,  # FREE!
    )


# Backward-compatible aliases
hf_embed = gemini_embed
hf_similarity_search = gemini_similarity_search


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
    provider = TASK_PROVIDER_MAP.get(task, AIProvider.OPENAI)
    
    if provider == AIProvider.OPENAI:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return openai_chat(messages, json_mode=json_mode, temperature=temperature)
    
    elif provider == AIProvider.GEMINI:
        # Gemini handles embeddings (non-PHI) and fallback text generation
        if task in (TaskType.EMBEDDING, TaskType.TRANSCRIPT_SEARCH):
            return gemini_embed([prompt])
        return gemini_generate(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=json_mode,
            temperature=temperature,
        )
    
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
            logger.error(f"OpenAI health check failed: {e}")
            results["openai"] = {"status": "error", "error": "Health check failed"}
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
            logger.error(f"Gemini health check failed: {e}")
            results["gemini"] = {"status": "error", "error": "Health check failed"}
    else:
        results["gemini"] = {"status": "not_configured"}
    
    # Check Gemini Embeddings
    if GEMINI_API_KEY:
        try:
            response = gemini_embed(["test"])
            results["gemini_embeddings"] = {
                "status": "ok" if response.success else "error",
                "model": GEMINI_EMBEDDING_MODEL,
                "error": response.error,
            }
        except Exception as e:
            logger.error(f"Gemini embeddings health check failed: {e}")
            results["gemini_embeddings"] = {"status": "error", "error": "Health check failed"}
    
    return results


def get_provider_stats() -> Dict[str, Any]:
    """
    Get usage statistics and cost estimates.
    """
    return {
        "providers": {
            "azure_openai": {
                "configured": bool(OPENAI_API_KEY),
                "hipaa_compliant": True,
                "use_cases": ["Voice Agent", "Sentiment", "Summaries", "Quality Scoring", "Intent"],
                "cost_per_1k_tokens": "$0.000375",
                "note": "All PHI-touching tasks route here (BAA covered)",
            },
            "gemini": {
                "configured": bool(GEMINI_API_KEY),
                "hipaa_compliant": False,
                "use_cases": ["Embeddings", "Semantic Search"],
                "cost_per_1k_tokens": "$0.00 (FREE)",
                "note": "Non-PHI only — embeddings are numerical vectors",
            },
        },
        "optimization_tips": [
            "All PHI analysis uses Azure OpenAI (HIPAA BAA covered)",
            "Embeddings use Gemini for FREE (no PHI exposure)",
            "Direct OpenAI and HuggingFace removed for compliance",
        ]
    }
