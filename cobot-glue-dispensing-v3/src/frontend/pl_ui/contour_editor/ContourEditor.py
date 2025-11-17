import os
import sys

import numpy as np
from PyQt6.QtCore import (
    pyqtSignal, QSize, QEventLoop, QPointF, Qt
)
from PyQt6.QtWidgets import QFrame, QWidget, QApplication, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout
from shapely import Polygon, LineString

from applications.glue_dispensing_application.workpiece.GlueWorkpiece import GlueWorkpiece
from frontend.pl_ui.contour_editor.services.CaptureDataHandler import CaptureDataHandler
from frontend.pl_ui.contour_editor.services.SaveWorkpieceHandler import SaveWorkpieceHandler
from frontend.pl_ui.contour_editor.contourEditorDecorators.ContourEditorWithBottomToolBar import ContourEditorWithBottomToolBar

from frontend.pl_ui.contour_editor.widgets.LayerAndValueInputDialog import LayerAndValueInputDialog
from frontend.pl_ui.contour_editor.widgets.PointManagerWidget import PointManagerWidget
from frontend.pl_ui.contour_editor.widgets.SlidingPanel import SlidingPanel
from frontend.pl_ui.contour_editor.widgets.TopbarWidget import TopBarWidget
from frontend.pl_ui.contour_editor.utils.utils import shrink_contour_points, generate_spray_pattern
from frontend.pl_ui.ui.widgets.CreateWorkpieceForm import CreateWorkpieceForm
from frontend.pl_ui.ui.widgets.CustomFeedbackDialog import CustomFeedbackDialog, DialogType
from modules.shared.core.workpiece.Workpiece import WorkpieceField

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

class MainApplicationFrame(QFrame):
    capture_requested = pyqtSignal()
    update_camera_feed_requested = pyqtSignal()
    save_workpiece_requested = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # State management
        self.current_view = "point_manager"  # "point_manager" or "create_workpiece"
        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Bezier editor on the left
        # from pl_ui.contour_editor.mockWorkpieceData import mock_workpiece_data
        # wp = Workpiece.fromDict(mock_workpiece_data)
        # wp = None
        # self.contourEditor = ContourEditorWithRulers(None, image_path="imageDebug.png",workpiece=None)
        self.contourEditor = ContourEditorWithBottomToolBar(None, image_path="imageDebug.png", workpiece=None)
        self.contourEditor.update_camera_feed_requested.connect(self.update_camera_feed_requested.emit)

        # Top bar widget
        self.topbar = TopBarWidget(self.contourEditor, None)
        self.topbar.save_requested.connect(self.on_first_save_clicked)
        self.topbar.capture_requested.connect(self.capture_requested.emit)
        self.topbar.start_requested.connect(self.onStart)
        self.topbar.zigzag_requested.connect(self.generateLineGridPattern)
        self.topbar.offset_requested.connect(self.shrink)
        self.topbar.undo_requested.connect(self.on_undo)
        self.topbar.redo_requested.connect(self.on_redo)
        self.topbar.preview_requested.connect(self.show_preview)
        self.topbar.multi_select_mode_requested.connect(self.on_multi_select_mode_requested)
        self.topbar.remove_points_requested.connect(self.contourEditor.remove_selected_points)
        self.topbar.settings_requested.connect(self.contourEditor.open_settings_dialog)
        self.topbar.tools_requested.connect(self.contourEditor.show_tools_menu)
        mainLayout.addWidget(self.topbar)

        # Horizontal layout for the main content
        horizontal_widget = QWidget()
        horizontalLayout = QHBoxLayout(horizontal_widget)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)

        horizontalLayout.addWidget(self.contourEditor, stretch=1)

        # Create the right panel widgets
        self.pointManagerWidget = PointManagerWidget(self.contourEditor, self.parent)
        self.pointManagerWidget.point_selected_signal.connect(lambda point_info:self.contourEditor.selection_manager.set_single_selection_from_dict(point_info))
        self.topbar.point_manager = self.pointManagerWidget
        self.contourEditor.point_manager_widget = self.pointManagerWidget
        self.pointManagerWidget.setFixedWidth(400)

        # Wrap point manager in a sliding panel
        self.sliding_panel = SlidingPanel(self.pointManagerWidget, parent=horizontal_widget)
        #
        # self.createWorkpieceForm = CreateWorkpieceForm(parent=self)
        # self.createWorkpieceForm.setFixedWidth(400)
        self.createWorkpieceForm = None # will be created on demand

        # Add sliding panel to layout (no stretch - it will use its size hints)
        horizontalLayout.addWidget(self.sliding_panel, stretch=0)

        mainLayout.addWidget(horizontal_widget)

    def on_save_workpiece_requested(self, data):
        """
        Handle workpiece save request.

        Uses SaveWorkpieceHandler to extract and merge contour data with form data.
        This method prepares the data and emits it for the controller to handle.
        """
        print(f"on_save_workpiece_requested called with data: {data}")

        try:

            # Prepare complete workpiece data using the handler
            complete_data = SaveWorkpieceHandler.prepare_workpiece_data(
                workpiece_manager=self.contourEditor.workpiece_manager,
                form_data=data
            )

            print("Workpiece data prepared for save:", complete_data.keys())
            self.save_workpiece_requested.emit(complete_data)

        except Exception as e:
            print(f"❌ Error preparing workpiece data: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to prepare workpiece data: {e}")

    def on_capture_requested(self):
        # clear the point manager and contour editor before capturing
        self.pointManagerWidget.refresh_points()
        self.contourEditor.reset_editor()

    def show_preview(self):
        self.contourEditor.save_robot_path_to_txt("preview.txt", samples_per_segment=5)
        self.contourEditor.plot_robot_path("preview.txt")

    def reset_zoom(self):
        if not self.contourEditor:
            raise ValueError("Contour editor is not set.")


        self.contourEditor.editor_with_rulers.editor.viewport_controller.reset_zoom()



    def on_redo(self):
        print(f"on redo pressed")
        if not self.contourEditor:
            print("Error", "Contour editor is not set.")
            # QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return

        self.contourEditor.manager.redo()
        self.pointManagerWidget.refresh_points()
        # Update both the inner editor and the wrapper
        self.contourEditor.editor.update()
        self.contourEditor.update()
        # Force immediate repaint
        self.contourEditor.editor.repaint()
        self.contourEditor.repaint()
        # Process pending events to ensure repaint completes
        QApplication.processEvents()


    def on_undo(self):
        if not self.contourEditor:
            print("Error", "Contour editor is not set.")
            # QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return

        self.contourEditor.manager.undo()
        self.pointManagerWidget.refresh_points()
        # Update both the inner editor and the wrapper
        self.contourEditor.editor.update()
        self.contourEditor.update()
        # Force immediate repaint
        self.contourEditor.editor.repaint()
        self.contourEditor.repaint()
        # Process pending events to ensure repaint completes
        QApplication.processEvents()


    def on_multi_select_mode_requested(self):
        """Handle multi-select mode toggle request from toolbar"""
        if not self.contourEditor:
            print("Error: Contour editor is not set.")
            return

        # Toggle multi-select mode in the editor
        is_active = self.contourEditor.toggle_multi_select_mode()

        # Update toolbar UI to reflect the new state
        self.topbar.update_multi_select_ui(is_active)



    def set_create_workpiece_for_on_submit_callback(self, callback):
        """
        Set the callback for when the create workpiece button is clicked.
        This allows the main application to handle the creation of a workpiece.
        """
        self.createWorkpieceForm.onSubmitCallBack = callback
        print("Set create workpiece callback in main application frame.")

    def shrink(self):

        external_segments = [s for s in self.contourEditor.manager.get_segments() if
                             getattr(s.layer, "name", "") == "Workpiece"]
        if not external_segments:
            dialog = CustomFeedbackDialog(
                parent=self,
                title="No Workpiece",
                message="No Workpiece contour found.",
                info_text="No Workpiece contour found.",
                dialog_type=DialogType.INFO,
                ok_text="OK",
                cancel_text=None
            )
            dialog.exec()
            return

        # Combined dialog for layer selection and shrink value input
        shrink_dialog = LayerAndValueInputDialog(
            dialog_title="Shrink Contour",
            layer_label="Select layer for shrunk contour:",
            input_labels=["Enter shrink value (mm):"],
            input_defaults=[5],
            input_ranges=[(1, 50)]
        )

        shrink_dialog.show()  # Show without blocking the rest of the app

        # Use an event loop to wait until the user has pressed "OK" or "Cancel"
        loop = QEventLoop()
        shrink_dialog.finished.connect(loop.quit)
        loop.exec()

        if shrink_dialog.result() != QDialog.DialogCode.Accepted:
            print("Shrink operation canceled.")
            return

        # Use the dialog's existing get_values() and unpack safely
        vals = shrink_dialog.get_values()
        if not vals or len(vals) < 2:
            print("Invalid dialog return values.")
            return

        selected_layer = vals[0]
        try:
            shrink_amount = float(vals[1])
        except Exception:
            print("Invalid shrink amount provided.")
            return

        # Validate shrink amount
        if shrink_amount <= 0:
            print("Shrink amount must be positive.")
            return

        print(f"Shrinking contour by: {shrink_amount} to layer: {selected_layer}")

        contour = external_segments[0]
        contour_points = np.array([(pt.x(), pt.y()) for pt in contour.points])
        if contour_points.size == 0:
            print("Workpiece contour has no points.")
            return
        if contour_points.shape[0] < 3:
            print("Contour has fewer than 3 points — can't shrink properly.")
            return

        new_contour_points = shrink_contour_points(contour_points, shrink_amount)
        if new_contour_points is None or len(new_contour_points) < 2:
            print("Shrink amount too large — polygon disappeared or invalid result!")
            return

        for i in range(len(new_contour_points) - 1):
            p1 = new_contour_points[i]
            p2 = new_contour_points[i + 1]
            qpoints = [QPointF(float(p1[0]), float(p1[1])), QPointF(float(p2[0]), float(p2[1]))]
            segment = self.contourEditor.manager.create_segment(qpoints, layer_name=selected_layer)
            self.contourEditor.manager.segments.append(segment)

        self.contourEditor.update()
        self.pointManagerWidget.refresh_points()
        print(f"Added shrunk contour inward by {shrink_amount} units as new segments in {selected_layer} layer.")

    def generateLineGridPattern(self):
        """
        Generate zig-zag lines aligned to the Workpiece contour using minimum area bounding box orientation.
        """

        external_segments = [s for s in self.contourEditor.manager.get_segments() if
                             getattr(s.layer, "name", "") == "Workpiece"]
        if not external_segments:
            dialog = CustomFeedbackDialog(
                parent=self,
                title="No Workpiece",
                message="No Workpiece contour found.",
                info_text="No Workpiece contour found.",
                dialog_type=DialogType.INFO,
                ok_text="OK",
                cancel_text=None
            )
            dialog.exec()
            return

        # Create and show the dialog
        dialog = LayerAndValueInputDialog(dialog_title="Spray Pattern Settings",
                                          layer_label="Select layer type:",
                                          input_labels=["Line grid spacing (mm):", "Shrink offset (mm):"],
                                          input_defaults=[20, 0.0],
                                          input_ranges=[(1, 1000), (0.0, 50.0)], )
        dialog.show()  # Show without blocking the rest of the application

        # Use an event loop to wait for the user's input (OK or Cancel)
        loop = QEventLoop()
        dialog.finished.connect(loop.quit)  # Once finished, quit the event loop
        loop.exec()  # Block until the user closes the dialog

        # If the dialog was canceled, stop the function
        if dialog.result() != QDialog.DialogCode.Accepted:
            print("Zig-zag pattern generation cancelled by user.")
            return

        # Get the selected layer, spacing, and shrink offset values
        selected_layer, spacing, shrink_offset = dialog.get_values()

        # Clear all segments in the selected layer
        self.contourEditor.manager.segments = [s for s in self.contourEditor.manager.get_segments() if
                                               getattr(s.layer, "name", "") != selected_layer]
        self.contourEditor.update()

        # If shrink requested, compute a shrunk contour first
        if shrink_offset < 1:
            shrink_offset = 1
        if shrink_offset > 0:

            contour = external_segments[0]
            contour_points = np.array([(pt.x(), pt.y()) for pt in contour.points])
            if contour_points.size == 0:
                print("Workpiece contour has no points.")
                return
            if contour_points.shape[0] < 3:
                print("Contour has fewer than 3 points — can't shrink properly.")
                return

            new_contour_points = shrink_contour_points(contour_points, shrink_offset)
            if new_contour_points is None or len(new_contour_points) < 2:
                print("Shrink amount too large — polygon disappeared or invalid result!")
                return
            contour_points = new_contour_points.astype(np.float32)
        else:
            # Get Workpiece contour
            external_segments = [s for s in self.contourEditor.manager.get_segments() if
                                 getattr(s.layer, "name", "") == "Workpiece"]
            if not external_segments:
                print("No Workpiece contour found.")
                return

            contour = external_segments[0]
            contour_points = np.array([(pt.x(), pt.y()) for pt in contour.points])
            if contour_points.size == 0:
                print("Workpiece contour has no points.")
                return

            if contour_points.shape[0] < 3:
                print("Contour has fewer than 3 points — can't compute minAreaRect.")
                return

            contour_points = contour_points.astype(np.float32)

        zigzag_segments = generate_spray_pattern(contour_points, spacing)
        contour_poly = Polygon(np.array(contour_points).squeeze())

        if selected_layer == "Fill":
            all_qpoints = []
            reverse = False
            prev_point = None

            for segment_coords in zigzag_segments:
                if segment_coords is None:
                    continue

                pts = segment_coords if not reverse else segment_coords[::-1]

                # If there is a previous endpoint, check that the connecting line stays inside
                if prev_point is not None:
                    connector = LineString([prev_point, pts[0]])

                    # ⚙️ Only connect if fully inside the contour
                    # if contour_poly.covers(connector):
                    print(f"Inside connector detected, connecting lines.")
                    # inside: connect directly
                    all_qpoints.append(QPointF(*pts[0]))
                    # else:
                    #     print(f"Outside connector detected, breaking line.")
                    #     # outside: finish the current segment and start a new one
                    #     if all_qpoints:
                    #         segment = self.contourEditor.manager.create_segment(all_qpoints, layer_name=selected_layer)
                    #         self.contourEditor.manager.segments.append(segment)
                    #     all_qpoints = []  # start a fresh path (pen up)

                # Add the actual sweep line points
                all_qpoints.extend(QPointF(x, y) for x, y in pts)

                prev_point = pts[-1]
                reverse = not reverse

            # Add the last accumulated polyline
            if all_qpoints:
                segment = self.contourEditor.manager.create_segment(all_qpoints, layer_name=selected_layer)
                self.contourEditor.manager.segments.append(segment)

        else:
            # For Contour layer (or others): Create individual segments with alternating directions
            reverse = False
            for segment_coords in zigzag_segments:

                if segment_coords is None or len(segment_coords) < 2:
                    continue

                # Reverse every other line to alternate the pattern
                pts = segment_coords if not reverse else segment_coords[::-1]
                qpoints = [QPointF(x, y) for x, y in pts]
                segment = self.contourEditor.manager.create_segment(qpoints, layer_name=selected_layer)
                self.contourEditor.manager.segments.append(segment)
                reverse = not reverse

        # Final UI update
        self.contourEditor.update()
        self.pointManagerWidget.refresh_points()
        print("Generated zig-zag grid aligned to Workpiece contour.")

    def on_first_save_clicked(self):
        """Handle the first save button click - switch from point manager to create workpiece form"""
        if self.current_view == "point_manager":

            if self.createWorkpieceForm is None:
                self.createWorkpieceForm = CreateWorkpieceForm(parent=self)
                self.createWorkpieceForm.setFixedWidth(400)
                self.createWorkpieceForm.data_submitted.connect(lambda data: self.save_workpiece_requested.emit(data))

            if self.contourEditor.workpiece is not None:
                # prefill form with existing workpiece data


                self.createWorkpieceForm.clear_form()
                self.createWorkpieceForm.prefill_form(self.contourEditor.workpiece)
            else:
                # clear the form in case it has old data
                self.createWorkpieceForm.clear_form()
                print("No workpiece data to prefill the form.")
            self.sliding_panel.replace_content_widget(self.createWorkpieceForm)
            # Update the save button callback to handle workpiece saving
            self.topbar.save_requested.disconnect()
            self.topbar.save_requested.connect(self.on_workpiece_save_clicked)
            # self.topbar.set_save_button_callback(self.on_workpiece_save_clicked)
            self.current_view = "create_workpiece"

            print("Switched to Create Workpiece form")

        # if the sliding panel is hidden, show it
        if not self.sliding_panel.is_visible:
            self.sliding_panel.toggle_panel()

    def onStart(self):
        """
        Quick start function for testing - creates mock workpiece and executes.

        Uses SaveWorkpieceHandler to extract contour data consistently.
        """


        # Mock form data
        mock_data = {
            WorkpieceField.WORKPIECE_ID.value: "WP123",
            WorkpieceField.NAME.value: "Test Workpiece",
            WorkpieceField.DESCRIPTION.value: "Sample description",
            WorkpieceField.OFFSET.value: "10,20,30",
            WorkpieceField.HEIGHT.value: "50",
            WorkpieceField.GLUE_QTY.value: "100",
            WorkpieceField.SPRAY_WIDTH.value: "5",
            WorkpieceField.TOOL_ID.value: "0",
            WorkpieceField.GRIPPER_ID.value: "0",
            WorkpieceField.GLUE_TYPE.value: "Type A",
            WorkpieceField.PROGRAM.value: "Trace",
            WorkpieceField.MATERIAL.value: "Material1",
            WorkpieceField.CONTOUR_AREA.value: "1000",
        }

        # Add pickup point if set
        if self.contourEditor.pickup_point is not None:
            pickup_point_str = f"{self.contourEditor.pickup_point.x():.2f},{self.contourEditor.pickup_point.y():.2f}"
            mock_data["pickup_point"] = pickup_point_str
            print(f"Pickup point included: {pickup_point_str}")
        else:
            print("No pickup point set")

        # Use SaveWorkpieceHandler to extract and merge contour data
        try:
            complete_data = SaveWorkpieceHandler.prepare_workpiece_data(
                workpiece_manager=self.contourEditor.workpiece_manager,
                form_data=mock_data
            )
        except Exception as e:
            print(f"❌ Error preparing workpiece data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to prepare workpiece data: {e}")
            return

        # Validate spray pattern data
        spray_pattern = complete_data.get(WorkpieceField.SPRAY_PATTERN.value, {})
        contour_data = spray_pattern.get("Contour", [])
        fill_data = spray_pattern.get("Fill", [])

        def has_valid_contours(contour_list):
            """Check if contour list has valid contour data"""
            if not contour_list or len(contour_list) == 0:
                return False
            for item in contour_list:
                if isinstance(item, dict) and 'contour' in item:
                    contour = item['contour']
                    if contour.size > 0 and len(contour) > 0:
                        return True
            return False

        if not has_valid_contours(contour_data) and not has_valid_contours(fill_data):
            QMessageBox.warning(self, "No Spray Pattern", "No valid contour or fill patterns found!")
            return

        # Create and execute workpiece
        wp = GlueWorkpiece.fromDict(complete_data)
        print("Workpiece created:", wp)
        print("Start button pressed: CONTOUR EDITOR ")
        self.parent.controller.handleExecuteFromGallery(wp)

    def on_workpiece_save_clicked(self):
        """Handle the second save button click - save the workpiece"""
        # Pass pickup point data to the form before submitting
        if self.contourEditor.pickup_point is not None:
            pickup_point_str = f"{self.contourEditor.pickup_point.x():.2f},{self.contourEditor.pickup_point.y():.2f}"
            # Store pickup point in the form's data
            self.createWorkpieceForm.pickup_point = pickup_point_str
            print(f"Pickup point passed to form: {pickup_point_str}")
        else:
            # Clear pickup point if none is set
            self.createWorkpieceForm.pickup_point = None
            print("No pickup point set, clearing form attribute")

        # Call the workpiece form's submit method and show confirmation
        try:
            self.createWorkpieceForm.onSubmit()
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Failed to save workpiece: {e}")
            return

        QMessageBox.information(self, "Saved", "Workpiece saved successfully.")
        print("Workpiece saved!")

        # Optionally, you could reset back to point manager or keep the form
        # For now, we'll keep the create workpiece form visible
        # Switch back to point manager view
        try:
            # Hide the create workpiece form and show point manager
            self.contourEditor.camera_feed_update_timer.start()
            self.contourEditor.reset_editor()
            self.pointManagerWidget.refresh_points()

            self.sliding_panel.replace_content_widget(self.pointManagerWidget)

            # Restore the topbar save button callback to the first-save behavior
            try:
                self.topbar.save_requested.disconnect()
            except Exception:
                # ignore if not connected
                pass
            self.topbar.save_requested.connect(self.on_first_save_clicked)

            self.current_view = "point_manager"
            print("Switched back to point manager view")
        except Exception as e:
            QMessageBox.warning(self, "View Switch Failed", f"Saved but failed to switch view: {e}")
            import traceback
            traceback.print_exc()
            print(f"Error switching to point manager: {e}")

    def set_image(self, image):
        self.contourEditor.set_image(image)

    def init_contours(self, contours):
        """
        Initialize contours using legacy format.

        DEPRECATED: Use load_capture_data() for new code.
        """
        print("in contour editor.py")
        self.contourEditor.initContour(contours)

    def load_capture_data(self, capture_data, close_contour=True):
        """
        Load camera capture data into the editor using ContourEditorData.

        This is the preferred method for loading capture data as it uses
        the centralized CaptureDataHandler.

        Args:
            capture_data: Dictionary with keys:
                - "contours": numpy array or list of contours
                - "image": optional image data
                - "height": optional height measurement
            close_contour: Whether to close the contour

        Returns:
            ContourEditorData instance that was loaded
        """

        return CaptureDataHandler.handle_capture_data(
            workpiece_manager=self.contourEditor.workpiece_manager,
            capture_data=capture_data,
            close_contour=close_contour
        )

    def resizeEvent(self, event):
        """Resize content and side menu dynamically."""
        super().resizeEvent(event)
        new_width = self.width()

        # Adjust icon sizes of the sidebar buttons
        icon_size = int(new_width * 0.05)  # 5% of the new window width
        for button in self.topbar.buttons:
            button.setIconSize(QSize(icon_size, icon_size))

        if self.createWorkpieceForm is not None:

            if hasattr(self.createWorkpieceForm, 'buttons'):
                for button in self.createWorkpieceForm.buttons:
                    button.setIconSize(QSize(icon_size, icon_size))

            # Resize the icons in the labels
            if hasattr(self.createWorkpieceForm, 'icon_widgets'):
                for label, original_pixmap in self.createWorkpieceForm.icon_widgets:
                    scaled_pixmap = original_pixmap.scaled(
                        int(icon_size / 2), int(icon_size / 2),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    label.setPixmap(scaled_pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load and apply stylesheet
    # stylesheetPath = "D:/GitHub/Cobot-Glue-Nozzle/pl_gui/styles.qss"
    # file = QFile(stylesheetPath)
    # if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
    #     stream = QTextStream(file)
    #     stylesheet = stream.readAll()
    #     file.close()
    #     app.setStyleSheet(stylesheet)

    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    app_frame = MainApplicationFrame()
    layout.addWidget(app_frame)
    main_window.setGeometry(100, 100, 1600, 800)
    main_window.setWindowTitle("Glue Dispensing Application")
    main_window.show()
    sys.exit(app.exec())
