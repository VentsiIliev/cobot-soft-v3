"""
Constants Manager
Handles loading and saving user settings from/to JSON file,
with fallback to defaults in constants.py
"""
import json
import os
from PyQt6.QtGui import QColor


class ConstantsManager:
    """Manages loading/saving constants from JSON with fallback to defaults"""

    SETTINGS_FILE = "contour_editor_settings.json"

    @staticmethod
    def get_settings_path():
        """Get the path to the settings JSON file"""
        # Save in the same directory as this file
        return os.path.join(
            os.path.dirname(__file__),
            ConstantsManager.SETTINGS_FILE
        )

    @staticmethod
    def color_to_dict(color):
        """Convert QColor to dictionary"""
        return {
            "r": color.red(),
            "g": color.green(),
            "b": color.blue(),
            "a": color.alpha()
        }

    @staticmethod
    def dict_to_color(color_dict):
        """Convert dictionary to QColor"""
        return QColor(
            color_dict["r"],
            color_dict["g"],
            color_dict["b"],
            color_dict["a"]
        )

    @staticmethod
    def load_settings():
        """
        Load settings from JSON file.
        Returns None if file doesn't exist (will use defaults from constants.py)
        """
        settings_path = ConstantsManager.get_settings_path()

        if not os.path.exists(settings_path):
            print(f"Settings file not found: {settings_path}")
            print("Using default values from constants.py")
            return None

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert color dictionaries back to QColor objects
            settings = {}
            for key, value in data.items():
                if isinstance(value, dict) and "r" in value and "g" in value:
                    # This is a color
                    settings[key] = ConstantsManager.dict_to_color(value)
                else:
                    settings[key] = value

            print(f"Loaded {len(settings)} settings from {settings_path}")
            return settings

        except Exception as e:
            print(f"Error loading settings: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def save_settings(settings):
        """
        Save settings to JSON file.

        Args:
            settings: Dictionary of setting_name -> value
        """
        settings_path = ConstantsManager.get_settings_path()

        try:
            # Convert QColor objects to dictionaries for JSON serialization
            data = {}
            for key, value in settings.items():
                if isinstance(value, QColor):
                    data[key] = ConstantsManager.color_to_dict(value)
                else:
                    data[key] = value

            # Write to JSON file with pretty formatting
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)

            print(f"Saved {len(settings)} settings to {settings_path}")
            return True

        except Exception as e:
            print(f"Error saving settings: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def apply_settings(settings):
        """
        Apply settings by overriding values in the constants module.

        Args:
            settings: Dictionary of setting_name -> value (can be None to use defaults)
        """
        if settings is None:
            print("No settings to apply, using defaults from constants.py")
            return

        try:
            from pl_ui.contour_editor import constants

            applied_count = 0
            for const_name, value in settings.items():
                if hasattr(constants, const_name):
                    setattr(constants, const_name, value)
                    applied_count += 1
                else:
                    print(f"Warning: Unknown constant '{const_name}' in settings")

            print(f"Applied {applied_count} settings to constants module")

        except Exception as e:
            print(f"Error applying settings: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def reset_to_defaults():
        """
        Reset all settings to defaults by deleting the JSON file
        and reloading the constants module.
        """
        settings_path = ConstantsManager.get_settings_path()

        try:
            if os.path.exists(settings_path):
                os.remove(settings_path)
                print(f"Deleted settings file: {settings_path}")

            # Reload constants module to get defaults
            from pl_ui.contour_editor import constants
            import importlib
            importlib.reload(constants)

            print("Reset to default settings")
            return True

        except Exception as e:
            print(f"Error resetting to defaults: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def get_all_constants():
        """Get all constant values from the constants module (for populating dialog)"""
        from pl_ui.contour_editor import constants

        # List of all constants we want to manage
        constant_names = [
            # Visualization toggles
            "SHOW_CONTROL_POINTS",
            "SHOW_ANCHOR_POINTS",
            "SHOW_AXES_ON_DRAG",
            "SHOW_LENGTH_ON_DRAG",
            "SHOW_ANGLE_ON_DRAG",
            "SHOW_AXES_ON_OVERLAY",
            "SHOW_LENGTH_ON_OVERLAY",
            "SHOW_ANGLE_ON_OVERLAY",

            # Axes and angles
            "AXIS_X_COLOR",
            "AXIS_Y_COLOR",
            "AXIS_ANGLE_ARC_COLOR",
            "AXIS_VECTOR_LINE_COLOR",
            "AXIS_LABEL_BG_COLOR",
            "AXIS_LINE_THICKNESS",
            "AXIS_VECTOR_LINE_THICKNESS",
            "AXIS_ARC_RADIUS",
            "AXIS_LABEL_FONT_SIZE",
            "AXIS_LABEL_PADDING_X",
            "AXIS_LABEL_PADDING_Y",
            "AXIS_LABEL_BORDER_RADIUS",

            # Segment length
            "SEGMENT_LENGTH_COLOR",
            "SEGMENT_LENGTH_BG_COLOR",
            "SEGMENT_LENGTH_LINE_THICKNESS",
            "SEGMENT_LENGTH_OFFSET_DISTANCE",
            "SEGMENT_LENGTH_TICK_SIZE",
            "SEGMENT_LENGTH_FONT_SIZE",

            # Highlighted line
            "HIGHLIGHTED_LINE_COLOR",
            "HIGHLIGHTED_LINE_THICKNESS",

            # Crosshair
            "CROSSHAIR_COLOR",
            "CROSSHAIR_CONNECTOR_COLOR",
            "CROSSHAIR_LINE_THICKNESS",
            "CROSSHAIR_SIZE",
            "CROSSHAIR_OFFSET_Y",
            "CROSSHAIR_CIRCLE_RADIUS",
            "CROSSHAIR_CONNECTOR_THICKNESS",

            # Points
            "POINT_HANDLE_COLOR",
            "POINT_HANDLE_SELECTED_COLOR",
            "POINT_HANDLE_RADIUS",
            "POINT_MIN_DISPLAY_SCALE",

            # Overlays
            "OVERLAY_BUTTON_SIZE",
            "OVERLAY_RADIUS",
            "OVERLAY_BUTTON_BORDER_WIDTH",
            "OVERLAY_BUTTON_SELECTED_BORDER_WIDTH",
            "OVERLAY_BUTTON_PRIMARY_COLOR",
            "OVERLAY_BUTTON_PRIMARY_HOVER",
            "OVERLAY_BUTTON_SELECTED_COLOR",
            "OVERLAY_BUTTON_SELECTED_BORDER",
            "OVERLAY_BUTTON_DELETE_COLOR",
            "OVERLAY_BUTTON_DELETE_HOVER",
            "OVERLAY_BUTTON_SET_LENGTH_COLOR",
            "OVERLAY_BUTTON_SET_LENGTH_HOVER",
            "OVERLAY_BUTTON_CANCEL_COLOR",
            "OVERLAY_BUTTON_CANCEL_HOVER",

            # Measurement and timing
            "PIXELS_PER_MM",
            "DRAG_THRESHOLD_PX",
            "POINT_HIT_RADIUS_PX",
            "CLUSTER_DISTANCE_PX",
            "DRAG_UPDATE_INTERVAL_MS",
            "POINT_INFO_HOLD_DURATION_MS",
            "PRESS_HOLD_MOVEMENT_THRESHOLD_PX",
        ]

        result = {}
        for name in constant_names:
            if hasattr(constants, name):
                result[name] = getattr(constants, name)

        return result
