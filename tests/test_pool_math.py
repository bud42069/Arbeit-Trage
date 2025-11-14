"""Unit tests for pool math calculations."""
import pytest
from decimal import Decimal
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))

from connectors.solana_connector import PoolMath


class TestConstantProductQuote:
    """Test suite for constant product AMM (x*y=k) quote calculations."""
    
    def test_basic_swap_no_fee(self):
        """Test basic swap calculation without fees."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("10")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=0
        )
        
        # With no fee and small size, should get close to 10 tokens out
        # Actual: (1000 * 10) / (1000 + 10) = 9.9009...
        assert amount_out > Decimal("9.9")
        assert amount_out < Decimal("10")
        
        # Execution price should be close to 1:1
        assert exec_price > Decimal("0.99")
        assert exec_price < Decimal("1.0")
        
        # Impact should be reasonable for 1% trade size
        assert impact_pct < Decimal("3.0")  # Less than 3%
    
    def test_swap_with_standard_fee(self):
        """Test swap with standard 30 bps (0.3%) fee."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("10")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # With 0.3% fee, should get slightly less than no-fee case
        # Fee reduces effective input: 10 * (1 - 0.003) = 9.97
        # Output: (1000 * 9.97) / (1000 + 9.97) = 9.871...
        assert amount_out > Decimal("9.87")
        assert amount_out < Decimal("9.90")
        
        # Execution price should reflect fee
        assert exec_price > Decimal("0.987")
        assert exec_price < Decimal("0.990")
    
    def test_large_swap_high_impact(self):
        """Test that large swaps relative to pool size have high impact."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("500")  # 50% of pool!
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Large swap should have significant price impact
        assert impact_pct > Decimal("15")  # > 15% impact
        
        # Should get much less than 500 tokens out due to slippage
        assert amount_out < Decimal("350")
        
        # Execution price should be much worse than spot
        assert exec_price < Decimal("0.7")  # Less than 0.7:1
    
    def test_small_swap_minimal_impact(self):
        """Test that small swaps have minimal price impact."""
        reserve_in = Decimal("1000000")  # Large pool
        reserve_out = Decimal("1000000")
        amount_in = Decimal("100")  # 0.01% of pool
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Small swap should have minimal impact
        assert impact_pct < Decimal("0.01")  # < 0.01%
        
        # Execution price should be very close to spot (1:1 minus fee)
        assert exec_price > Decimal("0.996")
        assert exec_price < Decimal("0.998")
    
    def test_unbalanced_pool(self):
        """Test swap in unbalanced pool (different reserve sizes)."""
        reserve_in = Decimal("2000")  # Token A
        reserve_out = Decimal("1000")  # Token B (2:1 ratio)
        amount_in = Decimal("100")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # In 2:1 pool, swapping 100 of A should get ~47 of B
        # (1000 * 99.7) / (2000 + 99.7) = 47.48...
        assert amount_out > Decimal("47")
        assert amount_out < Decimal("48")
        
        # Exec price should be around 0.47 (reflecting the 2:1 pool ratio minus slippage)
        assert exec_price > Decimal("0.47")
        assert exec_price < Decimal("0.48")
    
    def test_different_fee_tiers(self):
        """Test quote calculation with different fee tiers."""
        reserve_in = Decimal("10000")
        reserve_out = Decimal("10000")
        amount_in = Decimal("100")
        
        # Test 5 bps (0.05%) - low fee
        out_5bps, price_5bps, _ = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=5
        )
        
        # Test 30 bps (0.3%) - standard fee
        out_30bps, price_30bps, _ = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Test 100 bps (1.0%) - high fee
        out_100bps, price_100bps, _ = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=100
        )
        
        # Higher fees should give less output
        assert out_5bps > out_30bps > out_100bps
        assert price_5bps > price_30bps > price_100bps
    
    def test_zero_input_returns_zero(self):
        """Test that zero input returns zero output."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("0")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        assert amount_out == Decimal("0")
        assert impact_pct == Decimal("0")
    
    def test_price_impact_calculation_accuracy(self):
        """Test that price impact is calculated correctly."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("100")
        
        _, _, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # For a 10% swap (100/1000), price impact should be significant
        # but not as high as the swap size due to the curve
        assert impact_pct > Decimal("4")  # > 4%
        assert impact_pct < Decimal("6")  # < 6%
    
    def test_extreme_pool_imbalance(self):
        """Test behavior with extremely imbalanced pools."""
        reserve_in = Decimal("1000000")  # Very deep
        reserve_out = Decimal("100")  # Very shallow
        amount_in = Decimal("10")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Output should be very small due to shallow reserve
        assert amount_out < Decimal("0.1")
        
        # Price impact on shallow side should be significant
        assert impact_pct > Decimal("1")  # > 1%


class TestPoolMathEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_small_reserves(self):
        """Test behavior with very small reserves."""
        reserve_in = Decimal("0.001")
        reserve_out = Decimal("0.001")
        amount_in = Decimal("0.0001")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Should still return valid results
        assert amount_out > Decimal("0")
        assert exec_price > Decimal("0")
        assert impact_pct >= Decimal("0")
    
    def test_very_large_reserves(self):
        """Test behavior with very large reserves."""
        reserve_in = Decimal("1000000000")  # 1 billion
        reserve_out = Decimal("1000000000")
        amount_in = Decimal("1000000")  # 1 million (0.1% of pool)
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Large pool should have minimal impact for this size
        assert impact_pct < Decimal("0.05")  # < 0.05%
    
    def test_fee_of_zero(self):
        """Test that 0 bps fee works correctly."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("10")
        
        amount_out, _, _ = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=0
        )
        
        # With no fee, should get maximum output
        expected = (reserve_out * amount_in) / (reserve_in + amount_in)
        assert abs(amount_out - expected) < Decimal("0.0001")
    
    def test_maximum_fee(self):
        """Test with 100% fee (10000 bps)."""
        reserve_in = Decimal("1000")
        reserve_out = Decimal("1000")
        amount_in = Decimal("100")
        
        amount_out, _, _ = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=10000  # 100% fee
        )
        
        # With 100% fee, should get zero output
        assert amount_out == Decimal("0")
    
    def test_decimal_precision(self):
        """Test that decimal precision is maintained."""
        reserve_in = Decimal("1000.123456789")
        reserve_out = Decimal("999.987654321")
        amount_in = Decimal("10.111111111")
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_in, reserve_out, amount_in, fee_bps=30
        )
        
        # Results should maintain precision
        assert isinstance(amount_out, Decimal)
        assert isinstance(exec_price, Decimal)
        assert isinstance(impact_pct, Decimal)
        
        # Should have reasonable values
        assert amount_out > Decimal("0")
        assert exec_price > Decimal("0")


class TestPoolMathRealWorldScenarios:
    """Test pool math with real-world arbitrage scenarios."""
    
    def test_orca_sol_usdc_typical_trade(self):
        """Test typical trade size on Orca SOL/USDC pool."""
        # Approximate Orca SOL/USDC pool size
        reserve_usdc = Decimal("500000")  # $500k USDC
        reserve_sol = Decimal("3500")  # ~3500 SOL @ $143
        amount_in_usd = Decimal("100")  # $100 trade
        
        amount_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_usdc, reserve_sol, amount_in_usd, fee_bps=30
        )
        
        # $100 should get roughly 0.7 SOL @ $143
        assert amount_out > Decimal("0.69")
        assert amount_out < Decimal("0.71")
        
        # Impact should be minimal for this pool size
        assert impact_pct < Decimal("0.01")  # < 0.01%
    
    def test_arbitrage_profitability_calculation(self):
        """Test that pool math supports profitability calculations."""
        # CEX price: $143
        # DEX pool: Calculate what we get for $100
        reserve_usdc = Decimal("500000")
        reserve_sol = Decimal("3497")  # Slightly more expensive on DEX
        amount_in_usd = Decimal("100")
        
        sol_out, exec_price, impact_pct = PoolMath.constant_product_quote(
            reserve_usdc, reserve_sol, amount_in_usd, fee_bps=30
        )
        
        # If CEX price is $143/SOL, we can buy at CEX and sell on DEX
        cex_price = Decimal("143")
        sol_bought_cex = amount_in_usd / cex_price
        
        # Would we make money? (ignoring CEX fees for this test)
        usdc_value_on_dex = sol_bought_cex * exec_price
        # This is simplified; real calc needs reverse quote
    
    def test_round_trip_consistency(self):
        """Test that two opposite swaps approximately cancel out (minus fees)."""
        reserve_a = Decimal("1000")
        reserve_b = Decimal("1000")
        
        # Swap A -> B
        amount_b, _, _ = PoolMath.constant_product_quote(
            reserve_a, reserve_b, Decimal("10"), fee_bps=30
        )
        
        # Update reserves after first swap
        new_reserve_a = reserve_a + Decimal("10")
        new_reserve_b = reserve_b - amount_b
        
        # Swap B -> A (reverse)
        amount_a, _, _ = PoolMath.constant_product_quote(
            new_reserve_b, new_reserve_a, amount_b, fee_bps=30
        )
        
        # Should get less than original 10 back due to fees + slippage
        assert amount_a < Decimal("10")
        # But should get most of it back (fees are 0.6% total)
        assert amount_a > Decimal("9.9")  # Lost ~1% to fees + slippage


if __name__ == "__main__":
    # Run tests with: pytest tests/test_pool_math.py -v
    pytest.main([__file__, "-v"])
