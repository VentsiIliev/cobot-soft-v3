# State Machine Framework - Updated Documentation

## 📌 Important Notice

This framework has been **completely refactored and enhanced** from the original monolithic design. 

**Please refer to the new comprehensive documentation:**
👉 [**ENHANCED_FRAMEWORK_DOCUMENTATION.md**](./ENHANCED_FRAMEWORK_DOCUMENTATION.md)

## 🔄 What Changed

The original monolithic `v2.py` (823 lines) has been refactored into a modern, modular architecture:

### Before (Original):
- Single 823-line file with everything
- Basic dependency injection
- Limited error integration
- No performance monitoring
- Basic validation

### After (Enhanced):
- **Modular Architecture**: Clean separation of concerns
- **Enhanced Service Container**: Advanced DI with lifecycle management
- **Comprehensive Validation**: Preconditions, postconditions, guard conditions
- **Performance System**: Built-in monitoring and optimization
- **Error Integration**: Seamless integration with existing error system
- **Thread Safety**: All components designed for concurrent use
- **Production Ready**: Comprehensive testing and documentation

## 📂 New Structure

```
StateMachineFramework/
├── core/                    # Core components
├── builders/               # Builder pattern
├── services/               # Service architecture
├── validation/            # Validation system  
├── examples/              # Usage examples
└── errorCodesSystem/      # Preserved legacy system
```

## 🚀 Quick Migration

**Old Code:**
```python
from StateMachineFramework.v2 import BaseStateMachine
```

**New Code:**
```python
from StateMachineFramework import EnhancedStateMachine
# or better yet, use the builder:
from StateMachineFramework import EnhancedStateMachineBuilder
```

## 📖 Documentation

For complete documentation, examples, and API reference, see:
**[ENHANCED_FRAMEWORK_DOCUMENTATION.md](./ENHANCED_FRAMEWORK_DOCUMENTATION.md)**

---

*The legacy monolithic implementation has been completely replaced with a modern, maintainable architecture while preserving all existing functionality and adding significant enhancements.*