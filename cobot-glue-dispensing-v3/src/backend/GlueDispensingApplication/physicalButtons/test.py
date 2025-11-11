import time

from modbusCommunication.ModbusClient import ModbusClient
import minimalmodbus
from modules.shared.utils.linuxUtils import get_modbus_port
port = get_modbus_port()
client = ModbusClient(slave=1,
                      port=port,
                      baudrate=115200,
                      bytesize=8,
                      parity=minimalmodbus.serial.PARITY_NONE,
                      stopbits=1,
                      timeout=0.5)


result = client.writeRegister(12,0)
print("Result:", result)

time.sleep(5)

result,errors = client.read(12)
print("Result:", result, "Errors:", errors)