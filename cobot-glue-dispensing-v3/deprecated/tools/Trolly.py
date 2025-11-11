import time
from enum import Enum
from logging import CRITICAL

import serial.serialutil

from modules.modbusCommunication.ModbusClient import ModbusClient
from src.backend.system.SensorPublisher import Sensor, SENSOR_STATE_NO_COMMUNICATION, SENSOR_STATE_DISCONNECTED, SENSOR_STATE_RECONNECTING, SENSOR_STATE_READY, SENSOR_STATE_ERROR, \
    SENSOR_STATE_INITIALIZING,SENSOR_STATE_USB_NOT_CONNECTED
import linuxUtils
import minimalmodbus

import logging

from main import trolleyLeft

logger = logging.getLogger("Trolly")
logger.setLevel(CRITICAL)


#
#   File "/home/ilv/.local/lib/python3.8/site-packages/minimalmodbus.py", line 1521, in _communicate
#     raise NoResponseError("No communication with the instrument (no answer)")
# minimalmodbus.NoResponseError: No communication with the instrument (no answer)

# Register addresses
READ_STATUS_REGISTER = 1
SEND_COMMAND_REGISTER = 0
SEND_POSITION_REGISTER = 1


class TrollyDirection(Enum):
    UP = 1
    DOWN = 0


class TrollyStatus(Enum):
    """
    Enum representing the current status of the trolly, read from address 1 (hex 0x01).
    """
    NOTHING = 0
    """No operation is currently in progress."""

    INITIALIZED = 1
    """Initialization has completed successfully."""

    MOVING = 2
    """The trolly is currently moving."""

    MOVE_COMPLETED = 3
    """The last movement has been completed successfully."""

    GOING_TO_ZERO_POSITION = 4
    """The trolly is moving to the zero (home) position."""

    ERROR = 5
    """An error occurred (motor not moving or mechanical blockage)."""


class TrollyCommand(Enum):
    """
    Enum representing commands that can be sent to the trolly at address 0 (hex 0x00).
    """
    NOTHING = 0
    """No command is issued."""

    START_MOVEMENT = 1
    """Start the movement to the given position."""

    STOP = 2
    """Immediately stop any ongoing movement."""

    RESET = 3
    """Reset the system (return to zero position)."""


class Trolly(Sensor):
    """
    Class for controlling a trolly device over Modbus.

    Attributes:
        id (int): The Modbus slave ID.
        port (str): The serial port used for communication.
        client (ModbusClient): The Modbus client instance.
        topPosition (int): Predefined top position.
        bottomPosition (int): Predefined bottom position.
    """

    def __init__(self, id=20):
        """
        Initialize the Trolly with a Modbus client and default positions.

        Args:
            id (int): Modbus slave ID of the trolly (default: 20).
        """
        self.id = id
        self.name = f"Trolly_{self.id}"
        self.state = SENSOR_STATE_INITIALIZING
        self.port = linuxUtils.get_modbus_port()  # e.g., "/dev/ttyUSB0"
        self.client = None
        # self.port =  "/dev/ttyUSB4"
        self.pollTime = 1
        self.type = "modbus"
        self._create_modbus_client()
        self._reconnecting_lock = threading.Lock()
        # Test connection to the Modbus client
        self.testConnection()

        self.topPosition = 2500
        self.bottomPosition = 0
        self.direction = -1

    def _create_modbus_client(self):
        try:
            self.client = ModbusClient(slave=self.id, port=self.port)
            logger.debug(f"[{self.name}] Modbus client created for slave {self.id} on port {self.port}")

        except Exception as e:
            # import traceback
            # traceback.print_exc()
            logger.exception("Failed to create Modbus client.")
            self.state = SENSOR_STATE_USB_NOT_CONNECTED
            # print(f"[DEBUG] [{self.name}] Failed to create Modbus client.")
            # raise Exception(f"[DEBUG] [{self.name}] Failed to create Modbus client: {e}")

    def moveToTopPosition(self):
        """
        Move the trolly to the predefined top position.
        """
        self.__sendPosition(self.topPosition)
        time.sleep(0.1)
        self.__startMove()
        self.direction = TrollyDirection.UP.value

    def moveToBottomPosition(self):
        """
        Move the trolly to the predefined bottom position.
        """
        self.__sendPosition(self.bottomPosition)
        time.sleep(0.1)
        self.__startMove()
        self.direction = TrollyDirection.DOWN.value

    def moveToPosition(self, position):
        """
        Set a custom position for the trolly to move to (but does not start movement).

        Args:
            position (int): The position value to move to.
        """
        self.__sendPosition(position)
        time.sleep(0.1)
        self.__startMove()

    def moveUpWith(self, step):
        """
        Placeholder for moving the trolly up by a defined step (not implemented).

        Args:
            step (int): The number of units to move up.
        """
        pass

    def moveDownWith(self, step):
        """
        Placeholder for moving the trolly down by a defined step (not implemented).

        Args:
            step (int): The number of units to move down.
        """
        pass

    def stop(self):
        """
        Stop any ongoing movement of the trolly immediately.
        """
        self.client.writeRegister(SEND_COMMAND_REGISTER, TrollyCommand.STOP.value)
        self.direction = -1

    def __sendPosition(self, distance):
        """
        Internal method to send a position command to the trolly.

        Args:
            distance (int): The position to send.
        """
        self.client.writeRegister(SEND_POSITION_REGISTER, distance)

    def __startMove(self):
        """
        Internal method to issue the start movement command to the trolly.
        """
        self.client.writeRegister(SEND_COMMAND_REGISTER, TrollyCommand.START_MOVEMENT.value)

    def getStatus(self):
        """
        Public method to get the current status of the trolly.

        Returns:
            int: The status code read from the trolly.
        """
        try:
            return self.__queryStatus()
        except:
            return "Error reading status"

    def __queryStatus(self):
        """
        Internal method to read the current status from the trolly.

        Returns:
            int: The status code from the trolly.
        """
        return self.client.read(READ_STATUS_REGISTER)

    def home(self):
        """
        Send the reset command to move the trolly to its home (zero) position.
        """
        self.client.writeRegister(SEND_COMMAND_REGISTER, TrollyCommand.RESET.value)

    ### SENSOR INTERFACE METHODS IMPLEMENTATION

    def getState(self):
        return self.state

    def getValue(self):
        pass

    def getName(self):
        return self.name

    def testConnection(self):
        if self.client is None:
            self.state = SENSOR_STATE_DISCONNECTED
            return

        try:
            self.client.read(READ_STATUS_REGISTER)
            self.state = SENSOR_STATE_READY
        except minimalmodbus.NoResponseError as e:
            logger.error(f"[{self.name}] No communication with the instrument: {e}")
            self.state = SENSOR_STATE_NO_COMMUNICATION
        except minimalmodbus.InvalidResponseError as e:
            logger.error(f"[{self.name}] No communication with the instrument: {e}")
            self.state = SENSOR_STATE_NO_COMMUNICATION
        except serial.serialutil.SerialException as e:
            if "device reports readiness to read but returned no data" in str(e):
                self.logger.debug(f"[DEBUG] {self.logTag} Command processor error: {e}")
                self.state = SENSOR_STATE_READY
            else:
                self.logger.warning(f"[WARN] Could not configure port:: {e}")
                self.state = SENSOR_STATE_DISCONNECTED
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.state = SENSOR_STATE_ERROR
            self.reconnect()

    def reconnect(self):
        if self._reconnecting_lock.locked():
            return  # Already reconnecting

        def try_reconnect():
            with self._reconnecting_lock:
                self.state = SENSOR_STATE_RECONNECTING
                logger.debug(f"[{self.name}] Attempting reconnection...")


                try:
                    self.port = linuxUtils.get_modbus_port()
                    self._create_modbus_client()
                    self.testConnection()
                    logger.debug(f"[{self.name}] Reconnected successfully.")

                    self.state = SENSOR_STATE_READY
                    return
                except Exception as e:
                    logger.warning(f"[{self.name}] Reconnection failed: {e}")

                    self.state = SENSOR_STATE_ERROR
                    time.sleep(2)

                logger.debug(f"[{self.name}] Current state after reconnect attempt: {self.state}")


        threading.Thread(target=try_reconnect, daemon=True).start()


import threading

from src.backend.system.SensorPublisher import SensorPublisher
from modules.shared.MessageBroker import MessageBroker

from PyQt6.QtCore import QObject, pyqtSignal


class TrollyController(QObject):
    # Signal: trolley_id (int or str), connection status (bool)
    update_status_signal = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.trollyLeft = Trolly(20)  # assuming slave ID 22 for left
        self.trollyRight = Trolly(22)  # assuming slave ID 20 for right

        self.publisher = SensorPublisher()
        self.publisher.registerSensor(self.trollyLeft)
        self.publisher.registerSensor(self.trollyRight)

        self.broker = MessageBroker()
        self.broker.subscribe("Trolly_20/STATE", self.on_state_message)
        self.broker.subscribe("Trolly_22/STATE", self.on_state_message)

        self.publisher.start()

    def on_state_message(self, message):
        logger.debug(f"Received message: {message}")


        # Assuming message is a dict like: {"trolly_id": "left", "state": "READY"}
        trolley_id = None
        connected = False

        try:
            if isinstance(message, dict):
                trolley_id = message.get("trolly_id")  # e.g. "left" or "right"
                state = message.get("state", "").upper()

                if trolley_id and state:
                    connected = state in ("READY", "CONNECTED")
            elif isinstance(message, str):
                # fallback for simple string messages (maybe just one trolley)
                # Treat all as "left" for example
                trolley_id = "left"
                connected = message.upper() in ("READY", "CONNECTED")
            else:
                trolley_id = None
                connected = False

            logger.debug(f"Trolley '{trolley_id}' connection status parsed: {connected}")


            if trolley_id is not None:
                self.update_status_signal.emit(trolley_id, connected)

        except Exception as e:
            # print(f"[ERROR] Exception parsing message: {e}")
            logger.exception(f"Exception parsing message")


if __name__ == "__main__":
    trolleyLeft = Trolly(20)
    trolleyRight = Trolly(22)

    trolleyLeft.moveToTopPosition()
    trolleyRight.moveToTopPosition()