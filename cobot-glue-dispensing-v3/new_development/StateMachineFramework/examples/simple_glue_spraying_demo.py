"""
Simple Glue Spraying Application State Machine Demo

This is a simplified standalone demonstration that shows how the original
system.py could be refactored using state machine principles,
without complex framework dependencies.

This demo focuses on the core state management concepts and can run independently.
"""

import time
from enum import Enum
from typing import Dict, Any, Optional, Callable


class GlueSprayState(Enum):
    """States for the glue spraying application."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    CALIBRATING = "calibrating"
    ROBOT_CALIBRATION = "robot_calibration"
    CAMERA_CALIBRATION = "camera_calibration"
    WORKPIECE_CREATION = "workpiece_creation"
    PREPARING = "preparing"
    PROCESSING = "processing"
    MEASURING_HEIGHT = "measuring_height"
    SPRAYING = "spraying"
    FINALIZING = "finalizing"
    ERROR = "error"


class GlueSprayEvent(Enum):
    """Events that can trigger state transitions."""
    SERVICES_READY = "services_ready"
    INITIALIZATION_FAILED = "initialization_failed"
    START_CALIBRATION = "start_calibration"
    CALIBRATE_ROBOT = "calibrate_robot"
    CALIBRATE_CAMERA = "calibrate_camera"
    CALIBRATION_COMPLETE = "calibration_complete"
    CALIBRATION_FAILED = "calibration_failed"
    ROBOT_CALIBRATION_SUCCESS = "robot_calibration_success"
    ROBOT_CALIBRATION_FAILED = "robot_calibration_failed"
    CAMERA_CALIBRATION_SUCCESS = "camera_calibration_success"
    CAMERA_CALIBRATION_FAILED = "camera_calibration_failed"
    CREATE_WORKPIECE = "create_workpiece"
    WORKPIECE_CREATED = "workpiece_created"
    WORKPIECE_CREATION_FAILED = "workpiece_creation_failed"
    START_OPERATION = "start_operation"
    PREPARATION_COMPLETE = "preparation_complete"
    PREPARATION_FAILED = "preparation_failed"
    HEIGHT_MEASUREMENT = "height_measurement"
    HEIGHT_MEASURED = "height_measured"
    HEIGHT_MEASUREMENT_FAILED = "height_measurement_failed"
    GLUE_SPRAYING = "glue_spraying"
    SPRAYING_COMPLETE = "spraying_complete"
    SPRAYING_FAILED = "spraying_failed"
    OPERATION_COMPLETE = "operation_complete"
    OPERATION_FAILED = "operation_failed"
    FINALIZATION_COMPLETE = "finalization_complete"
    FINALIZATION_FAILED = "finalization_failed"
    RETRY_OPERATION = "retry_operation"
    RESET_SYSTEM = "reset_system"
    EMERGENCY_STOP = "emergency_stop"


class SimpleGlueSprayingStateMachine:
    """
    Simplified state machine for glue spraying operations.
    
    This demonstrates the core concepts of the state machine approach
    without the complexity of the full framework.
    """
    
    def __init__(self):
        """Initialize the state machine."""
        self.current_state = GlueSprayState.INITIALIZING
        self.context = {}
        self.running = False
        
        # Define state transitions
        self.transitions = {
            # From INITIALIZING
            (GlueSprayState.INITIALIZING, GlueSprayEvent.SERVICES_READY): GlueSprayState.IDLE,
            (GlueSprayState.INITIALIZING, GlueSprayEvent.INITIALIZATION_FAILED): GlueSprayState.ERROR,
            
            # From IDLE
            (GlueSprayState.IDLE, GlueSprayEvent.START_CALIBRATION): GlueSprayState.CALIBRATING,
            (GlueSprayState.IDLE, GlueSprayEvent.CREATE_WORKPIECE): GlueSprayState.WORKPIECE_CREATION,
            (GlueSprayState.IDLE, GlueSprayEvent.START_OPERATION): GlueSprayState.PREPARING,
            
            # From CALIBRATING
            (GlueSprayState.CALIBRATING, GlueSprayEvent.CALIBRATE_ROBOT): GlueSprayState.ROBOT_CALIBRATION,
            (GlueSprayState.CALIBRATING, GlueSprayEvent.CALIBRATE_CAMERA): GlueSprayState.CAMERA_CALIBRATION,
            (GlueSprayState.CALIBRATING, GlueSprayEvent.CALIBRATION_COMPLETE): GlueSprayState.IDLE,
            (GlueSprayState.CALIBRATING, GlueSprayEvent.CALIBRATION_FAILED): GlueSprayState.ERROR,
            
            # From ROBOT_CALIBRATION
            (GlueSprayState.ROBOT_CALIBRATION, GlueSprayEvent.ROBOT_CALIBRATION_SUCCESS): GlueSprayState.CALIBRATING,
            (GlueSprayState.ROBOT_CALIBRATION, GlueSprayEvent.ROBOT_CALIBRATION_FAILED): GlueSprayState.ERROR,
            
            # From CAMERA_CALIBRATION
            (GlueSprayState.CAMERA_CALIBRATION, GlueSprayEvent.CAMERA_CALIBRATION_SUCCESS): GlueSprayState.CALIBRATING,
            (GlueSprayState.CAMERA_CALIBRATION, GlueSprayEvent.CAMERA_CALIBRATION_FAILED): GlueSprayState.ERROR,
            
            # From WORKPIECE_CREATION
            (GlueSprayState.WORKPIECE_CREATION, GlueSprayEvent.WORKPIECE_CREATED): GlueSprayState.IDLE,
            (GlueSprayState.WORKPIECE_CREATION, GlueSprayEvent.WORKPIECE_CREATION_FAILED): GlueSprayState.ERROR,
            
            # From PREPARING
            (GlueSprayState.PREPARING, GlueSprayEvent.PREPARATION_COMPLETE): GlueSprayState.PROCESSING,
            (GlueSprayState.PREPARING, GlueSprayEvent.PREPARATION_FAILED): GlueSprayState.ERROR,
            
            # From PROCESSING
            (GlueSprayState.PROCESSING, GlueSprayEvent.HEIGHT_MEASUREMENT): GlueSprayState.MEASURING_HEIGHT,
            (GlueSprayState.PROCESSING, GlueSprayEvent.GLUE_SPRAYING): GlueSprayState.SPRAYING,
            (GlueSprayState.PROCESSING, GlueSprayEvent.OPERATION_COMPLETE): GlueSprayState.FINALIZING,
            (GlueSprayState.PROCESSING, GlueSprayEvent.OPERATION_FAILED): GlueSprayState.ERROR,
            
            # From MEASURING_HEIGHT
            (GlueSprayState.MEASURING_HEIGHT, GlueSprayEvent.HEIGHT_MEASURED): GlueSprayState.PROCESSING,
            (GlueSprayState.MEASURING_HEIGHT, GlueSprayEvent.HEIGHT_MEASUREMENT_FAILED): GlueSprayState.ERROR,
            
            # From SPRAYING
            (GlueSprayState.SPRAYING, GlueSprayEvent.SPRAYING_COMPLETE): GlueSprayState.PROCESSING,
            (GlueSprayState.SPRAYING, GlueSprayEvent.SPRAYING_FAILED): GlueSprayState.ERROR,
            
            # From FINALIZING
            (GlueSprayState.FINALIZING, GlueSprayEvent.FINALIZATION_COMPLETE): GlueSprayState.IDLE,
            (GlueSprayState.FINALIZING, GlueSprayEvent.FINALIZATION_FAILED): GlueSprayState.ERROR,
            
            # From ERROR
            (GlueSprayState.ERROR, GlueSprayEvent.RETRY_OPERATION): GlueSprayState.IDLE,
            (GlueSprayState.ERROR, GlueSprayEvent.RESET_SYSTEM): GlueSprayState.INITIALIZING,
        }
        
        # Global emergency transitions (from any state)
        self.global_transitions = {
            GlueSprayEvent.EMERGENCY_STOP: GlueSprayState.ERROR,
            GlueSprayEvent.RESET_SYSTEM: GlueSprayState.INITIALIZING,
        }
        
        # Entry actions for each state
        self.entry_actions = {
            GlueSprayState.INITIALIZING: self._initialize_services,
            GlueSprayState.IDLE: self._enter_idle_state,
            GlueSprayState.CALIBRATING: self._prepare_calibration,
            GlueSprayState.ROBOT_CALIBRATION: self._perform_robot_calibration,
            GlueSprayState.CAMERA_CALIBRATION: self._perform_camera_calibration,
            GlueSprayState.WORKPIECE_CREATION: self._create_workpiece,
            GlueSprayState.PREPARING: self._prepare_operation,
            GlueSprayState.PROCESSING: self._start_processing,
            GlueSprayState.MEASURING_HEIGHT: self._measure_height,
            GlueSprayState.SPRAYING: self._perform_spraying,
            GlueSprayState.FINALIZING: self._finalize_operation,
            GlueSprayState.ERROR: self._handle_error,
        }
        
        # Preconditions for state entry
        self.preconditions = {
            GlueSprayState.ROBOT_CALIBRATION: self._check_robot_ready,
            GlueSprayState.CAMERA_CALIBRATION: self._check_vision_ready,
            GlueSprayState.WORKPIECE_CREATION: self._check_vision_contours,
            GlueSprayState.PROCESSING: self._check_system_ready,
            GlueSprayState.SPRAYING: self._check_glue_system_ready,
        }
    
    def start(self):
        """Start the state machine."""
        self.running = True
        self._enter_state(self.current_state)
        print(f"State machine started in state: {self.current_state.value}")
    
    def stop(self):
        """Stop the state machine."""
        self.running = False
        print("State machine stopped")
    
    def send_event(self, event: GlueSprayEvent):
        """Send an event to trigger a state transition."""
        if not self.running:
            print("State machine is not running")
            return False
            
        # Check global transitions first
        if event in self.global_transitions:
            new_state = self.global_transitions[event]
            return self._transition_to_state(new_state, event)
        
        # Check regular transitions
        transition_key = (self.current_state, event)
        if transition_key in self.transitions:
            new_state = self.transitions[transition_key]
            return self._transition_to_state(new_state, event)
        
        print(f"No transition defined for event {event.value} in state {self.current_state.value}")
        return False
    
    def _transition_to_state(self, new_state: GlueSprayState, event: GlueSprayEvent) -> bool:
        """Perform state transition with validation."""
        # Check preconditions
        if new_state in self.preconditions:
            if not self.preconditions[new_state]():
                print(f"Precondition failed for entering state {new_state.value}")
                return False
        
        print(f"Transitioning from {self.current_state.value} to {new_state.value} on event {event.value}")
        
        # Exit current state (if needed)
        self._exit_state(self.current_state)
        
        # Enter new state
        self.current_state = new_state
        self._enter_state(new_state)
        
        return True
    
    def _enter_state(self, state: GlueSprayState):
        """Execute entry action for a state."""
        if state in self.entry_actions:
            self.entry_actions[state]()
    
    def _exit_state(self, state: GlueSprayState):
        """Execute exit action for a state (if needed)."""
        pass  # Could add exit actions here if needed
    
    # Precondition methods
    def _check_robot_ready(self) -> bool:
        """Check if robot is ready for operations."""
        return self.context.get('robot_ready', True)
    
    def _check_vision_ready(self) -> bool:
        """Check if vision system is ready."""
        return self.context.get('vision_ready', True)
    
    def _check_vision_contours(self) -> bool:
        """Check if vision contours are available."""
        contours = self.context.get('contours', [])
        return len(contours) > 0
    
    def _check_system_ready(self) -> bool:
        """Check if entire system is ready."""
        return (self.context.get('robot_ready', True) and
                self.context.get('vision_ready', True) and
                self.context.get('calibration_complete', False))
    
    def _check_glue_system_ready(self) -> bool:
        """Check if glue system is ready."""
        return (self.context.get('glue_system_ready', True) and
                0.5 <= self.context.get('glue_pressure', 1.0) <= 2.0)
    
    # Entry action methods (simulating actual operations)
    def _initialize_services(self):
        """Initialize all required services."""
        print("  [INIT] Initializing services...")
        time.sleep(0.5)
        self.context['robot_ready'] = True
        self.context['vision_ready'] = True
        self.context['glue_system_ready'] = True
        self.context['glue_pressure'] = 1.5
        self.context['contours'] = [[100, 100], [200, 100], [200, 200], [100, 200]]
        print("  [OK] Services initialized successfully")
    
    def _enter_idle_state(self):
        """Enter idle state."""
        print("  [IDLE] System idle - ready for operations")
        self.context['system_status'] = 'idle'
    
    def _prepare_calibration(self):
        """Prepare for calibration."""
        print("  [PREP] Preparing calibration procedures...")
    
    def _perform_robot_calibration(self):
        """Perform robot calibration."""
        print("  [ROBOT] Performing robot calibration with ArUco markers...")
        time.sleep(1.0)  # Simulate calibration time
        self.context['robot_calibrated'] = True
        print("  [OK] Robot calibration completed")
    
    def _perform_camera_calibration(self):
        """Perform camera calibration."""
        print("  [CAMERA] Performing camera calibration...")
        time.sleep(0.8)
        self.context['camera_calibrated'] = True
        self.context['calibration_complete'] = True
        print("  [OK] Camera calibration completed")
    
    def _create_workpiece(self):
        """Create workpiece from contours."""
        print("  [WORKPIECE] Creating workpiece from detected contours...")
        contours = self.context.get('contours', [])
        self.context['workpiece'] = {
            'contours': contours,
            'area': 1000,
            'height': 4,
            'created_at': time.time()
        }
        print(f"  [OK] Workpiece created with {len(contours)} contours")
    
    def _prepare_operation(self):
        """Prepare for operation."""
        print("  [PREP] Preparing operation - moving robot to position...")
        self.context['robot_position'] = [-400, 350, 125, 180, 0, 0]
    
    def _start_processing(self):
        """Start processing."""
        print("  [PROCESS] Starting processing routine...")
        self.context['processing_start'] = time.time()
    
    def _measure_height(self):
        """Measure workpiece height."""
        print("  [MEASURE] Measuring workpiece height with laser...")
        time.sleep(0.5)
        self.context['measured_height'] = 4.2
        print("  [OK] Height measured: 4.2mm")
    
    def _perform_spraying(self):
        """Perform glue spraying."""
        print("  [SPRAY] Performing glue spraying operation...")
        time.sleep(2.0)  # Simulate spraying time
        workpiece = self.context.get('workpiece', {})
        area = workpiece.get('area', 0)
        print(f"  [OK] Glue spraying completed on {area}mm^2 area")
    
    def _finalize_operation(self):
        """Finalize operation."""
        print("  [FINALIZE] Finalizing operation...")
        processing_time = time.time() - self.context.get('processing_start', time.time())
        self.context['robot_position'] = [0, 0, 250, 180, 0, 0]  # Return to start
        print(f"  [OK] Operation completed in {processing_time:.1f} seconds")
    
    def _handle_error(self):
        """Handle error state."""
        print("  [ERROR] Entering error state - analyzing issues...")
        error_count = self.context.get('error_count', 0) + 1
        self.context['error_count'] = error_count
        print(f"  [INFO] Total errors: {error_count}")


def demonstrate_full_workflow():
    """Demonstrate a complete glue spraying workflow."""
    print("=== Complete Glue Spraying Workflow Demonstration ===")
    
    # Create and start state machine
    sm = SimpleGlueSprayingStateMachine()
    sm.start()
    
    try:
        print(f"\nCurrent state: {sm.current_state.value}")
        
        # Step 1: Initialize system
        print("\n[1] System Initialization")
        sm.send_event(GlueSprayEvent.SERVICES_READY)
        time.sleep(0.3)
        
        # Step 2: Calibration workflow
        print("\n[2] Calibration Workflow")
        sm.send_event(GlueSprayEvent.START_CALIBRATION)
        time.sleep(0.2)
        
        sm.send_event(GlueSprayEvent.CALIBRATE_ROBOT)
        time.sleep(1.2)
        sm.send_event(GlueSprayEvent.ROBOT_CALIBRATION_SUCCESS)
        time.sleep(0.2)
        
        sm.send_event(GlueSprayEvent.CALIBRATE_CAMERA)
        time.sleep(1.0)
        sm.send_event(GlueSprayEvent.CAMERA_CALIBRATION_SUCCESS)
        time.sleep(0.2)
        
        sm.send_event(GlueSprayEvent.CALIBRATION_COMPLETE)
        time.sleep(0.2)
        
        # Step 3: Create workpiece
        print("\n[3] Workpiece Creation")
        sm.send_event(GlueSprayEvent.CREATE_WORKPIECE)
        time.sleep(0.3)
        sm.send_event(GlueSprayEvent.WORKPIECE_CREATED)
        time.sleep(0.2)
        
        # Step 4: Main operation
        print("\n[4] Main Glue Spraying Operation")
        sm.send_event(GlueSprayEvent.START_OPERATION)
        time.sleep(0.3)
        
        sm.send_event(GlueSprayEvent.PREPARATION_COMPLETE)
        time.sleep(0.2)
        
        # Height measurement
        sm.send_event(GlueSprayEvent.HEIGHT_MEASUREMENT)
        time.sleep(0.7)
        sm.send_event(GlueSprayEvent.HEIGHT_MEASURED)
        time.sleep(0.2)
        
        # Glue spraying
        sm.send_event(GlueSprayEvent.GLUE_SPRAYING)
        time.sleep(2.2)
        sm.send_event(GlueSprayEvent.SPRAYING_COMPLETE)
        time.sleep(0.2)
        
        # Finalize
        sm.send_event(GlueSprayEvent.OPERATION_COMPLETE)
        time.sleep(0.3)
        sm.send_event(GlueSprayEvent.FINALIZATION_COMPLETE)
        time.sleep(0.2)
        
        print(f"\n[SUCCESS] Workflow completed! Final state: {sm.current_state.value}")
        
        # Show context data
        print("\n[INFO] Final Context Data:")
        for key, value in sm.context.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            elif isinstance(value, list) and len(value) > 3:
                print(f"   {key}: [{len(value)} items]")
            else:
                print(f"   {key}: {value}")
    
    finally:
        sm.stop()


def demonstrate_error_handling():
    """Demonstrate error handling and recovery."""
    print("\n=== Error Handling Demonstration ===")
    
    sm = SimpleGlueSprayingStateMachine()
    
    # Simulate system not ready
    sm.context['robot_ready'] = False
    
    sm.start()
    
    try:
        print(f"\nInitial state: {sm.current_state.value}")
        
        # Try to proceed without proper initialization
        sm.send_event(GlueSprayEvent.SERVICES_READY)
        time.sleep(0.2)
        
        sm.send_event(GlueSprayEvent.START_CALIBRATION)
        time.sleep(0.2)
        
        # This should fail due to robot not being ready
        success = sm.send_event(GlueSprayEvent.CALIBRATE_ROBOT)
        if not success:
            print("[ERROR] Robot calibration failed due to precondition")
            sm.send_event(GlueSprayEvent.CALIBRATION_FAILED)
        
        time.sleep(0.3)
        print(f"After error: {sm.current_state.value}")
        
        # Test emergency stop
        print("\n[TEST] Testing Emergency Stop")
        sm.send_event(GlueSprayEvent.EMERGENCY_STOP)
        time.sleep(0.2)
        print(f"After emergency stop: {sm.current_state.value}")
        
        # Recovery
        print("\n[RECOVERY] System Recovery")
        sm.send_event(GlueSprayEvent.RESET_SYSTEM)
        time.sleep(0.2)
        print(f"After reset: {sm.current_state.value}")
        
    finally:
        sm.stop()


if __name__ == "__main__":
    """Run the demonstrations."""
    print("Simple Glue Spraying State Machine Demo")
    print("=" * 50)
    
    try:
        demonstrate_full_workflow()
        demonstrate_error_handling()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo error: {e}")
    
    print("\nDemo completed!")