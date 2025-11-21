import logging
import weakref
from typing import Dict, List, Any, Callable


class MessageBroker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageBroker, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.subscribers: Dict[str, List[weakref.ref]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with automatic cleanup of dead references"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []

        # Create weak reference to avoid keeping objects alive
        if hasattr(callback, '__self__'):
            # It's a bound method - use WeakMethod
            weak_callback = weakref.WeakMethod(callback, self._cleanup_callback(topic, callback))
        else:
            # It's a function - use regular weak reference
            weak_callback = weakref.ref(callback, self._cleanup_callback(topic, callback))

        self.subscribers[topic].append(weak_callback)
        print(f"Subscribed to topic '{topic}' with callback {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")
        self.logger.debug(f"Subscribed to topic '{topic}'. Total subscribers: {len(self.subscribers[topic])}")

    def _cleanup_callback(self, topic: str, original_callback: Callable):
        """Create a cleanup function that removes dead references"""

        def cleanup(weak_ref):
            if topic in self.subscribers:
                # Remove the dead reference
                self.subscribers[topic] = [
                    ref for ref in self.subscribers[topic]
                    if ref is not weak_ref
                ]
                # Clean up empty topic
                if topic in self.subscribers and not self.subscribers[topic]:
                    del self.subscribers[topic]
                self.logger.debug(f"Auto-cleaned up dead reference for topic '{topic}'")

        return cleanup

    def unsubscribe(self, topic: str, callback: Callable):
        """Manually unsubscribe from a topic"""
        if topic not in self.subscribers:
            return

        # Find and remove matching callbacks
        original_count = len(self.subscribers[topic])
        self.subscribers[topic] = [
            ref for ref in self.subscribers[topic]
            if ref() is not None and ref() != callback
        ]

        # Clean up empty topic
        if not self.subscribers[topic]:
            del self.subscribers[topic]

        removed_count = original_count - len(self.subscribers.get(topic, []))
        if removed_count > 0:
            self.logger.debug(f"Unsubscribed {removed_count} callback(s) from topic '{topic}'")

    def publish(self, topic: str, message: Any):
        """Publish message to all live subscribers"""
        # print(f"[MessageBroker] Publishing to topic '{topic}' message: {message}")

        if topic not in self.subscribers:
            # print(f"[MessageBroker] WARNING: No subscribers for topic '{topic}'")
            self.logger.debug(f"No subscribers for topic '{topic}'")
            return
        # Get all live callbacks and clean up dead ones
        live_callbacks = []
        dead_refs = []

        for weak_ref in self.subscribers[topic]:
            callback = weak_ref()
            if callback is not None:
                live_callbacks.append(callback)
            else:
                dead_refs.append(weak_ref)

        # Remove dead references
        if dead_refs:
            self.subscribers[topic] = [
                ref for ref in self.subscribers[topic]
                if ref not in dead_refs
            ]
            self.logger.debug(f"Cleaned up {len(dead_refs)} dead references for topic '{topic}'")

        # Call all live callbacks
        successful_calls = 0
        failed_calls = 0

        for callback in live_callbacks:
            try:
                self.logger.debug(f"Publishing to topic: '{topic}' message: {message}")
                callback(message)
                successful_calls += 1
            except Exception as e:
                import traceback
                traceback.print_exc()
                failed_calls += 1
                # DEBUG: Show which object/method is causing the error
                callback_info = f"{callback.__self__.__class__.__name__}.{callback.__name__}" if hasattr(callback, '__self__') else str(callback)
                self.logger.error(f"Error calling subscriber for topic '{topic}': {e} [Callback: {callback_info}]")
                # Don't break - continue with other subscribers

        if successful_calls > 0:
            self.logger.debug(f"Successfully published to {successful_calls} subscribers for topic '{topic}'")
        if failed_calls > 0:
            self.logger.warning(f"Failed to publish to {failed_calls} subscribers for topic '{topic}'")

        # Clean up empty topic
        if not self.subscribers[topic]:
            del self.subscribers[topic]

    def get_subscriber_count(self, topic: str) -> int:
        """Get the number of active subscribers for a topic"""
        if topic not in self.subscribers:
            return 0

        # Count only live references
        live_count = sum(1 for ref in self.subscribers[topic] if ref() is not None)
        return live_count

    def get_all_topics(self) -> List[str]:
        """Get list of all topics with active subscribers"""
        return list(self.subscribers.keys())

    def clear_topic(self, topic: str):
        """Clear all subscribers for a specific topic"""
        if topic in self.subscribers:
            count = len(self.subscribers[topic])
            del self.subscribers[topic]
            self.logger.debug(f"Cleared {count} subscribers from topic '{topic}'")

    def request(self, topic: str, message: Any, timeout: float = 1.0):
        """Synchronous request-response pattern - returns first non-None response"""
        if topic not in self.subscribers:
            self.logger.debug(f"No subscribers for request topic '{topic}'")
            return None

        # Get all live callbacks
        live_callbacks = []
        for weak_ref in self.subscribers[topic]:
            callback = weak_ref()
            if callback is not None:
                live_callbacks.append(callback)

        # Call callbacks until we get a non-None response
        for callback in live_callbacks:
            try:
                self.logger.debug(f"Making request to topic: '{topic}' message: {message}")
                result = callback(message)
                if result is not None:
                    self.logger.debug(f"Got response from topic '{topic}': {result}")
                    return result
            except Exception as e:
                self.logger.error(f"Error in request callback for topic '{topic}': {e}")
                continue

        self.logger.debug(f"No response received for request topic '{topic}'")
        return None

    def clear_all(self):
        """Clear all subscribers from all topics"""
        total_cleared = sum(len(subs) for subs in self.subscribers.values())
        self.subscribers.clear()
        self.logger.debug(f"Cleared all {total_cleared} subscribers from all topics")


# Example usage and testing:
if __name__ == "__main__":
    # Set up logging to see what's happening
    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s - %(levelname)s - %(message)s')

    broker1 = MessageBroker()
    broker2 = MessageBroker()

    print(f"broker1 is broker2: {broker1 is broker2}")  # Should print True


    def global_subscriber(msg):
        print(f"Global subscriber got: {msg}")


    class TestObject:
        def __init__(self, name):
            self.name = name

        def method_subscriber(self, msg):
            print(f"{self.name} method subscriber got: {msg}")


    # Test with function
    broker1.subscribe("chat", global_subscriber)

    # Test with method
    obj1 = TestObject("Object1")
    obj2 = TestObject("Object2")

    broker1.subscribe("chat", obj1.method_subscriber)
    broker1.subscribe("chat", obj2.method_subscriber)

    print(f"Subscriber count: {broker1.get_subscriber_count('chat')}")

    # Publish to all
    print("\n--- Publishing to all subscribers ---")
    broker2.publish("chat", "Hello from the singleton broker!")

    # Delete one object
    print("\n--- Deleting obj1 ---")
    del obj1

    # Publish again - should auto-cleanup dead reference
    print("\n--- Publishing after obj1 deletion ---")
    broker2.publish("chat", "Message after obj1 deletion")

    print(f"Subscriber count after cleanup: {broker1.get_subscriber_count('chat')}")

    # Manual unsubscribe
    print("\n--- Manual unsubscribe ---")
    broker1.unsubscribe("chat", global_subscriber)
    broker2.publish("chat", "After manual unsubscribe")


    # Test synchronous request-response
    def transform_service(msg):
        x, y = msg["x"], msg["y"]
        # Simulate coordinate transformation
        return {"transformed_x": x * 2, "transformed_y": y * 2}


    broker1.subscribe("vision/transformToCamera", transform_service)

    print("\n--- Testing synchronous request ---")
    result = broker1.request("vision/transformToCamera", {"x": 10, "y": 20})
    print(f"Transform result: {result}")

    # Test request with no subscribers
    no_result = broker1.request("nonexistent/topic", {"data": "test"})
    print(f"No subscriber result: {no_result}")

    print(f"Final subscriber count: {broker1.get_subscriber_count('chat')}")

