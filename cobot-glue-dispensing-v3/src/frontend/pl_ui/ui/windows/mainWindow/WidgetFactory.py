from enum import Enum

from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget
from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.GalleryAppWidget import GalleryAppWidget


class WidgetType(Enum):
    USER_MANAGEMENT = "user_management"
    SETTINGS = "settings"
    CREATE_WORKPIECE_OPTIONS =  "create_workpiece_options"
    CONTOUR_EDITOR = "contour_editor"
    DASHBOARD = "dashboard"
    GALLERY = "gallery"
    CALIBRATION = "calibration"
    GLUE_WEIGHT_CELL = "glue_weight_cell"  # Placeholder for future glue weight cell widget
    DXF_BROWSER = "dxf_browser"
    SERVICE = "service" # Placeholder for future service widget
    ANALYTICS = "analytics"  # Placeholder for future analytics widget
    REPORTS = "reports"  # Placeholder for future reports widget
    METRICS = "metrics"  # Placeholder for future metrics widget

    @classmethod
    def get_from_value(cls, value):
        try:
            return cls(value)  # Enum constructor
        except ValueError:
            return None


class WidgetFactory:
    def __init__(self,controller,main_window):
        self.controller= controller
        self.main_window = main_window
        self.widget_method_map = {
            WidgetType.USER_MANAGEMENT: self.__create_user_management_widget,
            WidgetType.SETTINGS: self.__create_settings_widget,
            WidgetType.CREATE_WORKPIECE_OPTIONS: self.__create_workpiece_options_widget,
            WidgetType.CONTOUR_EDITOR: self.__create_contour_editor_widget,
            WidgetType.DASHBOARD: self.__create_dashboard_widget,
            WidgetType.GALLERY: self.__create_gallery_widget,
            WidgetType.CALIBRATION: self.__create_calibration_widget,
            WidgetType.GLUE_WEIGHT_CELL: self.__create_glue_weight_cell_settings_widget,
            WidgetType.DXF_BROWSER: self.__create_dxf_browser_widget,
        }

    def create_widget(self, widget_type, *args, **kwargs):
        print(f"Request to create widget of type: {widget_type}")
        print(f"args: {args}, kwargs: {kwargs}")
        create_widget_method = self.widget_method_map.get(widget_type)
        if create_widget_method:
            return create_widget_method(*args, **kwargs)
        else:
            # Fallback to default widget
            return AppWidget(app_name="Default Widget")
            # raise ValueError(f"Unsupported widget type: {widget_type}")

    def __create_user_management_widget(self, *args, **kwargs):
        print("Creating User Management Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.UserManagementAppWidget import UserManagementAppWidget
        return UserManagementAppWidget(*args, **kwargs)

    def __create_settings_widget(self, *args, **kwargs):
        print("Creating Settings Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.SettingsAppWidget import SettingsAppWidget
        return SettingsAppWidget(controller = self.controller)

    def __create_workpiece_options_widget(self, *args, **kwargs):
        print("Creating Workpiece Options Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.CreateWorkpieceOptionsAppWidget import CreateWorkpieceOptionsAppWidget
        return CreateWorkpieceOptionsAppWidget(controller = self.controller)

    def __create_contour_editor_widget(self, *args, **kwargs):
        print("Creating Contour Editor Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.ContourEditorAppWidget import ContourEditorAppWidget
        return ContourEditorAppWidget(parent=self.main_window,controller=self.controller)

    def __create_dashboard_widget(self, *args, **kwargs):
        print("Creating Dashboard Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.DashboardAppWidget import DashboardAppWidget
        return DashboardAppWidget(controller=self.controller)

    def __create_gallery_widget(self, *args, **kwargs):
        print("Creating Gallery Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.GalleryAppWidget import GalleryAppWidget
        return GalleryAppWidget(controller=self.controller)

    def __create_calibration_widget(self, *args, **kwargs):
        print("Creating Calibration Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.CalibrationAppWidget import CalibrationAppWidget
        return CalibrationAppWidget(controller=self.controller)

    def __create_glue_weight_cell_settings_widget(self, *args, **kwargs):
        print("Creating Glue Weight Cell Settings Widget")
        from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.GlueWeightCellSettingsAppWidget import GlueWeightCellSettingsAppWidget
        return GlueWeightCellSettingsAppWidget(parent = self.main_window,controller=None)

    def __create_dxf_browser_widget(self, *args, **kwargs):
        print("Creating DXF Browser Widget")
        return GalleryAppWidget(*args, **kwargs)
        # from pl_ui.ui.windows.mainWindow.appWidgets.DXFBrowserAppWidget import DXFBrowserAppWidget
        # return DXFBrowserAppWidget(*args, **kwargs)


if __name__ == "__main__":
    class MockController:
        pass
    factory = WidgetFactory(controller=MockController())
    factory.create_widget(WidgetType.USER_MANAGEMENT)
    factory.create_widget(WidgetType.SETTINGS)
    factory.create_widget(WidgetType.DASHBOARD)
    try:
        factory.create_widget("INVALID_TYPE")
    except ValueError as e:
        print(e)
