"""
Test script for align contour function in CompareContours.py

This script creates various test contour shapes (convex, concave, complex)
and tests the alignment functionality.
"""

import numpy as np
import cv2
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GlueDispensingApplication.CompareContours import _alignContours, _calculateDifferences
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
    """Create a triangular contour (convex)."""
    x, y = center
    height = size * np.sqrt(3) / 2
    points = np.array([
        [x, y - 2*height/3],
        [x + size/2, y + height/3],
        [x - size/2, y + height/3]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_l_shape_contour(center=(400, 300), size=150):
    """Create an L-shaped contour (concave)."""
    x, y = center
    points = np.array([
        [x - size//2, y - size//2],
        [x, y - size//2],
        [x, y],
        [x + size//2, y],
        [x + size//2, y + size//2],
        [x - size//2, y + size//2]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_star_contour(center=(400, 300), outer_radius=100, inner_radius=40, points=5):
    """Create a star-shaped contour (concave with multiple defects)."""
    x, y = center
    angles = np.linspace(0, 2*np.pi, points*2, endpoint=False)
    radii = np.array([outer_radius if i % 2 == 0 else inner_radius for i in range(points*2)])

    star_points = []
    for angle, radius in zip(angles, radii):
        px = x + radius * np.cos(angle - np.pi/2)
        py = y + radius * np.sin(angle - np.pi/2)
        star_points.append([px, py])

    return np.array(star_points, dtype=np.float32).reshape(-1, 1, 2)


def create_c_shape_contour(center=(400, 300), outer_radius=100, inner_radius=70, gap_angle=90):
    """Create a C-shaped contour (concave arc)."""
    x, y = center
    angles = np.linspace(gap_angle/2, 360 - gap_angle/2, 50) * np.pi / 180

    # Outer arc
    outer_points = [[x + outer_radius * np.cos(a), y + outer_radius * np.sin(a)] for a in angles]

    # Inner arc (reverse direction)
    inner_points = [[x + inner_radius * np.cos(a), y + inner_radius * np.sin(a)] for a in reversed(angles)]

    all_points = outer_points + inner_points
    return np.array(all_points, dtype=np.float32).reshape(-1, 1, 2)


def create_cross_contour(center=(400, 300), arm_length=120, arm_width=40):
    """Create a cross/plus shaped contour (concave)."""
    x, y = center
    hw = arm_width // 2  # half width

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


def create_u_shape_contour(center=(400, 300), width=150, height=180, thickness=30):
    """Create a U-shaped contour (concave)."""
    x, y = center
    outer_points = [
        [x - width//2, y - height//2],
        [x + width//2, y - height//2],
        [x + width//2, y + height//2],
        [x - width//2, y + height//2]
    ]

    inner_points = [
        [x - width//2 + thickness, y - height//2 + thickness],
        [x - width//2 + thickness, y + height//2 - thickness],
        [x + width//2 - thickness, y + height//2 - thickness],
        [x + width//2 - thickness, y - height//2 + thickness]
    ]

    # Combine to form U shape (skip top of inner rectangle)
    u_points = [
        outer_points[0],  # top-left
        outer_points[1],  # top-right
        outer_points[2],  # bottom-right
        inner_points[2],  # inner bottom-right
        inner_points[1],  # inner bottom-left
        inner_points[0],  # inner top-left
        outer_points[3]   # bottom-left
    ]

    return np.array(u_points, dtype=np.float32).reshape(-1, 1, 2)


def create_heart_contour(center=(400, 300), size=100):
    """Create a heart-shaped contour (complex concave)."""
    x, y = center
    t = np.linspace(0, 2*np.pi, 100)

    # Parametric heart equation
    heart_x = 16 * np.sin(t)**3
    heart_y = -(13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t))

    # Scale and translate
    scale = size / 20
    heart_points = [[x + hx * scale, y + hy * scale] for hx, hy in zip(heart_x, heart_y)]

    return np.array(heart_points, dtype=np.float32).reshape(-1, 1, 2)


def create_gear_contour(center=(400, 300), outer_radius=100, inner_radius=80, teeth=8):
    """Create a gear-shaped contour (multiple concave sections)."""
    x, y = center
    points = []

    tooth_width = 2 * np.pi / teeth / 4

    for i in range(teeth):
        base_angle = 2 * np.pi * i / teeth

        # Outer tooth points
        angles = [
            base_angle - tooth_width,
            base_angle,
            base_angle + tooth_width
        ]

        for angle in angles:
            px = x + outer_radius * np.cos(angle)
            py = y + outer_radius * np.sin(angle)
            points.append([px, py])

        # Inner valley point
        valley_angle = base_angle + 2 * np.pi / teeth / 2
        px = x + inner_radius * np.cos(valley_angle)
        py = y + inner_radius * np.sin(valley_angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_arrow_contour(center=(400, 300), length=150, width=60, head_width=120):
    """Create an arrow-shaped contour (concave)."""
    x, y = center
    hw = width // 2
    hhw = head_width // 2
    head_length = length // 3

    points = np.array([
        # Arrow tip
        [x + length//2, y],
        # Right side of head
        [x + length//2 - head_length, y - hhw],
        [x + length//2 - head_length, y - hw],
        # Right side of shaft
        [x - length//2, y - hw],
        # Left side of shaft
        [x - length//2, y + hw],
        [x + length//2 - head_length, y + hw],
        # Left side of head
        [x + length//2 - head_length, y + hhw]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_pentagon_contour(center=(400, 300), radius=100):
    """Create a regular pentagon contour (5-fold symmetry)."""
    x, y = center
    points = []
    for i in range(5):
        angle = 2 * np.pi * i / 5 - np.pi / 2  # Start from top
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_hexagon_contour(center=(400, 300), radius=100):
    """Create a regular hexagon contour (6-fold symmetry)."""
    x, y = center
    points = []
    for i in range(6):
        angle = 2 * np.pi * i / 6
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_octagon_contour(center=(400, 300), radius=100):
    """Create a regular octagon contour (8-fold symmetry)."""
    x, y = center
    points = []
    for i in range(8):
        angle = 2 * np.pi * i / 8
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_t_shape_contour(center=(400, 300), top_width=180, stem_width=60, top_height=50, stem_height=130):
    """Create a T-shaped contour (asymmetric concave)."""
    x, y = center
    tw_half = top_width // 2
    sw_half = stem_width // 2

    # Calculate positions to center the T
    top_y = y - stem_height // 2
    bottom_y = y + stem_height // 2

    points = np.array([
        # Top left
        [x - tw_half, top_y],
        # Top right
        [x + tw_half, top_y],
        # Top right of stem
        [x + tw_half, top_y + top_height],
        [x + sw_half, top_y + top_height],
        # Bottom right of stem
        [x + sw_half, bottom_y],
        # Bottom left of stem
        [x - sw_half, bottom_y],
        # Top left of stem
        [x - sw_half, top_y + top_height],
        [x - tw_half, top_y + top_height]
    ], dtype=np.float32)
    return points.reshape(-1, 1, 2)


def create_spiral_contour(center=(400, 300), turns=2, start_radius=20, end_radius=100, points_per_turn=50):
    """Create a spiral-shaped contour (complex asymmetric)."""
    x, y = center
    total_points = int(turns * points_per_turn)
    points = []

    for i in range(total_points):
        t = i / points_per_turn  # Current turn number
        angle = 2 * np.pi * t
        radius = start_radius + (end_radius - start_radius) * (t / turns)

        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])

    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def create_irregular_polygon_contour(center=(400, 300), base_radius=100):
    """Create an irregular polygon with no symmetry."""
    x, y = center
    # Create irregular polygon by varying radius for each vertex
    radii = [base_radius * r for r in [1.0, 0.7, 1.2, 0.8, 1.1, 0.6, 0.9]]
    angles = [0, 40, 80, 130, 190, 250, 310]  # Irregular angles

    points = []
    for angle, radius in zip(angles, radii):
        rad = np.deg2rad(angle)
        px = x + radius * np.cos(rad)
        py = y + radius * np.sin(rad)
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


def create_workpiece_from_contour(contour, workpiece_id, name):
    """Create a mock workpiece object from a contour."""
    # Create a minimal workpiece structure
    workpiece = type('Workpiece', (), {
        'workpieceId': workpiece_id,
        'name': name,
        'contour': {'contour': contour, 'settings': {}},
        'sprayPattern': {'Contour': [], 'Fill': []},
        'get_main_contour': lambda self: contour,
        'get_spray_pattern_contours': lambda self: [],
        'get_spray_pattern_fills': lambda self: []
    })()
    return workpiece


def visualize_contours(original, transformed, title="Contour Alignment Test"):
    """Visualize original and transformed contours."""
    canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255

    # Draw original in blue
    orig_obj = Contour(original)
    orig_obj.draw(canvas, color=(255, 0, 0), thickness=2)

    # Draw transformed in red
    trans_obj = Contour(transformed)
    trans_obj.draw(canvas, color=(0, 0, 255), thickness=2)

    # Add legend
    cv2.putText(canvas, "Blue: Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(canvas, "Red: Aligned", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(canvas, title, (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    return canvas


def test_contour_alignment(contour_func, name, rotation=45, translation=(50, 30)):
    """Test alignment for a specific contour shape."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    # Create original contour
    original_contour = contour_func()
    print(f"Original contour points: {len(original_contour)}")

    # Create a transformed version (this simulates a detected contour)
    transformed = rotate_contour(original_contour.copy(), rotation)
    transformed = translate_contour(transformed, *translation)

    # Create workpiece from original
    workpiece = create_workpiece_from_contour(original_contour, f"WP_{name}", name)

    # Calculate differences
    orig_obj = Contour(original_contour)
    trans_obj = Contour(transformed)
    centroid_diff, rotation_diff, contour_angle = _calculateDifferences(orig_obj, trans_obj)

    print(f"Expected rotation: {rotation}°")
    print(f"Calculated rotation: {rotation_diff:.2f}°")
    print(f"Expected translation: {translation}")
    print(f"Calculated translation: ({centroid_diff[0]:.2f}, {centroid_diff[1]:.2f})")

    # Create match dictionary (simulating what findMatchingWorkpieces returns)
    match_dict = {
        "workpieces": workpiece,
        "newContour": transformed,
        "centroidDiff": centroid_diff,
        "rotationDiff": rotation_diff,
        "contourOrientation": contour_angle
    }

    # Test alignment
    result = _alignContours([match_dict], defectsThresh=5, debug=False)

    aligned_contour = result["workpieces"][0].contour["contour"]

    # Visualize
    canvas = visualize_contours(transformed, aligned_contour, f"{name} Alignment")

    # Save visualization
    output_dir = "test_align_outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"align_test_{name.replace(' ', '_')}.png")
    cv2.imwrite(output_path, canvas)
    print(f"Visualization saved to: {output_path}")

    # Calculate alignment error
    aligned_obj = Contour(aligned_contour)
    target_centroid = trans_obj.getCentroid()
    aligned_centroid = aligned_obj.getCentroid()
    centroid_error = np.linalg.norm(np.array(target_centroid) - np.array(aligned_centroid))

    print(f"Centroid alignment error: {centroid_error:.2f} pixels")

    if centroid_error < 5:
        print("[OK] Alignment SUCCESS - Error < 5 pixels")
    else:
        print("[WARN] Alignment WARNING - Error >= 5 pixels")

    return centroid_error


def main():
    """Run all contour alignment tests."""
    print("\n" + "="*60)
    print("CONTOUR ALIGNMENT TEST SUITE")
    print("="*60)

    # Define test cases: (function, name, rotation, translation)
    test_cases = [
        # Simple convex shapes
        (create_rectangle_contour, "Rectangle (Convex)", 30, (40, 25)),
        (create_triangle_contour, "Triangle (Convex)", 45, (50, 30)),
        (create_pentagon_contour, "Pentagon (5-Symmetry)", 72, (35, 30)),
        (create_hexagon_contour, "Hexagon (6-Symmetry)", 60, (40, 35)),
        (create_octagon_contour, "Octagon (8-Symmetry)", 45, (30, 40)),

        # Concave shapes
        (create_l_shape_contour, "L-Shape (Concave)", 60, (35, 40)),
        (create_u_shape_contour, "U-Shape (Concave)", 90, (30, 35)),
        (create_c_shape_contour, "C-Shape (Concave Arc)", 45, (45, 25)),
        (create_t_shape_contour, "T-Shape (Asymmetric)", 120, (40, 30)),

        # Complex shapes with multiple concave sections
        (create_star_contour, "Star (Multi-Concave)", 72, (40, 30)),
        (create_cross_contour, "Cross (Concave)", 46, (35, 35)),  # Test 46° rotation that was problematic
        (create_arrow_contour, "Arrow (Concave)", 30, (50, 20)),
        (create_gear_contour, "Gear (Multi-Concave)", 22.5, (40, 40)),
        (create_heart_contour, "Heart (Complex Concave)", 45, (30, 35)),
        (create_spiral_contour, "Spiral (Asymmetric)", 75, (25, 30)),
        (create_irregular_polygon_contour, "Irregular Polygon", 135, (30, 25)),
    ]

    errors = []

    for contour_func, name, rotation, translation in test_cases:
        try:
            error = test_contour_alignment(contour_func, name, rotation, translation)
            errors.append((name, error))
        except Exception as e:
            print(f"[ERROR] testing {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            errors.append((name, float('inf')))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, error in errors:
        status = "[PASS]" if error < 5 else "[WARN]" if error < 20 else "[FAIL]"
        print(f"{status} | {name:30s} | Error: {error:.2f} px")

    avg_error = np.mean([e for _, e in errors if e != float('inf')])
    print(f"\nAverage alignment error: {avg_error:.2f} pixels")

    print("\n" + "="*60)
    print("All tests completed!")
    print(f"Output images saved in: test_align_outputs/")
    print("="*60)


if __name__ == "__main__":
    main()
