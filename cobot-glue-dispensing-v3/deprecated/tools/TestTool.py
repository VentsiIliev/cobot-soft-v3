class TestTool:

    def __init__(self):
        self.xOffset = -53  # x offset from the main tooltip
        self.yOffset = -6  # y offset from the main tooltip
        self.zOffset = 0  # z offset from the main tooltip
        # self.modbusClient = ModbusClient(port=self.WINDOWS_PORT)
        self.modbusClient = None
