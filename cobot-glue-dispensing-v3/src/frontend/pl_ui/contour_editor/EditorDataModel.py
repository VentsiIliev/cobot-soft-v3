"""
EditorDataModel - Domain-agnostic data model for the Contour Editor.

This module provides a structured, domain-independent data representation
for the contour editor. It has NO knowledge of workpieces, robots, or any
domain-specific concepts.

The model wraps the existing Segment and Layer classes from BezierSegmentManager
and provides serialization/deserialization capabilities for import/export.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from PyQt6.QtCore import QPointF
from copy import deepcopy

from modules.shared.core.contour_editor.BezierSegmentManager import Segment, Layer


class ContourEditorData:
    """
    Top-level container for all contour editor data.

    This class provides a structured, domain-independent representation of
    contour data organized by layers. It supports import/export and has
    NO knowledge of workpieces or any domain-specific concepts.

    Uses the existing Segment and Layer classes from BezierSegmentManager.
    """

    def __init__(self, layers: Optional[Dict[str, Layer]] = None):
        """
        Initialize editor data.

        Args:
            layers: Dictionary mapping layer names to Layer objects
        """
        self.layers: Dict[str, Layer] = layers or {}

    def add_layer(self, layer: Layer):
        """
        Add or replace a layer.

        Args:
            layer: Layer to add
        """
        self.layers[layer.name] = layer

    def get_layer(self, name: str) -> Optional[Layer]:
        """
        Get a layer by name.

        Args:
            name: Layer name

        Returns:
            Layer object or None if not found
        """
        return self.layers.get(name)

    def remove_layer(self, name: str) -> bool:
        """
        Remove a layer by name.

        Args:
            name: Layer name

        Returns:
            True if layer was removed, False if not found
        """
        if name in self.layers:
            del self.layers[name]
            return True
        return False

    def get_layer_names(self) -> List[str]:
        """
        Get all layer names.

        Returns:
            List of layer names
        """
        return list(self.layers.keys())

    def get_all_segments(self) -> List[Segment]:
        """
        Get all segments from all layers.

        Returns:
            List of all Segment objects
        """
        segments = []
        for layer in self.layers.values():
            segments.extend(layer.segments)
        return segments

    def clear(self):
        """Clear all layers."""
        self.layers = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for serialization.

        Returns:
            Dictionary mapping layer names to layer data:
            {
                "layer_name": {
                    "locked": bool,
                    "visible": bool,
                    "segments": [
                        {
                            "points": [[x, y], ...],
                            "controls": [[x, y], None, ...],
                            "visible": bool,
                            "settings": {...}
                        },
                        ...
                    ]
                }
            }
        """
        result = {}
        for name, layer in self.layers.items():
            result[name] = {
                "locked": layer.locked,
                "visible": layer.visible,
                "segments": []
            }

            for segment in layer.segments:
                segment_data = {
                    "points": [[pt.x(), pt.y()] for pt in segment.points],
                    "controls": [
                        [ctrl.x(), ctrl.y()] if ctrl is not None else None
                        for ctrl in segment.controls
                    ],
                    "visible": segment.visible,
                    "settings": deepcopy(segment.settings)
                }
                result[name]["segments"].append(segment_data)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContourEditorData':
        """
        Create ContourEditorData from dictionary.

        Args:
            data: Dictionary in the format produced by to_dict()

        Returns:
            New ContourEditorData instance
        """
        editor_data = cls()

        for layer_name, layer_data in data.items():
            layer = Layer(
                name=layer_name,
                locked=layer_data.get("locked", False),
                visible=layer_data.get("visible", True)
            )

            for segment_data in layer_data.get("segments", []):
                segment = Segment(layer=layer, settings=segment_data.get("settings"))

                # Add points
                for pt in segment_data.get("points", []):
                    segment.add_point(QPointF(pt[0], pt[1]))

                # Add controls
                segment.controls = []
                for ctrl in segment_data.get("controls", []):
                    if ctrl is None:
                        segment.controls.append(None)
                    else:
                        segment.controls.append(QPointF(ctrl[0], ctrl[1]))

                segment.visible = segment_data.get("visible", True)
                layer.add_segment(segment)

            editor_data.add_layer(layer)

        return editor_data

    def to_legacy_format(self) -> Dict[str, Dict[str, List]]:
        """
        Convert to legacy format used by the editor's init_contour method.

        Legacy format: {
            layer_name: {
                "contours": [np.ndarray(shape=(N, 1, 2)), ...],
                "settings": [dict, ...]
            }
        }

        Returns:
            Dictionary in legacy format
        """
        result = {}

        for name, layer in self.layers.items():
            contours = []
            settings_list = []

            for segment in layer.segments:
                # Convert segment points to numpy array
                if len(segment.points) > 0:
                    points_array = np.array(
                        [[pt.x(), pt.y()] for pt in segment.points],
                        dtype=np.float32
                    ).reshape(-1, 1, 2)

                    contours.append(points_array)
                    settings_list.append(deepcopy(segment.settings))

            result[name] = {
                "contours": contours,
                "settings": settings_list
            }

        return result

    @classmethod
    def from_legacy_format(
        cls,
        data: Dict[str, Any],
        layer_defaults: Optional[Dict[str, Dict[str, bool]]] = None
    ) -> 'ContourEditorData':
        """
        Create ContourEditorData from legacy format.

        Legacy format supports two styles:
        1. New: {layer_name: {"contours": [...], "settings": [...]}}
        2. Old: {layer_name: [contour1, contour2, ...]}

        Args:
            data: Dictionary in legacy format
            layer_defaults: Optional dict with layer properties like:
                {"layer_name": {"locked": bool, "visible": bool}}

        Returns:
            New ContourEditorData instance
        """
        editor_data = cls()
        layer_defaults = layer_defaults or {}

        for layer_name, layer_content in data.items():
            # Get layer defaults
            defaults = layer_defaults.get(layer_name, {})
            layer = Layer(
                name=layer_name,
                locked=defaults.get("locked", False),
                visible=defaults.get("visible", True)
            )

            # Check if new format (dict with "contours" key) or old format (list)
            if isinstance(layer_content, dict) and "contours" in layer_content:
                # New format
                contours_list = layer_content.get("contours", [])
                settings_list = layer_content.get("settings", [])

                # Pad settings list if shorter than contours list
                while len(settings_list) < len(contours_list):
                    settings_list.append({})

                for contour_points, settings in zip(contours_list, settings_list):
                    segment = Segment(layer=layer, settings=settings)

                    # Convert numpy array to QPointF list
                    if isinstance(contour_points, np.ndarray):
                        # Handle shape (N, 1, 2) or (N, 2)
                        if contour_points.ndim == 3:
                            points = contour_points.reshape(-1, 2)
                        else:
                            points = contour_points

                        for pt in points:
                            segment.add_point(QPointF(float(pt[0]), float(pt[1])))

                    layer.add_segment(segment)

            elif isinstance(layer_content, list):
                # Old format - just a list of contours
                for contour_points in layer_content:
                    segment = Segment(layer=layer)

                    if isinstance(contour_points, np.ndarray):
                        # Handle shape (N, 1, 2) or (N, 2)
                        if contour_points.ndim == 3:
                            points = contour_points.reshape(-1, 2)
                        else:
                            points = contour_points

                        for pt in points:
                            segment.add_point(QPointF(float(pt[0]), float(pt[1])))

                    layer.add_segment(segment)

            editor_data.add_layer(layer)

        return editor_data

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the editor data.

        Returns:
            Dictionary containing:
            - total_layers: number of layers
            - total_segments: total number of segments
            - total_points: total number of points
            - layers: per-layer breakdown
        """
        total_segments = 0
        total_points = 0
        layers_info = {}

        for name, layer in self.layers.items():
            layer_segments = len(layer.segments)
            layer_points = sum(len(seg.points) for seg in layer.segments)

            total_segments += layer_segments
            total_points += layer_points

            layers_info[name] = {
                "segments": layer_segments,
                "points": layer_points,
                "locked": layer.locked,
                "visible": layer.visible
            }

        return {
            "total_layers": len(self.layers),
            "total_segments": total_segments,
            "total_points": total_points,
            "layers": layers_info
        }

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate the editor data.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for name, layer in self.layers.items():
            for i, segment in enumerate(layer.segments):
                # Check if segment has layer reference
                if segment.layer is None:
                    errors.append(f"Layer '{name}', Segment {i}: Missing layer reference")

                # Check if segment has enough points
                if len(segment.points) < 2:
                    errors.append(f"Layer '{name}', Segment {i}: Insufficient points ({len(segment.points)})")

                # Check controls list length
                expected_controls = len(segment.points) - 1
                if len(segment.controls) != expected_controls:
                    errors.append(
                        f"Layer '{name}', Segment {i}: Controls mismatch "
                        f"(expected {expected_controls}, got {len(segment.controls)})"
                    )

        return (len(errors) == 0, errors)

    def __repr__(self) -> str:
        layers_repr = ", ".join([
            f"{name}({len(layer.segments)} segments)"
            for name, layer in self.layers.items()
        ])
        return f"ContourEditorData(layers=[{layers_repr}])"

    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"ContourEditorData:\n"
            f"  Layers: {stats['total_layers']}\n"
            f"  Segments: {stats['total_segments']}\n"
            f"  Points: {stats['total_points']}"
        )