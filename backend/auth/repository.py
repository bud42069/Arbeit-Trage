"""User repository for database operations."""
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from auth.models import User, UserCreate, UserRole
from auth.jwt import get_password_hash
import repositories.db as db_module


class UserRepository:
    """Repository for user data operations."""
    
    def __init__(self):
        self.collection: Optional[AsyncIOMotorCollection] = None
    
    async def _ensure_collection(self):
        """Ensure collection is initialized."""
        if self.collection is None:
            if db_module.db is None:
                await db_module.init_repositories()
            self.collection = db_module.db["users"]
            
            # Create indexes
            await self.collection.create_index("username", unique=True)
            await self.collection.create_index("email", unique=True)
            await self.collection.create_index("api_key", unique=True, sparse=True)
    
    async def create(self, user_create: UserCreate) -> User:
        """Create a new user."""
        await self._ensure_collection()
        
        user = User(
            id=str(uuid.uuid4()),
            email=user_create.email,
            username=user_create.username,
            hashed_password=get_password_hash(user_create.password),
            role=user_create.role,
            created_at=datetime.now(timezone.utc)
        )
        
        await self.collection.insert_one(user.model_dump())
        return user
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        await self._ensure_collection()
        
        user_dict = await self.collection.find_one({"username": username})
        if user_dict:
            return User(**user_dict)
        return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        await self._ensure_collection()
        
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            return User(**user_dict)
        return None
    
    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        await self._ensure_collection()
        
        user_dict = await self.collection.find_one({"api_key": api_key})
        if user_dict:
            return User(**user_dict)
        return None
    
    async def update_last_login(self, username: str):
        """Update user's last login timestamp."""
        await self._ensure_collection()
        
        await self.collection.update_one(
            {"username": username},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
    
    async def set_api_key(self, username: str, api_key: str):
        """Set API key for user."""
        await self._ensure_collection()
        
        await self.collection.update_one(
            {"username": username},
            {"$set": {"api_key": api_key}}
        )
    
    async def list_all(self) -> List[User]:
        """List all users."""
        await self._ensure_collection()
        
        cursor = self.collection.find({})
        users = []
        async for user_dict in cursor:
            users.append(User(**user_dict))
        return users
    
    async def delete(self, username: str) -> bool:
        """Delete a user."""
        await self._ensure_collection()
        
        result = await self.collection.delete_one({"username": username})
        return result.deleted_count > 0
    
    async def create_default_admin(self) -> Optional[User]:
        """Create default admin user if no users exist."""
        await self._ensure_collection()
        
        # Check if any users exist
        count = await self.collection.count_documents({})
        if count > 0:
            return None
        
        # Create default admin
        default_admin = UserCreate(
            email="admin@arbitrage.local",
            username="admin",
            password="admin123",  # CHANGE THIS IN PRODUCTION
            role=UserRole.ADMIN
        )
        
        return await self.create(default_admin)


# Global instance
user_repo = UserRepository()
