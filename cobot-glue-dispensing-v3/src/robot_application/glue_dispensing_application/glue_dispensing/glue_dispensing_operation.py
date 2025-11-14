import time
import json
import os
from datetime import datetime

from robot_application.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey
from robot_application.glue_dispensing_application.glue_dispensing.ExecutionContext import ExecutionContext
from modules.glueSprayService.GlueSprayService import GlueSprayService

from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState

from backend.system.utils.custom_logging import log_debug_message, log_info_message, log_error_message, \
    log_calls_with_timestamp_decorator, setup_logger, LoggerContext
from robot_application.glue_dispensing_application.glue_dispensing.PumpController import PumpController
# glue dispensing process configuration
USE_SEGMENT_SETTINGS = True
TURN_OFF_PUMP_BETWEEN_PATHS = True
ADJUST_PUMP_SPEED_WHILE_SPRAY = True

# logging configuration
ENABLE_GLUE_DISPENSING_LOGGING = True
glue_dispensing_logger = setup_logger("Glue Dispensing") if ENABLE_GLUE_DISPENSING_LOGGING else None
glue_dispensing_logger_context = LoggerContext(enabled=ENABLE_GLUE_DISPENSING_LOGGING, logger=glue_dispensing_logger)

# debug configuration
ENABLE_CONTEXT_DEBUG = True
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "debug")

class GlueDispensingOperation:
    def __init__(self, robot_service, glue_application=None):
        self.robot_service = robot_service
        self.glue_application = glue_application
        
        # Get glue settings from the glue application
        if glue_application is not None:
            glue_settings = glue_application.get_glue_settings()
        else:
            # Fallback to default settings if no application provided
            from robot_application.glue_dispensing_application.settings.GlueSettings import GlueSettings
            glue_settings = GlueSettings()
        
        self.glue_service = GlueSprayService(
                generatorTurnOffTimeout=10,
                settings=glue_settings
            )

        self.pump_controller = PumpController(USE_SEGMENT_SETTINGS, glue_dispensing_logger_context, glue_settings)
        # Execution context for pause/resume
        # ✅ Initialize control flags and state variables

        self.motor_started = False
        self.resume_requested = False
        self.pause_requested = False
        self.stop_requested = False

        self.execution_context = ExecutionContext()

        # Create debug directory if it doesn't exist
        if ENABLE_CONTEXT_DEBUG:
            os.makedirs(DEBUG_DIR, exist_ok=True)

    def _write_context_debug(self, state_name: str):
        """
        Write execution context to debug file after state execution.

        Args:
            state_name: Name of the state that just completed
        """
        if not ENABLE_CONTEXT_DEBUG:
            return

        try:
            # Create debug directory if it doesn't exist
            os.makedirs(DEBUG_DIR, exist_ok=True)

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            # Get context as dict
            context_dict = self.execution_context.to_debug_dict()

            # Add metadata
            debug_data = {
                "timestamp": timestamp,
                "state": state_name,
                "context": context_dict
            }

            # Generate filename
            filename = f"{timestamp}_{state_name}.json"
            filepath = os.path.join(DEBUG_DIR, filename)

            # Write to file
            with open(filepath, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)

            log_debug_message(
                glue_dispensing_logger_context,
                message=f"Debug context written to: {filename}"
            )

        except Exception as e:
            log_error_message(
                glue_dispensing_logger_context,
                message=f"Failed to write debug context: {e}"
            )

    def setup_execution_context(self,paths,spray_on):
        self.execution_context.reset()
        self.execution_context.paths = paths
        self.execution_context.spray_on = spray_on
        self.execution_context.service = self.glue_service
        self.execution_context.robot_service = self.robot_service
        # Use the application's glue process state machine instead of robot service state machine
        self.execution_context.state_machine = getattr(self.glue_application, 'glue_process_state_machine', None)
        self.execution_context.glue_type = self.glue_service.glueA_addresses
        self.execution_context.current_path_index = 0
        self.execution_context.current_point_index = 0
        self.execution_context.is_resuming = False
        self.execution_context.current_settings = None
        self.execution_context.pump_controller = self.pump_controller

        # ✅ Add these for pump adjustment
        self.execution_context.pump_thread = None
        self.execution_context.pump_ready_event = None

    @log_calls_with_timestamp_decorator(enabled=ENABLE_GLUE_DISPENSING_LOGGING, logger=glue_dispensing_logger)
    def start(self, paths, spray_on=False, resume=False):
        """Main path execution method with proper state management"""
        message = f"Resuming from execution context: {self.execution_context}" if resume and self.execution_context.has_valid_context() else f"Starting new execution with {len(paths)} paths, spray_on={spray_on}"
        log_debug_message(glue_dispensing_logger_context,        message=message)

        if resume is False or not self.execution_context.has_valid_context():
          self.setup_execution_context(paths,spray_on)

          # ✅ Ensure proper state transition before execution
          if self.execution_context.state_machine.state == GlueProcessState.IDLE:
              self.execution_context.state_machine.transition(GlueProcessState.STARTING)
              log_debug_message(glue_dispensing_logger_context,
                                message="Transitioned from IDLE to STARTING to begin execution")

        try:
            # Main execution loop
            while self.execution_context.state_machine.state not in [GlueProcessState.COMPLETED, GlueProcessState.ERROR]:
                current_state = self.execution_context.state_machine.state
                log_debug_message(glue_dispensing_logger_context,
                                  message=f"Execution loop - Current State: {current_state}")

                if current_state == GlueProcessState.PAUSED:
                    self.execution_context.robot_service.robotStateManager.trajectoryUpdate = False
                    log_debug_message(glue_dispensing_logger_context,
                                      message=f"In PAUSED state - trajectoryUpdate set to {self.execution_context.robot_service.robotStateManager.trajectoryUpdate}")

                    time.sleep(0.5)
                    continue

                elif current_state == GlueProcessState.STOPPED:
                    self.execution_context.robot_service.robotStateManager.trajectoryUpdate = False
                    log_debug_message(glue_dispensing_logger_context, message="Execution stopped, completing...")
                    self.execution_context.state_machine.transition(GlueProcessState.COMPLETED)
                    break


                elif current_state == GlueProcessState.INITIALIZING:
                    # Transition from INITIALIZING to IDLE, then to STARTING
                    log_debug_message(glue_dispensing_logger_context,
                                      message="Transitioning from INITIALIZING to IDLE")
                    self.execution_context.state_machine.transition(GlueProcessState.IDLE)
                    continue

                elif current_state == GlueProcessState.IDLE:
                    # Transition from IDLE to STARTING to begin execution
                    log_debug_message(glue_dispensing_logger_context,
                                      message="Transitioning from IDLE to STARTING to begin execution")
                    self.execution_context.state_machine.transition(GlueProcessState.STARTING)
                    continue

                elif current_state == GlueProcessState.STARTING:

                    result = self._handle_starting_state(self.execution_context)
                    # Explicitly update execution context
                    ctx = self.execution_context
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.current_path = result.next_path
                    ctx.current_settings = result.next_settings
                    # Apply the state transition explicitly
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("STARTING")
                    # Log cleanly
                    log_debug_message(
                        glue_dispensing_logger_context,
                        message=(
                            f"STARTING handler → handled={result.handled}, resume={result.resume}, "
                            f"path_index={ctx.current_path_index}, point_index={ctx.current_point_index}, "
                            f"next_state={result.next_state}"
                        ),
                    )

                elif current_state == GlueProcessState.MOVING_TO_FIRST_POINT:
                    result = self._handle_moving_to_first_point_state(self.execution_context, resume)
                    ctx = self.execution_context
                    # Apply result to context (explicitly)
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.current_path = result.next_path
                    ctx.current_settings = result.next_settings
                    # Transition state based on result
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("MOVING_TO_FIRST_POINT")

                elif current_state == GlueProcessState.EXECUTING_PATH:
                    self.execution_context.state_machine.transition(GlueProcessState.PUMP_INITIAL_BOOST)
                    # Write debug context
                    self._write_context_debug("EXECUTING_PATH")

                elif current_state == GlueProcessState.PUMP_INITIAL_BOOST:
                    result = self._handle_pump_initial_boost(self.execution_context)
                    ctx = self.execution_context
                    # Explicitly apply result (no internal mutation)
                    ctx.motor_started = result.motor_started
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.current_path = result.next_path
                    ctx.current_settings = result.next_settings
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("PUMP_INITIAL_BOOST")

                elif current_state == GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD:
                    result = self._handle_start_pump_adjustment_thread(self.execution_context)
                    ctx = self.execution_context
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.current_path = result.next_path
                    ctx.current_settings = result.next_settings
                    # ✅ store thread + event in context
                    ctx.pump_thread = result.pump_thread
                    ctx.pump_ready_event = result.pump_ready_event
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("STARTING_PUMP_ADJUSTMENT_THREAD")

                elif current_state == GlueProcessState.SENDING_PATH_POINTS:

                    result = self._handle_send_path_to_robot_state(self.execution_context)
                    ctx = self.execution_context
                    # Update context explicitly
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.current_path = result.next_path
                    ctx.current_settings = result.next_settings
                    # Now handle the state transition in one place
                    if not result.handled:
                        ctx.state_machine.transition(GlueProcessState.ERROR)
                    elif result.resume:
                        ctx.state_machine.transition(GlueProcessState.PAUSED)
                    else:
                        ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("SENDING_PATH_POINTS")

                elif current_state == GlueProcessState.WAIT_FOR_PATH_COMPLETION:
                    result = self._handle_wait_for_path_completion(self.execution_context)
                    ctx = self.execution_context
                    # Update context with captured progress from pump thread
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("WAIT_FOR_PATH_COMPLETION")

                elif current_state == GlueProcessState.TRANSITION_BETWEEN_PATHS:
                    result = self._handle_transition_between_paths(self.execution_context)
                    ctx = self.execution_context
                    ctx.current_path_index = result.next_path_index
                    ctx.current_point_index = result.next_point_index
                    ctx.state_machine.transition(result.next_state)
                    # Write debug context
                    self._write_context_debug("TRANSITION_BETWEEN_PATHS")

                else:
                    log_debug_message(glue_dispensing_logger_context,
                                      message=f"Unexpected state in execution loop: {current_state}")
                    break


            self.execution_context.pump_controller.pump_off(self.execution_context.service,self.execution_context.robot_service,self.execution_context.glue_type,self.execution_context.current_settings)

            # Guard: current_settings may be None if no valid path/settings were established
            if self.execution_context.current_settings and isinstance(self.execution_context.current_settings, dict):
                timeout_before_generator_off = float(
                    self.execution_context.current_settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, 1))
            else:
                # Fallback safe default
                timeout_before_generator_off = 1.0

            log_info_message(glue_dispensing_logger_context,
                             message=f"Waiting {timeout_before_generator_off}s before turning generator off")
            time.sleep(timeout_before_generator_off)

            self.execution_context.service.generatorOff()
            log_info_message(glue_dispensing_logger_context,
                             message=f"Generator turned off after waiting {timeout_before_generator_off}s")
            self.execution_context.state_machine.transition(GlueProcessState.IDLE, None)
            self.execution_context.robot_service.robotStateManager.trajectoryUpdate = False
            self.execution_context.robot_service.message_publisher.publish_trajectory_stop_topic()
            return True, "Execution completed"

        except Exception as e:
            log_error_message(glue_dispensing_logger_context, message=f"Error during traceContours execution: {e}")

            import traceback
            traceback.print_exc()
            self.execution_context.state_machine.transition(GlueProcessState.ERROR)
            return False, f"Execution error: {e}"

    def pause_operation(self):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.pause_operation import pause_operation
        return pause_operation(self,self.execution_context)

    def stop_operation(self):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.stop_operation import stop_operation
        return stop_operation(self,self.execution_context)

    def resume_operation(self):
        """Resume operation from paused state"""
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.resume_operation import resume_operation
        return resume_operation(self.execution_context)

    def _resume_execution(self):
        """Resume execution from saved context"""

        try:
            paths = self.execution_context.paths
            spray_on = self.execution_context.spray_on
            self.start(paths, spray_on, resume=True)
        except Exception as e:
            log_debug_message(glue_dispensing_logger_context, message=f"Error during resume execution: {e}")
            self.execution_context.state_machine.transition(GlueProcessState.ERROR)

    def _handle_starting_state(self,context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.start_state_handler import handle_starting_state
        # Return whatever the handler returns so the caller can update its local execution context variables
        return handle_starting_state(context)

    def _handle_moving_to_first_point_state(self,context,resume):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.moving_to_first_point_state_handler import handle_moving_to_first_point_state
        return handle_moving_to_first_point_state(context,resume)

    def _handle_transition_between_paths(self,context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.transition_between_paths_state_handler import handle_transition_between_paths
        return handle_transition_between_paths(context)

    def _handle_pump_initial_boost(self, context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.initial_pump_boost_state_handler import handle_pump_initial_boost
        return handle_pump_initial_boost(context)

    def _handle_start_pump_adjustment_thread(self, execution_context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.start_pump_adjustment_thread_handler import handle_start_pump_adjustment_thread
        return handle_start_pump_adjustment_thread(execution_context)

    def _handle_send_path_to_robot_state(self, execution_context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.sending_path_to_robot_state_handler import handle_send_path_to_robot
        return handle_send_path_to_robot(execution_context)

    def _handle_wait_for_path_completion(self,execution_context):
        from robot_application.glue_dispensing_application.glue_dispensing.state_handlers.wait_for_path_completion_state_handler import handle_wait_for_path_completion
        return handle_wait_for_path_completion(execution_context)

