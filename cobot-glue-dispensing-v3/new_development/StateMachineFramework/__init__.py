"""
Enhanced State Machine Framework

A modular, service-oriented state machine framework with comprehensive features:
- Dependency injection and service container
- Advanced validation with preconditions/postconditions
- Comprehensive error handling with recovery strategies
- Performance monitoring and optimization
- Conditional transitions and guard conditions
- Thread-safe event processing
- Metrics collection and analysis
"""

__version__ = "2.0.0"

# Core components
from .core.state_machine import EnhancedStateMachine, StateMachineConfig
from .core.state import BaseState, StateConfig, ConfigurableState, OperationState, TimedState
from .core.context import BaseContext
from .core.events import BaseEvent, GenericEvent, PriorityEvent, EventQueue
from .core.performance import PerformanceManager

# Builder pattern
from .builders.enhanced_builder import EnhancedStateMachineBuilder, ConditionalTransition

# Services
from .services.enhanced_container import EnhancedServiceContainer
from .services.default_implementations import ServiceFactory
from .services.error_service import ErrorService, EnhancedErrorService
from .services.new_services import (
    TimerService, MetricsService, ValidationService,
    ConfigurationService, SecurityService, NotificationService
)

# Validation
from .validation.validation_result import ValidationResult, ValidationError

# Legacy interfaces for backward compatibility
from .ServiceInterfaces import ServiceContainer, LoggingService, ActionService, EventService

__all__ = [
    # Core
    'EnhancedStateMachine',
    'StateMachineConfig',
    'BaseState',
    'StateConfig',
    'ConfigurableState',
    'OperationState',
    'TimedState',
    'BaseContext',
    'BaseEvent',
    'GenericEvent',
    'PriorityEvent',
    'EventQueue',
    'PerformanceManager',
    
    # Builder
    'EnhancedStateMachineBuilder',
    'ConditionalTransition',
    
    # Services
    'EnhancedServiceContainer',
    'ServiceFactory',
    'ErrorService',
    'EnhancedErrorService',
    'TimerService',
    'MetricsService',
    'ValidationService',
    'ConfigurationService',
    'SecurityService',
    'NotificationService',
    
    # Validation
    'ValidationResult',
    'ValidationError',
    
    # Legacy
    'ServiceContainer',
    'LoggingService',
    'ActionService',
    'EventService',
]