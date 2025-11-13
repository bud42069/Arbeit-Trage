"""Execution engine for dual-leg arbitrage trades."""
import asyncio
import logging
import uuid
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime

from shared.types import Opportunity, Trade, Side, OrderStatus
from shared.events import event_bus
from config import settings
from connectors.gemini_connector import gemini_connector
from connectors.solana_connector import solana_connector

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Executes dual-leg arbitrage trades."""
    
    def __init__(self):
        self.active_trades: Dict[str, Trade] = {}
        self.trade_history: list[Trade] = []
        
        # Subscribe to opportunities
        event_bus.subscribe("signal.opportunity", self.handle_opportunity)
    
    async def handle_opportunity(self, opp: Opportunity):
        """Handle arbitrage opportunity."""
        # Create trade
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            opportunity_id=opp.id,
            asset=opp.asset,
            direction=opp.direction,
            size_asset=opp.size,
            cex_price=opp.cex_price,
            dex_price=opp.dex_price,
            fees_total=Decimal("0"),
            pnl_abs=Decimal("0"),
            pnl_pct=Decimal("0"),
            latency_ms=0,
            timestamp=datetime.utcnow(),
            window_id=opp.window_id,
            status=OrderStatus.PENDING
        )
        
        self.active_trades[trade.trade_id] = trade
        
        # Check if in observe-only mode
        if settings.observe_only_mode:
            logger.info(f"OBSERVE-ONLY: Simulating execution for {opp.id}")
            await self.simulate_dual_leg(trade, opp)
        else:
            # Execute dual-leg
            await self.execute_dual_leg(trade, opp)
    
    async def simulate_dual_leg(self, trade: Trade, opp: Opportunity):
        """Simulate both legs of the arbitrage trade in OBSERVE-ONLY mode."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"[SIMULATED] Executing {opp.direction}: {opp.asset} size={opp.size}")
            
            # Simulate network latency (200-500ms)
            import random
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Simulate order IDs
            trade.cex_order_id = f"sim_cex_{trade.trade_id[:8]}"
            trade.dex_tx_sig = f"sim_dex_{trade.trade_id[:8]}"
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            trade.latency_ms = int(latency)
            
            # Simulate fills with realistic slippage (0.05-0.15%)
            slippage_pct = Decimal(str(random.uniform(0.0005, 0.0015)))
            
            if opp.direction == "cex_to_dex":
                # Buy CEX (pay slightly more), Sell DEX (get slightly less)
                actual_cex_price = opp.cex_price * (Decimal("1") + slippage_pct)
                actual_dex_price = opp.dex_price * (Decimal("1") - slippage_pct)
            else:
                # Buy DEX (pay slightly more), Sell CEX (get slightly less)
                actual_dex_price = opp.dex_price * (Decimal("1") + slippage_pct)
                actual_cex_price = opp.cex_price * (Decimal("1") - slippage_pct)
            
            # Update trade with actual prices
            trade.cex_price = actual_cex_price
            trade.dex_price = actual_dex_price
            trade.status = OrderStatus.FILLED
            
            # Calculate realized PnL
            spread_abs = abs(actual_cex_price - actual_dex_price) * opp.size
            
            # Fees: CEX ~0.25%, DEX ~0.30%, plus 0.05% for Solana priority
            cex_fee = opp.size * actual_cex_price * Decimal("0.0025")
            dex_fee = opp.size * actual_dex_price * Decimal("0.0030")
            priority_fee = opp.size * actual_dex_price * Decimal("0.0005")
            
            trade.fees_total = cex_fee + dex_fee + priority_fee
            trade.pnl_abs = spread_abs - trade.fees_total
            trade.pnl_pct = (trade.pnl_abs / (opp.size * opp.cex_price)) * Decimal(100)
            
            logger.info(
                f"[SIMULATED] Trade {trade.trade_id[:8]}... completed: "
                f"PnL={trade.pnl_pct:.2f}% (${trade.pnl_abs:.2f}), "
                f"fees=${trade.fees_total:.2f}, "
                f"latency={trade.latency_ms}ms, "
                f"slippage={slippage_pct*100:.3f}%"
            )
            
            # Emit trade event
            await event_bus.publish("trade.completed", trade)
            
        except Exception as e:
            logger.error(f"[SIMULATED] Trade {trade.trade_id} failed: {e}")
            trade.status = OrderStatus.FAILED
        
        finally:
            # Move to history
            self.trade_history.append(trade)
            del self.active_trades[trade.trade_id]
    
    async def execute_dual_leg(self, trade: Trade, opp: Opportunity):
        """Execute both legs of the arbitrage trade."""
        start_time = datetime.utcnow()
        
        try:
            # Map asset to symbols
            cex_symbol = opp.asset.lower().replace("-", "")  # e.g., solusd
            pool_address = "mock_pool_address"  # Would be from config
            
            if opp.direction == "cex_to_dex":
                # Buy CEX, Sell DEX
                logger.info(f"Executing CEX->DEX: Buy {opp.size} on CEX, Sell on DEX")
                
                # Leg 1: Buy on CEX (IOC order)
                cex_order = await gemini_connector.place_ioc_order(
                    symbol=cex_symbol,
                    side=Side.BUY,
                    quantity=opp.size,
                    price=opp.cex_price * Decimal("1.001"),  # Slight price cushion
                    client_order_id=f"{trade.trade_id}_cex"
                )
                trade.cex_order_id = cex_order.get("order_id")
                
                # Leg 2: Sell on DEX
                dex_tx_sig = await solana_connector.execute_swap(
                    pool_address=pool_address,
                    side=Side.SELL,
                    size_in=opp.size,
                    min_size_out=opp.size * opp.dex_price * Decimal("0.99"),  # 1% slippage
                    priority_fee_lamports=5000
                )
                trade.dex_tx_sig = dex_tx_sig
                
            else:
                # Buy DEX, Sell CEX
                logger.info(f"Executing DEX->CEX: Buy on DEX, Sell {opp.size} on CEX")
                
                # Leg 1: Buy on DEX
                dex_tx_sig = await solana_connector.execute_swap(
                    pool_address=pool_address,
                    side=Side.BUY,
                    size_in=opp.size * opp.dex_price,  # Pay in USDC
                    min_size_out=opp.size * Decimal("0.99"),
                    priority_fee_lamports=5000
                )
                trade.dex_tx_sig = dex_tx_sig
                
                # Leg 2: Sell on CEX
                cex_order = await gemini_connector.place_ioc_order(
                    symbol=cex_symbol,
                    side=Side.SELL,
                    quantity=opp.size,
                    price=opp.cex_price * Decimal("0.999"),  # Slight price cushion
                    client_order_id=f"{trade.trade_id}_cex"
                )
                trade.cex_order_id = cex_order.get("order_id")
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            trade.latency_ms = int(latency)
            
            # Update trade status
            trade.status = OrderStatus.FILLED
            
            # Calculate realized PnL (simplified)
            spread_abs = abs(opp.cex_price - opp.dex_price) * opp.size
            fees = opp.size * (opp.cex_price + opp.dex_price) * Decimal("0.0065")  # ~0.65% total fees
            trade.fees_total = fees
            trade.pnl_abs = spread_abs - fees
            trade.pnl_pct = (trade.pnl_abs / (opp.size * opp.cex_price)) * Decimal(100)
            
            logger.info(
                f"Trade {trade.trade_id[:8]}... completed: "
                f"PnL={trade.pnl_pct:.2f}% ({trade.pnl_abs:.2f} USD), "
                f"latency={trade.latency_ms}ms"
            )
            
            # Emit trade event
            await event_bus.publish("trade.completed", trade)
            
        except Exception as e:
            logger.error(f"Trade {trade.trade_id} failed: {e}")
            trade.status = OrderStatus.FAILED
        
        finally:
            # Move to history
            self.trade_history.append(trade)
            del self.active_trades[trade.trade_id]


# Global instance
execution_engine = ExecutionEngine()
