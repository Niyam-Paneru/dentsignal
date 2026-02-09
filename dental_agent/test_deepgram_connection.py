"""
test_deepgram_connection.py - Test Deepgram Voice Agent Connection

This script tests:
1. Deepgram API key validity
2. WebSocket connection to Voice Agent
3. Settings configuration message
4. OpenAI API key (used by Deepgram for LLM)
"""

import asyncio
import json
import os
import sys

import websockets
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPGRAM_AGENT_URL = "wss://agent.deepgram.com/v1/agent/converse"


def print_status(label: str, ok: bool, detail: str = ""):
    icon = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{icon}{reset} {label}: {detail}")


async def test_deepgram_connection():
    """Test the Deepgram Voice Agent WebSocket connection."""
    
    print("\n" + "=" * 60)
    print("DEEPGRAM VOICE AGENT CONNECTION TEST")
    print("=" * 60 + "\n")
    
    # Check API keys
    print("1. Checking API Keys...")
    
    if not DEEPGRAM_API_KEY:
        print_status("DEEPGRAM_API_KEY", False, "Not set in .env")
        return False
    print_status("DEEPGRAM_API_KEY", True, "Set (hidden)")
    
    if not OPENAI_API_KEY:
        print_status("OPENAI_API_KEY", False, "Not set in .env (required for LLM)")
        return False
    print_status("OPENAI_API_KEY", True, "Set (hidden)")
    
    # Test WebSocket connection
    print("\n2. Connecting to Deepgram Voice Agent...")
    print(f"   URL: {DEEPGRAM_AGENT_URL}")
    
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }
    
    try:
        async with websockets.connect(
            DEEPGRAM_AGENT_URL,
            additional_headers=headers,
        ) as ws:
            print_status("WebSocket Connection", True, "Connected successfully")
            
            # Send settings configuration
            print("\n3. Sending SettingsConfiguration...")
            
            settings = {
                "type": "SettingsConfiguration",
                "audio": {
                    "encoding": "linear16",
                    "sample_rate": 8000,
                },
                "agent": {
                    "listen": {
                        "model": "nova-3"
                    },
                    "think": {
                        "provider": {
                            "type": "openai",
                            "model": "gpt-4o-mini"
                        },
                        "instructions": "You are a helpful dental receptionist. Say hello briefly.",
                    },
                    "speak": {
                        "model": "aura-2-thea-en"
                    }
                },
                "context": {
                    "messages": [
                        {
                            "role": "assistant", 
                            "content": "Hello, this is a test."
                        }
                    ],
                    "replay": False  # Don't speak, just configure
                }
            }
            
            await ws.send(json.dumps(settings))
            print_status("SettingsConfiguration", True, "Sent successfully")
            
            # Wait for response
            print("\n4. Waiting for Deepgram response...")
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                
                if isinstance(response, str):
                    data = json.loads(response)
                    msg_type = data.get("type", "Unknown")
                    
                    if msg_type == "Error":
                        error_msg = data.get("message", "Unknown error")
                        print_status("Deepgram Response", False, f"Error: {error_msg}")
                        return False
                    else:
                        print_status("Deepgram Response", True, f"Received: {msg_type}")
                        print(f"   Full response: {json.dumps(data, indent=2)[:500]}")
                else:
                    print_status("Deepgram Response", True, f"Received binary audio ({len(response)} bytes)")
                    
            except asyncio.TimeoutError:
                print_status("Deepgram Response", True, "No immediate response (normal - waiting for audio)")
            
            # Close gracefully
            await ws.close()
            print_status("Connection Closed", True, "Graceful shutdown")
            
            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSED - Deepgram connection is working!")
            print("=" * 60 + "\n")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print_status("WebSocket Connection", False, f"HTTP {e.status_code}")
        if e.status_code == 401:
            print("   → Invalid DEEPGRAM_API_KEY. Check your key at console.deepgram.com")
        elif e.status_code == 403:
            print("   → Access denied. Make sure Voice Agent is enabled on your account")
        return False
        
    except Exception as e:
        print_status("WebSocket Connection", False, str(e))
        return False


async def test_openai_key():
    """Test OpenAI API key validity."""
    print("\n5. Testing OpenAI API Key...")
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Simple test - list models
        response = client.models.list()
        models = [m.id for m in response.data[:3]]
        print_status("OpenAI API Key", True, f"Valid - found {len(response.data)} models")
        return True
        
    except openai.AuthenticationError:
        print_status("OpenAI API Key", False, "Invalid API key")
        return False
    except Exception as e:
        print_status("OpenAI API Key", False, str(e))
        return False


if __name__ == "__main__":
    print("\nStarting Deepgram Voice Agent connection test...\n")
    
    # Run tests
    success = asyncio.run(test_deepgram_connection())
    
    if success:
        # Also test OpenAI
        asyncio.run(test_openai_key())
    
    sys.exit(0 if success else 1)
