"""MongoDB repositories for data persistence."""
import logging
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings
from shared.types import Trade, Opportunity, Window, InventorySnapshot

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connection and repositories."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongo_url)
            self.db = self.client.get_default_database()
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongo_url}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


class TradeRepository:
    """Repository for trades."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["trades"]
    
    async def insert(self, trade: Trade) -> str:
        """Insert trade."""
        doc = trade.model_dump(mode="json")
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def find_by_id(self, trade_id: str) -> Optional[Trade]:
        """Find trade by ID."""
        doc = await self.collection.find_one({"trade_id": trade_id})
        return Trade(**doc) if doc else None
    
    async def find_recent(self, limit: int = 100) -> List[Trade]:
        """Find recent trades."""
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [Trade(**doc) for doc in docs]
    
    async def find_by_asset(self, asset: str, limit: int = 100) -> List[Trade]:
        """Find trades for asset."""
        cursor = self.collection.find({"asset": asset}).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [Trade(**doc) for doc in docs]


class OpportunityRepository:
    """Repository for opportunities."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["opportunities"]
    
    async def insert(self, opp: Opportunity) -> str:
        """Insert opportunity."""
        doc = opp.model_dump(mode="json")
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def find_recent(self, limit: int = 100) -> List[Opportunity]:
        """Find recent opportunities."""
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [Opportunity(**doc) for doc in docs]


class WindowRepository:
    """Repository for windows."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["windows"]
    
    async def insert(self, window: Window) -> str:
        """Insert window."""
        doc = window.model_dump(mode="json")
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def update(self, window: Window):
        """Update window."""
        await self.collection.update_one(
            {"id": window.id},
            {"$set": window.model_dump(mode="json")},
            upsert=True
        )
    
    async def find_by_asset(self, asset: str, limit: int = 50) -> List[Window]:
        """Find windows for asset."""
        cursor = self.collection.find({"asset": asset}).sort("start_ts", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [Window(**doc) for doc in docs]


class InventoryRepository:
    """Repository for inventory snapshots."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["inventory_snapshots"]
    
    async def insert(self, snapshot: InventorySnapshot) -> str:
        """Insert inventory snapshot."""
        doc = snapshot.model_dump(mode="json")
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def find_latest_by_venue(self, venue: str) -> Optional[InventorySnapshot]:
        """Find latest snapshot for venue."""
        doc = await self.collection.find_one(
            {"venue": venue},
            sort=[("timestamp", -1)]
        )
        return InventorySnapshot(**doc) if doc else None


# Global instances (initialized in server startup)
db_manager = DatabaseManager()
trade_repo: Optional[TradeRepository] = None
opportunity_repo: Optional[OpportunityRepository] = None
window_repo: Optional[WindowRepository] = None
inventory_repo: Optional[InventoryRepository] = None


async def init_repositories():
    """Initialize all repositories."""
    global trade_repo, opportunity_repo, window_repo, inventory_repo
    
    await db_manager.connect()
    
    trade_repo = TradeRepository(db_manager.db)
    opportunity_repo = OpportunityRepository(db_manager.db)
    window_repo = WindowRepository(db_manager.db)
    inventory_repo = InventoryRepository(db_manager.db)
    
    logger.info("Repositories initialized")
