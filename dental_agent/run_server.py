"""
run_server.py - Quick Start Script for Dental AI Voice Agent

This script:
1. Checks environment configuration
2. Optionally starts ngrok tunnel
3. Updates environment with ngrok URLs
4. Starts the FastAPI server

Usage:
    python run_server.py              # Start server only
    python run_server.py --ngrok      # Start with ngrok tunnel
    python run_server.py --help       # Show help
"""

import argparse
import os
import subprocess
import sys
import time
from dotenv import load_dotenv, set_key

load_dotenv()


def check_env():
    """Check required environment variables."""
    print("\n🔍 Checking environment configuration...")
    
    required = {
        "DEEPGRAM_API_KEY": "Deepgram API key for Voice Agent",
        "OPENAI_API_KEY": "OpenAI API key for LLM",
        "TWILIO_SID": "Twilio Account SID",
        "TWILIO_TOKEN": "Twilio Auth Token",
        "TWILIO_NUMBER": "Your Twilio phone number",
    }
    
    missing = []
    for key, desc in required.items():
        value = os.getenv(key, "")
        if not value or value.startswith("your-"):
            missing.append(f"  - {key}: {desc}")
            print(f"  ❌ {key}: Not configured")
        else:
            # Mask the value
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"  ✅ {key}: {masked}")
    
    if missing:
        print("\n⚠️  Missing environment variables!")
        print("Please update your .env file with the following:")
        for m in missing:
            print(m)
        print("\nCopy .env.example to .env if you haven't already:")
        print("  copy .env.example .env")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True


def start_ngrok(port: int = 8000) -> str:
    """Start ngrok tunnel and return the public URL."""
    print(f"\n🌐 Starting ngrok tunnel on port {port}...")
    
    try:
        # Start ngrok in background
        process = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Get the public URL from ngrok API
        import requests
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json().get("tunnels", [])
        
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                url = tunnel.get("public_url")
                print(f"  ✅ ngrok tunnel: {url}")
                return url
        
        print("  ❌ Could not get ngrok URL")
        return None
        
    except FileNotFoundError:
        print("  ❌ ngrok not found. Install it from: https://ngrok.com/download")
        print("  Or install via: choco install ngrok (Windows)")
        return None
    except Exception as e:
        print(f"  ❌ Error starting ngrok: {e}")
        return None


def update_env_urls(ngrok_url: str):
    """Update .env file with ngrok URLs."""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print("  ⚠️  .env file not found, creating from .env.example")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
    
    # Update the URLs
    api_url = ngrok_url
    ws_url = ngrok_url.replace("https://", "wss://")
    
    set_key(env_file, "API_BASE_URL", api_url)
    set_key(env_file, "WS_BASE_URL", ws_url)
    
    print(f"\n📝 Updated .env with ngrok URLs:")
    print(f"  API_BASE_URL={api_url}")
    print(f"  WS_BASE_URL={ws_url}")
    
    print(f"\n📱 Configure Twilio Webhook:")
    print(f"  URL: {api_url}/inbound/voice")
    print(f"  Method: POST")


def print_twilio_instructions():
    """Print Twilio webhook configuration instructions."""
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("📱 TWILIO WEBHOOK CONFIGURATION")
    print("=" * 60)
    print(f"""
1. Go to Twilio Console: https://console.twilio.com/
2. Navigate to: Phone Numbers → Manage → Active Numbers
3. Click on your number: {os.getenv('TWILIO_NUMBER', '+1XXXXXXXXXX')}
4. Under "Voice Configuration":
   - Configure with: Webhook
   - URL: {api_url}/inbound/voice
   - HTTP Method: POST
5. Save the configuration

Then call your Twilio number to test the voice agent!
""")


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Start the FastAPI server."""
    print("\n" + "=" * 60)
    print("🚀 STARTING DENTAL AI VOICE AGENT SERVER")
    print("=" * 60)
    
    print(f"\n  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Reload: {reload}")
    print(f"\n  API Docs: http://localhost:{port}/docs")
    print(f"  Health: http://localhost:{port}/health")
    
    print("\n" + "-" * 60)
    print("Press Ctrl+C to stop the server")
    print("-" * 60 + "\n")
    
    # Build command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api_main:app",
        f"--host={host}",
        f"--port={port}",
    ]
    
    if reload:
        cmd.append("--reload")
    
    # Run the server
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Start the Dental AI Voice Agent server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_server.py              # Start server on localhost:8000
  python run_server.py --ngrok      # Start with ngrok tunnel
  python run_server.py --port 8080  # Use different port
  python run_server.py --no-reload  # Disable auto-reload
        """
    )
    
    parser.add_argument(
        "--ngrok",
        action="store_true",
        help="Start ngrok tunnel for external access"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload on code changes"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check environment, don't start server"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "=" * 60)
    print("🦷 DENTAL AI VOICE AGENT")
    print("=" * 60)
    
    # Check environment
    env_ok = check_env()
    
    if args.check_only:
        if env_ok:
            print_twilio_instructions()
        return 0 if env_ok else 1
    
    if not env_ok:
        print("\n⚠️  Fix the environment issues above before starting.")
        print("   You can still start the server, but voice calls won't work.")
        response = input("\nContinue anyway? [y/N]: ")
        if response.lower() != "y":
            return 1
    
    # Start ngrok if requested
    if args.ngrok:
        ngrok_url = start_ngrok(args.port)
        if ngrok_url:
            update_env_urls(ngrok_url)
            # Reload env to pick up changes
            load_dotenv(override=True)
    
    # Print Twilio instructions
    print_twilio_instructions()
    
    # Start the server
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
