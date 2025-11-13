import numpy as np
import cv2

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

def plot_contour_alignment(original_contour, original_new_contour,centroid,original_spray_contours,workpiece,rotated_contour,final_contour,rotationDiff,centroidDiff,contourOrientation,sprayContourObjs,sprayFillObjs,i):
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

def get_similarity_debug_plot(workpieceContour, contour, workpieceCentroid, contourCentroid, wpAngle, contourAngle, centroidDiff, rotationDiff):
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