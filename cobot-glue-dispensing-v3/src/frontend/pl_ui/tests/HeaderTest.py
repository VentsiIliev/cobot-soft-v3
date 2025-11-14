# For test/demo
import sys

from PyQt6.QtWidgets import QApplication

from frontend.pl_ui.ui.widgets.Header import Header

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    header: Header = Header(
        screen_size.width(),
        screen_size.height(),
        lambda: print("Menu toggled"),
        lambda: print("Dashboard clicked"),
    )
    header.show()
    sys.exit(app.exec())