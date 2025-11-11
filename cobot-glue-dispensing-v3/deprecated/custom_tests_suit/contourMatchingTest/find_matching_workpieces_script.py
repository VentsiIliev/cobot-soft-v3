"""
Test script for findMatchingWorkpieces function in CompareContours.py

This script creates mock workpieces and new contours, then tests the complete
matching and alignment functionality.
"""

import cv2
import sys
import os
import matplotlib.pyplot as plt

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from GlueDispensingApplication.CompareContours import findMatchingWorkpieces
from GlueDispensingApplication.workpiece.Workpiece import Workpiece
from GlueDispensingApplication.tools.enums.Program import Program
from GlueDispensingApplication.tools.enums.ToolID import ToolID
from GlueDispensingApplication.tools.GlueCell import GlueType
from GlueDispensingApplication.tools.enums.Gripper import Gripper
from custom_tests_suit.contourMatchingTest.testShapeGenerator import *
from custom_tests_suit.contourMatchingTest.test_visualization_reports import (
    visualize_test_result_matplotlib,
    generate_low_confidence_report,
    visualize_test_clusters_and_model,
    visualize_model_fit_on_test_data
)



def render_contour_to_canvas(contour, canvas_size=(1280, 720), fill_value=255):
    """
    Render a contour onto a blank canvas and detect it using OpenCV findContours.
    This simulates the real vision system pipeline.

    Args:
        contour: Input contour (N, 1, 2) array
        canvas_size: Size of the canvas (width, height)
        fill_value: Value to fill the contour with (255 for white)

    Returns:
        Detected contour from cv2.findContours (most similar to vision system output)
    """
    # Create blank canvas
    canvas = np.zeros((canvas_size[1], canvas_size[0]), dtype=np.uint8)

    # Convert contour to integer coordinates for drawing
    contour_int = np.array(contour, dtype=np.int32)

    # Draw filled contour on canvas
    cv2.drawContours(canvas, [contour_int], -1, fill_value, thickness=cv2.FILLED)

    # Optionally add some blur to simulate camera noise (more realistic)
    # canvas = cv2.GaussianBlur(canvas, (3, 3), 0)

    # Find contours using the same method as vision system
    # RETR_EXTERNAL gets only outer contours, CHAIN_APPROX_SIMPLE compresses horizontal/vertical segments
    contours, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        raise ValueError("No contours detected! Contour might be outside canvas bounds.")

    # Return the largest contour (should be the only one in our case)
    largest_contour = max(contours, key=cv2.contourArea)

    # Convert back to float32 for consistency with the rest of the pipeline
    return np.array(largest_contour, dtype=np.float32)


def process_contour_for_test(contour):
    """
    Process a contour for testing based on TEST_CONFIG settings.
    If vision system simulation is enabled, render to canvas and detect.
    Otherwise, return the contour as-is.

    Args:
        contour: Input contour (N, 1, 2) array

    Returns:
        Processed contour ready for testing
    """
    if TEST_CONFIG["use_vision_system_simulation"]:
        return render_contour_to_canvas(contour, canvas_size=TEST_CONFIG["canvas_size"])
    else:
        return contour


def create_mock_workpiece(workpiece_id, name, contour, spray_pattern_contours=None, spray_pattern_fills=None):
    """Create a mock workpiece object for testing."""
    if spray_pattern_contours is None:
        spray_pattern_contours = []
    if spray_pattern_fills is None:
        spray_pattern_fills = []

    # Create spray pattern dictionary
    spray_pattern = {
        "Contour": [{"contour": cnt, "settings": {}} for cnt in spray_pattern_contours],
        "Fill": [{"contour": fill, "settings": {}} for fill in spray_pattern_fills]
    }

    # Calculate contour area
    contour_obj = Contour(contour)
    contour_area = cv2.contourArea(contour)

    workpiece = Workpiece(
        workpieceId=workpiece_id,
        name=name,
        description=f"Test workpiece {name}",
        toolID=ToolID.Tool0,
        gripperID=Gripper.SINGLE,
        glueType=GlueType.TypeA,
        program=Program.TRACE,
        material="Test Material",
        contour={"contour": contour, "settings": {}},
        offset=0.0,
        height=10.0,
        nozzles=[1],
        contourArea=contour_area,
        glueQty=100,
        sprayWidth=5,
        sprayPattern=spray_pattern
    )

    return workpiece


def get_matching_confidence_batch(workpiece_list, new_contours):
    """
    Get ML model confidence for all contours at once.
    This uses the same logic as match_workpiece() to ensure consistency.

    Returns a list of (result, confidence, match_id) tuples for each contour.
    """
    from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import load_latest_model
    from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import predict_similarity

    try:
        # IMPORTANT: Use the SAME path as CompareContours.py match_workpiece() to ensure consistency
        # This should point to the shapeMatchinModelTraining/saved_models folder with the NEW retrained model
        model = load_latest_model(
            save_dir=r"/home/plp/cobot-soft-v2.1.4/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/contourMatching/shapeMatchinModelTraining/saved_models"
        )

        match_info = []

        for new_contour in new_contours:
            cnt = Contour(new_contour)
            best_confidence = 0.0
            best_match_id = None
            best_result = "DIFFERENT"

            # Check against all workpieces
            for wp in workpiece_list:
                wp_contour = Contour(wp.get_main_contour())

                result, confidence, _ = predict_similarity(
                    model,
                    wp_contour.get_contour_points(),
                    cnt.get_contour_points()
                )

                # Track best match (SAME) or best different confidence
                if result == "SAME":
                    # For SAME results, always prefer higher confidence matches
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match_id = wp.workpieceId
                        best_result = result
                elif result in ["DIFFERENT", "UNCERTAIN"]:
                    # For non-matches, still track the confidence (but no match_id)
                    # Keep the result and confidence from the comparison that had highest confidence
                    if best_result == "DIFFERENT" and confidence > best_confidence:
                        best_confidence = confidence
                        best_result = result

            match_info.append((best_result, best_confidence, best_match_id))

        return match_info
    except Exception as e:
        import traceback
        print(f"    Error getting ML confidence: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
        # Return UNKNOWN for all contours
        return [("UNKNOWN", 0.0, None) for _ in new_contours]





def run_single_match(shape_func, shape_name, rotation=45, translation=(50, 30)):
    """Test matching a single workpiece with one new contour."""
    print(f"\n{'='*70}")
    print(f"Test: Single Match - {shape_name}")
    print(f"{'='*70}")

    # Create original workpiece
    original_contour = shape_func()
    workpiece = create_mock_workpiece(
        workpiece_id=1,
        name=shape_name,
        contour=original_contour
    )

    # Create transformed "detected" contour
    transformed = rotate_contour(original_contour.copy(), rotation)
    transformed = translate_contour(transformed, *translation)

    print(f"  Created workpiece: {shape_name}")
    print(f"  Applied transformation: rotation={rotation}°, translation={translation}")

    # Run matching
    matched_result, no_matches, new_with_matches = findMatchingWorkpieces(
        workpieces=[workpiece],
        newContours=[transformed]
    )

    # Extract workpieces list from result dictionary
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    print(f"\n  Results:")
    print(f"    Matched workpieces: {len(matched)}")
    print(f"    Unmatched contours: {len(no_matches)}")
    print(f"    New contours with matches: {len(new_with_matches)}")

    # Verify results
    success = len(matched) == 1 and len(no_matches) == 0

    if success:
        # Check alignment quality
        aligned_contour = matched[0].get_main_contour()
        aligned_obj = Contour(aligned_contour)
        target_obj = Contour(transformed)

        aligned_centroid = aligned_obj.getCentroid()
        target_centroid = target_obj.getCentroid()
        centroid_error = np.linalg.norm(np.array(aligned_centroid) - np.array(target_centroid))

        print(f"    Alignment error: {centroid_error:.2f} pixels")

        if centroid_error < 10:
            print(f"  ✓ TEST PASSED - Good alignment")
        else:
            print(f"  ⚠ TEST PASSED - But alignment error is high")
    else:
        print(f"  ✗ TEST FAILED - Matching failed")

    # Get ML model confidence
    print(f"  Getting ML model confidence...")
    match_info = get_matching_confidence_batch([workpiece], [transformed])
    for i, (result, confidence, match_id) in enumerate(match_info):
        print(f"    ML Result: {result}, Confidence: {confidence:.1%}")

    # Visualize with matplotlib
    fig = visualize_test_result_matplotlib(
        [workpiece],
        [transformed],
        matched,
        f"{shape_name} - Single Match Test",
        match_info=match_info
    )

    # Save
    output_dir = "test_matching_outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"match_test_single_{shape_name.replace(' ', '_')}.png")
    fig.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print(f"  Visualization saved: {output_path}")

    return success


def run_multiple_matches():
    """Comprehensive test suite for multiple matching scenarios."""

    all_test_results = []
    output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["multiple_matches_dir"])
    os.makedirs(output_dir, exist_ok=True)

    # ========================================================================
    # Test Case 1: Basic 1-to-1 matching (4 workpieces, 4 matching contours)
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Test 1: Basic 1-to-1 Matching (4 WP, 4 Matching Contours)")
    print(f"{'='*70}")

    workpieces = [
        create_mock_workpiece(1, "Rectangle", process_contour_for_test(create_rectangle_contour(center=(200, 200)))),
        create_mock_workpiece(2, "Triangle", process_contour_for_test(create_triangle_contour(center=(500, 200)))),
        create_mock_workpiece(3, "Cross", process_contour_for_test(create_cross_contour(center=(200, 500)))),
        create_mock_workpiece(4, "Pentagon", process_contour_for_test(create_pentagon_contour(center=(500, 500)))),
    ]

    new_contours = [
        process_contour_for_test(translate_contour(rotate_contour(create_cross_contour(center=(200, 500)), 90), 30, 40)),
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(200, 200)), 30), 40, 25)),
        process_contour_for_test(translate_contour(rotate_contour(create_pentagon_contour(center=(500, 500)), 72), 35, 30)),
        process_contour_for_test(translate_contour(rotate_contour(create_triangle_contour(center=(500, 200)), 45), 50, 30)),
    ]

    matched_result, no_matches, _ = findMatchingWorkpieces(workpieces=workpieces, newContours=new_contours)
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    success = len(matched) == 4 and len(no_matches) == 0
    print(f"  Expected: 4 matches, 0 unmatched | Got: {len(matched)} matches, {len(no_matches)} unmatched")
    print(f"  {'✓ PASSED' if success else '✗ FAILED'}")

    match_info = get_matching_confidence_batch(workpieces, new_contours)
    fig = visualize_test_result_matplotlib(workpieces, new_contours, matched, "Test 1: Basic 1-to-1 Matching", match_info)
    fig.savefig(os.path.join(output_dir, "Test1_Basic_1to1.png"), dpi=100, bbox_inches='tight')
    plt.close(fig)
    all_test_results.append(("Test 1: Basic 1-to-1", success))

    # ========================================================================
    # Test Case 2: Multiple contours match same workpiece (Many-to-1)
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Test 2: Many-to-1 (3 Contours Match Same Rectangle Workpiece)")
    print(f"{'='*70}")

    workpieces = [
        create_mock_workpiece(1, "Rectangle", process_contour_for_test(create_rectangle_contour(center=(400, 300)))),
    ]

    # 3 different rotations/translations of the same rectangle
    new_contours = [
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(400, 300)), 30), 40, 25)),
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(400, 300)), 90), 50, 35)),
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(400, 300)), 145), 60, 40)),
    ]

    matched_result, no_matches, _ = findMatchingWorkpieces(workpieces=workpieces, newContours=new_contours)
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    success = len(matched) == 3 and len(no_matches) == 0  # All 3 should match the same workpiece
    print(f"  Expected: 3 matches (all to same WP), 0 unmatched | Got: {len(matched)} matches, {len(no_matches)} unmatched")
    print(f"  {'✓ PASSED' if success else '✗ FAILED'}")

    match_info = get_matching_confidence_batch(workpieces, new_contours)
    fig = visualize_test_result_matplotlib(workpieces, new_contours, matched, "Test 2: Many-to-1 (3 Rectangles → 1 WP)", match_info)
    fig.savefig(os.path.join(output_dir, "Test2_ManyToOne.png"), dpi=100, bbox_inches='tight')
    plt.close(fig)
    all_test_results.append(("Test 2: Many-to-1", success))

    # ========================================================================
    # Test Case 3: Some workpieces have no matching contours
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Test 3: Orphan Workpieces (4 WP, Only 2 Have Matches)")
    print(f"{'='*70}")

    workpieces = [
        create_mock_workpiece(1, "Rectangle", process_contour_for_test(create_rectangle_contour(center=(200, 200)))),
        create_mock_workpiece(2, "Triangle", process_contour_for_test(create_triangle_contour(center=(500, 200)))),
        create_mock_workpiece(3, "Cross", process_contour_for_test(create_cross_contour(center=(200, 500)))),  # No match
        create_mock_workpiece(4, "Pentagon", process_contour_for_test(create_pentagon_contour(center=(500, 500)))),  # No match
    ]

    # Only 2 contours (Rectangle and Triangle)
    new_contours = [
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(200, 200)), 45), 40, 30)),
        process_contour_for_test(translate_contour(rotate_contour(create_triangle_contour(center=(500, 200)), 60), 35, 25)),
    ]

    matched_result, no_matches, _ = findMatchingWorkpieces(workpieces=workpieces, newContours=new_contours)
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    success = len(matched) == 2 and len(no_matches) == 0
    print(f"  Expected: 2 matches, 0 unmatched, 2 orphan WPs | Got: {len(matched)} matches, {len(no_matches)} unmatched")
    print(f"  {'✓ PASSED' if success else '✗ FAILED'}")

    match_info = get_matching_confidence_batch(workpieces, new_contours)
    fig = visualize_test_result_matplotlib(workpieces, new_contours, matched, "Test 3: Orphan Workpieces", match_info)
    fig.savefig(os.path.join(output_dir, "Test3_OrphanWorkpieces.png"), dpi=100, bbox_inches='tight')
    plt.close(fig)
    all_test_results.append(("Test 3: Orphan Workpieces", success))

    # ========================================================================
    # Test Case 4: Some contours have no matching workpieces
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Test 4: Unmatched Contours (2 WP, 4 Contours, 2 Don't Match)")
    print(f"{'='*70}")

    workpieces = [
        create_mock_workpiece(1, "Rectangle", process_contour_for_test(create_rectangle_contour(center=(300, 300)))),
        create_mock_workpiece(2, "Triangle", process_contour_for_test(create_triangle_contour(center=(600, 300)))),
    ]

    new_contours = [
        process_contour_for_test(translate_contour(rotate_contour(create_rectangle_contour(center=(300, 300)), 45), 40, 30)),
        process_contour_for_test(translate_contour(rotate_contour(create_triangle_contour(center=(600, 300)), 60), 35, 25)),
        process_contour_for_test(create_star_contour(center=(300, 600))),  # No matching WP
        process_contour_for_test(create_hexagon_contour(center=(600, 600))),  # No matching WP
    ]

    matched_result, no_matches, _ = findMatchingWorkpieces(workpieces=workpieces, newContours=new_contours)
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    success = len(matched) == 2 and len(no_matches) == 2
    print(f"  Expected: 2 matches, 2 unmatched | Got: {len(matched)} matches, {len(no_matches)} unmatched")
    print(f"  {'✓ PASSED' if success else '✗ FAILED'}")

    match_info = get_matching_confidence_batch(workpieces, new_contours)
    fig = visualize_test_result_matplotlib(workpieces, new_contours, matched, "Test 4: Unmatched Contours", match_info)
    fig.savefig(os.path.join(output_dir, "Test4_UnmatchedContours.png"), dpi=100, bbox_inches='tight')
    plt.close(fig)
    all_test_results.append(("Test 4: Unmatched Contours", success))

    # ========================================================================
    # Test Case 5: All shapes vs all shapes (Extensive cross-matching)
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Test 5: Extensive Cross-Matching (All vs All)")
    print(f"{'='*70}")

    # Create workpieces for all basic shapes
    all_shapes = [
        ("Rectangle", create_rectangle_contour),
        ("Triangle", create_triangle_contour),
        ("Cross", create_cross_contour),
        ("Pentagon", create_pentagon_contour),
        ("Hexagon", create_hexagon_contour),
        ("Star", create_star_contour),
    ]

    workpieces = [
        create_mock_workpiece(i+1, name, process_contour_for_test(shape_func(center=(300, 300))))
        for i, (name, shape_func) in enumerate(all_shapes)
    ]

    # Create contours for all shapes (each should match exactly one workpiece)
    new_contours = [
        process_contour_for_test(translate_contour(rotate_contour(shape_func(center=(300, 300)), 45 + i*15), 40 + i*5, 30 + i*5))
        for i, (name, shape_func) in enumerate(all_shapes)
    ]

    matched_result, no_matches, _ = findMatchingWorkpieces(workpieces=workpieces, newContours=new_contours)
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    success = len(matched) == 6 and len(no_matches) == 0
    print(f"  Expected: 6 matches (1-to-1), 0 unmatched | Got: {len(matched)} matches, {len(no_matches)} unmatched")
    print(f"  {'✓ PASSED' if success else '✗ FAILED'}")

    # Verify each shape matched to correct workpiece
    match_info = get_matching_confidence_batch(workpieces, new_contours)
    for i, (result, confidence, match_id) in enumerate(match_info):
        expected_id = i + 1
        match_status = "✓" if match_id == expected_id else "✗"
        print(f"    Contour {i} ({all_shapes[i][0]}): {result} → WP-{match_id} (expected WP-{expected_id}) {match_status}")

    fig = visualize_test_result_matplotlib(workpieces, new_contours, matched, "Test 5: Extensive Cross-Matching (All vs All)", match_info)
    fig.savefig(os.path.join(output_dir, "Test5_AllVsAll.png"), dpi=100, bbox_inches='tight')
    plt.close(fig)
    all_test_results.append(("Test 5: All vs All", success))

    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"MULTIPLE MATCHES TEST SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for _, result in all_test_results if result)
    total = len(all_test_results)

    for test_name, result in all_test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} | {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed ({100*passed/total:.1f}%)")

    overall_success = passed == total

    # Save failed tests to failed_tests directory
    if not overall_success:
        failed_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["failed_tests_dir"])
        os.makedirs(failed_dir, exist_ok=True)
        for test_name, result in all_test_results:
            if not result:
                # Copy failed test to failed directory
                safe_name = test_name.replace(" ", "_").replace(":", "").replace("-", "")
                src = os.path.join(output_dir, f"{safe_name}.png")
                if os.path.exists(src):
                    import shutil
                    dst = os.path.join(failed_dir, f"Multiple_{safe_name}.png")
                    shutil.copy(src, dst)
                    print(f"  ⚠ Copied {test_name} to failed_tests/")

    return overall_success


def run_partial_matches():
    """Test with some matching and some non-matching contours."""
    print(f"\n{'='*70}")
    print(f"Test: Partial Matches - Some Match, Some Don't")
    print(f"{'='*70}")

    # Create workpieces
    workpieces = [
        create_mock_workpiece(1, "Rectangle", create_rectangle_contour(center=(300, 300))),
        create_mock_workpiece(2, "Triangle", create_triangle_contour(center=(600, 300))),
    ]

    # Create new contours: 2 matching, 2 non-matching
    new_contours = [
        # These should match
        translate_contour(rotate_contour(create_rectangle_contour(center=(300, 300)), 45), 40, 30),
        translate_contour(rotate_contour(create_triangle_contour(center=(600, 300)), 60), 35, 25),
        # These should NOT match (different shapes)
        create_star_contour(center=(300, 600)),
        create_hexagon_contour(center=(600, 600)),
    ]

    print(f"  Created {len(workpieces)} workpieces")
    print(f"  Created {len(new_contours)} new contours (2 should match, 2 should not)")

    # Run matching
    matched_result, no_matches, new_with_matches = findMatchingWorkpieces(
        workpieces=workpieces,
        newContours=new_contours
    )

    # Extract workpieces list from result dictionary
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    print(f"\n  Results:")
    print(f"    Matched workpieces: {len(matched)}")
    print(f"    Unmatched contours: {len(no_matches)}")
    print(f"    New contours with matches: {len(new_with_matches)}")

    # Verify
    success = len(matched) == 2 and len(no_matches) == 2

    if success:
        print(f"  ✓ TEST PASSED - Correct partial matching")
    else:
        print(f"  ✗ TEST FAILED - Expected 2 matches and 2 no-matches")

    # Get ML model confidence for each contour
    print(f"  Getting ML model confidence...")
    match_info = get_matching_confidence_batch(workpieces, new_contours)
    for i, (result, confidence, match_id) in enumerate(match_info):
        print(f"    Contour {i}: {result}, Confidence: {confidence:.1%}, Match ID: {match_id}")

    # Visualize with matplotlib
    fig = visualize_test_result_matplotlib(
        workpieces,
        new_contours,
        matched,
        "Partial Matches Test",
        match_info=match_info
    )

    output_dir = "test_matching_outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "match_test_partial.png")
    fig.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print(f"  Visualization saved: {output_path}")

    return success


def run_rotation_stress():
    """Test with extreme rotations (near 180°) to verify mask-based alignment."""
    print(f"\n{'='*70}")
    print(f"Test: Rotation Stress - Extreme Rotations")
    print(f"{'='*70}")

    test_cases = [
        ("Cross 46°", create_cross_contour, 46),
        ("Cross 90°", create_cross_contour, 90),
        ("Cross 179°", create_cross_contour, 179),
        ("Pentagon 144°", create_pentagon_contour, 144),
        ("Star 120°", create_star_contour, 120),
    ]

    results = []

    for name, shape_func, rotation in test_cases:
        print(f"\n  Testing {name}...")

        original = shape_func(center=(400, 400))
        original = process_contour_for_test(original)
        workpiece = create_mock_workpiece(1, name, original)

        transformed = rotate_contour(original.copy(), rotation)
        transformed = translate_contour(transformed, 30, 30)
        transformed = process_contour_for_test(transformed)

        matched_result, no_matches, _ = findMatchingWorkpieces(
            workpieces=[workpiece],
            newContours=[transformed]
        )

        # Extract workpieces list from result dictionary
        matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

        success = len(matched) == 1
        results.append((name, success))

        if success:
            aligned_contour = matched[0].get_main_contour()
            error = np.linalg.norm(
                np.array(Contour(aligned_contour).getCentroid()) -
                np.array(Contour(transformed).getCentroid())
            )
            print(f"    ✓ Matched with error: {error:.2f} pixels")
        else:
            print(f"    ✗ Failed to match")

    # Overall result
    all_success = all(success for _, success in results)

    print(f"\n  Overall:")
    if all_success:
        print(f"  ✓ ALL ROTATION TESTS PASSED")
    else:
        print(f"  ✗ SOME ROTATION TESTS FAILED")

    return all_success


def run_same_shape_different_size():
    """Test matching same shapes with different sizes (scale variations).

    This test explores how the matching algorithm handles shapes that are identical
    in form but differ in size. This is important for:
    1. Understanding the scale-invariance of the matching algorithm
    2. Identifying acceptable tolerance ranges for size variations
    3. Testing real-world scenarios where parts may have size variations due to manufacturing
    """
    print(f"\n{'='*70}")
    print(f"Test: Same Shape Different Size")
    print(f"{'='*70}")

    # Test cases organized by shape complexity and scale factor
    # Format: (shape_name, shape_func, scale_factor, expected_behavior)
    test_cases = [
        # ===== SIMPLE CONVEX SHAPES =====
        # Rectangle - basic 4-sided convex polygon
        ("Rectangle", create_rectangle_contour, [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.5, 2.0]),

        # Triangle - simplest polygon
        ("Triangle", create_triangle_contour, [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.5, 2.0]),

        # Circle - curved convex shape
        ("Circle", create_circle_contour, [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.5, 2.0]),

        # Pentagon - 5-sided regular polygon
        ("Pentagon", create_pentagon_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6, 1.8]),

        # Hexagon - 6-sided regular polygon
        ("Hexagon", create_hexagon_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6, 1.8]),

        # Ellipse - curved shape with two different radii
        ("Ellipse", create_ellipse_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6]),

        # ===== ANGULAR CONVEX SHAPES =====
        # Diamond - 4-sided rotated square
        ("Diamond", create_diamond_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # Trapezoid - 4-sided with parallel sides
        ("Trapezoid", create_trapezoid_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # ===== CONCAVE SHAPES (Complex) =====
        # Star - highly concave with multiple points
        ("Star", create_star_contour, [0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 1.75]),

        # Cross - concave with perpendicular arms
        ("Cross", create_cross_contour, [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.5, 1.8]),

        # Gear - highly complex with many teeth
        ("Gear", create_gear_advanced_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6]),

        # ===== L-SHAPES AND U-SHAPES (Manufacturing common) =====
        # L-Shape - common in manufacturing, asymmetric
        ("L-Shape", create_l_shape_advanced_contour, [0.5, 0.7, 0.8, 0.9, 1.1, 1.2, 1.5, 1.6, 2.0]),

        # U-Shape - symmetric concave
        ("U-Shape", create_u_shape_advanced_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # C-Shape - similar to U but curved
        ("C-Shape", create_c_shape_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # ===== CURVED AND ROUNDED SHAPES =====
        # Rounded Rectangle - mixed straight and curved edges
        ("Rounded-Rect", create_rounded_rectangle_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # Crescent - complex curved concave shape
        ("Crescent", create_crescent_contour, [0.7, 0.85, 0.95, 1.1, 1.25, 1.4]),

        # Half Circle - semi-circular
        ("Half-Circle", create_half_circle_contour, [0.7, 0.85, 0.95, 1.1, 1.25, 1.4]),

        # ===== IRREGULAR/ORGANIC SHAPES =====
        # Convex Blob - organic shape with bumps
        ("Convex-Blob", create_convex_blob_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6]),

        # Concave Blob - organic shape with indents
        ("Concave-Blob", create_concave_blob_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.6]),

        # ===== COMPLEX MECHANICAL SHAPES =====
        # Hourglass - symmetric with narrow waist
        ("Hourglass", create_hourglass_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # Keyhole - mixed circle and rectangle
        ("Keyhole", create_keyhole_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),

        # Pac-Man - circle with wedge cutout
        ("Pac-Man", create_pac_man_contour, [0.6, 0.8, 0.9, 1.1, 1.3, 1.5]),
    ]

    all_results = []
    output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["same_shape_different_size_dir"])
    os.makedirs(output_dir, exist_ok=True)

    # Process each shape type
    for shape_name, shape_func, scale_factors in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing Shape: {shape_name}")
        print(f"{'='*70}")

        shape_results = []

        for scale_factor in scale_factors:
            test_name = f"{shape_name}_{scale_factor}x"
            print(f"\n  Testing {test_name} (scale={scale_factor})...")

            # Create original workpiece at normal size (center at 400, 400)
            original = shape_func(center=(400, 400))
            workpiece = create_mock_workpiece(1, shape_name, original)

            # Create scaled version as "new contour"
            scaled = scale_contour(original.copy(), scale_factor)
            # Add realistic transformation (rotation + translation)
            scaled = rotate_contour(scaled, 25)
            scaled = translate_contour(scaled, 30, 30)

            # Run matching
            matched_result, no_matches, _ = findMatchingWorkpieces(
                workpieces=[workpiece],
                newContours=[scaled]
            )

            # Extract workpieces list from result dictionary
            matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

            # Get ML model confidence
            match_info = get_matching_confidence_batch([workpiece], [scaled])
            result_type, confidence, match_id = match_info[0] if match_info else ("UNKNOWN", 0.0, None)

            did_match = len(matched) == 1

            # Calculate areas for comparison
            original_area = cv2.contourArea(original)
            scaled_area = cv2.contourArea(scaled)
            area_ratio = scaled_area / original_area if original_area > 0 else 0
            expected_area_ratio = scale_factor ** 2

            # Calculate perimeter ratio
            original_perimeter = cv2.arcLength(original, True)
            scaled_perimeter = cv2.arcLength(scaled, True)
            perimeter_ratio = scaled_perimeter / original_perimeter if original_perimeter > 0 else 0

            print(f"    Scale factor: {scale_factor:.2f}")
            print(f"    Area ratio: {area_ratio:.3f} (expected: {expected_area_ratio:.3f})")
            print(f"    Perimeter ratio: {perimeter_ratio:.3f} (expected: {scale_factor:.2f})")
            print(f"    ML Result: {result_type}, Confidence: {confidence:.1%}")
            print(f"    Matched: {'YES' if did_match else 'NO'}")

            alignment_error = None
            if did_match:
                aligned_contour = matched[0].get_main_contour()
                error = np.linalg.norm(
                    np.array(Contour(aligned_contour).getCentroid()) -
                    np.array(Contour(scaled).getCentroid())
                )
                alignment_error = error
                print(f"    Alignment error: {error:.2f} pixels")

            # Visualize
            fig = visualize_test_result_matplotlib(
                [workpiece],
                [scaled],
                matched,
                f"{shape_name} - Scale: {scale_factor}x\nArea Ratio: {area_ratio:.3f} (expected: {expected_area_ratio:.3f})",
                match_info=match_info
            )

            # Save visualization
            safe_name = test_name.replace(" ", "_").replace("/", "_").replace(".", "_")
            output_path = os.path.join(output_dir, f"{safe_name}.png")
            fig.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            print(f"    Visualization saved: {output_path}")

            # Store result for summary
            shape_results.append({
                'test_name': test_name,
                'scale_factor': scale_factor,
                'did_match': did_match,
                'ml_result': result_type,
                'confidence': confidence,
                'area_ratio': area_ratio,
                'perimeter_ratio': perimeter_ratio,
                'alignment_error': alignment_error
            })

        all_results.append((shape_name, shape_results))

    # ========================================================================
    # COMPREHENSIVE SUMMARY
    # ========================================================================
    print(f"\n\n{'='*100}")
    print(f"COMPREHENSIVE SUMMARY - Same Shape Different Size Tests")
    print(f"{'='*100}")

    for shape_name, shape_results in all_results:
        print(f"\n{shape_name}:")
        print(f"  {'Scale':<8} {'Matched':<10} {'ML Result':<12} {'Confidence':<12} {'Area Ratio':<12} {'Perim Ratio':<12} {'Align Err':<10}")
        print(f"  {'-'*90}")

        for result in shape_results:
            matched_str = "YES" if result['did_match'] else "NO"
            align_err_str = f"{result['alignment_error']:.2f}px" if result['alignment_error'] is not None else "N/A"
            print(f"  {result['scale_factor']:<8.2f} {matched_str:<10} {result['ml_result']:<12} "
                  f"{result['confidence']:<12.1%} {result['area_ratio']:<12.3f} "
                  f"{result['perimeter_ratio']:<12.3f} {align_err_str:<10}")

    # ========================================================================
    # SCALE TOLERANCE ANALYSIS
    # ========================================================================
    print(f"\n\n{'='*100}")
    print(f"SCALE TOLERANCE ANALYSIS")
    print(f"{'='*100}")

    for shape_name, shape_results in all_results:
        matched_scales = [r['scale_factor'] for r in shape_results if r['did_match']]
        unmatched_scales = [r['scale_factor'] for r in shape_results if not r['did_match']]

        if matched_scales:
            min_matched = min(matched_scales)
            max_matched = max(matched_scales)
            print(f"\n{shape_name}:")
            print(f"  Matched scale range: {min_matched:.2f}x to {max_matched:.2f}x")
            print(f"  Total matched: {len(matched_scales)}/{len(shape_results)}")

            if unmatched_scales:
                print(f"  Unmatched scales: {', '.join([f'{s:.2f}x' for s in unmatched_scales])}")
        else:
            print(f"\n{shape_name}:")
            print(f"  No matches found at any scale!")

    print(f"\n{'='*100}\n")

    return True  # Always return True since this is exploratory


# ============================================================================
# TEST CONFIGURATION FLAGS
# ============================================================================
TEST_CONFIG = {
    # What to test
    "test_known_matches": True,        # Test shapes that should match (same shape, rotated/translated)
    "test_known_different": True,      # Test shapes that should NOT match (different shapes)
    "test_multiple_matches": True,     # Test multiple workpieces with multiple contours
    "test_rotation_stress": True,      # Test extreme rotations (46°, 90°, 179°, etc.)
    "test_same_shape_different_size": True,  # DISABLED: Creates 100+ extra tests - enable only for scale analysis

    # Vision system simulation
    "use_vision_system_simulation": True,  # Render contours to canvas and detect with findContours (like real usage)
    "canvas_size": (1280, 720),            # Canvas size for vision system simulation

    # Output directories
    "output_base_dir": "test_matching_outputs",
    "known_matches_dir": "known_matches",
    "known_different_dir": "known_different",
    "multiple_matches_dir": "multiple_matches",
    "rotation_stress_dir": "rotation_stress",
    "same_shape_different_size_dir": "same_shape_different_size",
    "failed_tests_dir": "failed_tests",  # Directory for failed tests
}


def run_known_match_pair(workpiece_shape_func, test_shape_func, workpiece_name, test_name,
                         rotation, translation, output_dir):
    """
    Test a pair of shapes that SHOULD match (same shape, transformed).

    Returns:
        tuple: (success: bool, test_details: dict)
            test_details contains: {
                'test_name': str,
                'category': str,
                'workpiece_name': str,
                'test_shape_name': str,
                'ml_result': str,
                'ml_confidence': float,
                'expected_result': str,
                'test_passed': bool,
                'rotation': float,
                'translation': tuple
            }
    """
    print(f"\n{'='*70}")
    print(f"Test: Known Match - {workpiece_name} vs {test_name}")
    print(f"{'='*70}")

    # Create original workpiece
    original_contour = workpiece_shape_func()
    # Process workpiece contour through vision system if enabled
    original_contour = process_contour_for_test(original_contour)
    workpiece = create_mock_workpiece(
        workpiece_id=1,
        name=workpiece_name,
        contour=original_contour
    )

    # Create transformed "detected" contour
    test_contour = test_shape_func()
    transformed = rotate_contour(test_contour.copy(), rotation)
    transformed = translate_contour(transformed, *translation)
    # Process new contour through vision system if enabled
    transformed = process_contour_for_test(transformed)

    print(f"  Workpiece: {workpiece_name}")
    print(f"  Test shape: {test_name}")
    print(f"  Transformation: rotation={rotation}°, translation={translation}")

    # Run matching
    matched_result, no_matches, new_with_matches = findMatchingWorkpieces(
        workpieces=[workpiece],
        newContours=[transformed]
    )

    # Extract workpieces list from result dictionary
    matched = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else matched_result

    print(f"\n  Results:")
    print(f"    Matched: {len(matched)}")
    print(f"    Unmatched: {len(no_matches)}")

    # Verify - should match
    expected_match = (workpiece_name == test_name)
    success = (len(matched) == 1) == expected_match

    if len(matched) == 1:
        # Check alignment quality
        aligned_contour = matched[0].get_main_contour()
        aligned_obj = Contour(aligned_contour)
        target_obj = Contour(transformed)

        aligned_centroid = aligned_obj.getCentroid()
        target_centroid = target_obj.getCentroid()
        centroid_error = np.linalg.norm(np.array(aligned_centroid) - np.array(target_centroid))

        print(f"    Alignment error: {centroid_error:.2f} pixels")

        if expected_match:
            if centroid_error < 10:
                print(f"  ✓ TEST PASSED - Correctly matched")
            else:
                print(f"  ⚠ TEST WARNING - Matched but alignment error is high")
        else:
            print(f"  ✗ TEST FAILED - Should NOT have matched!")
    else:
        if expected_match:
            print(f"  ✗ TEST FAILED - Should have matched!")
        else:
            print(f"  ✓ TEST PASSED - Correctly NOT matched")

    # Extract ML model confidence from the matching result (SINGLE SOURCE OF TRUTH!)
    # This ensures we display the SAME prediction that was used for matching
    print(f"  Extracting ML confidence from match result...")
    match_info = []

    # matched_result is a dict with keys: "workpieces", "orientations", "mlConfidences", "mlResults"
    workpieces_list = matched_result.get("workpieces", []) if isinstance(matched_result, dict) else []
    ml_confidences = matched_result.get("mlConfidences", []) if isinstance(matched_result, dict) else []
    ml_results = matched_result.get("mlResults", []) if isinstance(matched_result, dict) else []

    if len(workpieces_list) > 0 and len(ml_confidences) > 0:
        # Match found - extract confidence from the result structure
        ml_confidence = ml_confidences[0]
        ml_result = ml_results[0] if len(ml_results) > 0 else "SAME"
        match_id = workpieces_list[0].workpieceId
        match_info.append((ml_result, ml_confidence, match_id))
        print(f"    ML Result: {ml_result}, Confidence: {ml_confidence:.1%}")
    else:
        # No match found - extract ML prediction from unmatched contours
        if len(no_matches) > 0:
            # Get the ML prediction that was attached to the no-match contour
            no_match_contour = no_matches[0]
            ml_result = getattr(no_match_contour, '_ml_result', "DIFFERENT")
            ml_confidence = getattr(no_match_contour, '_ml_confidence', 0.0)
            ml_wp_id = getattr(no_match_contour, '_ml_wp_id', None)
            match_info.append((ml_result, ml_confidence, ml_wp_id))
            print(f"    ML Result: {ml_result}, Confidence: {ml_confidence:.1%}")
        else:
            match_info.append(("DIFFERENT", 0.0, None))
            print(f"    ML Result: DIFFERENT (no match found)")

    # Visualize
    fig = visualize_test_result_matplotlib(
        [workpiece],
        [transformed],
        matched,
        f"{workpiece_name} vs {test_name}",
        match_info=match_info
    )

    # Save to regular output directory
    os.makedirs(output_dir, exist_ok=True)
    safe_name = f"{workpiece_name}_vs_{test_name}".replace(" ", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"{safe_name}.png")
    fig.savefig(output_path, dpi=100, bbox_inches='tight')

    # If test failed, also save to failed_tests directory
    if not success:
        failed_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["failed_tests_dir"])
        os.makedirs(failed_dir, exist_ok=True)
        failed_path = os.path.join(failed_dir, f"{safe_name}.png")
        fig.savefig(failed_path, dpi=100, bbox_inches='tight')
        print(f"  ⚠ FAILED - Also saved to: {failed_path}")

    plt.close(fig)
    print(f"  Visualization saved: {output_path}")

    # Build detailed test information
    ml_result = match_info[0][0] if match_info else "UNKNOWN"
    ml_confidence = match_info[0][1] if match_info else 0.0

    # Determine expected result based on test type
    expected_result = "SAME" if expected_match else "DIFFERENT"

    test_details = {
        'test_name': f"{workpiece_name} vs {test_name}",
        'category': 'Known Match' if expected_match else 'Known Different',
        'workpiece_name': workpiece_name,
        'test_shape_name': test_name,
        'ml_result': ml_result,
        'ml_confidence': ml_confidence,
        'expected_result': expected_result,
        'test_passed': success,
        'rotation': rotation,
        'translation': translation
    }

    return success, test_details


def main():
    """Run all test cases based on configuration flags."""
    print("\n" + "="*70)
    print("FIND MATCHING WORKPIECES TEST SUITE")
    print("="*70)
    print("\nTest Configuration:")
    for key, value in TEST_CONFIG.items():
        if key.startswith("test_"):
            status = "✓ ENABLED" if value else "✗ DISABLED"
            print(f"  {status} | {key}")

    all_results = []
    all_test_details = []  # NEW: Collect detailed test information for low confidence analysis

    # ========================================================================
    # SECTION 1: KNOWN MATCHES (Same shape, rotated/translated)
    # ========================================================================
    if TEST_CONFIG["test_known_matches"]:
        print("\n\n" + "="*70)
        print("SECTION 1: KNOWN MATCHES (Should Match)")
        print("="*70)

        output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["known_matches_dir"])

        # Generate test cases with multiple rotations and translations for each shape
        # This creates comprehensive coverage with 100+ tests
        known_match_test_cases = []

        # Define shapes to test - LIMITED SET for balanced testing
        # We'll test each shape with 2 different transformations to keep it manageable
        shapes_to_test = [
            # Basic convex shapes (9 shapes)
            (create_rectangle_contour, "Rectangle"),
            (create_rounded_rectangle_contour, "Rounded Rect"),
            (create_triangle_contour, "Triangle"),
            (create_pentagon_contour, "Pentagon"),
            (create_hexagon_contour, "Hexagon"),
            (create_trapezoid_contour, "Trapezoid"),
            (create_diamond_contour, "Diamond"),
            (create_ellipse_contour, "Ellipse"),
            (create_circle_contour, "Circle"),

            # Concave shapes (4 shapes)
            (create_cross_contour, "Cross"),
            (create_star_contour, "Star"),
            (create_l_shape_advanced_contour, "L-Shape"),
            (create_u_shape_advanced_contour, "U-Shape"),

            # Curved and complex (3 shapes)
            (create_c_shape_contour, "C-Shape"),
            (create_crescent_contour, "Crescent"),
            (create_gear_advanced_contour, "Gear"),
        ]

        # Two distinct transformations per shape for variety
        test_transformations = [
            (45, (40, 30)),   # moderate rotation, moderate translation
            (135, (25, 50)),  # large rotation, different translation
        ]

        # Generate tests: 16 shapes × 2 transformations = 32 tests
        for shape_func, shape_name in shapes_to_test:
            for rotation, translation in test_transformations:
                test_name = f"{shape_name}"
                known_match_test_cases.append(
                    (shape_func, shape_func, shape_name, test_name, rotation, translation)
                )

        print(f"\n  Generated {len(known_match_test_cases)} known match test cases")

        for wp_func, test_func, wp_name, test_name, rotation, translation in known_match_test_cases:
            success, test_details = run_known_match_pair(wp_func, test_func, wp_name, test_name,
                                                         rotation, translation, output_dir)
            all_results.append((f"Known Match - {wp_name}", success))
            all_test_details.append(test_details)  # NEW: Collect test details

    # ========================================================================
    # SECTION 2: KNOWN DIFFERENT (Different shapes, should NOT match)
    # ========================================================================
    if TEST_CONFIG["test_known_different"]:
        print("\n\n" + "="*70)
        print("SECTION 2: KNOWN DIFFERENT (Should NOT Match)")
        print("="*70)

        output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["known_different_dir"])

        # EXPANDED: Generate more shape pairs to balance with Known Matches
        # We want ~32 tests to match the Known Match count
        known_different_test_cases = [
            # (workpiece_shape, test_shape, workpiece_name, test_name, rotation, translation)

            # Rectangle vs other shapes (5 tests)
            (create_rectangle_contour, create_triangle_contour, "Rectangle", "Triangle", 30, (40, 25)),
            (create_rectangle_contour, create_rounded_rectangle_contour, "Rectangle", "Rounded Rect", 45, (35, 30)),
            (create_rectangle_contour, create_circle_contour, "Rectangle", "Circle", 0, (40, 30)),
            (create_rectangle_contour, create_star_contour, "Rectangle", "Star", 45, (35, 30)),
            (create_rectangle_contour, create_hexagon_contour, "Rectangle", "Hexagon", 60, (30, 40)),

            # Triangle vs other shapes (5 tests)
            (create_triangle_contour, create_pentagon_contour, "Triangle", "Pentagon", 60, (40, 30)),
            (create_triangle_contour, create_hexagon_contour, "Triangle", "Hexagon", 45, (35, 30)),
            (create_triangle_contour, create_cross_contour, "Triangle", "Cross", 90, (40, 35)),
            (create_triangle_contour, create_diamond_contour, "Triangle", "Diamond", 30, (45, 30)),
            (create_triangle_contour, create_gear_advanced_contour, "Triangle", "Gear", 75, (35, 40)),

            # Pentagon vs Hexagon and others (4 tests)
            (create_pentagon_contour, create_hexagon_contour, "Pentagon", "Hexagon", 60, (40, 30)),
            (create_pentagon_contour, create_trapezoid_contour, "Pentagon", "Trapezoid", 45, (35, 30)),
            (create_pentagon_contour, create_star_contour, "Pentagon", "Star", 72, (40, 35)),
            (create_pentagon_contour, create_circle_contour, "Pentagon", "Circle", 0, (45, 30)),

            # Cross vs Star and complex shapes (4 tests)
            (create_cross_contour, create_star_contour, "Cross", "Star", 45, (40, 30)),
            (create_cross_contour, create_gear_advanced_contour, "Cross", "Gear", 30, (35, 30)),
            (create_cross_contour, create_l_shape_advanced_contour, "Cross", "L-Shape", 90, (40, 40)),
            (create_cross_contour, create_hexagon_contour, "Cross", "Hexagon", 60, (35, 35)),

            # L-Shape vs U-Shape and similar concave (4 tests)
            (create_l_shape_advanced_contour, create_u_shape_advanced_contour, "L-Shape", "U-Shape", 90, (40, 35)),
            (create_l_shape_advanced_contour, create_c_shape_contour, "L-Shape", "C-Shape", 60, (35, 30)),
            (create_u_shape_advanced_contour, create_c_shape_contour, "U-Shape", "C-Shape", 45, (40, 30)),
            (create_u_shape_advanced_contour, create_crescent_contour, "U-Shape", "Crescent", 90, (35, 40)),

            # Curved vs Angular shapes (4 tests)
            (create_ellipse_contour, create_diamond_contour, "Ellipse", "Diamond", 45, (40, 30)),
            (create_crescent_contour, create_c_shape_contour, "Crescent", "C-Shape", 90, (35, 30)),
            (create_circle_contour, create_hexagon_contour, "Circle", "Hexagon", 60, (40, 35)),
            (create_rounded_rectangle_contour, create_ellipse_contour, "Rounded Rect", "Ellipse", 30, (35, 40)),

            # Star vs other concave shapes (3 tests)
            (create_star_contour, create_gear_advanced_contour, "Star", "Gear", 45, (40, 30)),
            (create_star_contour, create_cross_contour, "Star", "Cross", 36, (35, 35)),
            (create_star_contour, create_trapezoid_contour, "Star", "Trapezoid", 60, (40, 30)),

            # Additional mixed comparisons (3 tests)
            (create_gear_advanced_contour, create_hexagon_contour, "Gear", "Hexagon", 60, (40, 30)),
            (create_diamond_contour, create_trapezoid_contour, "Diamond", "Trapezoid", 45, (35, 35)),
            (create_hexagon_contour, create_circle_contour, "Hexagon", "Circle", 0, (40, 30)),
        ]

        print(f"\n  Generated {len(known_different_test_cases)} known different test cases")

        for wp_func, test_func, wp_name, test_name, rotation, translation in known_different_test_cases:
            success, test_details = run_known_match_pair(wp_func, test_func, wp_name, test_name,
                                                         rotation, translation, output_dir)
            all_results.append((f"Known Different - {wp_name} vs {test_name}", success))
            all_test_details.append(test_details)  # NEW: Collect test details

    # ========================================================================
    # SECTION 3: MULTIPLE MATCHES
    # ========================================================================
    if TEST_CONFIG["test_multiple_matches"]:
        print("\n\n" + "="*70)
        print("SECTION 3: MULTIPLE MATCHES TEST")
        print("="*70)

        output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["multiple_matches_dir"])
        result = run_multiple_matches()
        all_results.append(("Multiple Matches", result))

    # ========================================================================
    # SECTION 4: ROTATION STRESS TEST
    # ========================================================================
    if TEST_CONFIG["test_rotation_stress"]:
        print("\n\n" + "="*70)
        print("SECTION 4: ROTATION STRESS TEST")
        print("="*70)

        output_dir = os.path.join(TEST_CONFIG["output_base_dir"], TEST_CONFIG["rotation_stress_dir"])
        result = run_rotation_stress()
        all_results.append(("Rotation Stress", result))

    # ========================================================================
    # SECTION 5: SAME SHAPE DIFFERENT SIZE TEST
    # ========================================================================
    if TEST_CONFIG["test_same_shape_different_size"]:
        print("\n\n" + "="*70)
        print("SECTION 5: SAME SHAPE DIFFERENT SIZE TEST")
        print("="*70)

        result = run_same_shape_different_size()
        all_results.append(("Same Shape Different Size", result))

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)

    for test_name, result in all_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} | {test_name}")

    print(f"\n  Total: {passed}/{total} tests passed ({100*passed/total:.1f}%)")

    if passed == total:
        print(f"\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠ {total - passed} test(s) failed")

    print(f"\n  Output images saved in: {TEST_CONFIG['output_base_dir']}/")

    # ========================================================================
    # GENERATE COMPREHENSIVE VISUALIZATION
    # ========================================================================
    print("\n" + "="*70)
    print("GENERATING COMPREHENSIVE ANALYSIS VISUALIZATION")
    print("="*70)
    visualize_test_clusters_and_model(all_results,TEST_CONFIG)

    # ========================================================================
    # GENERATE MODEL FIT VISUALIZATION
    # ========================================================================
    print("\n" + "="*70)
    print("GENERATING MODEL FIT VISUALIZATION")
    print("="*70)
    visualize_model_fit_on_test_data(all_results,TEST_CONFIG)

    # ========================================================================
    # GENERATE LOW CONFIDENCE REPORT
    # ========================================================================
    if len(all_test_details) > 0:
        print("\n" + "="*70)
        print("GENERATING LOW CONFIDENCE REPORT")
        print("="*70)
        generate_low_confidence_report(all_test_details, test_config=TEST_CONFIG, confidence_threshold=0.80,)
    else:
        print("\n  Note: No detailed test data collected for low confidence analysis")

    print("="*70 + "\n")


def create_circle_contour(center=(400, 300), radius=100):
    """Create a circle contour for testing."""
    x, y = center
    points = []
    for i in range(100):
        angle = 2 * np.pi * i / 100
        px = x + radius * np.cos(angle)
        py = y + radius * np.sin(angle)
        points.append([px, py])
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)








if __name__ == "__main__":
    main()