import sys

from PyQt6.QtWidgets import QApplication

from src.frontend.pl_ui.ui.windows.dashboard.DashboardWidget import DashboardWidget

if __name__ == "__main__":
    def updateCameraFeedCallback():
        print("updating camera feed")


    app = QApplication(sys.argv)
    dashboard = DashboardWidget(updateCameraFeedCallback)
    dashboard.resize(1200, 800)  # Increased default size for better layout
    dashboard.show()
    sys.exit(app.exec())