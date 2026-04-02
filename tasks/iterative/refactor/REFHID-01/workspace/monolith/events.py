"""
Event dispatcher for the pub/sub system.
Do NOT modify this file.
"""
from typing import Callable, Dict, List, Any


class EventDispatcher:
    """Simple synchronous pub/sub event dispatcher."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        """Register a handler for an event."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)

    def publish(self, event: str, payload: Any) -> None:
        """Publish an event to all registered handlers."""
        for handler in self._subscribers.get(event, []):
            handler(payload)

    def clear(self) -> None:
        """Remove all subscribers (useful for testing)."""
        self._subscribers.clear()


# Module-level singleton dispatcher
dispatcher = EventDispatcher()
