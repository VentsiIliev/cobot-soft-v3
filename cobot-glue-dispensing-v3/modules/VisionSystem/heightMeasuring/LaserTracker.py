



import os
import sys
import json
import argparse
import cv2
import numpy
import numpy as np



class LaserTrackService:
    """
    Service class for laser-based height measurement from single images.
    Provides a simple shared for height measurement without UI components.
    """
    
    def __init__(self, cam_width=1280, cam_height=720, axis='x', save_file="laser_calibration.json"):
        """
        Initialize LaserTrackService with a headless LaserTracker.
        
        Args:
            cam_width (int): Camera width for image processing
            cam_height (int): Camera height for image processing  
            axis (str): Laser axis ('x' or 'y')
            save_file (str): Calibration file name
        """
        # Initialize tracker with headless configuration (no display)
        self.tracker = LaserTracker(
            cam_width=cam_width,
            cam_height=cam_height,
            hue_min=0,      # Red laser lower hue range
            hue_max=10,     # Red laser upper hue range  
            sat_min=150,    # High saturation for bright laser
            sat_max=255,
            val_min=200,    # High value for bright laser
            val_max=255,
            display_thresholds=False,  # Headless operation
            axis=axis,
            save_file=save_file
        )
        
    def measure_height(self, image):
        """
        Measure workpiece height from a single image.
        
        Args:
            image (np.ndarray): Input image containing laser line
            
        Returns:
            float: Estimated height in mm (if calibrated) or pixels (if not calibrated)
                   Returns None if measurement fails
        """
        try:
            # Process the image through the tracker
            result = self.tracker.run(image)
            
            if isinstance(result, tuple):
                estimated_height, max_disp, max_point = result
                value_in_pixels = estimated_height
            else:
                estimated_height = result
                value_in_pixels = estimated_height
                
            # Return None if no measurement obtained
            if estimated_height is None:
                return False, None,None
                
            # Convert to mm if calibrated, otherwise return pixels
            if hasattr(self.tracker, 'poly_func') and self.tracker.poly_func is not None:
                if estimated_height != 0:
                    height_mm = float(self.tracker.poly_func(estimated_height))
                    return True ,height_mm,value_in_pixels
                else:
                    return True, 0.0,0.0
            else:
                # Return pixel difference if no calibration available
                return True, float(estimated_height),value_in_pixels
                
        except Exception as e:
            print(f"LaserTrackService measurement error: {e}")
            return False, None,None
    
    def is_calibrated(self):
        """
        Check if the laser tracker has calibration data.
        
        Returns:
            bool: True if calibrated, False otherwise
        """
        return hasattr(self.tracker, 'poly_func') and self.tracker.poly_func is not None
    
    def get_calibration_info(self):
        """
        Get information about current calibration.
        
        Returns:
            dict: Calibration information including reference point and calibration points
        """
        return {
            'is_calibrated': self.is_calibrated(),
            'reference_point': self.tracker.reference_point,
            'calibration_points_count': len(self.tracker.calibration_points),
            'axis': self.tracker.axis
        }


class LaserTracker(object):

    def __init__(self, cam_width=1280, cam_height=720, hue_min=20, hue_max=160,
                 sat_min=100, sat_max=255, val_min=200, val_max=256,
                 display_thresholds=False, axis='y',
                 save_file="laser_calibration.json"):
        """
        LaserTracker initialization with HSV thresholds, camera dimensions,
        axis selection ('x' or 'y'), and JSON save/load for calibration.
        """
        self.save_file = os.path.join(os.path.dirname(__file__), save_file)
        self.position_history = []
        self.history_length = 5

        self.centerMM_Y = None
        self.ppmY = 1
        self.diff = None
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.display_thresholds = display_thresholds

        self.capture = None
        self.channels = {'hue': None, 'saturation': None, 'value': None, 'laser': None}

        self.previous_position = None
        self.trail = numpy.zeros((self.cam_height, self.cam_width, 3), numpy.uint8)

        # Reference and calibration data
        self.axis = axis.lower()  # 'x' or 'y'
        self.reference_point = None
        self.calibration_points = []  # list of tuples: (pixel_diff, real_height)

        # Try to load saved JSON calibration
        self.load_calibration_data()

    # ========================== JSON Save/Load ==========================
    def save_calibration_data(self):
        """
        Save zero reference, calibration points, and poly coefficients to JSON.
        """
        # Convert any numpy.float32 to native float
        reference_point = float(self.reference_point) if self.reference_point is not None else None
        calibration_points = [
            (float(px), float(real)) for px, real in self.calibration_points
        ]

        data = {
            "axis": self.axis,
            "reference_point_y": reference_point,
            "calibration_points": calibration_points,
            "poly_coeffs": self.poly_func.coefficients.tolist() if hasattr(self, 'poly_func') else None
        }
        with open(self.save_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Calibration data saved to {self.save_file}")

    def load_calibration_data(self):
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                data = json.load(f)
            if data.get("axis") == self.axis:
                self.reference_point = data.get("reference_point_y")
                self.calibration_points = data.get("calibration_points", [])
                poly_coeffs = data.get("poly_coeffs")
                if poly_coeffs:
                    self.poly_func = numpy.poly1d(poly_coeffs)
                    print("✅ Calibration model loaded from JSON.")
                print(f"✅ Loaded calibration data: zero reference={self.reference_point}, "
                      f"{len(self.calibration_points)} calibration points")
            else:
                print(f"⚠️ Saved calibration data axis mismatch (saved: {data.get('axis')}, current: {self.axis})")
        else:
            print("ℹ️ No saved calibration data found — you may need to calibrate.")

    # ========================== Camera & Windows ==========================
    def create_and_position_window(self, name, xpos, ypos):
        cv2.namedWindow(name)
        cv2.resizeWindow(name, self.cam_width, self.cam_height)
        cv2.moveWindow(name, xpos, ypos)

    def setup_camera_capture(self, device_num=1):
        try:
            device = int(device_num)
        except (IndexError, ValueError):
            device = 0
        self.capture = cv2.VideoCapture(device)
        if not self.capture.isOpened():
            sys.exit("Failed to open capture device.")
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)
        return self.capture

    # ========================== Image Processing ==========================
    def threshold_image(self, channel):
        if channel == "hue":
            minimum, maximum = self.hue_min, self.hue_max
        elif channel == "saturation":
            minimum, maximum = self.sat_min, self.sat_max
        elif channel == "value":
            minimum, maximum = self.val_min, self.val_max

        _, tmp = cv2.threshold(self.channels[channel], maximum, 0, cv2.THRESH_TOZERO_INV)
        _, self.channels[channel] = cv2.threshold(tmp, minimum, 255, cv2.THRESH_BINARY)

        if channel == 'hue':
            self.channels['hue'] = cv2.bitwise_not(self.channels['hue'])

    def find_max_displacement(self, mask):
        """Find the point along the laser line that is displaced the most."""
        if self.axis == 'y':  # horizontal laser line
            projection = np.argmax(mask, axis=0)
        else:  # vertical laser line
            projection = np.argmax(mask, axis=1)

        # Smooth the projection for stability
        projection = cv2.GaussianBlur(projection.astype(np.float32), (15, 1), 0)

        # Compute relative displacement
        baseline = np.median(projection)
        displacement = projection - baseline

        # Find max absolute displacement
        max_idx = int(np.argmax(np.abs(displacement)))
        max_disp = float(displacement[max_idx])

        # Map back to coordinates
        if self.axis == 'y':
            x, y = max_idx, projection[max_idx]
        else:
            x, y = projection[max_idx], max_idx

        return (int(x), int(y)), max_disp

    def track(self, frame, mask, sample_step=5, boundary_size=50):
        center = None
        mask_gray = mask.astype(np.uint8)

        if self.reference_point is None:
            self.reference_point = frame.shape[0] / 2 if self.axis == 'y' else frame.shape[1] / 2

        if self.axis == 'y':
            y_min = max(int(self.reference_point - boundary_size), 0)
            y_max = min(int(self.reference_point + boundary_size), mask_gray.shape[0])
            mask_boundary = mask_gray[y_min:y_max, :]
            points = []
            for x in range(0, mask_boundary.shape[1], sample_step):
                col = mask_boundary[:, x]
                if np.any(col > 0):
                    y_initial = np.argmax(col)
                    points.append([x, y_initial + y_min])
        else:  # 'x' axis
            x_min = max(int(self.reference_point - boundary_size), 0)
            x_max = min(int(self.reference_point + boundary_size), mask_gray.shape[1])

            mask_boundary = mask_gray[:, x_min:x_max]
            points = []
            for y in range(0, mask_boundary.shape[0], sample_step):
                row = mask_boundary[y, :]
                if np.any(row > 0):
                    x_initial = np.argmax(row)
                    points.append([x_initial + x_min, y])

        if points:
            # initial_pts = np.array(points, dtype=np.float32)
            initial_pts = np.array(points, dtype=np.int32)
            center_x = np.mean(initial_pts[:, 0])
            center_y = np.mean(initial_pts[:, 1])

            # Round down if < 0.5, else round up
            center_x = int(np.floor(center_x + 0.5))
            center_y = int(np.floor(center_y + 0.5))
            center_x = int(center_x)
            center_y = int(center_y)
            center = (center_x, center_y)

            current = center_y if self.axis == 'y' else center_x
            diff_val = current - self.reference_point
            if diff_val < 0:
                diff_val = 0
            # # --- Stabilize readings ---
            # self.position_history.append(diff_val)
            # if len(self.position_history) > self.history_length:
            #     self.position_history.pop(0)
            #
            # # Use a weighted or median filter for smoother results
            # smoothed_diff = np.median(self.position_history)  # or np.mean for averaging
            self.diff = round(diff_val, 2)

        else:
            center = None
            self.diff = None

        # Draw boundary
        color, thickness = (0, 255, 255), 2
        if self.axis == 'y':
            cv2.rectangle(frame, (0, y_min), (frame.shape[1], y_max), color, thickness)
        else:
            cv2.rectangle(frame, (x_min, 0), (x_max, frame.shape[0]), color, thickness)

        # Draw center
        if center is not None:
            cv2.circle(frame, (int(center[0]), int(center[1])), 8, (0, 0, 255), -1)
            cv2.circle(frame, (int(center[0]), int(center[1])), 14, (255, 255, 255), 2)

        self.previous_position = center

    def detect(self, frame):


        # Convert darkened frame to HSV
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv_img)
        self.channels['hue'], self.channels['saturation'], self.channels['value'] = h, s, v

        # Apply thresholds
        for ch in ['hue', 'saturation', 'value']:
            self.threshold_image(ch)

        # Combine thresholds to isolate laser
        self.channels['laser'] = cv2.bitwise_and(self.channels['hue'], self.channels['value'])
        self.channels['laser'] = cv2.bitwise_and(self.channels['saturation'], self.channels['laser'])

        # Track laser on the original frame (not darkened)
        self.track(frame, self.channels['laser'])

        return cv2.merge([self.channels['hue'], self.channels['saturation'], self.channels['value']])

    def display(self, img, frame):
        if self.display_thresholds:
            cv2.imshow('Thresholded_HSV_Image', img)
            cv2.imshow('Hue', self.channels['hue'])
            cv2.imshow('Saturation', self.channels['saturation'])
            cv2.imshow('Value', self.channels['value'])

    # ========================== Calibration ==========================
    def calibrate_zero_height(self):
        if self.previous_position:
            pixel_value = self.previous_position[0] if self.axis == 'x' else self.previous_position[1]
            self.reference_point = pixel_value
            print(f"Zero reference set for axis {self.axis.upper()} at {pixel_value} pixels")
            self.save_calibration_data()
            return pixel_value
        else:
            print("No laser detected! Cannot calibrate.")
            return None

    def add_calibration_point(self, pixel_diff, real_height):
        self.calibration_points.append((pixel_diff, real_height))
        self.save_calibration_data()
        print(f"Added calibration point: pixel_diff={pixel_diff}, real_height={real_height} mm")

    # ========================== Main run ==========================
    def run(self, frame=None):

        if frame is not None:
            hsv_image = self.detect(frame)
            # print(len(hsv_image))
            # --- Find where the laser line is displaced the most ---
            max_point, max_disp = self.find_max_displacement(self.channels['laser'])

            # # --- Annotate the frame ---
            # if max_point is not None:
            #     cv2.circle(frame, max_point, 10, (0, 255, 0), -1)
            #     cv2.putText(frame, f"Diff={max_disp:.2f}px", (max_point[0] + 20, max_point[1]),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # --- Existing height estimation (if you're still using diff) ---
            estimated_height = self.diff if self.diff is not None else None
            if estimated_height is not None:
                cv2.putText(frame, f"Height: {estimated_height:.2f} px", (100, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 10)

            # Optional: display HSV thresholds
            self.display(hsv_image, frame)

            # Return both values for flexibility
            return estimated_height, max_disp, max_point

    # ========================== HSV Slider Adjustment ==========================
    def create_hsv_sliders(self):
        """Create HSV sliders (trackbars) for dynamic threshold adjustment."""
        cv2.namedWindow("HSV Adjustments")
        cv2.resizeWindow("HSV Adjustments", 500, 300)

        cv2.createTrackbar("Hue Min", "HSV Adjustments", self.hue_min, 179, lambda x: None)
        cv2.createTrackbar("Hue Max", "HSV Adjustments", self.hue_max, 179, lambda x: None)
        cv2.createTrackbar("Sat Min", "HSV Adjustments", self.sat_min, 255, lambda x: None)
        cv2.createTrackbar("Sat Max", "HSV Adjustments", self.sat_max, 255, lambda x: None)
        cv2.createTrackbar("Val Min", "HSV Adjustments", self.val_min, 255, lambda x: None)
        cv2.createTrackbar("Val Max", "HSV Adjustments", self.val_max, 255, lambda x: None)

    def update_hsv_from_sliders(self):
        """Update HSV thresholds based on slider positions."""
        self.hue_min = cv2.getTrackbarPos("Hue Min", "HSV Adjustments")
        self.hue_max = cv2.getTrackbarPos("Hue Max", "HSV Adjustments")
        self.sat_min = cv2.getTrackbarPos("Sat Min", "HSV Adjustments")
        self.sat_max = cv2.getTrackbarPos("Sat Max", "HSV Adjustments")
        self.val_min = cv2.getTrackbarPos("Val Min", "HSV Adjustments")
        self.val_max = cv2.getTrackbarPos("Val Max", "HSV Adjustments")


if __name__ == '__main__':

    def draw_reference_point(frame, tracker):
        color = (255, 0, 0)  # Red color for reference
        thickness = 2
        if tracker.axis == 'y':
            # Horizontal line at center
            cv2.line(frame, (0, frame.shape[0] // 2), (frame.shape[1], frame.shape[0] // 2), color, thickness)
        elif tracker.axis == 'x':
            # Vertical line at center
            cv2.line(frame, (frame.shape[1] // 2, 0), (frame.shape[1] // 2, frame.shape[0]), color, thickness)


    def draw_crosshair(frame):
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2
        color = (0, 255, 0)  # Green color in BGR
        thickness = 1
        line_length = 100
        # Draw horizontal line
        cv2.line(frame, (center_x - line_length, center_y), (center_x + line_length, center_y), color, thickness)
        # Draw vertical line
        cv2.line(frame, (center_x, center_y - line_length), (center_x, center_y + line_length), color, thickness)

    from VisionSystem.VisionSystem import VisionSystem
    configFilePath = "/home/plp/cobot-soft-v2/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/system/storage/settings/camera_settings.json"
    parser = argparse.ArgumentParser(description='Run the Laser Tracker')
    parser.add_argument('-W', '--width',
                        default=1280,
                        type=int,
                        help='Camera Width')
    parser.add_argument('-H', '--height',
                        default=720,
                        type=int,
                        help='Camera Height')
    parser.add_argument('-u', '--huemin',
                        default=20,
                        type=int,
                        help='Hue Minimum Threshold')
    parser.add_argument('-U', '--huemax',
                        default=160,
                        type=int,
                        help='Hue Maximum Threshold')
    parser.add_argument('-s', '--satmin',
                        default=100,
                        type=int,
                        help='Saturation Minimum Threshold')
    parser.add_argument('-S', '--satmax',
                        default=255,
                        type=int,
                        help='Saturation Maximum Threshold')
    parser.add_argument('-v', '--valmin',
                        default=200,
                        type=int,
                        help='Value Minimum Threshold')
    parser.add_argument('-V', '--valmax',
                        default=255,
                        type=int,
                        help='Value Maximum Threshold')
    parser.add_argument('-d', '--display',
                        action='store_true',
                        help='Display Threshold Windows')
    params = parser.parse_args()

    tracker = LaserTracker(
        cam_width=params.width,
        cam_height=params.height,
        hue_min=0,  # lower red hue
        hue_max=10,  # upper red hue for lower range
        sat_min=150,  # high saturation for bright laser
        sat_max=255,
        val_min=200,  # high value for bright laser
        val_max=255,
        display_thresholds=params.display,
        axis='x'
    )

    tracker.create_hsv_sliders()
    tracker.display_thresholds = True

    VisionSystem = VisionSystem()
    from modules.shared.tools import Laser

    laser = Laser()
    laser.turnOn()

    calibration_points = getattr(tracker, "calibration_points", [])

    import time

    # --- Performance tracking state ---
    _perf_state = {"last_time": time.time(), "frames": 0, "updates": 0, "fps": 0.0, "rate": 0.0}


    def track_performance(has_measurement, display=False, frame=None):
        """
        Tracks and optionally displays how often new measurements are obtained.

        Args:
            has_measurement (bool): True if a valid diff/measurement was detected this frame.
            display (bool): If True, overlays FPS and measurement rate on the frame.
            frame (np.ndarray): The frame to overlay text on (optional).
        """
        now = time.time()
        _perf_state["frames"] += 1
        if has_measurement:
            _perf_state["updates"] += 1

        elapsed = now - _perf_state["last_time"]
        if elapsed >= 1.0:  # every 1 second
            _perf_state["fps"] = _perf_state["frames"] / elapsed
            _perf_state["rate"] = _perf_state["updates"] / elapsed
            # print(f"📸 FPS: {_perf_state['fps']:.1f} ")

            _perf_state["frames"] = 0
            _perf_state["updates"] = 0
            _perf_state["last_time"] = now

        # Optional: draw overlay
        if display and frame is not None:
            cv2.putText(frame, f"FPS: {_perf_state['fps']:.1f}", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 3)


    while True:
        tracker.update_hsv_from_sliders()
        _, frame, _ = VisionSystem.run()
        if frame is None:
            print("No frame captured from camera.")
            continue

        # --- Run tracker and get both diff and max displacement ---
        result = tracker.run(frame)
        if isinstance(result, tuple):
            diff, max_disp, max_point = result
        else:
            diff, max_disp, max_point = result, None, None
        # ✅ Measure how often we get updates (and overlay)
        track_performance(has_measurement=(diff is not None), display=True, frame=frame)
        # --- Display calibration model or raw pixel height ---
        if diff is not None:
            if hasattr(tracker, 'poly_func'):
                if diff != 0:
                    estimated_height_mm = tracker.poly_func(diff)
                else:
                    estimated_height_mm = 0
                cv2.putText(frame, f"Height: {estimated_height_mm:.2f} mm", (100, 400),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
            else:
                cv2.putText(frame, f"Height: {diff:.2f} px", (100, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 5)

        # --- Visualize the maximum displacement ---
        # if max_point is not None:
        #     cv2.circle(frame, max_point, 5, (0, 255, 0), -1)
        #     # print(f"Max Displacement at {max_point}: {max_disp:.2f}px")
        #     cv2.putText(frame, f"Max Disp: {max_disp:.2f}px",
        #                 (max_point[0] + 20, max_point[1]),
        #                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # --- Draw guides ---
        draw_crosshair(frame)
        cv2.imshow('LaserTracker Output', frame)

        # --- Key controls ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        elif key == ord('z'):
            tracker.calibrate_zero_height()
            tracker.save_calibration_data()
            print("Zero reference set!")

        elif key == ord('c'):
            if diff is not None:
                real_height = float(input("Enter real height in mm for this point: "))
                calibration_points.append((diff, real_height))
                tracker.calibration_points = calibration_points
                tracker.save_calibration_data()
                print(f"Collected calibration point: pixel_diff={diff}, height={real_height} mm")

        elif key == ord('f'):
            if len(calibration_points) >= 2:
                pixels, heights = zip(*calibration_points)
                poly_coeffs = numpy.polyfit(pixels, heights, deg=2)
                poly_func = numpy.poly1d(poly_coeffs)
                tracker.poly_func = poly_func
                tracker.calibration_points = calibration_points
                tracker.save_calibration_data()
                print("New calibration model saved!")
            else:
                print("Need at least 2 calibration points to fit a model.")

        elif key == ord('m'):
            tracker2 = LaserTracker(
                cam_width=params.width,
                cam_height=params.height,
                hue_min=params.huemin,
                hue_max=params.huemax,
                sat_min=100,
                sat_max=params.satmax,
                val_min=150,
                val_max=params.valmax,
                display_thresholds=params.display,
                axis='x'
            )
            result = tracker2.run(frame)
            if isinstance(result, tuple):
                diff, max_disp, max_point = result
            else:
                diff, max_disp, max_point = result, None, None

            print(f"Measured Diff: {diff} px, Max Displacement: {max_disp} px at {max_point}")

