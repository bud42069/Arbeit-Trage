#!/usr/bin/env python3
"""Coinbase Advanced WebSocket Debug Test"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_coinbase_ws():
    """Test Coinbase Advanced WebSocket with full debugging."""
    
    ws_url = "wss://advanced-trade-ws.coinbase.com"
    
    print("\n" + "="*60)
    print("🔍 COINBASE WEBSOCKET DEBUG TEST")
    print("="*60 + "\n")
    
    try:
        # Step 1: Connect
        print(f"1️⃣ Connecting to: {ws_url}")
        ws = await websockets.connect(ws_url)
        print(f"✅ Connected! State: {ws.state.name}")
        print(f"   Local: {ws.local_address}")
        print(f"   Remote: {ws.remote_address}\n")
        
        # Step 2: Send subscription
        print("2️⃣ Sending subscription message...")
        
        # TRY FORMAT 1: New format (channels plural)
        subscribe_msg_v1 = {
            "type": "subscribe",
            "product_ids": ["BTC-USD"],
            "channels": ["level2"]  # Note: plural
        }
        
        print(f"   Message: {json.dumps(subscribe_msg_v1, indent=2)}")
        await ws.send(json.dumps(subscribe_msg_v1))
        print("   ✅ Message sent!\n")
        
        # Step 3: Listen for responses
        print("3️⃣ Listening for responses (30 seconds)...")
        print("-" * 60)
        
        message_count = 0
        start_time = datetime.now()
        
        async for message in ws:
            message_count += 1
            data = json.loads(message)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n📨 Message #{message_count} ({elapsed:.1f}s)")
            print(f"Type: {data.get('type', 'UNKNOWN')}")
            print(f"Channel: {data.get('channel', 'N/A')}")
            
            # Pretty print the message
            msg_preview = json.dumps(data, indent=2)
            if len(msg_preview) > 500:
                print(msg_preview[:500] + "...")
            else:
                print(msg_preview)
            
            # Check for errors
            if data.get('type') == 'error':
                print(f"\n❌ ERROR RECEIVED!")
                print(f"Message: {data.get('message')}")
                print(f"Reason: {data.get('reason')}")
                break
            
            # Check for subscriptions confirmation
            if data.get('type') == 'subscriptions':
                print(f"\n✅ SUBSCRIPTION CONFIRMED!")
                print(f"Channels: {data.get('channels')}")
            
            # Check for snapshot
            if data.get('type') == 'snapshot':
                print(f"\n📸 SNAPSHOT RECEIVED!")
                updates = data.get('updates', [])
                print(f"Updates: {len(updates)} levels")
            
            # Check for l2update
            if data.get('type') == 'l2update':
                product = data.get('product_id')
                updates = data.get('updates', [])
                print(f"📊 L2 UPDATE: {product} - {len(updates)} changes")
            
            # Stop after 10 messages or 30 seconds
            if message_count >= 10 or elapsed > 30:
                print(f"\n⏹️  Stopping (received {message_count} messages)")
                break
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETE")
        print("="*60 + "\n")
        
        await ws.close()
        
    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n❌ CONNECTION CLOSED UNEXPECTEDLY!")
        print(f"Code: {e.code}")
        print(f"Reason: {e.reason}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coinbase_ws())
