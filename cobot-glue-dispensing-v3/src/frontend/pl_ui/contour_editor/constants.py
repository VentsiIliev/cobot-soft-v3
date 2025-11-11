from PyQt6.QtGui import QColor

# ============================================================================
# CAMERA FEED CONSTANTS
# ============================================================================
CAMERA_FEED_UPDATE_INTERVAL_MS = 100  # Update camera feed every 100 ms

# ============================================================================
# MODE CONSTANTS
# ============================================================================
DRAG_MODE = "drag"
EDIT_MODE = "edit"
PICKUP_POINT_MODE = "pickup_point"
MULTI_SELECT_MODE = "multi_select"
RECTANGLE_SELECT_MODE = "rectangle_select"
MEASURE_MODE = "measure"

# ============================================================================
# LAYER COLORS
# ============================================================================
LAYER_COLORS = {
    "Workpiece": QColor("#FF0000"),  # Red
    "Contour": QColor("#00FFFF"),  # Cyan
    "Fill": QColor("#00FF00"),  # Green
}

# ============================================================================
# COORDINATE AXES & ANGLE VISUALIZATION
# ============================================================================
# Colors (RGBA)
AXIS_X_COLOR = QColor(0, 100, 200, 180)  # Blue
AXIS_Y_COLOR = QColor(200, 100, 0, 180)  # Orange
AXIS_ANGLE_ARC_COLOR = QColor(100, 200, 100, 180)  # Green
AXIS_VECTOR_LINE_COLOR = QColor(150, 150, 150, 100)  # Gray (faint)

# Line properties
AXIS_LINE_THICKNESS = 2
AXIS_VECTOR_LINE_THICKNESS = 1
AXIS_ARC_RADIUS = 40

# Label properties
AXIS_LABEL_FONT_SIZE = 8
AXIS_LABEL_BG_COLOR = QColor(255, 255, 255, 220)  # White with transparency
AXIS_LABEL_PADDING_X = 3
AXIS_LABEL_PADDING_Y = 2
AXIS_LABEL_BORDER_RADIUS = 3

# ============================================================================
# SEGMENT LENGTH MEASUREMENT
# ============================================================================
SEGMENT_LENGTH_COLOR = QColor(0, 200, 0, 255)  # Green
SEGMENT_LENGTH_LINE_THICKNESS = 1
SEGMENT_LENGTH_OFFSET_DISTANCE = 25  # Offset from segment in screen space
SEGMENT_LENGTH_TICK_SIZE = 5
SEGMENT_LENGTH_FONT_SIZE = 9
SEGMENT_LENGTH_BG_COLOR = QColor(255, 255, 255, 200)  # White with transparency

# ============================================================================
# HIGHLIGHTED LINE SEGMENT
# ============================================================================
HIGHLIGHTED_LINE_COLOR = QColor(255, 165, 0, 200)  # Orange with transparency
HIGHLIGHTED_LINE_THICKNESS = 4

# ============================================================================
# DRAG CROSSHAIR (Touchscreen helper)
# ============================================================================
CROSSHAIR_COLOR = QColor(255, 0, 0, 255)  # Red
CROSSHAIR_LINE_THICKNESS = 2
CROSSHAIR_SIZE = 20  # Length of crosshair lines
CROSSHAIR_OFFSET_Y = -50  # Pixels above cursor
CROSSHAIR_CIRCLE_RADIUS = 8
CROSSHAIR_CONNECTOR_COLOR = QColor(255, 0, 0, 100)  # Red with transparency
CROSSHAIR_CONNECTOR_THICKNESS = 1

# Crosshair style options
CROSSHAIR_STYLE = "circle"  # Options: "circle" (circle+cross) or "simple" (just cross)
CROSSHAIR_LINE_STYLE = "solid"  # Options: "solid" or "dashed"

# ============================================================================
# POINT RENDERING
# ============================================================================
POINT_HANDLE_RADIUS = 6
POINT_HANDLE_COLOR = QColor(170, 170, 255, 180)  # Blue translucent
POINT_HANDLE_SELECTED_COLOR = QColor(0, 255, 0, 220)  # Green
POINT_MIN_DISPLAY_SCALE = 1.000  # Hide points when zoomed out beyond this

# ============================================================================
# OVERLAYS (PointInfoOverlay, SegmentClickOverlay)
# ============================================================================
OVERLAY_BUTTON_SIZE = 50
OVERLAY_RADIUS = 70
OVERLAY_BG_COLOR = "transparent"

# Button colors
OVERLAY_BUTTON_PRIMARY_COLOR = QColor(103, 80, 164, 255)#6750A4")  # Purple
OVERLAY_BUTTON_PRIMARY_HOVER = QColor(120, 96, 180, 255)#7860B4")
OVERLAY_BUTTON_SELECTED_COLOR = QColor(255, 165, 0, 255)#FFA500")  # Orange
OVERLAY_BUTTON_SELECTED_BORDER = QColor(255, 215, 0, 255)#FFD700")  # Gold
OVERLAY_BUTTON_DELETE_COLOR = QColor(255, 82, 82, 255)#FF5252")  # Red
OVERLAY_BUTTON_DELETE_HOVER = QColor(255, 102, 102, 255)#FF6666")
OVERLAY_BUTTON_SET_LENGTH_COLOR = QColor(33, 150, 243, 255)#2196F3")  # Blue
OVERLAY_BUTTON_SET_LENGTH_HOVER = QColor(66, 165, 245, 255)#42A5F5")
OVERLAY_BUTTON_CANCEL_COLOR = QColor(102, 102, 102, 255)#666666")  # Gray
OVERLAY_BUTTON_CANCEL_HOVER = QColor(136, 136, 136, 255)#888888")

# Button borders
OVERLAY_BUTTON_BORDER_WIDTH = 2
OVERLAY_BUTTON_BORDER_COLOR = "white"
OVERLAY_BUTTON_SELECTED_BORDER_WIDTH = 3

# ============================================================================
# MEASUREMENT & CONVERSION
# ============================================================================
PIXELS_PER_MM = 0.985  # Calibration factor for mm conversion

# ============================================================================
# DRAG & SELECTION
# ============================================================================
DRAG_THRESHOLD_PX = 10  # Minimum movement to trigger drag
POINT_HIT_RADIUS_PX = 10  # Screen-space hit radius for point selection
CLUSTER_DISTANCE_PX = 6  # Merge nearby points in screen-space

# ============================================================================
# TIMING
# ============================================================================
DRAG_UPDATE_INTERVAL_MS = 16  # ~60 FPS for drag updates
POINT_INFO_HOLD_DURATION_MS = 500  # Hold time to show point info overlay
PRESS_HOLD_MOVEMENT_THRESHOLD_PX = 5  # Max movement allowed during hold

# ============================================================================
# VISUALIZATION ENABLE/DISABLE FLAGS
# ============================================================================
# Point rendering toggles
SHOW_CONTROL_POINTS = True  # Show control points
SHOW_ANCHOR_POINTS = True  # Show anchor points

# Drag visualization toggles (when dragging a point)
SHOW_AXES_ON_DRAG = True  # Show X/Y coordinate axes while dragging
SHOW_LENGTH_ON_DRAG = True  # Show segment length measurements while dragging
SHOW_ANGLE_ON_DRAG = True  # Show angle arc and value while dragging

# Overlay visualization toggles (point info overlay - highlighted line)
SHOW_AXES_ON_OVERLAY = True  # Show X/Y coordinate axes for highlighted line
SHOW_LENGTH_ON_OVERLAY = True  # Show segment length for highlighted line
SHOW_ANGLE_ON_OVERLAY = True  # Show angle arc for highlighted line