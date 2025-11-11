"""
modbusCommunication - Modbus RTU communication module

Provides thread-safe Modbus RTU communication with automatic retry logic
and error handling for hardware control in the cobot glue dispensing system.

Quick Start:
    >>> from modbusCommunication import ModbusController
    >>> client = ModbusController.getModbusClient(slaveId=10)
    >>> value, error = client.read(100)

Main Components:
    - ModbusClient: Core Modbus RTU client
    - ModbusController: Factory for configured clients
    - ModbusClientSingleton: Singleton pattern wrapper
    - modbus_lock: Thread synchronization
    - MockClient: Testing mock
"""

from .ModbusClient import ModbusClient
from .ModbusController import ModbusController
from .ModbusClientSingleton import ModbusClientSingleton
from .modbus_lock import modbus_lock

__all__ = [
    'ModbusClient',
    'ModbusController',
    'ModbusClientSingleton',
    'modbus_lock',
]

__version__ = '2.0.0'
