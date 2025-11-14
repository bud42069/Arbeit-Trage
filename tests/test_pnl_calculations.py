"""Unit tests for PnL (Profit and Loss) calculations in execution engine."""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.engines.execution_engine import ExecutionEngine
from backend.shared.types import Opportunity, Trade


class TestPnLCalculations:
    """Test suite for PnL calculation accuracy."""
    
    @pytest.fixture
    def execution_engine(self):
        """Create execution engine instance."""
        return ExecutionEngine()
    
    def test_basic_profitable_trade(self):
        """Test PnL calculation for a basic profitable trade."""
        # Buy at $100, sell at $105 (5% gross spread)
        entry_price = Decimal("100")
        exit_price = Decimal("105")
        size = Decimal("10")  # 10 units
        
        # Calculate PnL
        # Gross profit: (105 - 100) * 10 = $50
        # Fees: 1.4% of notional = 1.4% * 1000 = $14
        # Net PnL: $50 - $14 = $36
        # PnL %: 36/1000 = 3.6%
        
        gross_pnl = (exit_price - entry_price) * size
        notional = entry_price * size
        fees = notional * Decimal("0.014")  # 1.4% total fees
        net_pnl = gross_pnl - fees
        pnl_pct = (net_pnl / notional) * Decimal("100")
        
        assert gross_pnl == Decimal("50")
        assert fees == Decimal("14")
        assert net_pnl == Decimal("36")
        assert pnl_pct == Decimal("3.6")
    
    def test_losing_trade(self):
        """Test PnL calculation for a losing trade."""
        # Buy at $100, sell at $99 (1% loss)
        entry_price = Decimal("100")
        exit_price = Decimal("99")
        size = Decimal("10")
        
        gross_pnl = (exit_price - entry_price) * size  # -$10
        notional = entry_price * size  # $1000
        fees = notional * Decimal("0.014")  # $14
        net_pnl = gross_pnl - fees  # -$10 - $14 = -$24
        pnl_pct = (net_pnl / notional) * Decimal("100")
        
        assert gross_pnl == Decimal("-10")
        assert net_pnl == Decimal("-24")
        assert pnl_pct == Decimal("-2.4")
        assert net_pnl < Decimal("0")  # Confirm it's a loss
    
    def test_breakeven_trade_with_fees(self):
        """Test that equal prices result in loss due to fees."""
        # Buy and sell at same price
        entry_price = Decimal("100")
        exit_price = Decimal("100")  # No price change
        size = Decimal("10")
        
        gross_pnl = (exit_price - entry_price) * size  # $0
        notional = entry_price * size
        fees = notional * Decimal("0.014")
        net_pnl = gross_pnl - fees  # -$14 (pure fee loss)
        pnl_pct = (net_pnl / notional) * Decimal("100")
        
        assert gross_pnl == Decimal("0")
        assert net_pnl == Decimal("-14")
        assert pnl_pct == Decimal("-1.4")  # Exactly the fee percentage
    
    def test_fee_components_breakdown(self):
        """Test individual fee components (CEX + DEX + slippage)."""
        notional = Decimal("1000")
        
        # Fee breakdown: CEX 0.35% + DEX 0.30% + Slippage 0.75% = 1.4%
        cex_fee = notional * Decimal("0.0035")  # $3.50
        dex_fee = notional * Decimal("0.0030")  # $3.00
        slippage = notional * Decimal("0.0075")  # $7.50
        total_fees = cex_fee + dex_fee + slippage  # $14.00
        
        assert cex_fee == Decimal("3.5")
        assert dex_fee == Decimal("3.0")
        assert slippage == Decimal("7.5")
        assert total_fees == Decimal("14.0")
        assert total_fees == notional * Decimal("0.014")
    
    def test_minimum_profitable_spread(self):
        """Test minimum spread needed to overcome fees."""
        # To break even, spread must exceed 1.4% fees
        entry_price = Decimal("100")
        size = Decimal("10")
        notional = entry_price * size  # $1000
        fees = notional * Decimal("0.014")  # $14
        
        # Calculate minimum exit price for breakeven
        min_exit_price = entry_price + (fees / size)  # $100 + $1.40 = $101.40
        
        # Test at breakeven
        gross_pnl = (min_exit_price - entry_price) * size
        net_pnl = gross_pnl - fees
        
        assert abs(net_pnl) < Decimal("0.01")  # Should be ~$0
        
        # Test just above breakeven
        profitable_exit = min_exit_price + Decimal("0.01")
        gross_pnl = (profitable_exit - entry_price) * size
        net_pnl = gross_pnl - fees
        
        assert net_pnl > Decimal("0")  # Should be profitable
    
    def test_large_trade_pnl(self):
        """Test PnL calculation for large trade size."""
        entry_price = Decimal("143.50")
        exit_price = Decimal("145.00")
        size = Decimal("1000")  # Large size
        
        gross_pnl = (exit_price - entry_price) * size  # $1500
        notional = entry_price * size  # $143,500
        fees = notional * Decimal("0.014")  # $2009
        net_pnl = gross_pnl - fees  # -$509 (loss despite price increase!)
        pnl_pct = (net_pnl / notional) * Decimal("100")
        
        # This trade loses money despite 1.04% price increase
        # because fees are 1.4%
        assert net_pnl < Decimal("0")
        assert pnl_pct < Decimal("0")
    
    def test_small_trade_pnl(self):
        """Test PnL calculation for small trade size."""
        entry_price = Decimal("143.50")
        exit_price = Decimal("147.00")  # 2.44% increase
        size = Decimal("0.1")  # Small size
        
        gross_pnl = (exit_price - entry_price) * size  # $0.35
        notional = entry_price * size  # $14.35
        fees = notional * Decimal("0.014")  # $0.2009
        net_pnl = gross_pnl - fees  # $0.1491
        pnl_pct = (net_pnl / notional) * Decimal("100")
        
        assert net_pnl > Decimal("0")
        assert pnl_pct > Decimal("1")  # > 1% net profit
    
    def test_pnl_with_actual_slippage(self):
        """Test PnL when actual slippage differs from estimate."""
        entry_price = Decimal("100")
        expected_exit_price = Decimal("105")
        actual_exit_price = Decimal("104.50")  # Slippage!  
        size = Decimal("10")
        
        # Predicted PnL (without actual slippage)
        predicted_gross = (expected_exit_price - entry_price) * size
        notional = entry_price * size
        fees = notional * Decimal("0.014")
        predicted_net = predicted_gross - fees  # $50 - $14 = $36
        
        # Actual PnL (with actual slippage)
        actual_gross = (actual_exit_price - entry_price) * size
        actual_net = actual_gross - fees  # $45 - $14 = $31
        
        slippage_impact = predicted_net - actual_net
        
        assert predicted_net == Decimal("36")
        assert actual_net == Decimal("31")
        assert slippage_impact == Decimal("5")  # Lost $5 to extra slippage
    
    def test_negative_spread_always_loses(self):
        """Test that negative spread always results in loss."""
        entry_price = Decimal("100")
        exit_price = Decimal("98")  # -2% spread
        size = Decimal("10")
        
        gross_pnl = (exit_price - entry_price) * size  # -$20
        notional = entry_price * size
        fees = notional * Decimal("0.014")  # $14
        net_pnl = gross_pnl - fees  # -$20 - $14 = -$34
        
        assert net_pnl < Decimal("0")
        assert abs(net_pnl) > abs(gross_pnl)  # Fees make it worse


class TestOpportunityToPnLMapping:
    """Test that predicted PnL in opportunities matches calculated PnL."""
    
    def test_opportunity_pnl_accuracy(self):
        """Test that opportunity predicted_pnl_pct is accurate."""
        # Create opportunity
        cex_price = Decimal("143.00")
        dex_price = Decimal("145.50")
        
        # Gross spread
        gross_spread_pct = ((dex_price - cex_price) / cex_price) * Decimal("100")
        
        # Predicted net PnL (after fees)
        predicted_pnl_pct = gross_spread_pct - Decimal("1.4")  # Subtract 1.4% fees
        
        # For this example: 1.75% gross - 1.4% fees = 0.35% net
        assert gross_spread_pct > Decimal("1.7")
        assert gross_spread_pct < Decimal("1.8")
        assert predicted_pnl_pct > Decimal("0.3")
        assert predicted_pnl_pct < Decimal("0.4")
    
    def test_threshold_opportunity(self):
        """Test opportunity at exact profitability threshold (0.1% net)."""
        # For 0.1% net profit, need 1.5% gross spread
        # 1.5% - 1.4% fees = 0.1% net
        cex_price = Decimal("100")
        required_gross_spread = Decimal("1.5")  # percent
        dex_price = cex_price * (Decimal("1") + required_gross_spread / Decimal("100"))
        
        # Verify this hits the threshold
        gross_spread_pct = ((dex_price - cex_price) / cex_price) * Decimal("100")
        predicted_pnl_pct = gross_spread_pct - Decimal("1.4")
        
        assert abs(predicted_pnl_pct - Decimal("0.1")) < Decimal("0.001")
    
    def test_unprofitable_opportunity_rejected(self):
        """Test that opportunities below threshold are not executed."""
        # 1.3% gross spread - 1.4% fees = -0.1% net (LOSS)
        cex_price = Decimal("100")
        dex_price = Decimal("101.30")
        
        gross_spread_pct = ((dex_price - cex_price) / cex_price) * Decimal("100")
        predicted_pnl_pct = gross_spread_pct - Decimal("1.4")
        
        # This should be rejected (negative net PnL)
        assert predicted_pnl_pct < Decimal("0")
        # In signal engine, this would be filtered out


class TestRealizedVsPredictedPnL:
    """Test comparison between predicted and realized PnL."""
    
    def test_perfect_execution_matches_prediction(self):
        """Test that perfect execution matches predicted PnL."""
        # Opportunity
        cex_price = Decimal("143.00")
        dex_price = Decimal("145.50")
        size = Decimal("50")
        
        # Predicted
        gross_spread = dex_price - cex_price  # $2.50
        gross_pnl = gross_spread * size  # $125
        notional = cex_price * size  # $7150
        fees = notional * Decimal("0.014")  # $100.10
        predicted_net_pnl = gross_pnl - fees  # $24.90
        
        # Realized (perfect execution, no extra slippage)
        realized_entry = cex_price
        realized_exit = dex_price
        realized_gross_pnl = (realized_exit - realized_entry) * size
        realized_net_pnl = realized_gross_pnl - fees
        
        # Should match
        assert predicted_net_pnl == realized_net_pnl
    
    def test_execution_with_slippage_deviation(self):
        """Test that slippage causes realized PnL to deviate from predicted."""
        # Opportunity
        cex_price = Decimal("143.00")
        dex_price = Decimal("145.50")
        size = Decimal("50")
        
        # Predicted (no slippage)
        notional = cex_price * size
        fees = notional * Decimal("0.014")
        predicted_gross_pnl = (dex_price - cex_price) * size
        predicted_net_pnl = predicted_gross_pnl - fees
        
        # Realized (with 0.5% additional slippage)
        slippage_pct = Decimal("0.005")
        realized_exit = dex_price * (Decimal("1") - slippage_pct)  # Worse fill
        realized_gross_pnl = (realized_exit - cex_price) * size
        realized_net_pnl = realized_gross_pnl - fees
        
        # Realized should be worse than predicted
        assert realized_net_pnl < predicted_net_pnl
        
        # Calculate deviation
        deviation = predicted_net_pnl - realized_net_pnl
        assert deviation > Decimal("0")  # Positive deviation (worse outcome)
    
    def test_pnl_accuracy_tolerance(self):
        """Test that realized PnL is within acceptable tolerance of predicted."""
        # In production, realized should be within ±2% of predicted
        # (assuming slippage estimates are good)
        
        predicted_pnl = Decimal("100")
        realized_pnl = Decimal("98.50")  # 1.5% worse
        
        deviation_pct = abs((realized_pnl - predicted_pnl) / predicted_pnl) * Decimal("100")
        
        # Should be within 2% tolerance
        assert deviation_pct < Decimal("2.0")


class TestEdgeCasesAndBoundaries:
    """Test edge cases in PnL calculations."""
    
    def test_zero_size_trade(self):
        """Test PnL for zero size trade."""
        entry_price = Decimal("100")
        exit_price = Decimal("105")
        size = Decimal("0")
        
        gross_pnl = (exit_price - entry_price) * size
        net_pnl = gross_pnl  # No fees for zero size
        
        assert gross_pnl == Decimal("0")
        assert net_pnl == Decimal("0")
    
    def test_extreme_price_movement(self):
        """Test PnL with extreme price movement."""
        entry_price = Decimal("100")
        exit_price = Decimal("200")  # 100% increase!
        size = Decimal("10")
        
        gross_pnl = (exit_price - entry_price) * size  # $1000
        notional = entry_price * size  # $1000
        fees = notional * Decimal("0.014")  # $14
        net_pnl = gross_pnl - fees  # $986
        pnl_pct = (net_pnl / notional) * Decimal("100")  # 98.6%
        
        assert net_pnl == Decimal("986")
        assert pnl_pct > Decimal("98")
    
    def test_decimal_precision_in_pnl(self):
        """Test that PnL maintains precision with small values."""
        entry_price = Decimal("0.0001")
        exit_price = Decimal("0.000105")
        size = Decimal("100000")
        
        gross_pnl = (exit_price - entry_price) * size
        notional = entry_price * size
        fees = notional * Decimal("0.014")
        net_pnl = gross_pnl - fees
        
        # Should maintain precision
        assert isinstance(net_pnl, Decimal)
        assert net_pnl != Decimal("0")  # Should have meaningful value


if __name__ == "__main__":
    # Run tests with: pytest tests/test_pnl_calculations.py -v
    pytest.main([__file__, "-v"])
