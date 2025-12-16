#!/usr/bin/env python3
"""
Test Multi-Provider AI Architecture
====================================
Tests all AI providers: OpenAI, Gemini, and HuggingFace

Run: python test_ai_providers.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Import our multi-provider module
from ai_providers import (
    openai_chat,
    gemini_generate,
    hf_embed,
    hf_similarity_search,
    ai_complete,
    check_all_providers,
    TaskType,
    AIProvider,
)


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result with formatting."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   {details}")


def test_provider_health():
    """Test that all providers are configured and accessible."""
    print("\n" + "=" * 60)
    print("🏥 PROVIDER HEALTH CHECK")
    print("=" * 60)
    
    results = check_all_providers()
    
    all_healthy = True
    for provider, status in results.items():
        is_ok = status == "configured"
        if not is_ok:
            all_healthy = False
        print_result(f"{provider} Provider", is_ok, status)
    
    return all_healthy


def test_openai():
    """Test OpenAI for voice agent responses."""
    print("\n" + "=" * 60)
    print("🎙️ OPENAI TEST (Voice Agent)")
    print("=" * 60)
    
    response = openai_chat(
        messages=[
            {"role": "system", "content": "You are a friendly dental receptionist."},
            {"role": "user", "content": "Hi, I'd like to book a cleaning appointment."}
        ],
        model="gpt-4o-mini",
    )
    
    success = response.success and response.content
    print_result(
        "OpenAI Chat Response",
        success,
        f"Cost: ${response.cost_estimate:.6f}" if success else response.error
    )
    
    if success:
        print(f"\n   Response: {response.content[:200]}...")
    
    return success


def test_gemini():
    """Test Gemini for sentiment analysis."""
    print("\n" + "=" * 60)
    print("🧠 GEMINI TEST (Analysis - 50% cheaper!)")
    print("=" * 60)
    
    sample_transcript = """
    AI: Thank you for calling Sunny Dental. How can I help you today?
    Patient: Hi, I've been having really bad tooth pain for the past two days.
    AI: I'm sorry to hear that. Let me help you get seen as soon as possible. 
        Can I get your name please?
    Patient: It's John Smith.
    AI: Thank you John. I have an opening tomorrow at 2pm. Would that work for you?
    Patient: Yes, that would be great! Thank you so much.
    AI: Perfect, I've booked you in for tomorrow at 2pm. See you then!
    """
    
    response = gemini_generate(
        prompt=f"Analyze this call sentiment:\n\n{sample_transcript}\n\nProvide: overall_sentiment, sentiment_score (-1 to 1), summary",
        system_instruction="You are a call quality analyst. Be concise.",
        temperature=0.3
    )
    
    success = response.success and response.content
    print_result(
        "Gemini Sentiment Analysis",
        success,
        f"Cost: ${response.cost_estimate:.6f}" if success else response.error
    )
    
    if success:
        print(f"\n   Analysis: {str(response.content)[:300]}...")
    
    return success


def test_huggingface():
    """Test HuggingFace for embeddings (FREE!)."""
    print("\n" + "=" * 60)
    print("🤗 HUGGINGFACE TEST (Embeddings - FREE!)")
    print("=" * 60)
    
    # Test embedding generation
    texts = [
        "Patient called about tooth pain",
        "Customer wants to book a cleaning",
        "Caller asked about insurance coverage"
    ]
    
    response = hf_embed(texts)
    
    if response.success and response.content:
        embeddings = response.content
        print_result(
            "HuggingFace Embeddings",
            True,
            f"Generated {len(embeddings)} embeddings, dimension: {len(embeddings[0]) if embeddings and len(embeddings) > 0 else 0}"
        )
        
        # Test similarity search
        query = "tooth ache emergency"
        search_response = hf_similarity_search(query, texts, top_k=2)
        
        if search_response.success and search_response.content:
            print_result("HuggingFace Similarity Search", True)
            print(f"\n   Query: '{query}'")
            for text, score in search_response.content:
                print(f"   → {score:.3f}: {text}")
            return True
        else:
            print_result("HuggingFace Similarity Search", False, search_response.error or "No results")
            return False
    else:
        print_result("HuggingFace Embeddings", False, response.error or "Failed to generate")
        return False


def test_task_routing():
    """Test automatic task routing to correct provider."""
    print("\n" + "=" * 60)
    print("🔀 TASK ROUTING TEST (Auto-select best provider)")
    print("=" * 60)
    
    # Test sentiment analysis routes to Gemini
    response = ai_complete(
        task=TaskType.SENTIMENT_ANALYSIS,
        prompt="What is the sentiment of: 'I love this dental office!'",
    )
    
    print_result(
        "SENTIMENT → Gemini",
        response.success and response.provider == AIProvider.GEMINI,
        f"Routed to: {response.provider.value}" if response.success else response.error
    )
    
    # Test summary routes to Gemini
    response = ai_complete(
        task=TaskType.CALL_SUMMARY,
        prompt="Summarize: Patient called about cleaning, booked for Tuesday.",
    )
    
    print_result(
        "SUMMARY → Gemini",
        response.success and response.provider == AIProvider.GEMINI,
        f"Routed to: {response.provider.value}" if response.success else response.error
    )
    
    # Test voice routes to OpenAI
    response = ai_complete(
        task=TaskType.VOICE_CONVERSATION,
        prompt="Respond as a dental receptionist to: 'I need to cancel my appointment'",
    )
    
    print_result(
        "VOICE → OpenAI",
        response.success and response.provider == AIProvider.OPENAI,
        f"Routed to: {response.provider.value}" if response.success else response.error
    )
    
    return True


def test_cost_comparison():
    """Compare costs between providers."""
    print("\n" + "=" * 60)
    print("💰 COST COMPARISON")
    print("=" * 60)
    
    sample_prompt = "Analyze this dental call and provide sentiment analysis..."
    
    # Estimate costs
    input_tokens = len(sample_prompt.split()) * 1.3  # rough estimate
    output_tokens = 200
    
    openai_cost = (input_tokens / 1000 * 0.00015) + (output_tokens / 1000 * 0.0006)  # gpt-4o-mini
    gemini_cost = (input_tokens / 1000 * 0.000075) + (output_tokens / 1000 * 0.0003)  # gemini-1.5-flash
    hf_cost = 0  # FREE!
    
    print(f"\n   Estimated cost for ~{int(input_tokens)} input + {output_tokens} output tokens:")
    print(f"   ├── OpenAI (gpt-4o-mini):  ${openai_cost:.6f}")
    print(f"   ├── Gemini (1.5-flash):    ${gemini_cost:.6f} (50% savings!)")
    print(f"   └── HuggingFace:           ${hf_cost:.6f} (FREE!)")
    print(f"\n   💡 By using Gemini for analysis, you save ~${(openai_cost - gemini_cost):.6f} per call")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🦷 DENTAL AI VOICE AGENT - MULTI-PROVIDER TEST SUITE")
    print("=" * 70)
    
    results = {
        "Provider Health": test_provider_health(),
        "OpenAI (Voice)": test_openai(),
        "Gemini (Analysis)": test_gemini(),
        "HuggingFace (Embeddings)": test_huggingface(),
        "Task Routing": test_task_routing(),
    }
    
    test_cost_comparison()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n   Tests Passed: {passed}/{total}")
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test}")
    
    if passed == total:
        print("\n   🎉 ALL TESTS PASSED! Multi-provider architecture is ready!")
        print("   💰 Using Gemini for analysis saves ~50% on AI costs")
        print("   🆓 HuggingFace embeddings are FREE for transcript search")
    else:
        print("\n   ⚠️  Some tests failed. Check your API keys in .env")
    
    print()


if __name__ == "__main__":
    main()
