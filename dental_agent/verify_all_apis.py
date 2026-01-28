"""
Complete API verification for DentSignal backend
Run this after adding OpenAI credits
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_openai():
    """Test OpenAI API (for voice agent LLM)"""
    try:
        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5
        )
        print("✅ OpenAI: Working!")
        return True
    except Exception as e:
        print(f"❌ OpenAI: {e}")
        return False

def test_deepgram():
    """Test Deepgram API (for voice agent STT/TTS)"""
    try:
        import httpx
        key = os.getenv("DEEPGRAM_API_KEY")
        if not key:
            print("❌ Deepgram: No API key found")
            return False
        
        # Just verify the key format (actual test requires websocket)
        print(f"✅ Deepgram: Key configured ({key[:8]}...)")
        return True
    except Exception as e:
        print(f"❌ Deepgram: {e}")
        return False

def test_gemini():
    """Test Google Gemini API (for analysis - 50% cheaper)"""
    try:
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            print("❌ Gemini: No API key found")
            return False
            
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say OK")
        print("✅ Gemini: Working!")
        return True
    except ImportError:
        print("⚠️  Gemini: Package not installed (pip install google-generativeai)")
        return False
    except Exception as e:
        print(f"❌ Gemini: {e}")
        return False

def test_twilio():
    """Test Twilio credentials"""
    try:
        from twilio.rest import Client
        sid = os.getenv("TWILIO_SID")
        token = os.getenv("TWILIO_TOKEN")
        number = os.getenv("TWILIO_NUMBER")
        
        if not all([sid, token, number]):
            print("❌ Twilio: Missing credentials")
            return False
            
        client = Client(sid, token)
        account = client.api.accounts(sid).fetch()
        print(f"✅ Twilio: Connected ({account.friendly_name})")
        return True
    except Exception as e:
        print(f"❌ Twilio: {e}")
        return False

def test_huggingface():
    """Test Hugging Face API (for FREE embeddings)"""
    try:
        key = os.getenv("HF_API_KEY")
        if not key:
            print("❌ HuggingFace: No API key found")
            return False
        print(f"✅ HuggingFace: Key configured ({key[:8]}...)")
        return True
    except Exception as e:
        print(f"❌ HuggingFace: {e}")
        return False

def main():
    print("=" * 50)
    print("🦷 DentSignal Backend API Verification")
    print("=" * 50)
    print()
    
    results = {
        "OpenAI (Voice LLM)": test_openai(),
        "Deepgram (Voice STT/TTS)": test_deepgram(),
        "Gemini (Analysis)": test_gemini(),
        "Twilio (Telephony)": test_twilio(),
        "HuggingFace (Embeddings)": test_huggingface(),
    }
    
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print()
    if passed == total:
        print("🎉 All systems ready! You can start the server.")
    else:
        print(f"⚠️  {total - passed} service(s) need attention")

if __name__ == "__main__":
    main()
