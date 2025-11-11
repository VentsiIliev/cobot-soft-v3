"""
WorkpieceAdapter - Adapter between Workpiece and ContourEditorData.

This module is the ONLY place that knows about Workpieces.
It converts between domain-specific Workpiece objects and the
domain-agnostic ContourEditorData model used by the contour editor.

This separation allows the contour editor to remain completely
independent of workpiece concepts.
"""

from typing import Dict, Any, Optional
import numpy as np

from src.frontend.pl_ui.contour_editor.EditorDataModel import ContourEditorData
from modules.shared.shared.contour_editor.BezierSegmentManager import Segment, Layer


class WorkpieceAdapter:
    """
    Adapter for converting between Workpiece objects and ContourEditorData.

    This is the ONLY class that should have knowledge of both Workpiece
    and ContourEditorData structures.
    """

    # Layer name constants
    LAYER_WORKPIECE = "Workpiece"
    LAYER_CONTOUR = "Contour"
    LAYER_FILL = "Fill"

    @classmethod
    def from_workpiece(cls, workpiece) -> ContourEditorData:
        """
        Convert a Workpiece object to ContourEditorData.

        Args:
            workpiece: Workpiece object with contour and spray pattern data

        Returns:
            ContourEditorData instance
        """
        # Extract main contour and settings
        print(f"from_workpiece: Extracting main contour and settings {workpiece}")
        main_contour = workpiece.get_main_contour()
        main_settings = workpiece.get_main_contour_settings()

        # Extract spray patterns
        spray_contours = workpiece.get_spray_pattern_contours()
        spray_fills = workpiece.get_spray_pattern_fills()

        # Build layer data structure
        layer_data = {
            cls.LAYER_WORKPIECE: [{"contour": main_contour, "settings": main_settings}],
            cls.LAYER_CONTOUR: spray_contours,
            cls.LAYER_FILL: spray_fills,
        }

        # Normalize and convert to ContourEditorData
        normalized_data = cls._normalize_layer_data(layer_data)
        return ContourEditorData.from_legacy_format(normalized_data)

    @classmethod
    def to_workpiece_data(cls, editor_data: ContourEditorData) -> Dict[str, Any]:
        """
        Convert ContourEditorData to workpiece-compatible data structure.

        This extracts the data needed to populate or update a Workpiece object,
        but does not create the Workpiece itself (as that requires many other
        domain-specific fields).

        Args:
            editor_data: ContourEditorData instance

        Returns:
            Dictionary with:
            - "main_contour": numpy array for the workpiece boundary
            - "main_settings": dict with main contour settings
            - "spray_pattern": dict with "Contour" and "Fill" entries
        """
        result = {
            "main_contour": None,
            "main_settings": {},
            "spray_pattern": {
                "Contour": [],
                "Fill": []
            }
        }

        # Extract main workpiece contour
        workpiece_layer = editor_data.get_layer(cls.LAYER_WORKPIECE)
        if workpiece_layer and len(workpiece_layer.segments) > 0:
            print(f"WorkpieceAdapter: Workpiece layer has {len(workpiece_layer.segments)} segments")
            # Use the first segment as the main contour
            main_segment = workpiece_layer.segments[0]
            print(f"WorkpieceAdapter: Main segment has {len(main_segment.points)} points")
            if len(main_segment.points) > 0:
                first_few_points = [(pt.x(), pt.y()) for pt in main_segment.points[:5]]
                print(f"WorkpieceAdapter: First few points: {first_few_points}")
            result["main_contour"] = cls._segment_to_contour_array(main_segment)
            result["main_settings"] = main_segment.settings.copy()
            if result["main_contour"] is not None:
                print(f"WorkpieceAdapter: Final main_contour shape: {result['main_contour'].shape}")
        else:
            print("WorkpieceAdapter: No workpiece layer or no segments found")

        # Extract spray pattern contours
        contour_layer = editor_data.get_layer(cls.LAYER_CONTOUR)
        if contour_layer:
            for segment in contour_layer.segments:
                contour_array = cls._segment_to_contour_array(segment)
                if contour_array is not None and len(contour_array) > 0:
                    result["spray_pattern"]["Contour"].append({
                        "contour": contour_array,
                        "settings": segment.settings.copy()
                    })

        # Extract spray pattern fills
        fill_layer = editor_data.get_layer(cls.LAYER_FILL)
        if fill_layer:
            for segment in fill_layer.segments:
                contour_array = cls._segment_to_contour_array(segment)
                if contour_array is not None and len(contour_array) > 0:
                    result["spray_pattern"]["Fill"].append({
                        "contour": contour_array,
                        "settings": segment.settings.copy()
                    })

        return result

    @staticmethod
    def _normalize_layer_data(layer_data: Dict[str, Any]) -> Dict[str, Dict[str, list]]:
        """
        Normalize layer data to the format expected by ContourEditorData.from_legacy_format().

        Converts:
        {
            "LayerName": [{"contour": np.array, "settings": dict}, ...]
        }

        To:
        {
            "LayerName": {
                "contours": [np.array, ...],
                "settings": [dict, ...]
            }
        }

        Args:
            layer_data: Raw layer data from workpiece

        Returns:
            Normalized layer data dictionary
        """
        normalized = {}

        for layer_name, entries in layer_data.items():
            contours = []
            settings_list = []

            if not isinstance(entries, list):
                entries = [entries]

            for item in entries:
                if not isinstance(item, dict):
                    print(f"⚠️ Unexpected entry type for {layer_name}: {type(item)}")
                    continue

                # Get contour and ensure it's a numpy array
                contour = np.array(item.get("contour", []), dtype=np.float32)

                # Normalize shape to (N, 1, 2)
                if contour.ndim == 2 and contour.shape[1] == 2:
                    contour = contour.reshape(-1, 1, 2)
                elif contour.ndim == 3 and contour.shape[1] == 1:
                    pass  # Already correct
                else:
                    print(f"⚠️ Unexpected contour shape in {layer_name}: {contour.shape}")
                    contour = contour.reshape(-1, 1, 2)

                contours.append(contour)
                settings_list.append(item.get("settings", {}))

            normalized[layer_name] = {
                "contours": contours,
                "settings": settings_list
            }

            print(f"✅ WorkpieceAdapter: Layer '{layer_name}' normalized with {len(contours)} contour(s)")

        return normalized

    @staticmethod
    def _segment_to_contour_array(segment: Segment) -> Optional[np.ndarray]:
        """
        Convert a Segment to a numpy contour array in (N, 1, 2) format.

        Args:
            segment: Segment object with points

        Returns:
            Numpy array in shape (N, 1, 2) or None if segment is empty
        """
        if len(segment.points) == 0:
            return None

        # Convert QPointF list to numpy array
        points = np.array(
            [[pt.x(), pt.y()] for pt in segment.points],
            dtype=np.float32
        ).reshape(-1, 1, 2)

        return points

    @classmethod
    def print_summary(cls, editor_data: ContourEditorData):
        """
        Print a summary of the editor data in workpiece terms.

        Args:
            editor_data: ContourEditorData instance
        """
        print("\n=== WorkpieceAdapter Summary ===")

        workpiece_layer = editor_data.get_layer(cls.LAYER_WORKPIECE)
        if workpiece_layer:
            print(f"Main workpiece contour: {len(workpiece_layer.segments)} segment(s)")
        else:
            print("Main workpiece contour: N/A")

        contour_layer = editor_data.get_layer(cls.LAYER_CONTOUR)
        if contour_layer:
            print(f"Spray pattern contours: {len(contour_layer.segments)} segment(s)")
        else:
            print("Spray pattern contours: N/A")

        fill_layer = editor_data.get_layer(cls.LAYER_FILL)
        if fill_layer:
            print(f"Spray pattern fills: {len(fill_layer.segments)} segment(s)")
        else:
            print("Spray pattern fills: N/A")

        stats = editor_data.get_statistics()
        print(f"Total segments: {stats['total_segments']}")
        print(f"Total points: {stats['total_points']}")
        print("================================\n")