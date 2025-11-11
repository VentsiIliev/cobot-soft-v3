from PyQt6.QtCore import QPointF

from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space


def zoom_in(contour_editor):
    _apply_centered_zoom(contour_editor, 1.25)

def zoom_out(contour_editor):
    _apply_centered_zoom(contour_editor, 0.8)


def _apply_centered_zoom(contour_editor, factor):
    # Center of the widget in screen space
    center_screen = QPointF(contour_editor.width() / 2, contour_editor.height() / 2)

    # Convert screen center to image space
    center_img_space = map_to_image_space(center_screen, contour_editor.translation, contour_editor.scale_factor)

    # Apply the zoom factor
    contour_editor.scale_factor *= factor

    # Calculate new screen position of image center after scaling
    new_center_screen_pos = center_img_space * contour_editor.scale_factor + contour_editor.translation

    # Adjust translation so that the zoom is centered on the widget center
    contour_editor.translation += center_screen - new_center_screen_pos


def reset_zoom(contour_editor):
    contour_editor.scale_factor = 1.0

    # Center image in widget
    frame_width = contour_editor.width()
    frame_height = contour_editor.height()
    img_width = contour_editor.image.width()
    img_height = contour_editor.image.height()

    x = (frame_width - img_width) / 2
    y = (frame_height - img_height) / 2
    contour_editor.translation = QPointF(x, y)


def handle_zoom(contour_editor,event):
    angle = event.angleDelta().y()
    factor = 1.25 if angle > 0 else 0.8

    cursor_pos = event.position()
    cursor_img_pos = map_to_image_space(cursor_pos,contour_editor.translation,contour_editor.scale_factor)
    contour_editor.scale_factor *= factor

    # Update translation to zoom towards cursor
    new_cursor_screen_pos = cursor_img_pos * contour_editor.scale_factor + contour_editor.translation
    contour_editor.translation += cursor_pos - new_cursor_screen_pos

