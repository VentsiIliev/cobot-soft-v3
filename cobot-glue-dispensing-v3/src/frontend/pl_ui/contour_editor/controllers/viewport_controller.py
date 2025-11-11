from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QImage
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space


class ViewportController:
    def __init__(self, editor):
        self.editor = editor
        
        # Viewport state - now owned by controller
        self.scale_factor = 1.0
        self.translation = QPointF(0, 0)
        self.is_zooming = False
        
        # Image state - now owned by controller
        self.image = None

    def zoom_in(self):
        self._apply_centered_zoom(1.25)
        self.editor.update()

    def zoom_out(self):
        self._apply_centered_zoom(0.8)
        self.editor.update()

    def _apply_centered_zoom(self, factor):
        """Apply zoom centered on the widget center"""
        # Center of the widget in screen space
        center_screen = QPointF(self.editor.width() / 2, self.editor.height() / 2)

        # Convert screen center to image space
        center_img_space = map_to_image_space(center_screen, self.translation, self.scale_factor)

        # Apply the zoom factor
        self.scale_factor *= factor

        # Calculate new screen position of image center after scaling
        new_center_screen_pos = center_img_space * self.scale_factor + self.translation

        # Adjust translation so that the zoom is centered on the widget center
        self.translation += center_screen - new_center_screen_pos

    def reset_zoom(self):
        """Reset zoom and center the image in the widget"""
        self.scale_factor = 1.0

        if self.image:
            # Center image in widget
            frame_width = self.editor.width()
            frame_height = self.editor.height()
            img_width = self.image.width()
            img_height = self.image.height()

            x = (frame_width - img_width) / 2
            y = (frame_height - img_height) / 2
            self.translation = QPointF(x, y)
        else:
            self.translation = QPointF(0, 0)

        self.editor.update()

    def handle_zoom(self, event):
        """Handle mouse wheel zoom towards cursor position"""
        angle = event.angleDelta().y()
        factor = 1.25 if angle > 0 else 0.8

        cursor_pos = event.position()
        cursor_img_pos = map_to_image_space(cursor_pos, self.translation, self.scale_factor)

        self.scale_factor *= factor

        # Update translation to zoom towards cursor
        new_cursor_screen_pos = cursor_img_pos * self.scale_factor + self.translation
        self.translation += cursor_pos - new_cursor_screen_pos
        self.editor.update()

    def reset_zoom_flag(self):
        self.is_zooming = False

    def toggle_zooming(self):
        self.is_zooming = not self.is_zooming
        if self.is_zooming:
            self.editor.grabGesture(Qt.GestureType.PinchGesture)
            print("Zooming and pinch gesture enabled.")
        else:
            self.editor.ungrabGesture(Qt.GestureType.PinchGesture)
            print("Zooming and pinch gesture disabled.")

    def load_image(self, path):
        """Load image from file path"""
        if path:
            image = QImage(path)
            if image.isNull():
                # print(f"Failed to load image from: {path}")
                image = QImage(1280, 720, QImage.Format.Format_RGB32)
        else:
            image = QImage(1280, 720, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        self.image = image
        return image

    def set_image(self, image):
        """Set image from numpy array"""
        if image is None:
            return
        height, width, channels = image.shape
        bytes_per_line = channels * width
        fmt = QImage.Format.Format_RGB888 if channels == 3 else QImage.Format.Format_RGBA888
        qimage = QImage(image.data, width, height, bytes_per_line, fmt)
        self.update_image(qimage)

    def is_within_image(self, pos: QPointF) -> bool:
        image_width = self.image.width()
        image_height = self.image.height()
        img_pos = map_to_image_space(pos, self.translation, self.scale_factor)
        return 0 <= img_pos.x() < image_width and 0 <= img_pos.y() < image_height

    def update_image(self, image_input):
        """Update the current image"""
        if isinstance(image_input, str):
            image = QImage(image_input)
            if image.isNull():
                # print(f"Failed to load image from path: {image_input}")
                return
            self.image = image
        elif isinstance(image_input, QImage):
            self.image = image_input
        else:
            print("Unsupported image input type.")
            return
        self.editor.update()