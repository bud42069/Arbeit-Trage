"""Shared type definitions for arbitrage system."""
from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Side(str, Enum):
    """Trade side."""
    BUY = "buy"
    SELL = "sell"


class VenueType(str, Enum):
    """Venue type."""
    CEX = "cex"
    DEX = "dex"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BookUpdate(BaseModel):
    """CEX order book update event."""
    venue: str
    pair: str
    timestamp: datetime
    bids: List[List[str]]  # [[price, size], ...]
    asks: List[List[str]]
    sequence: int


class PoolUpdate(BaseModel):
    """DEX pool update event."""
    program: str
    pool: str
    timestamp: datetime
    reserves: Dict[str, str]  # {mint: amount}
    price_mid: Decimal
    fee_bps: int


class BoundQuote(BaseModel):
    """DEX bound quote for execution."""
    pool_or_route_id: str
    side: Side
    size_in: Decimal
    size_out: Decimal
    exec_price: Decimal
    impact_pct: Decimal
    fee_pct: Decimal
    expires_ts: datetime


class Opportunity(BaseModel):
    """Arbitrage opportunity detected."""
    id: str
    asset: str
    direction: str  # "cex_to_dex" or "dex_to_cex"
    cex_price: Decimal
    dex_price: Decimal
    spread_pct: Decimal
    predicted_pnl_pct: Decimal
    size: Decimal
    timestamp: datetime
    window_id: Optional[str] = None


class Trade(BaseModel):
    """Executed arbitrage trade."""
    trade_id: str
    opportunity_id: str
    asset: str
    direction: str
    size_asset: Decimal
    cex_price: Decimal
    dex_price: Decimal
    fees_total: Decimal
    pnl_abs: Decimal
    pnl_pct: Decimal
    latency_ms: int
    timestamp: datetime
    window_id: Optional[str] = None
    cex_order_id: Optional[str] = None
    dex_tx_sig: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING


class Window(BaseModel):
    """Trading window for TOD analysis."""
    id: str
    asset: str
    start_ts: datetime
    end_ts: Optional[datetime] = None
    signals: int = 0
    trades: int = 0
    dominant_dir: Optional[str] = None
    max_net_pnl_pct: Decimal = Decimal("0")
    mean_net_pnl_pct: Decimal = Decimal("0")


class InventorySnapshot(BaseModel):
    """Inventory snapshot per venue."""
    id: str
    timestamp: datetime
    venue: str
    asset_bal: Decimal
    quote_bal: Decimal
