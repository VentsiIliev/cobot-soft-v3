"""
Class not in use as moved to depth camera.
"""

from modules.modbusCommunication.ModbusClient import ModbusClient
import platform
from modules.shared.utils import linuxUtils
from src.backend.system.SensorPublisher import SENSOR_STATE_ERROR
from modules.modbusCommunication.ModbusClientSingleton import ModbusClientSingleton


class Laser:
    """
    A class to control a laser device via Modbus communication.

    This class allows for controlling a laser by turning it on or off through Modbus commands. It also
    handles platform-dependent configuration for the communication port, automatically detecting
    the appropriate serial port on Linux systems.

    Attributes:
        slave (int): The Modbus slave address for the laser device.
        port (str): The serial port used for communication with the laser device (e.g., COM5 for Windows or dynamically detected on Linux).
        modbusClient (ModbusClient): The instance of the Modbus client used for communication with the laser device.
    """
    def __init__(self):
        """
               Initializes the Laser object by setting up the Modbus slave address, detecting the communication port,
               and initializing the Modbus client.

               The port is detected based on the operating system. If the system is Windows, a predefined port (COM5) is used.
               If the system is Linux, the appropriate port is detected using the `find_ch341_uart_port` method.

               Raises:
                   Exception: If the communication port cannot be detected or the Modbus client cannot be initialized, an exception is raised.
               """
        self.slave = 1

        # Determine OS and set the correct serial port
        if platform.system() == "Windows":
            self.port = "COM5"  # Adjust as necessary
        else:  # Assuming Linux
            # self.port = "/dev/ttyUSB0"  # Adjust as necessary
            self.port = linuxUtils.get_modbus_port()  # Adjust as necessary
            print(f"Detected laser port: {self.port}")
        self._create_modbus_client()
        # self.modbusClient = ModbusClient(self.slave, self.port, 115200, 8, 1, 0.05)

    def _create_modbus_client(self):
        try:
            # Reset singleton instance to force new connection on reconnect
            ModbusClientSingleton._client_instance = None
            self.modbusClient = ModbusClientSingleton.get_instance(
                slave=self.slave,
                port=self.port,
                baudrate=115200,
                bytesize=8,
                stopbits=1,
                timeout=0.05
            )
        except Exception as e:
            self.state = SENSOR_STATE_ERROR
            # raise Exception(f"Failed to create Modbus client: {e}")

    def turnOn(self):
        """
                Turns on the laser by sending a Modbus write command to the laser device.

                This method writes a value of 1 to register 16, signaling the laser to turn on.

                Raises:
                    Exception: If the Modbus command fails, an exception is raised.
                """
        self.modbusClient.writeRegister(14, 1)
        print("Turning on laser")

    def turnOff(self):
        """
               Turns off the laser by sending a Modbus write command to the laser device.

               This method writes a value of 0 to register 16, signaling the laser to turn off.

               Raises:
                   Exception: If the Modbus command fails, an exception is raised.
               """
        self.modbusClient.writeRegister(14, 0)
        print("Turning off laser")

if __name__ == "__main__":
    laser = Laser()
    laser.turnOn()
    # time.sleep(1)
    # laser.turnOff()