from typing import Dict, Any, List

from core.application_state_management import ApplicationState
from core.base_robot_application import BaseRobotApplication, ApplicationMetadata
from core.operation_state_management import IOperation, OperationStatePublisher, OperationResult
from modules.shared.MessageBroker import MessageBroker


class TestOperation(IOperation):

    def __init__(self, broker: MessageBroker):
        self.broker = broker
        super().__init__()
        self.set_state_publisher(OperationStatePublisher(broker=self.broker))

    def _do_start(self, *args, **kwargs)->OperationResult:
        print(f"Starting TestOperation with args: {args}, kwargs: {kwargs}")
        return OperationResult(success=True, message="TestOperation started")

    def _do_stop(self, *args, **kwargs)->OperationResult:
        print("Stopping TestOperation with args:", args, "kwargs:", kwargs)
        return OperationResult(success=True, message="TestOperation stopped")

    def _do_pause(self, *args, **kwargs)->OperationResult:
        print(f"Pausing TestOperation with args: {args}, kwargs: {kwargs}")
        return OperationResult(success=True, message="TestOperation paused")

    def _do_resume(self, *args, **kwargs)->OperationResult:
        print(f"Resuming TestOperation with args: {args}, kwargs: {kwargs}")
        return OperationResult(success=True, message="TestOperation resumed")


class TestApplication(BaseRobotApplication):
    def __init__(self, vision_service,settings_manager,robot_service,settings_registry, **kwargs):
        super().__init__(vision_service,settings_manager,robot_service,settings_registry, **kwargs)
        operation_1 = TestOperation(self.broker)
        operation_2 = TestOperation(self.broker)
        self.current_operation = operation_1

    @property
    def operation(self):
        return self.current_operation

    @staticmethod
    def get_metadata() -> ApplicationMetadata:
        return ApplicationMetadata(name="TestApplication",
                                   version="1.0.0",
                                   dependencies=["_VisionService",
                                                 "SettingsService",
                                                 "BaseRobotService",
                                                 "ApplicationSettingsRegistry"])

    def get_initial_state(self) -> ApplicationState:
        return ApplicationState.INITIALIZING

    def set_current_operation(self):
        self.current_operation = TestOperation(broker=self.broker)

    def __on_operation_start(self,**kwargs) -> OperationResult:
        print("[TestApplication] Operation is starting...")
        return OperationResult(success=True, message="Operation started in TestApplication")


    def stop(self) -> OperationResult:
        return self.operation.stop()

    def pause(self) -> OperationResult:
        return self.operation.pause()

    def resume(self) -> OperationResult:
        return self.operation.resume()

    def on_mode_change(self,mode):
        print(f"[TestApplication] Mode changed to {mode}")

    def calibrate_camera(self) -> Dict[str, Any]:
        print("[TestApplication] Calibrating camera...")
        return {"result": "camera calibrated"}

    def calibrate_robot(self):
        print("[TestApplication] Calibrating robot...")
        return {"result": "robot calibrated"}

    def get_supported_operations(self) -> List[str]:
        return ["test_operation"]

    def validate_configuration(self) -> Dict[str, Any]:
        print("[TestApplication] Validating configuration...")
        return {"result": "configuration valid"}
