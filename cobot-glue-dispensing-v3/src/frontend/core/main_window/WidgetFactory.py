from enum import Enum

from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.calibration.ui.CalibrationAppWidget import CalibrationAppWidget
from plugins.core.contour_editor.ui.ContourEditorAppWidget import ContourEditorAppWidget
from frontend.legacy_ui.app_widgets.CreateWorkpieceOptionsAppWidget import CreateWorkpieceOptionsAppWidget
from plugins.core.dashboard.ui.DashboardAppWidget import DashboardAppWidget
from plugins.core.wight_cells_settings_plugin.ui.GlueWeightCellSettingsAppWidget import GlueWeightCellSettingsAppWidget
from plugins.core.gallery.ui.GalleryAppWidget import GalleryAppWidget
from plugins.core.user_management.ui.UserManagementAppWidget import UserManagementAppWidget


class WidgetType(Enum):
    USER_MANAGEMENT = "User Management"
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

        return UserManagementAppWidget(*args, **kwargs)

    def __create_settings_widget(self, *args, **kwargs):
        print("Creating Settings Widget")
        from frontend.legacy_ui.windows import SettingsAppWidget
        return SettingsAppWidget(controller = self.controller)

    def __create_workpiece_options_widget(self, *args, **kwargs):
        print("Creating Workpiece Options Widget")

        return CreateWorkpieceOptionsAppWidget(controller = self.controller)

    def __create_contour_editor_widget(self, *args, **kwargs):
        print("🔧 Creating Contour Editor Widget via WidgetFactory")
        print(f"🔍 Args: {args}, Kwargs: {kwargs}")
        print(f"🔍 Parent: {self.main_window}, Controller: {self.controller}")
        
        try:
            print("🚀 About to call ContourEditorAppWidget constructor...")
            widget = ContourEditorAppWidget(parent=self.main_window,controller=self.controller)
            print(f"✅ ContourEditorAppWidget created successfully: {type(widget)}")
            print(f"🔍 Widget has content_widget: {hasattr(widget, 'content_widget')}")
            if hasattr(widget, 'content_widget'):
                print(f"🔍 Content widget type: {type(widget.content_widget)}")
            return widget
        except Exception as e:
            print(f"❌ Failed to create ContourEditorAppWidget: {e}")
            import traceback
            traceback.print_exc()
            # Return a basic AppWidget as fallback
            return AppWidget(app_name="Contour Editor (Error)")

    def __create_dashboard_widget(self, *args, **kwargs):
        print("Creating Dashboard Widget")

        return DashboardAppWidget(controller=self.controller)

    def __create_gallery_widget(self, *args, **kwargs):
        print("Creating Gallery Widget")
        return GalleryAppWidget(controller=self.controller)

    def __create_calibration_widget(self, *args, **kwargs):
        print("Creating Calibration Widget")
        return CalibrationAppWidget(controller_service=self.controller)

    def __create_glue_weight_cell_settings_widget(self, *args, **kwargs):
        print("Creating Glue Weight Cell Settings Widget")
        return GlueWeightCellSettingsAppWidget(parent = self.main_window,controller=None)

    def __create_dxf_browser_widget(self, *args, **kwargs):
        print("Creating DXF Browser Widget")
        # from pl_ui.ui.windows.mainWindow.appWidgets.DXFBrowserAppWidget import DXFBrowserAppWidget
        # return DXFBrowserAppWidget(*args, **kwargs)


