import numpy as np

from modules.shared.core.ContourStandartized import Contour


def transform_pickup_point(workpiece, rotationDiff, centroidDiff, centroid):
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
                return [transformed_x, transformed_y]
            except(ValueError, AttributeError) as e:
                print(f"  ⚠️ Invalid pickup point format '{workpiece.pickupPoint}': {e}")
    return None