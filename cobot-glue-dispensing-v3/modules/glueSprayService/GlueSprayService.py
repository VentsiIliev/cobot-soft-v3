from src.applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from modules.glueSprayService.fanControl.fanControl import FanControl, FanState
from modules.glueSprayService.generatorControl.GeneratorControl import GeneratorControl, GeneratorState
from modules.glueSprayService.generatorControl.timer import Timer
from modules.glueSprayService.motorControl.MotorControl import MotorControl
import time

from src.backend.system.utils.custom_logging import setup_logger,log_if_enabled, LoggingLevel

ENABLE_LOGGING = True
glue_spray_service_logger = setup_logger("GlueSprayService")

class GlueSprayService:
    def __init__(self, settings:GlueSettings,generatorTurnOffTimeout=10):
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


def fan_test():
    glueService = GlueSprayService()
    glueService.fanOn(100)
    # time.sleep(1)
    # glueService.fanOff()


def generator_test():
    glueService = GlueSprayService()
    
    print("=== Testing New GeneratorState ===")
    
    # Test new GeneratorState methods
    generator_state = glueService.getGeneratorState()
    print("Initial Generator State:")
    print(f"  {generator_state}")
    print(f"  Healthy: {glueService.isGeneratorHealthy()}")
    
    # Test legacy compatibility
    legacy_state = glueService.generatorState()
    print(f"Legacy state: {legacy_state}")
    
    # Turn on generator
    print("\nTurning generator ON...")
    glueService.generatorOn()
    
    generator_state = glueService.getGeneratorState()
    print("Generator State after ON:")
    print(f"  {generator_state}")
    
    time.sleep(1)
    
    # Turn off generator
    print("\nTurning generator OFF...")
    glueService.generatorOff()
    
    generator_state = glueService.getGeneratorState()
    print("Generator State after OFF:")
    print(f"  {generator_state}")
    
    # Test error checking
    errors = glueService.getGeneratorErrors()
    print(f"Generator Errors: {errors}")


def fan_test_new():
    """Test new FanState functionality"""
    glueService = GlueSprayService()
    
    print("=== Testing New FanState ===")
    
    # Test new FanState methods
    fan_state = glueService.getFanState()
    print("Initial Fan State:")
    print(f"  {fan_state}")
    print(f"  Healthy: {glueService.isFanHealthy()}")
    
    # Test legacy compatibility
    legacy_success, legacy_state = glueService.fanState()
    print(f"Legacy fan state: success={legacy_success}, state={legacy_state}")
    
    # Turn on fan
    print("\nTurning fan ON with speed 50...")
    result = glueService.fanOn(50)
    print(f"Fan ON result: {result}")
    
    fan_state = glueService.getFanState()
    print("Fan State after ON:")
    print(f"  {fan_state}")
    
    time.sleep(1)
    
    # Turn off fan
    print("\nTurning fan OFF...")
    result = glueService.fanOff()
    print(f"Fan OFF result: {result}")
    
    fan_state = glueService.getFanState()
    print("Fan State after OFF:")
    print(f"  {fan_state}")
    
    # Test error checking
    errors = glueService.getFanErrors()
    print(f"Fan Errors: {errors}")


def comprehensive_test():
    """Test all device states comprehensively"""
    glueService = GlueSprayService()
    
    print("=== Comprehensive Device State Test ===")
    
    # Test all device states
    print("\n--- Motor States ---")
    try:
        all_motors = glueService.motorController.getAllMotorStates()
        if all_motors.success:
            for addr, motor_state in all_motors.motors.items():
                print(f"Motor {addr}: {motor_state}")
        else:
            print("Failed to get motor states")
    except Exception as e:
        print(f"Error testing motors: {e}")
    
    print("\n--- Generator State ---")
    try:
        generator_state = glueService.getGeneratorState()
        print(f"Generator: {generator_state}")
        print(f"Generator Healthy: {glueService.isGeneratorHealthy()}")
    except Exception as e:
        print(f"Error testing generator: {e}")
    
    print("\n--- Fan State ---")
    try:
        fan_state = glueService.getFanState()
        print(f"Fan: {fan_state}")
        print(f"Fan Healthy: {glueService.isFanHealthy()}")
    except Exception as e:
        print(f"Error testing fan: {e}")
    
    print("\n--- Device Health Summary ---")
    try:
        motor_health = []
        all_motors = glueService.motorController.getAllMotorStates()
        if all_motors.success:
            for addr, motor_state in all_motors.motors.items():
                motor_health.append(f"M{addr}: {'✓' if motor_state.is_healthy else '✗'}")
        
        gen_healthy = glueService.isGeneratorHealthy()
        fan_healthy = glueService.isFanHealthy()
        
        print(f"Motors: {', '.join(motor_health)}")
        print(f"Generator: {'✓' if gen_healthy else '✗'}")
        print(f"Fan: {'✓' if fan_healthy else '✗'}")
        
    except Exception as e:
        print(f"Error in health summary: {e}")


if __name__ == "__main__":
    print("=== GlueSprayService Testing Interface ===")
    print("Available test functions:")
    print("1. generator_test() - New GeneratorState test")
    print("2. fan_test_new() - New FanState test")
    print("3. comprehensive_test() - Test all devices")
    print("4. Interactive mode")
    
    glueService = GlueSprayService()
    
    # Run comprehensive test first
    comprehensive_test()
    
    # Interactive testing mode
    print("\n=== Interactive Testing Mode ===")
    print("Commands: motor, generator, fan, all, exit")
    
    while True:
        try:
            command = input("\nEnter command: ").strip().lower()
            
            if command == "motor" or command == "m":
                print("\n--- Motor Testing ---")
                try:
                    all_motors = glueService.motorController.getAllMotorStates()
                    if all_motors.success:
                        for addr, motor_state in all_motors.motors.items():
                            print(f"Motor {addr}: {motor_state}")
                            if not motor_state.is_healthy:
                                print(f"  Errors: {motor_state.get_filtered_errors()}")
                    else:
                        print("Failed to get motor states")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif command == "generator" or command == "g":
                print("\n--- Generator Testing ---")
                try:
                    generator_state = glueService.getGeneratorState()
                    print(f"Generator: {generator_state}")
                    print(f"Healthy: {glueService.isGeneratorHealthy()}")
                    errors = glueService.getGeneratorErrors()
                    if errors['has_errors']:
                        print(f"Errors: {errors}")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif command == "fan" or command == "f":
                print("\n--- Fan Testing ---")
                try:
                    fan_state = glueService.getFanState()
                    print(f"Fan: {fan_state}")
                    print(f"Healthy: {glueService.isFanHealthy()}")
                    errors = glueService.getFanErrors()
                    if errors['has_errors']:
                        print(f"Errors: {errors}")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif command == "all" or command == "a":
                print("\n--- All Devices Status ---")
                comprehensive_test()
                
            elif command == "exit" or command == "q":
                break
                
            else:
                print("Unknown command. Use: motor, generator, fan, all, exit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Exiting GlueSprayService test.")
