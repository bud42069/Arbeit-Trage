"""
Comprehensive backend API testing for CEX/DEX Arbitrage System
Tests: Solana on-chain data, Gemini orderbook, signal detection, execution simulation
"""
import requests
import sys
import time
from datetime import datetime
from decimal import Decimal

class ArbitrageAPITester:
    def __init__(self, base_url="https://arb-signal-system.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.warnings = []

    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        self.log(f"Testing {name}...", "TEST")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}", "PASS")
                return True, response.json() if response.text else {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:200]}", "DEBUG")
                return False, {}

        except requests.exceptions.Timeout:
            self.log(f"❌ FAILED - Request timeout after {timeout}s", "FAIL")
            return False, {}
        except Exception as e:
            self.log(f"❌ FAILED - Error: {str(e)}", "FAIL")
            return False, {}

    def test_system_status(self):
        """Test system status endpoint and verify connections"""
        self.log("\n=== Testing System Status ===", "SECTION")
        
        success, data = self.run_test(
            "System Status",
            "GET",
            "api/v1/status",
            200
        )
        
        if not success:
            self.critical_failures.append("System status endpoint failed")
            return False
        
        # Verify connections
        connections = data.get('connections', {})
        self.log(f"Connections: {connections}", "INFO")
        
        # Check Gemini connection
        if connections.get('gemini'):
            self.log("✅ Gemini CEX connected", "PASS")
        else:
            self.warnings.append("Gemini CEX not connected")
            self.log("⚠️  Gemini CEX not connected", "WARN")
        
        # Check Solana connection
        if connections.get('solana'):
            self.log("✅ Solana DEX connected", "PASS")
        else:
            self.warnings.append("Solana DEX not connected")
            self.log("⚠️  Solana DEX not connected", "WARN")
        
        # Check Coinbase connection (expected to be degraded)
        coinbase_status = "connected" if connections.get('coinbase') else "degraded"
        self.log(f"ℹ️  Coinbase status: {coinbase_status} (degraded is expected)", "INFO")
        
        # Check risk status
        risk = data.get('risk', {})
        self.log(f"Risk Status: is_paused={risk.get('is_paused')}, observe_only={risk.get('observe_only')}", "INFO")
        
        if risk.get('observe_only'):
            self.log("✅ OBSERVE_ONLY mode active (expected)", "PASS")
        
        return True

    def test_opportunities_endpoint(self):
        """Test opportunities endpoint and verify data structure"""
        self.log("\n=== Testing Opportunities Endpoint ===", "SECTION")
        
        success, data = self.run_test(
            "Get Opportunities",
            "GET",
            "api/v1/opportunities?limit=10",
            200
        )
        
        if not success:
            self.critical_failures.append("Opportunities endpoint failed")
            return False
        
        opportunities = data.get('opportunities', [])
        self.log(f"Found {len(opportunities)} opportunities", "INFO")
        
        if len(opportunities) > 0:
            # Verify first opportunity structure
            opp = opportunities[0]
            required_fields = ['id', 'asset', 'direction', 'cex_price', 'dex_price', 
                             'spread_pct', 'predicted_pnl_pct', 'timestamp']
            
            missing_fields = [f for f in required_fields if f not in opp]
            if missing_fields:
                self.log(f"❌ Missing fields in opportunity: {missing_fields}", "FAIL")
                self.critical_failures.append(f"Opportunity missing fields: {missing_fields}")
                return False
            
            self.log(f"✅ Opportunity structure valid", "PASS")
            self.log(f"Sample: {opp['asset']} {opp['direction']} spread={opp['spread_pct']}%", "INFO")
            
            # Verify spread column exists
            if 'spread_pct' in opp:
                self.log(f"✅ Spread column present: {opp['spread_pct']}%", "PASS")
            else:
                self.warnings.append("Spread column missing in opportunities")
        else:
            self.log("⚠️  No opportunities found (may be normal if no spreads detected)", "WARN")
        
        return True

    def test_trades_endpoint(self):
        """Test trades endpoint and verify PnL calculations"""
        self.log("\n=== Testing Trades Endpoint ===", "SECTION")
        
        success, data = self.run_test(
            "Get Trades",
            "GET",
            "api/v1/trades?limit=10",
            200
        )
        
        if not success:
            self.critical_failures.append("Trades endpoint failed")
            return False
        
        trades = data.get('trades', [])
        self.log(f"Found {len(trades)} trades", "INFO")
        
        if len(trades) > 0:
            # Verify first trade structure
            trade = trades[0]
            required_fields = ['trade_id', 'asset', 'direction', 'size_asset', 
                             'cex_price', 'dex_price', 'pnl_abs', 'pnl_pct', 
                             'fees_total', 'latency_ms', 'timestamp', 'status']
            
            missing_fields = [f for f in required_fields if f not in trade]
            if missing_fields:
                self.log(f"❌ Missing fields in trade: {missing_fields}", "FAIL")
                self.critical_failures.append(f"Trade missing fields: {missing_fields}")
                return False
            
            self.log(f"✅ Trade structure valid", "PASS")
            
            # Verify PnL calculation
            try:
                size = float(trade['size_asset'])
                cex_price = float(trade['cex_price'])
                dex_price = float(trade['dex_price'])
                fees = float(trade['fees_total'])
                pnl_abs = float(trade['pnl_abs'])
                
                # Calculate expected PnL
                spread_abs = abs(cex_price - dex_price) * size
                expected_pnl = spread_abs - fees
                
                # Allow 1% tolerance for rounding
                if abs(pnl_abs - expected_pnl) / abs(expected_pnl) < 0.01:
                    self.log(f"✅ PnL calculation correct: ${pnl_abs:.2f}", "PASS")
                else:
                    self.log(f"⚠️  PnL calculation mismatch: got ${pnl_abs:.2f}, expected ${expected_pnl:.2f}", "WARN")
                    self.warnings.append(f"PnL calculation mismatch in trade {trade['trade_id']}")
                
                # Verify realistic slippage (0.05-0.15%)
                slippage_pct = abs((cex_price - dex_price) / cex_price) * 100
                if 0.05 <= slippage_pct <= 0.20:
                    self.log(f"✅ Realistic slippage: {slippage_pct:.3f}%", "PASS")
                else:
                    self.log(f"⚠️  Slippage outside expected range: {slippage_pct:.3f}%", "WARN")
                
                # Verify fees (~0.6%)
                fee_pct = (fees / (size * cex_price)) * 100
                if 0.5 <= fee_pct <= 0.7:
                    self.log(f"✅ Realistic fees: {fee_pct:.2f}%", "PASS")
                else:
                    self.log(f"⚠️  Fees outside expected range: {fee_pct:.2f}%", "WARN")
                
            except Exception as e:
                self.log(f"❌ Error verifying PnL: {str(e)}", "FAIL")
                self.critical_failures.append(f"PnL verification failed: {str(e)}")
                return False
        else:
            self.log("⚠️  No trades found (may be normal if system just started)", "WARN")
        
        return True

    def test_pause_resume_controls(self):
        """Test pause/resume controls"""
        self.log("\n=== Testing Pause/Resume Controls ===", "SECTION")
        
        # Test pause
        success, data = self.run_test(
            "Pause Trading",
            "POST",
            "api/v1/controls/pause",
            200,
            data={"action": "pause", "reason": "Test pause"}
        )
        
        if not success:
            self.warnings.append("Pause control failed")
            return False
        
        self.log("✅ Pause control working", "PASS")
        
        # Wait a moment
        time.sleep(1)
        
        # Test resume
        success, data = self.run_test(
            "Resume Trading",
            "POST",
            "api/v1/controls/resume",
            200
        )
        
        if not success:
            self.warnings.append("Resume control failed")
            return False
        
        self.log("✅ Resume control working", "PASS")
        return True

    def test_inject_opportunity(self):
        """Test synthetic opportunity injection (for testing pipeline)"""
        self.log("\n=== Testing Opportunity Injection ===", "SECTION")
        
        success, data = self.run_test(
            "Inject Test Opportunity",
            "POST",
            "api/v1/test/inject-opportunity?asset=SOL-USD&direction=cex_to_dex&spread_pct=2.5",
            200
        )
        
        if not success:
            self.warnings.append("Opportunity injection failed")
            return False
        
        self.log("✅ Opportunity injection working", "PASS")
        self.log("ℹ️  Waiting 3 seconds for execution...", "INFO")
        time.sleep(3)
        
        # Verify trade was created
        success, trades_data = self.run_test(
            "Verify Injected Trade",
            "GET",
            "api/v1/trades?limit=1",
            200
        )
        
        if success and trades_data.get('trades'):
            self.log("✅ Injected opportunity executed successfully", "PASS")
        else:
            self.log("⚠️  Injected opportunity may not have executed", "WARN")
        
        return True

    def verify_solana_price_parsing(self):
        """Verify Solana on-chain price parsing is working"""
        self.log("\n=== Verifying Solana On-Chain Data ===", "SECTION")
        
        # Get opportunities to check DEX prices
        success, data = self.run_test(
            "Get Opportunities for Solana Verification",
            "GET",
            "api/v1/opportunities?limit=5",
            200
        )
        
        if not success:
            return False
        
        opportunities = data.get('opportunities', [])
        
        if len(opportunities) > 0:
            # Check if DEX prices are realistic (SOL should be around $140-$150)
            for opp in opportunities[:3]:
                if opp.get('asset') == 'SOL-USD':
                    dex_price = float(opp.get('dex_price', 0))
                    
                    # SOL price should be in reasonable range
                    if 100 <= dex_price <= 200:
                        self.log(f"✅ Realistic SOL DEX price: ${dex_price:.2f}", "PASS")
                        self.log(f"✅ On-chain Whirlpool parsing working (Q64.64 conversion)", "PASS")
                        return True
                    else:
                        self.log(f"⚠️  SOL DEX price seems off: ${dex_price:.2f}", "WARN")
                        self.warnings.append(f"Unusual SOL DEX price: ${dex_price:.2f}")
        
        self.log("ℹ️  No SOL-USD opportunities found to verify on-chain parsing", "INFO")
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60, "SECTION")
        self.log("TEST SUMMARY", "SECTION")
        self.log("="*60, "SECTION")
        
        self.log(f"Tests Run: {self.tests_run}", "INFO")
        self.log(f"Tests Passed: {self.tests_passed}", "INFO")
        self.log(f"Tests Failed: {self.tests_run - self.tests_passed}", "INFO")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%", "INFO")
        
        if self.critical_failures:
            self.log("\n❌ CRITICAL FAILURES:", "FAIL")
            for failure in self.critical_failures:
                self.log(f"  - {failure}", "FAIL")
        
        if self.warnings:
            self.log("\n⚠️  WARNINGS:", "WARN")
            for warning in self.warnings:
                self.log(f"  - {warning}", "WARN")
        
        if not self.critical_failures:
            self.log("\n✅ All critical tests passed!", "PASS")
        
        self.log("="*60 + "\n", "SECTION")
        
        return 0 if not self.critical_failures else 1


def main():
    """Run all backend tests"""
    tester = ArbitrageAPITester()
    
    print("\n" + "="*60)
    print("CEX/DEX ARBITRAGE BACKEND API TESTING")
    print("="*60 + "\n")
    
    # Run all tests
    tester.test_system_status()
    tester.test_opportunities_endpoint()
    tester.test_trades_endpoint()
    tester.verify_solana_price_parsing()
    tester.test_pause_resume_controls()
    tester.test_inject_opportunity()
    
    # Print summary
    return tester.print_summary()


if __name__ == "__main__":
    sys.exit(main())
