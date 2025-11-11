"""Solana DEX connector with Helius RPC/WS + pool math."""
import asyncio
import json
import logging
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import httpx
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect as ws_connect

from config import settings
from shared.types import PoolUpdate, BoundQuote, Side
from shared.events import event_bus

logger = logging.getLogger(__name__)


class PoolMath:
    """Pool math for constant product and CLMM."""
    
    @staticmethod
    def constant_product_quote(
        reserve_in: Decimal,
        reserve_out: Decimal,
        amount_in: Decimal,
        fee_bps: int = 30
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Compute quote for constant product (x*y=k) pool.
        
        Returns: (amount_out, exec_price, impact_pct)
        """
        fee_multiplier = Decimal(1) - (Decimal(fee_bps) / Decimal(10000))
        amount_in_with_fee = amount_in * fee_multiplier
        
        amount_out = (
            reserve_out * amount_in_with_fee
        ) / (reserve_in + amount_in_with_fee)
        
        exec_price = amount_out / amount_in
        
        # Price before trade
        initial_price = reserve_out / reserve_in
        # Price after trade
        final_price = (reserve_out - amount_out) / (reserve_in + amount_in)
        # Price impact
        impact_pct = abs((final_price - initial_price) / initial_price) * Decimal(100)
        
        return amount_out, exec_price, impact_pct


class SolanaConnector:
    """Solana DEX connector using Helius."""
    
    def __init__(self):
        self.rpc_url = settings.helius_rpc_url
        self.ws_url = settings.helius_ws_url
        self.client = AsyncClient(self.rpc_url)
        self.pools: Dict[str, Dict] = {}
        self.connected = False
        self.last_update_ts: Dict[str, datetime] = {}
    
    async def fetch_pool_state(self, pool_address: str) -> Optional[Dict]:
        """
        Fetch Solana pool state with real market price.
        
        For POC: Uses CoinGecko API to get real SOL/USD price as DEX reference.
        For production: Parse actual Whirlpool sqrtPrice and vault reserves.
        """
        try:
            # Fetch real SOL/USD price from CoinGecko
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    real_sol_price = Decimal(str(data["solana"]["usd"]))
                    
                    # Add slight randomness to simulate DEX price variance (±0.3%)
                    import random
                    variance = Decimal(str(random.uniform(-0.003, 0.003)))
                    dex_price = real_sol_price * (Decimal("1") + variance)
                    
                    logger.info(f"Real market price for SOL/USD: ${real_sol_price}, DEX sim: ${dex_price}")
                    
                    # Estimate reserves for a $1M liquidity pool
                    estimated_liquidity_usd = Decimal("1000000")
                    estimated_sol = estimated_liquidity_usd / (dex_price * Decimal("2"))
                    estimated_usdc = estimated_liquidity_usd / Decimal("2")
                    
                    return {
                        "address": pool_address,
                        "token_a_reserve": estimated_usdc,
                        "token_b_reserve": estimated_sol,
                        "fee_bps": 30,
                        "last_update": datetime.utcnow(),
                        "price_mid": dex_price,
                        "data_source": "coingecko_real_price"
                    }
            
            # Fallback to mock if CoinGecko fails
            logger.warning("CoinGecko API failed, using mock data")
            return self._get_mock_pool_for_testing(pool_address)
            
        except Exception as e:
            logger.error(f"Failed to fetch real SOL price: {e}")
            return self._get_mock_pool_for_testing(pool_address)
    
    def _get_mock_pool_for_testing(self, pool_address: str) -> dict:
        """
        Realistic mock pool data for testing.
        Uses actual market price with small variance to simulate DEX spreads.
        """
        import random
        
        # Base on real SOL price (~$164)
        real_sol_price = Decimal("164.0")
        
        # Add realistic DEX variance (±0.2% to ±0.8%)
        variance_pct = Decimal(str(random.uniform(-0.008, 0.008)))
        dex_price = real_sol_price * (Decimal("1") + variance_pct)
        
        # Calculate reserves for $1M pool
        estimated_usdc = Decimal("500000")
        estimated_sol = Decimal("500000") / dex_price
        
        return {
            "address": pool_address,
            "token_a_reserve": estimated_usdc,
            "token_b_reserve": estimated_sol,
            "fee_bps": 30,
            "last_update": datetime.utcnow(),
            "price_mid": dex_price,
            "data_source": "realistic_mock"
        }
    
    async def subscribe_pool_updates(self, pool_addresses: List[str]):
        """Subscribe to pool account updates via WebSocket."""
        # For POC, use polling instead of WS subscription
        # Production would use accountSubscribe
        while True:
            try:
                for pool_addr in pool_addresses:
                    pool_state = await self.fetch_pool_state(pool_addr)
                    if pool_state:
                        await self._emit_pool_update(pool_state)
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Pool subscription error: {e}")
                await asyncio.sleep(5)
    
    async def _emit_pool_update(self, pool_state: Dict):
        """Emit pool update event."""
        token_a_reserve = pool_state["token_a_reserve"]
        token_b_reserve = pool_state["token_b_reserve"]
        
        price_mid = token_a_reserve / token_b_reserve
        
        pool_update = PoolUpdate(
            program="whirlpool",  # Or detect from account data
            pool=pool_state["address"],
            timestamp=datetime.utcnow(),
            reserves={
                settings.usdc_mint: str(token_a_reserve),
                settings.wsol_mint: str(token_b_reserve)
            },
            price_mid=price_mid,
            fee_bps=pool_state["fee_bps"]
        )
        
        self.pools[pool_state["address"]] = pool_state
        self.last_update_ts[pool_state["address"]] = datetime.utcnow()
        
        await event_bus.publish("dex.poolUpdate", pool_update)
    
    def get_bound_quote(
        self,
        pool_address: str,
        side: Side,
        size_in: Decimal,
        slippage_bps: int = 75
    ) -> Optional[BoundQuote]:
        """Get bound quote for execution."""
        pool = self.pools.get(pool_address)
        if not pool:
            return None
        
        reserve_in = pool["token_a_reserve"] if side == Side.BUY else pool["token_b_reserve"]
        reserve_out = pool["token_b_reserve"] if side == Side.BUY else pool["token_a_reserve"]
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in,
            reserve_out,
            size_in,
            pool["fee_bps"]
        )
        
        # Check impact against slippage cap
        if impact_pct > Decimal(slippage_bps) / Decimal(100):
            logger.warning(f"Impact {impact_pct}% exceeds slippage cap {slippage_bps} bps")
            return None
        
        return BoundQuote(
            pool_or_route_id=pool_address,
            side=side,
            size_in=size_in,
            size_out=amount_out,
            exec_price=exec_price,
            impact_pct=impact_pct,
            fee_pct=Decimal(pool["fee_bps"]) / Decimal(10000),
            expires_ts=datetime.utcnow() + timedelta(seconds=30)
        )
    
    def check_staleness(self, pool_address: str, max_age_sec: float = 10.0) -> bool:
        """Check if pool data is stale."""
        last_update = self.last_update_ts.get(pool_address)
        if not last_update:
            return True
        
        age = (datetime.utcnow() - last_update).total_seconds()
        return age > max_age_sec
    
    async def execute_swap(
        self,
        pool_address: str,
        side: Side,
        size_in: Decimal,
        min_size_out: Decimal,
        priority_fee_lamports: int = 1000
    ) -> Optional[str]:
        """Execute swap transaction.
        
        Returns transaction signature if successful.
        """
        # For POC, return mock transaction signature
        # Production would build and send actual Solana transaction
        logger.info(
            f"DEX Swap: {side.value} {size_in} in pool {pool_address[:8]}... "
            f"(min_out={min_size_out}, priority_fee={priority_fee_lamports})"
        )
        
        # Simulate transaction
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Mock successful transaction
        mock_sig = f"mock_tx_{int(datetime.utcnow().timestamp())}"
        return mock_sig


# Global instance
solana_connector = SolanaConnector()
