"""Prometheus metrics for observability."""
import logging
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

logger = logging.getLogger(__name__)

# Create registry
registry = CollectorRegistry()

# Opportunities
opportunities_total = Counter(
    'arb_opportunities_total',
    'Total arbitrage opportunities detected',
    ['asset', 'direction'],
    registry=registry
)

# Trades
trades_total = Counter(
    'arb_trades_total',
    'Total arbitrage trades executed',
    ['asset', 'direction', 'status'],
    registry=registry
)

trade_pnl_usd = Histogram(
    'arb_trade_pnl_usd',
    'Trade PnL in USD',
    ['asset'],
    registry=registry,
    buckets=[1, 5, 10, 25, 50, 100, 250, 500]
)

# Latency
trade_latency_seconds = Histogram(
    'arb_trade_latency_seconds',
    'End-to-end trade latency',
    ['asset'],
    registry=registry,
    buckets=[0.1, 0.25, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]
)

# Staleness
ws_staleness_seconds = Gauge(
    'arb_ws_staleness_seconds',
    'WebSocket data staleness',
    ['venue'],
    registry=registry
)

# Risk
risk_paused = Gauge(
    'arb_risk_paused',
    'Risk service paused status (1=paused, 0=active)',
    registry=registry
)

daily_pnl_usd = Gauge(
    'arb_daily_pnl_usd',
    'Daily cumulative PnL',
    registry=registry
)

# Connections
connection_status = Gauge(
    'arb_connection_status',
    'Connection status (1=connected, 0=disconnected)',
    ['venue'],
    registry=registry
)


def get_metrics() -> bytes:
    """Get Prometheus metrics."""
    return generate_latest(registry)
