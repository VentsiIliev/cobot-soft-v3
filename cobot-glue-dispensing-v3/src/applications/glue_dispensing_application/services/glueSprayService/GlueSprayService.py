from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from applications.glue_dispensing_application.services.glueSprayService.fanControl.fanControl import FanControl, FanState
from applications.glue_dispensing_application.services.glueSprayService.generatorControl.GeneratorControl import GeneratorControl, GeneratorState
from applications.glue_dispensing_application.services.glueSprayService.generatorControl.timer import Timer
from applications.glue_dispensing_application.services.glueSprayService.motorControl.MotorControl import MotorControl
import time

from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from src.backend.system.utils.custom_logging import setup_logger,log_if_enabled, LoggingLevel

ENABLE_LOGGING = True
glue_spray_service_logger = setup_logger("GlueSprayService")

class GlueSprayService:
    def __init__(self, settings:GlueSettings,generatorTurnOffTimeout=10):
        self.service_id = "GlueSprayService"
        self.settings = settings
        self.motorController = MotorControl(motorSlaveId=1)
        self.fanController = FanControl(fanSlaveId=1, fanSpeed_address=8)
        self.generatorController = GeneratorControl(
            timer=Timer(generatorTurnOffTimeout, self.generatorOff),
            generator_address=9,
            generator_id=1)
        self.generatorTurnOffTimeout = generatorTurnOffTimeout  # minutes
        self.timer = Timer(self.generatorTurnOffTimeout, self.generatorOff)

        self.glueA_addresses = 0  # MOTOR
        self.glueB_addresses = 2  # MOTOR
        self.glueC_addresses = 4  # MOTOR
        self.glueD_addresses = 6  # MOTOR

        self.generatorCurrentState = False  # Initial generator state

        self.glueMapping = {
            1: self.glueA_addresses,
            2: self.glueB_addresses,
            3: self.glueC_addresses,
            4: self.glueD_addresses
        }


    """ MOTOR CONTROL """

    def adjustMotorSpeed(self,motorAddress, speed):
        return self.motorController.adjustMotorSpeed(motorAddress=motorAddress,speed=speed)

    def motorOff(self, motorAddress, speedReverse, reverse_time,ramp_steps=None):
        # print("Service motorOff called")
        # Use passed ramp_steps if provided, otherwise fall back to settings
        actual_ramp_steps = ramp_steps if ramp_steps is not None else self.settings.get_reverse_ramp_steps()

        return self.motorController.motorOff(motorAddress=motorAddress,
                                             speedReverse=speedReverse,
                                             reverse_time=reverse_time,
                                             ramp_steps=actual_ramp_steps)

    def motorOn(self, motorAddress, speed,ramp_steps, initial_ramp_speed, initial_ramp_speed_duration):

        return self.motorController.motorOn(motorAddress=motorAddress,
                                            speed=speed,
                                            ramp_steps=ramp_steps,
                                            initial_ramp_speed=initial_ramp_speed,
                                            initial_ramp_speed_duration=initial_ramp_speed_duration)

    def motorState(self, motorAddress):
        return self.motorController.motorState(motorAddress)

    """ GENERATOR CONTROL """

    def generatorOff(self):
        # print("Turning generator OFF")
        result = self.generatorController.generatorOff()
        self.generatorCurrentState = self.getGeneratorState()
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=glue_spray_service_logger,
                       message=f"GlueSprayService.generatorOff -> Generator state: {self.generatorCurrentState}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        return self.generatorCurrentState

    def generatorOn(self):
        # print("Turning generator ON")
        result = self.generatorController.generatorOn()
        self.generatorCurrentState = self.getGeneratorState()
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=glue_spray_service_logger,
                       message=f"GlueSprayService.generatorOn ->  Generator state: {self.generatorCurrentState}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        return self.generatorCurrentState

    def generatorState(self):
        generator_state = self.generatorController.getGeneratorState()
        # Update internal state tracking if communication successful
        if not generator_state.modbus_errors:
            self.generatorCurrentState = generator_state.is_on
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=glue_spray_service_logger,
                       message=f"Generator state: {self.generatorCurrentState}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        return self.generatorCurrentState

    def getGeneratorState(self) -> GeneratorState:
        """Get comprehensive generator state using new GeneratorState class."""
        generator_state = self.generatorController.getGeneratorState()
        
        # Update internal state tracking
        if not generator_state.modbus_errors:
            self.generatorCurrentState = generator_state.is_on
        
        return generator_state

    def isGeneratorHealthy(self) -> bool:
        """Check if generator is healthy and operational."""
        generator_state = self.getGeneratorState()
        return generator_state.is_healthy

    def getGeneratorErrors(self) -> dict:
        """Get all generator errors in a structured format."""
        generator_state = self.getGeneratorState()
        return {
            'error_code': generator_state.error_code,
            'modbus_errors': generator_state.modbus_errors,
            'has_errors': generator_state.has_errors()
        }
    """ FAN CONTROL """

    def fanOff(self):  # FAN SPEED
        return self.fanController.fanOff()

    def fanOn(self, value):  # FAN SPEED
        return self.fanController.fanOn(value)

    def fanState(self):
        return self.fanController.getFanState()

    def getFanState(self) -> FanState:
        """Get comprehensive fan state using new FanState class."""
        return self.fanController.getFanState()

    def isFanHealthy(self) -> bool:
        """Check if fan is healthy and operational."""
        fan_state = self.getFanState()
        return fan_state.is_healthy

    def getFanErrors(self) -> dict:
        """Get all fan errors in a structured format."""
        fan_state = self.getFanState()
        return {
            'modbus_errors': fan_state.modbus_errors,
            'has_errors': fan_state.has_errors()
        }

    """ GLUE SPRAY CONTROL"""

    def startGlueDispensing(self,
                            glueType_addresses,
                            speed,
                            reverse_time,
                            speedReverse,
                            gen_pump_delay=0.5,
                            fanSpeed=0,
                            ramp_steps=3):
        result = False
        motorAddress = glueType_addresses
        try:
            self.fanOn(fanSpeed)
            self.generatorOn()
            time.sleep(gen_pump_delay)
            self.motorOn(motorAddress=motorAddress,
                         speed=speed,
                         ramp_steps=ramp_steps,
                         initial_ramp_speed=self.settings.get_initial_ramp_speed(),
                         initial_ramp_speed_duration=self.settings.get_initial_ramp_speed_duration())

            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=glue_spray_service_logger,
                           message=f"Glue dispensing started for {glueType_addresses} at speed {speed}, stepsReverse {reverse_time}, speedReverse {speedReverse}",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)

            result = True
        except Exception as e:
            import traceback
            self.generatorOff()
            self.fanOff()
            self.motorOff(motorAddress=motorAddress,
                          speedReverse=speedReverse,
                          reverse_time=0)
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=glue_spray_service_logger,
                           message=f"Error starting glue dispensing for {glueType_addresses}: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            traceback.print_exc()
        return result

    def stopGlueDispensing(self, glueType_addresses, speed_reverse, pump_reverse_time,ramp_steps, pump_gen_delay=0.5):
        result = False
        motorAddress = glueType_addresses
        try:
            self.motorOff(motorAddress=motorAddress,
                          speedReverse=speed_reverse,
                          reverse_time=pump_reverse_time,
                          ramp_steps=ramp_steps)

            time.sleep(pump_gen_delay)

            self.generatorOff()
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=glue_spray_service_logger,
                           message=f"Glue dispensing stopped for {glueType_addresses}",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            result = True
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=glue_spray_service_logger,
                           message=f"Error stopping glue dispensing for {glueType_addresses}: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        return result


