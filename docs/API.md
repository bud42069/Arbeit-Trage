# CEX/DEX Arbitrage Platform - API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8001` (development) | `https://your-domain.com` (production)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Status & Health](#status--health)
3. [Opportunities](#opportunities)
4. [Trades](#trades)
5. [Trading Windows](#trading-windows)
6. [Controls](#controls)
7. [Testing Utilities](#testing-utilities)
8. [Observability](#observability)
9. [WebSocket](#websocket)
10. [Error Responses](#error-responses)

---

## Authentication

**Current Status:** No authentication required (MVP)

**Production Recommendation:** Implement JWT or API key authentication for all control endpoints (`/api/v1/controls/*`)

---

## Status & Health

### Get System Status

Retrieve current system health, connection statuses, risk state, and event statistics.

**Endpoint:** `GET /api/v1/status`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T14:30:00.123456+00:00",
  "version": "1.0.0",
  "connections": {
    "gemini": true,
    "solana": true,
    "coinbase": true
  },
  "risk": {
    "is_paused": false,
    "pause_reason": null,
    "daily_pnl_usd": 125.50,
    "daily_loss_limit_usd": 500.0,
    "max_position_size_usd": 1000.0
  },
  "event_stats": {
    "cex.bookUpdate": 15234,
    "dex.poolUpdate": 4521,
    "signal.opportunity": 42,
    "trade.completed": 8
  }
}
```

**Status Codes:**
- `200 OK` - System healthy
- `503 Service Unavailable` - Critical services down

**Use Cases:**
- Health checks / monitoring
- Dashboard overview
- Connection validation

---

## Opportunities

### Get Recent Opportunities

Retrieve arbitrage opportunities detected by the signal engine.

**Endpoint:** `GET /api/v1/opportunities`

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of opportunities to return

**Request:**
```bash
curl -X GET "http://localhost:8001/api/v1/opportunities?limit=50"
```

**Response:**
```json
{
  "opportunities": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "asset": "SOL-USD",
      "direction": "cex_to_dex",
      "cex_price": "210.50",
      "dex_price": "215.00",
      "spread_pct": "2.14",
      "predicted_pnl_pct": "0.74",
      "size": "100.00",
      "timestamp": "2025-01-15T14:25:30.123456+00:00",
      "window_id": "660e8400-e29b-41d4-a716-446655440001"
    }
  ]
}
```

**Field Descriptions:**
- `direction`: Either `cex_to_dex` (buy CEX, sell DEX) or `dex_to_cex` (buy DEX, sell CEX)
- `spread_pct`: Gross spread before fees
- `predicted_pnl_pct`: Net profit after 1.4% total costs (CEX 0.35% + DEX 0.30% + Slippage 0.75%)
- `size`: Recommended trade size in USD

**Status Codes:**
- `200 OK` - Success
- `503 Service Unavailable` - Database not initialized

---

## Trades

### Get Trade History

Retrieve executed or simulated trades.

**Endpoint:** `GET /api/v1/trades`

**Query Parameters:**
- `asset` (optional) - Filter by asset (e.g., "SOL-USD")
- `limit` (optional, default: 100) - Maximum trades to return (0 = all)

**Request:**
```bash
# Get recent 100 trades
curl -X GET "http://localhost:8001/api/v1/trades"

# Get all SOL-USD trades
curl -X GET "http://localhost:8001/api/v1/trades?asset=SOL-USD&limit=0"
```

**Response:**
```json
{
  "trades": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "asset": "SOL-USD",
      "direction": "cex_to_dex",
      "entry_price": "210.50",
      "exit_price": "215.00",
      "size": "100.00",
      "pnl_usd": "3.10",
      "pnl_pct": "0.74",
      "fees_usd": "1.40",
      "timestamp": "2025-01-15T14:26:00.123456+00:00",
      "opportunity_id": "550e8400-e29b-41d4-a716-446655440000",
      "is_simulated": true
    }
  ],
  "total_count": 2641,
  "limit": 100
}
```

**Field Descriptions:**
- `entry_price`: Price where position was opened
- `exit_price`: Price where position was closed
- `pnl_usd`: Net profit/loss in USD
- `pnl_pct`: Net profit/loss as percentage
- `fees_usd`: Total fees paid (CEX + DEX + slippage)
- `is_simulated`: `true` if OBSERVE_ONLY mode, `false` if real trade

**Status Codes:**
- `200 OK` - Success
- `503 Service Unavailable` - Database not initialized

---

## Trading Windows

### Get Trading Windows

Retrieve time windows where trading was active.

**Endpoint:** `GET /api/v1/windows`

**Query Parameters:**
- `asset` (optional) - Filter by asset
- `limit` (optional, default: 50) - Maximum windows to return

**Request:**
```bash
curl -X GET "http://localhost:8001/api/v1/windows?limit=20"
```

**Response:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "asset": "SOL-USD",
    "start_time": "2025-01-15T14:25:00.000000+00:00",
    "end_time": "2025-01-15T14:26:30.000000+00:00",
    "opportunity_count": 3,
    "trade_count": 1,
    "total_pnl_usd": "3.10"
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `503 Service Unavailable` - Database not initialized

---

## Controls

### Pause Trading

Manually pause all trading activity.

**Endpoint:** `POST /api/v1/controls/pause`

**Request Body:**
```json
{
  "action": "pause",
  "reason": "Manual intervention - investigating wide spread"
}
```

**Response:**
```json
{
  "status": "paused",
  "reason": "Manual intervention - investigating wide spread"
}
```

**Use Cases:**
- Emergency stop during unusual market conditions
- Maintenance or system updates
- Investigation of suspicious opportunities

---

### Resume Trading

Resume trading after manual pause.

**Endpoint:** `POST /api/v1/controls/resume`

**Request:**
```bash
curl -X POST "http://localhost:8001/api/v1/controls/resume"
```

**Response:**
```json
{
  "status": "resumed"
}
```

**Note:** Will not resume if daily loss limit is exceeded. Wait until next day (midnight UTC) for automatic reset.

---

### Enable Observe-Only Mode

Switch to simulation mode (no real orders placed).

**Endpoint:** `POST /api/v1/controls/observe-only`

**Response:**
```json
{
  "status": "observe_only",
  "observe_only_mode": true
}
```

**Effect:**
- All detected opportunities will be simulated
- No real orders sent to exchanges
- Trades marked with `is_simulated: true`
- Safe for testing and monitoring

---

### Enable Live Trading

⚠️ **DANGER**: Switch to live trading mode (real orders placed).

**Endpoint:** `POST /api/v1/controls/live-trading`

**Response:**
```json
{
  "status": "live_trading",
  "observe_only_mode": false
}
```

**Requirements:**
- Valid API keys with trading permissions
- Sufficient account balances on both CEX and DEX
- Risk limits properly configured
- Thoroughly tested in observe-only mode first

**Effect:**
- Real orders will be placed on exchanges
- Real money at risk
- Trades marked with `is_simulated: false`

---

## Testing Utilities

### Inject Test Opportunity

Create a synthetic arbitrage opportunity to test the complete pipeline.

**Endpoint:** `POST /api/v1/test/inject-opportunity`

**Query Parameters:**
- `asset` (optional, default: "SOL-USD") - Asset pair
- `direction` (optional, default: "cex_to_dex") - Trade direction
- `spread_pct` (optional, default: 2.5) - Spread percentage

**Request:**
```bash
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=3.0"
```

**Response:**
```json
{
  "status": "injected",
  "opportunity": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "asset": "SOL-USD",
    "direction": "cex_to_dex",
    "spread_pct": "3.00",
    "predicted_pnl_pct": "1.60"
  },
  "note": "Synthetic opportunity created. Check /v1/opportunities and watch UI."
}
```

**Expected Flow:**
1. Opportunity created and published to event bus
2. Execution engine processes opportunity
3. Trade persisted to database (simulated or real)
4. WebSocket broadcasts update to UI
5. Visible in Opportunities and Trades pages

**Use Cases:**
- End-to-end pipeline testing
- UI development and debugging
- Demonstrating system functionality
- Training and onboarding

---

## Observability

### Prometheus Metrics

Expose metrics for Prometheus scraping.

**Endpoint:** `GET /api/metrics`

**Response Format:** Prometheus text format

**Sample Metrics:**
```
# HELP arb_connection_status Connection status for data venues
# TYPE arb_connection_status gauge
arb_connection_status{venue="gemini"} 1
arb_connection_status{venue="solana"} 1
arb_connection_status{venue="coinbase"} 1

# HELP arb_opportunities_total Total arbitrage opportunities detected
# TYPE arb_opportunities_total counter
arb_opportunities_total{asset="SOL-USD"} 42

# HELP arb_trades_total Total trades executed
# TYPE arb_trades_total counter
arb_trades_total{asset="SOL-USD",direction="cex_to_dex"} 8

# HELP arb_risk_paused Risk service pause status
# TYPE arb_risk_paused gauge
arb_risk_paused 0

# HELP arb_daily_pnl_usd Daily profit and loss in USD
# TYPE arb_daily_pnl_usd gauge
arb_daily_pnl_usd 125.50

# HELP arb_ws_staleness_seconds Time since last WebSocket update
# TYPE arb_ws_staleness_seconds gauge
arb_ws_staleness_seconds{venue="gemini"} 1.234
```

**Integration:**
Add to Prometheus `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'arbitrage'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/api/metrics'
```

---

## WebSocket

### Real-Time Updates

Receive live updates for opportunities and trades.

**Endpoint:** `ws://localhost:8001/api/ws` (development)  
**Endpoint:** `wss://your-domain.com/api/ws` (production)

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8001/api/ws');

ws.onopen = () => {
  console.log('Connected to arbitrage system');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'connected':
      console.log('WebSocket connected:', message.data);
      break;
      
    case 'opportunity':
      console.log('New opportunity:', message.data);
      // Update opportunities table
      break;
      
    case 'trade':
      console.log('New trade:', message.data);
      // Update trades table, refresh PnL
      break;
      
    case 'ping':
      // Heartbeat - connection alive
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Implement reconnection logic
};
```

**Message Types:**

#### Connected
```json
{
  "type": "connected",
  "data": {
    "status": "connected",
    "timestamp": "2025-01-15T14:30:00.123456"
  }
}
```

#### Opportunity
```json
{
  "type": "opportunity",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "asset": "SOL-USD",
    "direction": "cex_to_dex",
    "spread_pct": "2.14",
    "predicted_pnl_pct": "0.74",
    "timestamp": "2025-01-15T14:25:30.123456+00:00"
  }
}
```

#### Trade
```json
{
  "type": "trade",
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "asset": "SOL-USD",
    "pnl_usd": "3.10",
    "pnl_pct": "0.74",
    "is_simulated": true,
    "timestamp": "2025-01-15T14:26:00.123456+00:00"
  }
}
```

#### Ping (Heartbeat)
```json
{
  "type": "ping"
}
```

**Heartbeat:** Server sends ping every 30 seconds to keep connection alive.

---

## Error Responses

### Standard Error Format

All errors return a JSON object with `detail` field.

```json
{
  "detail": "Database not initialized"
}
```

### Common Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Request succeeded |
| `400` | Bad Request | Invalid parameters or request body |
| `404` | Not Found | Endpoint doesn't exist |
| `422` | Unprocessable Entity | Pydantic validation failed |
| `503` | Service Unavailable | Database not connected or service down |
| `500` | Internal Server Error | Unexpected error (check logs) |

### Error Examples

#### Database Not Initialized
```json
{
  "detail": "Database not initialized"
}
```
**Status:** 503  
**Cause:** MongoDB connection failed or repositories not initialized  
**Solution:** Check MongoDB status and restart backend

#### Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```
**Status:** 422  
**Cause:** Invalid query parameter type  
**Solution:** Ensure parameters match expected types

---

## Rate Limiting

**Current Status:** No rate limiting implemented (MVP)

**Production Recommendation:**
- Implement per-IP rate limiting (e.g., 100 requests/minute)
- Stricter limits on control endpoints (10 requests/minute)
- WebSocket connection limits (max 10 concurrent per IP)

---

## API Versioning

All endpoints are versioned under `/api/v1/`

Future versions will be available at `/api/v2/`, `/api/v3/`, etc.

**Deprecation Policy:**
- API versions supported for minimum 6 months after deprecation notice
- Breaking changes always require new version
- Backward-compatible changes may be added to current version

---

## CORS Policy

**Current:** Allow all origins (`*`)

**Production Recommendation:**
```python
allow_origins=[
    "https://your-frontend-domain.com",
    "https://app.your-company.com"
]
```

---

## Additional Resources

- **Setup Guide:** `/app/README.md`
- **Operator Runbook:** `/app/RUNBOOK.md`
- **GitHub Setup:** `/app/docs/GITHUB_SETUP.md`
- **Architecture Plan:** `/app/plan.md`
- **Design Guidelines:** `/app/design_guidelines.md`

---

**API Version:** 1.0.0  
**Last Updated:** 2025-01-15  
**Maintainer:** Development Team
