# modbusCommunication/MockClient.py
import random

class MockSerial:
    """Mock replacement for the .serial attribute."""
    def __init__(self, port, baudrate=115200, bytesize=8, stopbits=1, timeout=0.01, parity="N"):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.timeout = timeout
        self.parity = parity
        self.is_open = True

    def close(self):
        self.is_open = False
        print(f"[MOCK SERIAL] Closed port {self.port}")


class MockInstrument:
    """Mock replacement for minimalmodbus.Instrument."""
    def __init__(self, port, slaveaddress, debug=False):
        self.port = port
        self.slaveaddress = slaveaddress
        self.debug = debug
        self.serial = MockSerial(port)
        self.registers = {}
        self.bits = {}
        print(f"[MOCK] Created MockInstrument on {port}, slave {slaveaddress}")

    def write_register(self, register, value, signed=False):
        self.registers[register] = value
        print(f"[MOCK] write_register({register}, {value}, signed={signed})")

    def write_registers(self, start_register, values):
        for i, v in enumerate(values):
            self.registers[start_register + i] = v
        print(f"[MOCK] write_registers(start={start_register}, values={values})")

    def read_register(self, register):
        return self.registers.get(register, 0)

    def read_registers(self, start_register, count):
        return [self.registers.get(start_register + i, 0) for i in range(count)]

    def read_bit(self, address, functioncode=1):
        return self.bits.get(address, 0)

    def write_bit(self, address, value):
        self.bits[address] = value
