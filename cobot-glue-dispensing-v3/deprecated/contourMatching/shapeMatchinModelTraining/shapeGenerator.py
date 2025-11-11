import numpy as np
import cv2

def generate_shape(shape_type, scale=1.0, img_size=(256, 256)):
    """Generate a single shape contour with specified type and scale"""
    img = np.zeros(img_size, dtype=np.uint8)
    h, w = img_size
    cx, cy = w // 2, h // 2
    base = int(50 * min(scale, 2.0))  # Cap scale to avoid shapes too large

    if shape_type == "circle":
        cv2.circle(img, (cx, cy), base, 255, -1)

    elif shape_type == "ellipse":
        cv2.ellipse(img, (cx, cy), (base, int(base * 0.6)), 0, 0, 360, 255, -1)

    elif shape_type == "rectangle":
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy + base), 255, -1)

    elif shape_type == "square":
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy + base), 255, -1)

    elif shape_type == "triangle":
        pts = np.array([[cx, cy - base], [cx - base, cy + base], [cx + base, cy + base]])
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "diamond":
        pts = np.array([[cx, cy - base], [cx + base, cy], [cx, cy + base], [cx - base, cy]])
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "hexagon":
        pts = np.array([
            [cx + int(base * np.cos(a)), cy + int(base * np.sin(a))]
            for a in np.linspace(0, 2 * np.pi, 6, endpoint=False)
        ], np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)

    # Add similar-looking hard negative shapes
    elif shape_type == "oval":  # Similar to circle but different
        cv2.ellipse(img, (cx, cy), (base, int(base * 0.8)), 0, 0, 360, 255, -1)

    elif shape_type == "rounded_rect":  # Similar to rectangle but different
        # Create rounded rectangle
        cv2.rectangle(img, (cx - base, cy - base // 2), (cx + base, cy + base // 2), 255, -1)
        cv2.circle(img, (cx - base, cy), base // 2, 255, -1)
        cv2.circle(img, (cx + base, cy), base // 2, 255, -1)

    elif shape_type == "rounded_corner_rect":  # Rectangle with one rounded corner
        # Create rectangle with one rounded corner (top-right)
        # Main rectangle body
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy + base), 255, -1)
        
        # Remove the top-right corner
        corner_size = base // 3
        cv2.rectangle(img, (cx + base - corner_size, cy - base), (cx + base, cy - base + corner_size), 0, -1)
        
        # Add rounded corner
        cv2.circle(img, (cx + base - corner_size, cy - base + corner_size), corner_size, 255, -1)

    elif shape_type == "pentagon":  # Similar to hexagon but different
        pts = np.array([
            [cx + int(base * np.cos(a)), cy + int(base * np.sin(a))]
            for a in np.linspace(0, 2 * np.pi, 5, endpoint=False)
        ], np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "octagon":  # Similar to circle but different
        pts = np.array([
            [cx + int(base * np.cos(a)), cy + int(base * np.sin(a))]
            for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ], np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)


    elif shape_type == "star":
        pts = []
        for i in range(5):
            outer = base
            inner = base // 2
            angle = i * (2 * np.pi / 5)
            pts.append([cx + int(outer * np.cos(angle)), cy + int(outer * np.sin(angle))])
            pts.append([cx + int(inner * np.cos(angle + np.pi / 5)), cy + int(inner * np.sin(angle + np.pi / 5))])
        pts = np.array(pts)
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "cross":
        # Vertical bar
        cv2.rectangle(img, (cx - base // 3, cy - base), (cx + base // 3, cy + base), 255, -1)
        # Horizontal bar
        cv2.rectangle(img, (cx - base, cy - base // 3), (cx + base, cy + base // 3), 255, -1)

    elif shape_type == "t_shape":
        # Top horizontal bar
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy - base // 2), 255, -1)
        # Vertical stem
        cv2.rectangle(img, (cx - base // 3, cy - base // 2), (cx + base // 3, cy + base), 255, -1)

    elif shape_type == "l_shape":
        # Vertical part
        cv2.rectangle(img, (cx - base, cy - base), (cx - base // 2, cy + base), 255, -1)
        # Horizontal part
        cv2.rectangle(img, (cx - base, cy + base // 2), (cx + base // 2, cy + base), 255, -1)

    elif shape_type == "s_shape":
        # Create S shape using curves
        pts = []
        for t in np.linspace(0, 1, 30):
            # S curve parametric equations
            x = cx + int(base * np.sin(t * 2 * np.pi))
            y = cy + int((t - 0.5) * 2 * base)
            pts.append([x, y])
        pts = np.array(pts, np.int32)
        thickness = max(base // 3, 5)  # Ensure sufficient thickness
        cv2.polylines(img, [pts], False, 255, thickness=thickness)

    elif shape_type == "c_shape":
        # Create C shape using arc
        thickness = max(base // 3, 5)  # Ensure sufficient thickness
        cv2.ellipse(img, (cx, cy), (base, base), 0, 30, 330, 255, thickness=thickness)

    elif shape_type == "u_shape":
        # Create U shape
        thickness = max(base // 3, 5)  # Ensure sufficient thickness
        cv2.ellipse(img, (cx, cy + base // 2), (base // 2, base // 2), 0, 0, 180, 255, thickness=thickness)
        cv2.rectangle(img, (cx - base // 2, cy - base // 2), (cx - base // 3, cy + base // 2), 255, -1)
        cv2.rectangle(img, (cx + base // 3, cy - base // 2), (cx + base // 2, cy + base // 2), 255, -1)

    elif shape_type == "arrow":
        # Arrow pointing right
        pts = np.array([
            [cx - base, cy - base // 3], [cx, cy - base // 3],
            [cx, cy - base], [cx + base, cy],
            [cx, cy + base], [cx, cy + base // 3],
            [cx - base, cy + base // 3]
        ])
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "heart":
        # Simple heart shape
        pts = []
        for t in np.linspace(0, 2 * np.pi, 100):
            x = 16 * np.sin(t) ** 3
            y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
            pts.append([cx + int(x * scale), cy - int(y * scale)])
        pts = np.array(pts, np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "crescent":
        # Moon/crescent shape
        cv2.circle(img, (cx, cy), base, 255, -1)
        # Ensure the inner circle doesn't completely remove the outer circle
        offset = max(base // 4, 5)  # Smaller offset
        inner_radius = max(int(base * 0.6), 8)  # Smaller inner circle, with minimum size
        cv2.circle(img, (cx + offset, cy), inner_radius, 0, -1)  # Subtract smaller circle

    elif shape_type == "trapezoid":
        pts = np.array([
            [cx - base, cy + base], [cx + base, cy + base],
            [cx + base // 2, cy - base], [cx - base // 2, cy - base]
        ])
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "parallelogram":
        offset = base // 3
        pts = np.array([
            [cx - base + offset, cy - base], [cx + base + offset, cy - base],
            [cx + base - offset, cy + base], [cx - base - offset, cy + base]
        ])
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "hourglass":
        # Top triangle
        pts1 = np.array([[cx - base, cy - base], [cx + base, cy - base], [cx, cy]])
        cv2.drawContours(img, [pts1], 0, 255, -1)
        # Bottom triangle
        pts2 = np.array([[cx - base, cy + base], [cx + base, cy + base], [cx, cy]])
        cv2.drawContours(img, [pts2], 0, 255, -1)

    elif shape_type == "donut":
        # Ring/donut shape
        cv2.circle(img, (cx, cy), base, 255, -1)
        inner_radius = max(base // 3, 5)  # Ensure inner circle isn't too large
        cv2.circle(img, (cx, cy), inner_radius, 0, -1)  # Inner circle

    elif shape_type == "gear":
        # Simple gear shape
        pts = []
        for i in range(8):
            angle = i * np.pi / 4
            # Outer teeth
            outer_x = cx + int((base + 10) * np.cos(angle))
            outer_y = cy + int((base + 10) * np.sin(angle))
            pts.append([outer_x, outer_y])
            # Inner valleys
            inner_angle = angle + np.pi / 8
            inner_x = cx + int(base * np.cos(inner_angle))
            inner_y = cy + int(base * np.sin(inner_angle))
            pts.append([inner_x, inner_y])
        pts = np.array(pts, np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)

    elif shape_type == "lightning":
        # Lightning bolt shape
        pts = np.array([
            [cx - base // 2, cy - base], [cx + base // 4, cy - base],
            [cx - base // 4, cy], [cx + base // 2, cy],
            [cx - base // 4, cy + base], [cx - base // 2, cy + base // 2],
            [cx + base // 4, cy - base // 4]
        ])
        cv2.drawContours(img, [pts], 0, 255, -1)

    else:
        raise NotImplementedError(f"Shape {shape_type} not implemented")

    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError(f"No contours found for shape type: {shape_type}")
    return max(contours, key=cv2.contourArea)