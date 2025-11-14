from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QSizePolicy,
                             QApplication)
from typing import Callable

# CHANGE: Import the new FolderController system instead of old Folder
from frontend.pl_ui.ui.windows.mainWindow.Folder import FolderWidget, FolderController


@dataclass
class FolderConfig:
    ID: int
    name: str
    apps: list
    translate_fn: Callable = None  # Optional translation callback


class FoldersPage(QWidget):
    """Manages the main folders page layout using FolderController system"""

    # Signals to communicate with the main window
    folder_opened = pyqtSignal(object)  # FolderController object
    folder_closed = pyqtSignal()
    app_selected = pyqtSignal(str)  # App name
    close_current_app_requested = pyqtSignal()

    def __init__(self, parent=None, folder_config_list=None,main_window=None):
        super().__init__(parent)
        self.folder_config_list = folder_config_list
        self.folder_controllers = []  # Track all folder controllers
        self.folder_widgets = []  # Track all folder widgets
        self.main_window = main_window  # Store main window reference
        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI for the folders page"""
        # Main container widget with size constraints
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Use a main layout to center the container
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(40, 40, 40, 40)
        page_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)

        # Grid layout for folders with controlled spacing
        layout = QGridLayout(container)
        layout.setSpacing(30)  # Reasonable spacing between folders
        layout.setContentsMargins(0, 0, 0, 0)

        # Create and configure all folders
        self.__create_folders()

        # Add folders to grid (3 columns, 2 rows) with center alignment
        self.__add_folders_to_layout(layout)

        # Set the container to use its content size
        container.adjustSize()

    def __create_folders(self):
        """Create all folders using the new FolderController system"""
        for config in self.folder_config_list:
            ID = config.ID
            folder_name = config.name
            apps = config.apps
            translate_fn = config.translate_fn

            # Create folder widget and controller
            folder_widget, folder_controller = self.__create_folder(ID,folder_name, apps,translate_fn)

            # Store both widget and controller
            self.folder_widgets.append(folder_widget)
            self.folder_controllers.append(folder_controller)

        # Connect signals after all folders are created
        self.__connect_folder_signals()

    def __create_folder(self, ID,folder_name, apps,translate_fn):
        from frontend.pl_ui.localization import get_app_translator

        """Create a folder widget and its controller"""
        # Create folder widget
        folder_widget = FolderWidget(ID,folder_name)
        folder_widget.translate_fn = translate_fn
        
        # Connect to new translation system
        translator = get_app_translator()
        translator.language_changed.connect(folder_widget.update_title_label)

        # Add apps to folder widget
        for widget_type, icon_path in apps:
            folder_widget.add_app(widget_type.value, icon_path)

        # Create controller
        # print(f"Creating FolderController for folder '{folder_name}' with ID = {ID} with main_window: {self.main_window}")
        folder_controller = FolderController(folder_widget, self.main_window)

        return folder_widget, folder_controller

    def __add_folders_to_layout(self, layout):
        """Add folder widgets to the grid layout dynamically"""
        columns = 3
        for idx, folder_widget in enumerate(self.folder_widgets):
            row = idx // columns
            col = idx % columns
            layout.addWidget(folder_widget, row, col, Qt.AlignmentFlag.AlignCenter)

    def __connect_folder_signals(self):
        """Connect signals for all folder controllers"""
        for folder_controller in self.folder_controllers:
            # Connect controller signals to local handlers
            folder_controller.folder_opened.connect(self.on_folder_opened)
            folder_controller.folder_closed.connect(self.on_folder_closed)
            folder_controller.app_selected.connect(self.on_app_selected)
            folder_controller.close_current_app_signal.connect(self.on_close_current_app_requested)

    def on_folder_opened(self, opened_folder_controller=None):
        """Handle when a folder is opened - gray out other folders"""
        # print(f"FoldersPage: Folder opened by controller")

        # Find which controller opened
        opened_controller = self.sender() if opened_folder_controller is None else opened_folder_controller

        # # Gray out other folders
        # for folder_controller in self.folder_controllers:
        #     if folder_controller != opened_controller:
        #         folder_controller.set_disabled(True)

        # Emit signal to main window - pass the controller instead of old folder object
        self.folder_opened.emit(opened_controller)

    def enable_folder_by_id(self, ID):
        """Enable a folder by its name"""
        for folder_controller in self.folder_controllers:
            if folder_controller.folder_widget.ID == ID:
                folder_controller.set_disabled(False)
                # print(f"FoldersPage: Enabled folder '{ID}'")
                return
        # print(f"FoldersPage: Folder with ID ='{ID}' not found to enable")

    def disable_folder_by_id(self, ID):
        """Disable a folder by its name"""
        for folder_controller in self.folder_controllers:
            if folder_controller.folder_widget.ID == ID:
                folder_controller.set_disabled(True)
                # print(f"FoldersPage: Disabled folder '{ID}'")
                return
        # print(f"FoldersPage: Folder with ID ='{ID}' not found to disable")

    def on_folder_closed(self):
        """Handle when a folder is closed - restore all folders"""
        # print("FoldersPage: Folder closed - restoring all folders")

        # # Restore all folders
        # for folder_controller in self.folder_controllers:
        #     folder_controller.set_disabled(False)

        # Emit signal to main window
        self.folder_closed.emit()

    def on_app_selected(self, app_name):
        """Handle when an app is selected from any folder"""
        # print(f"FoldersPage: App selected - {app_name}")
        # Emit signal to main window
        self.app_selected.emit(app_name)

    def on_close_current_app_requested(self):
        """Handle when close current app is requested"""
        # print("FoldersPage: Close current app requested")
        # Emit signal to main window
        self.close_current_app_requested.emit()

    def get_folders(self):
        """Get the list of all folder controllers (updated for compatibility)"""
        return self.folder_controllers

    def get_folder_controllers(self):
        """Get the list of all folder controllers"""
        return self.folder_controllers

    def get_folder_widgets(self):
        """Get the list of all folder widgets"""
        return self.folder_widgets


if __name__ == "__main__":
    import sys
    from frontend.pl_ui.ui.windows.mainWindow.WidgetFactory import WidgetType
    from frontend.pl_ui.utils.IconLoader import (DASHBOARD_ICON, CREATE_WORKPIECE_ICON, GALLERY_ICON,
                                        SETTINGS_ICON, CALIBRATION_ICON, USER_MANAGEMENT_ICON,
                                        PLACEHOLDER_ICON)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = QWidget()
    window.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(248, 250, 252, 1),
                stop:1 rgba(241, 245, 249, 1));
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
    """)
    layout = QVBoxLayout(window)

    # Test folder configurations
    folder_config_list = [
        FolderConfig(name="Work", apps=[[WidgetType.DASHBOARD, DASHBOARD_ICON],
                                        [WidgetType.CREATE_WORKPIECE_OPTIONS, CREATE_WORKPIECE_ICON],
                                        [WidgetType.GALLERY, GALLERY_ICON]]),
        FolderConfig(name="Service", apps=[[WidgetType.SETTINGS, SETTINGS_ICON],
                                           [WidgetType.CALIBRATION, CALIBRATION_ICON]]),
        FolderConfig(name="Administration", apps=[[WidgetType.USER_MANAGEMENT, USER_MANAGEMENT_ICON]])
    ]

    folders_page = FoldersPage(folder_config_list=folder_config_list)

    # Set main window reference for testing
    # folders_page.set_main_window_reference(window)

    # Connect test signals
    folders_page.app_selected.connect(lambda app: print(f"TEST: App selected - {app}"))
    folders_page.folder_opened.connect(lambda: print("TEST: Folder opened"))
    folders_page.folder_closed.connect(lambda: print("TEST: Folder closed"))

    layout.addWidget(folders_page)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    window.resize(1200, 800)
    window.show()

    print("Updated FoldersPage using FolderController system!")
    print("Try opening a folder and clicking outside - it should work now!")

    sys.exit(app.exec())