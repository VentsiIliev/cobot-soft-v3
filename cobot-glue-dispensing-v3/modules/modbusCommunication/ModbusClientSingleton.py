from modules.modbusCommunication.modbus_lock import modbus_lock
from modules.modbusCommunication.ModbusClient import ModbusClient

class ModbusClientSingleton:
    """
    Singleton wrapper for ModbusClient to ensure only one instance is used throughout
    the application. Useful for managing shared hardware communication resources.

    Attributes:
        _client_instance (ModbusClient): Static variable holding the singleton instance.
        _lock (threading.Lock): Lock used for thread-safe singleton initialization.
    """
    _client_instance = None
    _lock = modbus_lock

    @staticmethod
    def get_instance(slave=10, port='COM5', baudrate=115200, bytesize=8, stopbits=1, timeout=0.01):
        if ModbusClientSingleton._client_instance is None:
            with ModbusClientSingleton._lock:
                if ModbusClientSingleton._client_instance is None:  # Double-checked locking
                    ModbusClientSingleton._client_instance = ModbusClient(slave, port, baudrate, bytesize, stopbits, timeout)
        return ModbusClientSingleton._client_instance

    @staticmethod
    def get_lock():
        return ModbusClientSingleton._lock
