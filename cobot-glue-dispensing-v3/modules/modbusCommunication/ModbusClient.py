import time
import minimalmodbus
import logging

from applications.glue_dispensing_application.services.glueSprayService.motorControl.errorCodes import \
    ModbusExceptionType
from modules.modbusCommunication.modbus_lock import modbus_lock

class ModbusClient:
    """
    ModbusClient class provides functionality to communicate with a Modbus slave device
    using the Modbus RTU protocol via a serial connection. It allows for reading and
    writing registers on the Modbus slave device.

    Attributes:
        slave (int): The Modbus slave address (default is 10).
        client (minimalmodbus.Instrument): An instance of the minimalmodbus Instrument class
                                           used for Modbus communication.
    """
    def __init__(self, slave=10, port='COM5', baudrate=115200, bytesize=8,
                 stopbits=1, timeout=0.01,parity = minimalmodbus.serial.PARITY_NONE):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.slave = slave
        try:
            self.client = minimalmodbus.Instrument(port, self.slave, debug=False)
            # from modbusCommunication.MockClient import MockInstrument
            # self.client = MockInstrument(port, self.slave, debug=False)
        except Exception as e:
            raise Exception(f"Could not open port {port}. Please check the connection and port settings.") from e

        self.client.serial.baudrate = baudrate
        self.client.serial.bytesize = bytesize
        self.client.serial.stopbits = stopbits
        self.client.serial.timeout = timeout
        self.client.serial.parity = parity

    def writeRegister(self, register, value, signed=False):
        maxAttempts = 30
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    self.client.write_register(register, value, signed=signed)
                    print(f"ModbusClient.writeRegister - > Wrote {value} to register {register}")
                    return None  # Success
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)
                    print(f"ModbusClient.writeRegister -> Error writing register {register}: {e} - {modbus_error.name}: {modbus_error.description()}")
                    # if modbus_error == ModbusExceptionType.CHECKSUM_ERROR:
                    #     return modbus_error  # Don't retry checksum errors
                    import traceback
                    traceback.print_exc()
                    attempts += 1
                    if attempts < maxAttempts:
                        time.sleep(0.1)
                    else:
                        return modbus_error  # Return the error type after max attempts
        
        return ModbusExceptionType.MODBUS_EXCEPTION  # Fallback

    def writeRegisters(self, start_register, values):
        maxAttempts = 30
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    # print(f"Writing registers starting from {start_register} with values: {values} Attempt {attempts+1}")
                    self.client.write_registers(start_register, values)
                    time.sleep(0.02)
                    # print("Written registers successfully")
                    return None  # Success
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)

                    # if modbus_error != ModbusExceptionType.CHECKSUM_ERROR:
                    import traceback
                    traceback.print_exc()

                    attempts += 1
                    if attempts >= maxAttempts:
                        return modbus_error  # Return error after max attempts



        return ModbusExceptionType.MODBUS_EXCEPTION  # Fallback

    def readRegisters(self, start_register, count):
        maxAttempts = 30
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    # print(f"Read {count} registers starting from register: {start_register}")
                    values = self.client.read_registers(start_register, count)
                    return values, None  # Success - return values and no error
                except Exception as e:
                    print(f"ModbusClient.readRegisters -> Error reading registers: {e}")
                    modbus_error = ModbusExceptionType.from_exception(e)
                    
                    # if modbus_error == ModbusExceptionType.CHECKSUM_ERROR:
                    #     return None, modbus_error  # Return None values with error
                    
                    attempts += 1
                    if attempts >= maxAttempts:
                        return None, modbus_error  # Return error after max attempts
        
        return None, ModbusExceptionType.MODBUS_EXCEPTION  # Fallback

    def read(self, register):
        maxAttempts = 30
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    value = self.client.read_register(register)
                    # print(f"Read value: {value} from register: {register}")
                    return value, None  # Success - return value and no error
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)
                    
                    if modbus_error == ModbusExceptionType.CHECKSUM_ERROR:
                        return None, modbus_error  # Return None value with error
                    
                    attempts += 1
                    if attempts >= maxAttempts:
                        return None, modbus_error  # Return error after max attempts
        
        return None, ModbusExceptionType.MODBUS_EXCEPTION  # Fallback

    def readBit(self,address,functioncode=1):
        with modbus_lock:
            return self.client.read_bit(address,functioncode=functioncode)

    def writeBit(self,address,value):
        maxAttempts = 30
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    self.client.write_bit(address, value)
                    break
                except minimalmodbus.ModbusException as e:
                    if "Checksum error in rtu mode" in str(e):
                        import traceback
                        traceback.print_exc()
                        break
                    else:
                        import traceback
                        traceback.print_exc()
                    attempts += 1
                    time.sleep(0.1)

    def close(self):
        self.client.serial.close()

