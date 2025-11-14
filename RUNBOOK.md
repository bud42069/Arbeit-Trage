# CEX/DEX Arbitrage Platform - Operator Runbook

**Version:** 1.0  
**Last Updated:** 2025-11-11  
**System:** Production MVP

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Startup Procedures](#startup-procedures)
3. [Monitoring](#monitoring)
4. [Troubleshooting](#troubleshooting)
5. [Emergency Procedures](#emergency-procedures)
6. [Maintenance](#maintenance)
7. [Configuration](#configuration)

---

## System Overview

### Architecture

```
CEX (Gemini) ──┐
               ├──> Signal Engine ──> Execution Engine ──> MongoDB
DEX (Solana) ──┘           │                   │
                           │                   └──> Event Bus ──> WebSocket
                           └──> Risk Service
```

### Key Components

- **Gemini Connector:** Live L2 orderbook WebSocket streaming
- **Solana Connector:** Pool state monitoring (realistic mock with ±0.8% variance)
- **Signal Engine:** Detects arbitrage opportunities (threshold: 0.1% net after 1.4% costs)
- **Execution Engine:** Dual-leg trade orchestration
- **Risk Service:** Kill-switches, daily limits, staleness monitoring
- **MongoDB:** Opportunities and trades persistence
- **FastAPI:** REST API + WebSocket gateway
- **React UI:** Operator console at preview URL

### Critical Metrics

- **Detection SLO:** p50 ≤ 700ms, p95 ≤ 1.5s
- **Daily Loss Limit:** $500
- **Max Position:** $1,000
- **Staleness Threshold:** 10 seconds
- **Fee Structure:** CEX 0.35% + DEX 0.30% + Slippage 0.75% = **1.4% total**
- **Profit Threshold:** 0.1% net (testing) | 1.0% (production)

---

## Startup Procedures

### Normal Startup

```bash
# 1. Verify MongoDB is running
supervisorctl status

# 2. Check environment variables
cat /app/backend/.env | grep -E "(GEMINI|HELIUS|MONGO)"

# 3. Start all services
supervisorctl start all

# 4. Verify services are running
supervisorctl status
# Expected: backend RUNNING, frontend RUNNING

# 5. Wait 30 seconds for connections to establish

# 6. Check system status
curl -s http://localhost:8001/api/v1/status | jq

# Expected output:
# {
#   "status": "healthy",
#   "connections": {
#     "gemini": true,
#     "solana": true
#   }
# }

# 7. Access UI
# Visit: https://arb-signal-system.preview.emergentagent.com
```

### Post-Deployment Verification

```bash
# Check backend logs for errors
tail -n 100 /var/log/supervisor/backend.err.log | grep ERROR

# Verify Gemini connection
tail -n 50 /var/log/supervisor/backend.err.log | grep "Gemini"
# Should see: "Connected to Gemini" or orderbook updates

# Check event bus activity
curl -s http://localhost:8001/api/v1/status | jq '.event_stats'
# Should show: cex.bookUpdate, dex.poolUpdate, signal.opportunity counts

# Test synthetic injector
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=3.0"

# Verify in UI
# Visit opportunities page, should see injected opportunity
```

---

## Monitoring

### Health Checks

**Primary Health Endpoint:**
```bash
curl -s http://localhost:8001/api/v1/status
```

**Key Indicators:**
- `status`: Should be "healthy"
- `connections.gemini`: Should be `true`
- `connections.solana`: Should be `true`
- `risk.is_paused`: Should be `false` (unless manually paused)
- `event_stats.cex.bookUpdate`: Should be incrementing
- `event_stats.signal.opportunity`: Count of opportunities detected

### Prometheus Metrics

```bash
curl -s http://localhost:8001/api/metrics
```

**Critical Metrics:**
- `arb_connection_status{venue="gemini"}`: Should be 1
- `arb_ws_staleness_seconds{venue="gemini"}`: Should be < 2.0
- `arb_opportunities_total{asset="SOL-USD"}`: Total detected opportunities
- `arb_trades_total{asset="SOL-USD"}`: Total executed trades
- `arb_risk_paused`: Should be 0

### Log Monitoring

**Backend Logs:**
```bash
# Real-time tail
tail -f /var/log/supervisor/backend.err.log

# Check for errors
tail -n 200 /var/log/supervisor/backend.err.log | grep ERROR

# Check for warnings
tail -n 200 /var/log/supervisor/backend.err.log | grep WARNING

# Monitor signal detection
tail -f /var/log/supervisor/backend.err.log | grep "spread detected"

# Monitor executions
tail -f /var/log/supervisor/backend.err.log | grep "Executing"
```

**Frontend Logs:**
```bash
tail -f /var/log/supervisor/frontend.err.log
```

### Database Monitoring

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/arbitrage

# Count opportunities
db.opportunities.countDocuments()

# Count trades
db.trades.countDocuments()

# Recent opportunities
db.opportunities.find().sort({timestamp: -1}).limit(5).pretty()

# Recent trades
db.trades.find().sort({timestamp: -1}).limit(5).pretty()

# Check for duplicates (idempotency verification)
db.trades.aggregate([
  {$group: {_id: "$id", count: {$sum: 1}}},
  {$match: {count: {$gt: 1}}}
])
```

### UI Monitoring

**Visual Checks:**
- Status Pills: Gemini should show "Connected" (lime dot)
- Opportunities Table: Should update every 2-5 seconds
- Overview KPIs: Should reflect current state
- No console errors in browser DevTools

---

## Troubleshooting

### Backend Not Starting

**Symptoms:**
- `supervisorctl status` shows backend as FATAL or BACKOFF
- API not responding on port 8001

**Diagnosis:**
```bash
# Check logs
tail -n 100 /var/log/supervisor/backend.err.log

# Common issues:
# - Missing pydantic-settings: pip install pydantic-settings
# - Invalid .env: Check GEMINI_API_KEY, HELIUS_API_KEY
# - MongoDB not connected: Verify MONGO_URL
# - Port conflict: Check if 8001 is in use
```

**Resolution:**
```bash
# Install missing dependencies
cd /app/backend && pip install -r requirements.txt

# Verify .env exists and has required keys
cat /app/backend/.env | grep -E "(GEMINI_API_KEY|HELIUS_API_KEY|MONGO_URL)"

# Restart
supervisorctl restart backend

# Verify
curl http://localhost:8001/api/v1/status
```

### Gemini Not Connecting

**Symptoms:**
- `connections.gemini`: false
- No `cex.bookUpdate` events
- Status pill shows "Disconnected"

**Diagnosis:**
```bash
# Check Gemini connector logs
tail -n 200 /var/log/supervisor/backend.err.log | grep -i gemini

# Common issues:
# - Invalid API keys
# - Rate limiting
# - Network connectivity
# - WebSocket URL wrong
```

**Resolution:**
```bash
# Verify API keys are valid
# Visit https://exchange.gemini.com/settings/api

# Check Gemini status
curl -s https://status.gemini.com/api/v2/status.json | jq

# Test REST API manually
cd /app/backend
python3 -c "
from connectors.gemini_connector import GeminiConnector
import asyncio
gc = GeminiConnector()
asyncio.run(gc.connect_public_ws(['solusd']))
"

# Restart connector
supervisorctl restart backend
```

### No Opportunities Detected

**Symptoms:**
- `signal.opportunity`: 0 in event stats
- Opportunities page shows "No opportunities detected"
- Logs show price comparisons but no "spread detected"

**Diagnosis:**
```bash
# Check if spread threshold is too high
tail -n 100 /var/log/supervisor/backend.err.log | grep "prices: CEX"

# Look for actual spreads
tail -n 100 /var/log/supervisor/backend.err.log | grep "spread"

# Common causes:
# - Spread < 0.1% + 1.4% costs = not profitable
# - DEX price equals CEX price (no arbitrage)
# - Signal engine threshold too high
```

**Resolution:**
```bash
# Option 1: Use synthetic injector for testing
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=2.0"

# Option 2: Lower threshold temporarily
# Edit /app/backend/engines/signal_engine.py line 131
# Change: threshold_pct = Decimal("0.1") to Decimal("0.01")
# Restart: supervisorctl restart backend

# Option 3: Wait for market volatility
# Real spreads occur during high volatility periods
```

### Database Connection Issues

**Symptoms:**
- "Database not initialized" errors
- API returns 503 errors
- Opportunities/trades not persisting

**Diagnosis:**
```bash
# Check MongoDB status
supervisorctl status | grep mongo
# Or: systemctl status mongod (if using systemd)

# Test MongoDB connection
mongosh mongodb://localhost:27017/arbitrage
# Should connect successfully

# Check repository initialization
tail -n 100 /var/log/supervisor/backend.err.log | grep -i "repository\|mongodb"
```

**Resolution:**
```bash
# Restart MongoDB (if needed)
systemctl restart mongod

# Restart backend
supervisorctl restart backend

# Verify connection
curl http://localhost:8001/api/v1/opportunities
# Should return [] or opportunities, not error
```

### UI Not Loading

**Symptoms:**
- Preview URL shows blank page or errors
- Frontend service shows FATAL

**Diagnosis:**
```bash
# Check frontend logs
tail -n 100 /var/log/supervisor/frontend.err.log

# Common issues:
# - Build errors
# - Missing dependencies
# - API connection failures
```

**Resolution:**
```bash
# Check build
cd /app/frontend
npx esbuild src/ --loader:.js=jsx --bundle --outfile=/dev/null

# Install dependencies
yarn install

# Restart
supervisorctl restart frontend

# Clear browser cache and reload
```

### High CPU Usage

**Symptoms:**
- CPU > 80%
- Slow API responses
- Logs show rapid event processing

**Diagnosis:**
```bash
# Check event rates
curl -s http://localhost:8001/api/v1/status | jq '.event_stats'

# Monitor processes
top -bn1 | grep python
```

**Resolution:**
```bash
# If too many opportunities:
# - Increase threshold in signal_engine.py
# - Add rate limiting to opportunity detection
# - Reduce polling frequency for Solana

# Restart services
supervisorctl restart backend
```

---

## Emergency Procedures

### Kill-Switch Triggered (Staleness)

**Trigger:** WebSocket data gap > 10 seconds

**Symptoms:**
- `risk.is_paused`: true
- Logs show "Risk paused: data staleness"
- UI shows "SYSTEM PAUSED" banner

**Actions:**
1. Verify Gemini connection:
   ```bash
   curl -s https://status.gemini.com/api/v2/status.json | jq
   ```

2. Check network connectivity:
   ```bash
   ping api.gemini.com
   ```

3. Restart backend:
   ```bash
   supervisorctl restart backend
   ```

4. Wait 30 seconds for reconnection

5. Resume trading (if staleness resolved):
   ```bash
   curl -X POST http://localhost:8001/api/v1/controls/resume
   ```

### Daily Loss Limit Reached

**Trigger:** Daily PnL < -$500

**Symptoms:**
- `risk.is_paused`: true
- Logs show "Risk paused: daily loss limit"
- No new trades executing

**Actions:**
1. **DO NOT RESUME** until reviewed

2. Analyze trades:
   ```bash
   curl -s "http://localhost:8001/api/v1/trades" | jq '.trades[] | {asset, pnl_usd, timestamp}'
   ```

3. Review logs for:
   - Execution errors
   - Slippage exceeding expectations
   - Pricing errors

4. If ready to resume (next day):
   ```bash
   # Risk service resets daily PnL at midnight UTC
   curl -X POST http://localhost:8001/api/v1/controls/resume
   ```

### MongoDB Connection Lost

**Symptoms:**
- All API endpoints return 503
- Logs show "Database not initialized"

**Actions:**
1. Check MongoDB status:
   ```bash
   systemctl status mongod
   ```

2. Restart MongoDB if needed:
   ```bash
   systemctl restart mongod
   ```

3. Restart backend:
   ```bash
   supervisorctl restart backend
   ```

4. Verify connection:
   ```bash
   mongosh mongodb://localhost:27017/arbitrage
   ```

### Execution Failures

**Symptoms:**
- Opportunities detected but no trades
- Logs show order placement errors
- "400 Bad Request" from Gemini

**Actions:**
1. Check Gemini API keys:
   ```bash
   # Verify keys are valid and not revoked
   # Visit: https://exchange.gemini.com/settings/api
   ```

2. Check execution logs:
   ```bash
   tail -n 200 /var/log/supervisor/backend.err.log | grep "Executing\|order"
   ```

3. If in OBSERVE_ONLY mode:
   ```bash
   # Check .env
   cat /app/backend/.env | grep OBSERVE_ONLY
   # Should be: OBSERVE_ONLY=false for live trading
   ```

4. Review Gemini order requirements:
   - Minimum order size
   - Price must be within spread
   - Account must have sufficient balance

---

## Maintenance

### Daily Tasks

**Morning Checklist:**
1. Check system status:
   ```bash
   curl -s http://localhost:8001/api/v1/status | jq
   ```

2. Review daily PnL:
   ```bash
   curl -s http://localhost:8001/api/v1/status | jq '.risk.daily_pnl_usd'
   ```

3. Check opportunity count:
   ```bash
   curl -s http://localhost:8001/api/v1/status | jq '.event_stats."signal.opportunity"'
   ```

4. Review recent trades:
   ```bash
   curl -s "http://localhost:8001/api/v1/trades?limit=10" | jq '.trades[] | {asset, pnl_usd, timestamp}'
   ```

5. Verify connections:
   - UI status pills should show Gemini as "Connected"
   - Solana should show "Connected" or "Degraded"

**Evening Review:**
1. Export trades for analysis:
   ```bash
   # Visit UI, navigate to Trades, click "Export CSV"
   ```

2. Review Prometheus metrics:
   ```bash
   curl -s http://localhost:8001/api/metrics | grep arb_
   ```

3. Check MongoDB size:
   ```bash
   mongosh mongodb://localhost:27017/arbitrage --eval "db.stats()"
   ```

### Weekly Tasks

1. **Backup MongoDB:**
   ```bash
   mongodump --uri="mongodb://localhost:27017/arbitrage" --out=/backups/arbitrage_$(date +%Y%m%d)
   ```

2. **Review performance:**
   - Average latency
   - Opportunity capture rate
   - Realized vs predicted PnL accuracy

3. **Update dependencies:**
   ```bash
   cd /app/backend && pip list --outdated
   cd /app/frontend && yarn outdated
   ```

4. **Review logs for patterns:**
   - Repeated errors
   - Connection instability
   - Performance degradation

### Monthly Tasks

1. **Rotate API keys** (security best practice)
2. **Review and update risk limits**
3. **Analyze historical data** for optimization
4. **Update documentation** with new learnings

---

## Configuration

### Adjusting Risk Parameters

**Edit `/app/backend/.env`:**

```env
# Increase daily loss limit
DAILY_LOSS_LIMIT_USD=1000  # From 500

# Increase max position
MAX_POSITION_USD=2000  # From 1000

# Enable observe-only mode (no executions)
OBSERVE_ONLY=true

# Enable auto-rebalancing
AUTO_REBALANCE=true
```

**After changes:**
```bash
supervisorctl restart backend
```

### Adjusting Profit Threshold

**Edit `/app/backend/engines/signal_engine.py` line ~131:**

```python
# For production (conservative)
threshold_pct = Decimal("1.0")  # 1.0% net after costs

# For testing (aggressive)
threshold_pct = Decimal("0.1")  # 0.1% net after costs
```

**After changes:**
```bash
supervisorctl restart backend
```

### Adding New Assets

1. **Update .env:**
   ```env
   ASSET_LIST=SOL-USD,BTC-USD,ETH-USD,AVAX-USD
   ```

2. **Subscribe to Gemini symbols:**
   Edit `/app/backend/server.py` lifespan:
   ```python
   await gemini_connector.connect_public_ws(["solusd", "btcusd", "ethusd", "avaxusd"])
   ```

3. **Add Solana pools:**
   Configure additional pool addresses in `.env`

4. **Restart:**
   ```bash
   supervisorctl restart backend
   ```

---

## Common Scenarios

### Scenario: Wide Spread Detected (>5%)

**Action:**
1. **PAUSE IMMEDIATELY:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/controls/pause
   ```

2. **Investigate:**
   - Check if CEX or DEX price is stale
   - Verify both venues show similar prices on their websites
   - Could be data error, not real opportunity

3. **Verify prices:**
   ```bash
   # Check Gemini directly
   curl -s "https://api.gemini.com/v1/pubticker/solusd" | jq

   # Check CoinGecko
   curl -s "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd" | jq
   ```

4. **Resume only if verified real:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/controls/resume
   ```

### Scenario: No Opportunities for 1+ Hour

**Possible Causes:**
1. **Market is tight** - Normal during low volatility
2. **Threshold too high** - Reduce from 1.0% to 0.5% for testing
3. **DEX price not updating** - Check Solana connector logs
4. **Signal engine stopped** - Check event bus subscriptions

**Actions:**
```bash
# Verify signal engine is running
tail -n 100 /var/log/supervisor/backend.err.log | grep "SignalEngine"

# Check if comparisons happening
tail -n 100 /var/log/supervisor/backend.err.log | grep "prices: CEX"

# Inject test opportunity
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=2.0"
```

### Scenario: Execution Errors

**Symptoms:**
- Opportunities detected but no trades in ledger
- Logs show Gemini 400/401 errors

**Actions:**
1. Check order placement logs:
   ```bash
   tail -n 200 /var/log/supervisor/backend.err.log | grep "order"
   ```

2. Verify API keys:
   - Not revoked
   - Have trading permissions
   - Account funded

3. Check minimum order sizes:
   - Gemini has minimum notional requirements
   - Verify trade size meets minimums

4. Review Gemini API response:
   ```bash
   # Look for error messages in logs
   tail -n 100 /var/log/supervisor/backend.err.log | grep "Gemini order"
   ```

---

## Performance Tuning

### Reducing Event Volume

If CPU usage is high due to excessive opportunities:

1. **Increase profit threshold:**
   ```python
   # In signal_engine.py
   threshold_pct = Decimal("0.5")  # From 0.1%
   ```

2. **Add minimum spread filter:**
   ```python
   # In signal_engine.py, before fee deductions
   if spread_pct < Decimal("1.0"):
       return  # Skip if gross spread < 1%
   ```

3. **Reduce polling frequency:**
   ```python
   # In solana_connector.py
   await asyncio.sleep(5)  # From 2 seconds
   ```

### Optimizing Database

```bash
# Create indexes (if not exists)
mongosh mongodb://localhost:27017/arbitrage <<EOF
db.opportunities.createIndex({timestamp: -1})
db.opportunities.createIndex({asset: 1, timestamp: -1})
db.trades.createIndex({timestamp: -1})
db.trades.createIndex({asset: 1, timestamp: -1})
EOF

# Clean old data (keep last 7 days)
mongosh mongodb://localhost:27017/arbitrage <<EOF
var sevenDaysAgo = new Date(Date.now() - 7*24*60*60*1000);
db.opportunities.deleteMany({timestamp: {\$lt: sevenDaysAgo}});
EOF
```

---

## Security

### API Key Rotation

**Gemini:**
1. Generate new keys at https://exchange.gemini.com/settings/api
2. Update `/app/backend/.env`:
   ```env
   GEMINI_API_KEY=new_key_here
   GEMINI_API_SECRET=new_secret_here
   ```
3. Restart: `supervisorctl restart backend`
4. Verify connection within 30 seconds
5. Revoke old keys after verification

**Helius:**
1. Generate new key at https://dashboard.helius.dev
2. Update `.env` with new key
3. Restart backend
4. Revoke old key

### Access Control

**Current State:** No authentication on API endpoints

**For Production:**
- Add JWT authentication to `/api/v1/controls/*` endpoints
- Implement API key authentication
- Add IP allowlist
- Enable CORS restrictions

---

## Support Contacts

**Technical Issues:**
- Gemini API: https://support.gemini.com
- Helius RPC: https://docs.helius.dev/support
- MongoDB: https://www.mongodb.com/docs/manual/support/

**Internal:**
- GitHub Issues: https://github.com/bud42069/Arbeit-Trage/issues
- Documentation: `/app/README.md`, `/app/design_guidelines.md`
- Architecture Plan: `/app/plan.md`

---

## Appendix

### System Ports

- Backend API: 8001
- Frontend: 3000
- MongoDB: 27017
- Prometheus (if deployed): 9090
- Grafana (if deployed): 3001

### Key File Locations

- Backend: `/app/backend/`
- Frontend: `/app/frontend/`
- Logs: `/var/log/supervisor/`
- Environment: `/app/backend/.env`
- Database: MongoDB at `mongodb://localhost:27017/arbitrage`

### Useful Commands Reference

```bash
# Service Management
supervisorctl status
supervisorctl start <service>
supervisorctl restart <service>
supervisorctl stop <service>
supervisorctl restart all

# Logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
tail -n 100 /var/log/supervisor/backend.err.log | grep ERROR

# API Testing
curl -s http://localhost:8001/api/v1/status | jq
curl -s http://localhost:8001/api/v1/opportunities | jq
curl -s http://localhost:8001/api/v1/trades | jq
curl -X POST http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=3.0

# Database
mongosh mongodb://localhost:27017/arbitrage
db.opportunities.find().sort({timestamp:-1}).limit(10)
db.trades.find().sort({timestamp:-1}).limit(10)
```

---

**End of Runbook**

For additional help, consult:
- `/app/README.md` - Setup and architecture
- `/app/design_guidelines.md` - UI specifications
- `/app/plan.md` - Development roadmap
- GitHub Issues: https://github.com/bud42069/Arbeit-Trage/issues
