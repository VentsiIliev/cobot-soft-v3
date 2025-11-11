# create class VacuumPump
import time


class VacuumPump:
    """
      A class to control the state of a vacuum pump for a robotic system.

      This class provides functionality to turn the vacuum pump on and off by controlling a digital output pin.
      The pump is typically used in robotic systems for tasks like picking and placing, where a vacuum is required to hold objects.

      Attributes:
          ON_VALUE (int): Constant representing the ON state for the vacuum pump (1).
          OFF_VALUE (int): Constant representing the OFF state for the vacuum pump (0).
          xOffset (float): The x-axis offset from the main tooltip for positioning the vacuum pump (default is 0).
          yOffset (float): The y-axis offset from the main tooltip for positioning the vacuum pump (default is 0).
          zOffset (float): The z-axis offset from the main tooltip for positioning the vacuum pump (default is 105).
          digitalOutput (int): The digital output pin number used to control the vacuum pump (default is 3).
          vacuumPump (object): A placeholder for the vacuum pump object, can be used to hold any further configurations (default is None).

      Methods:
          turnOn(robot):
              Turns on the vacuum pump by setting the corresponding digital output to the ON_VALUE.

          turnOff(robot):
              Turns off the vacuum pump by setting the corresponding digital output to the OFF_VALUE, and performs
              a quick reset on another digital output to ensure the pump is properly turned off.
      """
    ON_VALUE = 1
    OFF_VALUE = 0
    def __init__(self):
        """
               Initializes the VacuumPump with default values.

               The digital output pin used to control the pump is set to 3 by default. The offsets for the tooltip
               are also initialized (xOffset, yOffset, zOffset) to help place the vacuum pump in the correct position
               relative to the robotic arm or tool.

               Attributes are initialized as:
                   xOffset = 0
                   yOffset = 0
                   zOffset = 105
                   digitalOutput = 3
                   vacuumPump = None
               """
        self.xOffset = 0  # x offset from the main tooltip
        self.yOffset = 0  # y offset from the main tooltip
        self.zOffset = 125 # z offset from the main tooltip
        self.digitalOutput = 1
        self.vacuumPump = None

    def turnOn(self, robot):
        """
            Turns on the vacuum pump by activating the digital output.

            This method sets the digital output pin (configured by `self.digitalOutput`) to the ON_VALUE (1), which
            triggers the vacuum pump to turn on. It also prints a message confirming that the vacuum pump is turned on.

            Args:
                robot (object): The robot object that interfaces with the physical hardware. This object should provide
                                the method `setDigitalOutput` to set the state of digital outputs.

            Returns:
                None
            """
        result = robot.setDigitalOutput(self.digitalOutput, self.ON_VALUE)  # Open the control box DO
        print("PUMP TURNED ON")

    def turnOff(self, robot):
        """
             Turns off the vacuum pump by deactivating the digital output.

             This method sets the digital output pin (configured by `self.digitalOutput`) to the OFF_VALUE (0), which
             turns the vacuum pump off. Additionally, it performs a brief reset on another digital output pin (pin 2),
             which may be used to ensure the pump is completely deactivated.

             Args:
                 robot (object): The robot object that interfaces with the physical hardware. This object should provide
                                 the method `setDigitalOutput` to set the state of digital outputs.

             Returns:
                 None
             """
        result = robot.setDigitalOutput(self.digitalOutput, self.OFF_VALUE)  # Open the control box DO
        result = robot.setDigitalOutput(2, 1)
        time.sleep(0.3)
        result = robot.setDigitalOutput(2, 0)
        print("PUMP TURNED OFF")

if __name__ == "__main__":
    from src.backend.system.robot.FairinoRobot import FairinoRobot
    robot = FairinoRobot("192.168.58.2")
    pump = VacuumPump()
    print("Vacuum Pump initialized with digital output pin:", pump.digitalOutput)
    print("Vacuum Pump ON value:", pump.ON_VALUE)
    pump.turnOn(robot)
    time.sleep(1)
    pump.turnOff(robot)
    print("Vacuum Pump OFF value:", pump.OFF_VALUE)