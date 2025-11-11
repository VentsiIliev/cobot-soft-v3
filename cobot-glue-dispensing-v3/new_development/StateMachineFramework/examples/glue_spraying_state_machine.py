"""
Glue Spraying Application State Machine Example

This module demonstrates how to implement the GlueSprayingApplication state management
using the enhanced state machine framework. It provides a robust and maintainable
replacement for the manual state handling in the original application.

Key Features:
- Proper state transitions for glue spraying operations
- Error handling and recovery mechanisms
- Validation of preconditions before state transitions
- Performance monitoring and metrics collection
- Service integration for robot, vision, and glue systems
"""

import time
import sys
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add the StateMachineFramework to the path
framework_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, framework_path)

try:
    from builders.enhanced_builder import EnhancedStateMachineBuilder, ConditionalTransition
    from services.default_implementations import ServiceFactory
    from services.enhanced_container import EnhancedServiceContainer
    from services.new_services import MetricsService, ValidationService
    from core.context import BaseContext
    from core.state_machine import EnhancedStateMachine
    from validation.validation_result import ValidationResult
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating mock implementations for demonstration...")
    
    # Create minimal mock implementations for demonstration
    class MockStateMachineBuilder:
        def __init__(self):
            self.states = {}
            self.initial_state = None
            
        def set_initial_state(self, state):
            self.initial_state = state
            return self
            
        def add_state(self, name):
            return MockStateBuilder(self, name)
            
        def add_global_transition(self, event, target):
            return self
            
        def add_error_recovery(self, from_state, to_state):
            return self
            
        def add_conditional_transition(self, from_state, event, conditions):
            return self
            
        def configure_performance(self, **kwargs):
            return self
            
        def build(self, context):
            return MockStateMachine(context)
    
    class MockStateBuilder:
        def __init__(self, parent, name):
            self.parent = parent
            self.name = name
            
        def add_transition(self, event, target):
            return self
            
        def add_entry_action(self, action):
            return self
            
        def add_precondition(self, condition, description):
            return self
            
        def set_timeout(self, timeout):
            return self
            
        def done(self):
            return self.parent
    
    class MockStateMachine:
        def __init__(self, context):
            self.context = context
            self.current_state_name = "INITIALIZING"
            self.running = False
            
        def start(self):
            self.running = True
            
        def stop(self):
            self.running = False
            
        def send_event(self, event):
            # Simple state transitions for demonstration
            state_transitions = {
                ("INITIALIZING", "SERVICES_READY"): "IDLE",
                ("IDLE", "START_CALIBRATION"): "CALIBRATING", 
                ("IDLE", "CREATE_WORKPIECE"): "WORKPIECE_CREATION",
                ("IDLE", "START_OPERATION"): "PREPARING",
                ("CALIBRATING", "CALIBRATE_ROBOT"): "ROBOT_CALIBRATION",
                ("CALIBRATING", "CALIBRATE_CAMERA"): "CAMERA_CALIBRATION",
                ("CALIBRATING", "CALIBRATION_COMPLETE"): "IDLE",
                ("ROBOT_CALIBRATION", "ROBOT_CALIBRATION_SUCCESS"): "CALIBRATING",
                ("CAMERA_CALIBRATION", "CAMERA_CALIBRATION_SUCCESS"): "CALIBRATING",
                ("WORKPIECE_CREATION", "WORKPIECE_CREATED"): "IDLE",
                ("PREPARING", "PREPARATION_COMPLETE"): "PROCESSING",
                ("PROCESSING", "HEIGHT_MEASUREMENT"): "MEASURING_HEIGHT",
                ("PROCESSING", "GLUE_SPRAYING"): "SPRAYING",
                ("PROCESSING", "OPERATION_COMPLETE"): "FINALIZING",
                ("MEASURING_HEIGHT", "HEIGHT_MEASURED"): "PROCESSING",
                ("SPRAYING", "SPRAYING_COMPLETE"): "PROCESSING",
                ("FINALIZING", "FINALIZATION_COMPLETE"): "IDLE",
            }
            
            key = (self.current_state_name, event)
            if key in state_transitions:
                self.current_state_name = state_transitions[key]
                
        def get_performance_report(self):
            return {}
    
    class MockContext:
        def __init__(self):
            self.data = {}
            
        def get_data(self, key, default=None):
            return self.data.get(key, default)
            
        def set_data(self, key, value):
            self.data[key] = value
    
    class MockConditionalTransition:
        def __init__(self, condition, target_state, priority=0, description=""):
            self.condition = condition
            self.target_state = target_state
            self.priority = priority
            self.description = description
    
    # Use mock implementations
    EnhancedStateMachineBuilder = MockStateMachineBuilder
    ConditionalTransition = MockConditionalTransition
    BaseContext = MockContext
    EnhancedStateMachine = MockStateMachine
    MetricsService = type('MockMetricsService', (), {})
    ValidationService = type('MockValidationService', (), {})
    ServiceFactory = type('MockServiceFactory', (), {'create_default_services': lambda: {}})
    EnhancedServiceContainer = type('MockEnhancedServiceContainer', (), {})
    ValidationResult = type('MockValidationResult', (), {})


class GlueSprayingContext(BaseContext):
    """Extended context for glue spraying operations."""
    
    def __init__(self):
        super().__init__()
        # Service references (would be injected in real implementation)
        self.robot_service: Optional[Any] = None
        self.vision_service: Optional[Any] = None
        self.glue_nozzle_service: Optional[Any] = None
        self.settings_service: Optional[Any] = None
        self.workpiece_service: Optional[Any] = None
        self.robot_calibration_service: Optional[Any] = None
        
        # Application state data
        self.robot_position: Optional[list] = [0, 0, 0, 180, 0, 0]
        self.vision_contours: Optional[list] = None
        self.workpiece_data: Optional[Dict] = {}
        self.calibration_status: bool = False
        self.error_count: int = 0


class GlueSprayingStateMachine:
    """
    State machine implementation for glue spraying application.
    
    This class encapsulates all the state management logic from the original
    GlueSprayingApplication, providing better error handling, validation,
    and maintainability.
    """
    
    def __init__(self, context: GlueSprayingContext):
        """Initialize the glue spraying state machine."""
        self.context = context
        self.state_machine: Optional[EnhancedStateMachine] = None
        self._build_state_machine()
    
    def _build_state_machine(self):
        """Build the complete state machine configuration."""
        builder = EnhancedStateMachineBuilder()
        
        # Configure main states based on original GlueSprayApplicationState
        builder.set_initial_state("INITIALIZING") \
               .add_state("INITIALIZING") \
                   .add_transition("SERVICES_READY", "IDLE") \
                   .add_transition("INITIALIZATION_FAILED", "ERROR") \
                   .add_entry_action("initialize_services") \
                   .add_precondition(self._check_services_available, "All services must be available") \
                   .set_timeout(30) \
                   .done() \
               .add_state("IDLE") \
                   .add_transition("START_CALIBRATION", "CALIBRATING") \
                   .add_transition("START_OPERATION", "PREPARING") \
                   .add_transition("CREATE_WORKPIECE", "WORKPIECE_CREATION") \
                   .add_transition("SYSTEM_ERROR", "ERROR") \
                   .add_entry_action("enter_idle_state") \
                   .done() \
               .add_state("CALIBRATING") \
                   .add_transition("CALIBRATE_ROBOT", "ROBOT_CALIBRATION") \
                   .add_transition("CALIBRATE_CAMERA", "CAMERA_CALIBRATION") \
                   .add_transition("CALIBRATION_COMPLETE", "IDLE") \
                   .add_transition("CALIBRATION_FAILED", "ERROR") \
                   .add_entry_action("prepare_calibration") \
                   .done() \
               .add_state("ROBOT_CALIBRATION") \
                   .add_transition("ROBOT_CALIBRATION_SUCCESS", "CALIBRATING") \
                   .add_transition("ROBOT_CALIBRATION_FAILED", "ERROR") \
                   .add_entry_action("perform_robot_calibration") \
                   .add_precondition(self._check_robot_ready, "Robot must be ready for calibration") \
                   .set_timeout(60) \
                   .done() \
               .add_state("CAMERA_CALIBRATION") \
                   .add_transition("CAMERA_CALIBRATION_SUCCESS", "CALIBRATING") \
                   .add_transition("CAMERA_CALIBRATION_FAILED", "ERROR") \
                   .add_entry_action("perform_camera_calibration") \
                   .add_precondition(self._check_vision_system_ready, "Vision system must be ready") \
                   .set_timeout(45) \
                   .done() \
               .add_state("WORKPIECE_CREATION") \
                   .add_transition("WORKPIECE_CREATED", "IDLE") \
                   .add_transition("WORKPIECE_CREATION_FAILED", "ERROR") \
                   .add_entry_action("create_workpiece") \
                   .add_precondition(self._check_vision_contours, "Vision contours must be detected") \
                   .set_timeout(30) \
                   .done() \
               .add_state("PREPARING") \
                   .add_transition("PREPARATION_COMPLETE", "PROCESSING") \
                   .add_transition("PREPARATION_FAILED", "ERROR") \
                   .add_entry_action("prepare_operation") \
                   .add_precondition(self._check_system_ready, "All systems must be ready") \
                   .done() \
               .add_state("PROCESSING") \
                   .add_transition("HEIGHT_MEASUREMENT", "MEASURING_HEIGHT") \
                   .add_transition("GLUE_SPRAYING", "SPRAYING") \
                   .add_transition("OPERATION_COMPLETE", "FINALIZING") \
                   .add_transition("OPERATION_FAILED", "ERROR") \
                   .add_entry_action("start_processing") \
                   .done() \
               .add_state("MEASURING_HEIGHT") \
                   .add_transition("HEIGHT_MEASURED", "PROCESSING") \
                   .add_transition("HEIGHT_MEASUREMENT_FAILED", "ERROR") \
                   .add_entry_action("measure_workpiece_height") \
                   .set_timeout(20) \
                   .done() \
               .add_state("SPRAYING") \
                   .add_transition("SPRAYING_COMPLETE", "PROCESSING") \
                   .add_transition("SPRAYING_FAILED", "ERROR") \
                   .add_entry_action("perform_glue_spraying") \
                   .add_precondition(self._check_glue_system_ready, "Glue system must be ready") \
                   .done() \
               .add_state("FINALIZING") \
                   .add_transition("FINALIZATION_COMPLETE", "IDLE") \
                   .add_transition("FINALIZATION_FAILED", "ERROR") \
                   .add_entry_action("finalize_operation") \
                   .done() \
               .add_state("ERROR") \
                   .add_transition("RETRY_OPERATION", "IDLE") \
                   .add_transition("RESET_SYSTEM", "INITIALIZING") \
                   .add_entry_action("handle_error_state") \
                   .done()
        
        # Add global emergency transitions
        builder.add_global_transition("EMERGENCY_STOP", "ERROR") \
               .add_global_transition("SYSTEM_RESET", "INITIALIZING")
        
        # Add error recovery strategies
        builder.add_error_recovery("ROBOT_CALIBRATION", "ERROR") \
               .add_error_recovery("CAMERA_CALIBRATION", "ERROR") \
               .add_error_recovery("PROCESSING", "ERROR") \
               .add_error_recovery("ERROR", "IDLE")
        
        # Add conditional transitions for smart behavior
        low_battery_condition = ConditionalTransition(
            condition=lambda ctx: ctx.get_data('battery_level', 100) < 20,
            target_state="ERROR",
            priority=1,
            description="Emergency stop on low battery"
        )
        
        temperature_condition = ConditionalTransition(
            condition=lambda ctx: ctx.get_data('temperature', 20) > 80,
            target_state="ERROR",
            priority=2,
            description="Emergency stop on high temperature"
        )
        
        builder.add_conditional_transition("PROCESSING", "CHECK_CONDITIONS", 
                                         [low_battery_condition, temperature_condition])
        
        # Configure performance monitoring
        builder.configure_performance(
            enable_metrics=True,
            enable_validation=True,
            thread_pool_size=4
        )
        
        # Build the state machine
        self.state_machine = builder.build(self.context)
    
    # Precondition validation methods
    def _check_services_available(self, context: GlueSprayingContext) -> bool:
        """Check if all required services are available."""
        required_services = [
            'robot_service', 'vision_service', 'glue_nozzle_service',
            'settings_service', 'workpiece_service', 'robot_calibration_service'
        ]
        
        for service_name in required_services:
            if getattr(context, service_name, None) is None:
                print(f"Service {service_name} is not available")
                return False
        return True
    
    def _check_robot_ready(self, context: GlueSprayingContext) -> bool:
        """Check if robot is ready for operations."""
        # In real implementation, check robot state
        robot_state = context.get_data('robot_state', 'ready')
        return robot_state == 'ready'
    
    def _check_vision_system_ready(self, context: GlueSprayingContext) -> bool:
        """Check if vision system is operational."""
        vision_state = context.get_data('vision_state', 'ready')
        return vision_state == 'ready'
    
    def _check_vision_contours(self, context: GlueSprayingContext) -> bool:
        """Check if vision contours are available."""
        contours = context.get_data('contours', [])
        return len(contours) > 0
    
    def _check_system_ready(self, context: GlueSprayingContext) -> bool:
        """Check if entire system is ready for operation."""
        return (self._check_robot_ready(context) and 
                self._check_vision_system_ready(context) and
                context.calibration_status)
    
    def _check_glue_system_ready(self, context: GlueSprayingContext) -> bool:
        """Check if glue dispensing system is ready."""
        glue_state = context.get_data('glue_system_state', 'ready')
        pressure = context.get_data('glue_pressure', 1.0)
        return glue_state == 'ready' and 0.5 <= pressure <= 2.0
    
    # State action methods (would interface with actual services)
    def initialize_services(self, context: GlueSprayingContext):
        """Initialize all required services."""
        print("Initializing services...")
        # Simulate service initialization
        time.sleep(1)
        context.set_data('initialization_complete', True)
    
    def enter_idle_state(self, context: GlueSprayingContext):
        """Enter idle state and prepare for operations."""
        print("Entering idle state - system ready for operations")
        context.set_data('system_status', 'idle')
    
    def prepare_calibration(self, context: GlueSprayingContext):
        """Prepare system for calibration."""
        print("Preparing calibration procedures...")
    
    def perform_robot_calibration(self, context: GlueSprayingContext):
        """Perform robot calibration using ArUco markers."""
        print("Performing robot calibration...")
        # Simulate the calibrateRobot method from original application
        time.sleep(2)
        context.calibration_status = True
        print("Robot calibration completed successfully")
    
    def perform_camera_calibration(self, context: GlueSprayingContext):
        """Perform camera calibration."""
        print("Performing camera calibration...")
        # Simulate the calibrateCamera method
        time.sleep(1.5)
        print("Camera calibration completed successfully")
    
    def create_workpiece(self, context: GlueSprayingContext):
        """Create workpiece from detected contours."""
        print("Creating workpiece from vision data...")
        # Simulate the createWorkpiece method
        contours = context.get_data('contours', [])
        context.workpiece_data = {
            'contours': contours,
            'area': 1000,
            'height': 4,
            'timestamp': time.time()
        }
        print(f"Workpiece created with {len(contours)} contours")
    
    def prepare_operation(self, context: GlueSprayingContext):
        """Prepare for glue spraying operation."""
        print("Preparing operation - moving robot to position...")
        context.robot_position = [-400, 350, 125, 180, 0, 0]  # Calibration position
    
    def start_processing(self, context: GlueSprayingContext):
        """Start the main processing routine."""
        print("Starting processing routine...")
        context.set_data('processing_start_time', time.time())
    
    def measure_workpiece_height(self, context: GlueSprayingContext):
        """Measure workpiece height using laser system."""
        print("Measuring workpiece height...")
        # Simulate the measureHeight method
        estimated_height = 4.0  # Default height
        context.set_data('workpiece_height', estimated_height)
        print(f"Measured height: {estimated_height}mm")
    
    def perform_glue_spraying(self, context: GlueSprayingContext):
        """Perform the actual glue spraying operation."""
        print("Performing glue spraying operation...")
        # Simulate the start method from original application
        workpiece_data = context.workpiece_data
        if workpiece_data:
            print(f"Spraying glue on workpiece with area {workpiece_data.get('area', 0)}")
            time.sleep(3)  # Simulate spraying time
            print("Glue spraying completed successfully")
    
    def finalize_operation(self, context: GlueSprayingContext):
        """Finalize the operation and return to start position."""
        print("Finalizing operation...")
        context.robot_position = [0, 0, 250, 180, 0, 0]  # Start position
        processing_time = time.time() - context.get_data('processing_start_time', time.time())
        print(f"Operation completed in {processing_time:.2f} seconds")
    
    def handle_error_state(self, context: GlueSprayingContext):
        """Handle error conditions and prepare for recovery."""
        print("Entering error state - analyzing errors...")
        context.error_count += 1
        print(f"Total errors encountered: {context.error_count}")
    
    # Public interface methods
    def start(self):
        """Start the state machine."""
        if self.state_machine:
            self.state_machine.start()
            print("Glue spraying state machine started")
    
    def stop(self):
        """Stop the state machine."""
        if self.state_machine:
            self.state_machine.stop()
            print("Glue spraying state machine stopped")
    
    def send_event(self, event: str):
        """Send an event to the state machine."""
        if self.state_machine:
            self.state_machine.send_event(event)
    
    def get_current_state(self) -> str:
        """Get the current state name."""
        if self.state_machine:
            return self.state_machine.current_state_name
        return "NOT_STARTED"
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance monitoring report."""
        if self.state_machine and hasattr(self.state_machine, 'performance_manager'):
            return self.state_machine.performance_manager.get_comprehensive_report()
        return {}


def demonstrate_glue_spraying_state_machine():
    """Demonstrate the glue spraying state machine in action."""
    print("=== Glue Spraying State Machine Demonstration ===")
    
    # Create context with mock services
    context = GlueSprayingContext()
    
    # Mock service initialization
    context.robot_service = "MockRobotService"
    context.vision_service = "MockVisionService"
    context.glue_nozzle_service = "MockGlueNozzleService"
    context.settings_service = "MockSettingsService"
    context.workpiece_service = "MockWorkpieceService"
    context.robot_calibration_service = "MockRobotCalibrationService"
    
    # Set initial system conditions
    context.set_data('robot_state', 'ready')
    context.set_data('vision_state', 'ready')
    context.set_data('glue_system_state', 'ready')
    context.set_data('glue_pressure', 1.5)
    context.set_data('battery_level', 85)
    context.set_data('temperature', 25)
    context.set_data('contours', [[100, 100], [200, 100], [200, 200], [100, 200]])
    
    # Create and start state machine
    glue_spraying_sm = GlueSprayingStateMachine(context)
    
    try:
        glue_spraying_sm.start()
        print(f"Initial state: {glue_spraying_sm.get_current_state()}")
        
        # Simulate initialization sequence
        print("\n--- Initialization Sequence ---")
        glue_spraying_sm.send_event("SERVICES_READY")
        time.sleep(0.5)
        print(f"After initialization: {glue_spraying_sm.get_current_state()}")
        
        # Simulate calibration workflow
        print("\n--- Calibration Workflow ---")
        glue_spraying_sm.send_event("START_CALIBRATION")
        time.sleep(0.2)
        print(f"Calibration mode: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("CALIBRATE_ROBOT")
        time.sleep(2.5)
        print(f"Robot calibration: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("ROBOT_CALIBRATION_SUCCESS")
        time.sleep(0.2)
        glue_spraying_sm.send_event("CALIBRATE_CAMERA")
        time.sleep(2)
        print(f"Camera calibration: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("CAMERA_CALIBRATION_SUCCESS")
        time.sleep(0.2)
        glue_spraying_sm.send_event("CALIBRATION_COMPLETE")
        time.sleep(0.2)
        print(f"Calibration complete: {glue_spraying_sm.get_current_state()}")
        
        # Simulate workpiece creation
        print("\n--- Workpiece Creation ---")
        glue_spraying_sm.send_event("CREATE_WORKPIECE")
        time.sleep(1)
        print(f"Creating workpiece: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("WORKPIECE_CREATED")
        time.sleep(0.2)
        print(f"Workpiece created: {glue_spraying_sm.get_current_state()}")
        
        # Simulate main operation
        print("\n--- Main Operation Sequence ---")
        glue_spraying_sm.send_event("START_OPERATION")
        time.sleep(0.5)
        print(f"Preparing operation: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("PREPARATION_COMPLETE")
        time.sleep(0.2)
        print(f"Processing: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("HEIGHT_MEASUREMENT")
        time.sleep(1)
        print(f"Measuring height: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("HEIGHT_MEASURED")
        time.sleep(0.2)
        glue_spraying_sm.send_event("GLUE_SPRAYING")
        time.sleep(3.5)
        print(f"Spraying: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("SPRAYING_COMPLETE")
        time.sleep(0.2)
        glue_spraying_sm.send_event("OPERATION_COMPLETE")
        time.sleep(0.5)
        print(f"Finalizing: {glue_spraying_sm.get_current_state()}")
        
        glue_spraying_sm.send_event("FINALIZATION_COMPLETE")
        time.sleep(0.2)
        print(f"Operation complete: {glue_spraying_sm.get_current_state()}")
        
        # Display performance report
        print("\n--- Performance Report ---")
        performance_report = glue_spraying_sm.get_performance_report()
        if performance_report:
            print("Performance monitoring data collected")
            for section, data in performance_report.items():
                if isinstance(data, dict) and data:
                    print(f"  {section}: {len(data)} metrics")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
    
    finally:
        glue_spraying_sm.stop()
    
    print("\nGlue spraying state machine demonstration completed!")


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n=== Error Handling Demonstration ===")
    
    context = GlueSprayingContext()
    # Simulate missing service to trigger error
    context.robot_service = None  # Missing service
    
    glue_spraying_sm = GlueSprayingStateMachine(context)
    
    try:
        glue_spraying_sm.start()
        print(f"Initial state: {glue_spraying_sm.get_current_state()}")
        
        # Try to initialize - should fail due to missing service
        glue_spraying_sm.send_event("SERVICES_READY")
        time.sleep(0.5)
        print(f"After failed initialization: {glue_spraying_sm.get_current_state()}")
        
        # Demonstrate emergency stop
        glue_spraying_sm.send_event("EMERGENCY_STOP")
        time.sleep(0.2)
        print(f"After emergency stop: {glue_spraying_sm.get_current_state()}")
        
    finally:
        glue_spraying_sm.stop()
    
    print("Error handling demonstration completed!")


if __name__ == "__main__":
    """Run the glue spraying state machine examples."""
    print("Enhanced State Machine Framework - Glue Spraying Application")
    print("=" * 65)
    
    try:
        demonstrate_glue_spraying_state_machine()
        demonstrate_error_handling()
        
    except Exception as e:
        print(f"Demonstration error: {e}")
    
    print("\nAll demonstrations completed!")