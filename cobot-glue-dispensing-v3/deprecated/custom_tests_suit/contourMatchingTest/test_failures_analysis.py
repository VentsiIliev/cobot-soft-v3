"""
Analyze the specific failures after retraining the model.
"""
import cv2
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from find_matching_workpieces_script import (
    create_rectangle_contour,
    create_rounded_rectangle_contour,
    create_c_shape_contour,
    create_slider_straight_contour,
    create_convex_blob_contour,
    create_concave_blob_contour,
    render_contour_to_canvas,
    rotate_contour,
    translate_contour,
)
from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import predict_similarity, load_latest_model


def test_shape_pair(name1, func1, name2, func2, should_match, rotation=45, translation=(35, 30)):
    """Test a specific shape pair and report ML model decision."""
    print(f"\n{'='*70}")
    print(f"Testing: {name1} vs {name2}")
    print(f"Expected: {'MATCH' if should_match else 'NO MATCH'}")
    print(f"{'='*70}")

    # Generate contours
    c1 = func1(center=(400, 300))
    c1 = render_contour_to_canvas(c1, canvas_size=(1280, 720))

    c2 = func2(center=(400, 300))
    c2 = rotate_contour(c2, rotation)
    c2 = translate_contour(c2, *translation)
    c2 = render_contour_to_canvas(c2, canvas_size=(1280, 720))

    print(f"  {name1}: {len(c1)} points, area={cv2.contourArea(c1):.1f}px²")
    print(f"  {name2}: {len(c2)} points, area={cv2.contourArea(c2):.1f}px²")

    # Load model and predict
    model = load_latest_model(
        save_dir="/system/contourMatching/shapeMatchinModelTraining/saved_models"
    )

    result, confidence, features = predict_similarity(model, c1, c2)

    print(f"\n  ML Model Result: {result}")
    print(f"  Confidence: {confidence:.1%}")

    # Determine if test passes
    actual_match = (result == "SAME")
    test_passed = (actual_match == should_match)

    if test_passed:
        print(f"  ✓ TEST PASSED")
    else:
        if should_match:
            print(f"  ✗ TEST FAILED - Should match but model says DIFFERENT")
        else:
            print(f"  ✗ TEST FAILED - Should NOT match but model says SAME")

    return test_passed, result, confidence


def main():
    """Analyze all the current failures."""

    print("="*70)
    print("FAILURE ANALYSIS - Testing failed cases")
    print("="*70)

    test_cases = [
        # Failed tests based on file names in failed_tests folder
        ("Rectangle", create_rectangle_contour, "Rectangle", create_rectangle_contour, True, 30, (40, 25)),
        ("C-Shape", create_c_shape_contour, "C-Shape", create_c_shape_contour, True, 90, (35, 30)),
        ("Rounded Rect", create_rounded_rectangle_contour, "Rounded Rect", create_rounded_rectangle_contour, True, 45, (35, 30)),
        ("Straight Slider", create_slider_straight_contour, "Straight Slider", create_slider_straight_contour, True, 60, (40, 30)),
        ("Convex Blob", create_convex_blob_contour, "Concave Blob", create_concave_blob_contour, False, 45, (35, 30)),
    ]

    results = []
    for name1, func1, name2, func2, should_match, rotation, translation in test_cases:
        passed, result, confidence = test_shape_pair(name1, func1, name2, func2, should_match, rotation, translation)
        results.append({
            'test': f"{name1} vs {name2}",
            'expected': 'MATCH' if should_match else 'NO MATCH',
            'actual': result,
            'confidence': confidence,
            'passed': passed
        })

    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Test':<40} {'Expected':<12} {'Actual':<12} {'Conf':<8} {'Result'}")
    print(f"{'-'*70}")

    for r in results:
        status = "✓ PASS" if r['passed'] else "✗ FAIL"
        print(f"{r['test']:<40} {r['expected']:<12} {r['actual']:<12} {r['confidence']:>6.1%}  {status}")

    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nPassed: {passed_count}/{len(results)} ({passed_count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    main()