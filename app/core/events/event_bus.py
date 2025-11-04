from typing import Dict, List, Callable, Awaitable
from app.core.events.base import DomainEvent

class EventBus:
    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        if event.type in self.subscribers:
            for handler in self.subscribers[event.type]:
                # In a real async system, you might want to run these in a non-blocking way
                # For a simple skeleton, direct await is fine.
                await handler(event)

# Global instance for easy access (can be replaced with dependency injection)
event_bus = EventBus()