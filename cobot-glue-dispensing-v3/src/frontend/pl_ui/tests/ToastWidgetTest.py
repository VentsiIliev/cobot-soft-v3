import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from src.frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    main_window: QMainWindow = QMainWindow()
    main_window.resize(600, 400)
    main_window.show()

    toast: ToastWidget = ToastWidget(
        parent=main_window,
        message="This is toast message",
        duration=3000,
    )
    toast.show()

    sys.exit(app.exec())