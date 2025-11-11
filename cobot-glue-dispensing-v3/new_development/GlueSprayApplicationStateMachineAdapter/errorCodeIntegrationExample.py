"""
Comprehensive Error Code Integration Example

This demonstrates how the error code system integrates with the generic state machine
and provides real-world examples of error handling, recovery, and monitoring.
"""

from new_development.GlueSprayApplicationStateMachineAdapter.MigrationDemonstration import MockGlueSprayingApplication, MockRobotService

from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import *


from new_development.GlueSprayApplicationStateMachineAdapter.adapterV2 import *



# ============================================================================
# ENHANCED MOCK APPLICATION WITH REALISTIC ERROR SIMULATION
# ============================================================================

class RealisticMockGlueSprayingApplication(MockGlueSprayingApplication):
    """Enhanced mock that simulates realistic errors"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_modes = {
            'robot_connection_unstable': False,
            'camera_intermittent': False,
            'glue_low': False,
            'safety_fence_issue': False,
            'emergency_stop_test': False
        }
        self.operation_count = 0
        self.last_error_time = 0

    def set_failure_mode(self, mode: str, enabled: bool):
        """Enable/disable specific failure modes for testing"""
        if mode in self.failure_modes:
            self.failure_modes[mode] = enabled
            print(f"Failure mode '{mode}' {'enabled' if enabled else 'disabled'}")

    def start(self, contourMatching=True):
        """Start with realistic error simulation"""
        self.operation_count += 1

        # Simulate robot connection issues
        if self.failure_modes['robot_connection_unstable'] and self.operation_count % 3 == 0:
            raise Exception("Robot connection timeout - please check network")

        # Simulate emergency stop
        if self.failure_modes['emergency_stop_test']:
            self.failure_modes['emergency_stop_test'] = False  # One-time trigger
            raise Exception("Emergency stop activated by operator")

        # Simulate glue system issues
        if self.failure_modes['glue_low'] and self.operation_count % 5 == 0:
            raise Exception("Glue reservoir pressure low - refill required")

        print(f"[REALISTIC] Starting trajectory operation #{self.operation_count}")
        time.sleep(0.1)
        return True, "Operation completed", f"Trajectory {self.operation_count} executed"

    def calibrateRobot(self):
        """Robot calibration with error simulation"""
        if self.failure_modes['robot_connection_unstable'] and time.time() - self.last_error_time > 2:
            self.last_error_time = time.time()
            raise Exception("Robot servo error during calibration")

        print("[REALISTIC] Robot calibration with potential issues...")
        time.sleep(0.1)
        return True, "Robot calibrated", {"accuracy": "±0.1mm"}

    def calibrateCamera(self):
        """Camera calibration with intermittent issues"""
        if self.failure_modes['camera_intermittent'] and self.operation_count % 4 == 0:
            raise Exception("Camera connection lost during calibration")

        print("[REALISTIC] Camera calibration...")
        time.sleep(0.1)
        return True, "Camera calibrated", None

    def createWorkpiece(self):
        """Workpiece creation with vision errors"""
        if self.failure_modes['camera_intermittent']:
            raise Exception("Vision algorithm failed - insufficient lighting")

        print("[REALISTIC] Creating workpiece...")
        time.sleep(0.1)
        return True, "Workpiece created"


# ============================================================================
# ERROR MONITORING AND REPORTING
# ============================================================================

class ErrorMonitor:
    """Advanced error monitoring and reporting system"""

    def __init__(self, application_adapter: GlueSprayApplicationAdapter):
        self.app = application_adapter
        self.error_tracker = application_adapter.context.error_tracker
        self.monitoring_active = False
        self.alert_thresholds = {
            'error_rate_per_hour': 10,
            'critical_error_count': 3,
            'consecutive_failures': 5
        }
        self.alerts_sent = []

    def start_monitoring(self):
        """Start continuous error monitoring"""
        self.monitoring_active = True
        print("Error monitoring started")

    def stop_monitoring(self):
        """Stop error monitoring"""
        self.monitoring_active = False
        print("Error monitoring stopped")

    def generate_error_report(self) -> Dict[str, Any]:
        """Generate comprehensive error report"""
        recent_errors = self.error_tracker.get_recent_errors(50)
        active_errors = self.error_tracker.get_active_errors()

        # Categorize errors
        error_by_category = {}
        error_by_severity = {}
        error_timeline = []

        for error_context in recent_errors:
            error_info = ERROR_REGISTRY.get_error_info(error_context.code)
            if error_info:
                category = error_info.category.value
                severity = error_info.severity.name

                error_by_category[category] = error_by_category.get(category, 0) + 1
                error_by_severity[severity] = error_by_severity.get(severity, 0) + 1

                error_timeline.append({
                    'timestamp': error_context.timestamp,
                    'code': error_context.code,
                    'name': error_info.name,
                    'severity': severity,
                    'state': error_context.state,
                    'operation': error_context.operation
                })

        # Calculate error rates
        if recent_errors:
            time_span = time.time() - recent_errors[0].timestamp
            error_rate_per_hour = len(recent_errors) / (time_span / 3600) if time_span > 0 else 0
        else:
            error_rate_per_hour = 0

        # System health assessment
        health_score = self._calculate_health_score(error_by_severity, active_errors)

        report = {
            'timestamp': time.time(),
            'system_health_score': health_score,
            'error_rate_per_hour': round(error_rate_per_hour, 2),
            'total_errors': len(recent_errors),
            'active_errors': len(active_errors),
            'errors_by_category': error_by_category,
            'errors_by_severity': error_by_severity,
            'error_timeline': error_timeline[-10:],  # Last 10 errors
            'active_error_details': [
                {
                    'code': ec.code,
                    'name': ERROR_REGISTRY.get_error_info(ec.code).name if ERROR_REGISTRY.get_error_info(
                        ec.code) else 'Unknown',
                    'state': ec.state,
                    'operation': ec.operation,
                    'timestamp': ec.timestamp
                }
                for ec in active_errors
            ],
            'recommendations': self._generate_recommendations(error_by_category, error_by_severity, active_errors)
        }

        return report

    def _calculate_health_score(self, error_by_severity: Dict, active_errors: List) -> int:
        """Calculate system health score (0-100)"""
        base_score = 100

        # Deduct points for errors by severity
        deductions = {
            'FATAL': 50,
            'CRITICAL': 20,
            'ERROR': 5,
            'WARNING': 2,
            'INFO': 1
        }

        for severity, count in error_by_severity.items():
            deduction = deductions.get(severity, 0) * count
            base_score -= deduction

        # Additional deduction for active errors
        base_score -= len(active_errors) * 10

        return max(0, min(100, base_score))

    def _generate_recommendations(self, error_by_category: Dict, error_by_severity: Dict, active_errors: List) -> List[
        str]:
        """Generate actionable recommendations based on error patterns"""
        recommendations = []

        # Category-based recommendations
        if error_by_category.get('HARDWARE', 0) > 5:
            recommendations.append("High hardware error rate detected. Schedule maintenance check.")

        if error_by_category.get('COMMUNICATION', 0) > 3:
            recommendations.append("Communication issues detected. Check network connectivity.")

        if error_by_category.get('SAFETY', 0) > 0:
            recommendations.append("Safety errors detected. Review safety procedures immediately.")

        # Severity-based recommendations
        if error_by_severity.get('CRITICAL', 0) > 2:
            recommendations.append("Multiple critical errors. Consider system restart.")

        if error_by_severity.get('FATAL', 0) > 0:
            recommendations.append("Fatal errors present. System shutdown recommended.")

        # Active error recommendations
        for error_context in active_errors:
            error_info = ERROR_REGISTRY.get_error_info(error_context.code)
            if error_info and error_info.suggested_action:
                recommendations.append(f"Active Error {error_context.code}: {error_info.suggested_action}")

        return recommendations[:5]  # Limit to top 5 recommendations

    def check_alert_conditions(self) -> List[str]:
        """Check if any alert conditions are met"""
        alerts = []
        recent_errors = self.error_tracker.get_recent_errors(20)

        # Error rate check
        if len(recent_errors) >= 10:
            time_span = time.time() - recent_errors[0].timestamp
            if time_span > 0:
                error_rate = len(recent_errors) / (time_span / 3600)
                if error_rate > self.alert_thresholds['error_rate_per_hour']:
                    alerts.append(f"High error rate: {error_rate:.1f} errors/hour")

        # Critical error count
        critical_errors = [e for e in recent_errors
                           if ERROR_REGISTRY.get_error_info(e.code) and
                           ERROR_REGISTRY.get_error_info(e.code).severity >= ErrorSeverity.CRITICAL]
        if len(critical_errors) >= self.alert_thresholds['critical_error_count']:
            alerts.append(f"Multiple critical errors: {len(critical_errors)} in recent history")

        return alerts


# ============================================================================
# ERROR RECOVERY TESTING
# ============================================================================

class ErrorRecoveryTester:
    """Test error recovery strategies"""

    def __init__(self, application_adapter: GlueSprayApplicationAdapter):
        self.app = application_adapter
        self.test_results = []

    def test_retry_recovery(self):
        """Test retry recovery strategy"""
        print("\n" + "=" * 50)
        print("TESTING RETRY RECOVERY STRATEGY")
        print("=" * 50)

        # Enable intermittent camera issues
        if hasattr(self.app.original_app, 'set_failure_mode'):
            self.app.original_app.set_failure_mode('camera_intermittent', True)

        try:
            # Attempt camera calibration (should fail and retry)
            result = self.app.calibrateCamera()
            print(f"Result: {result}")

            # Wait for recovery attempt
            time.sleep(2)

            # Check if error was recovered
            active_errors = self.app.context.error_tracker.get_active_errors()
            recovery_successful = len(active_errors) == 0

            self.test_results.append({
                'test': 'retry_recovery',
                'success': recovery_successful,
                'details': f"Active errors after retry: {len(active_errors)}"
            })

        finally:
            if hasattr(self.app.original_app, 'set_failure_mode'):
                self.app.original_app.set_failure_mode('camera_intermittent', False)

    def test_safe_position_recovery(self):
        """Test safe position recovery strategy"""
        print("\n" + "=" * 50)
        print("TESTING SAFE POSITION RECOVERY")
        print("=" * 50)

        # Trigger emergency stop
        if hasattr(self.app.original_app, 'set_failure_mode'):
            self.app.original_app.set_failure_mode('emergency_stop_test', True)

        try:
            # Attempt start operation (should trigger emergency stop)
            self.app.start(contourMatching=True)
        except Exception as e:
            print(f"Expected error occurred: {e}")

        # Wait for recovery
        time.sleep(1)

        # Check if system moved to safe position (error state)
        current_state = self.app.get_current_state()
        recovery_successful = current_state == "ERROR"

        self.test_results.append({
            'test': 'safe_position_recovery',
            'success': recovery_successful,
            'details': f"Final state: {current_state}"
        })

        # Reset system
        if recovery_successful:
            self.app.reset()
            time.sleep(0.5)

    def test_error_escalation(self):
        """Test error escalation for persistent failures"""
        print("\n" + "=" * 50)
        print("TESTING ERROR ESCALATION")
        print("=" * 50)

        # Enable persistent robot connection issues
        if hasattr(self.app.original_app, 'set_failure_mode'):
            self.app.original_app.set_failure_mode('robot_connection_unstable', True)

        failure_count = 0
        try:
            # Attempt multiple operations to trigger escalation
            for i in range(5):
                try:
                    self.app.calibrateRobot()
                    time.sleep(0.5)
                except Exception:
                    failure_count += 1
                    print(f"Failure #{failure_count}")
                    time.sleep(0.5)

            # Check if errors were properly escalated
            recent_errors = self.app.context.error_tracker.get_recent_errors(10)
            robot_errors = [e for e in recent_errors
                            if e.code == HardwareErrorCode.ROBOT_CONNECTION_FAILED]

            escalation_successful = len(robot_errors) >= 3

            self.test_results.append({
                'test': 'error_escalation',
                'success': escalation_successful,
                'details': f"Robot errors recorded: {len(robot_errors)}, Failures: {failure_count}"
            })

        finally:
            if hasattr(self.app.original_app, 'set_failure_mode'):
                self.app.original_app.set_failure_mode('robot_connection_unstable', False)

    def print_test_results(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("ERROR RECOVERY TEST RESULTS")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "No tests")

        print("\nDetailed Results:")
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"  {result['test']}: {status} - {result['details']}")


# ============================================================================
# COMPREHENSIVE DEMONSTRATION
# ============================================================================

def demonstrate_complete_error_system():
    """Complete demonstration of the error code system integration"""

    print("=" * 80)
    print("COMPREHENSIVE ERROR CODE SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("This demonstration shows how error codes integrate with the state machine")
    print("to provide robust error handling, recovery, and monitoring.")

    # Create realistic application with error simulation
    robot_service = MockRobotService()
    original_app = RealisticMockGlueSprayingApplication(robot=robot_service)
    enhanced_app = create_enhanced_glue_spray_application(original_app)

    # Create error monitor
    error_monitor = ErrorMonitor(enhanced_app)
    error_monitor.start_monitoring()

    print("\n1. NORMAL OPERATIONS WITH ERROR TRACKING")
    print("-" * 45)

    # Perform some normal operations
    operations = [
        lambda: enhanced_app.start(contourMatching=True),
        lambda: enhanced_app.calibrateRobot(),
        lambda: enhanced_app.calibrateCamera(),
        lambda: enhanced_app.createWorkpiece()
    ]

    for i, operation in enumerate(operations, 1):
        try:
            print(f"\nOperation {i}:")
            result = operation()
            print(f"  Result: {result}")
            time.sleep(0.2)  # Allow state machine processing
            print(f"  Current state: {enhanced_app.get_current_state()}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n2. SIMULATED ERROR CONDITIONS")
    print("-" * 35)

    # Enable various failure modes and test error handling
    test_scenarios = [
        ('robot_connection_unstable', lambda: enhanced_app.calibrateRobot()),
        ('camera_intermittent', lambda: enhanced_app.calibrateCamera()),
        ('emergency_stop_test', lambda: enhanced_app.start()),
    ]

    for failure_mode, operation in test_scenarios:
        print(f"\nTesting {failure_mode}:")
        original_app.set_failure_mode(failure_mode, True)

        try:
            result = operation()
            print(f"  Unexpected success: {result}")
        except StateMachineError as e:
            print(f"  Caught StateMachineError [{e.code}]: {e.message}")
            print(f"  Severity: {e.severity.name}")
            print(f"  Recovery Possible: {e.recovery_possible}")
        except Exception as e:
            print(f"  Caught generic error: {e}")

        # Wait for error recovery attempts
        time.sleep(1)
        print(f"  Final state: {enhanced_app.get_current_state()}")

        # Reset if in error state
        if enhanced_app.get_current_state() == "ERROR":
            enhanced_app.reset()
            time.sleep(0.5)

    print("\n3. ERROR RECOVERY TESTING")
    print("-" * 30)

    # Test error recovery strategies
    recovery_tester = ErrorRecoveryTester(enhanced_app)
    recovery_tester.test_retry_recovery()
    recovery_tester.test_safe_position_recovery()
    recovery_tester.test_error_escalation()
    recovery_tester.print_test_results()

    print("\n4. ERROR MONITORING AND REPORTING")
    print("-" * 38)

    # Generate comprehensive error report
    error_report = error_monitor.generate_error_report()

    print(f"System Health Score: {error_report['system_health_score']}/100")
    print(f"Error Rate: {error_report['error_rate_per_hour']} errors/hour")
    print(f"Total Errors: {error_report['total_errors']}")
    print(f"Active Errors: {error_report['active_errors']}")

    print("\nErrors by Category:")
    for category, count in error_report['errors_by_category'].items():
        print(f"  {category}: {count}")

    print("\nErrors by Severity:")
    for severity, count in error_report['errors_by_severity'].items():
        print(f"  {severity}: {count}")

    if error_report['recommendations']:
        print("\nRecommendations:")
        for rec in error_report['recommendations']:
            print(f"  • {rec}")

    # Check alert conditions
    alerts = error_monitor.check_alert_conditions()
    if alerts:
        print("\n⚠️  ALERTS:")
        for alert in alerts:
            print(f"  • {alert}")

    print("\n5. ERROR CODE LOOKUP EXAMPLES")
    print("-" * 35)

    # Demonstrate error code lookup
    example_codes = [
        HardwareErrorCode.ROBOT_CONNECTION_FAILED,
        SafetyErrorCode.EMERGENCY_STOP_ACTIVATED,
        ValidationErrorCode.SAFETY_CHECK_FAILED,
        OperationErrorCode.OPERATION_TIMEOUT
    ]

    for code in example_codes:
        error_info = ERROR_REGISTRY.get_error_info(code)
        if error_info:
            print(f"\nError Code {code}:")
            print(f"  Name: {error_info.name}")
            print(f"  Category: {error_info.category.value}")
            print(f"  Severity: {error_info.severity.name}")
            print(f"  Action: {error_info.suggested_action}")
            print(f"  Recovery: {'Yes' if error_info.recovery_possible else 'No'}")

    print("\n6. ERROR EXPORT FOR ANALYSIS")
    print("-" * 32)

    # Export error log for analysis
    error_log = enhanced_app.context.error_tracker.export_error_log()

    print(f"Exported {len(error_log)} error entries")
    if error_log:
        print("\nSample error entry:")
        sample_entry = error_log[-1]  # Most recent
        print(json.dumps(sample_entry, indent=2, default=str))

    # Cleanup
    error_monitor.stop_monitoring()
    enhanced_app.stop()

    print("\n" + "=" * 80)
    print("ERROR SYSTEM SUMMARY")
    print("=" * 80)
    print("✓ Comprehensive error codes defined (1000-7999 range)")
    print("✓ Automatic error classification by category and severity")
    print("✓ Intelligent error recovery strategies")
    print("✓ Real-time error monitoring and alerting")
    print("✓ Detailed error reporting and analysis")
    print("✓ Error export for external analysis tools")
    print("✓ Backward compatibility with existing error handling")

    print("\n" + "=" * 80)
    print("INTEGRATION BENEFITS")
    print("=" * 80)
    print("• Standardized error identification across all components")
    print("• Automated error recovery reduces downtime")
    print("• Proactive monitoring prevents system failures")
    print("• Detailed error tracking enables predictive maintenance")
    print("• Clear error messages and suggested actions improve debugging")
    print("• Configurable recovery strategies for different error types")


if __name__ == "__main__":
    demonstrate_complete_error_system()

# ============================================================================
# USAGE EXAMPLES FOR REAL INTEGRATION
# ============================================================================

"""
REAL INTEGRATION EXAMPLES FOR ERROR CODES:

1. BASIC ERROR HANDLING:

   try:
       enhanced_app.start(contourMatching=True)
   except StateMachineError as e:
       print(f"Error {e.code}: {e.message}")
       print(f"Suggested action: {e.suggested_action}")
       if e.recovery_possible:
           # Attempt recovery
           enhanced_app.reset()

2. CUSTOM ERROR RECOVERY:

   class CustomRecoveryStrategy(ErrorRecoveryStrategy):
       def __init__(self):
           super().__init__([HardwareErrorCode.GLUE_RESERVOIR_EMPTY])

       def recover(self, error_context, state_machine):
           # Custom logic to handle glue reservoir empty
           notify_operator("Please refill glue reservoir")
           wait_for_operator_confirmation()
           return True

3. ERROR MONITORING INTEGRATION:

   # Setup monitoring
   monitor = ErrorMonitor(enhanced_app)
   monitor.start_monitoring()

   # Periodic health checks
   def health_check():
       report = monitor.generate_error_report()
       if report['system_health_score'] < 70:
           send_maintenance_alert(report)

   # Schedule health_check() to run every hour

4. CONFIGURATION-BASED ERROR HANDLING:

   error_config = {
       "retry_errors": [3001, 3101, 6002],  # Robot, Camera, Timeout
       "safe_position_errors": [3005, 7001, 7002],  # Emergency, Safety
       "max_retries": 3,
       "retry_delay": 2.0
   }

   # Apply configuration to recovery manager
   enhanced_app.context.error_recovery_manager.configure(error_config)

5. ERROR LOGGING INTEGRATION:

   import logging

   class ErrorLogger:
       def __init__(self, app):
           self.app = app
           self.logger = logging.getLogger('glue_spray_errors')

       def log_error(self, error_code, message, context):
           error_info = ERROR_REGISTRY.get_error_info(error_code)
           self.logger.error(f"[{error_code}] {error_info.name}: {message}", 
                           extra={'context': context, 'severity': error_info.severity.name})
"""