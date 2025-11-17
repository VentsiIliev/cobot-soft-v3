import os
import sys

from PyQt6.QtWidgets import QApplication

from modules.shared.core.settings.conreateSettings.CameraSettings import CameraSettings
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from modules.shared.core.settings.conreateSettings.RobotSettings import RobotSettings
from modules.shared.core.user import User
from modules.shared.core.user.CSVUsersRepository import CSVUsersRepository
from modules.shared.core.user.Session import SessionManager
from modules.shared.core.user.User import UserField
from modules.shared.core.user.UserService import UserService
from frontend.pl_ui.Endpoints import GET_SETTINGS
from frontend.pl_ui.ui.windows.mainWindow.MainWindow import MainWindow


class MockController:
    def __init__(self):
        print("MockController initialized")

    def handle(self, *args):
        first_arg = args[0]

        if first_arg == GET_SETTINGS:

            return self.__getSettings()


    def sendRequest(self, message):
        if message == GET_SETTINGS:
            return self.__getSettings()

        print("Sending Request: ", message)
        return True, {"image": "MockImage",
                      "height": 4}

    def updateCameraFeed(self):
        pass

    def saveWorkpiece(self, data):
        print("Saving WP: ", data)

    def sendJogRequest(self, request):
        print("Sending Jog Request: ", request)

    def saveRobotCalibrationPoint(self):
        print("Saving Robot Point")

    def __getSettings(self):
        cameraSettings = CameraSettings()
        robotSettings = RobotSettings()
        glueSettings = GlueSettings()
        print(f"Returning settings: {cameraSettings}, {robotSettings}, {glueSettings}")
        return cameraSettings, robotSettings, glueSettings

    def saveWorkpieceFromDXF(self, data):
        print("Saving wp from dxf: ", data)

    def handleLogin(self, user, password):
        csv_file_path = os.path.join(os.path.dirname(__file__), "shared/shared/user/users.csv")
        user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME, UserField.PASSWORD, UserField.ROLE]
        repo = CSVUsersRepository(csv_file_path, user_fields, User)
        service = UserService(repo)

        user = service.getUserById(2)
        SessionManager.login(user)
        return "1"


def main():
    app = QApplication(sys.argv)
    print("App started")
    # Set application style
    # app.setStyle('Fusion')

    # Create and show demo
    controller = MockController()
    print("Controller created")
    demo = MainWindow(controller)
    print("Main window created")
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
