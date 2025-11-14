"""
Coinbase Advanced Trade connector with CDP JWT authentication.
Supports WebSocket L2 orderbook + REST IOC orders for arbitrage.
"""
import asyncio
import time
import json
import hmac
import hashlib
from decimal import Decimal
from typing import Dict, Optional, List
from datetime import datetime, timezone
import logging

import httpx
import websockets
import jwt
from cryptography.hazmat.primitives import serialization

from shared.types import Side, BookUpdate
from shared.events import event_bus

logger = logging.getLogger(__name__)


class CoinbaseAuthenticator:
    """
    CDP JWT authentication for Coinbase Advanced Trade API.
    Uses EC private key (ES256) to sign requests.
    """
    
    def __init__(self, key_name: str, private_key_pem: str):
        self.key_name = key_name
        # Parse the PEM private key (handle escaped newlines from .env)
        private_key_cleaned = private_key_pem.replace('\\n', '\n')
        self.private_key = serialization.load_pem_private_key(
            private_key_cleaned.encode(),
            password=None
        )
    
    def build_jwt(self, service: str = "retail_rest_api_proxy", for_websocket: bool = False) -> str:
        """Build JWT token for API authentication."""
        now = int(time.time())
        
        if for_websocket:
            # WebSocket JWT - simpler payload (no aud, no uri)
            payload = {
                "sub": self.key_name,
                "iss": "coinbase-cloud",
                "iat": now,
                "exp": now + 120,  # 2 minute expiration
            }
        else:
            # REST API JWT - full payload
            uri = f"/{service}"
            payload = {
                "sub": self.key_name,
                "iss": "coinbase-cloud",
                "nbf": now,
                "exp": now + 120,
                "aud": [service],
                "uri": uri,
            }
        
        token = jwt.encode(payload, self.private_key, algorithm="ES256")
        return token
    
    def get_headers(self) -> Dict[str, str]:
        """Generate authenticated headers for REST API."""
        token = self.build_jwt()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


class CoinbaseConnector:
    """
    Coinbase Advanced Trade connector.
    
    Features:
    - WebSocket L2 orderbook subscription
    - REST API for order placement (IOC-style limit orders)
    - CDP JWT authentication
    """
    
    def __init__(
        self,
        key_name: str,
        private_key: str,
        base_url: str = "https://api.coinbase.com",
        ws_url: str = "wss://advanced-trade-ws.coinbase.com",
    ):
        self.authenticator = CoinbaseAuthenticator(key_name, private_key)
        self.base_url = base_url
        self.ws_url = ws_url
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Order book storage: product_id -> {bids: [], asks: []}
        self.books: Dict[str, Dict] = {}
        self.last_update: Dict[str, datetime] = {}
        
        self.ws = None
        self.ws_task = None
        self.subscribed_products: List[str] = []
        
        logger.info(f"CoinbaseConnector initialized: {base_url}")
    
    async def connect_public_ws(self):
        """Connect to Coinbase Advanced Trade WebSocket (public market data)."""
        try:
            # Increase max_size to handle large orderbook snapshots (10MB limit)
            self.ws = await websockets.connect(
                self.ws_url,
                max_size=10 * 1024 * 1024  # 10MB (Coinbase can send 1MB+ snapshots)
            )
            logger.info(f"Connected to Coinbase WS: {self.ws_url}")
            
            # Start message handler
            self.ws_task = asyncio.create_task(self._handle_ws_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect to Coinbase WS: {e}")
            raise
    
    async def subscribe_orderbook(self, product_id: str):
        """Subscribe to L2 orderbook for a product."""
        if not self.ws:
            await self.connect_public_ws()
        
        # ✅ CRITICAL FIX: Level2 is PUBLIC data - NO JWT needed!
        # Only user-specific channels need JWT on wss://advanced-trade-ws-user.coinbase.com
        # Market data endpoint (wss://advanced-trade-ws.coinbase.com) is public
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": [product_id],
            "channel": "level2"  # Singular "channel" for public endpoint
        }
        
        logger.info(f"Sending PUBLIC subscription for {product_id} (no auth required)")
        logger.debug(f"Subscription message: {json.dumps(subscribe_msg, indent=2)}")
        await self.ws.send(json.dumps(subscribe_msg))
        self.subscribed_products.append(product_id)
        self.books[product_id] = {"bids": [], "asks": []}
        
        logger.info(f"✅ Subscribed to {product_id} L2 orderbook")
    
    async def _handle_ws_messages(self):
        """Process incoming WebSocket messages."""
        try:
            logger.info("Coinbase WS: Starting message handler")
            message_count = 0
            
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    # Log first 5 messages for debugging
                    if message_count <= 5:
                        logger.info(f"Coinbase WS received: {json.dumps(data)[:200]}")
                    
                    # NEW FORMAT: Messages have channel and events array
                    channel = data.get("channel")
                    
                    if channel == "l2_data":
                        # Process l2_data events
                        events = data.get("events", [])
                        for event in events:
                            event_type = event.get("type")
                            
                            if event_type == "snapshot":
                                await self._handle_l2_snapshot(event)
                            elif event_type == "update":
                                await self._handle_l2_update(event)
                    
                    elif channel == "subscriptions":
                        logger.info(f"✅ Coinbase subscription confirmed: {data}")
                    
                    elif channel == "heartbeats":
                        # Heartbeat - silent
                        pass
                    
                    # Log every 100 messages
                    if message_count % 100 == 0:
                        logger.info(f"📊 Processed {message_count} Coinbase messages")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Coinbase WS JSON decode error: {e}, message: {message[:200]}")
                except Exception as e:
                    logger.error(f"Coinbase WS message handling error: {e}", exc_info=True)
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Coinbase WS connection closed: code={e.code}, reason={e.reason}")
        except Exception as e:
            logger.error(f"Coinbase WS error: {e}", exc_info=True)
    
    async def _handle_l2_snapshot(self, event: dict):
        """Handle initial L2 orderbook snapshot."""
        product_id = event.get("product_id")
        if not product_id:
            return
        
        # NEW FORMAT: updates array with side, price_level, new_quantity
        updates = event.get("updates", [])
        
        bids = []
        asks = []
        
        for update in updates:
            side = update.get("side")
            price = float(update.get("price_level", 0))
            size = float(update.get("new_quantity", 0))
            
            if side == "bid":
                bids.append((price, size))
            elif side == "offer":
                asks.append((price, size))
        
        # Store top 20 levels (sorted)
        self.books[product_id] = {
            "bids": sorted(bids, key=lambda x: x[0], reverse=True)[:20],
            "asks": sorted(asks, key=lambda x: x[0])[:20]
        }
        
        self.last_update[product_id] = datetime.now(timezone.utc)
        
        logger.info(f"📸 Coinbase {product_id} snapshot: {len(bids)} bids, {len(asks)} asks")
        
        # Emit initial book event
        if self.books[product_id]["bids"] and self.books[product_id]["asks"]:
            await self._emit_book_update(product_id)
    
    async def _handle_l2_update(self, event: dict):
        """Handle L2 orderbook updates."""
        product_id = event.get("product_id")
        if not product_id or product_id not in self.books:
            return
        
        updates = event.get("updates", [])
        book = self.books[product_id]
        
        for update in updates:
            side = update.get("side")
            price = float(update.get("price_level", 0))
            size = float(update.get("new_quantity", 0))
            
            if side == "bid":
                # Update bids
                bids_dict = {p: s for p, s in book["bids"]}
                if size == 0:
                    bids_dict.pop(price, None)
                else:
                    bids_dict[price] = size
                book["bids"] = sorted(bids_dict.items(), key=lambda x: x[0], reverse=True)[:20]
                
            elif side == "offer":
                # Update asks
                asks_dict = {p: s for p, s in book["asks"]}
                if size == 0:
                    asks_dict.pop(price, None)
                else:
                    asks_dict[price] = size
                book["asks"] = sorted(asks_dict.items(), key=lambda x: x[0])[:20]
        
        self.last_update[product_id] = datetime.now(timezone.utc)
        
        # Emit book update (only if we have both bids and asks)
        if book["bids"] and book["asks"]:
            await self._emit_book_update(product_id)
    
    def get_best_bid_ask(self, product_id: str) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Get best bid/ask with sizes."""
    
    async def _emit_book_update(self, product_id: str):
        """Emit book update event."""
        book = self.books[product_id]
        book_update = BookUpdate(
            venue="coinbase",
            pair=product_id,
            timestamp=self.last_update[product_id],
            bids=book["bids"],
            asks=book["asks"],
            sequence=None
        )
        await event_bus.publish("cex.bookUpdate", book_update)

        book = self.books.get(product_id, {})
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        
        if not bids or not asks:
            return None, None, None, None
        
        best_bid, bid_size = bids[0]
        best_ask, ask_size = asks[0]
        
        return best_bid, bid_size, best_ask, ask_size
    
    def check_staleness(self, product_id: str) -> float:
        """Check staleness in seconds since last update."""
        last = self.last_update.get(product_id)
        if not last:
            return 999.0
        return (datetime.now(timezone.utc) - last).total_seconds()
    
    async def place_ioc_order(
        self,
        product_id: str,
        side: Side,
        size: Decimal,
        limit_price: Optional[Decimal] = None
    ) -> dict:
        """
        Place IOC-style limit order on Coinbase Advanced Trade.
        
        Coinbase doesn't have pure IOC, but we use limit with short time_in_force.
        """
        client_order_id = f"arb-{int(time.time() * 1000)}"
        
        order_config = {
            "limit_limit_gtc": {
                "base_size": str(size),
                "limit_price": str(limit_price) if limit_price else None,
                "post_only": False
            }
        }
        
        body = {
            "client_order_id": client_order_id,
            "product_id": product_id,
            "side": side.value.upper(),  # "BUY" or "SELL"
            "order_configuration": order_config
        }
        
        headers = self.authenticator.get_headers()
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v3/brokerage/orders",
                json=body,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Coinbase order placed: {client_order_id} {side} {size} {product_id}")
            return {
                "client_order_id": client_order_id,
                "order_id": result.get("order_id"),
                "status": result.get("status"),
                "response": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Coinbase order failed: {e.response.text}")
            return {
                "client_order_id": client_order_id,
                "error": e.response.text
            }
        except Exception as e:
            logger.error(f"Coinbase order exception: {e}")
            return {
                "client_order_id": client_order_id,
                "error": str(e)
            }
    
    async def get_order_status(self, order_id: str) -> dict:
        """Get order status from Coinbase."""
        headers = self.authenticator.get_headers()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/api/v3/brokerage/orders/historical/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Coinbase order status: {e}")
            return {}
    
    async def get_balances(self) -> dict:
        """Get account balances from Coinbase."""
        headers = self.authenticator.get_headers()
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/api/v3/brokerage/accounts",
                headers=headers
            )
            response.raise_for_status()
            accounts = response.json().get("accounts", [])
            
            balances = {}
            for account in accounts:
                currency = account.get("currency")
                available = account.get("available_balance", {}).get("value", "0")
                balances[currency] = float(available)
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get Coinbase balances: {e}")
            return {}
    
    async def close(self):
        """Close connections."""
        if self.ws_task:
            self.ws_task.cancel()
        if self.ws:
            await self.ws.close()
        await self.http_client.aclose()
        logger.info("Coinbase connector closed")


# Global instance (initialized conditionally based on settings)
coinbase_connector = None

def init_coinbase_connector():
    """Initialize Coinbase connector if enabled. Returns connector instance or None."""
    from config import settings
    
    if settings.coinbase_adv_enabled and settings.coinbase_key_name and settings.coinbase_private_key:
        connector = CoinbaseConnector(
            key_name=settings.coinbase_key_name,
            private_key=settings.coinbase_private_key,
            base_url=settings.coinbase_adv_base_url,
            ws_url=settings.coinbase_adv_ws_url
        )
        logger.info("Coinbase connector initialized")
        return connector
    else:
        logger.info("Coinbase connector disabled")
        return None
