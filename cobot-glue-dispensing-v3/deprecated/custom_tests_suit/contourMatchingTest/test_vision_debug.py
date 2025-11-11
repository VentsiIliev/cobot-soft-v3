"""
Quick diagnostic script to understand vision system simulation impact on contours.
"""
import cv2
import numpy as np
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from find_matching_workpieces_script import (
    create_rectangle_contour,
    create_cross_contour,
    create_l_shape_advanced_contour,
    create_u_shape_advanced_contour,

    create_slider_straight_contour,
    create_convex_blob_contour,
    create_gear_advanced_contour,
    render_contour_to_canvas
)


def analyze_contour_processing(name, contour_func):
    """Analyze how vision system processing affects a contour."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    # Create original contour
    original = contour_func(center=(400, 300))
    print(f"\nOriginal contour:")
    print(f"  Points: {len(original)}")
    print(f"  Area: {cv2.contourArea(original):.1f} px²")

    # Get bounds
    orig_pts = original.reshape(-1, 2)
    orig_min = orig_pts.min(axis=0)
    orig_max = orig_pts.max(axis=0)
    print(f"  Bounds: ({orig_min[0]:.1f}, {orig_min[1]:.1f}) to ({orig_max[0]:.1f}, {orig_max[1]:.1f})")
    print(f"  Size: {orig_max[0] - orig_min[0]:.1f} x {orig_max[1] - orig_min[1]:.1f}")

    # Process through vision system
    try:
        processed = render_contour_to_canvas(original, canvas_size=(1280, 720))
        print(f"\nAfter vision system (CHAIN_APPROX_SIMPLE):")
        print(f"  Points: {len(processed)} (reduced by {len(original) - len(processed)})")
        print(f"  Area: {cv2.contourArea(processed):.1f} px²")

        # Get processed bounds
        proc_pts = processed.reshape(-1, 2)
        proc_min = proc_pts.min(axis=0)
        proc_max = proc_pts.max(axis=0)
        print(f"  Bounds: ({proc_min[0]:.1f}, {proc_min[1]:.1f}) to ({proc_max[0]:.1f}, {proc_max[1]:.1f})")
        print(f"  Size: {proc_max[0] - proc_min[0]:.1f} x {proc_max[1] - proc_min[1]:.1f}")

        # Calculate differences
        area_diff = abs(cv2.contourArea(original) - cv2.contourArea(processed))
        area_diff_pct = (area_diff / cv2.contourArea(original)) * 100
        point_reduction_pct = ((len(original) - len(processed)) / len(original)) * 100

        print(f"\nDifferences:")
        print(f"  Area change: {area_diff:.1f} px² ({area_diff_pct:.2f}%)")
        print(f"  Point reduction: {point_reduction_pct:.1f}%")

        # Check coordinate precision loss
        orig_has_floats = np.any(orig_pts != orig_pts.astype(int))
        proc_has_floats = np.any(proc_pts != proc_pts.astype(int))
        print(f"  Original has sub-pixel coords: {orig_has_floats}")
        print(f"  Processed has sub-pixel coords: {proc_has_floats}")

        return {
            'success': True,
            'original_points': len(original),
            'processed_points': len(processed),
            'area_diff_pct': area_diff_pct,
            'point_reduction_pct': point_reduction_pct
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Run diagnostic analysis on all failing shapes."""

    test_shapes = [
        ("Rectangle", create_rectangle_contour),
        ("Cross", create_cross_contour),
        ("L-Shape", create_l_shape_advanced_contour),
        ("U-Shape", create_u_shape_advanced_contour),
        ("Straight Slider", create_slider_straight_contour),
        ("Convex Blob", create_convex_blob_contour),
        ("Gear", create_gear_advanced_contour),
    ]

    results = []
    for name, func in test_shapes:
        result = analyze_contour_processing(name, func)
        result['name'] = name
        results.append(result)

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Shape':<20} {'Points':<15} {'Area Diff %':<15} {'Point Red %':<15}")
    print(f"{'-'*60}")

    for r in results:
        if r['success']:
            print(f"{r['name']:<20} {r['original_points']:>4} -> {r['processed_points']:<4} "
                  f"{r['area_diff_pct']:>8.2f}%      {r['point_reduction_pct']:>8.1f}%")
        else:
            print(f"{r['name']:<20} ERROR: {r['error']}")

    print("\n")


if __name__ == "__main__":
    main()