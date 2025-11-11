from PyQt6.QtWidgets import QApplication
from src.frontend.pl_ui.utils.IconLoader import BACKGROUND

from src.frontend.pl_ui.ui.widgets.CameraFeed import CameraFeed,CameraFeedConfig


def update_callback():
    print("Update callback triggered")


if __name__ == "__main__":
    import sys

    cameraFeedConfig = CameraFeedConfig(
        updateFrequency=30,
        screen_size=(1280, 720),
        resolution_small=(320, 180),
        resolution_large=(1280, 720),
        current_resolution=(1280, 720)
    )

    app = QApplication(sys.argv)
    window = CameraFeed(cameraFeedConfig=cameraFeedConfig,updateCallback=update_callback)
    window.set_image(BACKGROUND)
    window.show()
    sys.exit(app.exec())
