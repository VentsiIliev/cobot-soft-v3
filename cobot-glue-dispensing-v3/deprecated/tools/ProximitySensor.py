from enum import Enum
import logging
import minimalmodbus
import serial

utilsimport linuxUtils
from src.backend.system.SensorPublisher import Sensor, SENSOR_STATE_NO_COMMUNICATION, SENSOR_STATE_DISCONNECTED, \
    SENSOR_STATE_READY, SENSOR_STATE_ERROR
from src.backend.system.modbusCommunication.ModbusClient import ModbusClient


class DetectionStatus(Enum):
    NOTHING_DETECTED = 0
    DETECTED_LEFT = 1
    DETECTED_RIGHT = 2
    DETECTED_BOTH = 3


class ProximitySensor(Sensor):
    def __init__(self, id):
        super().__init__(name=f"ProximitySensor_{id}", state="Unknown")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id
        self.detected = -1
        self.type = "modbus"
        self.pollTime = 1
        self.logTag = "ProximitySensor"
        self._connect()
        self.client = None
        # test connection
        try:
            self.detected = self.client.read(110)
            self.logger.debug(f"[{self.logTag}] Initial detection read: {self.detected}")
            self.state = "Connected"
        except Exception as e:
            self._connect()
            self.state = "Disconnected"
            # raise Exception(f"Failed to read initial detection for slave {self.id}: {e}")

    def _connect(self):
        self.port = linuxUtils.get_modbus_port()
        try:
            self.client = ModbusClient(slave=self.id, port=self.port)
            self.logger.debug(f"[{self.logTag}] Modbus client created for slave {self.id} on port {self.port}")
            self.state = "Connected"
        except Exception as e:
            self.logger.debug(f"Connection failed on port {self.port}: {e}")
            # self.client = None
            self.state = "Disconnected"
            # raise Exception(f"Failed to create Modbus client for slave {self.id} on port {self.port}: {e}")
    def detect(self):
        if not self.client:
            self._connect()

        try:
            self.detected = self.client.read(110)
        except Exception as e:
            self.logger.debug(f"{self.logTag} Sensor not initialized: {e}")
            self._connect()
            return -1  # Error
        return self.detected

        # Implement required interface methods

    def getState(self):
        return self.state

    def getValue(self):
        self.value = self.detect()
        return self.value

    def getName(self):
        return self.name

    def testConnection(self):
        if self.client is None:
            self.state = SENSOR_STATE_DISCONNECTED
            return

        try:
            self.client.read(110)
            self.state = SENSOR_STATE_READY

        except minimalmodbus.NoResponseError as e:
            self.logger.warning(f"No communication with the instrument: {e}")
            self.state = SENSOR_STATE_READY
        except minimalmodbus.InvalidResponseError as e:
            self.logger.warning(f"No communication with the instrument: {e}")
            self.state = SENSOR_STATE_READY
        except serial.serialutil.SerialException as e:
            if "device reports readiness to read but returned no data" in str(e):
                self.logger.debug(f"[DEBUG] {self.logTag} Command processor error: {e}")
                self.state = SENSOR_STATE_READY
            else:
                self.logger.warning(f"[WARN] Could not configure port:: {e}")
                self.state = SENSOR_STATE_DISCONNECTED
        except Exception as e:
            # import traceback
            # traceback.print_exc()
            self.logger.warning(f"[{self.logTag}] An unexpected error occurred: {e}", exc_info=True)
            self.state = SENSOR_STATE_ERROR
            self.reconnect()

    def reconnect(self):
        try:
            # Close existing client if it has a close method
            if hasattr(self, "client") and hasattr(self.client, "close"):
                try:
                    self.client.close()
                    self.logger.debug(f"[{self.logTag}] Closed existing Modbus client for sensor {self.id}")
                except Exception as e:
                    self.logger.warning(f"[{self.logTag}] Failed to close client cleanly: {e}")

            # Recreate client
            self._connect()

            # Test connection
            self.client.read(110)
            self.state = "Connected"
            self.logger.debug(f"[{self.logTag}] Reconnected and tested sensor {self.id}")
            return True

        except Exception as e:
            self.state = "Disconnected"
            self.logger.warning(f"[{self.logTag}] Reconnection failed for sensor {self.id}: {e}")
            return False


if __name__ == "__main__":
    sensor = ProximitySensor(13)
    status = sensor.detect()
    print(status)