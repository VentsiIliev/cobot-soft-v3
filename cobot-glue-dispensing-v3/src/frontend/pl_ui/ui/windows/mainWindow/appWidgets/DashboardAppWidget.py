from PyQt6.QtCore import pyqtSignal

from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget


class DashboardAppWidget(AppWidget):
    """Specialized widget for User Management application"""
    # define logout signal
    LOGOUT_REQUEST = pyqtSignal()
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    clean_requested = pyqtSignal()
    reset_errors_requested = pyqtSignal()
    start_demo_requested = pyqtSignal()
    stop_demo_requested = pyqtSignal()
    mode_toggle_requested = pyqtSignal(str)

    def __init__(self, parent=None,controller=None):
        self.controller = controller
        super().__init__("Dashboard", parent)
    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            from src.frontend.pl_ui.ui.windows.dashboard.DashboardWidget import DashboardWidget
            from src.frontend.pl_ui.Endpoints import UPDATE_CAMERA_FEED
            # Remove the placeholder content
            self.content_widget = DashboardWidget(updateCameraFeedCallback=lambda: self.controller.handle(UPDATE_CAMERA_FEED))
            self.content_widget.start_requested.connect(self.start_requested.emit)
            self.content_widget.pause_requested.connect(self.pause_requested.emit)
            self.content_widget.stop_requested.connect(self.stop_requested.emit)
            self.content_widget.clean_requested.connect(self.on_clean)
            self.content_widget.reset_errors_requested.connect(self.reset_errors_requested.emit)
            self.content_widget.glue_type_changed_signal.connect(self.on_glue_type_changed)
            self.content_widget.start_demo_requested.connect(self.start_demo_requested.emit)
            self.content_widget.stop_demo_requested.connect(self.stop_demo_requested.emit)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            import traceback
            traceback.print_exc()
            # Keep the placeholder if the UserManagementWidget is not available
            print("Dashboard not available, using placeholder")

    def on_clean(self):
        print("Clean requested from DashboardAppWidget")
        self.clean_requested.emit()
    def onLogOut(self):
        print("Logout requested from Dashboard")

    def __del__(self):
        """Cleanup when the dashboard app widget is destroyed"""
        self._cleanup_dashboard()

    def _cleanup_dashboard(self):
        """Cleanup dashboard widgets and their MessageBroker subscriptions"""
        try:
            if hasattr(self, 'content_widget') and self.content_widget:
                dashboard_widget = self.content_widget
                print(f"Dashboard widget attributes: {[attr for attr in dir(dashboard_widget) if not attr.startswith('_')]}")
                
                # Try to access cards through glue_cards_dict (from DashboardWidget.py:120)
                if hasattr(dashboard_widget, 'glue_cards_dict'):
                    print(f"Found glue_cards_dict with {len(dashboard_widget.glue_cards_dict)} cards")
                    for index, card in dashboard_widget.glue_cards_dict.items():
                        print(f"Processing card {index}: {type(card)}")
                        print(f"Card {index} attributes: {[attr for attr in dir(card) if not attr.startswith('_')]}")
                        
                        # Try different ways to find the GlueMeterWidget
                        # Check content_widgets first (this is the correct attribute)
                        if hasattr(card, 'content_widgets') and card.content_widgets:
                            print(f"Card {index} has {len(card.content_widgets)} content widgets: {[type(w) for w in card.content_widgets]}")
                            # Find GlueMeterWidget in the card's content_widgets
                            for widget in card.content_widgets:
                                if hasattr(widget, '__class__') and 'GlueMeterWidget' in widget.__class__.__name__:
                                    print(f"Found GlueMeterWidget {widget.id} in content_widgets - manually unsubscribing")
                                    # Manually call the cleanup
                                    try:
                                        from modules.shared.MessageBroker import MessageBroker
                                        broker = MessageBroker()
                                        broker.unsubscribe(f"GlueMeter_{widget.id}/VALUE", widget.updateWidgets)
                                        broker.unsubscribe(f"GlueMeter_{widget.id}/STATE", widget.updateState)
                                        print(f"Successfully unsubscribed GlueMeterWidget {widget.id}")
                                    except Exception as e:
                                        print(f"Error unsubscribing GlueMeterWidget {widget.id}: {e}")
                        
                        # Also check legacy widgets attribute
                        elif hasattr(card, 'widgets') and card.widgets:
                            print(f"Card {index} has {len(card.widgets)} widgets: {[type(w) for w in card.widgets]}")
                            # Find GlueMeterWidget in the card's widgets (DashboardCard structure)
                            for widget in card.widgets:
                                if hasattr(widget, '__class__') and 'GlueMeterWidget' in widget.__class__.__name__:
                                    print(f"Found GlueMeterWidget {widget.id} - manually unsubscribing")
                                    # Manually call the cleanup
                                    try:
                                        from modules.shared.MessageBroker import MessageBroker
                                        broker = MessageBroker()
                                        broker.unsubscribe(f"GlueMeter_{widget.id}/VALUE", widget.updateWidgets)
                                        broker.unsubscribe(f"GlueMeter_{widget.id}/STATE", widget.updateState)
                                        print(f"Successfully unsubscribed GlueMeterWidget {widget.id}")
                                    except Exception as e:
                                        print(f"Error unsubscribing GlueMeterWidget {widget.id}: {e}")
                        else:
                            print(f"Card {index} has no content_widgets or widgets attribute")
                            # Try to find widgets through other attributes
                            for attr_name in dir(card):
                                if not attr_name.startswith('_'):
                                    attr_value = getattr(card, attr_name)
                                    if hasattr(attr_value, '__class__') and 'GlueMeterWidget' in attr_value.__class__.__name__:
                                        print(f"Found GlueMeterWidget in card.{attr_name} - manually unsubscribing")
                                        try:
                                            from modules.shared.MessageBroker import MessageBroker
                                            broker = MessageBroker()
                                            broker.unsubscribe(f"GlueMeter_{attr_value.id}/VALUE", attr_value.updateWidgets)
                                            broker.unsubscribe(f"GlueMeter_{attr_value.id}/STATE", attr_value.updateState)
                                            print(f"Successfully unsubscribed GlueMeterWidget {attr_value.id}")
                                        except Exception as e:
                                            print(f"Error unsubscribing GlueMeterWidget {attr_value.id}: {e}")
                
                # Also try original path as backup
                if hasattr(dashboard_widget, 'glue_meter_cards'):
                    print("Found glue_meter_cards - cleaning up")
                    for card in dashboard_widget.glue_meter_cards:
                        if hasattr(card, 'unsubscribe'):
                            card.unsubscribe()
                
                print("Dashboard widgets cleaned up")
        except Exception as e:
            print(f"Error during dashboard cleanup: {e}")

    def closeEvent(self, event):
        """Handle close event"""
        self._cleanup_dashboard()
        super().closeEvent(event)
        self.LOGOUT_REQUEST.emit()

    def on_glue_type_changed(self, index,glue_type):
        print(f"Glue type of {index} changed to: {glue_type} ")
        from src.backend.robot_application.glue_dispensing_application.tools.GlueCell import GlueCellsManagerSingleton
        manager = GlueCellsManagerSingleton.get_instance()
        manager.updateGlueTypeById(index,glue_type)

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print(">>> DashboardAppWidget.clean_up() called")
        self._cleanup_dashboard()
        super().clean_up() if hasattr(super(), 'clean_up') else None
