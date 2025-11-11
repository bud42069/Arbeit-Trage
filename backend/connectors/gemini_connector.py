"""Gemini Exchange connector with WS L2 + REST IOC orders."""
import asyncio
import json
import hmac
import hashlib
import base64
import time
import logging
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime
import httpx
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from config import settings
from shared.types import BookUpdate, Side, OrderStatus
from shared.events import event_bus

logger = logging.getLogger(__name__)


class GeminiAuthenticator:
    """Handles HMAC-SHA384 authentication for Gemini API."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
    
    def generate_signature(self, payload: Dict) -> tuple[str, str, str]:
        """Generate authentication headers."""
        nonce = str(int(time.time() * 1000))
        payload["nonce"] = nonce
        
        payload_json = json.dumps(payload).encode('utf-8')
        payload_b64 = base64.b64encode(payload_json).decode('utf-8')
        
        signature = hmac.new(
            self.api_secret,
            payload_b64.encode('utf-8'),
            hashlib.sha384
        ).hexdigest()
        
        return payload_b64, signature, nonce


class GeminiConnector:
    """Gemini exchange connector."""
    
    def __init__(self):
        self.base_url = settings.gemini_base_url
        self.ws_public_url = settings.gemini_ws_public_url
        self.ws_private_url = settings.gemini_ws_private_url
        self.auth = GeminiAuthenticator(
            settings.gemini_api_key,
            settings.gemini_api_secret
        )
        self.order_books: Dict[str, Dict] = {}
        self.connected = False
        self.last_update_ts: Dict[str, datetime] = {}
    
    async def connect_public_ws(self, symbols: List[str]):
        """Connect to public WS for L2 orderbook."""
        while True:
            try:
                async with connect(self.ws_public_url) as ws:
                    logger.info(f"Connected to Gemini public WS")
                    self.connected = True
                    
                    # Subscribe to L2 for all symbols
                    for symbol in symbols:
                        subscribe_msg = {
                            "type": "subscribe",
                            "subscriptions": [
                                {"name": "l2", "symbols": [symbol]}
                            ]
                        }
                        await ws.send(json.dumps(subscribe_msg))
                        logger.info(f"Subscribed to L2: {symbol}")
                    
                    # Listen for updates
                    async for message in ws:
                        data = json.loads(message)
                        await self._handle_public_message(data)
                        
            except ConnectionClosed:
                logger.warning("Gemini public WS closed, reconnecting...")
                self.connected = False
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Gemini public WS error: {e}")
                self.connected = False
                await asyncio.sleep(5)
    
    async def _handle_public_message(self, data: Dict):
        """Handle public WS message."""
        msg_type = data.get("type")
        
        if msg_type == "l2_updates":
            symbol = data.get("symbol")
            changes = data.get("changes", [])
            
            # Initialize order book if not exists
            if symbol not in self.order_books:
                self.order_books[symbol] = {"bids": {}, "asks": {}}
            
            book = self.order_books[symbol]
            
            # Apply changes
            for change in changes:
                side_str, price_str, size_str = change
                price = Decimal(price_str)
                size = Decimal(size_str)
                
                side_book = book["bids"] if side_str == "buy" else book["asks"]
                
                if size == 0:
                    side_book.pop(price, None)
                else:
                    side_book[price] = size
            
            # Update timestamp
            self.last_update_ts[symbol] = datetime.utcnow()
            
            # Emit book update event
            bids = [[str(p), str(s)] for p, s in sorted(book["bids"].items(), reverse=True)[:10]]
            asks = [[str(p), str(s)] for p, s in sorted(book["asks"].items())[:10]]
            
            book_update = BookUpdate(
                venue="gemini",
                pair=symbol,
                timestamp=datetime.utcnow(),
                bids=bids,
                asks=asks,
                sequence=0
            )
            
            await event_bus.publish("cex.bookUpdate", book_update)
    
    def get_best_bid_ask(self, symbol: str) -> Optional[tuple[Decimal, Decimal]]:
        """Get best bid/ask for symbol."""
        book = self.order_books.get(symbol)
        if not book or not book["bids"] or not book["asks"]:
            return None
        
        best_bid = max(book["bids"].keys())
        best_ask = min(book["asks"].keys())
        
        return best_bid, best_ask
    
    def check_staleness(self, symbol: str, max_age_sec: float = 10.0) -> bool:
        """Check if order book is stale."""
        last_update = self.last_update_ts.get(symbol)
        if not last_update:
            return True
        
        age = (datetime.utcnow() - last_update).total_seconds()
        return age > max_age_sec
    
    async def place_ioc_order(
        self,
        symbol: str,
        side: Side,
        quantity: Decimal,
        price: Decimal,
        client_order_id: Optional[str] = None
    ) -> Dict:
        """Place immediate-or-cancel order."""
        payload = {
            "request": "/v1/order/new",
            "symbol": symbol,
            "amount": str(quantity),
            "price": str(price),
            "side": side.value,
            "type": "exchange limit",
            "options": ["immediate-or-cancel"]
        }
        
        if client_order_id:
            payload["client_order_id"] = client_order_id
        
        payload_b64, signature, nonce = self.auth.generate_signature(payload)
        
        headers = {
            "Content-Type": "text/plain",
            "X-GEMINI-APIKEY": self.auth.api_key,
            "X-GEMINI-PAYLOAD": payload_b64,
            "X-GEMINI-SIGNATURE": signature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/order/new",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Gemini order failed: {response.text}")
                raise Exception(f"Order placement failed: {response.status_code}")
            
            return response.json()
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status."""
        payload = {
            "request": "/v1/order/status",
            "order_id": order_id
        }
        
        payload_b64, signature, nonce = self.auth.generate_signature(payload)
        
        headers = {
            "Content-Type": "text/plain",
            "X-GEMINI-APIKEY": self.auth.api_key,
            "X-GEMINI-PAYLOAD": payload_b64,
            "X-GEMINI-SIGNATURE": signature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/order/status",
                headers=headers
            )
            
            return response.json()


# Global instance
gemini_connector = GeminiConnector()
