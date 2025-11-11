import logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
# )


from utils import linuxUtils
import queue
import threading
import time
import minimalmodbus
import serial
from GlueDispensingApplication.modbusCommunication.ModbusClientSingleton import ModbusClientSingleton
from GlueDispensingApplication.SensorPublisher import Sensor, SENSOR_STATE_DISCONNECTED, SENSOR_STATE_RECONNECTING, SENSOR_STATE_READY, SENSOR_STATE_ERROR, \
    SENSOR_STATE_INITIALIZING, SENSOR_STATE_BUSY

class GlueNozzleService(Sensor):
    """
    Service to control glue nozzle via Modbus.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        if GlueNozzleService._instance is not None:
            raise Exception("Use get_instance() to get the singleton instance.")

        super().__init__(name="GlueNozzleService", state="INITIALIZING")
        self.logTag = "GlueNozzleService"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.slave = 13
        self.type = "modbus"
        self.pollTime = 1
        self.port = linuxUtils.get_modbus_port()
        self.commandQue = queue.Queue()
        self._stop_thread = threading.Event()
        self._reconnecting_lock = threading.Lock()
        self.state = SENSOR_STATE_INITIALIZING
        self.modbusClient = None
        self._create_modbus_client()
        # self.testConnection()
        self.logger.debug(f"[{self.name}] Modbus Client connected on {self.port}")


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

    # Command Methods
    def sendCommand(self, data):
        self.modbusClient.writeRegisters(100, data)
        self.logger.debug(f"[{self.name}] Entered Values: {data}")


    def startGlueDotsDispensing(self):
        data = [1, 16, 4, 20, 100, 24000, 0, 3400, 0]
        self.modbusClient.writeRegisters(100, data)
        self.state = SENSOR_STATE_BUSY
        self.logger.debug(f"[{self.name}] GLUE DISPENSING STARTED")

    def startGlueLineDispensing(self):
        data = [1, 16, 4, 20, 100, 24000, 0, 3400, 0]
        self.modbusClient.writeRegisters(100, data)
        self.state = SENSOR_STATE_BUSY
        self.logger.debug(f"[DEBUG] [{self.name}] GLUE DISPENSING STARTED")

    def stopGlueDispensing(self):
        self.modbusClient.writeRegister(100, 0)
        self.state = SENSOR_STATE_READY
        self.logger.debug(f"[DEBUG] [{self.name}] GLUE DISPENSING STOPPED")

    # Command Queue
    def addCommandToQueue(self, command):
        self.commandQue.put(command)

    def _startCommandProcessor(self):
        def run():
            self.logger.debug(f"[DEBUG] [{self.name}] Command processor started.")
            while not self._stop_thread.is_set():
                try:
                    command = self.commandQue.get(timeout=0.1)
                    command()
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"[DEBUG] [{self.name}] Command processor error: {e}")

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self._stop_thread.set()
        self.logger.debug(f"[{self.name}] Command processor stopping.")

    # Sensor Interface
    def getState(self):
        return self.state

    def getValue(self):
        return None

    def getName(self):
        return self.name

    # Connection Handling
    def testConnection(self):
        # print(self.state)
        if self.modbusClient is None:
            self.state = SENSOR_STATE_DISCONNECTED
            return

        try:
            self.modbusClient.read(101)
            if self.state != SENSOR_STATE_BUSY:
                self.state = SENSOR_STATE_READY

        except minimalmodbus.NoResponseError as e:
            self.logger.error(f"[{self.name}] No communication with the instrument: {e}")

            self.state = SENSOR_STATE_READY
        except minimalmodbus.InvalidResponseError as e:
            self.logger.error(f"[{self.name}] No communication with the instrument: {e}")
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
            logger.exception(f"[{self.name}] Unexpected error occurred")
            self.state = SENSOR_STATE_ERROR
            self.reconnect()

    def reconnect(self):
        if self._reconnecting_lock.locked():
            return  # Already reconnecting

        def try_reconnect():
            with self._reconnecting_lock:
                self.state = SENSOR_STATE_RECONNECTING
                self.logger.debug(f"[DEBUG] [{self.name}] Attempting reconnection...")
                while not self._stop_thread.is_set():
                    try:
                        self.port = linuxUtils.get_modbus_port()
                        self._create_modbus_client()
                        self.modbusClient.read(100)
                        self.logger.debug(f"[DEBUG] [{self.name}] Reconnected successfully.")
                        self.state = SENSOR_STATE_READY
                        break
                    except Exception as e:
                        self.logger.warning(f"[WARN] [{self.name}] Reconnection failed: {e}")
                        self.state = SENSOR_STATE_ERROR
                        time.sleep(2)

        threading.Thread(target=try_reconnect, daemon=True).start()

# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.DEBUG,
#         format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
#     )
#     glue_service = GlueNozzleService.get_instance()
#     # glue_service.testConnection()
#     try:
#         glue_service.startGlueDotsDispensing()
#     except Exception as e:
#         print(e)
#     time.sleep(1)
#     glue_service.stopGlueDispensing()
#     glue_service.stop()
#     print(f"[DEBUG] [{glue_service.name}] Service stopped.")