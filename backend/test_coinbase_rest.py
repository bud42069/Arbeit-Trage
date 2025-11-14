#!/usr/bin/env python3
"""Test Coinbase REST API Authentication"""

import os
import sys
import time
import httpx
import jwt as pyjwt
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

sys.path.insert(0, '/app/backend')

def test_rest_api():
    """Test Coinbase REST API to verify keys work."""
    
    load_dotenv('/app/backend/.env')
    
    key_name = os.getenv('COINBASE_KEY_NAME')
    private_key_pem = os.getenv('COINBASE_PRIVATE_KEY')
    
    print("\n" + "="*70)
    print("🔍 COINBASE REST API AUTHENTICATION TEST")
    print("="*70 + "\n")
    
    # Parse private key
    private_key_cleaned = private_key_pem.replace('\\n', '\n')
    private_key = serialization.load_pem_private_key(
        private_key_cleaned.encode(),
        password=None
    )
    
    # Build JWT for REST API
    now = int(time.time())
    service = "retail_rest_api_proxy"
    
    payload = {
        "sub": key_name,
        "iss": "coinbase-cloud",
        "nbf": now,
        "exp": now + 120,
        "aud": [service],
        "uri": f"/{service}",
    }
    
    token = pyjwt.encode(payload, private_key, algorithm="ES256")
    
    print(f"1️⃣ API Key: {key_name[:50]}...")
    print(f"2️⃣ JWT Generated: {token[:30]}...{token[-20:]}")
    print(f"3️⃣ Testing REST endpoints...\n")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test different endpoints
    tests = [
        ("GET Time (Public)", "GET", "https://api.coinbase.com/api/v3/brokerage/time"),
        ("GET Products (Public)", "GET", "https://api.coinbase.com/api/v3/brokerage/products"),
        ("GET Accounts (Private)", "GET", "https://api.coinbase.com/api/v3/brokerage/accounts"),
    ]
    
    client = httpx.Client(timeout=10.0)
    
    for name, method, url in tests:
        try:
            print(f"Testing: {name}")
            print(f"  URL: {url}")
            
            if method == "GET":
                response = client.get(url, headers=headers)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS")
                data = response.json()
                print(f"  Response preview: {str(data)[:100]}...")
            elif response.status_code == 401:
                print(f"  ❌ AUTHENTICATION FAILED")
                print(f"  Response: {response.text[:200]}")
            else:
                print(f"  ⚠️  Unexpected status")
                print(f"  Response: {response.text[:200]}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}\n")
    
    client.close()
    
    print("="*70)
    print("\n📋 Diagnosis:")
    print("- If 'GET Time' fails with 401: Keys are invalid or revoked")
    print("- If 'GET Time' succeeds but 'GET Products' fails: Wrong API product")
    print("- If both succeed but WebSocket fails: WebSocket-specific permission issue")
    print("- If 'GET Accounts' fails with 401: Missing 'View' permission")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_rest_api()
