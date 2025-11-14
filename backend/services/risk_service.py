"""Risk service for kill-switches and limits."""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict

from shared.types import Trade
from shared.events import event_bus
from config import settings

logger = logging.getLogger(__name__)


class RiskService:
    """Manages risk controls and kill-switches."""
    
    def __init__(self):
        self.daily_pnl: Decimal = Decimal("0")
        self.daily_trades: int = 0
        self.daily_reset_time: datetime = datetime.utcnow().replace(hour=0, minute=0, second=0)
        self.is_paused: bool = False
        self.pause_reason: str = ""
        self.staleness_checks: dict = {}
        
        # Subscribe to trade completions
        event_bus.subscribe("trade.completed", self.handle_trade_completed)
    
    async def handle_trade_completed(self, trade: Trade):
        """Track completed trade for risk limits."""
        # Reset daily counters if new day
        if datetime.utcnow() - self.daily_reset_time > timedelta(days=1):
            self.daily_pnl = Decimal("0")
            self.daily_trades = 0
            self.daily_reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0)
        
        # Update daily stats
        self.daily_pnl += trade.pnl_abs
        self.daily_trades += 1
        
        # Check daily loss limit
        if self.daily_pnl < -settings.daily_loss_limit_usd:
            await self.trigger_pause(f"Daily loss limit exceeded: {self.daily_pnl:.2f} USD")
    
    async def trigger_pause(self, reason: str):
        """Trigger kill-switch pause."""
        self.is_paused = True
        self.pause_reason = reason
        logger.warning(f"KILL-SWITCH TRIGGERED: {reason}")
        
        # Emit pause event
        await event_bus.publish("risk.paused", {
            "reason": reason,
            "timestamp": datetime.utcnow()
        })
    
    async def check_staleness(self, venue: str, last_update: datetime) -> bool:
        """Check if venue data is stale."""
        age = (datetime.utcnow() - last_update).total_seconds()
        
        if age > 10.0:  # 10 second staleness threshold
            if venue not in self.staleness_checks or \
               (datetime.utcnow() - self.staleness_checks[venue]).total_seconds() > 60:
                await self.trigger_pause(f"Venue {venue} data stale: {age:.1f}s")
                self.staleness_checks[venue] = datetime.utcnow()
                return True
        
        return False
    
    def get_status(self) -> dict:
        """Get current risk status."""
        return {
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason,
            "daily_pnl_usd": float(self.daily_pnl),
            "daily_trades": self.daily_trades,
            "daily_loss_limit_usd": settings.daily_loss_limit_usd,
            "daily_remaining_loss_usd": float(Decimal(str(settings.daily_loss_limit_usd)) + self.daily_pnl),
            "observe_only": settings.observe_only_mode
        }
    
    async def resume(self):
        """Resume trading after pause."""
        self.is_paused = False
        self.pause_reason = ""
        logger.info("Risk service resumed")
        
        await event_bus.publish("risk.resumed", {
            "timestamp": datetime.utcnow()
        })


# Global instance
risk_service = RiskService()
