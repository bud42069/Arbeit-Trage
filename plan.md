# CEX/DEX Arbitrage Application — Development Plan (Updated)

## 1) Objectives
- Ship a production-grade cross-venue spot arbitrage system meeting SLOs: p50 ≤ 700ms detect→both fills, p95 ≤ 1.5s; ≥60% capture of eligible windows; ≥99% trade verification; ≤10% partials.
- Solana-first DEX (Helius RPC/WS, direct pool math for x*y=k and CLMM) + **NY-compliant CEX stack**: **Coinbase Advanced Trade** (primary) + **Gemini** (co-primary) + **Bitstamp USA** (backup).
- Monorepo with typed packages, services split by responsibility, event bus fanout, strong observability and runbooks.
- Operator Console (React + shadcn) with dark + lime design, real-time metrics, risk controls, inventory & rebalancing.
- Secure deployment (Helm + Terraform), Postgres/Timescale for trades/windows/configs (MongoDB adapter for POC), Redis for cache/locks, NATS for events (in-memory bus for POC).

## 2) Key Architectural Decisions (Updated)

### CEX Venues (NY-Compliant)
- **Primary:** Coinbase Advanced Trade (`/api/v3/brokerage`; Advanced WS for L2 + user fills)
  - Auth: `CB-ACCESS-KEY`, `CB-ACCESS-SIGN`, `CB-ACCESS-TIMESTAMP` (HMAC-SHA256)
  - Products: `SOL-USD`, `SOL-USDC`, `BTC-USD`, `ETH-USD`
  - IOC-style: limit orders with price caps and short TTL
  - **NY limitation:** Multi-network support restricted; plan SOL rail fallback for settlement
- **Co-Primary:** Gemini (`/v1` REST + `/v2/marketdata` WS + `/v1/order/events` private WS)
  - Auth REST: payload base64 + HMAC-SHA384 in `X-GEMINI-SIGNATURE`
  - Auth WS: headers at handshake (cannot auth later)
  - Symbols: `solusd`, `solusdc`, `btcusd`, `ethusd`
  - IOC: `"options":["immediate-or-cancel"]` with `"exchange limit"` type
  - **Settlement advantage:** USDC(SPL) on Solana supported (fast CEX⇄Solana rail)
- **Backup:** Bitstamp USA (NYDFS BitLicense; SOL/USD listed)

### Settlement Rails (NY-Aware)
- **Plan A (preferred):** **Gemini ⇄ Solana USDC(SPL)** for inventory management and quick rebalance
- **Plan B (Coinbase NY):** **SOL** transfer Coinbase⇄Solana → Jupiter swap to USDC on-chain; reverse to refill Coinbase

### DEX Integration
- **Chain:** Solana mainnet/devnet
- **Quote Asset:** USDC(SPL)
- **Router:** Jupiter aggregator with route pinning
- **RPC:** Helius HTTP + WS (`accountSubscribe` for pool updates)
- **Pool Math:** Direct reads for x*y=k (Raydium) and CLMM (Orca Whirlpools)

### Infrastructure (POC-Aware)
- **Storage:** MongoDB (pre-configured in environment) with repository pattern for future Postgres/Timescale migration
- **Events:** In-memory event bus for POC; NATS wiring planned for Phase 2+
- **Cache:** In-memory for POC; Redis planned for Phase 2+
- **Observability:** Prometheus metrics + structured logs + Grafana dashboards

## 3) Implementation Steps (Phased)

### Phase 1 — Core POC (Status: In Progress)
**Goal:** Prove end-to-end core: live data → signal → dual-leg exec.try (idempotent) with staleness/risk gating.

**Scope & Deliverables:**
- **Data-plane:**
  - Coinbase Advanced WS L2 (level2 channel; depth=10) local book with staleness guard
  - Gemini WS L2 (`/v2/marketdata/{symbol}`) local book with staleness guard
  - Solana pool reads via Helius HTTP + WS `accountSubscribe`; CLMM + x*y=k price math
  - Bound quotes with slippage cap and route id pinning
- **Signals:**
  - Compute predicted PnL incl. fees + impact + haircut
  - Emit `exec.try` on threshold breach
  - Window tracking (start/extend/close by grace period)
- **Executor (dry-run first):**
  - Concurrent dual-leg submission ordering by recent fill reliability
  - Trade idempotency key (UUID per opportunity)
  - Retry + exponential backoff
  - Partial hedge logic stub
  - Coinbase: limit IOC-style with price cap = `reference_price * (1 ± ε)`
  - Gemini: `"immediate-or-cancel"` with price cap
- **Events (in-memory bus for POC):**
  - Subjects: `cex.bookUpdate`, `dex.poolUpdate`, `dex.boundQuote`, `exec.try`, `exec.result`
  - Typed event models with correlation-id
- **Storage (POC):**
  - Repository interface with MongoDB adapter
  - Collections: `opportunities`, `trades`, `windows`, `configs`, `inventory_snapshots`
  - Postgres schema drafted for future migration
- **Observability:**
  - Prometheus counters/histograms: latency, opportunities, trades, errors, staleness
  - Structured JSON logs with correlation-id
  - Basic Grafana dashboard JSON (latency p50/p95, opportunity rate, staleness gauges)
- **Integration playbooks:**
  - Call integration agent for Helius, Coinbase Advanced, Gemini
  - Capture required creds (sandbox keys for POC)
  - Document sandbox/devnet routes
- **UI POC:**
  - Minimal Ops console panel in React app
  - Live status indicators (CEX/DEX connection health with pulse animations)
  - Opportunities stream table with filters
  - Recent trades with realized vs predicted PnL
  - Control panel: OBSERVE-ONLY toggle, pause/resume

**User Stories:**
1. As an operator, I see live spread and effective size for SOL/USD from Coinbase+Gemini↔Solana in <200ms UI staleness.
2. As an operator, I can toggle OBSERVE-ONLY to prevent live orders while still computing exec.try.
3. As an operator, I see a generated idempotency trade key and both legs prepared concurrently.
4. As an operator, I get an auto-pause when WS staleness >10s with a visible banner.
5. As an operator, I view detection latency histogram and recent opportunity count.

**Exit Criteria:**
- Stable tick→signal latency p50 ≤ 200ms (local), deterministic idempotency, no duplicate exec.try on restart
- POC test suite green (unit + basic integration for data/exec/risk)
- Call testing agent: unit + basic integration tests
- UI renders live data with <200ms staleness; controls work end-to-end

**Assets for POC:**
- SOL/USD (Coinbase `SOL-USD`, Gemini `solusd`, Solana pools)
- BTC/USD (optional for multi-asset validation)
- ETH/USD (optional for multi-asset validation)

---

### Phase 2 — V1 App Development (Status: Not Started)
**Goal:** Stand up services and Operator UI with working CRUD for trades/opportunities/windows and control actions.

**Scope & Deliverables:**
- **Monorepo layout:**
  - `apps/`: gateway-api, arb-engine, data-service, risk-service, inventory-service, scheduler (stubs), report-service (skeleton)
  - `packages/`: connectors (cex-coinbase, cex-gemini, dex-solana), core-signal, core-exec, core-risk, core-inventory, telemetry, config, shared
- **Gateway-API (FastAPI):**
  - REST: `/v1/status`, `/v1/opportunities`, `/v1/trades`, `/v1/windows`, `/v1/inventory`, `/v1/controls` (pause/resume/rebalance), `/v1/config/{asset}`
  - WS streams: `status`, `opportunities`, `trades`, `metrics`
  - JWT auth with scopes (read, trade, admin); short TTL
- **DB:**
  - MongoDB collections with repository pattern
  - Redis locks for exec caps (or in-memory for POC)
  - NATS wiring between services (or in-memory event bus)
- **UI (React + shadcn, following `/app/design_guidelines.md`):**
  - Screens: Overview, Opportunities, Execution Monitor, Trades, Inventory, Risk, Settings (basic), Metrics
  - Dark + lime theme tokens applied
  - `data-testid` on all interactive/critical info
  - Recharts sparklines for KPIs
  - Status pills: lime=healthy, amber=degraded, red=down with pulse animations
- **Observability:**
  - Prometheus metrics emitted by each service
  - OTEL logs with correlation-id
  - Grafana dashboards: latency, capture rate, venue health, inventory drift
- **Security:**
  - JWT (short TTL) on Gateway with scopes
  - Service mTLS planned (stubbed for local)
  - Rate-limit on control endpoints

**User Stories:**
1. As an operator, I monitor live opportunities table with filters and row details slide-over.
2. As an operator, I pause/resume the engine from the UI and see effect within 1s.
3. As an operator, I view recent trades with realized vs predicted PnL and latency per leg.
4. As an operator, I see venue health pills (Coinbase, Gemini, Solana) with staleness and RTT.
5. As an operator, I export trades CSV from the ledger for a date range.

**Exit Criteria:**
- Full e2e flow: data→signal→(observe/execute)→persist→UI updates
- REST/WS documented (OpenAPI spec)
- Dashboards render with live data
- Call testing agent: e2e playwright + backend API tests; fix failures

---

### Phase 3 — Feature Expansion (Status: Not Started)
**Goal:** Production risk capsule, inventory tracking and auto/alert rebalancing; sizing caps tuned.

**Scope & Deliverables:**
- **Risk-service:**
  - Daily caps (notional, trades, loss%)
  - Prediction-error gate (|realized−predicted| > E% occurs 3× in 10m → OBSERVE-ONLY)
  - Anomaly detection (Xσ/Ys price jumps)
  - Per-asset risk capsules
  - Kill-switch banners + toasts in UI
- **Inventory-service:**
  - Per-venue balances tracking (Coinbase, Gemini, Solana wallet)
  - Drift ratio monitoring (vs thresholds)
  - Rebalance planner with cost estimate (fees, impact, bridge)
  - Modes: alert (default) / auto (execute in low-vol windows)
  - Settlement rail integration: Gemini USDC(SPL) + Coinbase SOL fallback
- **Executor enhancements:**
  - Dynamic sizing: `min(cex_depth_cap, dex_impact_cap, inventory_caps, max_notional)`
  - Book-usage cap (default 30%)
  - DEX priority fee: percentile-of-last-N scaler
  - Partial hedge overlay (immediate hedge on same venue if possible)
- **Aggregator fallback:**
  - Jupiter bound quotes with timestamp and route id
  - Latency delta logging (direct pool vs Jupiter)
  - Fallback policy: use Jupiter if direct pool quote stale >2s
- **Reports:**
  - Weekly/TOD profiles (hot window heatmap)
  - Window stats (signals, trades, dominant direction, max/mean net PnL%)
  - CSV/Parquet export

**User Stories:**
1. As an operator, I set per-asset loss/daily caps and see a preview of what would be paused.
2. As an operator, I view inventory drift per venue and receive actionable rebalance plans.
3. As an operator, I enable auto-rebalance in a specified time window and confirm execution.
4. As an operator, I analyze window heatmap and adjust aggressiveness multipliers.
5. As an operator, I compare realized vs predicted PnL scatter for selected trades.

**Exit Criteria:**
- Risk gates demonstrably pause on violations
- Rebalance plans executable with Gemini USDC(SPL) rail
- Sizing caps respected; book-usage cap enforced
- Reports populated with weekly/TOD data
- Call testing agent: scenario tests (chaos: WS drop, tx fail), risk gates, rebalance planner

---

### Phase 4 — Hardening, Ops, and Security (Status: Not Started)
**Goal:** Meet SLOs reliably with full observability, CI/CD, and secure deploys.

**Scope & Deliverables:**
- **CI/CD:**
  - GitHub Actions: ruff/mypy, eslint/tsc, unit/integration, Trivy scan, sign images
  - Staged Helm deploy (dev→stage→prod)
  - E2e smoke tests in staging
  - Manual prod approval gate
- **IaC:**
  - Terraform: VPC, EKS, RDS/Timescale (or managed Postgres), Elasticache (Redis), NATS/Kafka, ECR, IAM, Secrets Manager/Vault
  - Helm chart: HPA, PodDisruptionBudgets, PodSecurity, resource requests/limits
- **Observability:**
  - Prometheus metrics full set (latency p50/p95, capture rate, fail/partial rates, inventory drift, ws staleness)
  - Loki logs (optional)
  - Grafana dashboards: SLO tracking, capture heatmap, venue health, inventory timeline
- **Security:**
  - mTLS between services
  - JWT rotate/refresh flow
  - RBAC for admin ops
  - Rate-limit on control endpoints
  - Audit logs for config & admin actions
  - Secret rotation runbook (Coinbase, Gemini, Helius keys)
- **Reliability:**
  - Chaos tests: drop WS, delay RPC, random tx fails → kill-switch works
  - 72h staging soak test
  - Restart idempotency verified (no duplicate orders)
  - Backup/restore drills for DB

**User Stories:**
1. As a platform owner, I deploy to staging via GitHub Actions and promote to prod after green smoke tests.
2. As an SRE, I view latency SLO dashboards and drill into traces/logs for slow paths.
3. As a security admin, I rotate Coinbase/Gemini/Helius secrets without downtime.
4. As an operator, I see kill-switch incidents with reason, timeline, and remediation steps.
5. As a developer, I run replay/backtest jobs from recorded ticks to measure capture rate.

**Exit Criteria:**
- SLOs met in staging soak (p50 ≤ 700ms, p95 ≤ 1.5s; ≥60% capture; ≥99% verification; ≤10% partials)
- Incident rate ≤ target (≤1/day kill-switch triggers)
- Zero duplicate orders on restarts
- Runbooks complete (kill-switch, rebalance, secret rotation, incident response)
- Call testing agent: load/latency suite + e2e on staging profile
- **Acceptance:** 7-day prod run with zero critical incidents and ≥500 trades across ≥3 assets, median realized-vs-predicted error ≤ 25%

---

## 4) Next Actions (Immediate)

### Credentials & Access
- [ ] Obtain Coinbase Advanced sandbox keys (for POC connector testing)
- [ ] Obtain Gemini sandbox keys (for POC connector testing)
- [ ] Obtain Helius RPC/WS key (devnet for POC, mainnet for production)
- [ ] Approve storing secrets via environment variables (POC) → Vault/Secrets Manager (production)

### Asset Configuration
- [ ] Confirm initial asset list: SOL/USD (primary), BTC/USD, ETH/USD
- [ ] Provide Solana pool addresses (Whirlpool/Orca) for devnet/mainnet
- [ ] Approve Jupiter aggregator fallback policy and slippage caps (default: 75 bps)

### Infrastructure Decisions
- [ ] Approve MongoDB for POC storage (with Postgres migration path documented)
- [ ] Approve in-memory event bus for POC (with NATS migration path documented)
- [ ] Approve in-memory cache for POC (with Redis migration path documented)
- [ ] Confirm data retention policy (trades: 90d hot, 1y cold; opportunities: 30d; windows: 1y)

### Design & UI
- [ ] Confirm React (not Next.js) for Operator Console in this environment
- [ ] Approve design guidelines at `/app/design_guidelines.md` (dark + lime theme)
- [ ] Review key screens: Overview, Opportunities, Execution Monitor, Trades, Inventory, Risk

---

## 5) Success Criteria (Overall)

### Phase 1 (POC)
- ✅ Core verified with deterministic idempotency; no duplicate exec.try on restarts
- ✅ Stable tick→signal latency p50 ≤ 200ms (local)
- ✅ UI renders live data with <200ms staleness
- ✅ Testing agent validates unit + integration tests

### Phase 2 (V1 App)
- ✅ End-to-end flow operational with REST/WS, UI, persistence, and basic dashboards
- ✅ Full operator console with all key screens functional
- ✅ Testing agent validates e2e playwright + backend API tests

### Phase 3 (Features)
- ✅ Risk gates pause on violations; rebalance plans executable
- ✅ Sizing caps respected; inventory drift monitored
- ✅ Reports populated with weekly/TOD data
- ✅ Testing agent validates scenario tests (chaos, risk gates, rebalance)

### Phase 4 (Production)
- ✅ SLOs achieved in staging soak
- ✅ CI/CD green; IaC applied
- ✅ Observability dashboards actionable
- ✅ Security controls enforced
- ✅ **7-day prod run:** zero critical incidents, ≥500 trades across ≥3 assets, median realized-vs-predicted error ≤ 25%

---

## 6) Key Technical References

### Coinbase Advanced Trade
- **Docs:** https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/
- **Auth:** HMAC-SHA256 (`timestamp + method + requestPath + body`)
- **WS:** `wss://advanced-trade-ws.coinbase.com` (level2, ticker, user channels)
- **Orders:** `POST /api/v3/brokerage/orders` (limit IOC-style with price caps)
- **Sandbox:** Available for connector testing

### Gemini
- **Docs:** https://docs.gemini.com/
- **Auth REST:** payload base64 + HMAC-SHA384 in `X-GEMINI-SIGNATURE`
- **Auth WS:** headers at handshake (cannot auth later)
- **WS Public:** `wss://api.gemini.com/v2/marketdata/{symbol}`
- **WS Private:** `wss://api.gemini.com/v1/order/events`
- **Orders:** `POST /v1/order/new` with `"options":["immediate-or-cancel"]`
- **Settlement:** USDC(SPL) on Solana supported

### Solana / Helius
- **RPC HTTP:** `https://rpc.helius.xyz/?api-key=${HELIUS_API_KEY}`
- **RPC WS:** `wss://rpc.helius.xyz/?api-key=${HELIUS_API_KEY}`
- **accountSubscribe:** Monitor pool account updates for real-time price changes
- **Jupiter:** Aggregator fallback with route pinning

---

## 7) Config Example (Per-Asset)

```yaml
asset: "SOL"
cex_routes:
  - venue: coinbase_advanced
    product: SOL-USD
    taker_fee_bps: 60
    ioc_epsilon_pct: 0.10
    book_depth_levels: 10
    book_usage_cap_pct: 0.30
  - venue: gemini
    symbol: solusd
    taker_fee_bps: 35
    ioc_epsilon_pct: 0.10
    book_depth_levels: 10
    book_usage_cap_pct: 0.30

dex_route:
  chain: solana
  quote: USDC
  pools:
    - program: whirlpool
      pool_address: "<PUBKEY>"
      swap_fee_bps: 30
      slippage_bps_cap: 75
    - program: raydium
      pool_address: "<PUBKEY>"
      swap_fee_bps: 25
      slippage_bps_cap: 75
  aggregator_fallback:
    enabled: true
    provider: jupiter
    stale_threshold_ms: 2000

signal:
  profit_threshold_pct_hot: 1.0
  profit_threshold_pct_cold: 2.0
  slip_haircut_pct: 0.75
  window_grace_sec: 20
  hot_window_utc: [12, 13]

sizing:
  base_notional_quote: 50
  max_notional_quote: 500
  pool_usage_cap_pct: 0.01

risk:
  pnl_error_gate_pct: 0.8
  max_daily_loss_abs: 100
  max_trades_per_window: 5
  anomaly_sigma: 3
  anomaly_window_sec: 60

settlement:
  preferred_rail: gemini_usdc_spl
  fallback_rail: coinbase_sol_jupiter
```

---

**END OF PLAN**
