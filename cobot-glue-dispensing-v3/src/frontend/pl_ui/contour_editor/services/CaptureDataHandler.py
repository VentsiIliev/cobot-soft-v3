"""
CaptureDataHandler - Centralized handler for camera capture data.

This module provides a single place to handle data coming from camera capture,
converting it to ContourEditorData and loading it into the editor.

This ensures the capture flow uses the same data model as everything else.
"""

from typing import Dict, Any, Optional
import numpy as np

from frontend.pl_ui.contour_editor.EditorDataModel import ContourEditorData
from modules.shared.core.contour_editor.BezierSegmentManager import Layer, Segment
from PyQt6.QtCore import QPointF


class CaptureDataHandler:
    """
    Centralized handler for camera capture data.

    Converts raw capture data (numpy contours) into ContourEditorData
    and loads it into the editor using the proper data flow.
    """

    # Layer name for captured workpiece contour
    WORKPIECE_LAYER = "Workpiece"
    CONTOUR_LAYER = "Contour"
    FILL_LAYER = "Fill"

    @classmethod
    def handle_capture_data(
        cls,
        workpiece_manager,
        capture_data: Dict[str, Any],
        close_contour: bool = True
    ) -> Optional[ContourEditorData]:
        """
        Handle camera capture data and load it into the editor.

        This is the SINGLE entry point for all capture operations.

        Args:
            workpiece_manager: WorkpieceManager instance from the editor
            capture_data: Dictionary with keys:
                - "contours": numpy array or list of contours
                - "image": optional image data
                - "height": optional height measurement
            close_contour: Whether to close the contour

        Returns:
            ContourEditorData instance that was loaded, or None on failure
        """
        # Extract contours from capture data
        contours = capture_data.get("contours")
        if contours is None or (isinstance(contours, (list, np.ndarray)) and len(contours) == 0):
            print("⚠️ CaptureDataHandler: No contours in capture data")
            return None

        # Convert to ContourEditorData
        editor_data = cls.from_capture_data(
            contours=contours,
            metadata={
                "height": capture_data.get("height"),
                "source": "camera_capture"
            }
        )

        # Load into editor using the proper data model
        workpiece_manager.load_editor_data(editor_data, close_contour=close_contour)

        print(f"✅ CaptureDataHandler: Loaded capture data into editor")
        print(f"   - Layers: {editor_data.get_layer_names()}")
        print(f"   - Statistics: {editor_data.get_statistics()}")

        return editor_data

    @classmethod
    def from_capture_data(
        cls,
        contours: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContourEditorData:
        """
        Convert raw camera capture contours to ContourEditorData.

        Args:
            contours: Numpy array or list of contour points
            metadata: Optional metadata to attach to the contour

        Returns:
            ContourEditorData instance with the captured contour in "Workpiece" layer
        """
        editor_data = ContourEditorData()

        # Create Workpiece layer
        workpiece_layer = Layer(
            name=cls.WORKPIECE_LAYER,
            locked=False,
            visible=True
        )

        # Normalize contour data
        contour_array = cls._normalize_contour(contours)

        if contour_array is not None and len(contour_array) > 0:
            # Create segment from contour
            segment = Segment(layer=workpiece_layer, settings={})

            # Add points to segment
            for pt in contour_array:
                # Extract x, y from the normalized array
                if len(pt.shape) == 2 and pt.shape[0] == 1:
                    x, y = pt[0][0], pt[0][1]
                else:
                    x, y = pt[0], pt[1]
                segment.add_point(QPointF(float(x), float(y)))

            # Add metadata if provided
            if metadata:
                segment.metadata = metadata

            workpiece_layer.add_segment(segment)

        # Add layer to editor data
        editor_data.add_layer(workpiece_layer)

        # Create empty Contour and Fill layers
        editor_data.add_layer(Layer(name=cls.CONTOUR_LAYER, locked=False, visible=True))
        editor_data.add_layer(Layer(name=cls.FILL_LAYER, locked=False, visible=True))

        return editor_data

    @staticmethod
    def _normalize_contour(contours: Any) -> Optional[np.ndarray]:
        """
        Normalize contour data to standard (N, 1, 2) format.

        Args:
            contours: Various contour formats (numpy array, list, etc.)

        Returns:
            Normalized numpy array in (N, 1, 2) format or None
        """
        if contours is None:
            return None

        # Convert to numpy array
        if not isinstance(contours, np.ndarray):
            contours = np.array(contours, dtype=np.float32)

        # Handle different shapes
        if contours.ndim == 2 and contours.shape[1] == 2:
            # Shape (N, 2) -> (N, 1, 2)
            return contours.reshape(-1, 1, 2)
        elif contours.ndim == 3 and contours.shape[1] == 1 and contours.shape[2] == 2:
            # Already (N, 1, 2)
            return contours
        elif contours.ndim == 3 and contours.shape[0] == 1:
            # Shape (1, N, 2) -> (N, 1, 2)
            return contours.reshape(-1, 1, 2)
        else:
            # Try to reshape to (N, 1, 2)
            print(f"⚠️ CaptureDataHandler: Unusual contour shape {contours.shape}, attempting reshape")
            try:
                return contours.reshape(-1, 1, 2)
            except ValueError as e:
                print(f"❌ CaptureDataHandler: Cannot reshape contour: {e}")
                return None

    @classmethod
    def create_from_legacy_dict(
        cls,
        contours_by_layer: Dict[str, Any]
    ) -> ContourEditorData:
        """
        Convert legacy dictionary format to ContourEditorData.

        This supports the old capture format:
        {
            "Workpiece": [contour_array],
            "Contour": [],
            "Fill": []
        }

        Args:
            contours_by_layer: Legacy format dictionary

        Returns:
            ContourEditorData instance
        """
        return ContourEditorData.from_legacy_format(contours_by_layer)

    @classmethod
    def print_capture_summary(cls, editor_data: ContourEditorData):
        """
        Print a summary of captured data.

        Args:
            editor_data: ContourEditorData instance
        """
        print("\n=== Capture Data Summary ===")
        stats = editor_data.get_statistics()

        for layer_name in [cls.WORKPIECE_LAYER, cls.CONTOUR_LAYER, cls.FILL_LAYER]:
            layer = editor_data.get_layer(layer_name)
            if layer:
                layer_stats = stats["layers"].get(layer_name, {})
                print(f"{layer_name}: {layer_stats.get('segments', 0)} segments, "
                      f"{layer_stats.get('points', 0)} points")

        print("============================\n")