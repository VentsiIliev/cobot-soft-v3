import os

from src.frontend.pl_ui.Endpoints import CREATE_WORKPIECE_TOPIC, SAVE_WORKPIECE


class CreateWorkpieceManager:


    def __init__(self, contour_editor,controller):
        self.contour_editor = contour_editor
        self.controller = controller

    def via_camera(self):
        print("Invoking via_camera in CreateWorkpieceManager")
        self.controller.handle(CREATE_WORKPIECE_TOPIC,
                               self.via_camera_success,
                               self.via_camera_failure)

    def via_dxf(self):
        pass

    def via_camera_on_create_workpiece_submit(self,data):
        wp_contours_data = self.contour_editor.to_wp_data()
        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }
        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour')
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill')

        from modules.shared.shared.workpiece.Workpiece import WorkpieceField
        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('Workpiece')
        data[WorkpieceField.CONTOUR_AREA] = "0"
        print("Workpiece data to save:", data)

        self.controller.handle(SAVE_WORKPIECE, data)

    def via_camera_success(self,frame,contours,data):
        print("Setting image in via_camera_success")
        
        # Check if contour_editor is still valid before using it
        try:
            if not hasattr(self, 'contour_editor') or self.contour_editor is None:
                print("ContourEditor is None - cannot process camera success")
                return
                
            # Try to access a property to check if the object is still valid
            _ = self.contour_editor.objectName()
            
            self.contour_editor.set_image(frame)
            contours_by_layer = {
                "Workpiece": [contours] if len(contours) > 0 else [],
                "Contour": [],
                "Fill": []
            }
            print("Contours by layer:", contours_by_layer)
            self.contour_editor.init_contours(contours_by_layer)
            self.contour_editor.set_create_workpiece_for_on_submit_callback(self.via_camera_on_create_workpiece_submit)
            
        except RuntimeError as e:
            if "deleted" in str(e).lower() or "wrapped c/c++" in str(e).lower():
                print("ContourEditor has been deleted - cannot process camera success")
                return
            else:
                raise  # Re-raise if it's a different RuntimeError

    def via_camera_failure(self, req, msg):
        print("via_camera_failure called with message:", msg)
        from src.frontend.pl_ui.ui.widgets.FeedbackProvider import FeedbackProvider
        FeedbackProvider.showMessage(msg)

