# CEX/DEX Arbitrage Platform

Production-grade cross-venue spot arbitrage application with institutional operator console.

**Live Demo:** https://arb-signal-system.preview.emergentagent.com

![Status](https://img.shields.io/badge/status-MVP%20Demo-success)
![Completion](https://img.shields.io/badge/completion-85%25-yellow)
![Architecture](https://img.shields.io/badge/architecture-event--driven-blue)

---

## Overview

Real-time arbitrage detection and execution system capturing price discrepancies between centralized exchanges (Gemini, Coinbase Advanced) and Solana DEX pools (Orca, Raydium).

**Key Features:**
- ✅ Live Gemini CEX orderbook streaming
- ✅ Solana DEX pool monitoring (Orca Whirlpool)
- ✅ Event-driven architecture with MongoDB persistence
- ✅ Institutional dark + lime operator console
- ✅ Risk management with kill-switches
- ✅ Prometheus metrics exposure
- ✅ Synthetic opportunity injector for testing

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ / Yarn
- MongoDB (pre-configured in environment)
- Supervisor (process manager)

### Setup

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/cex-dex-arbitrage.git
cd cex-dex-arbitrage

# 2. Configure environment variables
cp backend/.env.template backend/.env
cp frontend/.env.template frontend/.env

# Edit backend/.env and add your API keys:
# - GEMINI_API_KEY / GEMINI_API_SECRET (required)
# - HELIUS_API_KEY (required for Solana)
# - COINBASE_KEY_NAME / COINBASE_PRIVATE_KEY (optional)

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt

# 4. Install frontend dependencies
cd ../frontend
yarn install
```

**Important:** Never commit your `.env` files. Use `.env.template` files as reference.

### Running

```bash
# Start services
supervisorctl start all

# Check status
supervisorctl status

# View logs
tail -f /var/log/supervisor/backend.err.log
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api/v1/status
- Metrics: http://localhost:8001/api/metrics

---

## Testing the Pipeline

### Synthetic Opportunity Injector

Test the complete pipeline without real market conditions:

```bash
# Inject test opportunity with 3% spread
curl -X POST "http://localhost:8001/api/v1/test/inject-opportunity?spread_pct=3.0"

# View opportunities
curl -s "http://localhost:8001/api/v1/opportunities" | jq

# Check UI
# Visit https://arb-signal-system.preview.emergentagent.com/opportunities
```

**Expected Flow:**
1. Creates synthetic opportunity
2. Publishes to event bus
3. Triggers execution engine
4. Persists to MongoDB
5. Displays in UI table

---

## Architecture

### Backend Structure

```
backend/
├── server.py              # FastAPI gateway
├── config.py              # Settings
├── shared/                # Types & events
├── connectors/            # CEX/DEX integrations
├── engines/               # Signal & execution
├── services/              # Risk management
├── repositories/          # MongoDB
└── observability/         # Prometheus
```

### Data Flow

```
Gemini WS ──┐
            ├──> Signal Engine ──> Execution ──> MongoDB
Solana RPC ─┘                          │
                                       └──> WebSocket ──> UI
```

---

## API Endpoints

### Core Endpoints
- `GET /api/v1/status` - System health & connection status
- `GET /api/v1/opportunities` - Detected arbitrage opportunities
- `GET /api/v1/trades` - Trade execution history
- `GET /api/v1/windows` - Trading time windows

### Controls
- `POST /api/v1/controls/pause` - Pause trading
- `POST /api/v1/controls/resume` - Resume trading
- `POST /api/v1/controls/observe-only` - Enable simulation mode
- `POST /api/v1/controls/live-trading` - ⚠️ Enable live trading

### Testing & Monitoring
- `POST /api/v1/test/inject-opportunity` - Inject synthetic opportunity
- `GET /api/metrics` - Prometheus metrics endpoint
- `WebSocket /api/ws` - Real-time updates stream

**Full API Documentation:** [/docs/API.md](/docs/API.md)

---

## Current Status

✅ **Fully Operational:**
- All 3 venues connected (Gemini, Coinbase, Solana)
- Real-time data streaming working
- Signal detection and opportunity identification
- Trade execution (OBSERVE_ONLY mode)
- 2600+ simulated trades in database
- Professional operator console with 6 screens

🚧 **In Development:**
- Additional UI features (Reports, Settings screens)
- Real inventory tracking and auto-rebalancing
- CI/CD pipeline
- Production security hardening

📝 **Phase 4 Complete:**
- ✅ Comprehensive documentation
- ✅ API reference
- ✅ Operator runbook
- ✅ GitHub setup guide

---

## Development Roadmap

### ✅ Phase 1-3: Core System (COMPLETE)
- Multi-venue data ingestion
- Signal detection engine
- Execution engine with OBSERVE_ONLY mode
- Professional operator console
- Risk management & kill-switches

### ✅ Phase 4: Documentation (COMPLETE)
- Comprehensive README & API docs
- Operator runbook with troubleshooting
- GitHub setup guide
- Environment configuration templates

### 🚧 Phase 5: Production Hardening (IN PROGRESS)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Infrastructure as Code (Terraform/Helm)
- [ ] Security hardening (auth, rate limiting)
- [ ] Prometheus alerting rules
- [ ] Load testing & performance optimization

### 📋 Phase 6: Feature Completion
- [ ] Complete UI (Reports, Settings screens)
- [ ] Real inventory tracking
- [ ] Automated balance rebalancing
- [ ] Additional venue integrations
- [ ] Advanced analytics & reporting

### 🔮 Future Enhancements
- Multi-chain support (Ethereum, Polygon)
- Triangular arbitrage detection
- Machine learning for spread prediction
- Advanced risk analytics

---

## Support

**GitHub Repository:** https://github.com/YOUR_USERNAME/cex-dex-arbitrage  
**Issues:** https://github.com/YOUR_USERNAME/cex-dex-arbitrage/issues  
**Documentation:** See comprehensive guides below

### Documentation Index

- **[README.md](/README.md)** - This file (project overview & quick start)
- **[RUNBOOK.md](/RUNBOOK.md)** - Operational procedures & troubleshooting
- **[API.md](/docs/API.md)** - Complete API reference
- **[GITHUB_SETUP.md](/docs/GITHUB_SETUP.md)** - GitHub repository setup guide
- **[design_guidelines.md](/design_guidelines.md)** - UI/UX specifications

---

## Getting Help

- **Quick Start Issues:** See [RUNBOOK.md](/RUNBOOK.md) troubleshooting section
- **API Questions:** Check [API.md](/docs/API.md) for complete reference
- **Setup Problems:** Follow [GITHUB_SETUP.md](/docs/GITHUB_SETUP.md)
- **Bug Reports:** Open an issue on GitHub
- **Feature Requests:** Create a GitHub discussion

---

## License

This project is proprietary software for internal use.

---

**Built for institutional-grade arbitrage trading** ⚡

*Documentation Last Updated: 2025-01-15*
