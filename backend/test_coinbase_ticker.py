#!/usr/bin/env python3
"""Test Coinbase Ticker Channel (Simpler, Public)"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_ticker():
    """Test with ticker channel (simpler than level2)."""
    
    ws_url = "wss://advanced-trade-ws.coinbase.com"
    
    print("\n🔍 Testing TICKER channel (public, no auth)...\n")
    
    try:
        ws = await websockets.connect(ws_url)
        print("✅ Connected!")
        
        # Ticker channel is simpler and more reliable
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD"],
            "channels": ["ticker"]  # Simpler than level2
        }
        
        print(f"📤 Sending: {subscribe_msg}\n")
        await ws.send(json.dumps(subscribe_msg))
        
        # Listen for 30 seconds
        message_count = 0
        start_time = datetime.now()
        
        async for message in ws:
            data = json.loads(message)
            message_count += 1
            
            if data.get('type') == 'ticker':
                product = data.get('product_id')
                price = data.get('price')
                print(f"📊 {product}: ${price}")
            
            elif data.get('type') == 'subscriptions':
                print(f"✅ Subscriptions confirmed: {data.get('channels')}\n")
            
            elif data.get('type') == 'error':
                print(f"❌ ERROR: {data}")
                break
            
            # Stop after 30 seconds or 20 messages
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > 30 or message_count > 20:
                print(f"\n⏹️  Stopping after {message_count} messages")
                break
        
        await ws.close()
        print("\n✅ Test complete!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ticker())
