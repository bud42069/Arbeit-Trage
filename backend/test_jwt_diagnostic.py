#!/usr/bin/env python3
"""
Coinbase JWT Diagnostic Tool
Helps debug authentication issues by showing JWT contents and testing different formats
"""

import os
import sys
import time
import json
import jwt as pyjwt
from datetime import datetime
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

sys.path.insert(0, '/app/backend')

def main():
    # Load environment
    load_dotenv('/app/backend/.env')
    
    key_name = os.getenv('COINBASE_KEY_NAME')
    private_key_pem = os.getenv('COINBASE_PRIVATE_KEY')
    
    print("\n" + "="*70)
    print("🔍 COINBASE JWT DIAGNOSTIC TOOL")
    print("="*70)
    
    if not key_name or not private_key_pem:
        print("\n❌ ERROR: API keys not found in .env")
        return
    
    print(f"\n1️⃣ API Key Configuration:")
    print(f"   Key Name: {key_name}")
    print(f"   Key Length: {len(private_key_pem)} characters")
    
    # Parse private key
    try:
        private_key_cleaned = private_key_pem.replace('\\n', '\n')
        private_key = serialization.load_pem_private_key(
            private_key_cleaned.encode(),
            password=None
        )
        print(f"   ✅ Private key parsed successfully")
    except Exception as e:
        print(f"   ❌ Private key parsing failed: {e}")
        return
    
    # Generate different JWT formats
    now = int(time.time())
    
    print(f"\n2️⃣ Testing JWT Formats:\n")
    
    # Format 1: WebSocket JWT (current implementation)
    print("   Format 1: WebSocket JWT (Simplified)")
    payload_ws = {
        "sub": key_name,
        "iss": "coinbase-cloud",
        "iat": now,
        "exp": now + 120,
    }
    token_ws = pyjwt.encode(payload_ws, private_key, algorithm="ES256")
    print(f"   Payload: {json.dumps(payload_ws, indent=6)}")
    print(f"   Token: {token_ws[:50]}...{token_ws[-20:]}")
    
    # Decode to verify
    try:
        decoded = pyjwt.decode(token_ws, options={"verify_signature": False})
        print(f"   ✅ Token decodes successfully")
        print(f"   Decoded: {json.dumps(decoded, indent=6)}")
    except Exception as e:
        print(f"   ❌ Token decode failed: {e}")
    
    print("\n" + "-"*70)
    
    # Format 2: REST API JWT (full payload)
    print("\n   Format 2: REST API JWT (Full payload)")
    payload_rest = {
        "sub": key_name,
        "iss": "coinbase-cloud",
        "nbf": now,
        "exp": now + 120,
        "aud": ["retail_rest_api_proxy"],
        "uri": "/retail_rest_api_proxy",
    }
    token_rest = pyjwt.encode(payload_rest, private_key, algorithm="ES256")
    print(f"   Payload: {json.dumps(payload_rest, indent=6)}")
    print(f"   Token: {token_rest[:50]}...{token_rest[-20:]}")
    
    print("\n" + "-"*70)
    
    # Format 3: Alternative WebSocket JWT (with nbf)
    print("\n   Format 3: Alternative WebSocket JWT (with nbf)")
    payload_alt = {
        "sub": key_name,
        "iss": "coinbase-cloud",
        "nbf": now,
        "iat": now,
        "exp": now + 120,
    }
    token_alt = pyjwt.encode(payload_alt, private_key, algorithm="ES256")
    print(f"   Payload: {json.dumps(payload_alt, indent=6)}")
    print(f"   Token: {token_alt[:50]}...{token_alt[-20:]}")
    
    print("\n" + "="*70)
    print("\n3️⃣ Diagnosis:\n")
    
    # Check key name format
    if key_name.startswith("organizations/"):
        print("   ✅ Key name format looks correct (CDP format)")
    else:
        print("   ⚠️  Key name format may be incorrect")
        print("      Expected: organizations/{org-id}/apiKeys/{key-id}")
    
    # Check if this might be wrong product
    print("\n   🔍 Common Issue: Wrong API Product")
    print("      - Coinbase has TWO different products:")
    print("        1. 'Trade API' (on-chain Ethereum/Base)")
    print("        2. 'Advanced Trade API' (CEX spot trading)")
    print("      - Your keys must be from 'Advanced Trade API'")
    print("      - Get keys from: https://portal.cdp.coinbase.com/")
    print("      - Make sure 'View' permission is enabled for market data")
    
    print("\n   📋 Next Steps:")
    print("      1. Verify your keys are from 'Advanced Trade API' (not 'Trade API')")
    print("      2. Check permissions include 'View' for market data")
    print("      3. Try generating a new API key set if issue persists")
    print("      4. Test with Coinbase's official SDK for comparison")
    
    print("\n" + "="*70 + "\n")
    
    # Save tokens for manual testing
    with open('/app/backend/jwt_test_tokens.txt', 'w') as f:
        f.write("WebSocket JWT (Format 1):\n")
        f.write(token_ws + "\n\n")
        f.write("REST API JWT (Format 2):\n")
        f.write(token_rest + "\n\n")
        f.write("Alternative JWT (Format 3):\n")
        f.write(token_alt + "\n")
    
    print("   📝 JWT tokens saved to: /app/backend/jwt_test_tokens.txt")
    print("      You can manually test these with curl or Postman\n")

if __name__ == "__main__":
    main()
