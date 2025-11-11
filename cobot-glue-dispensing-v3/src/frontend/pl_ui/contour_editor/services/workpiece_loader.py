"""
Workpiece loader service.

This module provides functionality to load Workpiece objects into the contour editor.
It uses the WorkpieceAdapter to convert from domain-specific Workpiece objects
to the domain-agnostic ContourEditorData format.
"""

from src.frontend.pl_ui.contour_editor.adapters.WorkpieceAdapter import WorkpieceAdapter
from src.frontend.pl_ui.contour_editor.EditorDataModel import ContourEditorData


def load_workpiece(workpiece):
    """
    Load a Workpiece object into the contour editor.

    This function uses the WorkpieceAdapter to convert the Workpiece
    into ContourEditorData, then converts it to the legacy format
    expected by the editor's init_contour method.

    Args:
        workpiece: Workpiece object to load

    Returns:
        tuple: (workpiece, contours_by_layer_dict)
            - workpiece: The original workpiece object (passed through)
            - contours_by_layer_dict: Dictionary in legacy format for init_contour
    """
    # Convert Workpiece to ContourEditorData
    editor_data = WorkpieceAdapter.from_workpiece(workpiece)

    # Print summary
    WorkpieceAdapter.print_summary(editor_data)

    # Convert to legacy format for compatibility with existing init_contour
    contours_by_layer = editor_data.to_legacy_format()

    return workpiece, contours_by_layer

