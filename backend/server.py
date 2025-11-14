"""FastAPI gateway server - REST API + WebSocket."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from shared.types import Trade, Opportunity
from shared.events import event_bus
import repositories.db as db_module
from connectors.gemini_connector import gemini_connector
from connectors.coinbase_connector import init_coinbase_connector
from connectors.solana_connector import solana_connector
from engines.signal_engine import signal_engine
from engines.execution_engine import execution_engine
from services.risk_service import risk_service
from observability.metrics import get_metrics, risk_paused, daily_pnl_usd, connection_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket connections
active_connections: List[WebSocket] = []

# Global reference for Coinbase connector
coinbase_connector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global coinbase_connector
    
    logger.info("Starting arbitrage application...")
    
    # Initialize Coinbase connector
    coinbase_connector = init_coinbase_connector()
    
    # Initialize database
    await db_module.init_repositories()
    
    # Start background tasks
    tasks = [
        asyncio.create_task(gemini_connector.connect_public_ws(["solusd", "btcusd", "ethusd"])),
        # Solana pool monitoring with real Orca Whirlpool SOL/USDC address
        asyncio.create_task(solana_connector.subscribe_pool_updates(["HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"])),
        asyncio.create_task(monitor_system_status())
    ]
    
    # Add Coinbase connector task if enabled
    if coinbase_connector:
        logger.info("Starting Coinbase Advanced connector...")
        # Create connection task
        asyncio.create_task(coinbase_connector.connect_public_ws())
        
        # Wait for connection to establish
        await asyncio.sleep(2)
        
        # Now subscribe to products
        await coinbase_connector.subscribe_orderbook("SOL-USD")
        await coinbase_connector.subscribe_orderbook("BTC-USD")
        await coinbase_connector.subscribe_orderbook("ETH-USD")
        logger.info("✅ Coinbase connector started and subscribed")
    else:
        logger.info("Coinbase connector disabled or not initialized")
    
    logger.info("Application started")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    for task in tasks:
        task.cancel()


app = FastAPI(
    title="CEX/DEX Arbitrage API",
    description="Production-grade arbitrage system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def monitor_system_status():
    """Monitor system status and update metrics."""
    while True:
        try:
            # Update connection status
            connection_status.labels(venue="gemini").set(1 if gemini_connector.connected else 0)
            connection_status.labels(venue="solana").set(1 if solana_connector.connected else 0)
            if coinbase_connector:
                connection_status.labels(venue="coinbase").set(1 if coinbase_connector.connected else 0)
            
            # Update risk metrics
            risk_status = risk_service.get_status()
            risk_paused.set(1 if risk_status["is_paused"] else 0)
            daily_pnl_usd.set(risk_status["daily_pnl_usd"])
            
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Status monitor error: {e}")
            await asyncio.sleep(5)


# ============= REST Endpoints =============

@app.get("/api/v1/status")
async def get_status():
    """Get system status."""
    connections = {
        "gemini": gemini_connector.connected,
        "solana": solana_connector.connected
    }
    
    # Add Coinbase status if enabled
    if coinbase_connector:
        connections["coinbase"] = coinbase_connector.connected
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "connections": connections,
        "risk": risk_service.get_status(),
        "event_stats": event_bus.get_stats()
    }


@app.get("/api/v1/opportunities")
async def get_opportunities(limit: int = 100) -> dict:
    """Get recent opportunities."""
    if not db_module.opportunity_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    opportunities = await db_module.opportunity_repo.find_recent(limit=limit)
    return {"opportunities": [o.model_dump(mode="json") for o in opportunities]}


@app.get("/api/v1/trades")
async def get_trades(
    asset: Optional[str] = None,
    limit: int = 100
) -> dict:
    """Get recent trades with total count."""
    if not db_module.trade_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if asset:
        trades = await db_module.trade_repo.find_by_asset(asset, limit=limit)
    else:
        trades = await db_module.trade_repo.find_recent(limit=limit)
    
    # Get total count from database
    total_count = await db_module.trade_repo.collection.count_documents({})
    
    return {
        "trades": [t.model_dump(mode="json") for t in trades],
        "total_count": total_count,
        "limit": limit
    }


@app.get("/api/v1/windows")
async def get_windows(asset: Optional[str] = None, limit: int = 50) -> List[dict]:
    """Get recent trading windows."""
    if not db_module.window_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if asset:
        windows = await db_module.window_repo.find_by_asset(asset, limit=limit)
    else:
        windows = await db_module.window_repo.find_recent(limit=limit)
    return [w.model_dump(mode="json") for w in windows]


@app.post("/api/v1/test/inject-opportunity")
async def inject_test_opportunity(
    asset: str = "SOL-USD",
    direction: str = "cex_to_dex",
    spread_pct: float = 2.5
):
    """
    TEST ENDPOINT: Inject synthetic opportunity to demonstrate pipeline.
    
    This bypasses real market data detection and creates a fake arbitrage
    opportunity to test signal → execution → UI flow.
    """
    from shared.types import Opportunity
    from decimal import Decimal
    from datetime import datetime, timezone
    import uuid
    
    # Create synthetic opportunity
    opportunity = Opportunity(
        id=str(uuid.uuid4()),
        asset=asset,
        direction=direction,
        cex_price=Decimal("210.50") if direction == "cex_to_dex" else Decimal("215.00"),
        dex_price=Decimal("215.00") if direction == "cex_to_dex" else Decimal("210.50"),
        spread_pct=Decimal(str(spread_pct)),
        predicted_pnl_pct=Decimal(str(spread_pct - 1.4)),  # After 1.4% costs
        size=Decimal("100"),
        timestamp=datetime.now(timezone.utc),
        window_id=str(uuid.uuid4())
    )
    
    # Emit to event bus (triggers execution + UI broadcast)
    await event_bus.publish("signal.opportunity", opportunity)
    
    # Also persist directly
    if db_module.opportunity_repo:
        await db_module.opportunity_repo.insert(opportunity)
    
    return {
        "status": "injected",
        "opportunity": opportunity.model_dump(mode="json"),
        "note": "Synthetic opportunity created. Check /v1/opportunities and watch UI."
    }



class ControlAction(BaseModel):
    action: str
    reason: Optional[str] = None


@app.post("/api/v1/controls/pause")
async def pause_trading(action: ControlAction):
    """Pause trading."""
    reason = action.reason or "Manual pause"
    await risk_service.trigger_pause(reason)
    return {"status": "paused", "reason": reason}


@app.post("/api/v1/controls/resume")
async def resume_trading():
    """Resume trading."""
    await risk_service.resume()
    return {"status": "resumed"}


@app.post("/api/v1/controls/observe-only")
async def enable_observe_only():
    """Enable observe-only mode (simulated trades)."""
    settings.observe_only_mode = True
    logger.info("Switched to OBSERVE ONLY mode")
    return {"status": "observe_only", "observe_only_mode": True}


@app.post("/api/v1/controls/live-trading")
async def enable_live_trading():
    """Enable live trading mode (real trades)."""
    settings.observe_only_mode = False
    logger.warning("⚠️ LIVE TRADING ENABLED - Real orders will be placed!")
    return {"status": "live_trading", "observe_only_mode": False}


@app.get("/api/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


# ============= WebSocket =============

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    logger.info("WebSocket connection attempt received")
    
    try:
        await websocket.accept()
        active_connections.append(websocket)
        
        logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
        
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "data": {
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Keep connection alive with heartbeat
        while True:
            try:
                # Wait for messages or timeout after 30 seconds
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back for debugging
                logger.debug(f"Received from client: {message}")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket cleaned up. Total: {len(active_connections)}")


async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")


# Subscribe to events for WebSocket broadcasts
async def broadcast_opportunity(opp: Opportunity):
    await broadcast_to_clients({
        "type": "opportunity",
        "data": opp.model_dump(mode="json")
    })
    
    # Also persist opportunity
    if db_module.opportunity_repo:
        await db_module.opportunity_repo.insert(opp)
        logger.info(f"Opportunity persisted: {opp.asset} {opp.direction} {opp.predicted_pnl_pct}%")


async def broadcast_trade(trade: Trade):
    await broadcast_to_clients({
        "type": "trade",
        "data": trade.model_dump(mode="json")
    })
    
    # Also persist trade
    if db_module.trade_repo:
        await db_module.trade_repo.insert(trade)


event_bus.subscribe("signal.opportunity", broadcast_opportunity)
event_bus.subscribe("trade.completed", broadcast_trade)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
