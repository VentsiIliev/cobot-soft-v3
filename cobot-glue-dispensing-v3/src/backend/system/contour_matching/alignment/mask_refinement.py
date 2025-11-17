from modules.shared.core.ContourStandartized import Contour
from backend.system.utils.contours import calculate_mask_overlap


def _refine_alignment_with_mask(workpiece_contour, target_contour):
    """
    Refine the alignment of a contour by rotating it to maximize mask overlap with a target contour.
    Performs three stages: coarse search, adaptive local refinement, and fine-tuning.

    Args:
        workpiece_contour (np.ndarray or Contour): The contour to rotate and align.
        target_contour (np.ndarray or Contour): The reference contour to align to.


    Returns:
        tuple: (best_rotation_angle, best_overlap_score)
            - best_rotation_angle (float): Optimal rotation angle in degrees [-180, 180].
            - best_overlap_score (float): Maximum mask overlap achieved.
    """
    contour_obj = Contour(workpiece_contour)
    centroid = contour_obj.getCentroid()

    best_rotation = 0
    best_overlap = calculate_mask_overlap(workpiece_contour, target_contour)
    print(f"      Initial overlap (0°): {best_overlap:.4f}")

    # Stage 1: Coarse search
    best_rotation, best_overlap = _coarse_search(
        workpiece_contour, target_contour, centroid, best_rotation, best_overlap
    )

    # Stage 2: Adaptive local refinement
    best_rotation, best_overlap = _local_refinement(
        workpiece_contour, target_contour, centroid, best_rotation, best_overlap
    )

    # Stage 3: Fine-tuning
    best_rotation, best_overlap = _fine_tune(
        workpiece_contour, target_contour, centroid, best_rotation, best_overlap
    )

    # Normalize rotation to [-180, 180]
    best_rotation = (best_rotation + 180) % 360 - 180
    print(f"      Final best rotation: {best_rotation:.2f}° with overlap: {best_overlap:.4f}")
    return best_rotation, best_overlap


def _coarse_search(workpiece_contour, target_contour, centroid, best_rotation, best_overlap):
    """
    Perform a coarse rotational search over 0–360° to find a rough alignment that increases overlap.

    Args:
        workpiece_contour (np.ndarray or Contour): Contour to rotate.
        target_contour (np.ndarray or Contour): Reference contour for overlap calculation.
        centroid (tuple): Pivot point for rotation.
        best_rotation (float): Current best rotation angle.
        best_overlap (float): Current best overlap score.

    Returns:
        tuple: Updated (best_rotation, best_overlap) after coarse search.
    """
    print(f"      Stage 1: Coarse search...")
    current_step = 10  # The initial step size in degrees for rotating the contour.
    # We start with 10° increments to quickly explore the 360° rotation space.
    min_coarse_step = 5  # The smallest allowed step size during coarse search.
    # If improvements are found, the step is reduced but never below this value.
    angle = 0  # The current absolute rotation angle being tested, starting from 0°.
    iteration = 0  # Loop counter to track how many rotations have been tested.
    max_iterations = 100  # Safety limit to prevent infinite loops if the algorithm does not converge.

    while angle < 360 and iteration < max_iterations:
        signed_angle = angle if angle <= 180 else angle - 360
        rotated_points = _rotate_contour(workpiece_contour, signed_angle, centroid)
        overlap = calculate_mask_overlap(rotated_points, target_contour)

        if overlap > best_overlap:
            improvement = overlap - best_overlap
            print(f"      Improvement at {signed_angle}°: overlap = {overlap:.4f} (+{improvement:.4f})")
            best_overlap = overlap
            best_rotation = signed_angle
            current_step = max(min_coarse_step, current_step * 0.7)
        else:
            current_step = min(15, current_step * 1.2)

        angle += int(current_step)
        iteration += 1

    print(f"      Stage 1 complete: best at {best_rotation}° with overlap {best_overlap:.4f}")
    return best_rotation, best_overlap


def _local_refinement(workpiece_contour, target_contour, centroid, best_rotation, best_overlap):
    """
    Refine rotation in a local neighborhood around the coarse alignment to improve mask overlap.
    Uses adaptive step size and stops when no improvement is seen after several iterations.

    Args:
        workpiece_contour (np.ndarray or Contour): Contour to rotate.
        target_contour (np.ndarray or Contour): Reference contour.
        centroid (tuple): Pivot for rotation.
        best_rotation (float): Starting rotation angle.
        best_overlap (float): Starting overlap score.

    Returns:
        tuple: Updated (best_rotation, best_overlap) after local refinement.
    """
    print(f"      Stage 2: Adaptive local refinement...")

    current_step = 3.0  # The initial rotation step size (in degrees) for the local refinement search.
    # Smaller than coarse search, allowing finer adjustments around the current best rotation.

    min_step = 0.5  # The minimum allowed step size during refinement.
    # Ensures the search can continue to very small rotations without going to zero.

    search_window = 15  # Maximum angular distance (in degrees) from the current best rotation to consider in this stage.
    # Restricts the refinement to a local neighborhood around the current best rotation.

    no_improvement_count = 0  # Counter to track consecutive iterations where no improvement in overlap is found.
    # Used to detect convergence and stop the refinement early.

    max_no_improvement = 5  # Maximum allowed consecutive iterations without improvement before terminating the local refinement stage.

    iteration = 0  # Counter for the total number of iterations performed in this refinement stage.

    max_iterations = 50  # Hard limit on the number of iterations in this stage to prevent infinite loops or excessive computation.

    search_angles = [best_rotation - current_step, best_rotation + current_step]

    while iteration < max_iterations and no_improvement_count < max_no_improvement:
        found_improvement = False
        for angle in search_angles:
            if abs(angle - best_rotation) > search_window:
                continue

            angle = (angle + 180) % 360 - 180
            rotated_points = _rotate_contour(workpiece_contour, angle, centroid)
            overlap = calculate_mask_overlap(rotated_points, target_contour)

            if overlap > best_overlap:
                improvement = overlap - best_overlap
                print(f"      Refined at {angle:.2f}°: overlap = {overlap:.4f} (+{improvement:.4f}), step = {current_step:.2f}°")
                best_overlap = overlap
                best_rotation = angle
                found_improvement = True
                no_improvement_count = 0
                current_step = max(min_step, current_step * 0.6)
                break

        if not found_improvement:
            no_improvement_count += 1
            current_step = min(5.0, current_step * 1.3)

        search_angles = [best_rotation - current_step, best_rotation + current_step]
        iteration += 1

    print(f"      Stage 2 complete after {iteration} iterations")
    return best_rotation, best_overlap


def _fine_tune(workpiece_contour, target_contour, centroid, best_rotation, best_overlap):
    """
    Perform very fine rotational adjustments (±2° in 0.5° steps) around the current best rotation
    to maximize mask overlap.

    Args:
        workpiece_contour (np.ndarray or Contour): Contour to rotate.
        target_contour (np.ndarray or Contour): Reference contour.
        centroid (tuple): Pivot point for rotation.
        best_rotation (float): Starting rotation angle.
        best_overlap (float): Starting overlap score.

    Returns:
        tuple: Updated (best_rotation, best_overlap) after fine-tuning.
    """
    print(f"      Stage 3: Final fine-tuning...")
    fine_step = 0.5
    fine_range = 2  # ±2°

    for offset_sign in [-1, 1]:
        offset = 0
        while offset <= fine_range:
            angle = best_rotation + offset_sign * offset
            angle = (angle + 180) % 360 - 180
            rotated_points = _rotate_contour(workpiece_contour, angle, centroid)
            overlap = calculate_mask_overlap(rotated_points, target_contour)

            if overlap > best_overlap:
                improvement = overlap - best_overlap
                print(f"      Fine-tuned at {angle:.2f}°: overlap = {overlap:.4f} (+{improvement:.4f})")
                best_overlap = overlap
                best_rotation = angle

            offset += fine_step

    return best_rotation, best_overlap


def _rotate_contour(contour, angle, centroid):
    """
    Rotate a contour (np.ndarray or Contour) around a pivot point (centroid).

    Args:
        contour (np.ndarray or Contour): Contour to rotate.
        angle (float): Rotation angle in degrees.
        centroid (tuple): Pivot point for rotation.

    Returns:
        np.ndarray: Rotated contour points.
    """
    if not isinstance(contour, Contour):
        contour_obj = Contour(contour.copy())
    else:
        contour_obj = contour
    contour_obj.rotate(angle, centroid)
    return contour_obj.get()
