"""
SaveWorkpieceHandler - Centralized handler for saving workpieces.

This module provides a single place to handle workpiece save operations,
ensuring consistency with the ContourEditorData model and eliminating
code duplication across the application.
"""

from typing import Dict, Any, Optional
from src.frontend.pl_ui.contour_editor.adapters.WorkpieceAdapter import WorkpieceAdapter
from src.frontend.pl_ui.contour_editor.EditorDataModel import ContourEditorData


class SaveWorkpieceHandler:
    """
    Centralized handler for workpiece save operations.

    This ensures all save operations go through the proper ContourEditorData
    pipeline instead of directly accessing BezierSegmentManager.
    """

    @classmethod
    def save_workpiece(
        cls,
        workpiece_manager,
        form_data: Dict[str, Any],
        controller,
        endpoint: str = "SAVE_WORKPIECE"
    ) -> tuple[bool, str]:
        """
        Save a workpiece using the proper data model.

        This is the SINGLE entry point for all workpiece save operations.

        Args:
            workpiece_manager: WorkpieceManager instance from the editor
            form_data: Dictionary with form fields (name, description, etc.)
            controller: Controller instance to handle the save request
            endpoint: Endpoint name to use (default: "SAVE_WORKPIECE")

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Step 1: Validate required fields before processing
            validation_result, validation_errors = cls.validate_form_data(form_data)
            if not validation_result:
                error_message = "Validation failed:\n" + "\n".join(validation_errors)
                print(f"❌ {error_message}")
                from pl_ui.ui.widgets.CustomFeedbackDialog import CustomFeedbackDialog,DialogType
                dialog = CustomFeedbackDialog(
                    title="Validation Error",
                    message=error_message,
                    dialog_type=DialogType.ERROR
                )
                dialog.exec()
                return False, error_message

            # Step 2: Export editor data using the new model
            print("SaveWorkpieceHandler: Exporting editor data...")
            editor_data = workpiece_manager.export_editor_data()

            # Step 3: Convert to workpiece format using adapter
            print("SaveWorkpieceHandler: Converting to workpiece format...")
            workpiece_data = WorkpieceAdapter.to_workpiece_data(editor_data)

            # Step 4: Merge contour data with form data
            complete_data = cls._merge_data(form_data, workpiece_data)

            # Step 5: Print summary before saving
            cls.print_save_summary(editor_data, complete_data)

            # Step 6: Save via controller
            print("SaveWorkpieceHandler: Sending to controller...")
            # from pl_ui.Endpoints import SAVE_WORKPIECE
            # result = controller.handle(SAVE_WORKPIECE, complete_data)
            result = controller.saveWorkpiece(complete_data)
            if result:
                if isinstance(result, tuple):
                    success, message = result
                    return success, message
                return True, "Workpiece saved successfully"
            else:
                return False, "No response from controller"

        except Exception as e:
            error_msg = f"SaveWorkpieceHandler error: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg

    @classmethod
    def prepare_workpiece_data(
        cls,
        workpiece_manager,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare workpiece data for saving without actually saving.

        Useful for preview or validation before save.

        Args:
            workpiece_manager: WorkpieceManager instance
            form_data: Form data dictionary

        Returns:
            Complete workpiece data dictionary ready for saving
        """
        editor_data = workpiece_manager.export_editor_data()
        workpiece_data = WorkpieceAdapter.to_workpiece_data(editor_data)
        return cls._merge_data(form_data, workpiece_data)

    @staticmethod
    def _merge_data(
        form_data: Dict[str, Any],
        workpiece_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge form data with extracted workpiece contour data.

        Args:
            form_data: Data from CreateWorkpieceForm
            workpiece_data: Data from WorkpieceAdapter.to_workpiece_data()

        Returns:
            Merged dictionary with all required fields
        """
        from modules.shared.shared.workpiece.Workpiece import WorkpieceField

        # Start with form data
        complete_data = form_data.copy()

        # Add workpiece contour data with settings
        if workpiece_data.get("main_contour") is not None:
            # Combine contour points and settings into expected dict format
            contour_data = {
                "contour": workpiece_data["main_contour"],
                "settings": workpiece_data.get("main_settings", {})
            }
            complete_data[WorkpieceField.CONTOUR.value] = contour_data

        # Add spray pattern
        if workpiece_data.get("spray_pattern"):
            complete_data[WorkpieceField.SPRAY_PATTERN.value] = workpiece_data["spray_pattern"]

        # Ensure contour_area is set (default to "0" if not present)
        if WorkpieceField.CONTOUR_AREA.value not in complete_data:
            complete_data[WorkpieceField.CONTOUR_AREA.value] = "0"

        return complete_data

    @classmethod
    def extract_contours_only(
        cls,
        workpiece_manager
    ) -> Dict[str, Any]:
        """
        Extract only contour data without form data.

        Useful for operations that only need geometric data.

        Args:
            workpiece_manager: WorkpieceManager instance

        Returns:
            Dictionary with contour data
        """
        editor_data = workpiece_manager.export_editor_data()
        return WorkpieceAdapter.to_workpiece_data(editor_data)

    @classmethod
    def print_save_summary(
        cls,
        editor_data: ContourEditorData,
        complete_data: Dict[str, Any]
    ):
        """
        Print a summary of what will be saved.

        Args:
            editor_data: ContourEditorData instance
            complete_data: Complete data dictionary that will be saved
        """
        print("\n=== Save Workpiece Summary ===")

        # Print editor statistics
        stats = editor_data.get_statistics()
        print(f"Editor Data:")
        print(f"  - Total layers: {stats['total_layers']}")
        print(f"  - Total segments: {stats['total_segments']}")
        print(f"  - Total points: {stats['total_points']}")

        for layer_name, layer_stats in stats['layers'].items():
            print(f"  - {layer_name}: {layer_stats['segments']} segments, {layer_stats['points']} points")

        # Print workpiece metadata
        print(f"\nWorkpiece Metadata:")
        from modules.shared.shared.workpiece.Workpiece import WorkpieceField

        metadata_fields = [
            WorkpieceField.WORKPIECE_ID,
            WorkpieceField.NAME,
            WorkpieceField.DESCRIPTION,
            WorkpieceField.HEIGHT,
        ]

        for field in metadata_fields:
            value = complete_data.get(field.value, "N/A")
            print(f"  - {field.name}: {value}")

        # Print spray pattern info
        spray_pattern = complete_data.get(WorkpieceField.SPRAY_PATTERN.value, {})
        if spray_pattern:
            contour_count = len(spray_pattern.get("Contour", []))
            fill_count = len(spray_pattern.get("Fill", []))
            print(f"\nSpray Pattern:")
            print(f"  - Contour patterns: {contour_count}")
            print(f"  - Fill patterns: {fill_count}")

        print("==============================\n")

    @classmethod
    def validate_before_save(
        cls,
        editor_data: ContourEditorData,
        form_data: Dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate data before saving.

        Args:
            editor_data: ContourEditorData instance
            form_data: Form data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate editor data
        is_valid, editor_errors = editor_data.validate()
        if not is_valid:
            errors.extend([f"Editor: {err}" for err in editor_errors])

        # Validate required form fields
        from modules.shared.shared.workpiece.Workpiece import WorkpieceField

        required_fields = [
            WorkpieceField.WORKPIECE_ID,
            WorkpieceField.NAME,
        ]

        for field in required_fields:
            if not form_data.get(field.value):
                errors.append(f"Missing required field: {field.name}")

        # Check if workpiece has contour data
        workpiece_layer = editor_data.get_layer("Workpiece")
        if not workpiece_layer or len(workpiece_layer.segments) == 0:
            errors.append("No workpiece contour data found")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_form_data(cls, form_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate form data before saving.

        Args:
            form_data: Form data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        from modules.shared.shared.workpiece.Workpiece import WorkpieceField

        # Validate required fields
        required_fields = {
            WorkpieceField.WORKPIECE_ID: "Workpiece ID",
            WorkpieceField.HEIGHT: "Height"
        }

        for field, field_name in required_fields.items():
            value = form_data.get(field.value, "").strip()
            if not value:
                errors.append(f"{field_name} is mandatory and cannot be empty")

        # Validate height is a valid number
        height_value = form_data.get(WorkpieceField.HEIGHT.value, "").strip()
        if height_value:  # Only validate if not empty (already checked above)
            try:
                height_float = float(height_value)
                if height_float <= 0:
                    errors.append("Height must be a positive number greater than 0")
            except ValueError:
                errors.append("Height must be a valid number")

        return (len(errors) == 0, errors)