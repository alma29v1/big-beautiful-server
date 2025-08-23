#!/usr/bin/env python3
"""
Secure test script to verify Replit server connection
NO HARDCODED API KEYS - Uses environment variables
"""

import requests
import json
import os

def test_replit_connection():
    """Test connection to Replit server"""

    # Get API key from environment variable
    api_key = os.getenv('MOBILE_APP_API_KEY')
    if not api_key:
        print("❌ ERROR: MOBILE_APP_API_KEY environment variable not set!")
        print("💡 Set it with: export MOBILE_APP_API_KEY='your_api_key_here'")
        return

    # Replit server URL (replace with your actual URL)
    base_url = "https://big-beautiful-server.alma29v1.repl.co"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    print("🧪 Testing Replit Server Connection (SECURE)...")
    print(f"🌐 Server URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}... (from environment)")
    print("-" * 50)

    # Test 1: Health Check
    try:
        print("1️⃣ Testing Health Check...")
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check successful!")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   API Key Configured: {data.get('api_key_configured')}")
            print(f"   Google API Configured: {data.get('google_api_configured')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    print("-" * 50)

    # Test 2: Contacts (requires API key)
    try:
        print("2️⃣ Testing Contacts Endpoint...")
        response = requests.get(f"{base_url}/api/contacts", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Contacts endpoint successful!")
            data = response.json()
            print(f"   Total contacts: {data.get('total', 0)}")
        else:
            print(f"❌ Contacts endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Contacts endpoint error: {e}")

    print("-" * 50)

    # Test 3: Analytics
    try:
        print("3️⃣ Testing Analytics Endpoint...")
        response = requests.get(f"{base_url}/api/analytics", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Analytics endpoint successful!")
            data = response.json()
            print(f"   Total contacts: {data.get('total_contacts', 0)}")
            print(f"   Fiber contacts: {data.get('fiber_contacts', 0)}")
            print(f"   Recent contacts: {data.get('recent_contacts', 0)}")
        else:
            print(f"❌ Analytics endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Analytics endpoint error: {e}")

    print("-" * 50)

    # Test 4: Create a test contact
    try:
        print("4️⃣ Testing Contact Creation...")
        test_contact = {
            "address": "123 Test Street",
            "city": "Test City",
            "state": "NC",
            "zip_code": "28401",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "owner_phone": "910-555-0123",
            "fiber_available": True
        }

        response = requests.post(
            f"{base_url}/api/contacts",
            headers=headers,
            json=test_contact,
            timeout=10
        )

        if response.status_code == 201:
            print("✅ Contact creation successful!")
            data = response.json()
            print(f"   Created contact ID: {data.get('id')}")
            print(f"   Address: {data.get('address')}")
        else:
            print(f"❌ Contact creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Contact creation error: {e}")

    print("-" * 50)
    print("🏁 Testing complete!")

if __name__ == "__main__":
    test_replit_connection()
