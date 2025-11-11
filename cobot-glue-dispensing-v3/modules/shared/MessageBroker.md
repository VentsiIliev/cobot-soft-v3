# MessageBroker.py

## Overview

Singleton publish-subscribe messaging system enabling decoupled communication between components. Uses weak references for automatic subscriber cleanup and provides error isolation.

## Location

`cobot-soft-glue-dispencing-v2/API/MessageBroker.py`

## Class: MessageBroker

### Pattern

Singleton - only one instance exists across the application.

### Initialization

```python
broker = MessageBroker()  # Always returns the same instance
```

**Implementation**:
```python
def __new__(cls):
    if cls._instance is None:
        cls._instance = super(MessageBroker, cls).__new__(cls)
        cls._instance._init()
    return cls._instance
```

### Attributes

#### subscribers
```python
subscribers: Dict[str, List[weakref.ref]]
```

**Type**: Dictionary mapping topic names to lists of weak references to subscriber callbacks.

**Purpose**: Stores all subscriptions with automatic garbage collection of dead subscribers.

#### logger
```python
logger: logging.Logger
```

**Type**: Logger instance for the MessageBroker class.

**Purpose**: Logs subscription, publication, and error events.

## Methods

### subscribe(topic, callback)

Subscribe a callback function to a topic.

**Signature**:
```python
def subscribe(self, topic: str, callback: Callable) -> None
```

**Parameters**:
- `topic` (str): Topic name to subscribe to
- `callback` (Callable): Function or method to call when topic is published

**Returns**: None

**Behavior**:
1. Creates topic in subscribers dict if not exists
2. Creates weak reference to callback
3. Registers cleanup function for when callback is garbage collected
4. Adds weak reference to topic's subscriber list
5. Logs subscription

**Weak Reference Handling**:
- For bound methods: Uses `weakref.WeakMethod`
- For functions: Uses `weakref.ref`
- Cleanup callback removes dead references automatically

**Example**:
```python
def handle_state(state):
    print(f"State: {state}")

broker.subscribe("system/state", handle_state)
```

**Example with Method**:
```python
class MyClass:
    def __init__(self):
        broker = MessageBroker()
        broker.subscribe("system/state", self.handle_state)
    
    def handle_state(self, state):
        print(f"State: {state}")
```

### unsubscribe(topic, callback)

Manually unsubscribe a callback from a topic.

**Signature**:
```python
def unsubscribe(self, topic: str, callback: Callable) -> None
```

**Parameters**:
- `topic` (str): Topic name
- `callback` (Callable): Callback to remove

**Returns**: None

**Behavior**:
1. Checks if topic exists
2. Filters out matching callbacks
3. Removes topic if no subscribers remain
4. Logs number of callbacks removed

**Example**:
```python
broker.unsubscribe("system/state", handle_state)
```

**Note**: Usually not needed due to automatic cleanup via weak references.

### publish(topic, message)

Publish a message to all subscribers of a topic.

**Signature**:
```python
def publish(self, topic: str, message: Any) -> None
```

**Parameters**:
- `topic` (str): Topic name
- `message` (Any): Message data to send (can be any type)

**Returns**: None

**Behavior**:
1. Checks if topic has subscribers
2. Resolves weak references to get live callbacks
3. Calls each live callback with message
4. Catches and logs errors from individual callbacks
5. Continues calling remaining callbacks even if one fails
6. Cleans up dead references
7. Logs success/failure statistics

**Error Isolation**:
```python
for callback in live_callbacks:
    try:
        callback(message)
        successful_calls += 1
    except Exception as e:
        failed_calls += 1
        logger.error(f"Error calling subscriber: {e}")
        # Continue with other subscribers
```

**Example**:
```python
broker.publish("system/state", {
    "state": "running",
    "progress": 50
})
```

### request(topic, message, timeout)

Synchronous request-response pattern.

**Signature**:
```python
def request(self, topic: str, message: Any, timeout: float = 1.0) -> Any
```

**Parameters**:
- `topic` (str): Request topic
- `message` (Any): Request data
- `timeout` (float): Response timeout in seconds (default: 1.0)

**Returns**: First non-None response from subscribers, or None if no response

**Behavior**:
1. Publishes message to topic
2. Waits for first non-None response
3. Returns response or None after timeout

**Example**:
```python
response = broker.request("config/get", {"key": "robot_ip"}, timeout=2.0)
if response:
    print(f"Robot IP: {response}")
```

**Note**: Requires subscriber to return a value:
```python
def handle_config_request(request):
    if request['key'] == 'robot_ip':
        return "192.168.1.100"
    return None

broker.subscribe("config/get", handle_config_request)
```

### get_subscriber_count(topic)

Get number of active subscribers for a topic.

**Signature**:
```python
def get_subscriber_count(self, topic: str) -> int
```

**Parameters**:
- `topic` (str): Topic name

**Returns**: int - Number of live subscribers

**Behavior**:
1. Returns 0 if topic doesn't exist
2. Counts only live references (not garbage collected)

**Example**:
```python
count = broker.get_subscriber_count("system/state")
print(f"Subscribers: {count}")
```

### get_all_topics()

Get list of all topics with active subscribers.

**Signature**:
```python
def get_all_topics(self) -> List[str]
```

**Parameters**: None

**Returns**: List[str] - List of topic names

**Example**:
```python
topics = broker.get_all_topics()
print(f"Active topics: {topics}")
```

### clear_topic(topic)

Remove all subscribers from a topic.

**Signature**:
```python
def clear_topic(self, topic: str) -> None
```

**Parameters**:
- `topic` (str): Topic to clear

**Returns**: None

**Behavior**:
1. Removes topic from subscribers dict
2. Logs number of subscribers removed

**Example**:
```python
broker.clear_topic("system/state")
```

## Private Methods

### _init()

Initializes the singleton instance.

**Called By**: `__new__` on first instantiation

**Behavior**:
- Initializes empty subscribers dict
- Creates logger instance

### _cleanup_callback(topic, original_callback)

Creates a cleanup function for weak references.

**Parameters**:
- `topic` (str): Topic name
- `original_callback` (Callable): Original callback being referenced

**Returns**: Callable - Cleanup function

**Behavior**:
- Returns function that removes dead reference when called
- Automatically invoked by Python when referenced object is garbage collected
- Removes empty topics

**Implementation**:
```python
def cleanup(weak_ref):
    if topic in self.subscribers:
        self.subscribers[topic] = [
            ref for ref in self.subscribers[topic]
            if ref is not weak_ref
        ]
        if not self.subscribers[topic]:
            del self.subscribers[topic]
```

## Usage Patterns

### Basic Pub/Sub

```python
# Publisher
broker = MessageBroker()
broker.publish("events/button-clicked", {"button": "start"})

# Subscriber
def on_button_click(data):
    print(f"Button clicked: {data['button']}")

broker.subscribe("events/button-clicked", on_button_click)
```

### State Updates

```python
# Publisher (in service)
class RobotService:
    def update_state(self, new_state):
        broker = MessageBroker()
        broker.publish("robot/state", new_state)

# Subscriber (in UI)
class DashboardWidget:
    def __init__(self):
        broker = MessageBroker()
        broker.subscribe("robot/state", self.on_robot_state_change)
    
    def on_robot_state_change(self, state):
        self.update_indicator(state)
```

### Multiple Subscribers

```python
def logger_handler(message):
    logging.info(f"Message: {message}")

def ui_handler(message):
    ui.update(message)

def database_handler(message):
    db.store(message)

# All receive the same message
broker.subscribe("data/update", logger_handler)
broker.subscribe("data/update", ui_handler)
broker.subscribe("data/update", database_handler)

broker.publish("data/update", {"value": 42})
```

## Thread Safety

The MessageBroker is generally thread-safe for:
- Publishing from different threads
- Subscribing from different threads

**Note**: Callbacks are executed in the publishing thread.

## Memory Management

### Automatic Cleanup

Weak references automatically clean up when:
- Subscriber object is deleted
- Method owner object is garbage collected
- Function goes out of scope

**Example**:
```python
class Widget:
    def __init__(self):
        broker.subscribe("topic", self.handler)
    
    def handler(self, msg):
        print(msg)

widget = Widget()
# ... use widget ...
del widget  # Subscription automatically removed
```

### Manual Cleanup

For long-lived applications, manually unsubscribe:
```python
broker.unsubscribe("topic", handler)
```

## Performance Considerations

### Subscription Cost

- O(1) topic lookup
- O(n) for filtering live references (n = subscribers)

### Publishing Cost

- O(n) where n = number of subscribers
- Each callback executed synchronously
- Slow callbacks block publishing thread

**Optimization**: Use async callbacks or worker threads for heavy processing.

## Error Handling

### Callback Errors

Errors in callbacks are caught and logged:

```python
def buggy_handler(message):
    raise ValueError("Bug!")

broker.subscribe("topic", buggy_handler)
broker.publish("topic", "data")
# ValueError logged, other subscribers still called
```

### Logging

All operations logged at appropriate levels:
- DEBUG: Subscription details, cleanup events
- INFO: Normal operations
- WARNING: Failed callback calls
- ERROR: Exceptions in callbacks

## Testing

### Mock Broker

For unit tests, create a mock:

```python
class MockMessageBroker:
    def __init__(self):
        self.published = []
    
    def publish(self, topic, message):
        self.published.append((topic, message))
    
    def subscribe(self, topic, callback):
        pass
```

### Verify Publications

```python
def test_state_change():
    broker = MessageBroker()
    received = []
    
    def handler(state):
        received.append(state)
    
    broker.subscribe("test/state", handler)
    broker.publish("test/state", "running")
    
    assert received == ["running"]
```

## Common Topics

| Topic | Publisher | Message Format |
|-------|-----------|----------------|
| `system/state` | GlueSprayingApp | `{"state": str, ...}` |
| `robot/state` | RobotService | RobotServiceState |
| `vision-system/state` | VisionSystem | VisionSystemState |
| `vision-system/contours` | VisionSystem | List[Contour] |
| `glue/weights` | GlueDataFetcher | `{"cell1": float, ...}` |
| `robot/trajectory/updateImage` | GlueSprayingApp | `{"image": ndarray}` |

## Best Practices

1. **Use Descriptive Topics**: `"module/component/event"` format
2. **Keep Callbacks Fast**: Offload heavy work to background threads
3. **Handle All Messages**: Don't assume message format
4. **Clean Up**: Unsubscribe when no longer needed (or use weak refs)
5. **Log Errors**: Always log callback errors for debugging

## Related Documentation

- [API/README.md](./README.md) - API module overview
- [Main README](../README.md) - System architecture

---

**File**: API/MessageBroker.py
**Class**: MessageBroker
**Pattern**: Singleton, Publish-Subscribe
**Last Updated**: 2025-11-08
