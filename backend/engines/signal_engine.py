"""Signal engine for arbitrage opportunity detection."""
import logging
import uuid
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from shared.types import Opportunity, Window, BookUpdate, PoolUpdate
from shared.events import event_bus
from config import settings

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages trading windows for TOD analysis."""
    
    def __init__(self):
        self.windows: Dict[str, Window] = {}
        self.current_window: Dict[str, Optional[Window]] = {}
        self.window_grace_sec = 20
    
    def get_or_create_window(self, asset: str) -> Window:
        """Get current window or create new one."""
        current = self.current_window.get(asset)
        
        if current:
            # Check if window should be closed
            if datetime.utcnow() - current.start_ts > timedelta(seconds=self.window_grace_sec * 2):
                # Close window
                current.end_ts = datetime.utcnow()
                self.windows[current.id] = current
                current = None
        
        if not current:
            # Create new window
            current = Window(
                id=str(uuid.uuid4()),
                asset=asset,
                start_ts=datetime.utcnow()
            )
            self.current_window[asset] = current
        
        return current


class SignalEngine:
    """Detects arbitrage opportunities from market data."""
    
    def __init__(self):
        self.window_manager = WindowManager()
        self.cex_books: Dict[str, BookUpdate] = {}
        self.dex_pools: Dict[str, PoolUpdate] = {}
        
        # Subscribe to market data events
        event_bus.subscribe("cex.bookUpdate", self.handle_cex_update)
        event_bus.subscribe("dex.poolUpdate", self.handle_dex_update)
    
    async def handle_cex_update(self, book: BookUpdate):
        """Handle CEX order book update."""
        # Store with lowercase key for consistent lookups
        pair_lower = book.pair.lower()
        self.cex_books[pair_lower] = book
        
        logger.info(f"SignalEngine: Received CEX update for {book.pair}, stored as {pair_lower}")
        
        # Normalize pair name for opportunity checking
        if pair_lower == "solusd":
            normalized = "SOL-USD"
        elif pair_lower == "btcusd":
            normalized = "BTC-USD"
        elif pair_lower == "ethusd":
            normalized = "ETH-USD"
        else:
            normalized = pair_lower.upper()
        
        logger.info(f"SignalEngine: Checking opportunities for {normalized}")
        await self.check_opportunities(normalized)
    
    async def handle_dex_update(self, pool: PoolUpdate):
        """Handle DEX pool update."""
        logger.info(f"SignalEngine: Received DEX pool update")
        # Map pool to asset symbol
        asset = "SOL-USD"  # Simplified for POC
        self.dex_pools[asset] = pool
        logger.info(f"SignalEngine: DEX pool stored for {asset}, price_mid={pool.price_mid}")
        await self.check_opportunities(asset)
    
    async def check_opportunities(self, asset: str):
        """Check for arbitrage opportunities."""
        # Map asset to CEX symbol (e.g., SOL-USD -> solusd for Gemini)
        cex_symbol = asset.lower().replace("-", "")
        
        cex_book = self.cex_books.get(cex_symbol)
        dex_pool = self.dex_pools.get(asset)
        
        logger.debug(f"Checking {asset}: CEX book={bool(cex_book)}, DEX pool={bool(dex_pool)}")
        
        if not cex_book or not dex_pool:
            return
        
        # Parse best prices
        if not cex_book.bids or not cex_book.asks:
            logger.debug(f"{asset}: CEX book has no bids/asks")
            return
        
        cex_bid = Decimal(cex_book.bids[0][0])
        cex_ask = Decimal(cex_book.asks[0][0])
        dex_price = dex_pool.price_mid
        
        logger.info(f"{asset} prices: CEX bid={cex_bid}, ask={cex_ask}, DEX mid={dex_price}")
        
        # Check both directions
        # Direction 1: Buy CEX, Sell DEX
        if dex_price > cex_ask:
            spread_pct = ((dex_price - cex_ask) / cex_ask) * Decimal(100)
            logger.info(f"CEX→DEX spread detected: {asset} spread={spread_pct:.4f}% (CEX ask={cex_ask}, DEX mid={dex_price})")
            await self._evaluate_opportunity(
                asset=asset,
                direction="cex_to_dex",
                cex_price=cex_ask,
                dex_price=dex_price,
                spread_pct=spread_pct
            )
        
        # Direction 2: Buy DEX, Sell CEX
        if cex_bid > dex_price:
            spread_pct = ((cex_bid - dex_price) / dex_price) * Decimal(100)
            logger.info(f"DEX→CEX spread detected: {asset} spread={spread_pct:.4f}% (CEX bid={cex_bid}, DEX mid={dex_price})")
            await self._evaluate_opportunity(
                asset=asset,
                direction="dex_to_cex",
                cex_price=cex_bid,
                dex_price=dex_price,
                spread_pct=spread_pct
            )
    
    async def _evaluate_opportunity(
        self,
        asset: str,
        direction: str,
        cex_price: Decimal,
        dex_price: Decimal,
        spread_pct: Decimal
    ):
        """Evaluate if opportunity meets threshold."""
        # Apply fees and slippage haircut
        cex_fee_pct = Decimal("0.35")  # Gemini taker fee ~0.35%
        dex_fee_pct = Decimal("0.30")  # Typical DEX fee 0.30%
        haircut_pct = Decimal("0.75")  # Slippage/impact haircut
        
        total_costs = cex_fee_pct + dex_fee_pct + haircut_pct
        predicted_pnl_pct = spread_pct - total_costs
        
        # Check threshold
        # For production demo: Accept negative PnL to show realistic spreads
        # Production: Use 1.0% threshold to ensure profitability
        threshold_pct = Decimal("-1.0")  # Accept any spread for demo
        
        if predicted_pnl_pct < threshold_pct:
            return
        
        # Opportunity detected!
        window = self.window_manager.get_or_create_window(asset)
        window.signals += 1
        
        opportunity = Opportunity(
            id=str(uuid.uuid4()),
            asset=asset,
            direction=direction,
            cex_price=cex_price,
            dex_price=dex_price,
            spread_pct=spread_pct,
            predicted_pnl_pct=predicted_pnl_pct,
            size=Decimal("50"),  # Base size, will be adjusted by executor
            timestamp=datetime.utcnow(),
            window_id=window.id
        )
        
        logger.info(
            f"Opportunity: {asset} {direction} spread={spread_pct:.2f}% "
            f"predicted_pnl={predicted_pnl_pct:.2f}%"
        )
        
        # Emit opportunity event
        await event_bus.publish("signal.opportunity", opportunity)


# Global instance
signal_engine = SignalEngine()
