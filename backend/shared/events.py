"""In-memory event bus for service communication."""
import asyncio
import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """Simple in-memory event bus for POC."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_count: Dict[str, int] = defaultdict(int)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type."""
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type}: {handler.__name__}")
    
    async def publish(self, event_type: str, data: Any) -> None:
        """Publish event to all subscribers."""
        self._event_count[event_type] += 1
        
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            logger.debug(f"No subscribers for {event_type}")
            return
        
        logger.debug(f"Publishing {event_type} to {len(handlers)} handlers")
        
        # Execute handlers concurrently
        tasks = [handler(data) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, int]:
        """Get event statistics."""
        return dict(self._event_count)


# Global event bus instance
event_bus = EventBus()
