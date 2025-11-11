"""FastAPI gateway server - REST API + WebSocket."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from shared.types import Trade, Opportunity
from shared.events import event_bus
from repositories.db import init_repositories, trade_repo, opportunity_repo, window_repo
from connectors.gemini_connector import gemini_connector
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting arbitrage application...")
    
    # Initialize database
    await init_repositories()
    
    # Start background tasks
    tasks = [
        asyncio.create_task(gemini_connector.connect_public_ws(["solusd", "btcusd", "ethusd"])),
        asyncio.create_task(solana_connector.subscribe_pool_updates(["mock_pool_1"])),
        asyncio.create_task(monitor_system_status())
    ]
    
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
            
            # Update risk metrics
            risk_status = risk_service.get_status()
            risk_paused.set(1 if risk_status["is_paused"] else 0)
            daily_pnl_usd.set(risk_status["daily_pnl_usd"])
            
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Status monitor error: {e}")
            await asyncio.sleep(5)


# ============= REST Endpoints =============

@app.get("/v1/status")
async def get_status():
    """Get system status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "connections": {
            "gemini": gemini_connector.connected,
            "solana": solana_connector.connected
        },
        "risk": risk_service.get_status(),
        "event_stats": event_bus.get_stats()
    }


@app.get("/v1/opportunities")
async def get_opportunities(limit: int = 100) -> List[dict]:
    """Get recent opportunities."""
    if not opportunity_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    opps = await opportunity_repo.find_recent(limit=limit)
    return [opp.model_dump(mode="json") for opp in opps]


@app.get("/v1/trades")
async def get_trades(asset: Optional[str] = None, limit: int = 100) -> List[dict]:
    """Get recent trades."""
    if not trade_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    if asset:
        trades = await trade_repo.find_by_asset(asset, limit=limit)
    else:
        trades = await trade_repo.find_recent(limit=limit)
    
    return [trade.model_dump(mode="json") for trade in trades]


@app.get("/v1/windows")
async def get_windows(asset: str, limit: int = 50) -> List[dict]:
    """Get trading windows for asset."""
    if not window_repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    windows = await window_repo.find_by_asset(asset, limit=limit)
    return [w.model_dump(mode="json") for w in windows]


class ControlAction(BaseModel):
    action: str
    reason: Optional[str] = None


@app.post("/v1/controls/pause")
async def pause_trading(action: ControlAction):
    """Pause trading."""
    reason = action.reason or "Manual pause"
    await risk_service.trigger_pause(reason)
    return {"status": "paused", "reason": reason}


@app.post("/v1/controls/resume")
async def resume_trading():
    """Resume trading."""
    await risk_service.resume()
    return {"status": "resumed"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


# ============= WebSocket =============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": {
                "connected": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")


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


async def broadcast_trade(trade: Trade):
    await broadcast_to_clients({
        "type": "trade",
        "data": trade.model_dump(mode="json")
    })
    
    # Also persist trade
    if trade_repo:
        await trade_repo.insert(trade)


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
