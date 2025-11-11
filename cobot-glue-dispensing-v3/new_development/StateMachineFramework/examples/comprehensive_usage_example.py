"""
Comprehensive usage examples for the enhanced state machine framework.

This module demonstrates the key features of the modular state machine framework,
including dependency injection, validation, error handling, and performance monitoring.
"""

import time
import sys
import os

# Add the StateMachineFramework to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builders.enhanced_builder import EnhancedStateMachineBuilder, ConditionalTransition
from services.default_implementations import ServiceFactory
from services.enhanced_container import EnhancedServiceContainer
from services.error_service import EnhancedErrorService
from services.new_services import MetricsService, ValidationService
from core.context import BaseContext
from core.performance import PerformanceManager
from validation.validation_result import ValidationResult


def basic_state_machine_example():
    """Demonstrate basic state machine creation and usage."""
    print("=== Basic State Machine Example ===")
    
    # Create enhanced builder
    builder = EnhancedStateMachineBuilder()
    
    # Build a simple state machine
    builder.set_initial_state("IDLE") \
           .add_state("IDLE") \
               .add_transition("START", "RUNNING") \
               .add_entry_action("initialize_system") \
               .done() \
           .add_state("RUNNING") \
               .add_transition("PAUSE", "PAUSED") \
               .add_transition("STOP", "STOPPED") \
               .add_entry_action("start_processing") \
               .done() \
           .add_state("PAUSED") \
               .add_transition("RESUME", "RUNNING") \
               .add_transition("STOP", "STOPPED") \
               .done() \
           .add_state("STOPPED") \
               .add_entry_action("cleanup_resources") \
               .done()
    
    # Create state machine
    context = BaseContext()
    state_machine = builder.build(context)
    
    try:
        # Start and demonstrate basic usage
        state_machine.start()
        print(f"Initial state: {state_machine.current_state_name}")
        
        # Transition through states
        state_machine.send_event("START")
        time.sleep(0.1)
        print(f"After START: {state_machine.current_state_name}")
        
        state_machine.send_event("PAUSE")
        time.sleep(0.1)
        print(f"After PAUSE: {state_machine.current_state_name}")
        
        state_machine.send_event("RESUME")
        time.sleep(0.1)
        print(f"After RESUME: {state_machine.current_state_name}")
        
        state_machine.send_event("STOP")
        time.sleep(0.1)
        print(f"After STOP: {state_machine.current_state_name}")
        
    finally:
        state_machine.stop()
    
    print("Basic example completed successfully!\n")


def enhanced_services_example():
    """Demonstrate enhanced service container and dependency injection."""
    print("=== Enhanced Services Example ===")
    
    # Create enhanced service container
    container = EnhancedServiceContainer()
    
    # Register all default services
    services = ServiceFactory.create_default_services()
    for service_type, service_instance in services.items():
        container.register_singleton(service_type, service_instance)
    
    # Create context with enhanced services
    context = BaseContext()
    context.services = container
    
    # Build state machine with services
    builder = EnhancedStateMachineBuilder()
    builder.set_initial_state("MONITOR") \
           .add_state("MONITOR") \
               .add_transition("ALERT", "ALERTING") \
               .set_timeout(5) \
               .done() \
           .add_state("ALERTING") \
               .add_transition("RESOLVE", "MONITOR") \
               .done() \
           .configure_performance(enable_metrics=True, enable_validation=True)
    
    state_machine = builder.build(context)
    
    try:
        state_machine.start()
        print(f"State machine started with enhanced services")
        
        # Demonstrate service usage
        if state_machine.context.has_service(MetricsService):
            metrics_service = state_machine.context.get_service(MetricsService)
            metrics_service.record_state_entry("MONITOR")
            print("Metrics service is active")
        
        # Let it run for a bit to collect metrics
        time.sleep(2)
        
        # Get performance statistics
        performance_stats = state_machine.performance_manager.get_comprehensive_report()
        print(f"Performance report available with {len(performance_stats)} sections")
        
    finally:
        state_machine.stop()
    
    print("Enhanced services example completed!\n")


def validation_example():
    """Demonstrate validation features."""
    print("=== Validation Example ===")
    
    def temperature_check(context: BaseContext) -> bool:
        """Precondition: Check if temperature is safe."""
        temperature = context.get_data('temperature', 20)
        return 0 <= temperature <= 100
    
    def pressure_check(context: BaseContext) -> bool:
        """Precondition: Check if pressure is within limits."""
        pressure = context.get_data('pressure', 1)
        return 0.5 <= pressure <= 2.0
    
    # Create state machine with validation
    builder = EnhancedStateMachineBuilder()
    builder.set_initial_state("IDLE") \
           .add_state("IDLE") \
               .add_transition("START_PROCESS", "PROCESSING") \
               .done() \
           .add_state("PROCESSING") \
               .add_precondition(temperature_check, "Temperature must be 0-100°C") \
               .add_precondition(pressure_check, "Pressure must be 0.5-2.0 bar") \
               .add_transition("COMPLETE", "IDLE") \
               .done() \
           .configure_performance(enable_validation=True)
    
    context = BaseContext()
    services = ServiceFactory.create_default_services()
    for service_type, service_instance in services.items():
        context.services.register_singleton(service_type, service_instance)
    
    state_machine = builder.build(context)
    
    try:
        state_machine.start()
        
        # Test with valid conditions
        context.set_data('temperature', 50)
        context.set_data('pressure', 1.5)
        
        state_machine.send_event("START_PROCESS")
        time.sleep(0.1)
        print(f"With valid conditions: {state_machine.current_state_name}")
        
        # Reset to idle
        state_machine.send_event("COMPLETE")
        time.sleep(0.1)
        
        # Test with invalid conditions
        context.set_data('temperature', 150)  # Too high
        
        state_machine.send_event("START_PROCESS")
        time.sleep(0.1)
        print(f"With invalid temperature: {state_machine.current_state_name}")
        
    finally:
        state_machine.stop()
    
    print("Validation example completed!\n")


def error_handling_example():
    """Demonstrate comprehensive error handling."""
    print("=== Error Handling Example ===")
    
    # Create state machine with error handling
    builder = EnhancedStateMachineBuilder()
    builder.set_initial_state("OPERATIONAL") \
           .add_state("OPERATIONAL") \
               .add_transition("ERROR", "ERROR_RECOVERY") \
               .add_transition("FAULT", "FAULT_STATE") \
               .done() \
           .add_state("ERROR_RECOVERY") \
               .add_transition("RETRY", "OPERATIONAL") \
               .add_transition("ESCALATE", "FAULT_STATE") \
               .done() \
           .add_state("FAULT_STATE") \
               .add_transition("RESET", "OPERATIONAL") \
               .done() \
           .add_error_recovery("OPERATIONAL", "ERROR_RECOVERY") \
           .add_error_recovery("ERROR_RECOVERY", "FAULT_STATE")
    
    context = BaseContext()
    services = ServiceFactory.create_default_services()
    for service_type, service_instance in services.items():
        context.services.register_singleton(service_type, service_instance)
    
    state_machine = builder.build(context)
    
    # Add error callback to monitor errors
    def error_monitor(error_context):
        print(f"Error detected: Code {error_context.code} in state {error_context.state}")
    
    try:
        state_machine.start()
        error_callback_id = state_machine.add_error_callback(error_monitor)
        
        print(f"Started in state: {state_machine.current_state_name}")
        
        # Simulate an error
        from errorCodesSystem.errorCodes.errorCodes import StateMachineErrorCode
        
        state_machine._handle_error(
            error_code=StateMachineErrorCode.INVALID_TRANSITION,
            state=state_machine.current_state_name,
            additional_data={'operation': 'test_error', 'severity': 'medium'}
        )
        
        time.sleep(0.5)
        
        # Check error statistics
        error_stats = state_machine.get_error_statistics()
        print(f"Total errors handled: {error_stats.get('total_errors', 0)}")
        print(f"Active errors: {error_stats.get('active_errors', 0)}")
        print(f"Recovery success rate: {error_stats.get('recovery_success_rate', 0):.1f}%")
        
        state_machine.remove_error_callback(error_callback_id)
        
    finally:
        state_machine.stop()
    
    print("Error handling example completed!\n")


def conditional_transitions_example():
    """Demonstrate conditional transitions."""
    print("=== Conditional Transitions Example ===")
    
    # Define conditional transitions
    def low_battery_condition(context: BaseContext) -> bool:
        battery_level = context.get_data('battery_level', 100)
        return battery_level < 20
    
    def high_battery_condition(context: BaseContext) -> bool:
        battery_level = context.get_data('battery_level', 100)
        return battery_level >= 80
    
    low_battery_transition = ConditionalTransition(
        condition=low_battery_condition,
        target_state="LOW_POWER",
        priority=1,
        description="Transition to low power mode when battery is low"
    )
    
    high_battery_transition = ConditionalTransition(
        condition=high_battery_condition,
        target_state="HIGH_PERFORMANCE",
        priority=2,
        description="Transition to high performance mode when battery is high"
    )
    
    builder = EnhancedStateMachineBuilder()
    builder.set_initial_state("NORMAL") \
           .add_state("NORMAL") \
               .add_conditional_transition("CHECK_BATTERY", [low_battery_transition, high_battery_transition]) \
               .done() \
           .add_state("LOW_POWER") \
               .add_transition("BATTERY_OK", "NORMAL") \
               .done() \
           .add_state("HIGH_PERFORMANCE") \
               .add_transition("BATTERY_LOW", "NORMAL") \
               .done()
    
    context = BaseContext()
    state_machine = builder.build(context)
    
    try:
        state_machine.start()
        print(f"Started in: {state_machine.current_state_name}")
        
        # Test with different battery levels
        context.set_data('battery_level', 15)  # Low battery
        print(f"Set battery to 15%")
        # Note: Conditional transitions would need additional implementation
        # This is a demonstration of the structure
        
    finally:
        state_machine.stop()
    
    print("Conditional transitions example completed!\n")


def performance_monitoring_example():
    """Demonstrate performance monitoring."""
    print("=== Performance Monitoring Example ===")
    
    builder = EnhancedStateMachineBuilder()
    builder.set_initial_state("WORKING") \
           .add_state("WORKING") \
               .add_transition("PROCESS", "PROCESSING") \
               .done() \
           .add_state("PROCESSING") \
               .add_transition("DONE", "WORKING") \
               .set_timeout(2) \
               .done() \
           .configure_performance(enable_metrics=True, thread_pool_size=4)
    
    context = BaseContext()
    services = ServiceFactory.create_default_services()
    for service_type, service_instance in services.items():
        context.services.register_singleton(service_type, service_instance)
    
    state_machine = builder.build(context)
    
    try:
        state_machine.start()
        
        # Generate some activity for performance monitoring
        for i in range(5):
            state_machine.send_event("PROCESS")
            time.sleep(0.5)
            state_machine.send_event("DONE")
            time.sleep(0.5)
        
        # Get performance report
        performance_report = state_machine.performance_manager.get_comprehensive_report()
        
        print("Performance Report:")
        profiler_data = performance_report.get('profiler', {})
        if profiler_data.get('total_operations', 0) > 0:
            print(f"  Total operations: {profiler_data.get('total_operations', 0)}")
            print(f"  Profiling duration: {profiler_data.get('profiling_duration', 0):.2f}s")
        
        cache_data = performance_report.get('cache', {})
        overall_cache = cache_data.get('overall', {})
        if overall_cache.get('total_hits', 0) > 0:
            print(f"  Cache hit ratio: {overall_cache.get('hit_ratio', 0):.1f}%")
        
        resources_data = performance_report.get('resources', {})
        memory_data = resources_data.get('memory', {})
        if memory_data.get('current_mb', 0) > 0:
            print(f"  Current memory usage: {memory_data.get('current_mb', 0):.1f}MB")
        
    finally:
        state_machine.stop()
    
    print("Performance monitoring example completed!\n")


def main():
    """Run all examples."""
    print("Enhanced State Machine Framework - Comprehensive Examples")
    print("="*60)
    
    examples = [
        basic_state_machine_example,
        enhanced_services_example,
        validation_example,
        error_handling_example,
        conditional_transitions_example,
        performance_monitoring_example
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}\n")
    
    print("All examples completed!")


if __name__ == "__main__":
    main()