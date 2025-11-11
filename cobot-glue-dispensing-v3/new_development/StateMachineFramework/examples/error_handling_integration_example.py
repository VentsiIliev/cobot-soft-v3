"""
Example demonstrating the integrated error handling system.

This example shows how the enhanced error service works with the state machine
to provide comprehensive error handling, recovery, and monitoring.
"""

import time
from typing import Dict, Any

# Add the StateMachineFramework to the path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builders.enhanced_builder import EnhancedStateMachineBuilder
from services.default_implementations import ServiceFactory
from services.error_service import EnhancedErrorService
from core.context import BaseContext
from errorCodesSystem.errorCodes.errorCodes import StateMachineErrorCode, SystemErrorCode


def create_error_callback():
    """Create an error callback for demonstration."""
    def on_error(error_context):
        print(f"Error detected: {error_context.code} in state {error_context.state}")
        print(f"  Additional data: {error_context.additional_data}")
        print(f"  Timestamp: {time.ctime(error_context.timestamp)}")
    
    return on_error


def simulate_system_with_errors():
    """Simulate a system that encounters various errors."""
    
    # Create state machine with enhanced error handling
    builder = EnhancedStateMachineBuilder()
    
    # Configure states with potential error scenarios
    builder.set_initial_state("IDLE") \
           .add_state("IDLE") \
               .add_transition("START", "INITIALIZING") \
               .done() \
           .add_state("INITIALIZING") \
               .add_transition("READY", "RUNNING") \
               .add_transition("ERROR", "ERROR_STATE") \
               .set_timeout(30) \
               .done() \
           .add_state("RUNNING") \
               .add_transition("PROCESS", "PROCESSING") \
               .add_transition("STOP", "STOPPING") \
               .add_transition("ERROR", "ERROR_STATE") \
               .done() \
           .add_state("PROCESSING") \
               .add_transition("COMPLETE", "RUNNING") \
               .add_transition("ERROR", "ERROR_STATE") \
               .set_timeout(60) \
               .done() \
           .add_state("STOPPING") \
               .add_transition("COMPLETE", "IDLE") \
               .add_transition("ERROR", "ERROR_STATE") \
               .done() \
           .add_state("ERROR_STATE") \
               .add_transition("RESET", "IDLE") \
               .add_transition("SHUTDOWN", "SHUTDOWN") \
               .done() \
           .add_state("SHUTDOWN") \
               .done()
    
    # Add error recovery mappings
    builder.add_error_recovery("INITIALIZING", "ERROR_STATE") \
           .add_error_recovery("PROCESSING", "RUNNING") \
           .add_error_recovery("RUNNING", "ERROR_STATE")
    
    # Create enhanced context with all services
    context = BaseContext()
    services = ServiceFactory.create_default_services()
    
    for service_type, service_instance in services.items():
        context.services.register_singleton(service_type, service_instance)
    
    # Build state machine
    state_machine = builder.build(context)
    
    # Add error callback
    error_callback_id = state_machine.add_error_callback(create_error_callback())
    print(f"Registered error callback: {error_callback_id}")
    
    try:
        # Start the state machine
        state_machine.start()
        print(f"State machine started in state: {state_machine.current_state_name}")
        
        # Simulate normal operation
        print("\n=== Normal Operation ===")
        state_machine.send_event("START")
        time.sleep(1)
        
        print(f"Current state: {state_machine.current_state_name}")
        
        state_machine.send_event("READY")
        time.sleep(1)
        print(f"Current state: {state_machine.current_state_name}")
        
        # Simulate errors
        print("\n=== Error Simulation ===")
        
        # Simulate a configuration error
        state_machine._handle_error(
            error_code=StateMachineErrorCode.CONFIGURATION_ERROR,
            state=state_machine.current_state_name,
            additional_data={
                'operation': 'process_data',
                'error_details': 'Invalid configuration parameter'
            }
        )
        
        time.sleep(1)
        
        # Simulate a system resource error
        state_machine.send_event("PROCESS")
        time.sleep(1)
        
        state_machine._handle_error(
            error_code=SystemErrorCode.RESOURCE_UNAVAILABLE,
            state=state_machine.current_state_name,
            additional_data={
                'operation': 'allocate_memory',
                'resource_type': 'memory',
                'requested_amount': '1GB'
            }
        )
        
        time.sleep(1)
        
        # Check error statistics
        print("\n=== Error Statistics ===")
        error_stats = state_machine.get_error_statistics()
        print(f"Total errors: {error_stats.get('total_errors', 0)}")
        print(f"Active errors: {error_stats.get('active_errors', 0)}")
        print(f"Recovery success rate: {error_stats.get('recovery_success_rate', 0):.1f}%")
        print(f"Severity distribution: {error_stats.get('severity_distribution', {})}")
        
        # Check for active errors
        active_errors = state_machine.get_active_errors()
        if active_errors:
            print(f"\nActive errors ({len(active_errors)}):")
            for error in active_errors:
                print(f"  - Error {error.code} in state {error.state}")
        else:
            print("\nNo active errors")
        
        # Check for fatal errors
        if state_machine.has_fatal_errors():
            print("\n⚠️  FATAL ERRORS DETECTED!")
        else:
            print("\n✅ No fatal errors")
        
        # Simulate error recovery
        print("\n=== Error Recovery ===")
        if active_errors:
            for error in active_errors[:2]:  # Clear first two errors
                if state_machine.clear_error(error.code):
                    print(f"✅ Cleared error {error.code}")
                else:
                    print(f"❌ Failed to clear error {error.code}")
        
        # Final statistics
        print("\n=== Final Statistics ===")
        final_stats = state_machine.get_error_statistics()
        print(f"Total errors handled: {final_stats.get('total_errors', 0)}")
        print(f"Remaining active errors: {final_stats.get('active_errors', 0)}")
        
        # Test error validation
        print("\n=== Error Handling Validation ===")
        validation_result = state_machine.validate_error_handling()
        print(f"Validation success: {validation_result.success}")
        if validation_result.errors:
            for error in validation_result.errors:
                print(f"  Error: {error}")
        if validation_result.warnings:
            for warning in validation_result.warnings:
                print(f"  Warning: {warning}")
        
    finally:
        # Cleanup
        state_machine.remove_error_callback(error_callback_id)
        state_machine.stop()
        print("\nState machine stopped and cleaned up")


if __name__ == "__main__":
    print("Enhanced Error Handling Integration Example")
    print("==========================================")
    simulate_system_with_errors()