# Enhanced State Machine Framework

A production-ready, modular state machine framework for Python with advanced features including dependency injection, validation, error handling, and performance monitoring.

## ✨ Key Features

- 🏗️ **Modular Architecture** - Clean separation of concerns
- 🔧 **Enhanced Service Container** - Advanced dependency injection with lifecycle management
- ✅ **Comprehensive Validation** - Preconditions, postconditions, and guard conditions
- ⚡ **Performance System** - Built-in monitoring, profiling, and optimization
- 🛡️ **Error Integration** - Comprehensive error handling with recovery strategies
- 🔒 **Thread Safety** - All components designed for concurrent use
- 📊 **Metrics Collection** - Detailed performance and usage analytics

## 🚀 Quick Start

### Installation

The framework is self-contained. Simply import and use:

```python
from StateMachineFramework import EnhancedStateMachineBuilder, BaseContext
```

### Basic Example

```python
# Create and configure state machine
builder = EnhancedStateMachineBuilder()
builder.set_initial_state("IDLE") \
       .add_state("IDLE") \
           .add_transition("START", "RUNNING") \
           .done() \
       .add_state("RUNNING") \
           .add_transition("STOP", "IDLE") \
           .done()

# Build and run
context = BaseContext()
state_machine = builder.build(context)

with state_machine:  # Automatic start/stop
    state_machine.send_event("START")
    print(f"Current state: {state_machine.current_state_name}")
```

### Enhanced Example with Services

```python
from StateMachineFramework import EnhancedStateMachineBuilder, ServiceFactory, BaseContext

# Create enhanced context with all services
context = BaseContext()
services = ServiceFactory.create_default_services()
for service_type, service_instance in services.items():
    context.services.register_singleton(service_type, service_instance)

# Build with enhanced features
builder = EnhancedStateMachineBuilder()
builder.configure_performance(enable_metrics=True, enable_validation=True) \
       .set_initial_state("OPERATIONAL") \
       .add_state("OPERATIONAL") \
           .add_precondition(lambda ctx: ctx.get_data('safety_ok', True), "Safety check") \
           .add_transition("ERROR", "ERROR_RECOVERY") \
           .done() \
       .add_state("ERROR_RECOVERY") \
           .add_transition("RETRY", "OPERATIONAL") \
           .done()

state_machine = builder.build(context)

# Monitor errors
def error_callback(error_context):
    print(f"Error {error_context.code} in {error_context.state}")

with state_machine:
    callback_id = state_machine.add_error_callback(error_callback)
    
    # Your application logic here
    state_machine.send_event("START")
    
    # Get statistics
    stats = state_machine.get_error_statistics()
    print(f"Recovery rate: {stats.get('recovery_success_rate', 0):.1f}%")
```

## 📚 Documentation

- **[ENHANCED_FRAMEWORK_DOCUMENTATION.md](./ENHANCED_FRAMEWORK_DOCUMENTATION.md)** - Complete documentation
- **[examples/comprehensive_usage_example.py](./examples/comprehensive_usage_example.py)** - Full feature demonstration
- **[examples/error_handling_integration_example.py](./examples/error_handling_integration_example.py)** - Error handling demo

## 🏗️ Architecture Overview

```
core/
├── state_machine.py       # Main state machine implementation
├── state.py              # State implementations (Basic, Configurable, Operation, Timed)
├── context.py            # Thread-safe context management
├── events.py             # Event system with priorities
└── performance.py        # Performance monitoring and optimization

builders/
└── enhanced_builder.py   # Fluent API for building state machines

services/
├── enhanced_container.py # Advanced dependency injection container
├── default_implementations.py # Default service implementations
├── error_service.py      # Enhanced error handling service
└── new_services.py       # Service interfaces

validation/
└── validation_result.py  # Validation system

examples/
├── comprehensive_usage_example.py # Complete examples
└── error_handling_integration_example.py # Error handling demo
```

## 🔧 Advanced Features

### State Validation

```python
def safety_check(context):
    return context.get_data('temperature', 0) < 100

builder.add_state("PROCESSING") \
       .add_precondition(safety_check, "Temperature safety check") \
       .add_guard_condition("START", lambda ctx: ctx.get_data('ready', False)) \
       .done()
```

### Performance Monitoring

```python
# Get comprehensive performance report
performance_report = state_machine.performance_manager.get_comprehensive_report()
print(f"Cache hit ratio: {performance_report['cache']['overall']['hit_ratio']:.1f}%")
print(f"Memory usage: {performance_report['resources']['memory']['current_mb']:.1f}MB")
```

### Error Handling

```python
# Monitor and handle errors
stats = state_machine.get_error_statistics()
active_errors = state_machine.get_active_errors()

if state_machine.has_fatal_errors():
    print("Critical errors detected!")
    
# Clear specific errors
state_machine.clear_error(error_code)
```

### Conditional Transitions

```python
from StateMachineFramework import ConditionalTransition

emergency_transition = ConditionalTransition(
    condition=lambda ctx: ctx.get_data('emergency', False),
    target_state="EMERGENCY_STOP",
    priority=1
)

builder.add_conditional_transition("RUNNING", "CHECK", [emergency_transition])
```

## 🧪 Testing

Run the examples to test the framework:

```bash
python examples/comprehensive_usage_example.py
python examples/error_handling_integration_example.py
```

## 📈 Performance

The framework is optimized for:
- **High throughput**: Asynchronous event processing
- **Low latency**: Optimized state transitions
- **Memory efficiency**: Object pooling and cleanup
- **Scalability**: Configurable thread pools and queues

## 🔄 Migration from Legacy

If migrating from the old monolithic `v2.py`:

```python
# Old
from StateMachineFramework.v2 import BaseStateMachine

# New
from StateMachineFramework import EnhancedStateMachine
# or better:
from StateMachineFramework import EnhancedStateMachineBuilder
```

The enhanced framework maintains full backward compatibility while adding significant new features.

## 📝 Version History

- **v2.0.0**: Complete modular refactoring with enhanced features
- **v1.x**: Legacy monolithic implementation (deprecated)

## 🤝 Contributing

This framework is designed to be generic and extensible. To add new features:

1. Follow the modular architecture patterns
2. Add comprehensive tests and examples
3. Update documentation
4. Ensure thread safety and performance

## 📄 License

This framework is part of the cobot-soft project for industrial automation applications.

---

**Enhanced State Machine Framework v2.0.0**  
*Production-ready, modular state machine framework for Python applications*