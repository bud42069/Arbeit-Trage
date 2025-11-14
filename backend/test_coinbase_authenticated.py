#!/usr/bin/env python3
"""
Test Coinbase Connector with Authentication
Uses actual API keys from .env to verify the fix works
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, '/app/backend')

from connectors.coinbase_connector import CoinbaseConnector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_authenticated_connection():
    """Test Coinbase connector with real authentication."""
    
    # Load environment variables
    load_dotenv('/app/backend/.env')
    
    key_name = os.getenv('COINBASE_KEY_NAME')
    private_key = os.getenv('COINBASE_PRIVATE_KEY')
    
    if not key_name or not private_key:
        print("\n❌ ERROR: COINBASE_KEY_NAME or COINBASE_PRIVATE_KEY not found in .env")
        print("Please configure these in /app/backend/.env")
        return
    
    print("\n" + "="*70)
    print("🔐 COINBASE AUTHENTICATED WEBSOCKET TEST")
    print("="*70)
    print(f"\nKey Name: {key_name[:50]}...")
    print(f"Private Key: {'*' * 20} (loaded from .env)\n")
    
    try:
        # Initialize connector
        print("1️⃣ Initializing Coinbase connector...")
        connector = CoinbaseConnector(
            key_name=key_name,
            private_key=private_key
        )
        print("✅ Connector initialized\n")
        
        # Connect to WebSocket
        print("2️⃣ Connecting to WebSocket...")
        asyncio.create_task(connector.connect_public_ws())
        await asyncio.sleep(2)
        
        if not connector.ws:
            print("❌ WebSocket connection failed")
            return
        
        print("✅ WebSocket connected\n")
        
        # Subscribe to orderbooks
        print("3️⃣ Subscribing to orderbooks...")
        products = ["SOL-USD", "BTC-USD", "BONK-USD"]
        
        for product in products:
            print(f"   Subscribing to {product}...")
            await connector.subscribe_orderbook(product)
            await asyncio.sleep(0.5)
        
        print("✅ Subscriptions sent\n")
        
        # Monitor for 30 seconds
        print("4️⃣ Monitoring orderbook updates for 30 seconds...")
        print("-" * 70)
        
        start_time = datetime.now()
        last_check = start_time
        
        for i in range(30):
            await asyncio.sleep(1)
            
            # Check every 3 seconds
            if (datetime.now() - last_check).total_seconds() >= 3:
                last_check = datetime.now()
                
                print(f"\n[{i}s elapsed]")
                
                for product in products:
                    book = connector.books.get(product, {})
                    bids = book.get("bids", [])
                    asks = book.get("asks", [])
                    
                    if bids and asks:
                        best_bid = bids[0][0]
                        best_ask = asks[0][0]
                        spread = ((best_ask - best_bid) / best_bid) * 100
                        staleness = connector.check_staleness(product)
                        
                        print(f"  {product:10s} | Bid: ${best_bid:>10.2f} | Ask: ${best_ask:>10.2f} | "
                              f"Spread: {spread:.3f}% | Age: {staleness:.1f}s")
                    else:
                        print(f"  {product:10s} | ⏳ Waiting for data...")
        
        print("\n" + "-" * 70)
        print("\n5️⃣ Final Results:")
        print("-" * 70)
        
        success_count = 0
        for product in products:
            book = connector.books.get(product, {})
            bids = book.get("bids", [])
            asks = book.get("asks", [])
            
            if bids and asks:
                print(f"✅ {product}: {len(bids)} bids, {len(asks)} asks (SUCCESS)")
                success_count += 1
            else:
                print(f"❌ {product}: No data received (FAILED)")
        
        print("\n" + "="*70)
        
        if success_count == len(products):
            print("🎉 ALL TESTS PASSED! Coinbase connector is working!")
        elif success_count > 0:
            print(f"⚠️  PARTIAL SUCCESS: {success_count}/{len(products)} products working")
        else:
            print("❌ ALL TESTS FAILED - Check authentication and API permissions")
        
        print("="*70 + "\n")
        
        # Close connection
        await connector.close()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_authenticated_connection())
