"""Quick test to verify OpenAI API key works"""
import os
from dotenv import load_dotenv

load_dotenv()

import openai

def test_openai():
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5
        )
        print("✅ OpenAI API Key works!")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return False

if __name__ == "__main__":
    test_openai()
