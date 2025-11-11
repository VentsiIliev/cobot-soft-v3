import json

import cv2
import numpy as np
import time
from itertools import combinations
from modules.VisionSystem.VisionSystem import VisionSystem
from src.backend.GlueDispensingApplication.robot.FairinoRobot import FairinoRobot
from src.backend.GlueDispensingApplication.robot.robotService.RobotService import RobotService
from src.backend.GlueDispensingApplication.robot.robotService.RobotService import RobotService
from src.backend.GlueDispensingApplication.settings.SettingsService import SettingsService
from src.backend.GlueDispensingApplication.utils.custom_logging import LoggingLevel, log_if_enabled, \
    setup_logger
from modules.shared.MessageBroker import MessageBroker

ENABLE_LOGGING = True
LOG_BROADCAST_TO_UI = True
BROAD_CAST_IMAGE = True
BROADCAST_TOPIC = "robot-calibration-log"
ROBOT_CALIBRATION_IMAGE_TOPIC = "robot-calibration-image"
ROBOT_CALIBRATION_STARTED_TOPIC = "robot-calibration-start"
ROBOT_CALIBRATION_STOPPED_TOPIC = "robot-calibration-stop"

nesting_logger = setup_logger("RobotCalibrationService") if ENABLE_LOGGING else None



class DebugDraw:
    def __init__(self):
        # drawing settings
        self.marker_color = (0, 255, 0)  # Green
        self.marker_radius = 6
        self.text_color = (0, 255, 0)  # Green
        self.text_scale = 0.7
        self.text_thickness = 2
        self.text_font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_offset = 10  # Offset for text position relative to marker top-left corner
        self.text_position = (self.marker_radius + self.text_offset, self.marker_radius + self.text_offset)
        self.image_center_color = (255, 0, 0)  # Blue
        self.image_center_radius = 4
        self.circle_thickness = -1

    def draw_marker_top_left_corner(self, frame, marker_id, marker_corners):
        """Draw marker top-left corner on frame"""
        if marker_id in marker_corners:
            top_left_px = marker_corners[marker_id]
            cv2.circle(frame, top_left_px, self.marker_radius, self.marker_color, self.circle_thickness)
            cv2.putText(frame, f"ID {marker_id}", (top_left_px[0] + self.text_offset, top_left_px[1]),
                        self.text_font, self.text_scale, self.text_color, self.text_thickness)
            return True
        return False

    def draw_image_center(self, frame):
        """Draw crosshair at image center"""
        frame_height, frame_width = frame.shape[:2]
        center_x, center_y = frame_width // 2, frame_height // 2

        # Color and thickness
        color = getattr(self, "image_center_color", (0, 255, 0))  # default green
        thickness = 1  # thinner than 12 so it looks clean

        # Draw horizontal line across the frame
        cv2.line(frame, (0, center_y), (frame_width, center_y), color, thickness)

        # Draw vertical line across the frame
        cv2.line(frame, (center_x, 0), (center_x, frame_height), color, thickness)

        # Optional: draw small circle at center (for reference)
        cv2.circle(frame, (center_x, center_y), 2, color, -1)


class CalibrationPipeline:
    def __init__(self, system=None, robot_service=None, required_ids=None, debug=False, step_by_step=False,
                 live_visualization=False):
        # --- STATES ---

        self.debug = debug
        self.step_by_step = step_by_step
        # if self.debug:
        self.debug_draw = DebugDraw()
        self.broker = MessageBroker()
        self.states = {
            "INITIALIZING": 0,
            "LOOKING_FOR_CHESSBOARD": 1,
            "CHESSBOARD_FOUND": 2,
            "ALIGN_TO_CHESSBOARD_CENTER": 3,
            "LOOKING_FOR_ARUCO_MARKERS": 4,
            "ALL_ARUCO_FOUND": 5,
            "COMPUTE_OFFSETS": 6,
            "ALIGN_ROBOT": 7,
            "ITERATE_ALIGNMENT": 8,
            "DONE": 9,
            "ERROR": 10
        }
        self.current_state = self.states["INITIALIZING"]

        # --- Vision system ---
        if system is None:
            self.system = VisionSystem()
        else:
            self.system = system

        self.system.camera_settings.set_draw_contours(False)

        # --- Settings Service ---
        settingsService = SettingsService()
        robot_config = settingsService.load_robot_config()

        # --- Robot ---
        if robot_service == None:
            self.robot = FairinoRobot(robot_config.robot_ip)
            self.settings_service = SettingsService()
            self.robot_service = RobotService(self.robot, self.settings_service, None)
        else:
            self.robot_service = robot_service

        self.robot_service.moveToCalibrationPosition()

        time.sleep(2)

        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.square_size_mm = self.system.camera_settings.get_square_size_mm()
        self.bottom_left_chessboard_corner_px = None
        self.chessboard_center_px = None

        # ArUco requirements
        self.required_ids = set(required_ids if required_ids is not None else [])
        self.detected_ids = set()
        self.marker_top_left_corners = {}
        self.markers_offsets_mm = {}
        self.current_marker_id = 0

        self.Z_current = self.robot_service.getCurrentPosition()[2]
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"Z_current: {self.Z_current}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        self.Z_target = 300  # desired height
        self.ppm_scale = self.Z_current / self.Z_target

        self.marker_top_left_corners_mm = {}
        self.robot_positions_for_calibration = {}
        self.camera_points_for_homography = {}

        self.PPM = None

        # Iterative alignment tracking
        self.iteration_count = 0
        self.max_iterations = 50
        self.alignment_threshold_mm = 0.25

        # Optimization parameters
        self.adaptive_movement = True  # Use larger moves when error is large
        self.min_camera_flush = 5  # Reduce camera buffer flushing
        self.fast_iteration_wait = 1  # Shorter wait time for iterations
        self.max_acceptable_calibration_error =1
        self.camera_to_tcp_offsets = (-5.81, 74.45)

        # Live visualization
        self.live_visualization = live_visualization  # Enable live camera feed
        self.show_debug_info = True  # Show state and error info on feed
        
        # Timing and performance tracking
        self.state_timings = {}  # Track time spent in each state
        self.current_state_start_time = None
        self.total_calibration_start_time = None

        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Looking for chessboard with size: {self.chessboard_size}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

    def compute_ppm_from_corners(self, corners_refined):
        """Compute pixels-per-mm from chessboard corners"""
        cols, rows = self.chessboard_size
        horiz, vert = [], []
        # corners_refined has shape (n_corners, 1, 2), so we need to access [i, 0]
        for r in range(rows):  # horizontal neighbors
            base = r * cols
            for c in range(cols - 1):
                i1 = base + c
                i2 = base + c + 1
                pt1 = corners_refined[i1, 0]  # Extract (x, y) coordinates
                pt2 = corners_refined[i2, 0]  # Extract (x, y) coordinates
                horiz.append(np.linalg.norm(pt2 - pt1))

        for r in range(rows - 1):  # vertical neighbors
            for c in range(cols):
                i1 = r * cols + c
                i2 = (r + 1) * cols + c
                pt1 = corners_refined[i1, 0]  # Extract (x, y) coordinates
                pt2 = corners_refined[i2, 0]  # Extract (x, y) coordinates
                vert.append(np.linalg.norm(pt2 - pt1))

        all_d = np.array(horiz + vert, dtype=np.float32)
        if all_d.size == 0:
            return None

        avg_square_px = float(np.mean(all_d))
        ppm = avg_square_px / float(self.square_size_mm)
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                       f"PPM calculation debug: avg_square_px={avg_square_px:.3f}, square_size_mm={self.square_size_mm:.2f}, ppm={ppm:.3f}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        return ppm

    def find_chessboard_and_compute_ppm(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Found chessboard! Detected {len(corners)} corners",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria
            )
            self.original_chessboard_corners = corners_refined
            # --- Store bottom-left corner of chessboard in pixels ---
            cols, rows = self.chessboard_size
            self.bottom_left_chessboard_corner_px = corners_refined[(rows - 1) * cols, 0]  # (x, y)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Bottom-left chessboard corner (px): {self.bottom_left_chessboard_corner_px}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            # Draw bottom-left corner marker
            bottom_left_px = tuple(self.bottom_left_chessboard_corner_px.astype(int))
            cv2.circle(frame, bottom_left_px, 8, (0, 0, 255), -1)  # Red circle
            cv2.putText(frame, "BL", (bottom_left_px[0] + 10, bottom_left_px[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # --- Compute chessboard center ---
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Chessboard dimensions: {rows} rows x {cols} cols",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Row parity: {'even' if rows % 2 == 0 else 'odd'}, Col parity: {'even' if cols % 2 == 0 else 'odd'}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            # For even-dimensioned chessboards, calculate center as average of 4 central corners
            if rows % 2 == 0 and cols % 2 == 0:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               "Using 4-corner averaging method for even dimensions",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                # Even dimensions - use 4 central corners
                center_row1 = rows // 2 - 1
                center_row2 = rows // 2
                center_col1 = cols // 2 - 1
                center_col2 = cols // 2

                # Get the 4 central corner indices
                idx1 = center_row1 * cols + center_col1  # top-left of center
                idx2 = center_row1 * cols + center_col2  # top-right of center
                idx3 = center_row2 * cols + center_col1  # bottom-left of center
                idx4 = center_row2 * cols + center_col2  # bottom-right of center

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Central corner indices: {idx1}, {idx2}, {idx3}, {idx4}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                # Average the 4 central corners
                center_x = (corners_refined[idx1, 0, 0] + corners_refined[idx2, 0, 0] +
                            corners_refined[idx3, 0, 0] + corners_refined[idx4, 0, 0]) / 4.0
                center_y = (corners_refined[idx1, 0, 1] + corners_refined[idx2, 0, 1] +
                            corners_refined[idx3, 0, 1] + corners_refined[idx4, 0, 1]) / 4.0

                self.chessboard_center_px = (float(center_x), float(center_y))
            else:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               "Using single center corner method for odd dimensions",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                # Odd dimensions - use single center corner
                center_row = rows // 2
                center_col = cols // 2
                center_corner_index = center_row * cols + center_col

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Center corner: row {center_row}, col {center_col}, index {center_corner_index}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                self.chessboard_center_px = (
                    float(corners_refined[center_corner_index, 0, 0]),  # x coordinate
                    float(corners_refined[center_corner_index, 0, 1])  # y coordinate
                )
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Chessboard center (px): {self.chessboard_center_px}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            if self.debug:
                self.debug_draw.draw_image_center(frame)

            ppm = self.compute_ppm_from_corners(corners_refined)

            cv2.drawChessboardCorners(frame, self.chessboard_size, corners_refined, ret)
            return True, ppm
        else:
            cv2.putText(frame, "No chessboard detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.bottom_left_chessboard_corner_px = None
            return False, None

    def find_required_aruco_markers(self, frame):

        arucoCorners, arucoIds, image = self.system.detectArucoMarkers(image=frame)

        if arucoIds is not None:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"Detected {len(arucoIds)} ArUco markers",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"Marker IDs: {arucoIds.flatten()}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            for i, marker_id in enumerate(arucoIds.flatten()):
                if marker_id in self.required_ids:
                    self.detected_ids.add(marker_id)
                    # Get top-left corner (first corner) of the ArUco marker
                    top_left_corner = tuple(arucoCorners[i][0][0].astype(int))
                    self.marker_top_left_corners[marker_id] = top_left_corner

                    # Draw top-left corner on frame
                    cv2.circle(frame, top_left_corner, 2, (0, 255, 0), -1)
                    # cv2.putText(frame, f"ID {marker_id}", (top_left_corner[0] + 10, top_left_corner[1]),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"Currently have: {self.detected_ids}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Still missing: {self.required_ids - self.detected_ids}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            all_found = self.required_ids.issubset(self.detected_ids)
            if all_found:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "🎯 All required ArUco markers found!",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            return frame, all_found

        return frame, False

    def detect_specific_marker(self, frame, marker_id):
        marker_found = False

        arucoCorners, arucoIds, image = self.system.detectArucoMarkers(image=frame)
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                       f"Detection loop for specific marker {marker_id}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        # log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
        #                f"Detected {len(arucoIds)} ArUco markers at new pose ID: {arucoIds if arucoIds is not None else 'None'}",
        #                broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        if arucoIds is not None and marker_id in arucoIds:
            marker_found = True

        return marker_found, arucoCorners, arucoIds, frame

    def update_marker_top_left_corners(self, marker_id, corners, ids):
        for i, iter_marker_id in enumerate(ids.flatten()):
            if iter_marker_id != marker_id:
                continue
            # update marker top-left corner in pixels
            top_left_corner_px = tuple(corners[i][0][0].astype(int))
            self.marker_top_left_corners[marker_id] = top_left_corner_px

            # Convert to mm relative to bottom-left of chessboard
            x_mm = (top_left_corner_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
            y_mm = (self.bottom_left_chessboard_corner_px[1] - top_left_corner_px[1]) / self.PPM

            # update marker top-left corner in mm
            self.marker_top_left_corners_mm[marker_id] = (x_mm, y_mm)
            # log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
            #                f"Updated marker {marker_id} top-left corner position in mm: {self.marker_top_left_corners_mm[marker_id]}",
            #                broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

    def draw_live_overlay(self, frame, current_error_mm=None, current_markers=None):
        """Draw comprehensive live visualization overlay"""
        if not self.live_visualization:
            return frame

        # Get current state name
        state_name = [name for name, value in self.states.items() if value == self.current_state][0]

        # Draw image center (always visible)
        if hasattr(self, 'debug_draw'):
            self.debug_draw.draw_image_center(frame)

        # Draw progress bar
        progress = (self.current_marker_id / len(self.required_ids)) * 100 if self.required_ids else 0
        cv2.rectangle(frame, (10, frame.shape[0] - 50), (int(10 + progress * 3), frame.shape[0] - 30), (0, 255, 0), -1)
        cv2.rectangle(frame, (10, frame.shape[0] - 50), (310, frame.shape[0] - 30), (255, 255, 255), 2)

        # Status text overlay
        y_offset = 30
        line_height = 25

        # Current state
        cv2.putText(frame, f"State: {state_name}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += line_height

        # Current marker info
        if hasattr(self, 'current_marker_id') and self.required_ids:
            required_ids_list = sorted(list(self.required_ids))
            if self.current_marker_id < len(required_ids_list):
                current_marker = required_ids_list[self.current_marker_id]
                cv2.putText(frame, f"Marker: {current_marker} ({self.current_marker_id + 1}/{len(required_ids_list)})",
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                y_offset += line_height

        # Iteration info (during iterative alignment)
        if self.current_state == self.states["ITERATE_ALIGNMENT"]:
            cv2.putText(frame, f"Iteration: {self.iteration_count}/{self.max_iterations}",
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += line_height

            if current_error_mm is not None:
                error_color = (0, 255, 0) if current_error_mm <= self.alignment_threshold_mm else (0, 0, 255)
                cv2.putText(frame, f"Error: {current_error_mm:.3f}mm",
                            (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, error_color, 2)
                y_offset += line_height

        # PPM info
        if hasattr(self, 'PPM') and self.PPM is not None:
            cv2.putText(frame, f"PPM: {self.PPM:.2f} px/mm",
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
            y_offset += line_height

        # Draw currently detected markers (only those visible in this frame)
        if current_markers:
            for marker_id, center in current_markers.items():
                # Color coding: Green for required markers, Yellow for others
                color = (0, 255, 0) if marker_id in self.required_ids else (0, 255, 255)
                # cv2.circle(frame, center, 2, color, -1)
                # cv2.putText(frame, f"ID{marker_id}", (center[0] + 15, center[1] - 15),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Progress text
        cv2.putText(frame, f"Progress: {progress:.0f}%",
                    (10, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def show_live_feed(self, frame, current_error_mm=None, window_name="Calibration Live Feed", draw_overlay=True,broadcast_image=False):
        """Show live camera feed with overlays"""

        if broadcast_image:
            self.broker.publish(ROBOT_CALIBRATION_IMAGE_TOPIC, frame)

        if not self.live_visualization:
            return False

        # Detect markers in current frame for live display
        current_markers = {}
        arucoCorners, arucoIds, _ = self.system.detectArucoMarkers(image=frame)

        if arucoIds is not None:
            for i, marker_id in enumerate(np.array(arucoIds).flatten()):
                # Only process markers that are in required_ids
                if marker_id in self.required_ids:
                    # Get top-left corner (first corner) of the ArUco marker
                    top_left_corner = tuple(arucoCorners[i][0][0].astype(int))
                    current_markers[marker_id] = top_left_corner

        # Add overlays with current frame markers
        if draw_overlay:
            display_frame = self.draw_live_overlay(frame.copy(), current_error_mm, current_markers)
        else:
            display_frame = frame.copy()
        # Show frame
        cv2.imshow(window_name, display_frame)

        # Check for exit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "Live feed stopped by user (q pressed)",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            return True  # Signal to exit
        elif key == ord('s'):
            # Save current frame
            cv2.imwrite(f"live_capture_{time.time():.0f}.png", display_frame)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "Live frame saved",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        elif key == ord('p'):
            # Pause/resume
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           "Live feed paused - press any key to continue",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            cv2.waitKey(0)

        return False  # Continue


    def compute_avg_ppm(self,camera_points,robot_points):
        # List to store PPM values
        ppms = []
        cam_pts = camera_points
        rob_pts = robot_points
        # Compute PPM for each pair of points
        for i, j in combinations(range(len(cam_pts)), 2):
            # Distance in pixels
            dist_px = np.linalg.norm(cam_pts[i] - cam_pts[j])
            # Distance in mm
            dist_mm = np.linalg.norm(rob_pts[i] - rob_pts[j])
            # PPM for this pair
            ppms.append(dist_px / dist_mm)
            print(f"Pair ({i}, {j}): dist_px={dist_px:.2f}, dist_mm={dist_mm:.2f}, PPM={ppms[-1]:.2f}")

        # Compute average PPM
        average_ppm = np.mean(ppms)

        print("Average PPM:", average_ppm)

    def test_calibration(self, homography_matrix, camera_points, robot_points, save_json_path=None):
        """
        Test a homography by comparing transformed camera points to robot points.
        Returns average error and transformed points in cv2 format (N, 1, 2).

        :param homography_matrix: 3x3 homography matrix
        :param camera_points: Nx2 array-like of camera points
        :param robot_points: Nx2 array-like of robot points
        :param save_json_path: Path to save JSON results (optional). `.json` appended if missing.
        :return: (average_error, transformed_points_cv2) where transformed_points_cv2 shape is (N, 1, 2)
        """
        # Normalize inputs
        cam_pts = np.asarray(camera_points, dtype=np.float32).reshape(-1, 2)
        rob_pts = np.asarray(robot_points, dtype=np.float32).reshape(-1, 2)

        self.compute_avg_ppm(cam_pts,rob_pts)

        # Compute transformed points in cv2 format (N, 1, 2)
        transformed_pts_cv2 = cv2.perspectiveTransform(cam_pts.reshape(-1, 1, 2), homography_matrix)  # shape (N,1,2)
        transformed_pts_flat = transformed_pts_cv2.reshape(-1, 2)  # for calculations/logging

        # Prepare data for logging and JSON
        results = []
        for i, (cam_pt, transformed, robot_pt) in enumerate(zip(cam_pts, transformed_pts_flat, rob_pts)):
            error = float(np.linalg.norm(transformed - robot_pt))

            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"Point {i + 1}:",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"  Camera point:      {cam_pt}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"  Transformed point: {transformed}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"  Robot point:       {robot_pt}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"  Error (mm):        {error:.3f}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            results.append({
                "point": i + 1,
                "camera_point": [float(cam_pt[0]), float(cam_pt[1])],
                "transformed_point": [float(transformed[0]), float(transformed[1])],
                "robot_point": [float(robot_pt[0]), float(robot_pt[1])],
                "error_mm": error
            })

        # Compute average error
        errors = np.array([r["error_mm"] for r in results], dtype=np.float32)
        average_error = float(np.mean(errors)) if errors.size > 0 else 0.0
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Average transformation error: {average_error} mm",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        # Save to JSON if path provided (ensure .json extension)
        if save_json_path:
            if not str(save_json_path).lower().endswith(".json"):
                save_json_path = f"{save_json_path}.json"
            json_data = {"calibration_points": results, "average_error_mm": average_error}
            with open(save_json_path, "w") as f:
                json.dump(json_data, f, indent=4)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Saved calibration results to {save_json_path}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        # Return average error and transformed points in cv2 format (N, 1, 2)
        return average_error, transformed_pts_cv2

    def start_state_timer(self, state_name):
        """Start timing for a state"""
        if self.current_state_start_time is not None:
            # End previous state
            self.end_state_timer()
        
        self.current_state_start_time = time.time()
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                       f"⏱️ Starting timer for state: {state_name}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
    
    def end_state_timer(self):
        """End timing for current state"""
        if self.current_state_start_time is None:
            return
            
        state_duration = time.time() - self.current_state_start_time
        state_name = [name for name, value in self.states.items() if value == self.current_state][0]
        
        # Store timing
        if state_name not in self.state_timings:
            self.state_timings[state_name] = []
        self.state_timings[state_name].append(state_duration)
        
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"⏱️ State '{state_name}' completed in {state_duration:.3f} seconds",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        self.current_state_start_time = None
    
    def log_timing_summary(self):
        """Log comprehensive timing summary for bottleneck analysis"""
        if not self.state_timings:
            return
            
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       "📊 === CALIBRATION TIMING ANALYSIS ===",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        total_time = 0
        for state_name, durations in self.state_timings.items():
            total_duration = sum(durations)
            avg_duration = total_duration / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            count = len(durations)
            
            total_time += total_duration
            
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"🔍 {state_name}:",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"   Total: {total_duration:.3f}s | Avg: {avg_duration:.3f}s | Count: {count}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"   Min: {min_duration:.3f}s | Max: {max_duration:.3f}s",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        # Calculate percentages and identify bottlenecks
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"🚀 Total calibration time: {total_time:.3f} seconds",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        # Find biggest bottlenecks
        state_percentages = {}
        for state_name, durations in self.state_timings.items():
            total_duration = sum(durations)
            percentage = (total_duration / total_time) * 100
            state_percentages[state_name] = percentage
        
        # Sort by percentage (highest first)
        sorted_bottlenecks = sorted(state_percentages.items(), key=lambda x: x[1], reverse=True)
        
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       "🎯 BOTTLENECK ANALYSIS (by % of total time):",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        for state_name, percentage in sorted_bottlenecks:
            if percentage > 5:  # Only show states that take more than 5%
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                               f"⚠️  {state_name}: {percentage:.1f}% of total time",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

    def flush_camera_buffer(self):
        # Flush camera buffer and get stable frame
        for _ in range(self.min_camera_flush):
            self.system.getLatestFrame()
            # log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"Flushing camera buffer... {_ + 1}/5",
            #                broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

    def run(self):
        self.broker.publish(ROBOT_CALIBRATION_STARTED_TOPIC,"")
        # Start total calibration timer
        self.total_calibration_start_time = time.time()
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       "🚀 Starting calibration pipeline with timing analysis...",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        while True:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           "--- Calibration Pipeline State Machine ---",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            init_frame= self.system.getLatestFrame()
            state_name = [name for name, value in self.states.items() if value == self.current_state][0]
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Current state: {state_name} ({self.current_state})",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            
            # Start timer for current state
            self.start_state_timer(state_name)
            
            if self.current_state == self.states["INITIALIZING"]:
                if init_frame is None:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                                   "Waiting for camera to initialize...",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    continue
                else:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "System initialized ✅",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    self.current_state = self.states["LOOKING_FOR_CHESSBOARD"]

            elif self.current_state == self.states["LOOKING_FOR_CHESSBOARD"]:
                chessboard_frame = None

                while chessboard_frame is None:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, "Capturing chessboard frame...",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    chessboard_frame = self.system.getLatestFrame()

                found, ppm = self.find_chessboard_and_compute_ppm(chessboard_frame)

                if found:
                    self.PPM = ppm
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                                   f"Chessboard found with PPM: {self.PPM:.3f} px/mm ✅",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                    # Draw the bottom-left corner
                    if self.bottom_left_chessboard_corner_px is not None:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                       "Drawing bottom-left corner...",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                        bottom_left_px = tuple(self.bottom_left_chessboard_corner_px.astype(int))
                        cv2.circle(chessboard_frame, bottom_left_px, 8, (0, 0, 255), -1)  # Red circle
                        cv2.putText(chessboard_frame, "BL", (bottom_left_px[0] + 10, bottom_left_px[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                                       "Bottom-left corner not defined.",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                    # Draw the chessboard center
                    if self.chessboard_center_px is not None:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                       "Drawing chessboard center...",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                        chessboard_center_int = (int(self.chessboard_center_px[0]), int(self.chessboard_center_px[1]))
                        cv2.circle(chessboard_frame, chessboard_center_int, 2, (255, 255, 0), -1)  # Yellow circle
                        cv2.putText(chessboard_frame, "CB Center",
                                    (chessboard_center_int[0] + 15, chessboard_center_int[1] - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    else:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                                       "Chessboard center not defined.",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                    # Draw image center
                    if self.debug and self.debug_draw:
                        self.debug_draw.draw_image_center(chessboard_frame)

                    cv2.imwrite("new_development/NewCalibrationMethod/chessboard_frame.png", chessboard_frame)
                    self.current_state = self.states["CHESSBOARD_FOUND"]

            elif self.current_state == self.states["CHESSBOARD_FOUND"]:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"CHESSBOARD FOUND at {self.chessboard_center_px}, aligning to center...",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                self.current_state = self.states["LOOKING_FOR_ARUCO_MARKERS"]

            elif self.current_state == self.states["LOOKING_FOR_ARUCO_MARKERS"]:

                self.flush_camera_buffer()

                # Capture frame for ArUco detection
                all_aruco_detection_frame = None
                while all_aruco_detection_frame is None:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                   "Capturing frame for ArUco detection...",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    all_aruco_detection_frame = self.system.getLatestFrame()

                # cv2.putText(all_aruco_detection_frame, "Looking for ArUco markers...", (10, 90),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

                frame, all_found = self.find_required_aruco_markers(all_aruco_detection_frame)
                # save the aruco detection frame
                cv2.imwrite("new_development/NewCalibrationMethod/aruco_detection_frame.png", frame)
                if all_found:
                    self.current_state = self.states["ALL_ARUCO_FOUND"]

            elif self.current_state == self.states["ALL_ARUCO_FOUND"]:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"All required ArUco markers found: {self.detected_ids} ✅",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Found marker top-left corners (px): {self.marker_top_left_corners}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                self.camera_points_for_homography = self.marker_top_left_corners.copy()
                # marker_top_left_corners_mm will be computed below

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    for marker_id, top_left_corner_px in self.marker_top_left_corners.items():
                        # Convert to mm relative to bottom-left
                        x_mm = (top_left_corner_px[0] - bottom_left_px[0]) / self.PPM
                        y_mm = (bottom_left_px[1] - top_left_corner_px[1]) / self.PPM  # y relative to bottom-left

                        self.marker_top_left_corners_mm[marker_id] = (x_mm, y_mm)

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               "Marker top-left corners in mm relative to bottom-left:",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                for marker_id, top_left_corner_mm in self.marker_top_left_corners_mm.items():
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, f"ID {marker_id}: {top_left_corner_mm}",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                self.current_state = self.states["COMPUTE_OFFSETS"]

            elif self.current_state == self.states["COMPUTE_OFFSETS"]:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               "Computing offsets for robot calibration...",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    # Image center in pixels
                    image_center_px = (self.system.camera_settings.get_camera_width() // 2,
                                       self.system.camera_settings.get_camera_height() // 2)

                    # Convert image center to mm relative to bottom-left of chessboard
                    center_x_mm = (image_center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
                    center_y_mm = (self.bottom_left_chessboard_corner_px[1] - image_center_px[1]) / self.PPM
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                   f"Image center in mm relative to bottom-left: ({center_x_mm:.2f}, {center_y_mm:.2f})",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                    # Calculate offsets for all markers relative to image center
                    for marker_id, marker_mm in self.marker_top_left_corners_mm.items():
                        offset_x = marker_mm[0] - center_x_mm
                        offset_y = marker_mm[1] - center_y_mm
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                       f"Marker {marker_id}: position in mm = {marker_mm}, offset from image center = (X={offset_x:.2f}, Y={offset_y:.2f})",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                        self.markers_offsets_mm[marker_id] = (offset_x, offset_y)

                    self.current_state = self.states["ALIGN_ROBOT"]

            elif self.current_state == self.states["ALIGN_ROBOT"]:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               "Aligning robot to each marker and recording positions...",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                required_ids_list = sorted(list(self.required_ids))
                marker_id = required_ids_list[self.current_marker_id]

                # Reset iteration count for new marker
                self.iteration_count = 0

                # (1) Precomputed offset from calibration pose to marker
                calib_to_marker = self.markers_offsets_mm.get(marker_id, (0, 0))

                # (2) Current robot pose
                current_pose = self.robot_service.getCurrentPosition()
                x, y, z, rx, ry, rz = current_pose

                # (3) Calibration pose
                # calib_pose = CALIBRATION_POS
                calib_pose = self.robot_service.robot_config.getCalibrationPositionParsed()
                cx, cy, cz, crx, cry, crz = calib_pose

                # (4) Compute delta: calibration -> current
                calib_to_current = (x - cx, y - cy)

                # (5) Compute current -> marker
                current_to_marker = (
                    calib_to_marker[0] - calib_to_current[0],
                    calib_to_marker[1] - calib_to_current[1]
                )

                # (6) Apply correction at current pose
                x_new = x + current_to_marker[0]
                y_new = y + current_to_marker[1]
                z_new = self.Z_target
                new_position = [x_new, y_new, z_new, rx, ry, rz]

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"First align position for marker {marker_id}: {new_position}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                result = self.robot_service.moveToPosition(position=new_position,
                                                           tool=self.robot_service.robot_config.robot_tool,
                                                           workpiece=self.robot_service.robot_config.robot_user,
                                                           velocity=30,
                                                           acceleration=10,
                                                           waitToReachPosition=True)

                if result != 0:
                    # move to the center of the chessboard if the move failed
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR,
                                   f"Movement to marker {marker_id} failed, returning to calibration position",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    # self.robot_service.moveToCalibrationPosition()

                    if len(self.robot_positions_for_calibration) != 0:
                        result = self.robot_service.moveToPosition(position=self.robot_positions_for_calibration[0],
                                                                   tool=self.robot_service.robot_config.robot_tool,
                                                                   workpiece=self.robot_service.robot_config.robot_user,
                                                                   velocity=30,
                                                                   acceleration=10,
                                                                   waitToReachPosition=False)

                    # than try again to go to the target position


                    result = self.robot_service.moveToPosition(position=new_position,
                                                               tool=self.robot_service.robot_config.robot_tool,
                                                               workpiece=self.robot_service.robot_config.robot_user,
                                                               velocity=30,
                                                               acceleration=10,
                                                               waitToReachPosition=True)

                    if result != 0:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR,
                                       f"Second attempt to move to marker {marker_id} also failed, skipping this marker",
                                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                        self.current_state = self.states["ERROR"]
                        continue

                # Wait for robot and camera stability after movement
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Waiting for robot stability after moving to marker {marker_id}...",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                time.sleep(1)

                self.current_state = self.states["ITERATE_ALIGNMENT"]


            elif self.current_state == self.states["ITERATE_ALIGNMENT"]:
                required_ids_list = sorted(list(self.required_ids))
                marker_id = required_ids_list[self.current_marker_id]
                self.iteration_count += 1
                # Example usage of issubset (if needed):
                # all_found = set(required_ids_list).issubset(self.detected_ids)

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"Iterative alignment for marker {marker_id} - Iteration {self.iteration_count}/{self.max_iterations}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                if self.iteration_count > self.max_iterations:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                                   f"Maximum iterations ({self.max_iterations}) reached for marker {marker_id}. Proceeding anyway.",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    self.current_state = self.states["DONE"]
                    continue

                # self.flush_camera_buffer()

                # Capture frame for marker detection
                capture_start = time.time()
                attempt = 0
                iteration_image = None
                while iteration_image is None:
                    attempt += 1
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                   "Capturing frame for iterative alignment...",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    iteration_image= self.system.getLatestFrame()
                capture_time = time.time() - capture_start
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"⏱️ Frame capture: {capture_time:.3f}s ({attempt} attempts)",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                attempt = 0

                # Detect marker
                detection_start = time.time()
                marker_found, arucoCorners, arucoIds, _ = self.detect_specific_marker(iteration_image, marker_id)
                detection_time = time.time() - detection_start
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"⏱️ ArUco detection: {detection_time:.3f}s",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                if not marker_found:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR,
                                   f"Marker {marker_id} not found during iteration {self.iteration_count}!",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    # self.current_state = self.states["DONE"]  # Skip this marker
                    continue

                # Update marker top-left corners
                processing_start = time.time()
                self.update_marker_top_left_corners(marker_id, arucoCorners, arucoIds)

                # Get current marker position and image center
                image_center_px = (
                    self.system.camera_settings.get_camera_width() // 2,
                    self.system.camera_settings.get_camera_height() // 2
                )
                marker_top_left_px = self.marker_top_left_corners[marker_id]
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, "Computing Error:",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Image center (px): {image_center_px}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Marker {marker_id} top-left corner (px): ({marker_top_left_px[0]}, {marker_top_left_px[1]})",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                # Calculate current error
                offset_x_px = marker_top_left_px[0] - image_center_px[0]
                offset_y_px = marker_top_left_px[1] - image_center_px[1]
                current_error_px = np.sqrt(offset_x_px ** 2 + offset_y_px ** 2)

                # Convert to mm
                newPpm = self.PPM * self.ppm_scale
                current_error_mm = current_error_px / newPpm
                offset_x_mm = offset_x_px / newPpm
                offset_y_mm = offset_y_px / newPpm
                
                processing_time = time.time() - processing_start
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"⏱️ Error calculation: {processing_time:.3f}s",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"Iteration {self.iteration_count} - Current error: {current_error_mm:.3f} mm",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Offset (mm): X={offset_x_mm:.3f}, Y={offset_y_mm:.3f}",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                # Check if we've reached the threshold
                if current_error_mm <= self.alignment_threshold_mm:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                                   f"Current Error RAW: {current_error_mm} mm , {current_error_px} px",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                                   f"✅ Alignment achieved! Error {current_error_mm:.3f} mm is within {self.alignment_threshold_mm} mm threshold.",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                    # Save final iteration image
                    self.debug_draw.draw_image_center(iteration_image)
                    # cv2.circle(iteration_image, (int(marker_center_px[0]), int(marker_center_px[1])),
                    #           8, (0, 255, 0), -1)  # Green circle for marker center
                    # cv2.putText(iteration_image, f"Iter {self.iteration_count} - Aligned!",
                    #            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    # cv2.imwrite(f"final_iteration_marker_{marker_id}_iter_{self.iteration_count}.png", iteration_image)
                    # Update the stored position

                    # Query robot position repeatedly for 1 second and keep last reading
                    start_time = time.time()
                    current_robot_pose = None
                    while time.time() - start_time < 1.0:
                        current_robot_pose = self.robot_service.getCurrentPosition()
                        time.sleep(0.05)
                    self.robot_positions_for_calibration[marker_id] = current_robot_pose

                    # current_robot_pose = self.robot_service.getCurrentPosition()

                    self.robot_positions_for_calibration[marker_id] = current_robot_pose
                    # Show live feed with current error
                    self.show_live_feed(iteration_image, current_error_mm,broadcast_image=BROAD_CAST_IMAGE)
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                                   "Live visualization exited by user",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI,
                                   topic=BROADCAST_TOPIC,)

                    self.current_state = self.states["DONE"]
                    continue

                # Adaptive movement calculation for faster convergence
                if self.adaptive_movement:

                    # --- Adaptive movement scaling (fast convergence + derivative control) ---
                    min_step_mm = 0.1  # minimum movement (for very small errors)
                    max_step_mm = 25.0  # maximum movement for very large misalignments
                    target_error_mm = self.alignment_threshold_mm
                    max_error_ref = 50.0  # error at which we reach max step
                    k = 2.0  # responsiveness (1.0 = smooth, 2.0 = faster reaction)
                    derivative_scaling = 0.5  # how strongly derivative term reduces step (tune this)

                    # Compute normalized error
                    normalized_error = min(current_error_mm / max_error_ref, 1.0)

                    # Tanh curve for smooth aggressive scaling
                    step_scale = np.tanh(k * normalized_error)
                    max_move_mm = min_step_mm + step_scale * (max_step_mm - min_step_mm)

                    # Near the target, apply soft damping
                    if current_error_mm < target_error_mm * 2:
                        damping_ratio = (current_error_mm / (target_error_mm * 2)) ** 2  # quadratic damping
                        max_move_mm *= max(damping_ratio, 0.05)

                    # Derivative control to reduce overshoot
                    # Requires storing previous_error_mm (from last iteration)
                    if hasattr(self, 'previous_error_mm'):
                        error_change = current_error_mm - self.previous_error_mm
                        derivative_factor = 1.0 / (1.0 + derivative_scaling * abs(error_change))
                        max_move_mm *= derivative_factor

                    # Save current error for next iteration
                    self.previous_error_mm = current_error_mm

                    # Optional: hard stop when very close to target
                    if current_error_mm < target_error_mm * 0.5:
                        max_move_mm = min_step_mm

                # For robot movement:
                # - If marker is to the RIGHT of image center (offset_x_mm > 0), move robot RIGHT (+X)
                # - If marker is to the LEFT of image center (offset_x_mm < 0), move robot LEFT (-X)
                # - If marker is BELOW image center (offset_y_mm > 0), move robot BACK (+Y)
                # - If marker is ABOVE image center (offset_y_mm < 0), move robot FORWARD (-Y)

                move_x_mm = max(-max_move_mm, min(max_move_mm, offset_x_mm))  # Move toward marker
                move_y_mm = max(-max_move_mm, min(max_move_mm, -offset_y_mm))  # Y inverted: image down = robot back

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Adaptive movement: max_move={max_move_mm:.1f}mm (error={current_error_mm:.3f}mm)",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               f"Making iterative movement: X+={move_x_mm:.3f}mm, Y+={move_y_mm:.3f}mm",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                # Move robot by small increment
                movement_start = time.time()
                current_pose = self.robot_service.getCurrentPosition()
                x, y, z, rx, ry, rz = current_pose
                x += move_x_mm
                y += move_y_mm
                iterative_position = [x, y, z, rx, ry, rz]

                self.robot_service.moveToPosition(position=iterative_position,
                                                  tool=self.robot_service.robot_config.robot_tool,
                                                  workpiece=self.robot_service.robot_config.robot_user,
                                                  velocity=30,  # Slower for precision
                                                  acceleration=10,
                                                  waitToReachPosition=True)
                movement_time = time.time() - movement_start
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"⏱️ Robot movement: {movement_time:.3f}s",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                # Optimized wait time for faster iterations
                stability_start = time.time()
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                               "Waiting for stability after iterative movement...",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                time.sleep(self.fast_iteration_wait)
                stability_time = time.time() - stability_start
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"⏱️ Stability wait: {stability_time:.3f}s",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

                # Save iteration debug image
                self.debug_draw.draw_image_center(iteration_image)
                cv2.circle(iteration_image, (int(marker_top_left_px[0]), int(marker_top_left_px[1])),
                           2, (255, 255, 0), -1)  # Yellow circle for marker top-left corner
                # cv2.putText(iteration_image, f"Iter {self.iteration_count}: {current_error_mm:.3f}mm",
                #             (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                if self.iteration_count >= self.max_iterations:
                    cv2.imwrite(f"iteration_marker_{marker_id}_iter_{self.iteration_count}.png", iteration_image)

                # Show live feed with current error
                self.show_live_feed(iteration_image, current_error_mm,broadcast_image=BROAD_CAST_IMAGE)
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               "Live visualization exited by user",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI,
                               topic=BROADCAST_TOPIC)


                # Continue iterating (stay in ITERATE_ALIGNMENT state)
            elif self.current_state == self.states["DONE"]:
                if self.current_marker_id < len(self.required_ids) - 1:
                    self.current_marker_id += 1
                    self.current_state = self.states["ALIGN_ROBOT"]
                else:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                                   "All markers processed. Calibration complete!",
                                   broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                    self.current_state = self.states["DONE"]
                    break
            elif self.current_state == self.states["ERROR"]:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR,
                               "An error occurred. Exiting calibration process.",
                               broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
                break

        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "Calibration process finished.",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "Markers and recorded robot positions:",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        # Sort by marker ID
        sorted_robot_items = sorted(self.robot_positions_for_calibration.items(), key=lambda x: x[0])
        sorted_camera_items = sorted(self.camera_points_for_homography.items(), key=lambda x: x[0])

        for marker_id, position in sorted_robot_items:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Marker ID {marker_id}: Robot Position {position}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "Camera points for homography:",
                       broadcast_to_ui=True)
        for marker_id, point in sorted_camera_items:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Marker ID {marker_id}: Camera Point {point}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        # Prepare corresponding points in sorted order
        robot_positions = [pos[:2] for _, pos in sorted_robot_items]
        camera_points = [pt for _, pt in sorted_camera_items]

        # Compute homography
        src_pts = np.array(camera_points, dtype=np.float32)
        dst_pts = np.array(robot_positions, dtype=np.float32)

        H_camera_center, status = cv2.findHomography(src_pts, dst_pts)
        # H_camera_center, status = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Homography computation status: {status.ravel()}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Homography matrix camera center:\n{H_camera_center}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

        # Test the homography
        """TRANSFORM CAMERA CENTER POINTS IN PIXELS TO ROBOT COORDINATES IN MM USING THE HOMOGRAPHY MATRIX"""
        average_error_camera_center, transformed_points_camera_center = self.test_calibration(H_camera_center, src_pts,
                                                                                              dst_pts,"transfromation_to_camera_center")
        if average_error_camera_center > 1:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                           "Average camera center error exceeds 1 mm, consider recalibration.",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        else:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           "H_camera_center test passed with acceptable error.",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            np.save("cameraToRobotMatrix_camera_center.npy", H_camera_center)

        """TRANSFORM CAMERA CENTER POINTS IN PIXELS TO ROBOT COORDINATES IN MM USING THE HOMOGRAPHY MATRIX AND APPLY TCP OFFSET"""
        # Now compute homography for robot TCP (tool center point)
        # offset = (-5.81, 74.45)
        offset = self.camera_to_tcp_offsets
        dst_pts_offset = dst_pts + np.array(offset)
        H_robot_tcp, status = cv2.findHomography(src_pts, dst_pts_offset)
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Homography matrix robot TCP:\n{H_robot_tcp}",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        average_error_tcp, transformed_points_tcp = self.test_calibration(H_robot_tcp, src_pts, dst_pts_offset)

        """ CALCULATE AVERAGE ERROR FOR ROBOT TCP HOMOGRAPHY AND SAVE IF ACCEPTABLE """
        if average_error_tcp > self.max_acceptable_calibration_error:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                           "Average TCP error exceeds 1 mm, consider recalibration.",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        else:
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           "H_robot_tcp test passed with acceptable error.",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
            from VisionSystem.VisionSystem import CAMERA_TO_ROBOT_MATRIX_PATH
            # np.save(CAMERA_TO_ROBOT_MATRIX_PATH, H_robot_tcp)
            np.save(CAMERA_TO_ROBOT_MATRIX_PATH,H_camera_center)
            # update the in memory matrix as well
            self.system.cameraToRobotMatrix = H_camera_center
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                           f"Saved robot TCP homography to {CAMERA_TO_ROBOT_MATRIX_PATH}",
                           broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)

            for point in transformed_points_camera_center:
                x, y = point[0]
                position = [x, y, self.Z_target, 180, 0, 0]
                self.robot_service.moveToPosition(position=position,
                                                  tool=self.robot_service.robot_config.robot_tool,
                                                  workpiece=self.robot_service.robot_config.robot_user,
                                                  velocity=30,
                                                  acceleration=10,
                                                  waitToReachPosition=True)
                self.robot_service._waitForRobotToReachPosition(endPoint=position, threshold=1, delay=0, timeout=30)
                time.sleep(1)  # Wait for stability at each test point
                self.flush_camera_buffer()

                calibration_test_image= self.system.getLatestFrame()
                self.debug_draw.draw_image_center(calibration_test_image)
                self.show_live_feed(calibration_test_image, window_name="Calibration Test",broadcast_image=BROAD_CAST_IMAGE)

        # End final state timer
        self.end_state_timer()
        
        # Log comprehensive timing summary
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       "All markers processed. Calibration complete!",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        # Calculate total calibration time
        total_calibration_time = time.time() - self.total_calibration_start_time
        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                       f"Total calibration time: {total_calibration_time:.3f} seconds",
                       broadcast_to_ui=LOG_BROADCAST_TO_UI, topic=BROADCAST_TOPIC)
        
        # Log detailed timing analysis for bottleneck identification
        self.log_timing_summary()

        self.broker.publish(ROBOT_CALIBRATION_STOPPED_TOPIC,"")
        self.broker.publish(ROBOT_CALIBRATION_STOPPED_TOPIC, "")
        return


if __name__ == "__main__":
    from src.backend.GlueDispensingApplication.vision.VisionService import VisionServiceSingleton
    import threading
    system = VisionServiceSingleton.get_instance()
    # Start the camera feed in a separate thread
    systemThread = threading.Thread(target=system.run, daemon=True)
    systemThread.start()
    # required_ids = [0, 1, 2, 3, 4, 5, 6]
    # required_ids = [0, 14, 28, 43, 57, 71, 86, 100, 115, 129, 143, 158, 172, 186, 201, 215, 229, 244, 258, 267, 272,
    #                 315, 330]
    required_ids = [0, 8, 15, 165, 173, 180, 272, 313, 329]
    pipeline = CalibrationPipeline(required_ids=required_ids,
                                   debug=True,
                                   live_visualization=True,
                                   system=system)
    pipeline.run()
