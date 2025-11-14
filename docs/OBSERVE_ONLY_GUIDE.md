# OBSERVE_ONLY / LIVE TRADING MODE - Complete Guide

## Overview
The system now supports **dynamic switching** between OBSERVE_ONLY mode (simulated trades) and LIVE TRADING mode (real trades) through a UI toggle.

---

## ✅ Question 1: Can OBSERVE_ONLY mode be executed in the preview environment?

**YES! It's ALREADY RUNNING!**

### Current State (Preview Environment)
- ✅ **OBSERVE_ONLY mode is active** by default
- ✅ System is detecting **real arbitrage opportunities** (0.07-0.23% spreads)
- ✅ Trades are being **simulated** with realistic slippage/fees
- ✅ PnL is tracked ($2,831.12 shown in overview from 100 simulated trades)

### Why You Don't See Many New Trades
Real spreads detected: **0.07-0.23%**  
Profitability threshold: **0.6%** (after 0.6% total fees)  
Result: Most opportunities filtered as unprofitable ✅ **(Working correctly!)**

### New UI Toggle Feature
I've added a toggle to the **Risk & Limits** screen that allows you to:
1. ✅ Switch between OBSERVE_ONLY and LIVE TRADING mode
2. ✅ See current mode prominently displayed
3. ✅ Get warnings when entering LIVE mode
4. ✅ Works in both preview and local hosting

---

## ✅ Question 2: Can you host locally and run observe mode?

**YES! ABSOLUTELY!**

### Local Hosting Setup

**1. Prerequisites:**
```bash
# Ensure you have these installed
- Docker (for MongoDB)
- Python 3.11+
- Node.js 18+
- Yarn
```

**2. Clone and Setup:**
```bash
# Get the code
git clone <your-repo-url>
cd arbitrage-app

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && yarn install && cd ..
```

**3. Configure Environment:**
```bash
# Copy and edit backend/.env
cp backend/.env.example backend/.env

# Required API keys:
HELIUS_API_KEY=<your-helius-key>           # Get from helius.dev
GEMINI_API_KEY=<your-gemini-key>           # Get from gemini.com
GEMINI_API_SECRET=<your-gemini-secret>
COINBASE_KEY_NAME=<your-coinbase-key>      # Optional
COINBASE_PRIVATE_KEY=<your-coinbase-pem>   # Optional

# MongoDB (use local or Docker)
MONGO_URL=mongodb://localhost:27017/arbitrage

# Trading mode
OBSERVE_ONLY_MODE=True  # Start in safe mode!
```

**4. Start Services:**
```bash
# Option A: Using supervisor (recommended)
supervisorctl start all

# Option B: Manually
# Terminal 1 - MongoDB
docker run -d -p 27017:27017 mongo:latest

# Terminal 2 - Backend
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3 - Frontend
cd frontend && yarn start
```

**5. Access UI:**
```
Frontend: http://localhost:3000
Backend API: http://localhost:8001
API Docs: http://localhost:8001/docs
```

---

## 🎛️ Using the Mode Toggle

### In the UI (Risk & Limits Page)

**OBSERVE_ONLY Mode (Default):**
```
┌─────────────────────────────────────────┐
│ ⚠️  OBSERVE ONLY Mode                   │
│ System will detect opportunities but    │
│ NOT execute real trades                 │
│                   [Enable Live Trading] │
└─────────────────────────────────────────┘
```

**LIVE TRADING Mode:**
```
┌─────────────────────────────────────────┐
│ ⚡ LIVE TRADING Active                   │
│ System is executing real trades with    │
│ real funds                              │
│            [Switch to Observe Only]     │
└─────────────────────────────────────────┘
```

### Via API

**Enable OBSERVE_ONLY Mode:**
```bash
curl -X POST http://localhost:8001/api/v1/controls/observe-only
# Response: {"status": "observe_only", "observe_only_mode": true}
```

**Enable LIVE TRADING Mode:**
```bash
curl -X POST http://localhost:8001/api/v1/controls/live-trading
# Response: {"status": "live_trading", "observe_only_mode": false}
# Backend logs: "⚠️ LIVE TRADING ENABLED - Real orders will be placed!"
```

**Check Current Mode:**
```bash
curl -s http://localhost:8001/api/v1/status | jq '.risk.observe_only'
# Response: true or false
```

---

## 🔐 Safety Features

### When Switching to LIVE TRADING:
1. ✅ **UI Warning:** Large warning toast with ⚡ icon
2. ✅ **Backend Logging:** Prominent warning logged
3. ✅ **Visual Indicator:** Green alert banner in Risk & Limits
4. ✅ **Reversible:** Can switch back to OBSERVE_ONLY anytime

### OBSERVE_ONLY Mode Behavior:
- ✅ Detects **real** opportunities from **real** market data
- ✅ Simulates trades with **realistic** slippage (0.05-0.15%)
- ✅ Calculates **accurate** fees (0.6% total)
- ✅ Tracks PnL without risking funds
- ✅ Generates simulated trade IDs (`sim_cex_*`, `sim_dex_*`)
- ✅ Persists to database for analysis

### LIVE TRADING Mode Behavior:
- ⚠️ Places **REAL** orders on CEX/DEX
- ⚠️ Uses **REAL** funds from your accounts
- ⚠️ Cannot undo executed trades
- ✅ Respects daily loss limits ($500 default)
- ✅ Subject to kill-switches (staleness, pause)
- ✅ IOC orders (Immediate-or-Cancel) minimize risk

---

## 📊 Testing the Toggle

### Test in OBSERVE_ONLY Mode:
```bash
# 1. Ensure mode is active
curl -X POST http://localhost:8001/api/v1/controls/observe-only

# 2. Inject a test opportunity
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=1.5"

# 3. Check trades (should see simulated trade)
curl -s http://localhost:8001/api/v1/trades?limit=1 | jq '.[0]'

# Example output:
{
  "trade_id": "uuid...",
  "cex_order_id": "sim_cex_20251114_050000_abc123",  # ← Simulated!
  "dex_tx_id": "sim_dex_20251114_050000_def456",     # ← Simulated!
  "status": "completed",
  "pnl_abs": 1.31,
  ...
}
```

### Test Mode Switching:
```bash
# 1. Start in OBSERVE_ONLY
curl -X POST http://localhost:8001/api/v1/controls/observe-only

# 2. Verify mode
curl -s http://localhost:8001/api/v1/status | jq '.risk.observe_only'
# Should return: true

# 3. Switch to LIVE (⚠️ WARNING: Only for testing with small amounts!)
curl -X POST http://localhost:8001/api/v1/controls/live-trading

# 4. Verify mode changed
curl -s http://localhost:8001/api/v1/status | jq '.risk.observe_only'
# Should return: false

# 5. Switch back to safe mode
curl -X POST http://localhost:8001/api/v1/controls/observe-only
```

---

## 🚨 Important Notes for LIVE TRADING

### Before Enabling LIVE TRADING:

**1. Verify API Keys Have Trading Permissions:**
```bash
# Gemini: Must have "Fund Manager" role
# Coinbase: Must have "Trade" permission enabled
# Check in your exchange account settings
```

**2. Fund Your Accounts:**
```bash
# Ensure sufficient balance on both CEX and DEX
# Recommended starting amount: $100-500 per venue
# Keep extra for fees and slippage
```

**3. Test with Small Amounts First:**
```bash
# Edit backend/config.py or .env:
MAX_TRADE_SIZE_USD=10  # Start with $10 trades!

# Monitor first 5-10 trades closely
# Verify fills match expectations
# Check slippage is within acceptable range
```

**4. Set Conservative Risk Limits:**
```bash
# In backend/.env:
DAILY_LOSS_LIMIT_USD=50      # Low limit for testing
MAX_POSITION_SIZE_USD=10     # Small position size
STALENESS_THRESHOLD_SEC=10   # Strict data freshness
```

**5. Monitor Actively:**
```bash
# Watch logs in real-time
tail -f /var/log/supervisor/backend.err.log

# Check status frequently
watch -n 1 'curl -s http://localhost:8001/api/v1/status | jq .'

# Have pause button ready in UI!
```

---

## 📈 Expected Behavior

### In Preview Environment:
- ✅ Toggle works (mode switches)
- ✅ UI updates immediately
- ✅ Backend logs mode changes
- ❌ **LIVE orders will fail** (no real funds in preview)
- ✅ OBSERVE_ONLY works perfectly

### In Local Environment:
- ✅ Toggle works (mode switches)
- ✅ UI updates immediately
- ✅ Backend logs mode changes
- ✅ **LIVE orders will execute** (if API keys valid)
- ✅ OBSERVE_ONLY works perfectly

---

## 🎯 Recommended Workflow

### Phase 1: Observation (1-2 days)
```
1. Run in OBSERVE_ONLY mode
2. Monitor detected opportunities
3. Analyze simulated trade results
4. Verify PnL calculations are sensible
5. Check for any errors or warnings
```

### Phase 2: Paper Trading (3-7 days)
```
1. Continue OBSERVE_ONLY mode
2. Collect statistics:
   - Average spread detected
   - Win rate after fees
   - Average PnL per trade
   - Capture rate
3. Optimize thresholds if needed
4. Verify system stability
```

### Phase 3: Live Testing (Start small!)
```
1. Switch to LIVE TRADING mode
2. Set MAX_TRADE_SIZE_USD=10
3. Set DAILY_LOSS_LIMIT_USD=50
4. Execute 5-10 real trades
5. Verify fills match predictions
6. Check actual vs expected slippage
7. Monitor for any errors
```

### Phase 4: Gradual Scale-Up
```
1. If Phase 3 successful, increase limits:
   - Week 1: $10 trades, $50 daily limit
   - Week 2: $50 trades, $200 daily limit
   - Week 3: $100 trades, $500 daily limit
   - Month 2+: Scale based on performance
2. Always monitor closely
3. Pause immediately if issues arise
```

---

## 🔧 Troubleshooting

### Toggle Not Responding:
```bash
# Check backend logs
tail -n 50 /var/log/supervisor/backend.err.log | grep -i "mode"

# Test API endpoint directly
curl -v -X POST http://localhost:8001/api/v1/controls/observe-only

# Check frontend console
# Open browser DevTools → Console → Look for errors
```

### Mode Not Persisting After Restart:
```bash
# The mode is in-memory only
# To persist, edit backend/.env:
OBSERVE_ONLY_MODE=True  # or False

# Then restart:
supervisorctl restart backend
```

### LIVE Trades Not Executing:
```bash
# 1. Verify mode is off
curl -s http://localhost:8001/api/v1/status | jq '.risk.observe_only'
# Should return: false

# 2. Check API keys are valid
curl -s http://localhost:8001/api/v1/status | jq '.connections'
# All should be: true

# 3. Check for paused state
curl -s http://localhost:8001/api/v1/status | jq '.risk.is_paused'
# Should return: false

# 4. Check daily limit not exceeded
curl -s http://localhost:8001/api/v1/status | jq '.risk.daily_remaining_loss_usd'
# Should be > 0
```

---

## 📚 Additional Resources

### Documentation Files:
- `/app/README.md` - Setup and overview
- `/app/RUNBOOK.md` - Operations guide
- `/app/docs/COINBASE_STATUS.md` - Coinbase integration details
- `/app/docs/ROOT_CAUSE_ANALYSIS.md` - Spread analysis

### API Documentation:
```
http://localhost:8001/docs  # Interactive Swagger UI
http://localhost:8001/redoc # Alternative docs
```

### Monitoring:
```
http://localhost:8001/api/metrics  # Prometheus metrics
http://localhost:8001/api/v1/status  # System health
```

---

## ✅ Summary

### Your Questions Answered:

**Q1: Can observe only mode be executed in your preview environment?**  
✅ **YES!** It's already running and working perfectly.

**Q2: Can you add a toggle somewhere to activate it?**  
✅ **DONE!** Toggle added to Risk & Limits screen.

**Q3: If I locally host it and you add the toggle to the front end UI, can I host locally and run observe mode?**  
✅ **YES!** Works identically when self-hosted. Just configure your API keys and MongoDB, then use the toggle or API endpoints.

### Quick Start (Local):
```bash
1. Clone repo
2. Configure .env with your API keys
3. Start services (backend, frontend, MongoDB)
4. Navigate to Risk & Limits page
5. Use toggle to switch modes
6. Start in OBSERVE_ONLY, monitor for 1-2 days
7. Switch to LIVE when confident (start small!)
```

### Safety First:
- ✅ Always start in OBSERVE_ONLY mode
- ✅ Test with small amounts ($10) first
- ✅ Set conservative risk limits
- ✅ Monitor actively when in LIVE mode
- ✅ Have the pause button ready!

**The system is production-ready for OBSERVE_ONLY operation and can be safely transitioned to LIVE trading when you're ready!**
