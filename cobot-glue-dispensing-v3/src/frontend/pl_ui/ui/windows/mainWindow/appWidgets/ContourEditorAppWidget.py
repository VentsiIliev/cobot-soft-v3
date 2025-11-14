from frontend.pl_ui.Endpoints import UPDATE_CAMERA_FEED, CREATE_WORKPIECE_STEP_2, SAVE_WORKPIECE, GET_LATEST_IMAGE
from frontend.pl_ui.localization import TranslationKeys
from frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget
from frontend.pl_ui.ui.widgets.CustomFeedbackDialog import CustomFeedbackDialog, DialogType


class ContourEditorAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None,controller=None):
        self.controller = controller
        self.parent = parent
        self.content_widget = None
        super().__init__("Contour Editor", parent)
    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            from frontend.pl_ui.contour_editor.ContourEditor import MainApplicationFrame
            # Remove the placeholder content
            self.content_widget = MainApplicationFrame(parent=self.parent)
            self.content_widget.capture_requested.connect(self.on_camera_capture_requested)
            self.content_widget.update_camera_feed_requested.connect(self.on_update_camera_feed_requested)
            self.content_widget.save_workpiece_requested.connect(lambda data: self.via_camera_on_create_workpiece_submit(data))
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            import traceback
            traceback.print_exc()
            print("Contour Editor not available, using placeholder")


    def on_update_camera_feed_requested(self):
        image = self.controller.handle(UPDATE_CAMERA_FEED)
        if image is None:
            # print("No image received for camera feed update")
            return
        self.content_widget.set_image(image)
        # print(f"Updated camera feed in Contour Editor")

    def on_camera_capture_requested(self):
        """
        Handle camera capture requested signal.

        Uses CaptureDataHandler to centralize the capture flow and ensure
        it goes through the proper ContourEditorData pipeline.
        """
        print("Camera capture requested from Contour Editor")
        result, message, data = self.controller.handle(CREATE_WORKPIECE_STEP_2)

        if not result:
            # show error message box
            warning_dialog = CustomFeedbackDialog(
                parent=self,
                title="Warning",
                message=f"Failed to capture image: {message}",
                dialog_type=DialogType.INFO,
                ok_text="OK",
                cancel_text=None
            )
            warning_dialog.show()
            return

        print(f"CREATE_WORKPIECE_STEP_2 result: {result}, message: {message}, data keys: {list(data.keys())}")

        # Handle image update
        image = data.get("image")
        if image is not None:
            print("Updating Contour Editor with new image")
            # pause the camera feed update timer
            self.content_widget.contourEditor.camera_feed_update_timer.stop()
            self.set_image(image)
        else:
            print("No image returned from CREATE_WORKPIECE_STEP_2")

        # Use CaptureDataHandler to load capture data into editor
        # This ensures we go through ContourEditorData instead of raw dicts
        from frontend.pl_ui.contour_editor.services.CaptureDataHandler import CaptureDataHandler

        editor_data = CaptureDataHandler.handle_capture_data(
            workpiece_manager=self.content_widget.contourEditor.workpiece_manager,
            capture_data=data,
            close_contour=True
        )

        if editor_data:
            CaptureDataHandler.print_capture_summary(editor_data)

        # Set callback for saving workpiece
        self.set_create_workpiece_for_on_submit_callback(self.via_camera_on_create_workpiece_submit)

    def via_camera_on_create_workpiece_submit(self, data):
        """
        Handle workpiece save via camera capture workflow.

        Uses SaveWorkpieceHandler to ensure consistent data flow through
        ContourEditorData and WorkpieceAdapter.
        """
        from frontend.pl_ui.contour_editor.services.SaveWorkpieceHandler import SaveWorkpieceHandler

        # Use the centralized handler
        success, message = SaveWorkpieceHandler.save_workpiece(
            workpiece_manager=self.content_widget.contourEditor.workpiece_manager,
            form_data=data,
            controller=self.controller
        )

        if success:
            print(f"✅ Workpiece saved successfully: {message}")
        else:
            print(f"❌ Failed to save workpiece: {message}")

        return success, message

    def set_image(self,image):
        """Set the image to be displayed in the contour editor"""
        try:
            self.content_widget.set_image(image)
            print("Set image in Contour Editor")
        except AttributeError:
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support set_image method")

    def init_contours(self,contours_by_layer):
        """Initialize contours in the contour editor"""
        try:
            print("content_widget type:", type(self.content_widget))
            self.content_widget.init_contours(contours_by_layer)
        except AttributeError:
            # print the actual error
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support init_contours method")

    def set_create_workpiece_for_on_submit_callback(self, callback):
        """Set the callback for when the create workpiece button is clicked"""
        try:
            print("Setting create workpiece callback")
            self.content_widget.set_create_workpiece_for_on_submit_callback(callback)
        except AttributeError:
            print("Contour Editor widget does not support set_create_workpiece_for_on_submit_callback method")

    def to_wp_data(self):
        return self.content_widget.contourEditor.manager.to_wp_data()

    def load_workpiece(self,workpiece):
        self.content_widget.contourEditor.load_workpiece(workpiece)