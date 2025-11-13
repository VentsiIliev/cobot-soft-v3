import cv2

def apply_rotation(contours, angle, pivot):
    for c in contours:
        c.rotate(angle, pivot)

def apply_translation(contours, dx, dy):
    for c in contours:
        c.translate(dx, dy)