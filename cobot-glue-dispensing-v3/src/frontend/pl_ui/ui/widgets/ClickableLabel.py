from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)  # Emits x, y coordinates of click
    corner_dragged = pyqtSignal(int, int, int)  # Emits corner_index, x, y coordinates

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dragging = False
        self.drag_corner_index = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.corner_positions = {}  # Will store corner positions in label coordinates
        self.corner_radius = 15  # Clickable radius around corners
        self.parent_widget = None

    def set_parent_widget(self, parent_widget):
        self.parent_widget = parent_widget

    def update_corner_positions(self, corners_image_coords, image_to_label_scale):
        """Update corner positions in label coordinates for hit testing"""
        self.corner_positions = {}
        if len(corners_image_coords) == 4:
            for i, (img_x, img_y) in enumerate(corners_image_coords):
                # Convert image coordinates to label coordinates
                label_x = img_x / image_to_label_scale
                label_y = img_y / image_to_label_scale
                self.corner_positions[i + 1] = (label_x, label_y)

    def get_corner_at_position(self, x, y):
        """Check if click position is near any corner"""
        for corner_index, (corner_x, corner_y) in self.corner_positions.items():
            distance = ((x - corner_x) ** 2 + (y - corner_y) ** 2) ** 0.5
            if distance <= self.corner_radius:
                return corner_index
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            y = event.position().y()

            # Check if we're clicking near a corner
            corner_at_pos = self.get_corner_at_position(x, y)

            if corner_at_pos is not None:
                # Start dragging this corner
                self.dragging = True
                self.drag_corner_index = corner_at_pos
                corner_x, corner_y = self.corner_positions[corner_at_pos]
                self.drag_offset_x = x - corner_x
                self.drag_offset_y = y - corner_y

                # Set this corner as selected
                if self.parent_widget:
                    self.parent_widget.set_selected_corner(corner_at_pos)

                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                # Regular click - emit clicked signal
                self.clicked.emit(int(x), int(y))

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_corner_index is not None:
            x = event.position().x()
            y = event.position().y()

            # Calculate new corner position (compensate for drag offset)
            new_x = x - self.drag_offset_x
            new_y = y - self.drag_offset_y

            # Emit drag signal
            self.corner_dragged.emit(self.drag_corner_index, int(new_x), int(new_y))
        else:
            # Check if we're hovering over a corner
            x = event.position().x()
            y = event.position().y()
            corner_at_pos = self.get_corner_at_position(x, y)

            if corner_at_pos is not None:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.drag_corner_index = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseReleaseEvent(event)