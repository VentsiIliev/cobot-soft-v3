"""
Magnifier widget that shows a zoomed-in view of the cursor position
for precise point placement.
"""
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint, QTimer
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QImage
from src.frontend.pl_ui.contour_editor.rendering.renderer import draw_segments, draw_ruler, draw_pickup_point


class MagnifierWidget(QWidget):
    """A floating magnifier that shows a zoomed view of the cursor position"""

    def __init__(self, editor):
        # Don't set a parent - this is a top-level window
        super().__init__(None)
        self.editor = editor
        self.magnification = 4.0  # Magnification factor
        self.size = 150  # Size of the magnifier window
        self.offset = QPoint(20, 20)  # Offset from cursor
        self.cursor_pos = QPointF(0, 0)  # Current cursor position in image space

        # Setup widget as a frameless, always-on-top tool window
        self.setFixedSize(self.size, self.size)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Timer for throttling updates and avoiding reentrancy
        self.update_timer = QTimer()
        self.update_timer.setInterval(16)  # ~60 FPS
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update)

    def update_position(self, widget_pos, image_pos):
        """Update the magnifier content based on cursor position, keep magnifier at top-left

        Args:
            widget_pos: Mouse position in editor widget coordinates
            image_pos: Mouse position in image space coordinates
        """
        try:
            # Safety check
            if not hasattr(self, 'editor') or self.editor is None:
                return

            # Update cursor position for content rendering
            self.cursor_pos = image_pos

            # Position magnifier at top-left corner of the editor widget
            try:
                # Get top-left corner of editor in global coordinates (with small padding)
                top_left_global = self.editor.mapToGlobal(QPoint(10, 10))

                # Move magnifier to top-left corner
                self.move(top_left_global)

                # Schedule update instead of calling it directly to avoid reentrancy issues
                if not self.update_timer.isActive():
                    self.update_timer.start()
            except Exception as e:
                print(f"Error positioning magnifier: {e}")
        except Exception as e:
            print(f"Magnifier update_position error: {e}")

    def _do_update(self):
        """Perform the actual widget update (called by timer)"""
        try:
            self.update()
        except:
            pass

    def _draw_magnified_view(self, painter, manager):
        """Draw bezier curves and points at normal screen size (compensating for magnification)"""
        from PyQt6.QtGui import QPainterPath, QTransform
        from pl_ui.contour_editor.constants import LAYER_COLORS

        segments = manager.get_segments()
        if not segments:
            return

        # Compensate for magnification - divide sizes by magnification factor
        # so they appear at normal screen size in the magnified view
        line_width = 2.0 / self.magnification  # Normal line width
        point_radius = 3.0 / self.magnification  # Normal point size (3px on screen)

        for seg in segments:
            # Skip invisible segments
            if hasattr(seg, 'layer') and seg.layer and not seg.layer.visible:
                continue
            if hasattr(seg, 'visible') and not seg.visible:
                continue

            points = seg.points
            controls = seg.controls
            if len(points) < 2:
                continue

            # Draw the bezier curve
            path = QPainterPath()
            path.moveTo(points[0].x(), points[0].y())

            for i in range(len(points) - 1):
                p2 = points[i + 1]
                if i < len(controls) and controls[i] is not None:
                    ctrl = controls[i]
                    path.quadTo(ctrl.x(), ctrl.y(), p2.x(), p2.y())
                else:
                    path.lineTo(p2.x(), p2.y())

            # Draw path with compensated line width
            layer_color = LAYER_COLORS.get(seg.layer.name, QColor("black"))
            pen = QPen(layer_color, line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            # Draw anchor points with compensated size
            for pt in points:
                painter.setBrush(QBrush(QColor(0, 150, 255, 180)))  # Blue
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(pt, point_radius, point_radius)

            # Draw control points with compensated size
            for ctrl in controls:
                if ctrl is not None:
                    painter.setBrush(QBrush(QColor(255, 0, 0, 180)))  # Red
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(ctrl, point_radius * 0.8, point_radius * 0.8)

    def _draw_curves_only(self, painter, manager):
        """Draw only the bezier curves without control points or anchor points"""
        from PyQt6.QtGui import QPainterPath

        segments = manager.get_segments()
        if not segments:
            return

        for seg in segments:
            # Skip invisible segments
            if hasattr(seg, 'layer') and seg.layer and not seg.layer.visible:
                continue

            # Skip if segment is not visible
            if hasattr(seg, 'visible') and not seg.visible:
                continue

            points = seg.points
            if len(points) < 2:
                continue

            # Determine line color and width
            if hasattr(seg, 'settings') and seg.settings:
                line_color = QColor(
                    int(seg.settings.get('line_color_r', 0)),
                    int(seg.settings.get('line_color_g', 0)),
                    int(seg.settings.get('line_color_b', 255))
                )
                line_width = float(seg.settings.get('line_width', 2.0))
            else:
                line_color = QColor(0, 0, 255)  # Default blue
                line_width = 2.0

            # Create path for the bezier curve
            path = QPainterPath()
            path.moveTo(points[0].x(), points[0].y())

            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]

                # Check if we have control points for this segment
                if i < len(seg.controls) and seg.controls[i] is not None:
                    ctrl = seg.controls[i]
                    # Quadratic bezier curve with one control point
                    path.quadTo(ctrl.x(), ctrl.y(), p2.x(), p2.y())
                else:
                    # Straight line
                    path.lineTo(p2.x(), p2.y())

            # Draw the path
            pen = QPen(line_color, line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def paintEvent(self, event):
        """Paint the magnified view with complete rendering (image + curves + points)"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw rounded background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(40, 40, 40, 230)))
            painter.drawRoundedRect(self.rect(), 10, 10)

            # Draw border
            painter.setPen(QPen(QColor(103, 80, 164), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)

            # Clip to rounded rectangle for content
            painter.setClipRect(self.rect().adjusted(5, 5, -5, -5))

            # Render the complete magnified view
            if hasattr(self, 'editor') and self.editor is not None:
                try:
                    # Calculate the area to show in image space
                    capture_size = self.size / self.magnification
                    half_capture = capture_size / 2

                    # Center on cursor position
                    view_center_x = self.cursor_pos.x()
                    view_center_y = self.cursor_pos.y()

                    # Calculate the offset to center this area in the magnifier window
                    # We need to translate so that cursor_pos is at the center of the view
                    target_rect = self.rect().adjusted(5, 5, -5, -5)

                    # Save painter state
                    painter.save()

                    # Apply transformations:
                    # 1. Translate to center of target rect
                    painter.translate(target_rect.center())

                    # 2. Apply magnification
                    painter.scale(self.magnification, self.magnification)

                    # 3. Translate to center on cursor position in image space
                    painter.translate(-view_center_x, -view_center_y)

                    # Now draw the scene with the editor's current scale and translation
                    # First, fill with white background
                    from PyQt6.QtCore import QRectF
                    img_width = self.editor.image.width() if self.editor.image else 1280
                    img_height = self.editor.image.height() if self.editor.image else 720
                    painter.fillRect(QRectF(0, 0, img_width, img_height), Qt.GlobalColor.white)

                    # Draw the background image
                    if self.editor.image and not self.editor.image.isNull():
                        painter.drawImage(0, 0, self.editor.image)

                    # Draw bezier curves and small points
                    if hasattr(self.editor, 'manager') and self.editor.manager:
                        self._draw_magnified_view(painter, self.editor.manager)

                    # Draw ruler if active
                    if hasattr(self.editor, 'ruler_mode_active') and self.editor.ruler_mode_active:
                        draw_ruler(self.editor, painter)

                    # Draw pickup point if active
                    if hasattr(self.editor, 'pickup_point') and self.editor.pickup_point:
                        draw_pickup_point(self.editor, painter)

                    # Restore painter state
                    painter.restore()

                except Exception as e:
                    print(f"Magnifier render error: {e}")
                    import traceback
                    traceback.print_exc()

            # Draw crosshair at center (on top of everything)
            painter.setClipping(False)
            center = self.rect().center()
            crosshair_size = 10

            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)

            # Horizontal line
            painter.drawLine(center.x() - crosshair_size, center.y(),
                            center.x() + crosshair_size, center.y())
            # Vertical line
            painter.drawLine(center.x(), center.y() - crosshair_size,
                            center.x(), center.y() + crosshair_size)

            # Draw coordinate text
            painter.setPen(QPen(QColor(255, 255, 255)))
            coord_text = f"({self.cursor_pos.x():.1f}, {self.cursor_pos.y():.1f})"
            painter.drawText(self.rect().adjusted(10, self.size - 25, -10, -10),
                            Qt.AlignmentFlag.AlignCenter, coord_text)
        finally:
            painter.end()