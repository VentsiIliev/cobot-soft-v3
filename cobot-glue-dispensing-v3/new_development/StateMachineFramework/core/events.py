"""
Event system for state machine framework.

This module provides the event abstraction and event handling capabilities
for the state machine framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
import time
import threading
import heapq


class BaseEvent(ABC):
    """
    Base class for all events in the state machine framework.

    This abstract class defines the interface for event objects.
    Subclasses must implement the `name` property to provide a unique
    identifier for the event.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the unique name of the event.

        This property must be implemented by subclasses to identify
        the event type.

        Returns:
            str: The name of the event.
        """
        pass

    @property
    def data(self) -> Dict[str, Any]:
        """
        Get event data.
        
        Returns:
            Dict containing event data
        """
        return getattr(self, '_data', {})

    @data.setter
    def data(self, value: Dict[str, Any]) -> None:
        """
        Set event data.
        
        Args:
            value: Event data dictionary
        """
        self._data = value or {}


class GenericEvent(BaseEvent):
    """Generic event implementation with data support."""

    def __init__(self, name: str, data: Dict[str, Any] = None):
        """
        Initialize generic event.
        
        Args:
            name: Event name
            data: Optional event data
        """
        self._name = name
        self._data = data or {}

    @property
    def name(self) -> str:
        """Get event name."""
        return self._name

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"GenericEvent(name='{self._name}', data={self._data})"


@dataclass
class PriorityEvent:
    """Event with priority for priority queue processing."""
    priority: int
    timestamp: float
    event_name: str
    data: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    
    def __lt__(self, other: 'PriorityEvent') -> bool:
        """Priority comparison for heapq."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp

    def to_generic_event(self) -> GenericEvent:
        """Convert to GenericEvent."""
        return GenericEvent(self.event_name, self.data)


class EventQueue:
    """Thread-safe event queue with priority support."""
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize event queue.
        
        Args:
            max_size: Maximum queue size (None for unlimited)
        """
        self._queue: list[PriorityEvent] = []
        self._lock = threading.RLock()
        self._max_size = max_size
        self._dropped_events = 0

    def enqueue(self, event: PriorityEvent) -> bool:
        """
        Add event to queue.
        
        Args:
            event: Event to add
            
        Returns:
            True if added successfully, False if queue is full
        """
        with self._lock:
            if self._max_size and len(self._queue) >= self._max_size:
                self._dropped_events += 1
                return False
            
            heapq.heappush(self._queue, event)
            return True

    def dequeue(self) -> Optional[PriorityEvent]:
        """
        Remove and return highest priority event.
        
        Returns:
            Next event or None if queue is empty
        """
        with self._lock:
            if not self._queue:
                return None
            return heapq.heappop(self._queue)

    def peek(self) -> Optional[PriorityEvent]:
        """
        Get highest priority event without removing it.
        
        Returns:
            Next event or None if queue is empty
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._queue) == 0

    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._queue)

    def clear(self) -> int:
        """
        Clear all events from queue.
        
        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            return count

    def get_dropped_count(self) -> int:
        """Get number of dropped events due to queue being full."""
        with self._lock:
            return self._dropped_events

    def reset_dropped_count(self) -> None:
        """Reset dropped event counter."""
        with self._lock:
            self._dropped_events = 0


class EventManager:
    """Manages event processing and routing."""
    
    def __init__(self, max_queue_size: Optional[int] = 1000):
        """
        Initialize event manager.
        
        Args:
            max_queue_size: Maximum event queue size
        """
        self._queue = EventQueue(max_queue_size)
        self._handlers: Dict[str, list[Callable[[BaseEvent], None]]] = {}
        self._global_handlers: list[Callable[[BaseEvent], None]] = []
        self._lock = threading.RLock()
        self._metrics = {
            'events_processed': 0,
            'events_dropped': 0,
            'handler_errors': 0
        }

    def register_handler(self, event_name: str, handler: Callable[[BaseEvent], None]) -> None:
        """
        Register event handler for specific event type.
        
        Args:
            event_name: Name of event to handle
            handler: Handler function
        """
        with self._lock:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)

    def register_global_handler(self, handler: Callable[[BaseEvent], None]) -> None:
        """
        Register global event handler for all events.
        
        Args:
            handler: Handler function
        """
        with self._lock:
            self._global_handlers.append(handler)

    def unregister_handler(self, event_name: str, handler: Callable[[BaseEvent], None]) -> bool:
        """
        Unregister specific event handler.
        
        Args:
            event_name: Event name
            handler: Handler to remove
            
        Returns:
            True if handler was found and removed
        """
        with self._lock:
            if event_name in self._handlers:
                try:
                    self._handlers[event_name].remove(handler)
                    if not self._handlers[event_name]:
                        del self._handlers[event_name]
                    return True
                except ValueError:
                    pass
            return False

    def emit_event(self, event: BaseEvent, priority: int = 5) -> bool:
        """
        Emit event for processing.
        
        Args:
            event: Event to emit
            priority: Event priority (lower = higher priority)
            
        Returns:
            True if event was queued successfully
        """
        priority_event = PriorityEvent(
            priority=priority,
            timestamp=time.time(),
            event_name=event.name,
            data=event.data
        )
        
        success = self._queue.enqueue(priority_event)
        if not success:
            self._metrics['events_dropped'] += 1
        
        return success

    def process_events(self, max_events: Optional[int] = None) -> int:
        """
        Process queued events.
        
        Args:
            max_events: Maximum number of events to process (None for all)
            
        Returns:
            Number of events processed
        """
        processed = 0
        
        while not self._queue.is_empty():
            if max_events and processed >= max_events:
                break
                
            priority_event = self._queue.dequeue()
            if priority_event:
                event = priority_event.to_generic_event()
                self._handle_event(event)
                processed += 1
                
                # Execute callback if provided
                if priority_event.callback:
                    try:
                        priority_event.callback()
                    except Exception:
                        self._metrics['handler_errors'] += 1
        
        return processed

    def _handle_event(self, event: BaseEvent) -> None:
        """
        Handle a single event by calling all registered handlers.
        
        Args:
            event: Event to handle
        """
        self._metrics['events_processed'] += 1
        
        # Call specific handlers
        with self._lock:
            handlers = self._handlers.get(event.name, []).copy()
            global_handlers = self._global_handlers.copy()
        
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                self._metrics['handler_errors'] += 1
        
        # Call global handlers
        for handler in global_handlers:
            try:
                handler(event)
            except Exception:
                self._metrics['handler_errors'] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event processing metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            **self._metrics,
            'queue_size': self._queue.size(),
            'dropped_events': self._queue.get_dropped_count()
        }

    def clear_queue(self) -> int:
        """
        Clear event queue.
        
        Returns:
            Number of events cleared
        """
        return self._queue.clear()


# Event priority constants
class EventPriority:
    """Standard event priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 5
    LOW = 8
    BACKGROUND = 10