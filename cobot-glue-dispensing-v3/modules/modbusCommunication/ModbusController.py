from modules.modbusCommunication.ModbusClient import ModbusClient
# from utils.linuxUtils import get_modbus_port
import minimalmodbus

class ModbusController:
    @classmethod
    def getModbusClient(cls,slaveId):
        # port = get_modbus_port()
        port = "/dev/ttyUSB0"
        # port = "/dev/ttyS1"
        # client = minimalmodbus.Instrument(port, slaveId)
        client = ModbusClient(slave=slaveId, port=port)
        # print(f"Connected Port: {port} Slave Id: {slaveId}")

        """CLIENT CONFIG"""
        client.client.serial.baudrate = 115200
        client.client.serial.bytesize = 8
        client.client.serial.parity = minimalmodbus.serial.PARITY_NONE
        client.client.serial.stopbits = 1
        client.client.serial.timeout = 0.02  # 10 ms timeout
        client.clear_buffers_before_each_transaction = True
        # client.close_port_after_each_call = False
        client.mode = minimalmodbus.MODE_RTU
        client.client.serial.inter_byte_timeout = 0.01  # 10 ms delay

        return client

