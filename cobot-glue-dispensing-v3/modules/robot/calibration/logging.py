from typing import Optional, List, Dict, Tuple, Set, Any

import numpy as np


def get_log_timing_summary(state_timings):
    """
    Construct and return a detailed timing summary for calibration state durations.

    Args:
        state_timings (dict[str, list[float]]): Mapping of state names to lists of duration values.

    Returns:
        str: A formatted multi-line string containing total times, averages, and bottleneck analysis.
    """
    if not state_timings:
        return "⚠️ No timing data available."

    lines = ["📊 === CALIBRATION TIMING ANALYSIS ==="]
    total_time = 0

    # Compute per-state statistics
    for state_name, durations in state_timings.items():
        total_duration = sum(durations)
        avg_duration = total_duration / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        count = len(durations)

        total_time += total_duration

        lines.append(f"\n🔍 {state_name}:")
        lines.append(f"   Total: {total_duration:.3f}s | Avg: {avg_duration:.3f}s | Count: {count}")
        lines.append(f"   Min: {min_duration:.3f}s | Max: {max_duration:.3f}s")

    # Summary
    lines.append(f"\n🚀 Total calibration time: {total_time:.3f} seconds")

    # Bottleneck analysis
    state_percentages = {}
    for state_name, durations in state_timings.items():
        total_duration = sum(durations)
        percentage = (total_duration / total_time) * 100
        state_percentages[state_name] = percentage

    sorted_bottlenecks = sorted(state_percentages.items(), key=lambda x: x[1], reverse=True)
    lines.append("\n🎯 BOTTLENECK ANALYSIS (by % of total time):")

    for state_name, percentage in sorted_bottlenecks:
        indicator = "⚠️" if percentage > 5 else "✅"
        lines.append(f"   {indicator} {state_name}: {percentage:.1f}%")

    return "\n".join(lines)


def construct_chessboard_state_log_message(
    found: bool,
    ppm: Optional[float] = None,
    bottom_left_corner: Optional[np.ndarray] = None,
    debug_enabled: bool = False
) -> str:
    """
    Construct a structured log message describing the LOOKING_FOR_CHESSBOARD state results.

    Args:
        found (bool): Whether the chessboard was successfully detected.
        ppm (Optional[float]): Pixels-per-millimeter value computed from the chessboard.
        bottom_left_corner (Optional[np.ndarray]): Pixel coordinates of the bottom-left chessboard corner.
        chessboard_center (Optional[np.ndarray]): Pixel coordinates of the chessboard center.
        debug_enabled (bool): Whether debug drawing is active.

    Returns:
        str: Formatted multi-line message summarizing the chessboard detection step.
    """
    lines = ["🧩 === CHESSBOARD DETECTION SUMMARY ==="]

    if not found:
        lines.append("❌ Chessboard not found. Retrying...")
        return "\n".join(lines)

    lines.append(f"✅ Chessboard found successfully.")
    if ppm is not None:
        lines.append(f"   • Pixels per millimeter (PPM): {ppm:.3f}")

    # Bottom-left corner info
    if bottom_left_corner is not None:
        corner_int = tuple(bottom_left_corner.astype(int))
        lines.append(f"   • Bottom-left corner (px): {corner_int}")
    else:
        lines.append("⚠️  Bottom-left corner not defined.")



    # Debug mode note
    if debug_enabled:
        lines.append("🔧 Debug mode: image center drawn on frame.")

    return "\n".join(lines)

def construct_aruco_state_log_message(
    detected_ids: Set[Any],
    marker_top_left_corners_px: Dict[int, Tuple[float, float]],
    marker_top_left_corners_mm: Optional[Dict[int, Tuple[float, float]]] = None,
    ppm: Optional[float] = None,
    bottom_left_corner_px: Optional[np.ndarray] = None,
) -> str:
    """
    Construct a structured log message summarizing the ALL_ARUCO_FOUND state.

    Args:
        detected_ids (List[int]): List of detected ArUco marker IDs.
        marker_top_left_corners_px (Dict[int, Tuple[float, float]]): Top-left corner pixel positions for each marker.
        marker_top_left_corners_mm (Optional[Dict[int, Tuple[float, float]]]): Converted millimeter positions.
        ppm (Optional[float]): Pixels per millimeter value (used for conversion).
        bottom_left_corner_px (Optional[np.ndarray]): Bottom-left chessboard corner in pixels.

    Returns:
        str: Multi-line formatted message summarizing ArUco marker detection results.
    """
    lines = ["🏁 === ARUCO MARKER DETECTION SUMMARY ==="]

    # Basic marker detection
    if not detected_ids:
        lines.append("❌ No ArUco markers detected.")
        return "\n".join(lines)

    lines.append(f"✅ All required ArUco markers found: {detected_ids}")

    # Pixel-space information
    lines.append("📍 Marker top-left corners (px):")
    for marker_id, coords in marker_top_left_corners_px.items():
        lines.append(f"   • ID {marker_id}: ({coords[0]:.1f}, {coords[1]:.1f})")

    # Conversion info
    if ppm is not None and bottom_left_corner_px is not None:
        lines.append(f"🧮 Conversion: using PPM={ppm:.3f} and bottom-left corner={tuple(bottom_left_corner_px.astype(int))}")
    elif ppm is None:
        lines.append("⚠️  Cannot compute mm coordinates: PPM not defined.")
    elif bottom_left_corner_px is None:
        lines.append("⚠️  Cannot compute mm coordinates: bottom-left corner missing.")

    # Millimeter-space info
    if marker_top_left_corners_mm:
        lines.append("📏 Marker top-left corners (mm relative to bottom-left):")
        for marker_id, coords_mm in marker_top_left_corners_mm.items():
            lines.append(f"   • ID {marker_id}: ({coords_mm[0]:.3f}, {coords_mm[1]:.3f})")

    return "\n".join(lines)


def construct_compute_offsets_log_message(
    ppm: Optional[float],
    bottom_left_corner_px: Optional[np.ndarray],
    image_center_px: Optional[Tuple[int, int]],
    marker_top_left_corners_mm: Dict[int, Tuple[float, float]],
    markers_offsets_mm: Optional[Dict[int, Tuple[float, float]]] = None,
) -> str:
    """
    Construct a detailed log message summarizing the COMPUTE_OFFSETS stage of calibration.

    Args:
        ppm (Optional[float]): Pixels per millimeter calibration constant.
        bottom_left_corner_px (Optional[np.ndarray]): Bottom-left chessboard corner in pixels.
        image_center_px (Optional[Tuple[int, int]]): Camera image center in pixels.
        marker_top_left_corners_mm (Dict[int, Tuple[float, float]]): Marker positions in mm relative to bottom-left.
        markers_offsets_mm (Optional[Dict[int, Tuple[float, float]]]): Computed offsets from image center.

    Returns:
        str: Multi-line human-readable calibration summary.
    """
    lines = ["📐 === ROBOT CALIBRATION OFFSET COMPUTATION ==="]

    if ppm is None:
        lines.append("⚠️  Cannot compute offsets: PPM (pixels per mm) is undefined.")
        return "\n".join(lines)

    if bottom_left_corner_px is None:
        lines.append("⚠️  Cannot compute offsets: Bottom-left chessboard corner is missing.")
        return "\n".join(lines)

    if image_center_px is None:
        lines.append("⚠️  Cannot compute offsets: Image center is unavailable.")
        return "\n".join(lines)

    # Summarize input geometry
    lines.append(f"🧮 Using PPM = {ppm:.3f}")
    lines.append(f"📍 Bottom-left corner (px): {tuple(bottom_left_corner_px.astype(int))}")
    lines.append(f"🎯 Image center (px): {image_center_px}")

    # Compute image center in mm relative to bottom-left
    center_x_mm = (image_center_px[0] - bottom_left_corner_px[0]) / ppm
    center_y_mm = (bottom_left_corner_px[1] - image_center_px[1]) / ppm
    lines.append(f"📏 Image center in mm (relative to bottom-left): ({center_x_mm:.2f}, {center_y_mm:.2f})")

    # Marker offsets
    if not marker_top_left_corners_mm:
        lines.append("⚠️  No marker positions available for offset computation.")
        return "\n".join(lines)

    lines.append("🔹 Marker offsets from image center (in mm):")
    for marker_id, (mx, my) in marker_top_left_corners_mm.items():
        offset_x = mx - center_x_mm
        offset_y = my - center_y_mm
        lines.append(f"   • ID {marker_id}: pos=({mx:.2f}, {my:.2f}) → offset=(X={offset_x:.2f}, Y={offset_y:.2f})")

    return "\n".join(lines)

def construct_align_robot_log_message(
    marker_id: int,
    calib_to_marker: Tuple[float, float],
    current_pose: Tuple[float, float, float, float, float, float],
    calib_pose: Tuple[float, float, float, float, float, float],
    z_target: float,
    result: Optional[int] = None,
    retry_attempted: bool = False,
) -> str:
    """
    Construct a detailed log message summarizing the ALIGN_ROBOT stage.

    Args:
        marker_id (int): Current marker being aligned to.
        calib_to_marker (Tuple[float, float]): Offset from calibration pose to marker (mm).
        current_pose (Tuple[float, float, float, float, float, float]): Current robot pose (x, y, z, rx, ry, rz).
        calib_pose (Tuple[float, float, float, float, float, float]): Calibration reference pose.
        z_target (float): Z target height for movement.
        result (Optional[int]): Result of movement command (0 = success, nonzero = failure).
        retry_attempted (bool): Whether a retry was performed.

    Returns:
        str: Formatted multi-line log summary for this robot alignment step.
    """
    lines = [
        "🤖 === ROBOT ALIGNMENT STEP ===",
        f"🎯 Marker ID: {marker_id}",
        f"📍 Calibration → Marker offset (mm): {calib_to_marker}",
    ]

    x, y, z, rx, ry, rz = current_pose
    cx, cy, cz, crx, cry, crz = calib_pose

    # Compute deltas
    calib_to_current = (x - cx, y - cy)
    current_to_marker = (
        calib_to_marker[0] - calib_to_current[0],
        calib_to_marker[1] - calib_to_current[1],
    )

    # Compute new target pose
    x_new = x + current_to_marker[0]
    y_new = y + current_to_marker[1]
    new_position = [x_new, y_new, z_target, rx, ry, rz]

    # Movement summary
    lines.append(f"⚙️  Calibration → Current offset (mm): {calib_to_current}")
    lines.append(f"📐 Correction to marker (mm): {current_to_marker}")
    lines.append(f"🚀 Target pose for marker {marker_id}: {new_position}")

    # Execution result
    if result is not None:
        if result == 0:
            lines.append(f"✅ Movement to marker {marker_id} succeeded.")
        else:
            lines.append(f"❌ Movement to marker {marker_id} failed.")
            if retry_attempted:
                lines.append("   ↩️  Retried movement after returning to calibration position.")

    lines.append("⏳ Waiting 1s for robot stabilization...")
    return "\n".join(lines)


def construct_iterative_alignment_log_message(
    marker_id: int,
    iteration: int,
    max_iterations: int,
    capture_time: float,
    detection_time: float,
    processing_time: float,
    movement_time: Optional[float] = None,
    stability_time: Optional[float] = None,
    current_error_mm: Optional[float] = None,
    current_error_px: Optional[float] = None,
    offset_mm: Optional[Tuple[float, float]] = None,
    threshold_mm: Optional[float] = None,
    alignment_success: bool = False,
    result: Optional[int] = None
) -> str:
    """
    Construct a structured log summary for the ITERATE_ALIGNMENT state.

    Args:
        marker_id (int): Marker being processed.
        iteration (int): Current iteration number.
        max_iterations (int): Maximum allowed iterations.
        capture_time (float): Time to capture frame.
        detection_time (float): Time to detect ArUco marker.
        processing_time (float): Time for error computation and data updates.
        movement_time (float, optional): Time for robot movement.
        stability_time (float, optional): Time waited for stabilization.
        current_error_mm (float, optional): Current alignment error in mm.
        current_error_px (float, optional): Current alignment error in px.
        offset_mm (tuple, optional): (X, Y) offset in mm.
        threshold_mm (float, optional): Error threshold for success.
        alignment_success (bool): True if alignment succeeded this iteration.
        result (int, optional): Movement command result (0=success, nonzero=failure).

    Returns:
        str: A formatted multi-line log summary.
    """
    lines = [
        "🔁 === ITERATIVE ALIGNMENT ===",
        f"🎯 Marker ID: {marker_id}",
        f"🧭 Iteration: {iteration}/{max_iterations}",
        f"⏱️ Frame capture time: {capture_time:.3f}s",
        f"⏱️ Detection time: {detection_time:.3f}s",
        f"⏱️ Processing time: {processing_time:.3f}s"
    ]

    if movement_time is not None:
        lines.append(f"⏱️ Movement time: {movement_time:.3f}s")
    if stability_time is not None:
        lines.append(f"⏱️ Stability wait: {stability_time:.3f}s")

    if current_error_mm is not None:
        lines.append(f"📏 Current error: {current_error_mm:.3f} mm ({current_error_px:.1f} px)")
    if offset_mm is not None:
        lines.append(f"↔️ Offset (mm): X={offset_mm[0]:.3f}, Y={offset_mm[1]:.3f}")

    if alignment_success:
        lines.append(f"✅ Alignment successful — error {current_error_mm:.3f} mm ≤ threshold {threshold_mm:.3f} mm")
    else:
        lines.append(f"🔄 Continuing alignment... target threshold: {threshold_mm:.3f} mm")

    if result is not None and result != 0:
        lines.append(f"⚠️ Movement failed (result code {result})")

    return "\n".join(lines)

def construct_calibration_completion_log_message(
    sorted_robot_items,
    sorted_camera_items,
    H_camera_center,
    status,
    average_error_camera_center,
    matrix_path,
    total_calibration_time
) -> str:
    """
    Construct a structured log message summarizing the calibration completion phase.

    Args:
        sorted_robot_items (list): List of (marker_id, robot_position) pairs.
        sorted_camera_items (list): List of (marker_id, camera_point) pairs.
        H_camera_center (np.ndarray): Computed homography matrix.
        status (np.ndarray): Homography computation status array.
        average_error_camera_center (float): Mean reprojection error in mm.
        matrix_path (str): File path where matrix is saved.
        total_calibration_time (float): Total duration of calibration in seconds.

    Returns:
        str: Multi-line structured summary log.
    """
    lines = [
        "🎯 === CALIBRATION COMPLETE ===",
        f"📍 Total markers processed: {len(sorted_robot_items)}",
        "",
        "🤖 Robot positions (mm):"
    ]

    for marker_id, position in sorted_robot_items:
        lines.append(f"  • ID {marker_id}: {np.round(position, 3).tolist()}")

    lines.append("")
    lines.append("📸 Camera points (px):")
    for marker_id, point in sorted_camera_items:
        lines.append(f"  • ID {marker_id}: {np.round(point, 3).tolist()}")

    lines.append("")
    lines.append(f"🧮 Homography computation status: {status.ravel().tolist()}")
    lines.append("📐 Homography matrix:")
    lines.append(np.array2string(H_camera_center, formatter={'float_kind':lambda x: f'{x:8.3f}'}))

    if average_error_camera_center > 1:
        lines.append(f"⚠️  Average reprojection error: {average_error_camera_center:.3f} mm (too high — recalibration recommended)")
    else:
        lines.append(f"✅ Average reprojection error: {average_error_camera_center:.3f} mm (acceptable)")
        lines.append(f"💾 Matrix saved to: {matrix_path}")

    lines.append("")
    lines.append(f"⏱️ Total calibration time: {total_calibration_time:.3f} seconds")
    lines.append("📊 Detailed timing summary follows...")

    return "\n".join(lines)
