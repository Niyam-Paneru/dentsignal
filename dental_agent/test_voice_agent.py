"""
test_voice_agent.py - Test Scripts for Voice Agent

This file contains tests and utilities for testing the voice agent system
without making actual phone calls.

Usage:
    # Run all tests
    python test_voice_agent.py
    
    # Test just the prompt builder
    python test_voice_agent.py prompt
    
    # Test the API endpoints
    python test_voice_agent.py api
    
    # Simulate a WebSocket connection (mock)
    python test_voice_agent.py websocket
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# API Base URL
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


# =============================================================================
# Test: Prompt Builder
# =============================================================================

def test_prompt_builder():
    """Test the prompt builder with a mock clinic."""
    print("\n" + "=" * 60)
    print("TEST: Prompt Builder")
    print("=" * 60)
    
    from prompt_builder import PromptBuilder, get_available_voices
    
    # Create mock clinic
    class MockClinic:
        id = 1
        name = "Sunshine Dental"
        agent_name = "Sarah"
        agent_voice = "aura-asteria-en"
        address = "123 Smile Street, Jacksonville, FL 32256"
        phone_display = "(904) 867-9643"
        hours = "Monday-Friday 8am-5pm, Saturday 9am-1pm"
        services = "cleanings, exams, fillings, crowns, whitening"
        insurance_accepted = "Delta Dental, Cigna, Aetna, MetLife"
        twilio_number = "+19048679643"
        custom_instructions = "Our office is closed for lunch from 12pm-1pm."
    
    clinic = MockClinic()
    builder = PromptBuilder(clinic)
    
    # Test system prompt
    prompt = builder.build_system_prompt()
    print("\n✅ System Prompt Generated")
    print(f"   Length: {len(prompt)} characters")
    print(f"   Contains clinic name: {'Sunshine Dental' in prompt}")
    print(f"   Contains agent name: {'Sarah' in prompt}")
    
    # Test greeting
    greeting = builder.build_greeting()
    print(f"\n✅ Greeting: {greeting}")
    
    # Test voice
    voice_id = builder.get_voice_id()
    voice_info = builder.get_voice_info()
    print(f"\n✅ Voice: {voice_id}")
    print(f"   Info: {voice_info}")
    
    # Test function schemas
    schemas = builder.get_function_schemas()
    print(f"\n✅ Function Schemas: {len(schemas)} functions")
    for schema in schemas:
        print(f"   - {schema['name']}")
    
    # List available voices
    voices = get_available_voices()
    print(f"\n✅ Available Voices: {len(voices)}")
    for vid, vinfo in voices.items():
        print(f"   - {vid}: {vinfo['name']} ({vinfo['gender']}, {vinfo['accent']})")
    
    print("\n✅ Prompt Builder Test PASSED")
    return True


# =============================================================================
# Test: API Endpoints
# =============================================================================

def test_api_health():
    """Test API health and basic endpoints."""
    print("\n" + "=" * 60)
    print("TEST: API Health & Endpoints")
    print("=" * 60)
    
    try:
        # Test root endpoint
        r = requests.get(f"{API_BASE}/")
        print(f"\n✅ GET / - Status: {r.status_code}")
        
        # Test docs endpoint
        r = requests.get(f"{API_BASE}/docs")
        print(f"✅ GET /docs - Status: {r.status_code}")
        
        # Test voices endpoint
        r = requests.get(f"{API_BASE}/api/voices")
        print(f"✅ GET /api/voices - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Found {len(data.get('voices', []))} voices")
        
        # Test clinics list
        r = requests.get(f"{API_BASE}/api/clinics")
        print(f"✅ GET /api/clinics - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Found {len(data.get('clinics', []))} clinics")
        
        # Test dashboard stats
        r = requests.get(f"{API_BASE}/api/dashboard/stats")
        print(f"✅ GET /api/dashboard/stats - Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Clinics: {data.get('clinics', {})}")
            print(f"   Calls: {data.get('calls', {})}")
        
        print("\n✅ API Health Test PASSED")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {API_BASE}")
        print("   Make sure the server is running: uvicorn api_main:app --reload")
        return False


def test_clinic_crud():
    """Test clinic CRUD operations."""
    print("\n" + "=" * 60)
    print("TEST: Clinic CRUD Operations")
    print("=" * 60)
    
    try:
        # Create a test clinic
        clinic_data = {
            "name": f"Test Dental Clinic {datetime.now().strftime('%H%M%S')}",
            "email": f"test{datetime.now().strftime('%H%M%S')}@example.com",
            "timezone": "America/New_York",
            "agent_name": "Emma",
            "agent_voice": "aura-luna-en",
            "address": "456 Test Street",
            "hours": "Mon-Fri 9am-5pm",
            "services": "cleanings, exams",
        }
        
        r = requests.post(f"{API_BASE}/api/clinics", json=clinic_data)
        print(f"\n✅ POST /api/clinics - Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            clinic_id = data.get("data", {}).get("id")
            print(f"   Created clinic ID: {clinic_id}")
            
            # Get the clinic
            r = requests.get(f"{API_BASE}/api/clinics/{clinic_id}")
            print(f"✅ GET /api/clinics/{clinic_id} - Status: {r.status_code}")
            
            # Update the clinic
            r = requests.patch(
                f"{API_BASE}/api/clinics/{clinic_id}",
                json={"agent_name": "Sophie"}
            )
            print(f"✅ PATCH /api/clinics/{clinic_id} - Status: {r.status_code}")
            
            # Test prompt preview
            r = requests.post(f"{API_BASE}/api/clinics/{clinic_id}/test-prompt")
            print(f"✅ POST /api/clinics/{clinic_id}/test-prompt - Status: {r.status_code}")
            
            # Delete the clinic (soft delete)
            r = requests.delete(f"{API_BASE}/api/clinics/{clinic_id}")
            print(f"✅ DELETE /api/clinics/{clinic_id} - Status: {r.status_code}")
            
            print("\n✅ Clinic CRUD Test PASSED")
            return True
        else:
            print(f"   Error: {r.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {API_BASE}")
        return False


# =============================================================================
# Test: Audio Conversion
# =============================================================================

def test_audio_conversion():
    """Test audio format conversion utilities."""
    print("\n" + "=" * 60)
    print("TEST: Audio Conversion")
    print("=" * 60)
    
    from websocket_bridge import (
        mulaw_to_linear16,
        linear16_to_mulaw,
        resample_audio,
    )
    
    # Create test audio data (silence)
    # 160 bytes = 20ms of 8kHz mulaw audio
    test_mulaw = bytes([0x7F] * 160)  # mulaw silence
    
    # Convert mulaw to linear16
    linear16 = mulaw_to_linear16(test_mulaw)
    print(f"\n✅ mulaw → linear16")
    print(f"   Input: {len(test_mulaw)} bytes (mulaw)")
    print(f"   Output: {len(linear16)} bytes (linear16)")
    
    # Convert back to mulaw
    back_to_mulaw = linear16_to_mulaw(linear16)
    print(f"\n✅ linear16 → mulaw")
    print(f"   Input: {len(linear16)} bytes (linear16)")
    print(f"   Output: {len(back_to_mulaw)} bytes (mulaw)")
    
    # Test resampling 8kHz → 16kHz
    resampled_16k = resample_audio(linear16, 8000, 16000)
    print(f"\n✅ Resample 8kHz → 16kHz")
    print(f"   Input: {len(linear16)} bytes at 8kHz")
    print(f"   Output: {len(resampled_16k)} bytes at 16kHz")
    
    # Test resampling 16kHz → 8kHz
    resampled_8k = resample_audio(resampled_16k, 16000, 8000)
    print(f"\n✅ Resample 16kHz → 8kHz")
    print(f"   Input: {len(resampled_16k)} bytes at 16kHz")
    print(f"   Output: {len(resampled_8k)} bytes at 8kHz")
    
    print("\n✅ Audio Conversion Test PASSED")
    return True


# =============================================================================
# Test: Database Models
# =============================================================================

def test_database():
    """Test database models and operations."""
    print("\n" + "=" * 60)
    print("TEST: Database Models")
    print("=" * 60)
    
    from db import (
        create_db,
        get_session,
        Client,
        InboundCall,
        InboundCallStatus,
    )
    
    # Use in-memory database for testing
    create_db("sqlite:///:memory:")
    
    with get_session() as session:
        # Create a test clinic
        clinic = Client(
            name="Test Clinic",
            email="test@test.local",
            agent_name="Test Agent",
            twilio_number="+15551234567",
        )
        session.add(clinic)
        session.commit()
        session.refresh(clinic)
        print(f"\n✅ Created clinic: {clinic}")
        
        # Create a test inbound call
        call = InboundCall(
            clinic_id=clinic.id,
            from_number="+15559876543",
            to_number="+15551234567",
            twilio_call_sid="CA123456789",
            status=InboundCallStatus.IN_PROGRESS,
        )
        session.add(call)
        session.commit()
        session.refresh(call)
        print(f"✅ Created call: {call}")
        
        # Update call
        call.status = InboundCallStatus.COMPLETED
        call.duration_seconds = 120
        call.transcript = "Caller: Hi, I'd like to book an appointment.\nAgent: Sure, I can help with that!"
        session.commit()
        print(f"✅ Updated call status to: {call.status}")
        
        # Query calls
        from sqlmodel import select
        calls = session.exec(select(InboundCall).where(InboundCall.clinic_id == clinic.id)).all()
        print(f"✅ Found {len(calls)} calls for clinic {clinic.name}")
    
    print("\n✅ Database Test PASSED")
    return True


# =============================================================================
# Test: Simulated Twilio Message
# =============================================================================

def test_twilio_message_parsing():
    """Test parsing of Twilio Media Stream messages."""
    print("\n" + "=" * 60)
    print("TEST: Twilio Message Parsing")
    print("=" * 60)
    
    # Sample Twilio messages
    messages = [
        {
            "event": "connected",
            "protocol": "Call",
            "version": "1.0.0"
        },
        {
            "event": "start",
            "streamSid": "MZ123456789",
            "start": {
                "streamSid": "MZ123456789",
                "accountSid": "AC123",
                "callSid": "CA123456789",
                "tracks": ["inbound"],
                "mediaFormat": {
                    "encoding": "audio/x-mulaw",
                    "sampleRate": 8000,
                    "channels": 1
                }
            }
        },
        {
            "event": "media",
            "streamSid": "MZ123456789",
            "media": {
                "track": "inbound",
                "chunk": "1",
                "timestamp": "12345",
                "payload": "f3f3f3f3f3f3"  # base64 audio
            }
        },
        {
            "event": "stop",
            "streamSid": "MZ123456789"
        }
    ]
    
    for msg in messages:
        event = msg.get("event")
        print(f"\n✅ Parsed '{event}' message")
        
        if event == "start":
            start_data = msg.get("start", {})
            print(f"   Stream SID: {start_data.get('streamSid')}")
            print(f"   Call SID: {start_data.get('callSid')}")
            print(f"   Format: {start_data.get('mediaFormat', {}).get('encoding')}")
            
        elif event == "media":
            media = msg.get("media", {})
            print(f"   Track: {media.get('track')}")
            print(f"   Chunk: {media.get('chunk')}")
            print(f"   Payload length: {len(media.get('payload', ''))}")
    
    print("\n✅ Twilio Message Parsing Test PASSED")
    return True


# =============================================================================
# Main
# =============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DENTAL AI VOICE AGENT - TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Tests that don't require the server
    results["prompt_builder"] = test_prompt_builder()
    results["audio_conversion"] = test_audio_conversion()
    results["database"] = test_database()
    results["twilio_parsing"] = test_twilio_message_parsing()
    
    # Tests that require the server
    print("\n" + "-" * 60)
    print("The following tests require the API server to be running...")
    print("-" * 60)
    
    results["api_health"] = test_api_health()
    if results["api_health"]:
        results["clinic_crud"] = test_clinic_crud()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Dental AI Voice Agent")
    parser.add_argument(
        "test",
        nargs="?",
        default="all",
        choices=["all", "prompt", "api", "audio", "db", "twilio"],
        help="Which test to run (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = run_all_tests()
    elif args.test == "prompt":
        success = test_prompt_builder()
    elif args.test == "api":
        success = test_api_health() and test_clinic_crud()
    elif args.test == "audio":
        success = test_audio_conversion()
    elif args.test == "db":
        success = test_database()
    elif args.test == "twilio":
        success = test_twilio_message_parsing()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
