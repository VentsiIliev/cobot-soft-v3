"""
Complete Migration Example and Usage Guide for Generic State Machine Refactoring

This file demonstrates:
1. How to migrate existing code to use the generic state machine
2. Benefits of the new architecture
3. Different usage patterns
4. Testing strategies
"""

import time
from typing import Dict, Any

from new_development.StateMachineFramework.StateMachineFactory import StateMachineFactory
from new_development.StateMachineFramework.StateMachineBuilder import StateMachineBuilder

from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayApplicationAdapter import create_enhanced_glue_spray_application
from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayApplicationAdapter import create_glue_spray_from_config
from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayApplicationAdapter import GLUE_SPRAY_CONFIG
from new_development.StateMachineFramework.v2 import BaseContext, BaseStateMachine


# ============================================================================
# MULTIPLE APPLICATION DEMONSTRATION
# ============================================================================

def demonstrate_generic_framework():
    """Show how the generic framework can be used for different applications"""

    print("\n" + "=" * 80)
    print("GENERIC FRAMEWORK - DIFFERENT APPLICATIONS")
    print("=" * 80)

    # Example 1: Traffic Light System
    print("\n1. TRAFFIC LIGHT STATE MACHINE")
    print("-" * 35)

    traffic_context = BaseContext()

    # Register traffic light callbacks
    def change_light(params):
        color = params.get('color', 'unknown')
        duration = params.get('duration', 0)
        print(f"[TRAFFIC] Light changed to {color} for {duration}s")
        return f"Light is now {color}"

    def log_transition(params):
        print(f"[TRAFFIC] {params.get('action', 'action')} in state {params.get('state', 'unknown')}")

    traffic_context.register_callback('change_light', change_light)
    traffic_context.register_callback('on_entry_log_entry', log_transition)
    traffic_context.register_callback('process_event', lambda p: None)

    # Build traffic light state machine
    traffic_sm = (StateMachineBuilder()
                  .add_state("RED")
                    .add_entry_action("log_entry")
                    .add_transition("TIMER_EXPIRED", "GREEN")
                    .done()
                  .add_state("GREEN")
                    .add_entry_action("log_entry")
                    .add_transition("TIMER_EXPIRED", "YELLOW")
                    .done()
                  .add_state("YELLOW")
                    .add_entry_action("log_entry")
                    .add_transition("TIMER_EXPIRED", "RED")
                    .done()
                  .set_initial_state("RED")
                  .add_global_transition("EMERGENCY", "RED")
                  .build(traffic_context))

    traffic_sm.start()
    print(f"Traffic light state: {traffic_sm.get_current_state()}")

    # Cycle through states
    for i in range(3):
        traffic_sm.process_event("TIMER_EXPIRED")
        time.sleep(0.1)
        print(f"Traffic light state: {traffic_sm.get_current_state()}")

    traffic_sm.stop()

    # Example 2: Vending Machine
    print("\n2. VENDING MACHINE STATE MACHINE")
    print("-" * 37)

    vending_context = BaseContext()

    def process_payment(params):
        amount = params.get('amount', 0)
        print(f"[VENDING] Processing ${amount} payment")
        return amount >= 1.50  # Product costs $1.50

    def dispense_product(params):
        product = params.get('product', 'item')
        print(f"[VENDING] Dispensing {product}")
        return f"{product} dispensed"

    def return_change(params):
        change = params.get('change', 0)
        if change > 0:
            print(f"[VENDING] Returning ${change:.2f} change")

    vending_context.register_callback('process_payment', process_payment)
    vending_context.register_callback('dispense_product', dispense_product)
    vending_context.register_callback('return_change', return_change)
    vending_context.register_callback('on_entry_log_entry', lambda p: print(f"[VENDING] Entering {p.get('state')}"))

    # Build vending machine (simplified)
    vending_config = {
        "initial_state": "IDLE",
        "states": {
            "IDLE": {
                "entry_actions": ["log_entry"],
                "transitions": {
                    "COIN_INSERTED": "PAYMENT_PROCESSING",
                    "PRODUCT_SELECTED": "WAITING_PAYMENT"
                }
            },
            "PAYMENT_PROCESSING": {
                "entry_actions": ["log_entry"],
                "transitions": {
                    "PAYMENT_SUFFICIENT": "DISPENSING",
                    "PAYMENT_INSUFFICIENT": "WAITING_PAYMENT"
                }
            },
            "DISPENSING": {
                "entry_actions": ["log_entry"],
                "transitions": {
                    "PRODUCT_DISPENSED": "IDLE"
                }
            },
            "WAITING_PAYMENT": {
                "entry_actions": ["log_entry"],
                "transitions": {
                    "COIN_INSERTED": "PAYMENT_PROCESSING",
                    "CANCEL": "IDLE"
                }
            }
        }
    }

    vending_sm = StateMachineFactory.from_dict(vending_config, vending_context)
    vending_sm.start()

    print(f"Vending machine state: {vending_sm.get_current_state()}")

    # Simulate vending machine usage
    print("Customer selects product...")
    vending_sm.process_event("PRODUCT_SELECTED")
    time.sleep(0.1)
    print(f"State: {vending_sm.get_current_state()}")

    print("Customer inserts coin...")
    vending_sm.process_event("COIN_INSERTED", {"amount": 2.00})
    time.sleep(0.1)
    print(f"State: {vending_sm.get_current_state()}")

    print("Payment sufficient, dispensing...")
    vending_sm.process_event("PAYMENT_SUFFICIENT")
    time.sleep(0.1)
    print(f"State: {vending_sm.get_current_state()}")

    print("Product dispensed...")
    vending_sm.process_event("PRODUCT_DISPENSED")
    time.sleep(0.1)
    print(f"Final state: {vending_sm.get_current_state()}")

    vending_sm.stop()


# ============================================================================
# TESTING FRAMEWORK
# ============================================================================

class StateMachineTestFramework:
    """Framework for testing state machines"""

    def __init__(self, state_machine: BaseStateMachine):
        self.state_machine = state_machine
        self.test_results = []
        self.mock_callbacks = {}

    def mock_callback(self, name: str, return_value: Any = None, side_effect: callable = None):
        """Mock a callback for testing"""
        def mock_func(params):
            if side_effect:
                return side_effect(params)
            return return_value

        self.mock_callbacks[name] = mock_func
        self.state_machine.context.register_callback(name, mock_func)

    def assert_state(self, expected_state: str, message: str = ""):
        """Assert current state matches expected"""
        current_state = self.state_machine.get_current_state()
        success = current_state == expected_state

        result = {
            'test': f"Assert state: {expected_state}",
            'message': message,
            'expected': expected_state,
            'actual': current_state,
            'success': success
        }
        self.test_results.append(result)

        if success:
            print(f"✓ PASS: State is {current_state} {message}")
        else:
            print(f"✗ FAIL: Expected {expected_state}, got {current_state} {message}")

        return success

    def assert_can_handle_event(self, event: str, expected: bool = True, message: str = ""):
        """Assert whether state machine can handle an event"""
        can_handle = self.state_machine.can_handle_event(event)
        success = can_handle == expected

        result = {
            'test': f"Assert can handle event: {event}",
            'message': message,
            'expected': expected,
            'actual': can_handle,
            'success': success
        }
        self.test_results.append(result)

        if success:
            print(f"✓ PASS: Can handle {event}: {can_handle} {message}")
        else:
            print(f"✗ FAIL: Expected can handle {event}: {expected}, got {can_handle} {message}")

        return success

    def send_event_and_wait(self, event: str, data: Dict[str, Any] = None, wait_time: float = 0.1):
        """Send event and wait for processing"""
        self.state_machine.process_event(event, data)
        time.sleep(wait_time)

    def run_test_scenario(self, name: str, steps: list):
        """Run a complete test scenario"""
        print(f"\n--- Test Scenario: {name} ---")

        for step in steps:
            step_type = step['type']

            if step_type == 'event':
                self.send_event_and_wait(step['event'], step.get('data'), step.get('wait', 0.1))

            elif step_type == 'assert_state':
                self.assert_state(step['state'], step.get('message', ''))

            elif step_type == 'assert_can_handle':
                self.assert_can_handle_event(step['event'], step.get('expected', True), step.get('message', ''))

    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed

        print(f"\n" + "=" * 50)
        print(f"TEST SUMMARY")
        print(f"Total: {total}, Passed: {passed}, Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")

        if failed > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: Expected {result['expected']}, got {result['actual']}")


def demonstrate_testing():
    """Demonstrate testing framework"""

    print("\n" + "=" * 80)
    print("STATE MACHINE TESTING FRAMEWORK")
    print("=" * 80)

    # Create a simple state machine for testing
    context = BaseContext()

    # Mock callbacks that can be controlled in tests
    def mock_operation(params):
        operation_type = params.get('operation_type', 'unknown')
        # Simulate different outcomes based on test data
        if params.get('should_fail', False):
            raise Exception(f"Mock failure for {operation_type}")
        return f"Mock result for {operation_type}"

    context.register_callback('execute_operation', mock_operation)
    context.register_callback('process_event', lambda p: None)
    context.register_callback('on_entry_log_entry', lambda p: None)

    # Build test state machine
    test_sm = (StateMachineBuilder()
               .add_state("IDLE")
                 .add_transition("START", "PROCESSING")
                 .done()
               .add_state("PROCESSING")
                 .set_operation("test_operation")
                 .add_transition("SUCCESS", "IDLE")
                 .add_transition("FAILURE", "ERROR")
                 .done()
               .add_state("ERROR")
                 .add_transition("RESET", "IDLE")
                 .done()
               .set_initial_state("IDLE")
               .build(context))

    test_sm.start()

    # Create test framework
    test_framework = StateMachineTestFramework(test_sm)

    # Test Scenario 1: Normal operation
    test_framework.run_test_scenario("Normal Operation", [
        {'type': 'assert_state', 'state': 'IDLE', 'message': '(initial state)'},
        {'type': 'assert_can_handle', 'event': 'START', 'expected': True},
        {'type': 'assert_can_handle', 'event': 'RESET', 'expected': False},
        {'type': 'event', 'event': 'START'},
        {'type': 'assert_state', 'state': 'PROCESSING', 'message': '(after start)'},
        {'type': 'event', 'event': 'SUCCESS'},
        {'type': 'assert_state', 'state': 'IDLE', 'message': '(after success)'}
    ])

    # Test Scenario 2: Error handling
    test_framework.run_test_scenario("Error Handling", [
        {'type': 'event', 'event': 'START'},
        {'type': 'assert_state', 'state': 'PROCESSING'},
        {'type': 'event', 'event': 'FAILURE'},
        {'type': 'assert_state', 'state': 'ERROR', 'message': '(after failure)'},
        {'type': 'assert_can_handle', 'event': 'START', 'expected': False, 'message': '(cannot start from error)'},
        {'type': 'assert_can_handle', 'event': 'RESET', 'expected': True, 'message': '(can reset from error)'},
        {'type': 'event', 'event': 'RESET'},
        {'type': 'assert_state', 'state': 'IDLE', 'message': '(after reset)'}
    ])

    test_framework.print_summary()
    test_sm.stop()


# ============================================================================
# PERFORMANCE COMPARISON
# ============================================================================

def demonstrate_performance():
    """Compare performance between original and enhanced implementations"""

    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)

    # Create applications
    robot_service = MockRobotService()
    original_app = MockGlueSprayingApplication(robot=robot_service)
    enhanced_app = create_enhanced_glue_spray_application(original_app)

    # Test original performance
    print("\nTesting original application performance...")
    start_time = time.time()
    for i in range(100):
        original_app.start(contourMatching=True)
        original_app.calibrateRobot()
    original_time = time.time() - start_time
    print(f"Original: 200 operations in {original_time:.4f}s ({200/original_time:.1f} ops/sec)")

    # Test enhanced performance
    print("\nTesting enhanced application performance...")
    start_time = time.time()
    for i in range(100):
        enhanced_app.start(contourMatching=True)
        time.sleep(0.001)  # Small delay for state machine processing
        enhanced_app.calibrateRobot()
        time.sleep(0.001)
    enhanced_time = time.time() - start_time
    print(f"Enhanced: 200 operations in {enhanced_time:.4f}s ({200/enhanced_time:.1f} ops/sec)")

    # Calculate overhead
    overhead_percent = ((enhanced_time - original_time) / original_time) * 100
    print(f"\nState machine overhead: {overhead_percent:.1f}%")

    enhanced_app.stop()





# ============================================================================
# USAGE EXAMPLES FOR REAL INTEGRATION
# ============================================================================

"""
REAL INTEGRATION EXAMPLES:

1. MINIMAL MIGRATION (Backward Compatible):
   
   # Before
   app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)
   
   # After (no other changes needed)
   original_app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)
   app = create_enhanced_glue_spray_application(original_app)


2. CONFIGURATION-BASED APPROACH:

   # Load configuration from file
   with open('glue_spray_config.json', 'r') as f:
       config = json.load(f)
   
   app = create_glue_spray_from_config(original_app, config)


3. CUSTOM ENHANCED APPLICATION:

   class CustomGlueSprayApp(GlueSprayApplicationAdapter):
       def __init__(self, original_app):
           super().__init__(original_app)
           # Add custom functionality
           self.context.register_callback('on_custom_event', self.handle_custom_event)
       
       def handle_custom_event(self, params):
           # Custom logic here
           pass


4. TESTING INTEGRATION:

   def test_glue_spray_state_machine():
       original_app = MockGlueSprayingApplication()
       enhanced_app = create_enhanced_glue_spray_application(original_app)
       
       test_framework = StateMachineTestFramework(enhanced_app.state_machine)
       
       # Mock external dependencies
       test_framework.mock_callback('execute_operation', return_value="success")
       
       # Run test scenarios
       test_framework.run_test_scenario("Basic Operation", [
           {'type': 'assert_state', 'state': 'IDLE'},
           {'type': 'event', 'event': 'START_REQUESTED'},
           {'type': 'assert_state', 'state': 'EXECUTING_TRAJECTORY'},
           {'type': 'event', 'event': 'OPERATION_COMPLETED'},
           {'type': 'assert_state', 'state': 'IDLE'}
       ])
       
       test_framework.print_summary()


5. MONITORING AND METRICS:

   class MonitoredGlueSprayApp(GlueSprayApplicationAdapter):
       def __init__(self, original_app, metrics_collector):
           super().__init__(original_app)
           self.metrics = metrics_collector
           
           # Register monitoring callbacks
           self.context.register_callback('on_state_changed', self.log_state_change)
           self.context.register_callback('on_error', self.log_error)
       
       def log_state_change(self, params):
           transition_time = time.time()
           from_state = params.get('from_state')
           to_state = params.get('to_state')
           
           self.metrics.record_state_transition(from_state, to_state, transition_time)
       
       def log_error(self, params):
           error = params.get('error')
           state = self.get_current_state()
           
           self.metrics.record_error(error, state, time.time())
"""
# MOCK ORIGINAL APPLICATION (for demonstration)
# ============================================================================

class MockGlueSprayingApplication:
    """Mock of the original GlueSprayingApplication for demonstration"""

    def __init__(self, callback=None, vision=None, settings=None, glue=None,
                 workpiece=None, robot=None, calib=None):
        self.callback = callback
        self.vision = vision
        self.settings = settings
        self.glue = glue
        self.workpiece = workpiece
        self.robotService = robot
        self.calib = calib
        self.state = "IDLE"  # Original had this attribute

        # Mock some additional attributes that might exist
        self.last_operation_result = None
        self.error_count = 0

    def start(self, contourMatching=True):
        """Original start method"""
        print(f"[ORIGINAL] Starting glue spray operation with contourMatching={contourMatching}")
        time.sleep(0.1)  # Simulate work
        self.last_operation_result = "Trajectory executed successfully"
        return True, "Operation completed", self.last_operation_result

    def calibrateRobot(self):
        """Original robot calibration method"""
        print("[ORIGINAL] Calibrating robot...")
        time.sleep(0.1)  # Simulate work
        return True, "Robot calibrated", {"calibration_data": "mock_data"}

    def calibrateCamera(self):
        """Original camera calibration method"""
        print("[ORIGINAL] Calibrating camera...")
        time.sleep(0.1)  # Simulate work
        return True, "Camera calibrated", None

    def createWorkpiece(self):
        """Original workpiece creation method"""
        print("[ORIGINAL] Creating workpiece...")
        time.sleep(0.1)  # Simulate work
        return True, "Workpiece created"

    def measureHeight(self):
        """Original height measurement method"""
        print("[ORIGINAL] Measuring height...")
        time.sleep(0.1)  # Simulate work
        return True, "Height measured", 42.5

    def updateToolChangerStation(self):
        """Original tool changer update method"""
        print("[ORIGINAL] Updating tool changer...")
        time.sleep(0.1)  # Simulate work
        return True, "Tool changer updated"

    def handleBelt(self):
        """Original belt handling method"""
        print("[ORIGINAL] Handling belt...")
        time.sleep(0.1)  # Simulate work
        return True, "Belt handled"

    def testRun(self):
        """Original test run method"""
        print("[ORIGINAL] Running test...")
        time.sleep(0.1)  # Simulate work
        return True, "Test completed"


class MockRobotService:
    """Mock robot service for demonstration"""

    def moveToStartPosition(self):
        print("[ROBOT] Moving to start position")
        return True


# ============================================================================
# MIGRATION DEMONSTRATION
# ============================================================================

def demonstrate_migration():
    """Show step-by-step migration from original to enhanced application"""

    print("=" * 80)
    print("MIGRATION DEMONSTRATION")
    print("=" * 80)

    # Step 1: Original application usage
    print("\n1. ORIGINAL APPLICATION USAGE")
    print("-" * 40)

    robot_service = MockRobotService()
    original_app = MockGlueSprayingApplication(
        callback=None, vision=None, settings=None,
        glue=None, workpiece=None, robot=robot_service, calib=None
    )

    # Original way of using the application
    print("Original usage:")
    result = original_app.start(contourMatching=True)
    print(f"Result: {result}")

    result = original_app.calibrateRobot()
    print(f"Result: {result}")

    # Step 2: Enhanced application with backward compatibility
    print("\n2. ENHANCED APPLICATION (Backward Compatible)")
    print("-" * 50)

    enhanced_app = create_enhanced_glue_spray_application(original_app)

    print("Enhanced usage (same API, but with state machine):")
    result = enhanced_app.start(contourMatching=True)
    print(f"Result: {result}")
    print(f"Current state: {enhanced_app.get_current_state()}")

    # Wait for operation to complete
    time.sleep(0.2)
    print(f"State after operation: {enhanced_app.get_current_state()}")

    # Step 3: New capabilities
    print("\n3. NEW CAPABILITIES")
    print("-" * 25)

    print("Available operations:", enhanced_app.get_available_operations())

    # Try emergency stop
    print("\nTesting emergency stop:")
    enhanced_app.emergency_stop()
    print(f"State after emergency stop: {enhanced_app.get_current_state()}")
    print("Available operations:", enhanced_app.get_available_operations())

    # Reset system
    print("\nResetting system:")
    enhanced_app.reset()
    time.sleep(0.1)
    print(f"State after reset: {enhanced_app.get_current_state()}")

    # Show state history
    print("\nState transition history:")
    history = enhanced_app.get_state_history()
    for i, transition in enumerate(history[-5:], 1):
        print(f"  {i}. {transition['from_state']} -> {transition['to_state']}")

    enhanced_app.stop()


# ============================================================================
# CONFIGURATION-DRIVEN DEMONSTRATION
# ============================================================================

def demonstrate_configuration_driven():
    """Show how to use configuration-driven state machine"""

    print("\n" + "=" * 80)
    print("CONFIGURATION-DRIVEN STATE MACHINE")
    print("=" * 80)

    # Create original application
    robot_service = MockRobotService()
    original_app = MockGlueSprayingApplication(robot=robot_service)

    # Create from configuration
    config_app = create_glue_spray_from_config(original_app, GLUE_SPRAY_CONFIG)

    print("Configuration-based state machine created")
    print(f"Initial state: {config_app.get_current_state()}")

    # Process events
    print("\nProcessing START_REQUESTED event:")
    config_app.process_event("START_REQUESTED", {"contour_matching": True})
    time.sleep(0.1)
    print(f"Current state: {config_app.get_current_state()}")

    # Simulate operation completion
    print("\nSimulating operation completion:")
    config_app.process_event("OPERATION_COMPLETED")
    time.sleep(0.1)
    print(f"Final state: {config_app.get_current_state()}")


# ============================================================================

# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def main():
    """Run all demonstrations"""

    print("GENERIC STATE MACHINE REFACTORING DEMONSTRATION")
    print("=" * 80)
    print("This demonstration shows the complete refactoring from a")
    print("tightly-coupled glue spraying state machine to a generic,")
    print("reusable state machine framework.")

    try:
        # Run all demonstrations
        demonstrate_migration()
        demonstrate_configuration_driven()
        demonstrate_generic_framework()
        demonstrate_testing()
        demonstrate_performance()

        print("\n" + "=" * 80)
        print("SUMMARY OF BENEFITS")
        print("=" * 80)
        print("✓ Backward compatibility - existing code continues to work")
        print("✓ Generic framework - reusable across different applications")
        print("✓ Configuration-driven - behavior changes without code changes")
        print("✓ Enhanced functionality - emergency stop, pause/resume, state history")
        print("✓ Better testing - mock callbacks, test scenarios")
        print("✓ Improved error handling - configurable error recovery")
        print("✓ State validation - prevent invalid operations")
        print("✓ Monitoring - state history and transition logging")

        print("\n" + "=" * 80)
        print("NEXT STEPS FOR INTEGRATION")
        print("=" * 80)
        print("1. Replace existing state machine with GlueSprayApplicationAdapter")
        print("2. Update tests to use StateMachineTestFramework")
        print("3. Gradually migrate other applications to use generic framework")
        print("4. Create configuration files for different environments")
        print("5. Add monitoring and metrics collection")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()