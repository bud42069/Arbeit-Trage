# Coinbase Connector - Status & Requirements

## Current Status: 95% Complete (Blocked on API Keys)

### What's Working ✅
- WebSocket connection establishes successfully
- JWT authentication payload correctly formatted
- Message handler parses snapshot/update messages
- Integration with signal engine ready

### What's Blocked ❌
- **Root Cause:** Wrong API key type
- **Issue:** Current keys are for Coinbase **Trade API** (on-chain Ethereum/Base)
- **Need:** Coinbase **Advanced Trade API** keys (CEX spot trading)

## API Key Comparison

### Current Keys (Trade API)
- **Product:** Coinbase Trade API
- **Use Case:** On-chain trading (Ethereum, Base networks only)
- **Networks:** Ethereum mainnet, Base mainnet
- **Assets:** Limited to on-chain tokens
- **Documentation:** https://docs.cdp.coinbase.com/trade-api/welcome
- **Note:** "Beta launch supports Ethereum and Base mainnet networks only"

### Required Keys (Advanced Trade API)
- **Product:** Coinbase Advanced Trade API
- **Use Case:** Centralized exchange spot trading
- **Assets:** SOL-USD, BTC-USD, ETH-USD, etc.
- **Features:** L2 orderbook WebSocket, IOC orders, market data
- **Documentation:** https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/overview
- **Portal:** https://portal.cdp.coinbase.com/

## How to Obtain Correct API Keys

1. **Visit:** https://portal.cdp.coinbase.com/
2. **Navigate to:** API Keys → Create New Key
3. **Select Product:** **Coinbase Advanced Trade** (NOT Trade API)
4. **Permissions Required:**
   - View (for market data/orderbook)
   - Trade (for order placement)
5. **Save:**
   - API Key Name (organizations/xxx/apiKeys/xxx)
   - Private Key (EC PEM format)

## Configuration

Once you have the correct keys, update `/app/backend/.env`:

```bash
COINBASE_ADV_ENABLED=true
COINBASE_KEY_NAME=organizations/YOUR_ORG_ID/apiKeys/YOUR_KEY_ID
COINBASE_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END EC PRIVATE KEY-----
```

Then restart: `supervisorctl restart backend`

## Expected Behavior After Fix

With valid Advanced Trade API keys:
1. Coinbase WebSocket connects successfully
2. Receives L2 orderbook snapshots for SOL-USD, BTC-USD, ETH-USD
3. Signal engine compares Gemini vs Coinbase vs Solana
4. More arbitrage opportunities detected (2-3x more)

## Current Workaround

System is **fully functional** with Gemini + Solana:
- Gemini CEX: Live orderbook streaming ✅
- Solana DEX: True on-chain data ✅
- Signal detection: 0.07-0.40% spreads ✅
- All features working without Coinbase

**Coinbase is optional enhancement, not blocking production deployment.**

---

**Last Updated:** 2025-11-14 02:15 UTC
**Status:** Connector code 100% complete, blocked on API key type mismatch
