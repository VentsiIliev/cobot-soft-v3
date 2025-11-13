from modules.shared.shared.ContourStandartized import Contour
from src.backend.system.utils.contours import calculate_mask_overlap
import cv2

def _adaptive_rotation_search():
    pass

def _local_refinement_search():
    pass

def _refine_alignment_with_mask(workpiece_contour, target_contour, search_range=180, step=1, check_flips=True):
    """
    Refine contour alignment by rotating and checking mask overlap using adaptive step size.
    The step size reduces as we get closer to the optimal rotation (gradient descent-like approach).

    Args:
        workpiece_contour: The workpiece contour after initial alignment
        target_contour: The target/new contour to align to
        search_range: Range in degrees to search (±search_range, default ±180 for full rotation)
        step: Initial step size in degrees (will be adapted based on improvement)
        check_flips: If True, do comprehensive angle search

    Returns:
        tuple: (best_rotation_angle, best_overlap_score)
    """


    # Start with current position as baseline
    best_rotation = 0
    best_overlap = calculate_mask_overlap(workpiece_contour, target_contour)
    print(f"      Initial overlap (0°): {best_overlap:.4f}")

    # Get centroid for rotation
    contour_obj = Contour(workpiece_contour)
    centroid = contour_obj.getCentroid()

    # Stage 1: Coarse search across full rotation space (0° to 360° with adaptive step)
    print(f"      Stage 1: Coarse search (0° to 360° with adaptive step)...")
    current_step = 10  # Start with 10° steps
    min_coarse_step = 5  # Don't go below 5° in coarse search

    angle = 0
    iteration = 0
    max_iterations = 100  # Safety limit

    while angle < 360 and iteration < max_iterations:
        # Convert to signed angle (-180 to 180)
        signed_angle = angle if angle <= 180 else angle - 360

        test_contour = Contour(workpiece_contour.copy())
        test_contour.rotate(signed_angle, centroid)
        rotated_points = test_contour.get()
        overlap = calculate_mask_overlap(rotated_points, target_contour)

        improvement = overlap - best_overlap

        if overlap > best_overlap:
            print(f"      Improvement at {signed_angle}°: overlap = {overlap:.4f} (+{improvement:.4f})")
            best_overlap = overlap
            best_rotation = signed_angle

            # Reduce step size when we find improvement (we're getting closer)
            current_step = max(min_coarse_step, current_step * 0.7)
        else:
            # Increase step size when no improvement (we're far from optimum)
            current_step = min(15, current_step * 1.2)

        angle += int(current_step)
        iteration += 1

    print(f"      Stage 1 complete: best at {best_rotation}° with overlap {best_overlap:.4f}")

    # Stage 2: Adaptive local refinement around best angle
    print(f"      Stage 2: Adaptive refinement around {best_rotation}°...")

    # Adaptive parameters
    current_step = 3.0  # Start with 3° steps
    min_step = 0.5      # Minimum step size (0.5°)
    search_window = 15  # Search ±15° around best

    # Keep track of last few improvements to detect convergence
    no_improvement_count = 0
    max_no_improvement = 5

    iteration = 0
    max_iterations = 50

    # Test both directions around current best
    search_angles = []
    for offset in [-current_step, current_step]:
        search_angles.append(best_rotation + offset)

    while iteration < max_iterations and no_improvement_count < max_no_improvement:
        found_improvement = False

        for angle in search_angles:
            # Keep within search window
            if abs(angle - best_rotation) > search_window:
                continue

            # Normalize to [-180, 180]
            angle = (angle + 180) % 360 - 180

            test_contour = Contour(workpiece_contour.copy())
            test_contour.rotate(angle, centroid)
            rotated_points = test_contour.get()
            overlap = calculate_mask_overlap(rotated_points, target_contour)

            improvement = overlap - best_overlap

            if overlap > best_overlap:
                print(f"      Refined at {angle:.2f}°: overlap = {overlap:.4f} (+{improvement:.4f}), step = {current_step:.2f}°")
                best_overlap = overlap
                best_rotation = angle
                found_improvement = True
                no_improvement_count = 0

                # Reduce step size when we find improvement
                current_step = max(min_step, current_step * 0.6)
                break

        if not found_improvement:
            no_improvement_count += 1
            # Slightly increase step to explore a bit more
            current_step = min(5.0, current_step * 1.3)

        # Update search angles for next iteration
        search_angles = [best_rotation - current_step, best_rotation + current_step]
        iteration += 1

    print(f"      Stage 2 complete after {iteration} iterations")

    # Stage 3: Final fine-tuning with very small steps
    print(f"      Stage 3: Final fine-tuning...")
    fine_step = 0.5
    fine_range = 2  # ±2° around best

    for offset_sign in [-1, 1]:
        offset = 0
        while offset <= fine_range:
            angle = best_rotation + offset_sign * offset
            angle = (angle + 180) % 360 - 180

            test_contour = Contour(workpiece_contour.copy())
            test_contour.rotate(angle, centroid)
            rotated_points = test_contour.get()
            overlap = calculate_mask_overlap(rotated_points, target_contour)

            if overlap > best_overlap:
                improvement = overlap - best_overlap
                print(f"      Fine-tuned at {angle:.2f}°: overlap = {overlap:.4f} (+{improvement:.4f})")
                best_overlap = overlap
                best_rotation = angle

            offset += fine_step

    # Normalize final result to [-180, 180]
    best_rotation = (best_rotation + 180) % 360 - 180

    print(f"      Final best rotation: {best_rotation:.2f}° with overlap: {best_overlap:.4f}")
    return best_rotation, best_overlap


