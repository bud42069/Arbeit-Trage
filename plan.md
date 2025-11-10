# CEX/DEX Arbitrage Application — Development Plan

## 1) Objectives
- Ship a production-grade cross-venue spot arbitrage system meeting SLOs: p50 ≤ 700ms detect→both fills, p95 ≤ 1.5s; ≥60% capture of eligible windows; ≥99% trade verification; ≤10% partials.
- Solana-first DEX (Helius RPC/WS, direct pool math for x*y=k and CLMM) + Kraken CEX (WS L2 + IOC).
- Monorepo with typed packages, services split by responsibility, event bus fanout, strong observability and runbooks.
- Operator Console (React + shadcn) with dark + lime design, real-time metrics, risk controls, inventory & rebalancing.
- Secure deployment (Helm + Terraform), Postgres/Timescale for trades/windows/configs, Redis for cache/locks, NATS for events.

## 2) Implementation Steps (Phased)

### Phase 1 — Core POC (Isolation; DO NOT proceed until stable)
Goal: Prove end-to-end core: live data → signal → dual-leg exec.try (idempotent) with staleness/risk gating.
Scope & Deliverables:
- Data-plane: Kraken WS L2 (depth=10) local book with staleness guard; Solana pool reads via Helius HTTP + WS accountSubscribe; CLMM + x*y=k price math; bound quotes with slippage cap.
- Signals: compute predicted PnL incl. fees + impact + haircut; emit exec.try on threshold.
- Executor (dry-run first): concurrent dual-leg submission ordering by recent fill reliability; trade idempotency key; retry + backoff; partial hedge logic stub.
- Events: NATS subjects (`cex.bookUpdate`, `dex.poolUpdate`, `dex.boundQuote`, `exec.try`, `exec.result`).
- Storage (POC): repository interface + in-memory/SQLite adapter; Postgres schema drafted.
- Observability: Prometheus counters/histograms; structured logs with correlation-id; basic Grafana dashboard JSON.
- Websearch: validate best-practices for Kraken L2 diffing, Solana CLMM math, idempotent execution, NATS subject design.
- Integration playbooks: Helius, Kraken. Capture required creds; sandbox/devnet routes.
- UI POC: minimal Ops console panel in current React app to show live status/opportunities stream.
User Stories:
1. As an operator, I see live spread and effective size for ASSET/USDT from Kraken↔Solana in <200ms UI staleness.
2. As an operator, I can toggle OBSERVE-ONLY to prevent live orders while still computing exec.try.
3. As an operator, I see a generated idempotency trade key and both legs prepared concurrently.
4. As an operator, I get an auto-pause when WS staleness >10s with a visible banner.
5. As an operator, I view detection latency histogram and recent opportunity count.
Exit Criteria:
- Stable tick→signal latency p50 ≤ 200ms (local), deterministic idempotency, no duplicate exec.try on restart; POC test suite green.
- Call testing agent: unit + basic integration for data/exec/risk.

### Phase 2 — V1 App Development (Build around proven core)
Goal: Stand up services and Operator UI with working CRUD for trades/opportunities/windows and control actions.
Scope & Deliverables:
- Monorepo layout as per spec (apps/*, packages/*). Implement services: data-service, arb-engine, risk-service, inventory-service, gateway-api, scheduler (stubs for canaries), report-service (skeleton).
- Gateway-API (FastAPI): REST: /v1/status, /v1/opportunities, /v1/trades, /v1/windows, /v1/inventory, /v1/controls (pause/resume/rebalance), /v1/config/{asset}; WS streams: status, opportunities, trades, metrics.
- DB: Postgres/Timescale migrations for core tables; repository pattern (with temporary Mongo adapter in this environment to run UI until Postgres is wired). Redis locks for exec caps; NATS wiring between services.
- UI (React + shadcn, following /app/design_guidelines.md):
  - Screens: Overview, Opportunities, Execution Monitor, Trades, Inventory, Risk, Settings (basic), Metrics.
  - Dark + lime theme tokens; data-testid on all interactive/critical info; Recharts sparklines.
- Observability: Prometheus metrics emitted by each service; OTEL logs; basic Grafana dashboards.
- Security: JWT (short TTL) on Gateway with scopes (read, trade, admin); service mTLS planned (stubbed for local).
User Stories:
1. As an operator, I monitor live opportunities table with filters and row details slide-over.
2. As an operator, I pause/resume the engine from the UI and see effect within 1s.
3. As an operator, I view recent trades with realized vs predicted PnL and latency per leg.
4. As an operator, I see venue health pills (Kraken, Solana) with staleness and RTT.
5. As an operator, I export trades CSV from the ledger for a date range.
Exit Criteria:
- Full e2e flow: data→signal→(observe/execute)→persist→UI updates; REST/WS documented; dashboards render.
- Call testing agent: e2e playwright + backend API tests; fix failures.

### Phase 3 — Feature Expansion (Risk, Inventory, Sizing, Rebalance)
Goal: Production risk capsule, inventory tracking and auto/alert rebalancing; sizing caps tuned.
Scope & Deliverables:
- Risk-service: daily caps (notional, trades, loss%), prediction-error gate, anomaly detection (Xσ/Ys), per-asset capsules; kill-switch banners + toasts.
- Inventory-service: per-venue balances, drift ratio; planner with cost estimate (fees, impact, bridge); modes: alert/auto; schedule into low-vol windows.
- Executor: dynamic sizing `min(cex_depth_cap, dex_impact_cap, inventory_caps, max_notional)`; DEX priority fee percentile-of-last-N; partial hedge overlay.
- Aggregator fallback: Jupiter bound quotes with timestamp and route id; latency delta logging.
- Reports: weekly/TOD profiles; window stats; CSV/Parquet export.
User Stories:
1. As an operator, I set per-asset loss/daily caps and see a preview of what would be paused.
2. As an operator, I view inventory drift per venue and receive actionable rebalance plans.
3. As an operator, I enable auto-rebalance in a specified time window and confirm execution.
4. As an operator, I analyze window heatmap and adjust aggressiveness multipliers.
5. As an operator, I compare realized vs predicted PnL scatter for selected trades.
Exit Criteria:
- Risk gates demonstrably pause on violations; rebalance plans executable; sizing caps respected; reports populated.
- Call testing agent: scenario tests (chaos: WS drop, tx fail), risk gates, rebalance planner.

### Phase 4 — Hardening, Ops, and Security (Production)
Goal: Meet SLOs reliably with full observability, CI/CD, and secure deploys.
Scope & Deliverables:
- CI/CD: GitHub Actions (ruff/mypy, eslint/tsc, unit/integration, Trivy, sign images); staged Helm deploy; e2e smoke; manual prod approval.
- IaC: Terraform (VPC, EKS, RDS/Timescale, Elasticache, NATS/Kafka, ECR, IAM, Secrets/Vault). Helm chart with HPA, PDB, PodSecurity, resources.
- Observability: Prometheus metrics full set; Loki(optional) logs; Grafana dashboards (latency p50/p95, capture heatmap, fail/partial, inventory drift, ws staleness).
- Security: mTLS between services; JWT rotate/refresh; RBAC; rate-limit controls; audit logs; secret rotation runbook.
- Reliability: chaos tests (drop WS, delay RPC, random tx fails); 72h staging soak; restart idempotency verified; backup/restore drills.
User Stories:
1. As a platform owner, I deploy to staging via GitHub Actions and promote to prod after green smoke tests.
2. As an SRE, I view latency SLO dashboards and drill into traces/logs for slow paths.
3. As a security admin, I rotate Kraken/Helius secrets without downtime.
4. As an operator, I see kill-switch incidents with reason, timeline, and remediation steps.
5. As a developer, I run replay/backtest jobs from recorded ticks to measure capture rate.
Exit Criteria:
- SLOs met in staging soak, incident rate ≤ target, zero duplicate orders on restarts, runbooks complete.
- Call testing agent: load/latency suite + e2e on staging profile.

## 3) Next Actions (Immediate)
- Confirm credentials: Kraken API keys (sandbox/production), Helius RPC/WS key; approve storing via Vault/SM.
- Approve NATS/Redis/Postgres deployment targets (dev/stage/prod) and data retention policy.
- Confirm initial asset list (≥3 assets) and pool addresses (Whirlpool/Orca) for devnet/mainnet.
- Approve aggregator fallback (Jupiter) and acceptable slippage caps + route pinning policy.
- Confirm UI design spec (use /app/design_guidelines.md) and React (not Next.js) for Operator Console in this environment.

## 4) Success Criteria
- Core verified (Phase 1) with deterministic idempotency; no duplicate exec.try on restarts.
- End-to-end flow operational (Phase 2) with REST/WS, UI, persistence, and basic dashboards.
- Risk, inventory, sizing, and rebalance functioning with measurable improvements in capture and safety (Phase 3).
- Production readiness (Phase 4): SLOs achieved, CI/CD green, IaC applied, observability dashboards actionable, security controls enforced; 7-day prod run with zero critical incidents and ≥500 trades across ≥3 assets, median realized-vs-predicted error ≤ 25%.
