#!/usr/bin/env python3
"""Quick test script for the dental agent API."""
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8080"

def test_api():
    print("=" * 50)
    print("Testing Dental Agent API")
    print("=" * 50)
    
    # Test 1: Health check (root endpoint)
    print("\n1. Testing root endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   Make sure the server is running!")
        sys.exit(1)
    
    # Test 2: Post a lead batch
    print("\n2. Posting test lead batch...")
    try:
        payload = {
            "leads": [
                {"name": "John Doe", "phone": "+15551234567"},
                {"name": "Jane Smith", "phone": "+15559876543"}
            ]
        }
        r = requests.post(f"{BASE_URL}/api/clients/1/uploads", json=payload, timeout=5)
        print(f"   Status: {r.status_code}")
        result = r.json()
        print(f"   Response: {result}")
        batch_id = result.get("batch_id")
    except Exception as e:
        print(f"   ERROR: {e}")
        sys.exit(1)
    
    # Test 3: Get calls for the batch
    if batch_id:
        print(f"\n3. Getting calls for batch {batch_id}...")
        try:
            r = requests.get(f"{BASE_URL}/api/clients/1/batches/{batch_id}/calls", timeout=5)
            print(f"   Status: {r.status_code}")
            calls = r.json()
            print(f"   Found {len(calls)} calls:")
            for call in calls:
                print(f"      - Call {call['id']}: {call['lead_name']} ({call['lead_phone']}) - Status: {call['status']}")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("API Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_api()
