# Enhanced State Machine Framework - Complete Documentation

## 🎯 Overview

The Enhanced State Machine Framework is a production-ready, modular system for building robust state machines with comprehensive features including dependency injection, validation, error handling, performance monitoring, and more. This framework has been completely refactored from a monolithic architecture into a clean, modular design following best practices.

## 🏗️ Architecture

### Modular Directory Structure

```
StateMachineFramework/
├── __init__.py                          # Main framework exports
├── core/                                # Core framework components
│   ├── context.py                      # Enhanced context with thread safety
│   ├── events.py                       # Event system with priorities
│   ├── performance.py                  # Performance monitoring & optimization
│   ├── state.py                        # State implementations
│   └── state_machine.py                # Main state machine implementation
├── builders/                           # Builder pattern implementations
│   └── enhanced_builder.py             # Enhanced fluent API builder
├── services/                           # Service-oriented architecture
│   ├── enhanced_container.py           # Advanced DI container
│   ├── default_implementations.py      # Default service implementations
│   ├── error_service.py               # Comprehensive error handling
│   └── new_services.py                # Service interfaces
├── validation/                         # Validation system
│   └── validation_result.py           # Validation results & errors
├── examples/                           # Usage examples
│   ├── comprehensive_usage_example.py  # Complete feature demonstration
│   └── error_handling_integration_example.py # Error handling demo
├── errorCodesSystem/                   # Legacy error system (preserved)
│   ├── contextAndTracking/
│   ├── errorCodes/
│   ├── recoveryStrategies/
│   └── InformationRegistry/
└── ServiceInterfaces.py               # Legacy interfaces (preserved)
```

### Key Architectural Improvements

1. **Modular Design**: Separated concerns into focused modules
2. **Enhanced Service Container**: Advanced DI with lifecycle management  
3. **Performance Monitoring**: Built-in profiling and optimization
4. **Comprehensive Validation**: Preconditions, postconditions, and guard conditions
5. **Thread Safety**: All components designed for concurrent use
6. **Error Integration**: Seamless integration of existing error handling system

## 🚀 Quick Start

### Basic Usage

```python
from StateMachineFramework import EnhancedStateMachineBuilder, BaseContext

# Create and configure state machine
builder = EnhancedStateMachineBuilder()
builder.set_initial_state("IDLE") \
       .add_state("IDLE") \
           .add_transition("START", "RUNNING") \
           .done() \
       .add_state("RUNNING") \
           .add_transition("STOP", "IDLE") \
           .done()

# Build and start
context = BaseContext()
state_machine = builder.build(context)

with state_machine:  # Automatic start/stop
    state_machine.send_event("START")
    # Machine is now in RUNNING state
```

### With Enhanced Services

```python
from StateMachineFramework import (
    EnhancedStateMachineBuilder, 
    ServiceFactory,
    BaseContext
)

# Create enhanced context with all services
context = BaseContext()
services = ServiceFactory.create_default_services()
for service_type, service_instance in services.items():
    context.services.register_singleton(service_type, service_instance)

# Build with enhanced features
builder = EnhancedStateMachineBuilder()
builder.configure_performance(enable_metrics=True, enable_validation=True)
# ... configure states ...

state_machine = builder.build(context)
```

## 🔧 Core Components

### 1. Enhanced State Machine (`core/state_machine.py`)

The main state machine implementation with comprehensive features:

**Key Features:**
- Thread-safe event processing
- Integrated error handling and recovery
- Performance monitoring and metrics
- Validation with caching
- Service integration
- Context management

**Usage Example:**
```python
# Get performance statistics
stats = state_machine.get_error_statistics()
print(f"Recovery rate: {stats['recovery_success_rate']:.1f}%")

# Monitor for fatal errors
if state_machine.has_fatal_errors():
    print("Critical errors detected!")
    
# Add error notification
callback_id = state_machine.add_error_callback(my_error_handler)
```

### 2. Enhanced Builder Pattern (`builders/enhanced_builder.py`)

Fluent API for building complex state machines with validation:

**Features:**
- Conditional transitions based on context
- Guard conditions for state entry/exit
- Built-in configuration validation
- Metadata support
- Performance tuning options

**Usage Example:**
```python
def temperature_check(context):
    return context.get_data('temperature', 0) < 100

builder = EnhancedStateMachineBuilder()
builder.add_state("PROCESSING") \
       .add_precondition(temperature_check, "Temperature safety check") \
       .add_guard_condition("START", lambda ctx: ctx.get_data('ready', False)) \
       .set_timeout(30) \
       .done()

# Add conditional transitions
from StateMachineFramework import ConditionalTransition

emergency_condition = ConditionalTransition(
    condition=lambda ctx: ctx.get_data('emergency', False),
    target_state="EMERGENCY_STOP",
    priority=1
)

builder.add_conditional_transition("RUNNING", "CHECK", [emergency_condition])
```

### 3. Service Container (`services/enhanced_container.py`)

Advanced dependency injection container:

**Features:**
- Multiple lifetime scopes (Singleton, Transient, Scoped)
- Service metadata and discovery
- Lifecycle event handling
- Thread-safe registration and resolution

**Usage Example:**
```python
from StateMachineFramework import EnhancedServiceContainer

container = EnhancedServiceContainer()

# Register with metadata
container.register_singleton(
    MyService, 
    MyServiceImpl(),
    metadata={"version": "1.0", "feature": "advanced"}
)

# Register factory
container.register_factory(
    DatabaseService,
    lambda: create_database_connection(),
    lifetime=ServiceLifetime.SCOPED
)

# Query services
db_services = container.get_services_by_metadata({"type": "database"})
```

### 4. Performance System (`core/performance.py`)

Comprehensive performance monitoring and optimization:

**Components:**
- **PerformanceProfiler**: Method-level timing and profiling
- **PerformanceOptimizer**: Caching, batching, and optimization strategies  
- **ResourceMonitor**: System resource usage tracking
- **PerformanceManager**: Unified performance management

**Usage Example:**
```python
# Get comprehensive performance report
performance_report = state_machine.performance_manager.get_comprehensive_report()

print(f"Cache hit ratio: {performance_report['cache']['overall']['hit_ratio']:.1f}%")
print(f"Memory usage: {performance_report['resources']['memory']['current_mb']:.1f}MB")

# Use profiler decorator
@state_machine.performance_manager.profiler.measure("custom_operation")
def my_expensive_operation():
    # ... complex logic ...
    pass
```

### 5. Validation System (`validation/validation_result.py`)

Comprehensive validation with detailed error reporting:

**Features:**
- Fluent validation result building
- Error and warning aggregation
- Field-level validation tracking
- Serializable results

**Usage Example:**
```python
from StateMachineFramework import ValidationResult

def validate_configuration(config):
    result = ValidationResult.success("Initial validation")
    
    if not config.get('initial_state'):
        result.add_error("MISSING_INITIAL", "Initial state required", field="initial_state")
    
    if config.get('timeout', 0) < 0:
        result.add_warning("NEGATIVE_TIMEOUT", "Negative timeout detected", field="timeout")
    
    return result

# Use validation
validation = validate_configuration(my_config)
if not validation.success:
    for error in validation.errors:
        print(f"Error in {error.field}: {error.message}")
```

### 6. Error Service (`services/error_service.py`)

Enhanced error handling with circuit breaker pattern:

**Features:**
- Integration with existing error system
- Circuit breaker for high error rates
- Error callback notifications
- Comprehensive error statistics
- Recovery strategy management

**Usage Example:**
```python
# Add error callback
def on_error(error_context):
    if error_context.code in CRITICAL_ERRORS:
        notify_operations_team(error_context)

callback_id = state_machine.add_error_callback(on_error)

# Get detailed error statistics
stats = state_machine.get_error_statistics()
if stats['error_rate_tracking']:
    for error_code, rate_info in stats['error_rate_tracking'].items():
        if rate_info['rate'] > 10:
            print(f"High error rate for {error_code}: {rate_info['rate']} errors/min")
```

## 🛠️ Advanced Features

### 1. State Validation

States can have preconditions, postconditions, and guard conditions:

```python
def safety_precondition(context):
    return context.get_data('safety_systems_ok', False)

def completion_postcondition(context):
    return context.get_data('operation_complete', False)

builder.add_state("CRITICAL_OPERATION") \
       .add_precondition(safety_precondition, "Safety systems must be operational") \
       .add_postcondition(completion_postcondition, "Operation must complete successfully") \
       .add_guard_condition("ABORT", lambda ctx: ctx.get_data('can_abort', True)) \
       .done()
```

### 2. Performance Optimization

Built-in optimization features:

```python
# Configure performance options
builder.configure_performance(
    max_queue_size=5000,      # Larger event queue
    thread_pool_size=8,       # More worker threads  
    enable_metrics=True,      # Collect detailed metrics
    enable_validation=True    # Enable validation with caching
)

# Use caching for expensive operations
@state_machine.performance_manager.optimizer.create_lru_cache(maxsize=512)
def expensive_calculation(input_data):
    # Complex computation
    return result
```

### 3. Custom Services

Create and register custom services:

```python
from StateMachineFramework.services.new_services import NotificationService

class EmailNotificationService(NotificationService):
    def send_notification(self, message, level="info", recipients=None):
        # Custom email implementation
        send_email(recipients, f"[{level}] {message}")
        return True
    
    def subscribe_to_state_changes(self, callback):
        # Custom subscription logic
        return subscription_id

# Register custom service
context.services.register_singleton(
    NotificationService, 
    EmailNotificationService(),
    metadata={"type": "email", "priority": "high"}
)
```

### 4. Conditional Logic

Implement complex conditional transitions:

```python
from StateMachineFramework import ConditionalTransition

# Define conditions
def is_maintenance_mode(context):
    return context.get_data('maintenance_mode', False)

def is_high_load(context):
    cpu_usage = context.get_data('cpu_usage', 0)
    memory_usage = context.get_data('memory_usage', 0)
    return cpu_usage > 80 or memory_usage > 90

# Create conditional transitions
maintenance_transition = ConditionalTransition(
    condition=is_maintenance_mode,
    target_state="MAINTENANCE",
    priority=1,
    description="Enter maintenance mode when scheduled"
)

overload_transition = ConditionalTransition(
    condition=is_high_load,
    target_state="THROTTLED",
    priority=2,
    description="Throttle when system is overloaded"
)

# Apply to state
builder.add_state("NORMAL_OPERATION") \
       .add_conditional_transition("SYSTEM_CHECK", [maintenance_transition, overload_transition]) \
       .done()
```

## 📊 Performance Considerations

### Memory Usage

The framework is designed for efficient memory usage:
- Object pooling for frequently created objects
- Weak references to prevent circular dependencies
- Configurable cache sizes with LRU eviction
- Automatic cleanup of expired data

### Thread Safety

All components are thread-safe:
- RLock usage for fine-grained locking
- Lock-free algorithms where possible
- Thread-safe collections
- Proper resource cleanup

### Scalability

Designed to handle high-throughput scenarios:
- Asynchronous event processing
- Configurable thread pools
- Batch processing capabilities
- Priority-based event queues

## 🔍 Migration Guide

### From Legacy v2.py

The monolithic v2.py has been refactored into the modular architecture. Here's how to migrate:

**Old Code:**
```python
from StateMachineFramework.v2 import BaseStateMachine, StateMachineConfig
```

**New Code:**
```python
from StateMachineFramework import EnhancedStateMachine, StateMachineConfig
# or use the builder pattern (recommended)
from StateMachineFramework import EnhancedStateMachineBuilder
```

**Service Registration:**
```python
# Old
container = ServiceContainer()
container.register_singleton(MyService, MyServiceImpl())

# New (enhanced features)
from StateMachineFramework import EnhancedServiceContainer
container = EnhancedServiceContainer()
container.register_singleton(
    MyService, 
    MyServiceImpl(),
    metadata={"component": "business_logic"}
)
```

### Backward Compatibility

The framework maintains compatibility with existing code:
- Legacy service interfaces are preserved
- Error handling system is fully integrated
- Existing state and transition logic works unchanged
- Gradual migration is supported

## 🧪 Testing

### Unit Testing

The modular architecture makes unit testing straightforward:

```python
import unittest
from StateMachineFramework import EnhancedStateMachineBuilder, BaseContext

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.builder = EnhancedStateMachineBuilder()
        self.context = BaseContext()
    
    def test_basic_transitions(self):
        # Build simple state machine
        self.builder.set_initial_state("A") \
                   .add_state("A").add_transition("GO", "B").done() \
                   .add_state("B").done()
        
        sm = self.builder.build(self.context)
        
        with sm:
            self.assertEqual(sm.current_state_name, "A")
            sm.send_event("GO")
            time.sleep(0.1)  # Allow event processing
            self.assertEqual(sm.current_state_name, "B")
```

### Integration Testing

Test service integration:

```python
def test_error_service_integration(self):
    from StateMachineFramework import ServiceFactory
    
    # Setup services
    services = ServiceFactory.create_default_services()
    for service_type, service_instance in services.items():
        self.context.services.register_singleton(service_type, service_instance)
    
    sm = self.builder.build(self.context)
    
    # Test error handling
    error_callback_called = False
    def error_handler(error_context):
        nonlocal error_callback_called
        error_callback_called = True
    
    with sm:
        callback_id = sm.add_error_callback(error_handler)
        
        # Trigger error
        sm._handle_error(123, "TEST_STATE", {"test": True})
        
        time.sleep(0.1)
        self.assertTrue(error_callback_called)
```

## 📈 Monitoring and Observability

### Metrics Collection

Built-in metrics provide comprehensive insight:

```python
# State-level metrics
state_metrics = state_machine.context.get_service(MetricsService)
if state_metrics:
    metrics = state_metrics.get_state_metrics("PROCESSING")
    print(f"Average duration: {metrics.average_duration:.2f}s")
    print(f"Error rate: {metrics.error_count}/{metrics.entry_count}")

# System-wide metrics
performance_report = state_machine.performance_manager.get_comprehensive_report()
print(f"Total operations: {performance_report['profiler']['total_operations']}")
print(f"Cache efficiency: {performance_report['cache']['overall']['hit_ratio']:.1f}%")
```

### Logging Integration

Custom logging integration:

```python
import logging

class CustomLoggingService(LoggingService):
    def __init__(self):
        self.logger = logging.getLogger('StateMachine')
    
    def log_state_change(self, from_state, to_state, data):
        self.logger.info(f"State transition: {from_state} → {to_state}", extra=data)
    
    def log_error(self, message, state, data):
        self.logger.error(f"Error in {state}: {message}", extra=data)

# Register custom logging
context.services.register_singleton(LoggingService, CustomLoggingService())
```

## 🎯 Best Practices

### 1. State Design
- Keep states focused on single responsibilities
- Use meaningful state names that describe the system condition
- Implement proper entry/exit actions for resource management
- Use timeouts for states that might hang

### 2. Error Handling
- Always implement error recovery strategies
- Use circuit breaker pattern for external dependencies
- Monitor error rates and patterns
- Provide meaningful error messages

### 3. Performance
- Use caching for expensive operations
- Monitor memory usage and implement cleanup
- Configure thread pools based on workload
- Use batch processing for bulk operations

### 4. Validation
- Implement preconditions for critical operations
- Use guard conditions to prevent invalid transitions
- Validate configuration early and often
- Provide detailed validation messages

### 5. Service Design
- Follow dependency injection principles
- Keep services stateless when possible
- Use appropriate service lifetimes
- Document service contracts clearly

## 🔮 Future Enhancements

Potential areas for future development:

1. **Visual State Machine Designer**: GUI tool for designing state machines
2. **Distributed State Machines**: Support for state machines across multiple processes
3. **State Persistence**: Automatic state persistence and recovery
4. **Hot Reloading**: Dynamic state machine reconfiguration
5. **Advanced Analytics**: Machine learning-based performance optimization
6. **Cloud Integration**: Native cloud service integrations
7. **WebSocket API**: Real-time state machine monitoring
8. **State Machine Composition**: Hierarchical and parallel state machines

## 📚 API Reference

### Core Classes

- **EnhancedStateMachine**: Main state machine implementation
- **EnhancedStateMachineBuilder**: Fluent builder for state machine configuration
- **BaseContext**: Thread-safe context for state data and services
- **EnhancedServiceContainer**: Advanced dependency injection container
- **ValidationResult**: Comprehensive validation result handling
- **PerformanceManager**: Performance monitoring and optimization

### Service Interfaces

- **TimerService**: State timeout and scheduled event management
- **MetricsService**: State and transition metrics collection
- **ValidationService**: State and transition validation
- **ErrorService**: Enhanced error handling and recovery
- **NotificationService**: Event notifications and callbacks
- **SecurityService**: Access control and authorization

### Utility Classes

- **ConditionalTransition**: Conditional state transitions
- **PerformanceProfiler**: Method-level performance profiling
- **ResourceMonitor**: System resource monitoring
- **ValidationError**: Detailed validation error information

For complete API documentation, see the docstrings in each module and the comprehensive usage examples.

---

*Enhanced State Machine Framework v2.0.0*  
*Production-ready, modular state machine framework for Python applications*