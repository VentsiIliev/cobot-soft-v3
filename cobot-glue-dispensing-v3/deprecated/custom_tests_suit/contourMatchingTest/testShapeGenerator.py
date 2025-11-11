import numpy as np

from API.shared.Contour import Contour


def create_rectangle_contour(center=(400, 300), width=200, height=100):
    """Create a simple rectangular contour."""
    x, y = center
    points = np.array([
        [x - width//2, y - height//2],
        [x + width//2, y - height//2],
        [x + width//2, y + height//2],
        [x - width//2, y + height//2]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_triangle_contour(center=(400, 300), size=150):
    """Create a triangular contour."""
    x, y = center
    height = size * np.sqrt(3) / 2
    points = np.array([
        [x, y - 2*height/3],
        [x + size/2, y + height/3],
        [x - size/2, y + height/3]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_cross_contour(center=(400, 300), arm_length=120, arm_width=40):
    """Create a cross/plus shaped contour."""
    x, y = center
    hw = arm_width // 2

    points = np.array([
        # Top arm
        [x - hw, y - arm_length],
        [x + hw, y - arm_length],
        [x + hw, y - hw],
        # Right arm
        [x + arm_length, y - hw],
        [x + arm_length, y + hw],
        [x + hw, y + hw],
        # Bottom arm
        [x + hw, y + arm_length],
        [x - hw, y + arm_length],
        [x - hw, y + hw],
        # Left arm
        [x - arm_length, y + hw],
        [x - arm_length, y - hw],
        [x - hw, y - hw]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_pentagon_contour(center=(400, 300), radius=100):
    """Create a regular pentagon contour."""
    x, y = center
    points = []
    for i in range(5):
        angle = 2 * np.pi * i / 5 - np.pi / 2  # Start from top
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_star_contour(center=(400, 300), outer_radius=100, inner_radius=40, points=5):
    """Create a star-shaped contour."""
    x, y = center
    angles = np.linspace(0, 2*np.pi, points*2, endpoint=False)
    radii = np.array([outer_radius if i % 2 == 0 else inner_radius for i in range(points*2)])

    star_points = []
    for angle, radius in zip(angles, radii):
        px = x + radius * np.cos(angle - np.pi/2)
        py = y + radius * np.sin(angle - np.pi/2)
        star_points.append([px, py])

    return np.array(star_points, dtype=np.float32).reshape(-1, 1, 2)


def create_hexagon_contour(center=(400, 300), radius=100):
    """Create a regular hexagon contour."""
    x, y = center
    points = []
    for i in range(6):
        angle = 2 * np.pi * i / 6
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_rounded_rectangle_contour(center=(400, 300), width=200, height=100, corner_radius=30):
    """Create a rectangle with rounded corners."""
    x, y = center
    hw, hh = width // 2, height // 2
    r = corner_radius

    points = []

    # Top edge (right to left, with rounded top-right corner)
    for angle in np.linspace(0, np.pi/2, 10):
        px = x + hw - r + r * np.cos(angle)
        py = y - hh + r - r * np.sin(angle)
        points.append([px, py])

    # Left edge (top to bottom, with rounded top-left corner)
    for angle in np.linspace(np.pi/2, np.pi, 10):
        px = x - hw + r + r * np.cos(angle)
        py = y - hh + r - r * np.sin(angle)
        points.append([px, py])

    # Bottom edge (left to right, with rounded bottom-left corner)
    for angle in np.linspace(np.pi, 3*np.pi/2, 10):
        px = x - hw + r + r * np.cos(angle)
        py = y + hh - r - r * np.sin(angle)
        points.append([px, py])

    # Right edge (bottom to top, with rounded bottom-right corner)
    for angle in np.linspace(3*np.pi/2, 2*np.pi, 10):
        px = x + hw - r + r * np.cos(angle)
        py = y + hh - r - r * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_half_circle_contour(center=(400, 300), radius=100, orientation='top'):
    """Create a half circle (semicircle)."""
    x, y = center
    points = []

    if orientation == 'top':
        # Top half: from left to right (π to 0)
        for angle in np.linspace(np.pi, 0, 50):
            px = x + radius * np.cos(angle)
            py = y + radius * np.sin(angle)
            points.append([px, py])
        # Close with straight line
        points.append([x + radius, y])
        points.append([x - radius, y])
    elif orientation == 'bottom':
        # Bottom half: from right to left (0 to π)
        for angle in np.linspace(0, np.pi, 50):
            px = x + radius * np.cos(angle)
            py = y + radius * np.sin(angle)
            points.append([px, py])
        points.append([x - radius, y])
        points.append([x + radius, y])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_slider_straight_contour(center=(400, 300), length=200, width=60, slider_width=40, slider_height=80):
    """Create a straight slider shape (track with slider head)."""
    x, y = center
    hw = width // 2
    sw = slider_width // 2
    sh = slider_height // 2

    points = np.array([
        # Track - right side
        [x + length//2, y + hw],
        [x + length//2, y - hw],
        # Transition to slider head
        [x + sw, y - hw],
        # Slider head - top
        [x + sw, y - sh],
        [x - sw, y - sh],
        # Slider head - left side
        [x - sw, y - hw],
        # Track - left side
        [x - length//2, y - hw],
        [x - length//2, y + hw],
        # Transition back
        [x - sw, y + hw],
        # Slider head - bottom
        [x - sw, y + sh],
        [x + sw, y + sh],
        # Close slider head
        [x + sw, y + hw],
    ], dtype=np.float32)

    return points.reshape(-1, 1, 2)


def create_slider_curved_contour(center=(400, 300), radius=80, width=40, slider_size=60):
    """Create a curved slider (circular track with slider)."""
    x, y = center
    points = []

    # Outer arc (0 to π)
    for angle in np.linspace(0, np.pi, 30):
        px = x + (radius + width//2) * np.cos(angle)
        py = y + (radius + width//2) * np.sin(angle)
        points.append([px, py])

    # Slider head at top
    slider_x = x - radius
    for angle in np.linspace(0, 2*np.pi, 20):
        px = slider_x + slider_size//2 * np.cos(angle)
        py = y + slider_size//2 * np.sin(angle)
        points.append([px, py])

    # Inner arc (π to 0, reversed)
    for angle in np.linspace(np.pi, 0, 30):
        px = x + (radius - width//2) * np.cos(angle)
        py = y + (radius - width//2) * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_convex_blob_contour(center=(400, 300), base_radius=100, num_bumps=8):
    """Create a blob with convex bumps (all outward) - MORE OBVIOUS."""
    x, y = center
    points = []

    for i in range(num_bumps * 10):
        angle = 2 * np.pi * i / (num_bumps * 10)
        # Vary radius to create LARGER bumps (increased from 20 to 40)
        radius_variation = base_radius + 40 * np.sin(num_bumps * angle)
        px = x + radius_variation * np.cos(angle)
        py = y + radius_variation * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_concave_blob_contour(center=(400, 300), base_radius=100, num_indents=6):
    """Create a blob with concave indents (all inward) - MORE OBVIOUS DEEP INDENTS."""
    x, y = center
    points = []

    for i in range(num_indents * 10):
        angle = 2 * np.pi * i / (num_indents * 10)
        # Vary radius to create DEEPER indents (increased from 20 to 50)
        # This creates much more pronounced concave sections
        radius_variation = base_radius - 50 * np.sin(num_indents * angle)
        px = x + radius_variation * np.cos(angle)
        py = y + radius_variation * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_gear_advanced_contour(center=(400, 300), inner_radius=60, outer_radius=100, teeth=12):
    """Create an advanced gear shape with more teeth."""
    x, y = center
    points = []

    for i in range(teeth * 2):
        angle = 2 * np.pi * i / (teeth * 2)
        radius = outer_radius if i % 2 == 0 else inner_radius
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_l_shape_advanced_contour(center=(400, 300), width=180, height=180, thickness=60):
    """Create an advanced L-shape with specific dimensions."""
    x, y = center

    points = np.array([
        # Outer corner
        [x - width//2, y - height//2],
        [x + width//2, y - height//2],
        [x + width//2, y - height//2 + thickness],
        [x - width//2 + thickness, y - height//2 + thickness],
        [x - width//2 + thickness, y + height//2],
        [x - width//2, y + height//2],
    ], dtype=np.float32)

    return points.reshape(-1, 1, 2)


def create_u_shape_advanced_contour(center=(400, 300), width=180, height=150, thickness=50):
    """Create an advanced U-shape."""
    x, y = center
    hw, hh = width // 2, height // 2
    t = thickness

    points = np.array([
        # Outer left
        [x - hw, y - hh],
        [x - hw, y + hh],
        [x + hw, y + hh],
        [x + hw, y - hh],
        # Inner right
        [x + hw - t, y - hh],
        [x + hw - t, y + hh - t],
        # Inner bottom
        [x - hw + t, y + hh - t],
        # Inner left
        [x - hw + t, y - hh],
    ], dtype=np.float32)

    return points.reshape(-1, 1, 2)


def create_trapezoid_contour(center=(400, 300), top_width=120, bottom_width=200, height=120):
    """Create a trapezoid shape."""
    x, y = center
    tw, bw = top_width // 2, bottom_width // 2
    hh = height // 2

    points = np.array([
        [x - tw, y - hh],  # Top left
        [x + tw, y - hh],  # Top right
        [x + bw, y + hh],  # Bottom right
        [x - bw, y + hh],  # Bottom left
    ], dtype=np.float32)

    return points.reshape(-1, 1, 2)


def create_diamond_contour(center=(400, 300), width=150, height=200):
    """Create a diamond (rhombus) shape."""
    x, y = center
    hw, hh = width // 2, height // 2

    points = np.array([
        [x, y - hh],      # Top
        [x + hw, y],      # Right
        [x, y + hh],      # Bottom
        [x - hw, y],      # Left
    ], dtype=np.float32)

    return points.reshape(-1, 1, 2)


def create_ellipse_contour(center=(400, 300), width=200, height=120):
    """Create an ellipse shape."""
    x, y = center
    points = []

    for i in range(100):
        angle = 2 * np.pi * i / 100
        px = x + (width // 2) * np.cos(angle)
        py = y + (height // 2) * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_crescent_contour(center=(400, 300), outer_radius=100, inner_radius=80, offset=30):
    """Create a crescent moon shape."""
    x, y = center
    points = []

    # Outer circle
    for angle in np.linspace(0, 2*np.pi, 50):
        px = x + outer_radius * np.cos(angle)
        py = y + outer_radius * np.sin(angle)
        points.append([px, py])

    # Inner circle (offset to create crescent) - reverse direction
    for angle in np.linspace(2*np.pi, 0, 50):
        px = x + offset + inner_radius * np.cos(angle)
        py = y + inner_radius * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_hourglass_contour(center=(400, 300), width=100, height=200, waist=40):
    """Create an hourglass shape."""
    x, y = center
    points = []

    # Top half
    for i in range(25):
        t = i / 24
        py = y - height//2 + t * height//2
        px_offset = width//2 - (width//2 - waist//2) * t
        points.append([x - px_offset, py])

    # Bottom half
    for i in range(25):
        t = i / 24
        py = y + t * height//2
        px_offset = waist//2 + (width//2 - waist//2) * t
        points.append([x - px_offset, py])

    # Right side (mirror)
    for i in range(len(points) - 1, -1, -1):
        px, py = points[i]
        points.append([2*x - px, py])

    return np.array(points[:50], dtype=np.float32).reshape(-1, 1, 2)


def create_keyhole_contour(center=(400, 300), circle_radius=60, slot_width=40, slot_height=80):
    """Create a keyhole shape."""
    x, y = center
    points = []

    # Circle part (top)
    for angle in np.linspace(0, 2*np.pi, 40):
        px = x + circle_radius * np.cos(angle)
        py = y - slot_height//2 + circle_radius * np.sin(angle)
        points.append([px, py])

    # Rectangular slot (bottom)
    sw = slot_width // 2
    points.extend([
        [x + sw, y],
        [x + sw, y + slot_height//2],
        [x - sw, y + slot_height//2],
        [x - sw, y],
    ])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_pac_man_contour(center=(400, 300), radius=100, mouth_angle=60):
    """Create a pac-man shape (circle with wedge cut out)."""
    x, y = center
    points = []

    # Start from center
    points.append([x, y])

    # Arc around (skipping the mouth)
    mouth_rad = np.deg2rad(mouth_angle)
    for angle in np.linspace(mouth_rad/2, 2*np.pi - mouth_rad/2, 50):
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])

    # Back to center
    points.append([x, y])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_c_shape_contour(center=(400, 300), outer_radius=100, inner_radius=70, opening_angle=90):
    """Create a C-shaped contour (arc with opening)."""
    x, y = center
    points = []

    # Opening angle in radians
    opening_rad = np.deg2rad(opening_angle)
    start_angle = opening_rad / 2
    end_angle = 2 * np.pi - opening_rad / 2

    # Outer arc
    for angle in np.linspace(start_angle, end_angle, 40):
        px = x + outer_radius * np.cos(angle)
        py = y + outer_radius * np.sin(angle)
        points.append([px, py])

    # Inner arc (reversed)
    for angle in np.linspace(end_angle, start_angle, 40):
        px = x + inner_radius * np.cos(angle)
        py = y + inner_radius * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def rotate_contour(contour, angle_degrees, center=None):
    """Rotate a contour by a given angle."""
    contour_obj = Contour(contour)
    if center is None:
        center = contour_obj.getCentroid()
    contour_obj.rotate(angle_degrees, center)
    return contour_obj.get_contour_points()


def translate_contour(contour, dx, dy):
    """Translate a contour by dx, dy."""
    contour_obj = Contour(contour)
    contour_obj.translate(dx, dy)
    return contour_obj.get_contour_points()


def scale_contour(contour, scale_factor, center=None):
    """Scale a contour by a given factor around a center point."""
    contour_obj = Contour(contour)
    if center is None:
        center = contour_obj.getCentroid()

    # Get contour points
    points = contour_obj.get_contour_points().squeeze()
    if points.ndim == 1:
        points = points.reshape(-1, 2)

    # Scale around center
    scaled_points = []
    for point in points:
        # Translate to origin
        translated = point - np.array(center)
        # Scale
        scaled = translated * scale_factor
        # Translate back
        final = scaled + np.array(center)
        scaled_points.append(final)

    return np.array(scaled_points, dtype=np.float32).reshape(-1, 1, 2)