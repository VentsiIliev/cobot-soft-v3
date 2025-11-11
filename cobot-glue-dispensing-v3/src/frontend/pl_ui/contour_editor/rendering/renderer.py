from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainterPath, QTransform

from src.frontend.pl_ui.contour_editor import constants
from src.frontend.pl_ui.contour_editor.constants import LAYER_COLORS
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import calculate_distance
from src.frontend.pl_ui.contour_editor.utils.point_visibility import get_visible_points


def draw_ruler(contour_editor,painter):
    # --- Draw Ruler Measurement ---
    if getattr(contour_editor, "ruler_mode_active", False) and contour_editor.ruler_mode.ruler_start and contour_editor.ruler_mode.ruler_end:
        # Map image-space points to screen-space using current transform
        painter.save()  # save current transform
        screen_start = painter.transform().map(contour_editor.ruler_mode.ruler_start)
        screen_end = painter.transform().map(contour_editor.ruler_mode.ruler_end)

        # Draw ruler in widget coordinates
        painter.resetTransform()
        pen = QPen(QColor(0, 200, 255), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(screen_start.toPoint(), screen_end.toPoint())

        # Draw distance text
        dist_px = calculate_distance(contour_editor.ruler_mode.ruler_start, contour_editor.ruler_mode.ruler_end)
        px_per_mm = 0.985
        dist_mm = dist_px / px_per_mm

        mid_x = (screen_start.x() + screen_end.x()) / 2
        mid_y = (screen_start.y() + screen_end.y()) / 2
        dx = screen_end.x() - screen_start.x()
        dy = screen_end.y() - screen_start.y()
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length != 0:
            ux, uy = -dy / length, dx / length
        else:
            ux, uy = 0, -1
        offset_distance = 15
        text_x = mid_x + ux * offset_distance
        text_y = mid_y + uy * offset_distance

        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        text = f"{dist_mm:.1f}mm"
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        painter.drawText(
            QRectF(text_x - text_width / 2, text_y - text_height / 2, text_width, text_height),
            Qt.AlignmentFlag.AlignCenter,
            text
        )

        painter.restore()  # restore original transform so segments draw correctly

def draw_segments(contour_editor,painter,bezier_manager):
    for segment in contour_editor.manager.get_segments():
        if segment.visible:
            # if segment.get("visible", True):  # Default to True if missing
            draw_bezier_segment(contour_editor,painter, segment)

def draw_pickup_point(contour_editor,painter):
    # Draw pickup point if set
    if contour_editor.pickup_point is not None:
        contour_editor.draw_pickup_point(painter, contour_editor.pickup_point)

def draw_selection_status(contour_editor, painter):
    """Draw selection status indicator in the top-right corner"""
    selected_count = contour_editor.get_selected_points_count()
    if selected_count <= 1:
        return  # Don't show indicator for single or no selection

    # Reset painter transformations for UI overlay
    painter.resetTransform()

    # Set up text
    status_text = f"{selected_count} points selected"
    font = painter.font()
    font.setPointSize(10)
    font.setBold(True)
    painter.setFont(font)

    # Calculate text size and position
    text_rect = painter.fontMetrics().boundingRect(status_text)
    padding = 8
    margin = 10

    # Position in top-right corner
    x = contour_editor.width() - text_rect.width() - padding * 2 - margin
    y = margin

    # Draw background
    bg_rect = QRectF(x - padding, y, text_rect.width() + padding * 2, text_rect.height() + padding)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(103, 80, 164, 200)))  # Semi-transparent #6750A4

    painter.drawRoundedRect(bg_rect, 4, 4)

    # Draw text
    painter.setPen(QPen(Qt.GlobalColor.white))
    painter.drawText(int(x), int(y + text_rect.height()), status_text)

def draw_rectangle_selection(contour_editor, painter):
    """Draw the rectangle selection overlay"""
    # Check if rectangle select mode is active and has a selection rectangle
    if hasattr(contour_editor, 'rectangle_select_mode'):
        rect = contour_editor.rectangle_select_mode.get_selection_rect()
        if rect:
            # Draw in image space (before resetTransform)
            # Rectangle border
            pen = QPen(QColor(103, 80, 164, 255), 2 / contour_editor.scale_factor, Qt.PenStyle.DashLine)
            painter.setPen(pen)

            # Semi-transparent fill
            brush = QBrush(QColor(103, 80, 164, 50))
            painter.setBrush(brush)

            painter.drawRect(rect)

            # Reset brush
            painter.setBrush(Qt.BrushStyle.NoBrush)

def draw_bezier_segment(contour_editor, painter, segment):
    points = segment.points
    controls = segment.controls
    seg_index = contour_editor.manager.segments.index(segment)
    is_active = (seg_index == contour_editor.manager.active_segment_index)

    # ----------------------------
    # Line thickness settings (screen-space)
    # ----------------------------
    min_line_thickness = 2
    max_line_thickness = 6
    base_thickness = 2 if is_active else 1
    # Do NOT scale line thickness with zoom for precision
    thickness = max(min_line_thickness, min(max_line_thickness, base_thickness))

    # Draw Bezier curve (image space)
    if len(points) >= 2:
        path = QPainterPath()
        path.moveTo(points[0])
        for i in range(1, len(points)):
            if i - 1 < len(controls) and controls[i - 1] is not None:
                path.quadTo(controls[i - 1], points[i])
            else:
                path.lineTo(points[i])

        layer_color = LAYER_COLORS.get(segment.layer.name, QColor("black"))
        pen = QPen(layer_color, thickness / contour_editor.scale_factor)  # scale down by zoom
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if not is_active:
            pen.setColor(layer_color.lighter(150))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    # Draw tangents (image space)
    if is_active or contour_editor.show_handles_only_on_selection:
        tangent_thickness = 1 / contour_editor.scale_factor  # keep thin at any zoom
        painter.setPen(QPen(Qt.GlobalColor.gray, tangent_thickness, Qt.PenStyle.DashLine))
        for i in range(1, len(points)):
            if i - 1 < len(controls):
                ctrl = controls[i - 1]
                if ctrl is not None:
                    painter.drawLine(points[i - 1], ctrl)
                    painter.drawLine(ctrl, points[i])

    # ----------------------------
    # Draw handles (screen-space size, independent of zoom)
    # ----------------------------
    selected_points = {
        (s["role"], s["seg_index"], s["point_index"])
        for s in contour_editor.selection_manager.selected_points_list
    }

    # Use smaller points while dragging for cleaner view but still visible for alignment
    is_dragging = contour_editor.drag_mode.dragging_point is not None

    if is_dragging:
        min_px = 3  # Much smaller circles while dragging
        max_px = 3
        handle_px = 3
    else:
        min_px = 20
        max_px = 20
        handle_px = contour_editor.handle_radius
        handle_px = max(min_px, min(max_px, handle_px))

    old_transform = painter.transform()

    visible_points = get_visible_points(points,contour_editor.scale_factor)
    valid_controls = [c for c in controls if c is not None]
    visible_controls = get_visible_points(valid_controls,contour_editor.scale_factor)

    # Draw anchors (if enabled)
    if constants.SHOW_ANCHOR_POINTS:
        for idx, pt in enumerate(points):
            selected = ("anchor", seg_index, idx) in selected_points
            if not selected and pt not in visible_points:
                continue

            color = contour_editor.handle_selected_color if selected else contour_editor.handle_color
            screen_pt = old_transform.map(pt)

            painter.setTransform(QTransform())  # draw in screen space
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(screen_pt, handle_px, handle_px)
            painter.setTransform(old_transform)

    # Draw control points (if enabled)
    if constants.SHOW_CONTROL_POINTS:
        for idx, ctrl in enumerate(controls):
            if ctrl is None:
                continue

            selected = ("control", seg_index, idx) in selected_points
            if not selected and ctrl not in visible_controls:
                continue

            color = contour_editor.handle_selected_color if selected else QColor(255, 0, 0, 180)
            size = handle_px * (1.2 if selected else 0.8)
            size = max(min_px, min(max_px, size))

            screen_pt = old_transform.map(ctrl)
            painter.setTransform(QTransform())
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(screen_pt, size, size)
            painter.setTransform(old_transform)

def draw_drag_crosshair(editor,painter, screen_pos):
    """Draw a crosshair above the cursor when dragging (helps with touchscreen)"""
    # Offset the crosshair above the cursor so it's visible above the finger
    crosshair_x = screen_pos.x()
    crosshair_y = screen_pos.y() + constants.CROSSHAIR_OFFSET_Y

    from PyQt6.QtGui import QPen

    # Determine line style (solid or dashed)
    line_style = Qt.PenStyle.DashLine if constants.CROSSHAIR_LINE_STYLE == "dashed" else Qt.PenStyle.SolidLine

    # Draw based on selected crosshair style
    if constants.CROSSHAIR_STYLE == "circle":
        # Original style: circle with cross
        # Draw circle at center
        pen = QPen(constants.CROSSHAIR_COLOR, constants.CROSSHAIR_LINE_THICKNESS, line_style)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(crosshair_x, crosshair_y), constants.CROSSHAIR_CIRCLE_RADIUS, constants.CROSSHAIR_CIRCLE_RADIUS)

        # Draw crosshair lines
        pen = QPen(constants.CROSSHAIR_COLOR, constants.CROSSHAIR_LINE_THICKNESS, line_style)
        painter.setPen(pen)

        # Horizontal line
        painter.drawLine(int(crosshair_x - constants.CROSSHAIR_SIZE), int(crosshair_y),
                        int(crosshair_x + constants.CROSSHAIR_SIZE), int(crosshair_y))
        # Vertical line
        painter.drawLine(int(crosshair_x), int(crosshair_y - constants.CROSSHAIR_SIZE),
                        int(crosshair_x), int(crosshair_y + constants.CROSSHAIR_SIZE))

        # Draw connecting line from crosshair to actual cursor
        pen_connector = QPen(constants.CROSSHAIR_CONNECTOR_COLOR, constants.CROSSHAIR_CONNECTOR_THICKNESS, Qt.PenStyle.DashLine)
        painter.setPen(pen_connector)
        painter.drawLine(QPointF(crosshair_x, crosshair_y + constants.CROSSHAIR_CIRCLE_RADIUS),
                        QPointF(screen_pos.x(), screen_pos.y()))

    elif constants.CROSSHAIR_STYLE == "simple":
        # Simple style: just a cross
        pen = QPen(constants.CROSSHAIR_COLOR, constants.CROSSHAIR_LINE_THICKNESS, line_style)
        painter.setPen(pen)

        # Horizontal line
        painter.drawLine(int(crosshair_x - constants.CROSSHAIR_SIZE), int(crosshair_y),
                        int(crosshair_x + constants.CROSSHAIR_SIZE), int(crosshair_y))
        # Vertical line
        painter.drawLine(int(crosshair_x), int(crosshair_y - constants.CROSSHAIR_SIZE),
                        int(crosshair_x), int(crosshair_y + constants.CROSSHAIR_SIZE))

        # Draw connecting line from crosshair to actual cursor (dashed)
        pen_connector = QPen(constants.CROSSHAIR_CONNECTOR_COLOR, constants.CROSSHAIR_CONNECTOR_THICKNESS, Qt.PenStyle.DashLine)
        painter.setPen(pen_connector)
        painter.drawLine(QPointF(crosshair_x, crosshair_y),
                        QPointF(screen_pos.x(), screen_pos.y()))

    # Draw segment lengths for connected segments (if enabled)
    if constants.SHOW_LENGTH_ON_DRAG:
        draw_connected_segment_lengths(editor,painter)

    # Draw coordinate axes and angle visualization (if enabled)
    if constants.SHOW_AXES_ON_DRAG or constants.SHOW_ANGLE_ON_DRAG:
        draw_coordinate_axes_and_angle(editor,painter)

def draw_connected_segment_lengths(editor, painter):
    """Draw lengths of segments connected to the dragged point with offset dashed lines"""
    try:
        if not editor.drag_mode.dragging_point:
            return

        from pl_ui.contour_editor.utils.coordinate_utils import calculate_distance
        import math

        role, seg_index, point_index = editor.drag_mode.dragging_point

        # Only show lengths for anchor points (not control points)
        if role != "anchor":
            return

        segments = editor.manager.get_segments()
        if seg_index < 0 or seg_index >= len(segments):
            return

        segment = segments[seg_index]
        points = segment.points

        if point_index < 0 or point_index >= len(points):
            return

        # Get the current point position
        current_point = points[point_index]

        # Draw length to previous point
        if point_index > 0:
            prev_point = points[point_index - 1]
            draw_segment_length_line(editor,painter, prev_point, current_point, constants.SEGMENT_LENGTH_OFFSET_DISTANCE, constants.PIXELS_PER_MM)

        # Draw length to next point
        if point_index < len(points) - 1:
            next_point = points[point_index + 1]
            draw_segment_length_line(editor,painter, current_point, next_point, constants.SEGMENT_LENGTH_OFFSET_DISTANCE, constants.PIXELS_PER_MM)
    except Exception as e:
        print(f"Error in _draw_connected_segment_lengths: {e}")
        import traceback
        traceback.print_exc()

def draw_segment_length_line(editor,painter, p1, p2, offset, px_per_mm):
    """Draw a dashed measurement line parallel to the segment with length text"""
    import math
    from pl_ui.contour_editor.utils.coordinate_utils import calculate_distance

    # Calculate distance
    dist_px = calculate_distance(p1, p2)
    dist_mm = dist_px / px_per_mm

    # Convert points to screen space
    p1_screen = editor.translation + QPointF(p1.x() * editor.scale_factor, p1.y() * editor.scale_factor)
    p2_screen = editor.translation + QPointF(p2.x() * editor.scale_factor, p2.y() * editor.scale_factor)

    # Calculate perpendicular offset vector
    dx = p2_screen.x() - p1_screen.x()
    dy = p2_screen.y() - p1_screen.y()
    length = math.sqrt(dx * dx + dy * dy)

    if length == 0:
        return

    # Perpendicular unit vector (rotated 90 degrees)
    perp_x = -dy / length
    perp_y = dx / length

    # Offset both points
    p1_offset = QPointF(
        p1_screen.x() + perp_x * offset,
        p1_screen.y() + perp_y * offset
    )
    p2_offset = QPointF(
        p2_screen.x() + perp_x * offset,
        p2_screen.y() + perp_y * offset
    )

    # Draw dashed line
    pen = QPen(constants.SEGMENT_LENGTH_COLOR, constants.SEGMENT_LENGTH_LINE_THICKNESS, Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.drawLine(p1_offset, p2_offset)

    # Draw small perpendicular ticks at endpoints
    painter.setPen(QPen(constants.SEGMENT_LENGTH_COLOR, constants.SEGMENT_LENGTH_LINE_THICKNESS, Qt.PenStyle.SolidLine))

    # Tick at p1
    tick1_start = QPointF(p1_offset.x() - perp_y * constants.SEGMENT_LENGTH_TICK_SIZE, p1_offset.y() + perp_x * constants.SEGMENT_LENGTH_TICK_SIZE)
    tick1_end = QPointF(p1_offset.x() + perp_y * constants.SEGMENT_LENGTH_TICK_SIZE, p1_offset.y() - perp_x * constants.SEGMENT_LENGTH_TICK_SIZE)
    painter.drawLine(tick1_start, tick1_end)

    # Tick at p2
    tick2_start = QPointF(p2_offset.x() - perp_y * constants.SEGMENT_LENGTH_TICK_SIZE, p2_offset.y() + perp_x * constants.SEGMENT_LENGTH_TICK_SIZE)
    tick2_end = QPointF(p2_offset.x() + perp_y * constants.SEGMENT_LENGTH_TICK_SIZE, p2_offset.y() - perp_x * constants.SEGMENT_LENGTH_TICK_SIZE)
    painter.drawLine(tick2_start, tick2_end)

    # Draw length text at midpoint of offset line
    mid_offset = QPointF(
        (p1_offset.x() + p2_offset.x()) / 2,
        (p1_offset.y() + p2_offset.y()) / 2
    )

    # Draw text background for better readability
    text = f"{dist_mm:.1f}mm"
    font = painter.font()
    font.setPointSize(constants.SEGMENT_LENGTH_FONT_SIZE)
    font.setBold(True)
    painter.setFont(font)

    metrics = painter.fontMetrics()
    text_width = metrics.horizontalAdvance(text)
    text_height = metrics.height()

    # Background rectangle
    bg_rect = QRectF(
        mid_offset.x() - text_width / 2 - constants.AXIS_LABEL_PADDING_X,
        mid_offset.y() - text_height / 2 - constants.AXIS_LABEL_PADDING_Y,
        text_width + (constants.AXIS_LABEL_PADDING_X * 2),
        text_height + (constants.AXIS_LABEL_PADDING_Y * 2)
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(constants.SEGMENT_LENGTH_BG_COLOR))
    painter.drawRoundedRect(bg_rect, constants.AXIS_LABEL_BORDER_RADIUS, constants.AXIS_LABEL_BORDER_RADIUS)

    # Draw text
    painter.setPen(QPen(constants.SEGMENT_LENGTH_COLOR))
    painter.drawText(
        int(mid_offset.x() - text_width / 2),
        int(mid_offset.y() + text_height / 4),
        text
    )

def draw_coordinate_axes_and_angle(editor,painter):
    """Draw X/Y coordinate axes and angle visualization when dragging a point"""
    try:
        if not editor.drag_mode.dragging_point:
            return

        import math
        from pl_ui.contour_editor.utils.coordinate_utils import calculate_distance
        from PyQt6.QtGui import QPainterPath

        role, seg_index, point_index = editor.drag_mode.dragging_point

        # Only show for anchor points
        if role != "anchor":
            return

        segments = editor.manager.get_segments()
        if seg_index < 0 or seg_index >= len(segments):
            return

        segment = segments[seg_index]
        points = segment.points

        if point_index < 0 or point_index >= len(points):
            return

        # Get the current point and reference point (previous point if it exists)
        current_point = points[point_index]

        # Use previous point as reference (origin of coordinate system)
        if point_index > 0:
            reference_point = points[point_index - 1]
        else:
            # No previous point, can't draw axes
            return

        # Convert to screen space
        ref_screen = editor.translation + QPointF(reference_point.x() * editor.scale_factor, reference_point.y() * editor.scale_factor)
        curr_screen = editor.translation + QPointF(current_point.x() * editor.scale_factor, current_point.y() * editor.scale_factor)

        # Calculate deltas
        dx_screen = curr_screen.x() - ref_screen.x()
        dy_screen = curr_screen.y() - ref_screen.y()

        # Calculate distances in image space (for accurate mm measurements)
        dx_img = current_point.x() - reference_point.x()
        dy_img = current_point.y() - reference_point.y()
        dx_mm = dx_img / constants.PIXELS_PER_MM
        dy_mm = dy_img / constants.PIXELS_PER_MM

        # Calculate angle (in degrees, relative to positive X axis)
        angle_rad = math.atan2(dy_screen, dx_screen)
        angle_deg = math.degrees(angle_rad)

        # Draw axes (if enabled)
        if constants.SHOW_AXES_ON_DRAG:
            # Draw horizontal axis line (X projection)
            x_end_point = QPointF(curr_screen.x(), ref_screen.y())
            pen_x = QPen(constants.AXIS_X_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_x)
            painter.drawLine(ref_screen, x_end_point)

            # Draw vertical axis line (Y projection)
            y_end_point = QPointF(ref_screen.x(), curr_screen.y())
            pen_y = QPen(constants.AXIS_Y_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_y)
            painter.drawLine(ref_screen, y_end_point)

            # Draw the actual vector line (from reference to current)
            pen_vector = QPen(constants.AXIS_VECTOR_LINE_COLOR, constants.AXIS_VECTOR_LINE_THICKNESS, Qt.PenStyle.DotLine)
            painter.setPen(pen_vector)
            painter.drawLine(ref_screen, curr_screen)

            # Draw X distance label
            x_mid = QPointF((ref_screen.x() + x_end_point.x()) / 2, ref_screen.y() - 10)
            draw_axis_label(painter, f"X: {abs(dx_mm):.1f}mm", x_mid, constants.AXIS_X_COLOR)

            # Draw Y distance label
            y_mid = QPointF(ref_screen.x() + 10, (ref_screen.y() + y_end_point.y()) / 2)
            draw_axis_label(painter, f"Y: {abs(dy_mm):.1f}mm", y_mid, constants.AXIS_Y_COLOR)

        # Draw angle arc (if enabled)
        if constants.SHOW_ANGLE_ON_DRAG:
            start_angle = 0  # Start from positive X axis
            span_angle = angle_deg

            # Create arc path
            arc_rect = QRectF(
                ref_screen.x() - constants.AXIS_ARC_RADIUS,
                ref_screen.y() - constants.AXIS_ARC_RADIUS,
                constants.AXIS_ARC_RADIUS * 2,
                constants.AXIS_ARC_RADIUS * 2
            )

            pen_arc = QPen(constants.AXIS_ANGLE_ARC_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_arc)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw arc (Qt uses 1/16th of a degree as unit)
            painter.drawArc(arc_rect, int(start_angle * 16), int(-span_angle * 16))

            # Draw angle label
            # Position label at the middle of the arc
            label_angle_rad = angle_rad / 2
            label_radius = constants.AXIS_ARC_RADIUS + 25
            label_pos = QPointF(
                ref_screen.x() + label_radius * math.cos(label_angle_rad),
                ref_screen.y() - label_radius * math.sin(label_angle_rad)
            )
            draw_axis_label(painter, f"{angle_deg:.1f}°", label_pos, constants.AXIS_ANGLE_ARC_COLOR)

    except Exception as e:
        print(f"Error in _draw_coordinate_axes_and_angle: {e}")
        import traceback
        traceback.print_exc()

def draw_axis_label(painter, text, pos, color):
    """Draw a label with background for axis measurements"""
    font = painter.font()
    font.setPointSize(constants.AXIS_LABEL_FONT_SIZE)
    font.setBold(True)
    painter.setFont(font)

    metrics = painter.fontMetrics()
    text_width = metrics.horizontalAdvance(text)
    text_height = metrics.height()

    # Background rectangle
    bg_rect = QRectF(
        pos.x() - text_width / 2 - constants.AXIS_LABEL_PADDING_X,
        pos.y() - text_height / 2 - constants.AXIS_LABEL_PADDING_Y,
        text_width + (constants.AXIS_LABEL_PADDING_X * 2),
        text_height + (constants.AXIS_LABEL_PADDING_Y * 2)
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(constants.AXIS_LABEL_BG_COLOR))
    painter.drawRoundedRect(bg_rect, constants.AXIS_LABEL_BORDER_RADIUS, constants.AXIS_LABEL_BORDER_RADIUS)

    # Draw text
    painter.setPen(QPen(color))
    painter.drawText(
        int(pos.x() - text_width / 2),
        int(pos.y() + text_height / 4),
        text
    )

def draw_line_axes_and_angle(editor, painter, p1, p2, px_per_mm):
    """Draw X/Y coordinate axes and angle visualization for a line segment (p1 to p2)"""
    try:
        import math

        # Convert to screen space
        ref_screen = editor.translation + QPointF(p1.x() * editor.scale_factor, p1.y() * editor.scale_factor)
        curr_screen = editor.translation + QPointF(p2.x() * editor.scale_factor, p2.y() * editor.scale_factor)

        # Calculate deltas
        dx_screen = curr_screen.x() - ref_screen.x()
        dy_screen = curr_screen.y() - ref_screen.y()

        # Calculate distances in image space (for accurate mm measurements)
        dx_img = p2.x() - p1.x()
        dy_img = p2.y() - p1.y()
        dx_mm = dx_img / px_per_mm  # Uses passed-in px_per_mm parameter
        dy_mm = dy_img / px_per_mm

        # Calculate angle (in degrees, relative to positive X axis)
        angle_rad = math.atan2(dy_screen, dx_screen)
        angle_deg = math.degrees(angle_rad)

        # Draw axes (if enabled)
        if constants.SHOW_AXES_ON_OVERLAY:
            # Draw horizontal axis line (X projection)
            x_end_point = QPointF(curr_screen.x(), ref_screen.y())
            pen_x = QPen(constants.AXIS_X_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_x)
            painter.drawLine(ref_screen, x_end_point)

            # Draw vertical axis line (Y projection)
            y_end_point = QPointF(ref_screen.x(), curr_screen.y())
            pen_y = QPen(constants.AXIS_Y_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_y)
            painter.drawLine(ref_screen, y_end_point)

            # Draw the actual vector line (from reference to current)
            pen_vector = QPen(constants.AXIS_VECTOR_LINE_COLOR, constants.AXIS_VECTOR_LINE_THICKNESS, Qt.PenStyle.DotLine)
            painter.setPen(pen_vector)
            painter.drawLine(ref_screen, curr_screen)

            # Draw X distance label
            x_mid = QPointF((ref_screen.x() + x_end_point.x()) / 2, ref_screen.y() - 10)
            draw_axis_label(painter, f"X: {abs(dx_mm):.1f}mm", x_mid, constants.AXIS_X_COLOR)

            # Draw Y distance label
            y_mid = QPointF(ref_screen.x() + 10, (ref_screen.y() + y_end_point.y()) / 2)
            draw_axis_label(painter, f"Y: {abs(dy_mm):.1f}mm", y_mid, constants.AXIS_Y_COLOR)

        # Draw angle arc (if enabled)
        if constants.SHOW_ANGLE_ON_OVERLAY:
            # Draw angle arc
            start_angle = 0  # Start from positive X axis
            span_angle = angle_deg

            # Create arc path
            arc_rect = QRectF(
                ref_screen.x() - constants.AXIS_ARC_RADIUS,
                ref_screen.y() - constants.AXIS_ARC_RADIUS,
                constants.AXIS_ARC_RADIUS * 2,
                constants.AXIS_ARC_RADIUS * 2
            )

            pen_arc = QPen(constants.AXIS_ANGLE_ARC_COLOR, constants.AXIS_LINE_THICKNESS, Qt.PenStyle.DashLine)
            painter.setPen(pen_arc)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw arc (Qt uses 1/16th of a degree as unit)
            painter.drawArc(arc_rect, int(start_angle * 16), int(-span_angle * 16))

            # Draw angle label
            # Position label at the middle of the arc
            label_angle_rad = angle_rad / 2
            label_radius = constants.AXIS_ARC_RADIUS + 25
            label_pos = QPointF(
                ref_screen.x() + label_radius * math.cos(label_angle_rad),
                ref_screen.y() - label_radius * math.sin(label_angle_rad)
            )
            draw_axis_label(painter, f"{angle_deg:.1f}°", label_pos, constants.AXIS_ANGLE_ARC_COLOR)

    except Exception as e:
        print(f"Error in _draw_line_axes_and_angle: {e}")
        import traceback
        traceback.print_exc()

def draw_highlighted_line_segment(editor, painter):
    """Draw the highlighted line segment with thick orange line and measurement lines"""
    try:
        seg_index, line_index = editor.highlighted_line_segment

        segments = editor.manager.get_segments()
        if seg_index < 0 or seg_index >= len(segments):
            return

        segment = segments[seg_index]
        points = segment.points

        # line_index represents the line from points[line_index] to points[line_index + 1]
        if line_index < 0 or line_index >= len(points) - 1:
            return

        p1 = points[line_index]
        p2 = points[line_index + 1]

        # Draw thick highlighted line (in image space, so painter already has transform)
        pen = QPen(constants.HIGHLIGHTED_LINE_COLOR, constants.HIGHLIGHTED_LINE_THICKNESS)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

        # Draw the measurement line in screen space
        # Save current transform
        old_transform = painter.transform()

        # Reset to screen space
        painter.resetTransform()

        # Draw measurement lines in screen space (if enabled)
        if constants.SHOW_LENGTH_ON_OVERLAY:
            draw_segment_length_line(editor,painter, p1, p2, constants.SEGMENT_LENGTH_OFFSET_DISTANCE, constants.PIXELS_PER_MM)

        # Draw coordinate axes and angle for highlighted line (if enabled)
        if constants.SHOW_AXES_ON_OVERLAY or constants.SHOW_ANGLE_ON_OVERLAY:
            draw_line_axes_and_angle(editor,painter, p1, p2, constants.PIXELS_PER_MM)

        # Restore image space transform
        painter.setTransform(old_transform)

    except Exception as e:
        print(f"Error in _draw_highlighted_line_segment: {e}")
        import traceback
        traceback.print_exc()
