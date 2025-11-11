import threading
import time
from abc import ABC, abstractmethod
from modules.shared.MessageBroker import MessageBroker


SENSOR_STATE_CONNECTED = "Connected"
SENSOR_STATE_DISCONNECTED = "Disconnected"
SENSOR_STATE_UNKNOWN = "Unknown"
SENSOR_STATE_INITIALIZING = "Initializing"
SENSOR_STATE_ERROR = "Error"
SENSOR_STATE_READY = "Ready"
SENSOR_STATE_BUSY = "Busy"
SENSOR_STATE_RECONNECTING = "Reconnecting"
SENSOR_STATE_NO_COMMUNICATION = "No Communication"
SENSOR_STATE_USB_NOT_CONNECTED = "USB Not Connected"
# Abstract base class to enforce implementation of methods
class Sensor(ABC):
    def __init__(self, name, state,type="modbus"):
        self.name = name
        self.state = state
        self.value = None
        self.pollTime = 1
        self.type = type

    @abstractmethod
    def getState(self):
        pass

    @abstractmethod
    def getValue(self):
        pass

    @abstractmethod
    def getName(self):
        pass

    @abstractmethod
    def testConnection(self):
        pass

    @abstractmethod
    def reconnect(self):
        pass

class SensorPublisher:
    def __init__(self):
        self.sensors = []
        self.broker = MessageBroker()
        self._stop_thread = threading.Event()
        self.threads = []
        self.modbus_sensors = []
        self.modbus_thread = None

    def _publish_sensor(self, sensor):
        while not self._stop_thread.is_set():
            try:
                sensor.testConnection()
                state = sensor.getState()
                value = sensor.getValue()
                self.broker.publish(f"{sensor.getName()}/STATE", state)
                self.broker.publish(f"{sensor.getName()}/VALUE", value)
            except Exception as e:
                print(f"Error in sensor {sensor.getName()}: {e}")
            time.sleep(sensor.pollTime)

    def _publish_modbus_sensors(self):
        while not self._stop_thread.is_set():
            for sensor in self.modbus_sensors:
                try:
                    sensor.testConnection()
                    state = sensor.getState()
                    value = sensor.getValue()
                    self.broker.publish(f"{sensor.getName()}/STATE", state)
                    self.broker.publish(f"{sensor.getName()}/VALUE", value)
                except Exception as e:
                    print(f"Error in Modbus sensor {sensor.getName()}: {e}")
                time.sleep(sensor.pollTime)
            # Optional: small delay to avoid a tight loop
            time.sleep(0.1)

    def registerSensor(self, sensor):
        self.sensors.append(sensor)
        print(f"[SensorPublisher] Registered sensor: {sensor.getName()}")
        if sensor.type == "modbus":
            self.modbus_sensors.append(sensor)
            # Start modbus thread if not already started
            if self.modbus_thread is None or not self.modbus_thread.is_alive():
                self.modbus_thread = threading.Thread(target=self._publish_modbus_sensors, daemon=True)
                self.modbus_thread.start()
                self.threads.append(self.modbus_thread)
        else:
            t = threading.Thread(target=self._publish_sensor, args=(sensor,), daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self._stop_thread.set()
        for t in self.threads:
            t.join()


# EXAMPLE Concrete class implementing the Sensor interface
class TemperatureSensor(Sensor):
    def __init__(self, name, state):
        super().__init__(name, state)

    def getState(self):
        return self.state

    def getValue(self):
        # Simulate a temperature value
        return 25.0

    def getName(self):
        return self.name


    def testConnection(self):
        pass


    def reconnect(self):
        pass

# Example usage
if __name__ == "__main__":
    publisher = SensorPublisher()

    # Register concrete sensors
    sensor1 = TemperatureSensor(name="TemperatureSensor", state="Active")

    publisher.registerSensor(sensor1)

    # publisher.start()
    time.sleep(10)
    publisher.stop()
