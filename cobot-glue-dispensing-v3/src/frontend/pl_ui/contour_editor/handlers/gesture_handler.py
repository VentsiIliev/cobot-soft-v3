from PyQt6.QtCore import Qt


def handle_gesture_event(contour_editor, event):
    # Handle pinch gesture
    pinch = event.gesture(Qt.GestureType.PinchGesture)
    if pinch:
        if pinch.state() == Qt.GestureState.GestureStarted:
            contour_editor._initial_scale = contour_editor.scale_factor
        elif pinch.state() == Qt.GestureState.GestureUpdated:
            total_scale_factor = pinch.totalScaleFactor()
            center = pinch.centerPoint()
            old_scale = contour_editor.scale_factor
            image_point_under_fingers = (center - contour_editor.translation) / old_scale
            contour_editor.scale_factor = contour_editor._initial_scale * total_scale_factor
            contour_editor.scale_factor = max(0.1, min(contour_editor.scale_factor, 20.0))
            contour_editor.translation = center - image_point_under_fingers * contour_editor.scale_factor
            contour_editor.update()
        elif pinch.state() == Qt.GestureState.GestureFinished:
            pass