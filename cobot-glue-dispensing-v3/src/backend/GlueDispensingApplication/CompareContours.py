import cv2
import numpy as np
import copy
from modules.shared.shared.ContourStandartized import Contour
from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import predict_similarity, \
     load_latest_model

from src.backend.GlueDispensingApplication.utils.contours import calculate_mask_overlap

SIMILARITY_THRESHOLD = 80
DEFECT_THRESHOLD = 5

# Global debug flags - Set these to True to enable debugging
DEBUG_SIMILARITY = False
DEBUG_CALCULATE_DIFFERENCES = False
DEBUG_ALIGN_CONTOURS = False


# def _isValid(contour):
#     """Check if the contour is valid."""
#     return contour is not None and len(contour) > 0

def _isValid(sprayPatternList):
    """
  Check if the given spray pattern list is valid.

  Args:
      sprayPatternList (list): A list of spray pattern contours to be validated.

  Returns:
      bool: True if the spray pattern list is not empty and not None, False otherwise.
  """

    return sprayPatternList is not None and len(sprayPatternList) > 0

def findMatchingWorkpieces(workpieces, newContours):
    """
        Find matching workpieces based on new contours and align them.

        This function compares the contours of workpieces with the new contours and aligns them
        based on the similarity and defect thresholds.

        Args:
            workpieces (list): List of workpieces to compare against.
            newContours (list): List of new contours to be matched.

        Returns:
            tuple: A tuple containing:
                - finalMatches (list): List of workpieces that have been aligned and matched.
                - noMatches (list): List of contours that couldn't be matched.
                - newContoursWithMatches (list): List of new contours that have been matched.
        """
    print(f"🔍 ENTERING findMatchingWorkpieces with {len(workpieces)} workpieces and {len(newContours)} contours")
    """FIND MATCHES BETWEEN NEW CONTOURS AND WORKPIECES."""
    USE_COMPARISON_MODEL = False
    if USE_COMPARISON_MODEL:
        matched, noMatches, newContoursWithMatches = match_workpiece(workpieces,newContours)
    else:

        matched, noMatches, newContoursWithMatches = _findMatches(newContours,workpieces)


    """ALIGN MATCHED CONTOURS."""
    finalMatches = _alignContours(matched, defectsThresh=DEFECT_THRESHOLD, debug=DEBUG_ALIGN_CONTOURS)

    # print(f"Final Matched {len(finalMatches)} workpieces")
    return finalMatches, noMatches, newContoursWithMatches
    # return matched, noMatches, newContoursWithMatches

def _remove_contour(newContours, contour_to_remove):
    """
   Safely remove an exact matching contour from the newContours list.

   Args:
       newContours (list): List of contours from which the matching contour should be removed.
       contour_to_remove (array): The contour to be removed.

   Returns:
       None
   """

    for i, stored_contour in enumerate(newContours):
        if np.array_equal(stored_contour, contour_to_remove):
            del newContours[i]  # Remove the matching contour
            print(f"Removed Contour")
            return
    print(f"Error: Could not find an exact match to remove.")

def match_workpiece(workpieces_list, newContours: list[np.ndarray]):
    """
    ML-based version of _findMatches.
    Compares each new contour with known workpieces using the trained model.

    Returns:
        matched (list): List of dicts containing match info (same structure as _findMatches)
        noMatches (list): List of new contours that could not be matched
        newContourWithMatches (list): List of contours that were matched
    """

    print("Finding matches using ML model...")
    from pathlib import Path

    # Resolve saved_models relative to this file so the code doesn't rely on an absolute path
    model_dir = Path(__file__).resolve().parent / "contourMatching" / "shapeMatchinModelTraining" / "saved_models"

    # If the expected folder doesn't exist (e.g., running from a different layout), try a fallback
    if not model_dir.exists():
        print(f"Warning: model_dir {model_dir} not found. Trying fallback relative to cwd.")
        model_dir = Path.cwd() / "GlueDispensingApplication" / "contourMatching" / "shapeMatchinModelTraining" / "saved_models"

    # model = load_latest_model(save_dir=str(model_dir))

    matched = []
    noMatches = []
    newContourWithMatches = []

    # Work on a copy since we’ll remove processed contours
    remainingContours = newContours.copy()

    # Track ML predictions for ALL contours (even non-matches) for visualization
    ml_predictions = {}  # Store {contour_id: (result, confidence, wp_id)}

    while remainingContours:
        cnt = remainingContours.pop(0)
        cnt = Contour(cnt)  # Convert to Contour object to use the methods
        best_match = None
        best_confidence = 0.0
        best_ml_result = "DIFFERENT"
        best_wp_id = None

        for wp in workpieces_list:

            wp_contour = Contour(wp.get_main_contour())

            result, confidence, features = predict_similarity(model,
                                                       wp_contour.get(),
                                                       cnt.get())

            # CRITICAL: Prioritize SAME results over DIFFERENT, even if DIFFERENT has higher confidence
            # When multiple workpieces exist, we want the one that MATCHES, not the one with highest confidence
            if result == "SAME":
                # For SAME results, prefer higher confidence
                if best_match is None or confidence > best_confidence:
                    best_match = wp
                    best_confidence = confidence
                    best_ml_result = result
                    best_wp_id = wp.workpieceId
                    best_centroid_diff, best_rotation_diff, contourAngle = _calculateDifferences(wp_contour, cnt)
            else:
                # For DIFFERENT/UNCERTAIN, only track if we haven't found a SAME match yet
                if best_match is None and confidence > best_confidence:
                    best_confidence = confidence
                    best_ml_result = result
                    best_wp_id = wp.workpieceId

        # Store ML prediction for this contour
        contour_id = id(cnt.get().tobytes())
        ml_predictions[contour_id] = (best_ml_result, best_confidence, best_wp_id)

        if best_match is not None:
            # Build same structure as _findMatches() with ML confidence added
            matchDict = {
                "workpieces": best_match,
                "newContour": cnt.get(),
                "centroidDiff": best_centroid_diff,
                "rotationDiff": best_rotation_diff,
                "contourOrientation": contourAngle,
                "mlConfidence": best_confidence,  # Add ML confidence to result
                "mlResult": best_ml_result  # Add ML result (SAME/DIFFERENT/UNCERTAIN)
            }
            matched.append(matchDict)
            newContourWithMatches.append(cnt)
            print(f"✅ Matched contour to workpiece {best_match.workpieceId} (confidence={best_confidence:.2f})")

        else:
            print(f"❌ No match found for this contour (best: {best_ml_result} with {best_confidence:.1%} confidence)")
            # Attach ML prediction to the no-match contour for visualization
            cnt._ml_result = best_ml_result
            cnt._ml_confidence = best_confidence
            cnt._ml_wp_id = best_wp_id
            noMatches.append(cnt)

    return matched, noMatches, newContourWithMatches

def _findMatches(newContours, workpieces):
    print(f"Finding matches")
    matched = []
    noMatches = []
    newContourWithMatches = []
    count = 0

    for contour in newContours.copy():
        contour = Contour(contour)
        best_match = None
        best_similarity = -1
        best_centroid_diff = None
        best_rotation_diff = None
        contourAngle = None

        for workpiece in workpieces:
            workpieceContour = Contour(workpiece.get_main_contour())
            if workpieceContour is None:
                continue

            similarity = _getSimilarity(workpieceContour.get(),
                                        contour.get(),
                                        debug=DEBUG_SIMILARITY)

            if similarity > SIMILARITY_THRESHOLD and similarity > best_similarity:
                best_match = workpiece
                best_similarity = similarity
                best_centroid_diff, best_rotation_diff, contourAngle = _calculateDifferences(workpieceContour, contour)

        if best_match is not None:
            # Store matched contour
            newContourWithMatches.append(contour.get())
            matchDict = {
                "workpieces": best_match,
                "newContour": contour.get(),
                "centroidDiff": best_centroid_diff,
                "rotationDiff": best_rotation_diff,
                "contourOrientation": contourAngle
            }
            matched.append(matchDict)
            _remove_contour(newContours, contour.get())

            # --- DRAW MATCH ON FRESH CANVAS ---
            canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # white canvas
            workpieceContour = Contour(best_match.get_main_contour())

            workpieceContour.draw(canvas, color=(0, 255, 0), thickness=2)  # Workpiece in GREEN
            cv2.putText(canvas, f"WP {best_match.workpieceId}", tuple(workpieceContour.getCentroid()), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            contour.draw(canvas, color=(0, 0, 255), thickness=2)  # New contour in RED
            cv2.putText(canvas, "NEW", tuple(contour.getCentroid()), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

            # Add similarity score
            cv2.putText(canvas, f"Similarity: {best_similarity:.1f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

            # Highlight match
            cv2.putText(canvas, "MATCH!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 3)
            cv2.imwrite(f"findMatches_MATCH_{count}.png", canvas)
            count += 1
        else:
            print(f"    No match found for this contour")

    noMatches = newContours
    return matched, noMatches, newContourWithMatches



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


def _alignContours(matched, defectsThresh=5, debug=False):
    """
    Align matched contours to the workpieces by rotating and translating based on differences.

    Args:
        matched (list): List of matched workpieces and their corresponding contour differences.
        defectsThresh (float): Threshold for comparing convexity defects.
        debug (bool): If True, show detailed debug plots of the alignment process.

    Returns:
        list: List of workpieces with aligned contours.
    """
    transformedMatchesDict = {"workpieces": [], "orientations": [], "mlConfidences": [], "mlResults": []}

    for i, match in enumerate(matched):
        workpiece = copy.deepcopy(match["workpieces"])
        newContour = match["newContour"]
        rotationDiff = match["rotationDiff"]
        centroidDiff = match["centroidDiff"]
        contourOrientation = match["contourOrientation"]

        canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255

        newCntObject = Contour(newContour)
        newCntObject.draw(canvas, color=(255, 255, 0), thickness=2)  # Draw the new contour
        main_contour = workpiece.get_main_contour()
        if not _isValid(main_contour):
            raise ValueError("invalid contour")
            continue

        # ✅ Prepare main contour object
        contourObj = Contour(main_contour)
        # ✅ Use the helper methods to get spray pattern data correctly
        sprayContourEntries = workpiece.get_spray_pattern_contours()
        sprayFillEntries = workpiece.get_spray_pattern_fills()

        # print("_alignContours sprayContourEntries: ", len(sprayContourEntries))
        # print("_alignContours sprayFillEntries: ", len(sprayFillEntries))

        # ✅ Create Contour objects for each spray pattern entry
        sprayContourObjs = []
        for entry in sprayContourEntries:
            contour_data = entry.get("contour")
            if contour_data is not None and len(contour_data) > 0:
                obj = Contour(contour_data)
                sprayContourObjs.append(obj)
                # print(f"    Spray Contour OBJ: {obj.get()}")

        sprayFillObjs = []
        for entry in sprayFillEntries:
            contour_data = entry.get("contour")
            if contour_data is not None and len(contour_data) > 0:
                sprayFillObjs.append(Contour(contour_data))

        contourObj.draw(canvas, color=(0, 0, 255), thickness=2)  # Draw the main contour

        # ✅ Apply transformations
        centroid = contourObj.getCentroid()

        # Store original positions for debug visualization
        if debug:
            original_contour = contourObj.get().copy()
            original_new_contour = newContour.copy()
            original_spray_contours = [obj.get().copy() for obj in sprayContourObjs]

        # Rotation
        # print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to External Contour")
        contourObj.rotate(rotationDiff, centroid)
        contourObj.draw(canvas, color=(0, 255, 0), thickness=2)  # Draw the rotated contour

        # Store after rotation for debug
        if debug:
            rotated_contour = contourObj.get().copy()

        # print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to Spray contour")
        for obj in sprayContourObjs:
            obj.rotate(rotationDiff, centroid)

        # print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to Fill contour")
        for obj in sprayFillObjs:
            obj.rotate(rotationDiff, centroid)

        # Translation
        contourObj.translate(*centroidDiff)
        contourObj.draw(canvas, color=(255, 0, 0), thickness=2)  # Draw the translated contour
        # cv2.imwrite("aligned_contour_" + str(i) + ".png", canvas)
        for obj in sprayContourObjs:
            obj.translate(*centroidDiff)
        for obj in sprayFillObjs:
            obj.translate(*centroidDiff)

        # ✅ Mask-based refinement to avoid mirrored shapes
        # print(f"    Performing mask-based alignment refinement...")
        best_rotation, best_overlap = _refine_alignment_with_mask(
            contourObj.get(),
            newContour,
            search_range=2,  # Search ±10 degrees
            step=1  # 1 degree steps
        )

        if abs(best_rotation) > 0.1:  # Apply refinement if significant
            # print(f"    Applying refinement rotation: {best_rotation:.2f}° (overlap: {best_overlap:.4f})")
            centroid_after_translation = contourObj.getCentroid()

            # Apply refinement rotation to all contours
            contourObj.rotate(best_rotation, centroid_after_translation)
            for obj in sprayContourObjs:
                obj.rotate(best_rotation, centroid_after_translation)
            for obj in sprayFillObjs:
                obj.rotate(best_rotation, centroid_after_translation)
        else:
            # print(f"    No refinement needed (overlap: {best_overlap:.4f})")
            pass
        # Store final position for debug
        if debug:
            final_contour = contourObj.get().copy()

        # Debug visualization for _alignContours
        if debug:
            import matplotlib.pyplot as plt
            from pathlib import Path
            import datetime

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

            # Plot 1: Original positions
            orig_points = original_contour.reshape(-1, 2) if len(original_contour.shape) == 3 else original_contour
            new_points = original_new_contour.reshape(-1, 2) if len(
                original_new_contour.shape) == 3 else original_new_contour

            ax1.plot(orig_points[:, 0], orig_points[:, 1], 'b-', linewidth=2, label=f'Original Workpiece')
            ax1.plot(new_points[:, 0], new_points[:, 1], 'r-', linewidth=2, label='New Contour (Target)')
            ax1.plot(centroid[0], centroid[1], 'bo', markersize=8, label=f'Rotation Pivot: {centroid}')

            # Draw spray contours if available
            for idx, spray_contour in enumerate(original_spray_contours):
                spray_points = spray_contour.reshape(-1, 2) if len(spray_contour.shape) == 3 else spray_contour
                ax1.plot(spray_points[:, 0], spray_points[:, 1], 'g--', linewidth=1, alpha=0.7,
                         label=f'Spray Pattern {idx + 1}' if idx == 0 else "")

            ax1.set_title(f'Step 1: Original Position\nWorkpiece ID: {workpiece.workpieceId}')
            ax1.set_aspect('equal')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Plot 2: After rotation
            rot_points = rotated_contour.reshape(-1, 2) if len(rotated_contour.shape) == 3 else rotated_contour

            ax2.plot(orig_points[:, 0], orig_points[:, 1], 'b--', linewidth=1, alpha=0.5, label='Original')
            ax2.plot(rot_points[:, 0], rot_points[:, 1], 'g-', linewidth=2,
                     label=f'After Rotation ({rotationDiff:.1f}°)')
            ax2.plot(new_points[:, 0], new_points[:, 1], 'r-', linewidth=2, label='Target')
            ax2.plot(centroid[0], centroid[1], 'ko', markersize=8, label='Rotation Pivot')

            # Draw rotation arc
            from matplotlib.patches import Arc
            arc_radius = 50
            arc = Arc((centroid[0], centroid[1]), 2 * arc_radius, 2 * arc_radius,
                      angle=0, theta1=0, theta2=abs(rotationDiff),
                      color='purple', linewidth=2, linestyle='--')
            ax2.add_patch(arc)

            ax2.set_title(f'Step 2: After Rotation\nRotation: {rotationDiff:.1f}° around {centroid}')
            ax2.set_aspect('equal')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

            # Plot 3: Final alignment
            final_points = final_contour.reshape(-1, 2) if len(final_contour.shape) == 3 else final_contour

            ax3.plot(rot_points[:, 0], rot_points[:, 1], 'g--', linewidth=1, alpha=0.5, label='After Rotation')
            ax3.plot(final_points[:, 0], final_points[:, 1], 'm-', linewidth=2, label='Final Aligned')
            ax3.plot(new_points[:, 0], new_points[:, 1], 'r-', linewidth=2, label='Target')

            # Draw translation vector
            rot_centroid = np.mean(rot_points, axis=0)
            new_centroid = np.mean(new_points, axis=0)
            ax3.arrow(rot_centroid[0], rot_centroid[1],
                      centroidDiff[0], centroidDiff[1],
                      head_width=15, head_length=20, fc='orange', ec='orange',
                      label=f'Translation: {centroidDiff}')

            ax3.set_title(f'Step 3: Final Alignment\nTranslation: {centroidDiff}')
            ax3.set_aspect('equal')
            ax3.grid(True, alpha=0.3)
            ax3.legend()

            # Plot 4: Transformation summary
            ax4.text(0.1, 0.9, f'Workpiece ID: {workpiece.workpieceId}', transform=ax4.transAxes, fontsize=12,
                     weight='bold')
            ax4.text(0.1, 0.8, f'Rotation Applied: {rotationDiff:.1f}°', transform=ax4.transAxes, fontsize=11)
            ax4.text(0.1, 0.7, f'Rotation Pivot: ({centroid[0]:.1f}, {centroid[1]:.1f})', transform=ax4.transAxes,
                     fontsize=11)
            ax4.text(0.1, 0.6, f'Translation: ({centroidDiff[0]:.1f}, {centroidDiff[1]:.1f})', transform=ax4.transAxes,
                     fontsize=11)
            ax4.text(0.1, 0.5, f'Contour Orientation: {contourOrientation:.1f}°', transform=ax4.transAxes, fontsize=11)

            # Summary stats
            ax4.text(0.1, 0.4, 'Transformation Summary:', transform=ax4.transAxes, fontsize=12, weight='bold')
            ax4.text(0.1, 0.3, f'• Spray Contours: {len(sprayContourObjs)}', transform=ax4.transAxes, fontsize=10)
            ax4.text(0.1, 0.25, f'• Fill Contours: {len(sprayFillObjs)}', transform=ax4.transAxes, fontsize=10)
            ax4.text(0.1, 0.2, f'• Main Contour Points: {len(final_points)}', transform=ax4.transAxes, fontsize=10)

            # Status
            ax4.text(0.1, 0.1, '✅ Alignment Complete', transform=ax4.transAxes, fontsize=12,
                     weight='bold', color='green')

            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title(f'Alignment Summary\nMatch #{i + 1}')

            plt.tight_layout()

            # Save debug image to `debug` folder
            debug_dir = Path(__file__).resolve().parent / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"align_debug_wp{workpiece.workpieceId}_match{i + 1}_{timestamp}.png"
            filepath = debug_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"🔍 Alignment debug plot saved: {filepath}")

            # plt.show(block=True)
            plt.close(fig)

        # ✅ Update the workpiece with transformed contours
        workpiece.contour = {"contour": contourObj.get(), "settings": {}}

        # ✅ Update spray pattern contours correctly
        if sprayContourObjs and "Contour" in workpiece.sprayPattern:
            for i, obj in enumerate(sprayContourObjs):
                if i < len(workpiece.sprayPattern["Contour"]):
                    workpiece.sprayPattern["Contour"][i]["contour"] = obj.get()

        if sprayFillObjs and "Fill" in workpiece.sprayPattern:
            for i, obj in enumerate(sprayFillObjs):
                if i < len(workpiece.sprayPattern["Fill"]):
                    workpiece.sprayPattern["Fill"][i]["contour"] = obj.get()

        # ✅ Update pickup point if it exists
        if hasattr(workpiece, 'pickupPoint') and workpiece.pickupPoint is not None:
            # Parse pickup point string if needed
            if isinstance(workpiece.pickupPoint, str):
                try:
                    x_str, y_str = workpiece.pickupPoint.split(',')
                    pickup_x, pickup_y = float(x_str), float(y_str)
                    print(f"  📍 Original pickup point: ({pickup_x:.1f}, {pickup_y:.1f})")

                    # Apply the same transformations as applied to contours
                    # 1. Apply rotation around the centroid
                    pickup_point = np.array([[pickup_x, pickup_y]], dtype=np.float32)
                    pickup_contour_obj = Contour(pickup_point.reshape(-1, 1, 2))
                    pickup_contour_obj.rotate(rotationDiff, pivot=centroid)
                    pickup_contour_obj.translate(centroidDiff[0], centroidDiff[1])

                    # Get transformed coordinates
                    transformed_pickup = pickup_contour_obj.get()[0][0]  # Extract the point
                    transformed_x, transformed_y = transformed_pickup[0], transformed_pickup[1]

                    # Update workpiece with transformed pickup point
                    workpiece.pickupPoint = f"{transformed_x:.2f},{transformed_y:.2f}"
                    print(f"  📍 Transformed pickup point: ({transformed_x:.1f}, {transformed_y:.1f})")

                except (ValueError, AttributeError) as e:
                    print(f"  ⚠️ Invalid pickup point format '{workpiece.pickupPoint}': {e}")
            else:
                print(f"  📍 Pickup point already in correct format: {workpiece.pickupPoint}")

        # Compare contours
        print(f"SKIP: _compareContoursHullAndDefects FOR DEBUGGING")


        transformedMatchesDict["workpieces"].append(workpiece)
        transformedMatchesDict["orientations"].append(contourOrientation)
        # Preserve ML confidence from the original match dictionary
        transformedMatchesDict["mlConfidences"].append(match.get("mlConfidence", 0.0))
        transformedMatchesDict["mlResults"].append(match.get("mlResult", "UNKNOWN"))
        external = workpiece.get_main_contour()
        # print(f"    Transformed Match {i + 1}: {external}")
    return transformedMatchesDict


def _calculateDifferences(workpieceContour, contour):
    """
       Calculate the centroid and rotation differences between two contours.

       Args:
           workpieceContour (Contour): Contour object representing the workpieces contour.
           contour (Contour): Contour object representing the new contour.

       Returns:
           tuple: Centroid difference (numpy array) and rotation difference (float).
       """

    # check if the new contour last point is different then the first point if so close the contour
    if not np.array_equal(contour.get()[0], contour.get()[-1]):
        print("    Closing contour by adding first point to the end")
        closed_points = np.vstack([
            contour.get(),
            contour.get()[0].reshape(1, 1, 2)
        ])

        contour = Contour(closed_points)

    # print(f"    Calculating differences between: ")
    # print(f"        Workpiece Contour: {workpieceContour.get()}")
    # print(f"        New Contour: {contour.get()}")


    workpieceCentroid = workpieceContour.getCentroid()
    contourCentroid = contour.getCentroid()
    centroidDiff = np.array(contourCentroid) - np.array(workpieceCentroid)

    wpAngle = workpieceContour.getOrientation()
    contourAngle = contour.getOrientation()

    rotationDiff = contourAngle - wpAngle

    rotationDiff = (rotationDiff + 180) % 360 - 180  # Normalize to [-180, 180]

    from pathlib import Path

    # ... after computing wpAngle, contourAngle, rotationDiff ...
    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    file_path = debug_dir / "contour_debug.txt"

    with file_path.open("w", encoding="utf-8") as f:
        f.write(f"Workpiece orientation: {wpAngle}\n")
        f.write(f"Workpiece points: {workpieceContour.get()}\n")
        f.write(f"Contour orientation: {contourAngle}\n")
        f.write(f"Contour points: {contour.get()}\n")
        f.write(f"Calculated rotation difference: {rotationDiff}\n")

    print(f"Contour debug written to: {file_path}")

    # Debug plotting for _calculateDifferences
    if DEBUG_CALCULATE_DIFFERENCES:
        import matplotlib.pyplot as plt

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # Plot workpiece contour
        wp_points = workpieceContour.get()
        if len(wp_points.shape) == 3:
            wp_plot = wp_points.reshape(-1, 2)
        else:
            wp_plot = wp_points
        ax1.plot(wp_plot[:, 0], wp_plot[:, 1], 'b-', linewidth=2, marker='o')
        ax1.plot(workpieceCentroid[0], workpieceCentroid[1], 'bo', markersize=10, label=f'Centroid {workpieceCentroid}')
        ax1.set_title(f'Workpiece Contour\nAngle: {wpAngle:.2f}°')
        ax1.set_aspect('equal')
        ax1.grid(True)
        ax1.legend()

        # Plot new contour
        new_points = contour.get()
        if len(new_points.shape) == 3:
            new_plot = new_points.reshape(-1, 2)
        else:
            new_plot = new_points
        ax2.plot(new_plot[:, 0], new_plot[:, 1], 'r-', linewidth=2, marker='s')
        ax2.plot(contourCentroid[0], contourCentroid[1], 'ro', markersize=10, label=f'Centroid {contourCentroid}')
        ax2.set_title(f'New Contour\nAngle: {contourAngle:.2f}°')
        ax2.set_aspect('equal')
        ax2.grid(True)
        ax2.legend()

        # Plot both contours overlaid
        ax3.plot(wp_plot[:, 0], wp_plot[:, 1], 'b-', linewidth=2, label='Workpiece', alpha=0.7)
        ax3.plot(new_plot[:, 0], new_plot[:, 1], 'r-', linewidth=2, label='New Contour', alpha=0.7)
        ax3.plot(workpieceCentroid[0], workpieceCentroid[1], 'bo', markersize=8, label='WP Centroid')
        ax3.plot(contourCentroid[0], contourCentroid[1], 'ro', markersize=8, label='New Centroid')

        # Draw centroid difference vector
        ax3.arrow(workpieceCentroid[0], workpieceCentroid[1],
                 centroidDiff[0], centroidDiff[1],
                 head_width=10, head_length=15, fc='g', ec='g',
                 label=f'Centroid Diff: {centroidDiff}')

        ax3.set_title(f'Overlay View\nCentroid Diff: {centroidDiff}\nRotation Diff: {rotationDiff:.2f}°')
        ax3.set_aspect('equal')
        ax3.grid(True)
        ax3.legend()

        # Plot angle visualization
        angles = [wpAngle, contourAngle]
        labels = ['Workpiece', 'New Contour']
        colors = ['blue', 'red']

        ax4.bar(labels, angles, color=colors, alpha=0.7)
        ax4.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax4.set_ylabel('Angle (degrees)')
        ax4.set_title(f'Orientation Comparison\nDifference: {rotationDiff:.2f}°')
        ax4.grid(True, alpha=0.3)

        # Add text annotation
        ax4.text(0.5, max(angles) * 0.8, f'Rotation Diff:\n{rotationDiff:.2f}°',
                horizontalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

        plt.tight_layout()
        plt.show(block=False)

    return centroidDiff, rotationDiff, contourAngle


# def _getSimilarity(contour1, contour2, debug=True):
#     """
#     Simplified contour similarity test using only Hu moments.
#     Returns a percentage similarity score.
#     """
#     MOMENT_THRESHOLD = 0.05  # Only used for debug tagging
#
#     contour1 = np.array(contour1, dtype=np.float32)
#     contour2 = np.array(contour2, dtype=np.float32)
#     print(f"Calculating similarity between contours of lengths {len(contour1)} and {len(contour2)}")
#     # Compute Hu moments distance
#     moment_diff = cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I1, 0.0)
#     print(f"raw_similarity (moment diff): {moment_diff:.4f}")
#     similarity_percent = (1 - moment_diff) * 100
#     # moment_diff = np.clip(moment_diff, 0.0, 1.0)
#     # similarity_percent = float(np.clip(100 * np.exp(-moment_diff * 10), 0, 100))
#
#     # --- Area penalty ---
#     area1 = cv2.contourArea(contour1)
#     area2 = cv2.contourArea(contour2)
#     area_diff= abs(area1-area2)
#     area_ratio= 0
#     if area1 > 0 and area2 > 0:
#         area_ratio = min(area1, area2) / max(area1, area2)
#
#         AREA_TOLERANCE = 0.90  # Allow 10% difference
#         if area_ratio < AREA_TOLERANCE:
#             # Penalize only if area difference exceeds tolerance
#             similarity_percent *= area_ratio ** 2  # square makes it harsher
#     else:
#         similarity_percent = 0
#
#     similarity_percent = float(np.clip(similarity_percent, 0, 100))
#
#     # Store metrics for debugging
#     metrics = {
#         "moment_diff": moment_diff,
#         "area_ratio":area_ratio,
#         "area_diff":area_diff,
#         "similarity_percent": similarity_percent,
#     }
#
#     if debug:
#         _create_debug_plot(contour1, contour2, metrics)
#     print(f"Similarity Score: {similarity_percent:.2f}% (Moment Diff: {moment_diff:.4f})")
#     return similarity_percent

def _getSimilarity(contour1, contour2, debug=True):
    """
    Simplified contour similarity test using only area difference.
    Returns a percentage similarity score based on area ratio.
    """
    contour1 = np.array(contour1, dtype=np.float32)
    contour2 = np.array(contour2, dtype=np.float32)

    print(f"Calculating similarity between contours of lengths {len(contour1)} and {len(contour2)}")

    # Compute areas
    area1 = cv2.contourArea(contour1)
    area2 = cv2.contourArea(contour2)
    area_diff = abs(area1 - area2)

    if area1 > 0 and area2 > 0:
        # Compute area ratio
        area_ratio = min(area1, area2) / max(area1, area2)
        similarity_percent = area_ratio * 100
    else:
        area_ratio = 0
        similarity_percent = 0

    # Clip to [0, 100]
    similarity_percent = float(np.clip(similarity_percent, 0, 100))

    # Store metrics for debugging
    metrics = {
        "area1": area1,
        "area2": area2,
        "area_diff": area_diff,
        "area_ratio": area_ratio,
        "similarity_percent": similarity_percent,
        "moment_diff": 0
    }

    if debug:
        _create_debug_plot(contour1, contour2, metrics)

    print(f"Similarity Score: {similarity_percent:.2f}% (Area Diff: {area_diff:.2f})")
    return similarity_percent



def _create_debug_plot(contour1, contour2, metrics):
    """Helper function to create debug plots for similarity analysis with all metrics."""
    import matplotlib.pyplot as plt
    from pathlib import Path
    import datetime

    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)


    print("Creating similarity debug plot...")

    # Unpack metrics safely
    moment_diff = metrics.get("moment_diff", None)
    area_diff = metrics.get("area_diff", None)
    area_ratio = metrics.get("area_ratio", None)
    similarity_percent = metrics.get("similarity_percent", 0)

    # Prepare contour data for plotting
    points1 = contour1.reshape(-1, 2) if len(contour1.shape) == 3 else contour1
    points2 = contour2.reshape(-1, 2) if len(contour2.shape) == 3 else contour2

    # Calculate bounding box width and height for both contours and print
    def _bbox_size(pts):
        if pts is None or len(pts) == 0:
            return 0.0, 0.0
        xs = pts[:, 0]
        ys = pts[:, 1]
        width = float(xs.max() - xs.min())
        height = float(ys.max() - ys.min())
        return width, height

    w1, h1 = _bbox_size(points1)
    w2, h2 = _bbox_size(points2)
    print(f"Contour 1 size: width={w1:.2f}, height={h1:.2f} | Contour 2 size: width={w2:.2f}, height={h2:.2f}")

    # Save both corners to the `debug` folder (numpy and readable text)
    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    np.save(debug_dir / f"corner1_{timestamp}.npy", points1)
    np.save(debug_dir / f"corner2_{timestamp}.npy", points2)
    np.savetxt(debug_dir / f"corner1_{timestamp}.txt", points1, fmt="%f")
    np.savetxt(debug_dir / f"corner2_{timestamp}.txt", points2, fmt="%f")

    # Create figure
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # Contour 1
    ax1.plot(points1[:, 0], points1[:, 1], 'b-', linewidth=2, marker='o', markersize=3)
    ax1.set_title('Contour 1 (Reference)')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.invert_yaxis()

    # Contour 2
    ax2.plot(points2[:, 0], points2[:, 1], 'r-', linewidth=2, marker='s', markersize=3)
    ax2.set_title('Contour 2 (Test)')
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.invert_yaxis()

    # Overlay
    ax3.plot(points1[:, 0], points1[:, 1], 'b-', linewidth=2, label='Contour 1', alpha=0.7)
    ax3.plot(points2[:, 0], points2[:, 1], 'r-', linewidth=2, label='Contour 2', alpha=0.7)
    ax3.set_title(f'Overlay - Similarity: {similarity_percent:.2f}%')
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.invert_yaxis()

    # ============================
    # Annotate with all metrics
    # ============================
    metrics_text = (
        f"moment_diff: {moment_diff:.4f}\n"
        f"area_diff: {area_diff if area_diff is not None else 'N/A'}\n"
        f"area_ratio: {area_ratio:.2f}%\n"
        f"similarity: {similarity_percent:.2f}%\n"
    )

    # Decide pass/fail based on similarity
    if similarity_percent >= 90:
        color = 'green'
        status = 'PASSED'
    else:
        color = 'red'
        status = 'FAILED'

    ax3.text(
        0.02, 0.98,
        f"{status}\n{metrics_text}",
        transform=ax3.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=color, alpha=0.7, edgecolor='black')
    )

    plt.tight_layout()

    # ============================
    # Save debug image
    # ============================
    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"similarity_debug_{timestamp}_{similarity_percent:.1f}pct.png"
    filepath = debug_dir / filename

    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"🔍 Similarity debug plot saved: {filepath}")
    plt.close()

